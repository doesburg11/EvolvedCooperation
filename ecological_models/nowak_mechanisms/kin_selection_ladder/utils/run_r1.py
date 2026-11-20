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
    SUCCESS_FINAL_MEAN_TRAIT, WORKERS, r1_arms, r1_roles, run_config,
)
from ..ladder_model import make_engine
from .analysis import check_seeds, fisher_greater, neighbour_correlation, successes
from .run_step1 import STEP1_SUSTAINED_LAST, corr_steps, summarize
from .run_steps01 import edge_pairs, write_csv

DIAG_KEYS = ("offspring_mean", "frac_no_offspring", "benefit_lost", "parent_offspring_corr", "death_mean",
             "death_cared", "death_uncared", "death_parents", "frac_cared")
EXTRA_KEYS = ("juvenile_offspring_mean", "juvenile_fraction", "mean_age",     # R2 onward
              "S_mean", "D_mean", "S_juvenile", "D_juvenile", "S_parents", "D_parents",   # R3a onward
              "births_per_occupant", "frac_births_charged", "Db_mean", "D_recent_parents")   # R3b onward


def run_one(job):
    arm, mech, updates, seed, steps = job
    mech = dict(mech)
    eng = make_engine(run_config(seed, updates, steps), replacement=mech.pop("replacement"),
                      death=mech.pop("death"), **mech)
    ei, ej = edge_pairs(eng)
    cs = corr_steps(steps)
    traj, corr, surv, diag = [], [], [], {k: [] for k in DIAG_KEYS}
    with contextlib.redirect_stdout(io.StringIO()):
        while eng.step_index < steps:
            start = eng.step_index
            eng.step()
            t = eng.step_index
            surv.append(float(eng.last_survivors.mean()))
            if start >= K1_DIAG_FROM:                      # payoff states after 1000, ..., 5999 updates
                for k in DIAG_KEYS:
                    diag[k].append(eng.last_diag[k])
                for k in EXTRA_KEYS:
                    if k in eng.last_diag:
                        diag.setdefault(k, []).append(eng.last_diag[k])
            if t % 50 == 0:
                traj.append(float(np.mean(eng.h)))
            if t in cs:
                corr.append(neighbour_correlation(eng.h, ei, ej))
    final = float(np.mean(eng.h))
    n_last = STEP1_SUSTAINED_LAST // 50 + 1
    row = {"arm": arm, "seed": seed, "final_mean_trait": final, "success": int(final >= SUCCESS_FINAL_MEAN_TRAIT),
           "sustained_success": int(all(x >= SUCCESS_FINAL_MEAN_TRAIT for x in traj[-n_last:])),
           "survival_fraction": float(np.mean(surv)), "traj_every_50": traj, "neighbour_h_corr": corr}
    for k in (*DIAG_KEYS, *[k for k in EXTRA_KEYS if k in diag]):
        v = np.asarray(diag[k], dtype=float)
        row[k] = float(np.nanmean(v)) if v.size and np.isfinite(v).any() else float("nan")
    return row


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
                        "mcnemar_descriptive": mcnemar_greater(arms[test], arms[control])})
            desc = {}
            for a, v in arms.items():
                d = summarize(v, K0_STEPS)
                for k in (*DIAG_KEYS, *[k for k in EXTRA_KEYS if k in v[0]]):
                    vals = np.asarray([r[k] for r in v], dtype=float)
                    d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
                desc[a] = d
            res["descriptive"] = desc
            verdict[f"attempt{attempt}"] = res
            print(f"attempt {attempt}:", res["class"], "H2:", res["h2"]["result"], flush=True)
            if res["class"] not in ("local failure", "comparison failed"):
                break
    verdict[f"{name}_met"] = any(v["met"] for v in verdict.values() if isinstance(v, dict))
    write_csv(out / f"{name}_runs.csv", all_rows)
    (out / f"{name}_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "descriptive"} if isinstance(v, dict) else v)
                      for k, v in verdict.items()}, indent=1))


if __name__ == "__main__":
    main()
