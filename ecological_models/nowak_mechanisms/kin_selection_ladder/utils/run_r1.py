#!/usr/bin/env python3
"""Step R1: care raises the offspring's survival (README pre-registration 0231603).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r1
"""
from __future__ import annotations

import contextlib
import math
import io
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r1")

from ..config.ladder_config import (
    DATA_DIR, K0_STEPS, K1_DIAG_FROM, K1_MIN_TEST, SEEDS, STEP1_ALPHA, STEP1_MAX_GLOBAL_CORR,
    R3C_MIN_OCCUPANCY, R3D_MIN_ACTIVATION, R4_MAX_HARVEST, SUCCESS_FINAL_MEAN_TRAIT, WORKERS, r1_arms, r1_roles, run_config,
)
from ..ladder_model import make_engine
from .analysis import check_seeds, fisher_greater, neighbour_correlation, successes
from .run_step1 import STEP1_SUSTAINED_LAST, corr_steps, summarize
from .run_steps01 import edge_pairs, write_csv

DIAG_KEYS = ("offspring_mean", "frac_no_offspring", "benefit_lost", "parent_offspring_corr", "death_mean",
             "death_cared", "death_uncared", "death_parents", "frac_cared")
EXTRA_KEYS = ("juvenile_offspring_mean", "juvenile_fraction", "mean_age",     # R2 onward
              "S_mean", "D_mean", "S_juvenile", "D_juvenile", "S_parents", "D_parents",   # R3a onward
              "births_per_occupant", "frac_births_charged", "Db_mean", "D_recent_parents",   # R3b onward
              "occupancy", "frac_fill_trimmed", "frac_fill_emptied", "frac_ineligible",       # R3c onward
              "frac_ineligible_low_h", "frac_ineligible_high_h",
              "starve_added_per_occ", "starve_all_per_occ", "starve_added_share",                  # R3d onward
              "starve_rate_low_h", "starve_rate_high_h", "starve_rate_recent_parents", "starve_rate_juveniles",
              "harvest_mean", "G_mean", "G_juvenile", "G_parents", "r_occupied", "r_empty",       # R4 onward
              "frac_harvest_capped",
              "frac_ineligible_recent_parents",                                              # DR4 onward
              "frac_exposed", "harvest_near_empty", "harvest_away_empty",                    # R5a onward
              "frac_overdraft_recent_parents")                                               # R6 onward
FILL_KEYS = ("n_fill_needed", "n_fill_emptied")                                              # R6: pooled counts
AGE_KEYS = ("n_fill_age_blocked", "births_adult_sum", "n_adult", "births_juvenile_sum", "n_juvenile",  # R7
            "parent_age_sum", "n_births_age", "empty_nb_sum", "n_empty_end")
PAY_KEYS = ("paid_total", "n_births", "births_by_dying_parents", "n_overdraft")               # R6: pooled
EXPOSURE_KEYS = ("n_exposed", "n_near_empty")                                               # R5a: pooled counts
BIRTH_CLASS_KEYS = ("births_low_h_sum", "n_low_h", "births_high_h_sum", "n_high_h")          # DR4: pooled counts


def joint_success(final_h, final_occ=None) -> bool:
    """Success: final mean h >= 0.60 (nan, e.g. extinct, fails); from R3c also final occupancy >= 0.5."""
    ok = bool(final_h >= SUCCESS_FINAL_MEAN_TRAIT)
    if final_occ is not None:
        ok = ok and final_occ >= R3C_MIN_OCCUPANCY
    return ok


def occupied_corr(eng, ei, ej) -> float:
    """R3c: neighbour h correlation over edges with both ends occupied (undefined if none)."""
    both = eng.occ[ei] & eng.occ[ej]
    return neighbour_correlation(eng.h, ei[both], ej[both]) if both.any() else float("nan")


