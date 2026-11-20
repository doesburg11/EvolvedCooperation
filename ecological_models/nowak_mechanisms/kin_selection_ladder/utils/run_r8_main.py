#!/usr/bin/env python3
"""Step R8 Stage M (README pre-registration 852cd06): the care test with parent-driven births.

Reads the Stage-S choice (r8_screen_selection.json: complete with a chosen point; otherwise refuses). Attempt 1: 8 arms
(U...) x seeds 0-19, 6000 updates, energy split; attempt 2 (U2-..., free endowment + birth cost) only if a complete
attempt 1 is local failure or comparison failed. Classification as R4 (run_r1.classify_r1, score_h2); labels:
income activation, vacancy (pooled over non-extinct test seeds; "undefined" if all extinct). An incomplete attempt gets
no classification and triggers nothing. Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r8_main
"""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m "
                     "ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r8_main")

from ..config.ladder_config import (
    DATA_DIR, R3C_MIN_OCCUPANCY, R8_D0, R8_G_REP, R8_MAIN_SEEDS, R8_MAIN_STEPS, R8_MAX_HARVEST, R8_VACANCY_FILL, R8_VACANCY_OCC,
    R8_WINDOW_FROM, SUCCESS_FINAL_MEAN_TRAIT, WORKERS, r8_arms, r8_roles,
)
from . import run_r8
from .run_step1 import corr_steps
from .run_dr4 import write_union_csv
from .run_r1 import classify_r1, json_safe, mcnemar_greater, score_h2

N_SITES = 576
EXPECTED_STATES = R8_MAIN_STEPS - R8_WINDOW_FROM


def joint_success(r) -> int:
    h, occ = r["final_mean_trait"], r["final_occupancy"]
    return int(bool(np.isfinite(h) and h >= SUCCESS_FINAL_MEAN_TRAIT and occ >= R3C_MIN_OCCUPANCY))


def finished(r) -> bool:
    is_int = lambda x: not isinstance(x, bool) and isinstance(x, (int, np.integer))
    return (len(r.get("neighbour_h_corr", [])) == len(corr_steps(R8_MAIN_STEPS))       # all H2 samples present
            and is_int(r.get("steps_done")) and r["steps_done"] == R8_MAIN_STEPS
            and is_int(r.get("window_states")) and r["window_states"] == EXPECTED_STATES
            and is_int(r.get("site_steps")) and r["site_steps"] == EXPECTED_STATES * N_SITES)


def complete(rows, arms) -> bool:
    if any(isinstance(r["seed"], bool) or int(r["seed"]) != r["seed"] for r in rows):
        return False
    want = sorted((a, s) for a in arms for s in R8_MAIN_SEEDS)
    return sorted((r["arm"], int(r["seed"])) for r in rows) == want and all(finished(r) for r in rows)


def vacancy(r) -> dict:
    ff = r["n_fill_emptied"] / r["n_fill_needed"] if r["n_fill_needed"] else None
    occ = r["occ_site_steps"] / r["site_steps"] if r["site_steps"] else None
    present = (ff is not None and ff >= R8_VACANCY_FILL) or (occ is not None and occ <= R8_VACANCY_OCC)
    return {"fill_failure": ff, "window_occupancy": occ, "vacant": bool(present)}


def vacancy_label(test_rows) -> dict:
    alive = [r for r in test_rows if not int(r["extinct"])]
    per_seed = {int(r["seed"]): vacancy(r) for r in test_rows}
    n_both = sum(1 for r in test_rows if r["success"] and not int(r["extinct"]) and per_seed[int(r["seed"])]["vacant"])
    n_vacant_alive = sum(1 for r in alive if per_seed[int(r["seed"])]["vacant"])
    if not alive:
        return {"label": "undefined", "per_seed": per_seed, "extinct_seeds": len(test_rows),
                "successes_with_vacant_space": 0, "non_extinct_seeds_with_vacant_space": 0}
    pooled = vacancy({k: sum(r[k] for r in alive) for k in ("n_fill_emptied", "n_fill_needed", "occ_site_steps",
                                                             "site_steps")})
    return {"label": "vacant space present" if pooled["vacant"] else "vacant space rare", "pooled": pooled,
            "per_seed": per_seed, "extinct_seeds": len(test_rows) - len(alive),
            "successes_with_vacant_space": n_both, "non_extinct_seeds_with_vacant_space": n_vacant_alive}


