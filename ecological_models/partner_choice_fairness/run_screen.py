"""Run the step-2 grid of PREREG_SCREEN.md (1,800 runs) with the registered compute kill rule.

    ./.conda/bin/python -m ecological_models.partner_choice_fairness.run_screen [--workers 28] [--smoke]

Writes data/screen_runs.csv (one row per run), data/screen_traj.npz (per-generation mean s and a) and
data/screen_status.json (complete / killed, timing). Run order is shuffled with a fixed seed. The first 60
runs are run as one batch; if their wall time projects to more than 4 h for all runs, the screen stops
there (NO VERDICT, compute) and the remaining runs are never started.
"""

import argparse
import csv
import itertools
import json
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np

from ecological_models.partner_choice_fairness import market

TS = (1, 5, 20, 50, 100)
HS = (0.0, 0.1, 0.3)
ARMS = (True, False)
SEEDS = range(20)
KILL_AFTER = 60
KILL_HOURS = 4.0
DATA = Path(__file__).resolve().parent / "data"


def grid():
    return list(itertools.product(TS, HS, market.STARTS, ARMS, SEEDS))


def _one(args):
    T, h, start, choice, seed, gens = args
    summary, ms, ma = market.run(T, h, start, choice, seed, gens=gens)
    summary["gens"] = gens
    return summary, ms.astype(np.float32), ma.astype(np.float32)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=28)
    p.add_argument("--smoke", action="store_true", help="30 generations, outputs to data/smoke_*")
    args = p.parse_args(argv)
    gens = 30 if args.smoke else market.G
    prefix = "smoke_" if args.smoke else "screen_"
    jobs = [(*j, gens) for j in grid()]
    random.Random(12345).shuffle(jobs)
    market.run(1, 0.0, "fair", True, 0, gens=2)  # compile once before forking
    DATA.mkdir(exist_ok=True)
    results = []
    t0 = time.time()
    killed = False
    with ProcessPoolExecutor(args.workers) as ex:
        results += list(ex.map(_one, jobs[:KILL_AFTER]))
        el = time.time() - t0
        proj = el * len(jobs) / KILL_AFTER / 3600
        print(f"after {KILL_AFTER} runs: {el / 60:.2f} min, projected {proj:.3f} h", flush=True)
        if proj > KILL_HOURS and not args.smoke:
            print("KILL RULE: projected wall time exceeds 4 h -> NO VERDICT (compute)", flush=True)
            killed = True
        else:
            results += list(ex.map(_one, jobs[KILL_AFTER:]))
    rows = [r[0] for r in results]
    trajs = {}
    for summary, ms, ma in results:
        key = f"{summary['T']}_{summary['h']}_{summary['start']}_{summary['arm']}_{summary['seed']}"
        trajs[key + "_s"] = ms
        trajs[key + "_a"] = ma
    with open(DATA / f"{prefix}runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["arm"], r["start"], r["h"], r["T"], r["seed"])))
    np.savez_compressed(DATA / f"{prefix}traj.npz", **trajs)
    wall = time.time() - t0
    status = {"complete": not killed and len(rows) == len(jobs), "killed": killed, "runs": len(rows),
              "gens": gens, "projected_hours_after_60": proj, "wall_minutes": wall / 60}
    (DATA / f"{prefix}status.json").write_text(json.dumps(status, indent=1))
    print(f"done: {len(rows)} runs in {wall / 60:.1f} min" + (" (KILLED)" if killed else ""))
    return 1 if killed else 0


if __name__ == "__main__":
    sys.exit(main())
