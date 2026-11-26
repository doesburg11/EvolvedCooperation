"""Runner for the Kanwal-Gardner kin-selection test (PREREG_KIN_TEST.md).

Stage V (port validation): the authors' model and start (random z), all 25 grid cells, seed 1.
Stage M (test): cells (n, c) in {(2, 0.8), (5, 0.8)}; arms T (authors' model), X (juveniles shuffled across
patches before helping), F (fixed, density-independent dispersal); all from the no-helping start (z = 0);
seeds 100-109, shared across arms. Stage M refuses to start unless data/stage_v_summary.json says Stage V passed
for the frozen Stage V code (kg_model_stage_v.py, hash STAGE_V_SHA) and the current model's T and F paths are
bit-identical to it on short runs (amendment A1: only the X arm's shuffle implementation changed). Stage M starts
the X runs (the slowest) first.

Usage: python -m ecological_models.density_dependent_dispersal.run_test {V|M} [--workers 30]
Raw output (one .npz per run, float32 per-generation arrays plus a JSON manifest) goes to
~/simulation_results/kg_kin_test/stage_{v,m}/, outside the repository. Finished runs are validated and skipped on
restart; a file that does not validate stops the runner. A crash in any run stops the stage (registered kill rule).
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
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
STAGE_V_SHA = "8347eda93788f762"   # kg_model.py at 532611c, the code that passed Stage V
ARRAYS = ("b1", "b2", "z", "z_median", "d_mean", "d_sum", "d_rows", "empty", "survivors", "dispersers",
          "cost_z", "total_z")


def git_state():
    root = HERE.parents[1]
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--",
                            "ecological_models/density_dependent_dispersal"],
                           capture_output=True, text=True).stdout
    return commit, dirty.strip() == ""


def model_sha(name="kg_model.py"):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()[:16]


def stage_sha(stage):
    """Model code hash a stage's runs must carry: Stage V runs the frozen Stage V code, Stage M the current model."""
    return STAGE_V_SHA if stage == "V" else model_sha()


def stage_model(stage):
    from ecological_models.density_dependent_dispersal import kg_model, kg_model_stage_v
    return kg_model_stage_v if stage == "V" else kg_model


def check_equivalence():
    """Raise unless the current model's T and F paths are bit-identical to the frozen Stage V code (both Stage M
    cells, two seeds, 30 generations at full size)."""
    K, V = stage_model("M"), stage_model("V")
    for n, c in M_CELLS:
        for arm in ("T", "F"):
            for seed in (100, 101):
                kw = dict(G=30, seed=seed, init_z="zero", **ARMS[arm])     # the runner's own arm settings
                a, b = K.run(n, c, **kw), V.run(n, c, **kw)
                if sorted(a) != sorted(b):
                    raise SystemExit(f"arm {arm}: output keys differ from the Stage V code")
                for key in a:
                    x, y = np.asarray(a[key]), np.asarray(b[key])
                    if x.dtype != y.dtype or x.shape != y.shape or x.tobytes() != y.tobytes():
                        raise SystemExit(f"arm {arm} n{n} seed {seed}: {key} differs from the Stage V code")


def stage_dir(stage):
    return RAW / ("stage_v" if stage == "V" else "stage_m")


def jobs(stage):
    if stage == "V":
        return [dict(stage="V", name=f"n{n}_c{c}", n=n, c=c, seed=1, arm="T", init_z="random") for n, c in V_CELLS]
    return [dict(stage="M", name=f"{arm}_n{n}_c{c}_s{s}", n=n, c=c, seed=s, arm=arm, init_z="zero")
            for arm in ("X", "T", "F") for n, c in M_CELLS for s in M_SEEDS]   # X (slowest) first


def validate(path, job, sha=None):
    """Raise if the file is not a complete run of exactly this job (and, if sha is given, of this model code)."""
    with np.load(path) as f:
        meta = json.loads(str(f["meta"]))
        for key in ("stage", "name", "n", "c", "seed", "arm", "init_z"):
            if meta[key] != job[key]:
                raise ValueError(f"{path.name}: meta {key}={meta[key]!r}, expected {job[key]!r}")
        if meta["G"] != G:
            raise ValueError(f"{path.name}: G={meta['G']}")
        if sha is not None and meta.get("model_sha") != sha:
            raise ValueError(f"{path.name}: model_sha {meta.get('model_sha')} != current {sha}")
        for a in ARRAYS:
            if f[a].shape != (G + 1,):
                raise ValueError(f"{path.name}: {a} shape {f[a].shape}")
            vals = f[a] if a in ("b1", "b2", "z", "z_median") else f[a][1:]   # generation 0 has no step stats
            if not np.isfinite(vals).all():
                raise ValueError(f"{path.name}: non-finite {a}")
        if (f["d_rows"][1:] <= 0).any():
            raise ValueError(f"{path.name}: a generation with no surviving patch")
    return meta


