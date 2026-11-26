"""Run the reputation grid of PREREG_REPUTATION.md (2,160 runs) with the registered compute kill rule.

    ./.conda/bin/python -m ecological_models.partner_choice_fairness.run_reputation [--workers 28] [--smoke]

Writes data/reputation_runs.csv, data/reputation_traj.npz and data/reputation_status.json. Choice arm: q x T x h
x start x seed; no-choice arm: T x h x start x seed (q has no effect there). The first 60 runs (shuffled order,
fixed seed) are one batch; if they project to more than 1 h for all runs, the run stops (NO VERDICT, compute).
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

QS = (0.0, 0.25, 0.5, 0.75, 1.0)
TS = (1, 5, 20)
HS = (0.0, 0.1)
SEEDS = range(20)
KILL_AFTER = 60
KILL_HOURS = 1.0
DATA = Path(__file__).resolve().parent / "data"


def grid():
    choice = [(q, T, h, st, True, sd) for q, T, h, st, sd in itertools.product(QS, TS, HS, market.STARTS, SEEDS)]
    no_choice = [(0.0, T, h, st, False, sd) for T, h, st, sd in itertools.product(TS, HS, market.STARTS, SEEDS)]
    return choice + no_choice


def _one(args):
    q, T, h, start, choice, seed, gens = args
    summary, ms, ma = market.run(T, h, start, choice, seed, gens=gens, q=q)
    summary["gens"] = gens
    return summary, ms.astype(np.float32), ma.astype(np.float32)


def key(r):
    return f"{r['q']}_{r['T']}_{r['h']}_{r['start']}_{r['arm']}_{r['seed']}"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=28)
    p.add_argument("--smoke", action="store_true", help="30 generations, outputs to data/smoke_reputation_*")
    args = p.parse_args(argv)
    gens = 30 if args.smoke else market.G
    prefix = "smoke_reputation_" if args.smoke else "reputation_"
    jobs = [(*j, gens) for j in grid()]
    random.Random(54321).shuffle(jobs)
    market.run(1, 0.0, "fair", True, 0, gens=2, q=0.5)  # compile once before forking
    DATA.mkdir(exist_ok=True)
    t0 = time.time()
    killed = False
    with ProcessPoolExecutor(args.workers) as ex:
        results = list(ex.map(_one, jobs[:KILL_AFTER]))
        el = time.time() - t0
        proj = el * len(jobs) / KILL_AFTER / 3600
        print(f"after {KILL_AFTER} runs: {el / 60:.2f} min, projected {proj:.3f} h", flush=True)
        if proj > KILL_HOURS and not args.smoke:
            print("KILL RULE: projected wall time exceeds 1 h -> NO VERDICT (compute)", flush=True)
            killed = True
        else:
            results += list(ex.map(_one, jobs[KILL_AFTER:]))
    rows = [r[0] for r in results]
    trajs = {}
    for summary, ms, ma in results:
        trajs[key(summary) + "_s"] = ms
        trajs[key(summary) + "_a"] = ma
    with open(DATA / f"{prefix}runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["arm"], r["q"], r["start"], r["h"], r["T"], r["seed"])))
    np.savez_compressed(DATA / f"{prefix}traj.npz", **trajs)
    wall = time.time() - t0
    status = {"complete": not killed and len(rows) == len(jobs), "killed": killed, "runs": len(rows),
              "gens": gens, "projected_hours_after_60": proj, "wall_minutes": wall / 60}
    (DATA / f"{prefix}status.json").write_text(json.dumps(status, indent=1))
    print(f"done: {len(rows)} runs in {wall / 60:.1f} min" + (" (KILLED)" if killed else ""))
    return 1 if killed else 0


if __name__ == "__main__":
    sys.exit(main())
