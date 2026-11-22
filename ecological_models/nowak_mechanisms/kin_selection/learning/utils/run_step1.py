#!/usr/bin/env python3
"""Step 1: versions A/B/C x starts rare/weak x 40 seeds at c* with the calibrated alpha; scores T1-T3 (README).

Run from the repo root (after run_step0 and calibrate_alpha):
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.learning.utils.run_step1
"""
from __future__ import annotations

import csv
import json
import math
from multiprocessing import Pool
from pathlib import Path

from scipy.stats import fisher_exact

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.learning.utils.run_step1")

from ...config.kin_selection_config import resolve_config
from ..config.learning_config import (
    DATA_DIR,
    LEARNING,
    STARTS,
    STEP1_BASELINE_STEP,
    STEP1_MIN_EXPRESSED_INCREASE,
    STEP1_MIN_FINAL_POPULATION,
    STEP1_SEEDS,
    VERSIONS,
    WORKERS,
)
from ..learning_model import run_version


def step1_success(payload) -> tuple[bool, float]:
    expressed = payload["history"]["mean_expressed_helping"]  # index 0 = initial state, index t = after step t
    if len(expressed) <= STEP1_BASELINE_STEP:  # extinct before the baseline step: a failure
        return False, math.nan
    start, end = expressed[STEP1_BASELINE_STEP], expressed[-1]
    rise = end - start if math.isfinite(start) and math.isfinite(end) else math.nan
    ok = (math.isfinite(rise) and rise >= STEP1_MIN_EXPRESSED_INCREASE
          and int(payload["summary"]["final_population"]) >= STEP1_MIN_FINAL_POPULATION)
    return bool(ok), rise


def run_one(job):
    version, start, seed, cost, alpha = job
    cfg = resolve_config({"random_seed": seed, "care_cost_per_unit": cost, "write_latest_run": False,
                          **STARTS[start]})
    payload = run_version(cfg, version, {**LEARNING, "alpha": alpha})
    ok, rise = step1_success(payload)
    s, h = payload["summary"], payload["history"]
    return {"version": version, "start": start, "seed": seed, "success": int(ok), "expressed_rise": rise,
            "final_expressed": h["mean_expressed_helping"][-1], "final_mean_gene": float(s["final_mean_helping_trait"]),
            "gene_change": float(s["helping_trait_change"]), "final_population": int(s["final_population"])}


def score(rows) -> dict:
    n = len(STEP1_SEEDS)
    wins = {}
    for v in VERSIONS:
        for st in STARTS:
            cell = [r for r in rows if r["version"] == v and r["start"] == st]
            if "seed" in rows[0] and sorted(r["seed"] for r in cell) != sorted(STEP1_SEEDS):
                raise ValueError(f"cell {v}/{st} does not have exactly one row per configured seed")
            if len(cell) != n:
                raise ValueError(f"cell {v}/{st} has {len(cell)} rows, expected {n}")
            wins[(v, st)] = sum(int(r["success"]) for r in cell)
    rate = {key: w / n for key, w in wins.items()}
    t1 = all(rate[("B", st)] <= 0.10 for st in STARTS)
    t2 = rate[("C", "rare")] >= rate[("A", "rare")] - 0.15 and rate[("C", "rare")] >= rate[("B", "rare")] + 0.30
    c_s, a_s = wins[("C", "weak")], wins[("A", "weak")]
    p = float(fisher_exact([[c_s, n - c_s], [a_s, n - a_s]], alternative="greater")[1])
    t3 = rate[("C", "weak")] - rate[("A", "weak")] >= 0.20 and p < 0.05
    return {"success_rate": {f"{v}_{st}": r for (v, st), r in rate.items()},
            "T1": t1, "T2": t2, "T3": t3, "T3_fisher_p": p}


def main() -> None:
    out = Path(DATA_DIR)
    cost = json.loads((out / "step0_result.json").read_text())["c_star"]
    alpha = json.loads((out / "alpha_result.json").read_text())["alpha"]
    if cost is None or alpha is None:
        raise SystemExit(f"c* = {cost}, alpha = {alpha}: calibration did not pass, the design says stop")
    jobs = [(v, st, s, cost, alpha) for v in VERSIONS for st in STARTS for s in STEP1_SEEDS]
    with Pool(WORKERS) as pool:
        rows = pool.map(run_one, jobs)
    with open(out / "step1_runs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    verdict = {"c_star": cost, "alpha": alpha, **score(rows)}
    (out / "step1_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    main()
