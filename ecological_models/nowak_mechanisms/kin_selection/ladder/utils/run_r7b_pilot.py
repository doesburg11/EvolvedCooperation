#!/usr/bin/env python3
"""Step R7b pilot (README pre-registration 6d79213): R7 at a_b = 2 with adult founders (age 2), data-suggested.

Seeds 20-21 of the test arm B6-local (b/c 6, local), 6000 steps. Same counts, viability and vacancy rule as the R6/R7
pilots (run_r6_pilot.level_outcome). Complete = exactly one finished result per seed and no other rows. The decision
is written (r7b_pilot_selection.json) before any h is reported; a failed run leaves an "incomplete" selection.
Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r7b_pilot
"""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m "
                     "ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r7b_pilot")

from ..config.ladder_config import (
    DATA_DIR, K0_STEPS, K1_DIAG_FROM, R7B_PILOT_SEEDS, R7B_STARTUP_STEPS, r7b_pilot_arms,
)
from . import run_r1
from .run_dr4 import write_union_csv
from .run_r6_pilot import level_outcome
from .run_r7_pilot import ratio

ARM = "B6-local"
INCOMPLETE = {"complete": False, "passed": None, "decision": "pilot incomplete: no verdict, no main attempt",
              "level": {}}


N_SITES = 576
EXPECTED_SITE_STEPS = (K0_STEPS - K1_DIAG_FROM) * N_SITES          # a finished run covers the whole window


def select(rows, expected_site_steps=EXPECTED_SITE_STEPS) -> dict:
    if any(isinstance(r["seed"], bool) or int(r["seed"]) != r["seed"] for r in rows):
        return dict(INCOMPLETE)
    if any(int(r["site_steps"]) != expected_site_steps for r in rows):   # Codex R7b review: short windows
        return dict(INCOMPLETE)
    if sorted((r["arm"], int(r["seed"])) for r in rows) != sorted((ARM, s) for s in R7B_PILOT_SEEDS):
        return dict(INCOMPLETE)
    o = level_outcome(rows)
    passed = o["reason"] == "passed"
    decision = "pilot passed: main run" if passed else o["reason"]
    return {"complete": True, "passed": passed, "decision": decision, "level": o}


def main():
    out = Path(DATA_DIR)
    sel_path, verdict_path = out / "r7b_pilot_selection.json", out / "r7b_pilot_verdict.json"
    sel_path.write_text(json.dumps(INCOMPLETE, indent=1))                 # fail closed
    verdict_path.unlink(missing_ok=True)
    (out / "r7b_pilot_runs.csv").unlink(missing_ok=True)
    m, u = r7b_pilot_arms()[ARM]
    jobs = [(ARM, m, u, s, K0_STEPS) for s in R7B_PILOT_SEEDS]
    with Pool(len(jobs)) as pool:
        rows = pool.map(run_r1.run_one, jobs)
    sel = select(rows)
    sel_path.write_text(json.dumps(run_r1.json_safe(sel), indent=1, allow_nan=False))
    print("SELECTION:", json.dumps(run_r1.json_safe(sel), indent=1), flush=True)
    if not sel["complete"]:                                          # no h, no verdict for an incomplete pilot
        return
    write_union_csv(out / "r7b_pilot_runs.csv", rows)
    d = {"final_h_per_seed": [r["final_mean_trait"] for r in rows],
         "first_empty_update_per_seed": [r["first_empty_update"] for r in rows],
         "startup_occupancy_per_seed": {str(r["seed"]): [r[f"occ_after_{t}"] for t in R7B_STARTUP_STEPS] for r in rows},
         "per_seed_fill_failure": [r["n_fill_emptied"] / r["n_fill_needed"] if r["n_fill_needed"] else None
                                   for r in rows],
         "per_seed_window_occupancy": [r["occ_site_steps"] / r["site_steps"] if r["site_steps"] else None
                                       for r in rows],
         "age_blocked_share_of_failed_fills": ratio(rows, "n_fill_age_blocked", "n_fill_emptied"),
         "births_per_adult_step": ratio(rows, "births_adult_sum", "n_adult"),
         "mean_parent_age": ratio(rows, "parent_age_sum", "n_births_age"),
         "empty_neighbours_per_empty_site": ratio(rows, "empty_nb_sum", "n_empty_end")}
    for k in ("births_per_occupant", "juvenile_fraction", "mean_age", "starve_added_share", "frac_ineligible",
              "starve_rate_recent_parents", "S_juvenile", "G_mean"):
        vals = np.asarray([r.get(k, np.nan) for r in rows], dtype=float)
        d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
    verdict = {**sel, "startup_steps": list(R7B_STARTUP_STEPS), "after_selection_descriptive": d}
    verdict_path.write_text(json.dumps(run_r1.json_safe(verdict), indent=1, allow_nan=False))
    print(json.dumps(run_r1.json_safe(d), indent=1))


if __name__ == "__main__":
    main()
