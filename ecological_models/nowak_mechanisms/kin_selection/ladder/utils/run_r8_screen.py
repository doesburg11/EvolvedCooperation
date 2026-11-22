#!/usr/bin/env python3
"""Step R8 Stage S (README pre-registration 852cd06): demographic screen at fixed h, before any care test.

24 jobs: d0 in {0.1, 0.2, 0.3} x g_rep in {0.5, 0.7} x h in {0, 0.6} x seeds {50, 51}, 3000 updates, local births,
attempt-1 rules (energy split, no birth cost), no mutation. A point passes if every one of its 4 runs is not extinct,
ends with occupancy >= 0.5 and has window occupancy in [0.50, 0.95]. Choice: highest d0, then lower g_rep. Complete =
exactly one finished run per job with the full window; otherwise no point is chosen. Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r8_screen
"""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m "
                     "ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r8_screen")

from ..config.ladder_config import (
    DATA_DIR, R8_D0, R8_G_REP, R8_MIN_FINAL_OCCUPANCY, R8_OCC_BOUNDS, R8_SCREEN_H, R8_SCREEN_SEEDS,
    R8_SCREEN_STEPS, R8_WINDOW_FROM, WORKERS, r8_screen_jobs,
)
from . import run_r8
from .run_dr4 import write_union_csv
from .run_r1 import json_safe

N_SITES = 576
EXPECTED_STATES = R8_SCREEN_STEPS - R8_WINDOW_FROM
EXPECTED_SITE_STEPS = EXPECTED_STATES * N_SITES
INCOMPLETE = {"complete": False, "chosen": None, "decision": "screen incomplete: rerun the same jobs", "points": {}}


def run_ok(r) -> dict:
    occ = r["occ_site_steps"] / r["site_steps"] if r["site_steps"] else None
    lo, hi = R8_OCC_BOUNDS
    ok = (not int(r["extinct"]) and float(r["final_occupancy"]) >= R8_MIN_FINAL_OCCUPANCY
          and occ is not None and lo <= occ <= hi)
    return {"seed": r["seed"], "h": r["h"], "window_occupancy": occ, "final_occupancy": r["final_occupancy"],
            "extinct": int(r["extinct"]), "first_empty_update": r["first_empty_update"], "passes": bool(ok)}


def finished(r, expected_site_steps) -> bool:
    """Exact completion fields (Codex R8 review): all updates done, the full window, integral counts."""
    def is_int(x):
        return not isinstance(x, bool) and isinstance(x, (int, np.integer))
    return (is_int(r.get("steps_done")) and r["steps_done"] == R8_SCREEN_STEPS
            and is_int(r.get("window_states")) and r["window_states"] == expected_site_steps // N_SITES
            and is_int(r.get("site_steps")) and r["site_steps"] == expected_site_steps)


def select(rows, expected_site_steps=EXPECTED_SITE_STEPS) -> dict:
    want = sorted((d, g, h, s) for d in R8_D0 for g in R8_G_REP for h in R8_SCREEN_H for s in R8_SCREEN_SEEDS)
    if any(isinstance(r["seed"], bool) or int(r["seed"]) != r["seed"] for r in rows):
        return dict(INCOMPLETE)
    got = sorted((r["d0"], r["g_rep"], r["h"], int(r["seed"])) for r in rows)
    if got != want or not all(finished(r, expected_site_steps) for r in rows):
        return dict(INCOMPLETE)
    points = {}
    for d in R8_D0:
        for g in R8_G_REP:
            runs = [run_ok(r) for r in rows if r["d0"] == d and r["g_rep"] == g]
            points[f"d{d:g}-g{g:g}"] = {"d0": d, "g_rep": g, "passes": all(x["passes"] for x in runs), "runs": runs}
    passing = [p for p in points.values() if p["passes"]]
    chosen = None
    if passing:
        best = sorted(passing, key=lambda p: (-p["d0"], p["g_rep"]))[0]
        chosen = {"d0": best["d0"], "g_rep": best["g_rep"]}
    decision = (f"point chosen: d0 = {chosen['d0']:g}, g_rep = {chosen['g_rep']:g}" if chosen
                else "no setting passed the registered R8 screen")
    return {"complete": True, "chosen": chosen, "decision": decision, "points": points}


def main():
    out = Path(DATA_DIR)
    sel_path = out / "r8_screen_selection.json"
    sel_path.write_text(json.dumps(INCOMPLETE, indent=1))                 # fail closed
    (out / "r8_screen_runs.csv").unlink(missing_ok=True)
    jobs = r8_screen_jobs()
    with Pool(min(WORKERS, len(jobs))) as pool:
        rows = pool.map(run_r8.run_one, [(a, m, u, s, R8_SCREEN_STEPS, R8_WINDOW_FROM)
                                         for a, m, u, d, g, h in jobs for s in R8_SCREEN_SEEDS])
    meta = {a: (d, g, h) for a, m, u, d, g, h in jobs}
    for r in rows:
        r["d0"], r["g_rep"], r["h"] = meta[r["arm"]]
    sel = select(rows)
    if sel["complete"]:
        write_union_csv(out / "r8_screen_runs.csv", rows)               # the run record first ...
    tmp = sel_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(json_safe(sel), indent=1, allow_nan=False))
    tmp.replace(sel_path)                                                # ... then the choice, atomically
    print(json.dumps(json_safe({k: v for k, v in sel.items() if k != "points"}), indent=1))
    for k, p in sel.get("points", {}).items():
        print(k, "passes" if p["passes"] else "fails",
              [(x["h"], x["seed"], None if x["window_occupancy"] is None else round(x["window_occupancy"], 3),
                x["extinct"]) for x in p["runs"]])


if __name__ == "__main__":
    main()