def describe(v) -> dict:
    hs = [r["final_mean_trait"] for r in v]
    d = {"successes": int(sum(r["success"] for r in v)), "extinctions": int(sum(r["extinct"] for r in v)),
         "final_h_per_seed": hs, "final_occupancy_per_seed": [r["final_occupancy"] for r in v],
         "mean_final_h": float(np.nanmean(hs)) if np.isfinite(hs).any() else None,
         "mean_final_occupancy": float(np.mean([r["final_occupancy"] for r in v]))}
    for t in (2000, 4000, 6000):
        vals = [r["traj_every_50"][t // 50 - 1] for r in v]
        d[f"mean_h_{t}"] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
    tot = lambda k: sum(r[k] for r in v)
    d["births_per_occupant_update"] = tot("n_births") / tot("n_occ_start") if tot("n_occ_start") else None
    d["window_occupancy"] = tot("occ_site_steps") / tot("site_steps") if tot("site_steps") else None
    d["fill_failure"] = tot("n_fill_emptied") / tot("n_fill_needed") if tot("n_fill_needed") else None
    d["starvation_share_of_deaths"] = tot("n_starve_added") / tot("n_deaths") if tot("n_deaths") else None
    d["claims_per_target"] = tot("n_claims") / tot("n_targets") if tot("n_targets") else None
    d["births_per_occ_low_h"] = tot("births_low_h_sum") / tot("n_low_h") if tot("n_low_h") else None
    d["births_per_occ_high_h"] = tot("births_high_h_sum") / tot("n_high_h") if tot("n_high_h") else None
    d["harvest_pooled"] = tot("harvest_total") / tot("n_occ_start") if tot("n_occ_start") else None
    for k in run_r8.MEAN_KEYS:
        vals = np.asarray([r[k] for r in v], dtype=float)
        d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
    corr = np.asarray([np.mean(r["neighbour_h_corr"]) for r in v], dtype=float)
    d["neighbour_h_corr"] = float(np.nanmean(corr)) if np.isfinite(corr).any() else None
    for t in (10, 50, 100, 500):
        d[f"occ_after_{t}"] = float(np.nanmean([r[f"occ_after_{t}"] for r in v]))
    d["first_empty_updates"] = [r["first_empty_update"] for r in v if r["first_empty_update"] >= 0]
    return d


def read_choice(out: Path):
    """The chosen point, or None for a complete screen with no passing point (a terminal outcome)."""
    sel = json.loads((out / "r8_screen_selection.json").read_text())
    if sel.get("complete") is not True:
        raise SystemExit("R8 Stage M needs a complete Stage S")
    ch = sel.get("chosen")
    if ch is None:
        return None
    if ch.get("d0") not in R8_D0 or ch.get("g_rep") not in R8_G_REP:
        raise SystemExit("R8 Stage S choice is not a registered grid point")
    return ch


def disposition(verdict) -> str:
    """Hard stop: every terminal outcome leads to the write-up, never another variant."""
    att = [v for k, v in verdict.items() if k.startswith("attempt")]
    met = [v for v in att if v.get("met")]
    if met:
        lab = met[0]["vacancy"]["label"]
        if lab == "vacant space present":
            return "met with vacant space; empty-site rung closed; next: write-up (decided with the user)"
        return "met, but vacancy " + lab + ": the empty-site question is still not reached; next: write-up"
    return "neither attempt met: empty-site rung closed; next: write-up (decided with the user)"


def main():
    out = Path(DATA_DIR)
    verdict_path = out / "r8_main_verdict.json"
    verdict_path.write_text(json.dumps({"complete": False, "note": "running or failed"}, indent=1))   # fail closed
    (out / "r8_main_runs.csv").unlink(missing_ok=True)
    choice = read_choice(out)
    if choice is None:
        verdict_path.write_text(json.dumps({"complete": True, "chosen_point": None, "r8_met": False,
                                            "disposition": "no setting passed the registered R8 screen; "
                                                           "empty-site rung closed; next: write-up"}, indent=1))
        return
    d0, g_rep = choice["d0"], choice["g_rep"]
    verdict, all_rows = {"chosen_point": choice}, []
    with Pool(WORKERS) as pool:
        for attempt in (1, 2):
            arms = r8_arms(attempt, d0, g_rep)
            rows = pool.map(run_r8.run_one, [(a, m, u, s, R8_MAIN_STEPS, R8_WINDOW_FROM)
                                             for a, (m, u) in arms.items() for s in R8_MAIN_SEEDS])
            for r in rows:
                r["success"] = joint_success(r)
                r["attempt"] = attempt
            all_rows += rows
            if not complete(rows, arms):
                verdict[f"attempt{attempt}"] = {"complete": False, "class": None}
                break
            by = {a: sorted([r for r in rows if r["arm"] == a], key=lambda r: r["seed"]) for a in arms}
            test, control, below, glob = r8_roles(attempt)
            res = {"complete": True, **classify_r1(by[test], by[control], by[below])}
            res["h2"] = score_h2(by[glob])
            res["mcnemar_descriptive"] = mcnemar_greater(by[test], by[control])
            n_occ = sum(r["n_occ_start"] for r in by[test])
            hv = sum(r["harvest_total"] for r in by[test]) / n_occ if n_occ else None      # all extinct: undefined
            res["income_activation"] = {"pooled_harvest": hv,
                                        "active": None if hv is None else hv <= R8_MAX_HARVEST + 1e-12}
            res["vacancy"] = vacancy_label(by[test])
            res["roles"] = {"test": test, "control": control, "below": below, "global": glob}
            res["descriptive"] = {a: describe(v) for a, v in by.items()}
            verdict[f"attempt{attempt}"] = res
            print(f"attempt {attempt}:", res["class"], "H2:", res["h2"]["result"], res["vacancy"]["label"], flush=True)
            if res["class"] not in ("local failure", "comparison failed"):
                break
    done = [v for k, v in verdict.items() if k.startswith("attempt") and v.get("complete")]
    verdict["complete"] = all(v.get("complete") for k, v in verdict.items() if k.startswith("attempt"))
    verdict["r8_met"] = any(v.get("met") for v in done) if verdict["complete"] else None
    if verdict["complete"]:
        verdict["disposition"] = disposition(verdict)
    write_union_csv(out / "r8_main_runs.csv", all_rows)
    verdict_path.write_text(json.dumps(json_safe(verdict), indent=1, allow_nan=False))
    print(json.dumps(json_safe({k: ({kk: vv for kk, vv in v.items() if kk not in ("descriptive", "vacancy")}
                                    if isinstance(v, dict) and k.startswith("attempt") else v)
                                for k, v in verdict.items()}), indent=1))


if __name__ == "__main__":
    main()
