#!/usr/bin/env python3
"""Step R6 pilot (README pre-registration 8e056ea): the newborn's endowment paid by its parent.

Seeds 0-1 of the test arm (b/c 6, local) at q = 1 and q = 0.5, 6000 steps. Per level, pooled over the window
(payoff states after 1000-5999 updates) and both seeds: window occupancy = occupied site-steps / all site-steps (start
of step), fill failure = sites left empty / sites that needed a fill. Viable: no extinction and final occupancy >= 0.5
in both seeds. Vacant space: fill failure >= 5% or window occupancy <= 0.97 (fill failure undefined without fills:
occupancy decides). Main-run level: q = 1 if viable with vacant space, else q = 0.5 if that is, else none.
The chosen level is written (r6_pilot_selection.json) before any h is reported or written (the workers compute h
along with everything else; it is not read before the selection is written). A failed or incomplete pilot leaves an
"incomplete" selection file, never an earlier passing one. Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r6_pilot
"""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m "
                     "ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r6_pilot")

from ..config.ladder_config import (
    DATA_DIR, K0_STEPS, R6_MAX_OCCUPANCY, R6_MIN_FILL_FAILURE, R6_MIN_FINAL_OCCUPANCY, R6_PILOT_SEEDS,
    R6_Q_LEVELS, r6_pilot_arms,
)
from . import run_r1
from .run_dr4 import write_union_csv

H_KEYS = ("final_mean_trait", "traj_every_50", "success", "sustained_success", "neighbour_h_corr")


def level_outcome(rows) -> dict:
    """Viability and vacancy for one level from its pilot rows (h is not read)."""
    occ_steps = sum(int(r["occ_site_steps"]) for r in rows)
    site_steps = sum(int(r["site_steps"]) for r in rows)
    need = sum(int(r["n_fill_needed"]) for r in rows)
    emptied = sum(int(r["n_fill_emptied"]) for r in rows)
    occupancy = occ_steps / site_steps if site_steps else None
    fill_failure = emptied / need if need else None
    viable = all(not int(r["extinct"]) and float(r["final_occupancy"]) >= R6_MIN_FINAL_OCCUPANCY for r in rows)
    vacant = ((fill_failure is not None and fill_failure >= R6_MIN_FILL_FAILURE)
              or (occupancy is not None and occupancy <= R6_MAX_OCCUPANCY))
    reason = "not viable" if not viable else ("passed" if vacant else "vacant space rare")
    return {"window_occupancy": occupancy, "fill_failure": fill_failure, "fills_needed": need,
            "fills_emptied": emptied, "occupied_site_steps": occ_steps, "site_steps": site_steps,
            "final_occupancy_per_seed": [float(r["final_occupancy"]) for r in rows],
            "extinct_per_seed": [int(r["extinct"]) for r in rows],
            "viable": viable, "vacant_space": bool(vacant), "reason": reason}


def select(rows_by_level: dict) -> dict:
    """rows_by_level: q -> rows. Incomplete (wrong level set or seed roster) -> no level chosen."""
    if sorted(rows_by_level) != sorted(R6_Q_LEVELS):
        return {"complete": False, "chosen_q": None, "decision": "pilot incomplete: rerun or decide with the user",
                "levels": {}}
    for q, rows in rows_by_level.items():
        if sorted(int(r["seed"]) for r in rows) != sorted(R6_PILOT_SEEDS):
            return {"complete": False, "chosen_q": None, "decision": "pilot incomplete: rerun or decide with the user",
                    "levels": {}}
    levels = {f"{q:g}": level_outcome(rows) for q, rows in rows_by_level.items()}
    chosen = next((q for q in sorted(rows_by_level, reverse=True) if levels[f"{q:g}"]["reason"] == "passed"), None)
    if chosen is not None:
        decision = f"pilot passed: main run at q = {chosen:g}"
    elif not any(v["viable"] for v in levels.values()):
        decision = "not viable"
    else:
        decision = "vacant space rare at these levels" if all(
            v["reason"] != "passed" for v in levels.values()) else "no level chosen"
    return {"complete": True, "chosen_q": chosen, "decision": decision, "levels": levels}


def main():
    out = Path(DATA_DIR)
    sel_path, verdict_path = out / "r6_pilot_selection.json", out / "r6_pilot_verdict.json"
    incomplete = {"complete": False, "chosen_q": None, "decision": "pilot incomplete: rerun or decide with the user",
                  "levels": {}}
    # fail closed (Codex R6 review): a failed run must not leave an earlier passing selection behind
    sel_path.write_text(json.dumps(incomplete, indent=1))
    verdict_path.unlink(missing_ok=True)
    arms = r6_pilot_arms()
    jobs = [(a, m, u, s, K0_STEPS) for a, (m, u) in arms.items() for s in R6_PILOT_SEEDS]
    with Pool(len(jobs)) as pool:
        rows = pool.map(run_r1.run_one, jobs)
    by_level = {q: [r for r in rows if r["arm"] == f"T6-local-q{q:g}"] for q in R6_Q_LEVELS}
    sel = select(by_level)
    # the level choice is fixed and written before any h is looked at
    sel_path.write_text(json.dumps(run_r1.json_safe(sel), indent=1, allow_nan=False))
    print("SELECTION:", json.dumps(run_r1.json_safe(sel), indent=1), flush=True)
    write_union_csv(out / "r6_pilot_runs.csv", rows)
    record = {}
    for q, v in by_level.items():
        d = {"final_h_per_seed": [r["final_mean_trait"] for r in v]}
        for k in ("births_per_occupant", "starve_added_share", "starve_rate_recent_parents", "frac_ineligible",
                  "frac_overdraft_recent_parents", "S_juvenile", "G_mean", "mean_age", "juvenile_fraction"):
            vals = np.asarray([r.get(k, np.nan) for r in v], dtype=float)
            d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
        nb = sum(r["n_births"] for r in v)
        d["frac_births_by_dying_parents"] = sum(r["births_by_dying_parents"] for r in v) / nb if nb else None
        d["paid_per_birth"] = sum(r["paid_total"] for r in v) / nb if nb else None
        record[f"{q:g}"] = d
    verdict = {**sel, "after_selection_descriptive": record}
    verdict_path.write_text(json.dumps(run_r1.json_safe(verdict), indent=1, allow_nan=False))
    print(json.dumps(run_r1.json_safe(record), indent=1))


if __name__ == "__main__":
    main()
