"""Runner for the Kanwal-Gardner kin-selection test (PREREG_KIN_TEST.md).

Stage V (port validation): the authors' model and start (random z), all 25 grid cells, seed 1.
Stage M (test): cells (n, c) in {(2, 0.8), (5, 0.8)}; arms T (authors' model), X (juveniles shuffled across
patches before helping), F (fixed, density-independent dispersal); all from the rare start (z = 0);
seeds 100-109, shared across arms.

Usage: python -m ecological_models.density_dependent_dispersal.run_test {V|M} [--workers 30]
Each run writes data/<stage>/<name>.npz (float32 per-generation arrays) and a progress file; finished runs are
skipped on restart. The git commit and a clean-tree flag are recorded in each file.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
G = 20000
ARMS = {"T": dict(dd=True, shuffle=False), "X": dict(dd=True, shuffle=True), "F": dict(dd=False, shuffle=False)}
V_CELLS = [(n, c) for n in (1, 2, 3, 5, 10) for c in (0.0, 0.2, 0.4, 0.6, 0.8)]
M_CELLS = [(2, 0.8), (5, 0.8)]
M_SEEDS = list(range(100, 110))


def git_state():
    root = HERE.parents[1]
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "ecological_models/density_dependent_dispersal"],
                           capture_output=True, text=True).stdout.strip()
    return commit, dirty == ""


def jobs(stage):
    if stage == "V":
        return [dict(stage="V", name=f"n{n}_c{c}", n=n, c=c, seed=1, arm="T", init_z="random") for n, c in V_CELLS]
    return [dict(stage="M", name=f"{arm}_n{n}_c{c}_s{s}", n=n, c=c, seed=s, arm=arm, init_z="zero")
            for n, c in M_CELLS for arm in ("T", "X", "F") for s in M_SEEDS]


def run_one(job):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from ecological_models.density_dependent_dispersal import kg_model as K
    out_dir = DATA / ("stage_v" if job["stage"] == "V" else "stage_m")
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"{job['name']}.npz"
    if final.exists():
        return job["name"], "skipped"
    prog = out_dir / f"{job['name']}.progress"
    t0 = time.time()

    def progress(g):
        if g % 100 == 0:
            prog.write_text(f"{g} {time.time() - t0:.0f}\n")

    arm = ARMS[job["arm"]]
    o = K.run(job["n"], job["c"], G=G, seed=job["seed"], dd=arm["dd"], shuffle=arm["shuffle"],
              init_z=job["init_z"], progress=progress)
    commit, clean = git_state()
    meta = dict(job, G=G, wall_s=time.time() - t0, commit=commit, clean=clean)
    tmp = out_dir / f"{job['name']}.tmp.npz"
    np.savez_compressed(tmp, **{k: np.asarray(v, np.float32) for k, v in o.items() if k != "final_breeders"},
                        final_breeders=o["final_breeders"].astype(np.float32), meta=json.dumps(meta))
    os.replace(tmp, final)
    prog.unlink(missing_ok=True)
    return job["name"], f"done {meta['wall_s'] / 3600:.2f} h"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["V", "M"])
    ap.add_argument("--workers", type=int, default=30)
    a = ap.parse_args()
    commit, clean = git_state()
    if not clean:
        raise SystemExit("module tree not clean; commit first")
    js = jobs(a.stage)
    print(f"stage {a.stage}: {len(js)} runs, commit {commit}", flush=True)
    with Pool(min(a.workers, len(js))) as p:
        for name, status in p.imap_unordered(run_one, js):
            print(time.strftime("%H:%M:%S"), name, status, flush=True)


if __name__ == "__main__":
    main()
