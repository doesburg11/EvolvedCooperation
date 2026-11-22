#!/usr/bin/env python3
"""Step 0: cost calibration with version A only (README "Steps").

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.learning.utils.run_step0
"""
from __future__ import annotations

import csv
import json
import math
from multiprocessing import Pool
from pathlib import Path

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.learning.utils.run_step0")

from ...config.kin_selection_config import resolve_config
from ..config.learning_config import DATA_DIR, LEARNING, STEP0_BAND, STEP0_COSTS, STEP0_SEEDS, STEP0_TARGET, WORKERS
from ..learning_model import run_version


def last_finite(values) -> float:
    for v in reversed(values):
        if v is not None and math.isfinite(float(v)):
            return float(v)
    return math.nan


def existing_success(cfg, payload) -> bool:
    """The success rule of kin_selection/utils/proof_of_mechanism.py, unchanged."""
    s, h = payload["summary"], payload["history"]
    trait, inv = float(s["helping_trait_change"]), float(s["helping_invasion_frequency_change"])
    return bool(
        math.isfinite(trait) and math.isfinite(inv)
        and trait >= float(cfg["proof_success_min_trait_increase"])
        and inv >= float(cfg["proof_success_min_invasion_frequency_increase"])
        and last_finite(h["hamilton_margin_proxy"]) > float(cfg["proof_success_min_hamilton_margin_proxy"])
        and int(s["final_population"]) >= int(cfg["proof_success_min_final_population"])
    )


def run_one(job):
    cost, seed = job
    cfg = resolve_config({"random_seed": seed, "care_cost_per_unit": cost, "write_latest_run": False})
    payload = run_version(cfg, "A", LEARNING)
    s = payload["summary"]
    return {"cost": cost, "seed": seed, "success": int(existing_success(cfg, payload)),
            "helping_trait_change": float(s["helping_trait_change"]),
            "invasion_frequency_change": float(s["helping_invasion_frequency_change"]),
            "final_population": int(s["final_population"])}


def choose_cost(rates: dict[float, float]):
    """c* = cost whose success rate is closest to STEP0_TARGET, within STEP0_BAND; highest cost on a tie."""
    lo, hi = STEP0_BAND
    inside = [(abs(r - STEP0_TARGET), -c, c) for c, r in rates.items() if lo <= r <= hi]
    return min(inside)[2] if inside else None


def main() -> None:
    out = Path(DATA_DIR)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(c, s) for c in STEP0_COSTS for s in STEP0_SEEDS]
    with Pool(WORKERS) as pool:
        rows = pool.map(run_one, jobs)
    with open(out / "step0_runs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    rates = {c: sum(r["success"] for r in rows if r["cost"] == c) / len(STEP0_SEEDS) for c in STEP0_COSTS}
    c_star = choose_cost(rates)
    result = {"success_rate_by_cost": {str(c): r for c, r in rates.items()}, "c_star": c_star}
    (out / "step0_result.json").write_text(json.dumps(result, indent=1))
    for c in STEP0_COSTS:
        print(f"cost {c:<5}: success {rates[c]:.2f}")
    print("c* =", c_star if c_star is not None else "NONE (no cost in band: stop and report)")


if __name__ == "__main__":
    main()