def _atomic_write_text(path, text):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def run_one(job):
    K = stage_model(job["stage"])
    out_dir = stage_dir(job["stage"])
    final = out_dir / f"{job['name']}.npz"
    if final.exists():
        validate(final, job, job["model_sha"])
        return job["name"], "skipped (valid)"
    prog = out_dir / f"{job['name']}.progress"
    t0 = time.time()
    _atomic_write_text(prog, "0 0.0\n")     # heartbeat from dispatch on

    def progress(g):
        if g % 100 == 0:
            _atomic_write_text(prog, f"{g} {time.time() - t0:.1f}\n")

    arm = ARMS[job["arm"]]
    o = K.run(job["n"], job["c"], G=G, seed=job["seed"], dd=arm["dd"], shuffle=arm["shuffle"],
              init_z=job["init_z"], progress=progress)
    meta = dict(job, G=G, wall_s=time.time() - t0)   # job carries commit and model_sha from the launch
    tmp = out_dir / f"{job['name']}.{os.getpid()}.partial.npz"
    np.savez_compressed(tmp, **{a: np.asarray(o[a], np.float32) for a in ARRAYS},
                        final_breeders=o["final_breeders"].astype(np.float32), meta=json.dumps(meta))
    validate(tmp, job, job["model_sha"])
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
    if model_sha("kg_model_stage_v.py") != STAGE_V_SHA:
        raise SystemExit("kg_model_stage_v.py is not the frozen Stage V code")
    sha = stage_sha(a.stage)
    if a.stage == "M":
        vs = DATA / "stage_v_summary.json"
        summ = json.loads(vs.read_text()) if vs.exists() else {}
        if summ.get("passes") is not True or summ.get("G") != 20000 or summ.get("last") != 1000 \
                or summ.get("model_sha") != STAGE_V_SHA or model_sha("kg_model_stage_v.py") != STAGE_V_SHA \
                or G != 20000:
            raise SystemExit("Stage V has not passed for the frozen Stage V code at G = 20000; Stage M not started")
        for j in jobs("V"):                               # the Stage V files themselves must be there and valid
            validate(stage_dir("V") / f"{j['name']}.npz", j, STAGE_V_SHA)
        check_equivalence()
        print("T and F paths bit-identical to the Stage V code", flush=True)
    out_dir = stage_dir(a.stage)
    out_dir.mkdir(parents=True, exist_ok=True)
    lock = open(out_dir / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("another runner holds this stage")
    if a.stage == "M" and (out_dir / "launch.json").exists():
        raise SystemExit("Stage M was already launched once under amendment A1 (launch.json exists); no relaunch")
    js = [dict(j, commit=commit, model_sha=sha) for j in jobs(a.stage)]
    launch = dict(stage=a.stage, commit=commit, model_sha=sha, runs=len(js), start=time.time(), workers=a.workers,
                  G=G)
    _atomic_write_text(out_dir / "launch.json", json.dumps(launch))
    print(f"stage {a.stage}: {len(js)} runs, commit {commit}", flush=True)
    # ProcessPoolExecutor raises BrokenProcessPool if a worker dies abruptly (multiprocessing.Pool can hang);
    # any failure stops the stage (registered kill rule). Jobs are submitted in launch order.
    with ProcessPoolExecutor(max_workers=min(a.workers, len(js))) as ex:
        futs = [ex.submit(run_one, j) for j in js]
        try:
            for fut in as_completed(futs):
                name, status = fut.result()
                print(time.strftime("%H:%M:%S"), name, status, flush=True)
        except BaseException as e:
            for f in futs:
                f.cancel()
            print(time.strftime("%H:%M:%S"), "STAGE FAILED:", repr(e), flush=True)
            for proc in list(getattr(ex, "_processes", {}).values()):
                proc.terminate()
            raise SystemExit(1)
    print("stage complete", flush=True)


if __name__ == "__main__":
    main()
