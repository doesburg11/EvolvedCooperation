#!/usr/bin/env python3
"""Run all NetLogo experiments in the Python port (30 seeds each), compare with the NetLogo runs, summarise lineage.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_experiments
Writes data/runs.csv (reporters per run), data/lineage.csv (lineage samples), data/check.csv and data/summary.json.
"""
from __future__ import annotations

import csv
import json
import math
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy import stats

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_experiments")

from ..config.ethnocentrism_config import (
    CHECK_ALPHA, CHECK_MAX_ABS_DIFF, CHECK_METRICS, DATA_DIR, EXPECT_MIN_SEEDS, EXPERIMENTS, NETLOGO_RESULTS_DIR,
    NETLOGO_RUNS, SEEDS, WORKERS,
    run_config,
)
from ..ethnocentrism_model import Ethnocentrism


def one(job: tuple[str, int]) -> dict:
    exp, seed = job
    out = Ethnocentrism(run_config(exp), seed).run()
    return {"experiment": exp, "seed": seed, **out}


NETLOGO_PARAM = {"gain-of-receiving": "gain_of_receiving", "initial-ptr": "initial_ptr",
                 "immigrants-per-day": "immigrants_per_day", "mutation-rate": "mutation_rate",
                 "cost-of-giving": "cost_of_giving", "death-rate": "death_rate",
                 "immigrant-chance-cooperate-with-same": "immigrant_chance_cooperate_with_same",
                 "immigrant-chance-cooperate-with-different": "immigrant_chance_cooperate_with_different"}


def netlogo_table(exp: str) -> list[dict[str, float]]:
    """NetLogo BehaviorSpace table for one experiment, validated against the port's config (fails fast)."""
    path = Path(NETLOGO_RESULTS_DIR) / f"netlogo_exp{exp}" / "table.csv"
    rows = list(csv.reader(open(path)))
    h = next(i for i, r in enumerate(rows) if r and r[0] == "[run number]")
    recs = [dict(zip(rows[h], r)) for r in rows[h + 1:] if r]
    cfg = run_config(exp)
    if len(recs) != NETLOGO_RUNS or len({r["[run number]"] for r in recs}) != NETLOGO_RUNS:
        raise ValueError(f"{path}: expected {NETLOGO_RUNS} distinct runs, got {len(recs)}")
    for r in recs:
        if int(r["[step]"]) != cfg["ticks"]:
            raise ValueError(f"{path}: run {r['[run number]']} ended at step {r['[step]']}, not {cfg['ticks']}")
        if int(r["max-pxcor"]) + 1 != cfg["width"] or int(r["max-pycor"]) + 1 != cfg["height"]:
            raise ValueError(f"{path}: world size differs from config")
        for nl, py in NETLOGO_PARAM.items():
            if not math.isclose(float(r[nl]), cfg[py]):
                raise ValueError(f"{path}: {nl} = {r[nl]} but config {py} = {cfg[py]}")
    out = [{m: float(r[m]) for m in CHECK_METRICS} for r in recs]
    if not all(math.isfinite(v) for r in out for v in r.values()):
        raise ValueError(f"{path}: non-finite metric")
    return out


def flag(p: float, diff: float) -> bool:
    """Pre-registered rule: flag when p < CHECK_ALPHA and |diff| > CHECK_MAX_ABS_DIFF; an undefined p flags."""
    return (not math.isfinite(p)) or (p < CHECK_ALPHA and abs(diff) > CHECK_MAX_ABS_DIFF)


def welch(a: np.ndarray, b: np.ndarray) -> float:
    """Two-sided Welch t-test p-value."""
    if a.var() == 0 and b.var() == 0:
        return 1.0 if a.mean() == b.mean() else 0.0
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)


def main() -> None:
    out_dir = Path(DATA_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(e, s) for e in EXPERIMENTS for s in SEEDS]
    with Pool(WORKERS) as pool:
        res = pool.map(one, jobs, chunksize=1)

    with open(out_dir / "runs.csv", "w", newline="") as f:
        keys = list(res[0]["reporters"])
        w = csv.writer(f); w.writerow(["experiment", "seed", "population", "births_total", *keys])
        for r in res:
            w.writerow([r["experiment"], r["seed"], r["population"], r["births_total"], *[r["reporters"][k] for k in keys]])
    lkeys = sorted({k for r in res for s in r["lineage"] for k in s})
    with open(out_dir / "lineage.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["experiment", "seed", *lkeys])
        for r in res:
            for s in r["lineage"]:
                w.writerow([r["experiment"], r["seed"], *[s.get(k, "") for k in lkeys]])

    # 1. port vs NetLogo
    check, flagged = [], []
    for e in EXPERIMENTS:
        nl = netlogo_table(e)
        for m in CHECK_METRICS:
            a = np.array([r["reporters"][m] for r in res if r["experiment"] == e])
            b = np.array([r[m] for r in nl])
            p = welch(a, b)
            row = {"experiment": e, "metric": m, "python_mean": a.mean(), "netlogo_mean": b.mean(),
                   "diff": a.mean() - b.mean(), "p": p, "n_python": a.size, "n_netlogo": b.size}
            check.append(row)
            if flag(p, row["diff"]):
                flagged.append(row)
    with open(out_dir / "check.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(check[0])); w.writeheader(); w.writerows(check)

    port_passes = not flagged
    summary: dict = {"port_passes": port_passes, "flagged": flagged, "n_checks": len(check),
                     "n_p_below_0.05": sum(c["p"] < 0.05 for c in check),
                     "min_p": min(c["p"] for c in check), "max_abs_diff": max(abs(c["diff"]) for c in check)}
    if not port_passes:
        json.dump(summary, open(out_dir / "summary.json", "w"), indent=1)
        raise SystemExit(f"Port FAILS the NetLogo check ({len(flagged)} flagged); lineage results not summarised.")

    # 2. lineage, experiment 104, final tick (undefined values count as "not met")
    fin = [r["lineage"][-1] for r in res if r["experiment"] == "104"]
    e1 = sum(bool(s["same_frac_same_founder"] > s["diff_frac_same_founder"]) for s in fin)
    e2 = sum(bool(s["same_r_pop_cs"] > 0) for s in fin)
    keys = ["frac_pairs_same_colour", "n_founders_alive", "colour_fidelity",
            *[f"{g}_{k}" for g in ("same", "diff") for k in
              ("frac_same_founder", "frac_gen_le2", "gen_dist_median", "tmrca_median",
               "r_pop_cs", "r_pop_cd", "r_reg_cs", "r_reg_cd")]]
    lin = {k: {"mean": float(np.nanmean([s[k] for s in fin])), "min": float(np.nanmin([s[k] for s in fin])),
               "max": float(np.nanmax([s[k] for s in fin]))} for k in keys}
    summary.update({"E1_seeds": e1, "E2_seeds": e2, "n_seeds": len(fin),
                    "E1_met": e1 >= EXPECT_MIN_SEEDS, "E2_met": e2 >= EXPECT_MIN_SEEDS, "lineage_104_final": lin})
    json.dump(summary, open(out_dir / "summary.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "lineage_104_final"}, indent=1))
    for k, v in lin.items():
        print(f"  {k:28} mean {v['mean']:8.3f}  range {v['min']:.3f}..{v['max']:.3f}")

if __name__ == "__main__":
    main()
