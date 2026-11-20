#!/usr/bin/env python3
"""Step R7 pilot (README pre-registration 20bbece): juveniles cannot breed (breeding age a_b, D-E base).

Seeds 0-1 of the test arm (b/c 6, local) at a_b = 2 and a_b = 1, 6000 steps. Same counts, viability, vacancy rule
and fail-closed selection as the R6 pilot (run_r6_pilot.level_outcome). Complete = exactly one finished result per
(level, seed) and no other rows. The chosen level is written (r7_pilot_selection.json) before any h is reported.
Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r7_pilot
"""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m "
                     "ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r7_pilot")

from ..config.ladder_config import DATA_DIR, K0_STEPS, R7_LEVELS, R7_PILOT_SEEDS, r7_pilot_arms
from . import run_r1
from .run_dr4 import write_union_csv
from .run_r6_pilot import level_outcome

INCOMPLETE = {"complete": False, "chosen_a_b": None, "decision": "pilot incomplete: rerun or decide with the user",
              "levels": {}}


def arm_name(a_b) -> str:
    return f"J6-local-a{a_b}"


def select(rows) -> dict:
    """rows: all pilot rows. Incomplete unless exactly one row per (level, seed) and nothing else."""
    want = sorted((arm_name(a), s) for a in R7_LEVELS for s in R7_PILOT_SEEDS)
    if any(isinstance(r["seed"], bool) or int(r["seed"]) != r["seed"] for r in rows):   # no truncated seeds
        return dict(INCOMPLETE)
    got = sorted((r["arm"], int(r["seed"])) for r in rows)
    if got != want:
        return dict(INCOMPLETE)
    levels = {str(a): level_outcome([r for r in rows if r["arm"] == arm_name(a)]) for a in R7_LEVELS}
    chosen = next((a for a in sorted(R7_LEVELS, reverse=True) if levels[str(a)]["reason"] == "passed"), None)
    if chosen is not None:
        decision = f"pilot passed: main run at a_b = {chosen}"
    elif not any(v["viable"] for v in levels.values()):
        decision = "not viable"
    else:
        decision = "vacant space rare at these levels"
    return {"complete": True, "chosen_a_b": chosen, "decision": decision, "levels": levels}


def ratio(rows, num, den):
    n = sum(r[num] for r in rows)
    d = sum(r[den] for r in rows)
    return n / d if d else None


def main():
    out = Path(DATA_DIR)
    sel_path, verdict_path = out / "r7_pilot_selection.json", out / "r7_pilot_verdict.json"
    sel_path.write_text(json.dumps(INCOMPLETE, indent=1))                 # fail closed
    verdict_path.unlink(missing_ok=True)
    (out / "r7_pilot_runs.csv").unlink(missing_ok=True)                    # no stale h from an earlier run
    arms = r7_pilot_arms()
    jobs = [(a, m, u, s, K0_STEPS) for a, (m, u) in arms.items() for s in R7_PILOT_SEEDS]
    with Pool(len(jobs)) as pool:
        rows = pool.map(run_r1.run_one, jobs)
    sel = select(rows)
    sel_path.write_text(json.dumps(run_r1.json_safe(sel), indent=1, allow_nan=False))
    print("SELECTION:", json.dumps(run_r1.json_safe(sel), indent=1), flush=True)
    write_union_csv(out / "r7_pilot_runs.csv", rows)
    record = {}
    for a in R7_LEVELS:
        v = [r for r in rows if r["arm"] == arm_name(a)]
        d = {"final_h_per_seed": [r["final_mean_trait"] for r in v],
             "age_blocked_share_of_failed_fills": ratio(v, "n_fill_age_blocked", "n_fill_emptied"),
             "births_per_adult_step": ratio(v, "births_adult_sum", "n_adult"),
             "births_per_juvenile_step": ratio(v, "births_juvenile_sum", "n_juvenile"),
             "mean_parent_age": ratio(v, "parent_age_sum", "n_births_age"),
             "empty_neighbours_per_empty_site": ratio(v, "empty_nb_sum", "n_empty_end")}
        for k in ("births_per_occupant", "juvenile_fraction", "mean_age", "starve_added_share", "frac_ineligible",
                  "starve_rate_recent_parents", "S_juvenile", "G_mean"):
            vals = np.asarray([r.get(k, np.nan) for r in v], dtype=float)
            d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
        record[str(a)] = d
    verdict = {**sel, "after_selection_descriptive": record}
    verdict_path.write_text(json.dumps(run_r1.json_safe(verdict), indent=1, allow_nan=False))
    print(json.dumps(run_r1.json_safe(record), indent=1))


if __name__ == "__main__":
    main()
