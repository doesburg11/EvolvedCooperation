#!/usr/bin/env python3
"""Diagnostic DR1: does survival care settle at a level approached from both sides? (README pre-registration 8317f48)

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_dr1
"""
from __future__ import annotations

import csv
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_dr1")

from ..config.ladder_config import (
    DATA_DIR, DR1_NULL_FOR, DR1_NULL_MIN, DR1_PAIRS, DR1_RARE_REF, DR1_SETTLED_FROM, DR1_SETTLED_RANGE, DR1_TOL,
    K0_STEPS, SEEDS, WORKERS, dr1_arms,
)
from .analysis import check_seeds
from .run_r1 import DIAG_KEYS, run_one
from .run_step1 import summarize
from .run_steps01 import write_csv


def settled_range(mean_traj):
    """Max - min of the arm-mean h over the 50-step samples from step DR1_SETTLED_FROM to the end."""
    first = DR1_SETTLED_FROM // 50 - 1                    # traj[k] is the sample at step 50 (k + 1)
    w = mean_traj[first:]
    return float(max(w) - min(w))


def first_below(mean_traj, level):
    for k, x in enumerate(mean_traj):
        if x < level:
            return 50 * (k + 1)
    return "never"


def paired(a_rows, b_by_seed, key="final_mean_trait"):
    a = {r["seed"]: r[key] for r in a_rows}
    d = [float(a[s] - b_by_seed[s]) for s in SEEDS]
    p = float(wilcoxon(d).pvalue) if all(np.isfinite(d)) and any(x != 0 for x in d) else float("nan")
    return {"per_seed_diff": d, "mean_diff": float(np.mean(d)), "min_diff": float(min(d)),
            "max_diff": float(max(d)), "wilcoxon_p": p}


def load_r1_reference(r1_csv: Path):
    """Archived R1 per-seed final h for the four counterparts; each must have seeds 0-19 exactly once, finite values,
    and a mean equal to the frozen reference."""
    with open(r1_csv) as f:
        r1 = [r for r in csv.DictReader(f) if r["arm"] in DR1_RARE_REF]
    out = {}
    for a, ref in DR1_RARE_REF.items():
        rows = [r for r in r1 if r["arm"] == a]
        seeds = sorted(int(r["seed"]) for r in rows)
        vals = {int(r["seed"]): float(r["final_mean_trait"]) for r in rows}
        if seeds != list(SEEDS) or not all(np.isfinite(list(vals.values()))) \
                or abs(np.mean([vals[s] for s in SEEDS]) - ref) > 1e-12:
            raise RuntimeError(f"archived R1 runs for {a} do not match the frozen reference")
        out[a] = vals
    return out


def score(arms, r1_csv: Path):
    desc = {a: summarize(v, K0_STEPS) for a, v in arms.items()}
    for a, v in arms.items():
        for k in DIAG_KEYS:
            vals = np.asarray([r[k] for r in v], dtype=float)
            desc[a][k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
        desc[a]["settled_range"] = settled_range(desc[a]["mean_h_every_50"])
    r1_by = load_r1_reference(r1_csv)
    pairs, n_met = {}, 0
    for high, rare in DR1_PAIRS.items():
        m = desc[high]["mean_final_h"]
        null_ok = desc[DR1_NULL_FOR[high]]["mean_final_h"] > DR1_NULL_MIN
        close = abs(m - DR1_RARE_REF[rare]) <= DR1_TOL
        settled = desc[high]["settled_range"] <= DR1_SETTLED_RANGE
        met = bool(close and settled and null_ok)
        n_met += met
        pairs[high] = {"rare_ref": rare, "high_mean_final_h": m, "rare_mean_final_h": DR1_RARE_REF[rare],
                       "abs_diff": abs(m - DR1_RARE_REF[rare]), "close": close,
                       "settled_range": desc[high]["settled_range"], "settled": settled, "null_ok": null_ok,
                       "met": met, "first_below_ref_plus_tol": first_below(desc[high]["mean_h_every_50"],
                                                                           DR1_RARE_REF[rare] + DR1_TOL),
                       "paired_vs_rare": paired(arms[high], r1_by[rare])}
    t1 = {"pairs": pairs, "n_met": n_met, "result": "supported" if n_met >= 3 else "not supported"}
    a24, a48 = desc["D24-local-high"], desc["D48-local-high"]
    both_settled = a24["settled_range"] <= DR1_SETTLED_RANGE and a48["settled_range"] <= DR1_SETTLED_RANGE
    lower_h = a48["mean_final_h"] < a24["mean_final_h"]
    lower_d = (a48["death_cared"] is not None and a24["death_cared"] is not None
               and a48["death_cared"] < a24["death_cared"])
    if not both_settled:
        t2r = "not settled"
    else:
        t2r = "supported" if (lower_h and lower_d) else "not supported"
    t2 = {"h48": a48["mean_final_h"], "h24": a24["mean_final_h"], "death_cared48": a48["death_cared"],
          "death_cared24": a24["death_cared"], "lower_h": lower_h, "lower_death": lower_d,
          "settled_range48": a48["settled_range"], "settled_range24": a24["settled_range"], "result": t2r,
          "paired_48_minus_24": paired(arms["D48-local-high"],
                                       {r["seed"]: r["final_mean_trait"] for r in arms["D24-local-high"]}),
          "paired_death_cared_48_minus_24": paired(arms["D48-local-high"],
                                                   {r["seed"]: r["death_cared"] for r in arms["D24-local-high"]},
                                                   key="death_cared"),
          "first_below_D48_rare_plus_tol": first_below(a48["mean_h_every_50"],
                                                       desc["D48-local"]["mean_final_h"] + DR1_TOL)}
    return {"T1": t1, "T2": t2, "descriptive": desc,
            "nulls": {n: desc[n]["mean_final_h"] for n in ("D-null-local-high", "D-null-global-high")}}


def main():
    out = Path(DATA_DIR)
    arms_cfg = dr1_arms()
    with Pool(WORKERS) as pool:
        rows = pool.map(run_one, [(a, m, u, s, K0_STEPS) for a, (m, u) in arms_cfg.items() for s in SEEDS])
    arms = {a: [r for r in rows if r["arm"] == a] for a in arms_cfg}
    for v in arms.values():
        check_seeds(v, SEEDS)
    verdict = score(arms, out / "r1_runs.csv")
    write_csv(out / "dr1_runs.csv", rows)
    (out / "dr1_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: v for k, v in verdict.items() if k != "descriptive"}, indent=1))


if __name__ == "__main__":
    main()
