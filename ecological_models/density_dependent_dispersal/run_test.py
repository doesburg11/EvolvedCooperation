"""Runner for the Kanwal-Gardner kin-selection test (PREREG_KIN_TEST.md).

Stage V (port validation): the authors' model and start (random z), all 25 grid cells, seed 1.
Stage M (test): cells (n, c) in {(2, 0.8), (5, 0.8)}; arms T (authors' model), X (juveniles shuffled across
patches before helping), F (fixed, density-independent dispersal); all from the no-helping start (z = 0);
seeds 100-109, shared across arms. Stage M refuses to start unless data/stage_v_summary.json says Stage V passed.

Usage: python -m ecological_models.density_dependent_dispersal.run_test {V|M} [--workers 30]
Raw output (one .npz per run, float32 per-generation arrays plus a JSON manifest) goes to
~/simulation_results/kg_kin_test/stage_{v,m}/, outside the repository. Finished runs are validated and skipped on
restart; a file that does not validate stops the runner. A crash in any run stops the stage (registered kill rule).
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
# KG_RAW, KG_DATA and KG_G override paths and length for smoke tests only; the registered runs use the defaults.
RAW = Path(os.environ.get("KG_RAW", Path.home() / "simulation_results" / "kg_kin_test"))
DATA = Path(os.environ.get("KG_DATA", HERE / "data"))
G = int(os.environ.get("KG_G", 20000))
ARMS = {"T": dict(dd=True, shuffle=False), "X": dict(dd=True, shuffle=True), "F": dict(dd=False, shuffle=False)}
V_CELLS = [(n, c) for n in (1, 2, 3, 5, 10) for c in (0.0, 0.2, 0.4, 0.6, 0.8)]
M_CELLS = [(2, 0.8), (5, 0.8)]
M_SEEDS = list(range(100, 110))
ARRAYS = ("b1", "b2", "z", "z_median", "d_mean", "d_sum", "d_rows", "empty", "survivors", "dispersers",
          "cost_z", "total_z")


def git_state():
    root = HERE.parents[1]
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--",
                            "ecological_models/density_dependent_dispersal"],
                           capture_output=True, text=True).stdout
    return commit, dirty.strip() == ""


def stage_dir(stage):
    return RAW / ("stage_v" if stage == "V" else "stage_m")


def jobs(stage):
    if stage == "V":
        return [dict(stage="V", name=f"n{n}_c{c}", n=n, c=c, seed=1, arm="T", init_z="random") for n, c in V_CELLS]
    return [dict(stage="M", name=f"{arm}_n{n}_c{c}_s{s}", n=n, c=c, seed=s, arm=arm, init_z="zero")
            for n, c in M_CELLS for arm in ("T", "X", "F") for s in M_SEEDS]


def validate(path, job):
    """Raise if the file is not a complete run of exactly this job."""
    with np.load(path) as f:
        meta = json.loads(str(f["meta"]))
        for key in ("stage", "name", "n", "c", "seed", "arm", "init_z"):
            if meta[key] != job[key]:
                raise ValueError(f"{path.name}: meta {key}={meta[key]!r}, expected {job[key]!r}")
        if meta["G"] != G:
            raise ValueError(f"{path.name}: G={meta['G']}")
        for a in ARRAYS:
            if f[a].shape != (G + 1,):
                raise ValueError(f"{path.name}: {a} shape {f[a].shape}")
        if not np.isfinite(f["z"]).all():
            raise ValueError(f"{path.name}: non-finite z")
    return meta


def _atomic_write_text(path, text):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def run_one(job):
    from ecological_models.density_dependent_dispersal import kg_model as K
    out_dir = stage_dir(job["stage"])
    final = out_dir / f"{job['name']}.npz"
    if final.exists():
        validate(final, job)
        return job["name"], "skipped (valid)"
    prog = out_dir / f"{job['name']}.progress"
    t0 = time.time()

    def progress(g):
        if g % 100 == 0:
            _atomic_write_text(prog, f"{g} {time.time() - t0:.1f}\n")

    arm = ARMS[job["arm"]]
    o = K.run(job["n"], job["c"], G=G, seed=job["seed"], dd=arm["dd"], shuffle=arm["shuffle"],
              init_z=job["init_z"], progress=progress)
    meta = dict(job, G=G, wall_s=time.time() - t0)
    tmp = out_dir / f"{job['name']}.{os.getpid()}.partial.npz"
    np.savez_compressed(tmp, **{a: np.asarray(o[a], np.float32) for a in ARRAYS},
                        final_breeders=o["final_breeders"].astype(np.float32), meta=json.dumps(meta))
    validate(tmp, job)
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
    if a.stage == "M":
        vs = DATA / "stage_v_summary.json"
        if not vs.exists() or json.loads(vs.read_text()).get("passes") is not True:
            raise SystemExit("Stage V has not passed; Stage M not started")
    out_dir = stage_dir(a.stage)
    out_dir.mkdir(parents=True, exist_ok=True)
    js = jobs(a.stage)
    launch = dict(stage=a.stage, commit=commit, runs=len(js), start=time.time(), workers=a.workers, G=G)
    _atomic_write_text(out_dir / "launch.json", json.dumps(launch))
    print(f"stage {a.stage}: {len(js)} runs, commit {commit}", flush=True)
    with Pool(min(a.workers, len(js))) as p:
        for name, status in p.imap_unordered(run_one, js):
            print(time.strftime("%H:%M:%S"), name, status, flush=True)
    print("stage complete", flush=True)


if __name__ == "__main__":
    main()
