#!/usr/bin/env python3
"""Confirmation test: persistence (README, pre-registered 2026-11-18). Runs every arm, scores H1-H3 and the
descriptive measures, writes data/confirm_runs.csv and data/confirm_verdict.json.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_learning.utils.run_confirm
"""
from __future__ import annotations

import csv
import json
import math
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_learning.utils.run_confirm")

from ...kin_selection.config.kin_selection_config import resolve_config
from ..config.learning_config import (
    CONFIRM_ALPHA, CONFIRM_ARMS, CONFIRM_BOOTSTRAP, CONFIRM_CONSTANT_ARMS, CONFIRM_CONSTANT_EFFORT,
    CONFIRM_COST_STEPS, CONFIRM_GRID, CONFIRM_LONG_ARMS, CONFIRM_LONG_STEPS, CONFIRM_LONG_WINDOW,
    CONFIRM_MIN_POPULATION, CONFIRM_SEEDS, CONFIRM_STEPS, CONFIRM_WINDOW, DATA_DIR, LEARNING, STARTS, WORKERS,
)
from ..learning_model import run_version

C_STAR = 0.03


def persists(population, window) -> bool:
    """History index t = after step t; a run that died out before the window's end has a shorter history."""
    lo, hi = window
    if len(population) <= hi:
        return False
    return bool(min(population[lo:hi + 1]) >= CONFIRM_MIN_POPULATION)


def window_cost(h, steps=CONFIRM_COST_STEPS) -> float:
    lo, hi = steps
    cost = np.asarray(h["total_helper_energy_cost"][lo:hi + 1], float)
    carers = np.asarray(h["adult_count"][lo:hi + 1], float) + np.asarray(h["elder_count"][lo:hi + 1], float)
    return float(cost.sum() / carers.sum()) if carers.sum() > 0 else math.nan


def feedback_corr(h, rng) -> tuple[float, float]:
    """Correlation of juveniles-per-carer at step t with the change in mean effort from t to t+1, and the same
    after shuffling the changes (one shuffle)."""
    juv = np.asarray(h["juvenile_count"], float)
    carers = np.asarray(h["adult_count"], float) + np.asarray(h["elder_count"], float)
    e = np.asarray(h["mean_expressed_helping"], float)
    ok = carers[:-1] > 0
    x, d = (juv[:-1] / np.where(carers[:-1] > 0, carers[:-1], 1))[ok], np.diff(e)[ok]
    good = np.isfinite(x) & np.isfinite(d)
    x, d = x[good], d[good]
    if len(x) < 10 or x.std() == 0 or d.std() == 0:
        return math.nan, math.nan
    return float(np.corrcoef(x, d)[0, 1]), float(np.corrcoef(x, rng.permutation(d))[0, 1])


def run_one(job):
    arm, start, seed, steps = job
    version, overrides, _ = CONFIRM_ARMS[arm]
    cfg = resolve_config({"random_seed": seed, "care_cost_per_unit": C_STAR, "simulation_steps": steps,
                          "write_latest_run": False, **STARTS[start]})
    h = run_version(cfg, version, {**LEARNING, "alpha": CONFIRM_ALPHA, **overrides})["history"]
    pop = list(h["population"])
    lo, hi = CONFIRM_COST_STEPS
    row = {"arm": arm, "start": start, "seed": seed, "steps": steps,
           "persists": int(persists(pop, CONFIRM_WINDOW if steps == CONFIRM_STEPS else CONFIRM_LONG_WINDOW)),
           "final_population": pop[-1], "history_length": len(pop),
           "cost_per_carer_step": window_cost(h),
           "mean_action_1_60": nanmean(h["mean_care_action"][lo:hi + 1]),
           "reached_cap_by_60": int(max(pop[:hi + 1]) >= int(cfg["max_population"])),
           "mean_k_0": float(h["mean_helping_trait"][0]),
           "mean_k_60": float(h["mean_helping_trait"][hi]) if len(pop) > hi else math.nan,
           "mean_k_end": float(h["mean_helping_trait"][-1])}
    if arm == "C" and start == "weak" and steps == CONFIRM_STEPS:
        row["feedback_corr"], row["feedback_corr_shuffled"] = feedback_corr(h, np.random.default_rng(seed))
    if arm == "C" and steps == CONFIRM_STEPS:
        row["_k_series"] = [float(x) for x in h["mean_helping_trait"]]
    return row