def run_one(job):
    arm, mech, updates, seed, steps = job
    mech = dict(mech)
    eng = make_engine(run_config(seed, updates, steps), replacement=mech.pop("replacement"),
                      death=mech.pop("death"), **mech)
    ei, ej = edge_pairs(eng)
    cs = corr_steps(steps)
    traj, corr, surv, diag = [], [], [], {k: [] for k in DIAG_KEYS}
    vac = hasattr(eng, "occ")                          # R3c: statistics over occupied sites only
    mean_h = eng.occupied_mean_h if vac else (lambda: float(np.mean(eng.h)))
    occ_traj, occ_steps = [], []
    starve_sums = {"n_starve_added": 0, "n_deaths": 0}
    harvest_sums = {"harvest_total": 0.0, "n_occ_start": 0}
    birth_sums = {k: 0 for k in BIRTH_CLASS_KEYS}
    exposure_sums = {k: 0 for k in EXPOSURE_KEYS}
    fill_sums = {k: 0 for k in FILL_KEYS}
    pay_sums = {k: 0.0 if k == "paid_total" else 0 for k in PAY_KEYS}
    age_sums = {k: 0 for k in AGE_KEYS}
    occ_site_steps = 0
    with contextlib.redirect_stdout(io.StringIO()):
        while eng.step_index < steps:
            start = eng.step_index
            occ0 = eng.occ.copy() if vac else None
            eng.step()
            t = eng.step_index
            if vac:                                        # survivors among start-of-step occupants
                surv.append(float(eng.last_survivors.sum() / occ0.sum()) if occ0.any() else float("nan"))
                occ_steps.append(float(eng.occ.mean()))
            else:
                surv.append(float(eng.last_survivors.mean()))
            if start >= K1_DIAG_FROM:                      # payoff states after 1000, ..., 5999 updates
                for k in DIAG_KEYS:
                    diag[k].append(eng.last_diag[k])
                for k in EXTRA_KEYS:
                    if k in eng.last_diag:
                        diag.setdefault(k, []).append(eng.last_diag[k])
                for k in starve_sums:
                    starve_sums[k] += int(eng.last_diag.get(k, 0))
                if "n_fill_needed" in eng.last_diag:
                    for k in fill_sums:
                        fill_sums[k] += int(eng.last_diag[k])
                    occ_site_steps += int(occ0.sum())
                if "n_fill_age_blocked" in eng.last_diag:
                    for k in age_sums:
                        age_sums[k] += int(eng.last_diag[k])
                if "paid_total" in eng.last_diag:
                    for k in pay_sums:
                        pay_sums[k] += eng.last_diag[k]
                if "n_exposed" in eng.last_diag:
                    for k in exposure_sums:
                        exposure_sums[k] += int(eng.last_diag[k])
                if "births_low_h_sum" in eng.last_diag:
                    for k in birth_sums:
                        birth_sums[k] += int(eng.last_diag[k])
                if hasattr(eng, "gamma"):
                    harvest_sums["harvest_total"] += float(eng.last_diag["harvest_total"])
                    harvest_sums["n_occ_start"] += int(eng.last_diag["n_occ_start"])
            if t % 50 == 0:
                traj.append(mean_h())
                if vac:
                    occ_traj.append(float(eng.occ.mean()))
            if t in cs:
                if vac:
                    corr.append(occupied_corr(eng, ei, ej))
                else:
                    corr.append(neighbour_correlation(eng.h, ei, ej))
    final = mean_h()
    final_occ = float(eng.occ.mean()) if vac else None
    ok = joint_success(final, final_occ)
    n_last = STEP1_SUSTAINED_LAST // 50 + 1
    row = {"arm": arm, "seed": seed, "final_mean_trait": final, "success": int(ok),
           "sustained_success": int(all(x >= SUCCESS_FINAL_MEAN_TRAIT for x in traj[-n_last:])),
           "survival_fraction": float(np.nanmean(surv)) if np.isfinite(surv).any() else float("nan"),
           "traj_every_50": traj, "neighbour_h_corr": corr}
    if hasattr(eng, "sigma"):
        row.update({"starve_added_total": starve_sums["n_starve_added"], "deaths_total": starve_sums["n_deaths"]})
        row.update(birth_sums)
    if hasattr(eng, "gamma"):
        row.update(harvest_sums)
    if hasattr(eng, "w_own"):
        row.update(exposure_sums)
    if hasattr(eng, "parent_pay") or hasattr(eng, "breed_age"):
        row.update(fill_sums)
        row.update({"occ_site_steps": occ_site_steps, "site_steps": int(eng.n_sites) * len(diag["death_mean"])})
    if hasattr(eng, "parent_pay"):
        row.update(pay_sums)
    if hasattr(eng, "breed_age"):
        row.update(age_sums)
    if vac:
        row.update({"final_occupancy": final_occ, "extinct": int(not eng.occ.any()),
                    "occupancy_last1000": float(np.mean(occ_steps[-1000:])), "occ_every_50": occ_traj})
    for k in (*DIAG_KEYS, *[k for k in EXTRA_KEYS if k in diag]):
        v = np.asarray(diag[k], dtype=float)
        row[k] = float(np.nanmean(v)) if v.size and np.isfinite(v).any() else float("nan")
    return row


