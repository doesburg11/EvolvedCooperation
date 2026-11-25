#!/usr/bin/env python3
"""Stage 1 (rung 4) of the Taylor-Davies et al. (2024) replication (PREREGISTRATION_DRAFT.md).

Phase A: feeding-enabled runs, seeds 0-4 at the three infant-move levels (15 runs), then the registered interim kill
check. Phase B (only if the check passes): feeding-enabled seeds 5-9 and all 30 feeding-disabled runs. Four runs at a
time (the GPU's measured limit). Each run is a separate process (run_feeding.py) writing its own result JSON; a run
whose JSON exists is not rerun, so an interrupted stage can be resumed.

  ~/simulation_results/altruistic_feeding/venv_050/bin/python run_stage1.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = Path(os.path.expanduser("~/simulation_results/altruistic_feeding/stage1"))
LEVELS = [0.1, 0.5, 1.0]
SEEDS_A, SEEDS_B = list(range(5)), list(range(5, 10))
ENABLED = dict(steps=250_000, window=25_000)
DISABLED = dict(steps=100_000, window=10_000)
WORKERS = 4


def result_path(level, seed, feeding):
    return OUT / f"result_move{level}_seed{seed}_feed{feeding}.json"


def valid_result(level, seed, feeding):
    """A result counts only if it parses, matches the run's identity and design, and is complete."""
    rp = result_path(level, seed, feeding)
    if not rp.exists():
        return False
    try:
        r = json.loads(rp.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    p = ENABLED if feeding else DISABLED
    return (r.get("level") == level and r.get("seed") == seed and r.get("feeding") == feeding
            and r.get("steps") == p["steps"] and r.get("window") == p["window"] and r.get("complete") is True)


def run_one(job):
    level, seed, feeding = job
    rp = result_path(level, seed, feeding)
    if valid_result(level, seed, feeding):
        return job, "exists"
    p = ENABLED if feeding else DISABLED
    log = OUT / "logs" / f"move{level}_seed{seed}_feed{feeding}.log"
    cmd = [sys.executable, str(HERE / "run_feeding.py"), "--level", str(level), "--seed", str(seed),
           "--feeding", str(feeding), "--steps", str(p["steps"]), "--window", str(p["window"]), "--out", str(OUT)]
    with open(log, "w") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    return job, ("ok" if r.returncode == 0 and valid_result(*job) else f"FAILED rc={r.returncode}")


def run_batch(jobs, label):
    print(f"{time.strftime('%Y-%m-%d %H:%M')} {label}: {len(jobs)} runs", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        for job, status in ex.map(run_one, jobs):
            print(f"{time.strftime('%Y-%m-%d %H:%M')}  {job} {status}", flush=True)
    missing = [j for j in jobs if not valid_result(*j)]
    if missing:
        raise SystemExit(f"{label}: runs without results {missing}; rerun this script to resume")


def interim_check():
    """Registered rule (A0): after phase A, stop if the OLS slope of log(1 + amount) on the infant-move level is >= 0
    (amount does not rise as infants become less able to move). Inclusion: runs not extinct with amount defined.
    The sign rule is applied only if the slope is estimable (every level has >= 3 included runs and the outcome is not
    constant); otherwise Stage 1 continues and the check is reported as not estimable."""
    xs, ys = [], []
    for lv in LEVELS:
        for s in SEEDS_A:
            r = json.loads(result_path(lv, s, 1).read_text())
            if r.get("extinct_at") is None and r.get("amount") is not None:
                xs.append(lv)
                ys.append(float(np.log1p(r["amount"])))
    per_level = {str(lv): xs.count(lv) for lv in LEVELS}
    if min(per_level.values()) < 3 or len(set(ys)) < 2:
        return {"slope": None, "n": len(xs), "per_level": per_level, "decision": "continue (not estimable)"}
    slope = float(np.polyfit(xs, ys, 1)[0])
    return {"slope": slope, "n": len(xs), "per_level": per_level,
            "decision": "continue" if slope < 0 else "stop (wrong sign)"}


def main():
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    run_batch([(lv, s, 1) for s in SEEDS_A for lv in LEVELS], "phase A (feeding enabled, seeds 0-4)")
    chk = interim_check()
    (OUT / "interim_check.json").write_text(json.dumps(chk, indent=1))
    print("interim check:", chk, flush=True)
    if chk["decision"] != "continue":
        print("Stage 1 stopped at the interim check: not replicated (stopped at interim).", flush=True)
        return
    jobs = [(lv, s, 1) for s in SEEDS_B for lv in LEVELS] + [(lv, s, 0) for s in SEEDS_A + SEEDS_B for lv in LEVELS]
    run_batch(jobs, "phase B (enabled seeds 5-9, all disabled)")
    print("Stage 1 runs complete.", flush=True)


if __name__ == "__main__":
    main()