def nanmean(values) -> float:
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    return float(v.mean()) if len(v) else math.nan


def outcomes(rows, arm, start, steps=CONFIRM_STEPS):
    cell = {r["seed"]: r for r in rows if r["arm"] == arm and r["start"] == start and r["steps"] == steps}
    if sorted(cell) != sorted(CONFIRM_SEEDS):
        raise ValueError(f"{arm}/{start}/{steps}: not exactly one run per configured seed")
    return cell


def count(rows, arm, start, steps=CONFIRM_STEPS) -> int:
    cell = outcomes(rows, arm, start, steps)
    return int(sum(int(cell[s]["persists"]) for s in CONFIRM_SEEDS))


def rate(rows, arm, start, steps=CONFIRM_STEPS) -> float:
    return count(rows, arm, start, steps) / len(CONFIRM_SEEDS)


def runs(fraction) -> int:
    """A rate threshold as a whole number of runs (0.40 of 40 = 16), so no float rounding at the boundary."""
    return int(round(fraction * len(CONFIRM_SEEDS)))


def paired(rows, better, worse, start, threshold) -> dict:
    """One-sided exact sign test on discordant seeds (McNemar); both the size threshold and p < 0.05 must hold."""
    b_, w_ = outcomes(rows, better, start), outcomes(rows, worse, start)
    only_b = sum(1 for s in CONFIRM_SEEDS if b_[s]["persists"] and not w_[s]["persists"])
    only_w = sum(1 for s in CONFIRM_SEEDS if w_[s]["persists"] and not b_[s]["persists"])
    p = float(binomtest(only_b, only_b + only_w, 0.5, alternative="greater").pvalue) if only_b + only_w else 1.0
    diff_runs = count(rows, better, start) - count(rows, worse, start)
    return {"diff": diff_runs / len(CONFIRM_SEEDS), "only_better": only_b, "only_worse": only_w, "p": p,
            "met": bool(diff_runs >= runs(threshold) and p < 0.05)}


def boot_ci(values, rng, stat=np.mean) -> list[float]:
    v = np.asarray([x for x in values if math.isfinite(x)], float)
    if len(v) == 0:
        return [math.nan, math.nan]
    idx = rng.integers(0, len(v), (CONFIRM_BOOTSTRAP, len(v)))
    return [float(x) for x in np.percentile(stat(v[idx], axis=1), [2.5, 97.5])]


def h3(rows, rng) -> dict:
    c_runs = count(rows, "C", "weak")
    c = outcomes(rows, "C", "weak")
    c_action = nanmean([c[s]["mean_action_1_60"] for s in CONFIRM_SEEDS])
    matching = [a for a in CONFIRM_CONSTANT_ARMS if count(rows, a, "weak") >= c_runs - runs(0.10)]
    out = {"C_rate": c_runs / len(CONFIRM_SEEDS), "C_mean_action_1_60": c_action, "matching_arms": matching}
    if not matching:
        inside = bool(math.isfinite(c_action) and CONFIRM_GRID[0] <= c_action <= CONFIRM_GRID[1])
        out.update({"outcome": "met" if inside else "inconclusive", "met": inside})
        return out

    def median_cost(a):  # over the arm's persisting runs
        cell = outcomes(rows, a, "weak")
        v = [cell[s]["cost_per_carer_step"] for s in CONFIRM_SEEDS if cell[s]["persists"]]
        v = [x for x in v if math.isfinite(x)]
        return float(np.median(v)) if v else math.inf
    arm = min(matching, key=lambda a: (median_cost(a), CONFIRM_CONSTANT_EFFORT[a], a))  # cheapest; ties: lower effort
    f = outcomes(rows, arm, "weak")
    both = [s for s in CONFIRM_SEEDS if c[s]["persists"] and f[s]["persists"]]
    ratios = []
    for s in both:
        num, den = f[s]["cost_per_carer_step"], c[s]["cost_per_carer_step"]
        if math.isfinite(num) and math.isfinite(den) and den > 0:
            ratios.append(num / den)
    ratios = np.asarray(ratios, float)
    med = float(np.median(ratios)) if len(ratios) else math.nan
    ci = boot_ci(ratios, rng, np.median) if len(ratios) else [math.nan, math.nan]
    met = bool(len(ratios) > 0 and med >= 1.25 and ci[0] > 1.0)
    out.update({"cheapest_matching_arm": arm, "matching_median_costs": {a: median_cost(a) for a in matching},
                "seeds_both_persist": len(both), "ratios_used": len(ratios), "median_cost_ratio": med,
                "cost_ratio_ci": ci, "outcome": "met" if met else "not met", "met": met})
    return out