def json_safe(o):
    """Undefined values (NaN, inf) are written as JSON null (Codex R3b review)."""
    if isinstance(o, dict):
        return {k: json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [json_safe(v) for v in o]
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def classify_r1(test_rows, control_rows, below_rows, alpha=STEP1_ALPHA):
    t, c, b = successes(test_rows), successes(control_rows), successes(below_rows)
    p = fisher_greater(t, len(test_rows), c, len(control_rows))
    if t < K1_MIN_TEST or b > 2:
        cls = "local failure"
    elif t - c < 8 or not p < alpha:
        cls = "comparison failed"
    else:
        cls = "met"
    return {"test": t, "control": c, "below_maintained": b, "fisher_p": p, "alpha": alpha, "class": cls,
            "met": cls == "met"}


def score_h2(global_rows):
    corr = float(np.mean([np.mean(r["neighbour_h_corr"]) for r in global_rows]))
    s = successes(global_rows)
    res = "not interpretable" if not (corr <= STEP1_MAX_GLOBAL_CORR) else ("met" if s >= K1_MIN_TEST else "not met")
    per_seed = {int(r.get("seed", i)): [float(x) for x in r["neighbour_h_corr"]] for i, r in enumerate(global_rows)}
    return {"successes": s, "neighbour_corr": corr, "result": res, "per_seed_corr": per_seed}


def mcnemar_greater(test_rows, control_rows):
    """One-sided exact McNemar on matched seeds (descriptive, R3b onward): P(X >= n10 | n10 + n01, 1/2)."""
    t = {int(r["seed"]): int(r["success"]) for r in test_rows}
    c = {int(r["seed"]): int(r["success"]) for r in control_rows}
    if sorted(t) != sorted(c):
        raise ValueError("McNemar needs the same seeds in both arms")
    n10 = sum(1 for s in t if t[s] and not c[s])
    n01 = sum(1 for s in t if c[s] and not t[s])
    n = n10 + n01
    p = sum(math.comb(n, j) for j in range(n10, n + 1)) / 2 ** n if n else 1.0
    return {"n10": n10, "n01": n01, "p": p}


def main(arms_fn=None, roles_fn=None, name="r1"):
    arms_fn = arms_fn or r1_arms
    roles_fn = roles_fn or r1_roles
    out = Path(DATA_DIR)
    verdict, all_rows = {}, []
    with Pool(WORKERS) as pool:
        for attempt in (1, 2):
            arms_cfg = arms_fn(attempt)
            rows = pool.map(run_one, [(a, m, u, s, K0_STEPS) for a, (m, u) in arms_cfg.items() for s in SEEDS])
            all_rows += rows
            arms = {a: [r for r in rows if r["arm"] == a] for a in arms_cfg}
            for v in arms.values():
                check_seeds(v, SEEDS)
            test, control, below, glob = roles_fn(attempt)
            res = classify_r1(arms[test], arms[control], arms[below])
            res["h2"] = score_h2(arms[glob])
            res.update({"test_arm": test, "control_arm": control, "below_arm": below, "global_arm": glob,
                        "care_lam": arms_cfg[test][0]["care_lam"],
                        "care_juvenile": arms_cfg[test][0].get("care_juvenile"),
                        "care_rho": arms_cfg[test][0].get("care_rho"),
                        "care_birth_cost": arms_cfg[test][0].get("care_birth_cost"),
                        "care_theta": arms_cfg[test][0].get("care_theta"),
                        "mcnemar_descriptive": mcnemar_greater(arms[test], arms[control])})
            desc = {}
            for a, v in arms.items():
                d = summarize(v, K0_STEPS)
                for k in (*DIAG_KEYS, *[k for k in EXTRA_KEYS if k in v[0]],
                          *[k for k in ("final_occupancy", "occupancy_last1000") if k in v[0]]):
                    vals = np.asarray([r[k] for r in v], dtype=float)
                    d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
                if "starve_added_total" in v[0]:
                    d["starve_added_per_seed"] = [int(r["starve_added_total"]) for r in v]
                    d["deaths_per_seed"] = [int(r["deaths_total"]) for r in v]
                    tot = sum(d["deaths_per_seed"])
                    d["starvation_activation"] = sum(d["starve_added_per_seed"]) / tot if tot else None
                if "harvest_total" in v[0]:
                    d["harvest_per_seed"] = [float(r["harvest_total"]) for r in v]
                    d["occ_steps_per_seed"] = [int(r["n_occ_start"]) for r in v]
                    tot = sum(d["occ_steps_per_seed"])
                    d["pooled_harvest"] = sum(d["harvest_per_seed"]) / tot if tot else None
                if "extinct" in v[0]:
                    d["extinctions"] = int(sum(r["extinct"] for r in v))
                    d["final_occupancy_per_seed"] = [r["final_occupancy"] for r in v]
                    d["final_h_per_seed"] = [r["final_mean_trait"] for r in v]
                    d["occ_every_50"] = [float(np.mean([r["occ_every_50"][t] for r in v]))
                                         for t in range(len(v[0]["occ_every_50"]))]
                desc[a] = d
            res["descriptive"] = desc
            act = desc[test].get("starvation_activation", "absent")
            if act != "absent":
                res["care_sigma"] = arms_cfg[test][0].get("care_sigma")
                res["starvation_activation"] = act
                res["starvation_active"] = act is not None and act >= R3D_MIN_ACTIVATION
            hv = desc[test].get("pooled_harvest", "absent")
            if hv != "absent":
                res["care_gamma"] = arms_cfg[test][0].get("care_gamma")
                res["pooled_harvest"] = hv
                # inclusive cutoff with a float tolerance (Codex R4 review: a decimal 0.19 can sum to 0.19000000000000003)
                res["income_limitation_active"] = hv is not None and hv <= R4_MAX_HARVEST + 1e-12
                res["income_limitation_label"] = ("income limitation active" if res["income_limitation_active"]
                                                  else "income limitation inactive")
            verdict[f"attempt{attempt}"] = res
            print(f"attempt {attempt}:", res["class"], "H2:", res["h2"]["result"], flush=True)
            if res["class"] not in ("local failure", "comparison failed"):
                break
    verdict[f"{name}_met"] = any(v["met"] for v in verdict.values() if isinstance(v, dict))
    write_csv(out / f"{name}_runs.csv", all_rows)
    (out / f"{name}_verdict.json").write_text(json.dumps(json_safe(verdict), indent=1, allow_nan=False))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "descriptive"} if isinstance(v, dict) else v)
                      for k, v in verdict.items()}, indent=1))


if __name__ == "__main__":
    main()
