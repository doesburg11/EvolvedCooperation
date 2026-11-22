#!/usr/bin/env python3
"""Step R5a exposure pilot (README pre-registration 51821a1): seeds 0-1 of A6-local and A6-local-lean, 6000 steps.

Exposure: occupant-steps (payoff states after 1000-5999 updates, pooled over both seeds) in which the neighbourhood
harvest g differs by more than 0.01 from R4's own-site rule min(r, 0.2) in the same state. Kill rule: exposure
strictly below 2% in both arms -> "below the pilot exposure threshold" (main run not done); an arm with no
occupant-steps is void and the pilot is decided with the user. Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r5a_pilot
"""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m "
                     "ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r5a_pilot")

from ..config.ladder_config import (
    DATA_DIR, K0_STEPS, R5A_MIN_EXPOSURE, R5A_PILOT_ARMS, R5A_PILOT_SEEDS, r5a_arms,
)
from . import run_r1
from .run_dr4 import write_union_csv

DESC_KEYS = ("occupancy", "frac_fill_emptied", "harvest_mean", "harvest_near_empty", "harvest_away_empty",
             "G_mean", "starve_added_share", "frac_ineligible")      # exposure: pooled counts only (Codex review)


def exposure(rows) -> dict:
    n_occ = int(sum(r["n_occ_start"] for r in rows))
    n_exp = int(sum(r["n_exposed"] for r in rows))
    n_near = int(sum(r["n_near_empty"] for r in rows))
    return {"occupant_steps": n_occ, "exposed": n_exp, "near_empty": n_near,
            "exposure": n_exp / n_occ if n_occ else None, "near_empty_frac": n_near / n_occ if n_occ else None,
            "void": n_occ == 0}


def decide(per_arm: dict) -> dict:
    if any(v["void"] for v in per_arm.values()):
        return {"decision": "void arm: decided with the user", "main_run": None}
    below = all(v["exposure"] < R5A_MIN_EXPOSURE for v in per_arm.values())       # at the bar passes
    if below:
        return {"decision": "below the pilot exposure threshold", "main_run": False}
    return {"decision": "pilot passed", "main_run": True}


def main():
    out = Path(DATA_DIR)
    cfg = r5a_arms(1)
    jobs = [(a, *cfg[a], s, K0_STEPS) for a in R5A_PILOT_ARMS for s in R5A_PILOT_SEEDS]
    with Pool(len(jobs)) as pool:
        rows = pool.map(run_r1.run_one, jobs)
    write_union_csv(out / "r5a_pilot_runs.csv", rows)
    per_arm, desc = {}, {}
    for a in R5A_PILOT_ARMS:
        v = [r for r in rows if r["arm"] == a]
        if sorted(r["seed"] for r in v) != sorted(R5A_PILOT_SEEDS):
            raise ValueError(f"{a}: wrong seeds")
        per_arm[a] = exposure(v)
        d = {"final_h_per_seed": [r["final_mean_trait"] for r in v],
             "exposure_per_seed": [r["n_exposed"] / r["n_occ_start"] if r["n_occ_start"] else None for r in v],
             "final_occupancy_per_seed": [r["final_occupancy"] for r in v]}
        for k in DESC_KEYS:
            vals = np.asarray([r.get(k, np.nan) for r in v], dtype=float)
            d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
        desc[a] = d
    verdict = {"min_exposure": R5A_MIN_EXPOSURE, "w_own": cfg[R5A_PILOT_ARMS[0]][0]["care_forage_own"],
               "exposure": per_arm, **decide(per_arm), "descriptive": desc}
    (out / "r5a_pilot_verdict.json").write_text(json.dumps(run_r1.json_safe(verdict), indent=1, allow_nan=False))
    print(json.dumps(run_r1.json_safe(verdict), indent=1))


if __name__ == "__main__":
    main()