def score(rows, k_series=None) -> dict:
    k_series = k_series or {}
    rng = np.random.default_rng(0)
    h1_cells = {}
    for st in ("rare", "weak"):
        h1_cells[st] = {"C_rate": rate(rows, "C", st), "C_vs_A": paired(rows, "C", "A", st, 0.40),
                        "C_vs_B": paired(rows, "C", "B", st, 0.40)}
    h1 = all(count(rows, "C", st) >= runs(0.80) and v["C_vs_A"]["met"] and v["C_vs_B"]["met"]
             for st, v in h1_cells.items())
    h2 = paired(rows, "C", "C-nolearn", "weak", 0.30)
    h3r = h3(rows, rng)
    arms = {}
    for arm, (_, _, starts) in CONFIRM_ARMS.items():
        for st in starts:
            cell = outcomes(rows, arm, st)
            per = [cell[s]["persists"] for s in CONFIRM_SEEDS]
            cost = [cell[s]["cost_per_carer_step"] for s in CONFIRM_SEEDS]
            arms[f"{arm}/{st}"] = {"persistence": float(np.mean(per)), "persistence_ci": boot_ci(per, rng),
                                   "cost_mean": float(np.nanmean(cost)), "cost_ci": boot_ci(cost, rng),
                                   "reached_cap_by_60": int(sum(cell[s]["reached_cap_by_60"] for s in CONFIRM_SEEDS)),
                                   "mean_k_0_60_end": [float(np.nanmean([cell[s][k] for s in CONFIRM_SEEDS]))
                                                       for k in ("mean_k_0", "mean_k_60", "mean_k_end")]}
    c = outcomes(rows, "C", "weak")
    fb = [c[s]["feedback_corr"] for s in CONFIRM_SEEDS]
    fbs = [c[s]["feedback_corr_shuffled"] for s in CONFIRM_SEEDS]
    descriptive = {
        "C_frozen_vs_C_weak": {"C": rate(rows, "C", "weak"), "C-frozen": rate(rows, "C-frozen", "weak")},
        "feedback_corr_C_weak": {"mean": float(np.nanmean(fb)), "ci": boot_ci(fb, rng),
                                 "shuffled_mean": float(np.nanmean(fbs)), "shuffled_ci": boot_ci(fbs, rng)},
        "C_mean_k_by_step": {st: mean_series([v for key, v in k_series.items() if key.startswith(st + "/")])
                             for st in ("rare", "weak")},
        "long_run_persistence_weak": {a: rate(rows, a, "weak", CONFIRM_LONG_STEPS) for a in CONFIRM_LONG_ARMS},
    }
    return {"H1": h1, "H1_cells": h1_cells, "H2": h2["met"], "H2_detail": h2, "H3": h3r["met"], "H3_detail": h3r,
            "arms": arms, "descriptive": descriptive}


def mean_series(series) -> list[float]:
    """Mean over runs at each step; extinct runs drop out (nan when none is left)."""
    if not series:
        return []
    n = max(len(x) for x in series)
    return [nanmean([x[t] for x in series if t < len(x)]) for t in range(0, n, 10)]


def jobs():
    out = [(arm, st, s, CONFIRM_STEPS) for arm, (_, _, starts) in CONFIRM_ARMS.items() for st in starts
           for s in CONFIRM_SEEDS]
    out += [(arm, "weak", s, CONFIRM_LONG_STEPS) for arm in CONFIRM_LONG_ARMS for s in CONFIRM_SEEDS]
    return out


def main() -> None:
    out = Path(DATA_DIR)
    with Pool(WORKERS) as pool:
        rows = pool.map(run_one, jobs(), chunksize=4)
    k_series = {}
    for r in rows:
        if "_k_series" in r:
            k_series[f"{r['start']}/{r['seed']}"] = r.pop("_k_series")
    (out / "confirm_k_series_C.json").write_text(json.dumps(k_series))
    fields = sorted({k for r in rows for k in r}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 99)
    with open(out / "confirm_runs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    verdict = score(rows, k_series)
    (out / "confirm_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: verdict[k] for k in ("H1", "H2", "H3")}, indent=1))


if __name__ == "__main__":
    main()
