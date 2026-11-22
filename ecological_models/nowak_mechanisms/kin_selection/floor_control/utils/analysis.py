"""Scoring for the survival-floor test (README). Pure functions on run rows, unit-tested."""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np
from scipy.stats import fisher_exact, mannwhitneyu

from ..config.floor_config import (
    BOOTSTRAP, MIN_ANALYSABLE_RUNS, MIN_COHORT, MIN_POPULATION, SPREAD_MIN_FREQUENCY_INCREASE,
    SPREAD_MIN_TRAIT_INCREASE,
)


def persists(population: Sequence[int], window: tuple[int, int]) -> bool:
    """History index t = after step t; a run that died out has a shorter history and fails."""
    lo, hi = window
    return len(population) > hi and min(population[lo:hi + 1]) >= MIN_POPULATION


def last_finite(values) -> float:
    for v in reversed(list(values)):
        if v is not None and math.isfinite(float(v)):
            return float(v)
    return math.nan


def trait_change(history) -> float:
    return last_finite(history["mean_helping_trait"]) - float(history["mean_helping_trait"][0])


def frequency_change(history) -> float:
    return last_finite(history["helping_invasion_frequency"]) - float(history["helping_invasion_frequency"][0])


def spreads(persisted: bool, d_trait: float, d_freq: float) -> bool:
    return bool(persisted and math.isfinite(d_trait) and math.isfinite(d_freq)
                and d_trait >= SPREAD_MIN_TRAIT_INCREASE and d_freq >= SPREAD_MIN_FREQUENCY_INCREASE)


def hamilton(rows: list[dict[str, float]]) -> dict[str, Any]:
    """Queller regression for one run: w/mean(w) ~ 1 + h + s + male; r = slope of s on h; margin = r*b_s - c."""
    out = {"n": len(rows), "analysable": False}
    if len(rows) < MIN_COHORT:
        return out
    w = np.array([r["w"] for r in rows], float)
    h = np.array([r["h"] for r in rows], float)
    s = np.array([r["s"] for r in rows], float)
    male = np.array([r["male"] for r in rows], float)
    if w.mean() <= 0 or h.std() == 0 or s.std() == 0:
        return out
    X = np.column_stack([np.ones_like(h), h, s, male])
    if np.linalg.matrix_rank(X) < X.shape[1]:
        return out
    beta = np.linalg.lstsq(X, w / w.mean(), rcond=None)[0]
    b_h, b_s = float(beta[1]), float(beta[2])
    r = float(np.cov(s, h, ddof=0)[0, 1] / h.var())
    return {**out, "analysable": True, "b_h": b_h, "c": -b_h, "b_s": b_s, "r": r, "margin": r * b_s + b_h}


def boot_mean_ci(values, rng, draws=BOOTSTRAP) -> list[float]:
    v = np.asarray([x for x in values if math.isfinite(x)], float)
    if len(v) == 0:
        return [math.nan, math.nan]
    m = v[rng.integers(0, len(v), (draws, len(v)))].mean(1)
    return [float(x) for x in np.percentile(m, [2.5, 97.5])]


def boot_diff_ci(a, b, rng, draws=BOOTSTRAP) -> list[float]:
    a = np.asarray([x for x in a if math.isfinite(x)], float)
    b = np.asarray([x for x in b if math.isfinite(x)], float)
    if len(a) == 0 or len(b) == 0:
        return [math.nan, math.nan]
    d = a[rng.integers(0, len(a), (draws, len(a)))].mean(1) - b[rng.integers(0, len(b), (draws, len(b)))].mean(1)
    return [float(x) for x in np.percentile(d, [2.5, 97.5])]


def arm_hamilton(runs: list[dict[str, Any]], rng) -> dict[str, Any]:
    ok = [r for r in runs if r["ham"]["analysable"]]
    out = {"analysable_runs": len(ok), "enough": len(ok) >= MIN_ANALYSABLE_RUNS}
    for k in ("c", "b_s", "r", "margin"):
        vals = [r["ham"][k] for r in ok]
        out[k] = float(np.mean(vals)) if vals else math.nan
        out[k + "_ci"] = boot_mean_ci(vals, rng)
    return out


def score(main: dict[str, list[dict[str, Any]]], rng=None) -> dict[str, Any]:
    """main: arm -> list of run rows (persists, spreads, trait_change, ham, cohort rows for pooled)."""
    rng = rng or np.random.default_rng(0)
    n = {a: len(v) for a, v in main.items()}
    persist = {a: sum(r["persists"] for r in v) for a, v in main.items()}
    spread = {a: sum(r["spreads"] for r in v) for a, v in main.items()}
    dtrait = {a: [r["trait_change"] for r in v] for a, v in main.items()}

    h0 = all(persist[a] >= 36 for a in ("K", "U", "K-N", "U-N"))
    fisher_p = float(fisher_exact([[spread["K"], n["K"] - spread["K"]], [spread["U"], n["U"] - spread["U"]]],
                                  alternative="greater")[1])
    mw_ku = float(mannwhitneyu(dtrait["K"], dtrait["U"], alternative="greater").pvalue)
    h1 = bool(spread["K"] - spread["U"] >= 10 and fisher_p < 0.05 and mw_ku < 0.05)
    mw_kn = float(mannwhitneyu(dtrait["K"], dtrait["K-N"], alternative="greater").pvalue)
    h1b = bool(mw_kn < 0.05)
    med_gap = float(np.median(dtrait["U"]) - np.median(dtrait["U-N"]))
    h2 = bool(spread["U"] <= 4 and med_gap <= 0.005)

    ham = {a: arm_hamilton(main[a], rng) for a in ("K", "U")}
    k_ok = [r["ham"]["margin"] for r in main["K"] if r["ham"]["analysable"]]
    u_ok = [r["ham"]["margin"] for r in main["U"] if r["ham"]["analysable"]]
    diff_ci = boot_diff_ci(k_ok, u_ok, rng)
    enough = ham["K"]["enough"] and ham["U"]["enough"]
    h3_parts = {"K_margin_above_0": ham["K"]["margin_ci"][0] > 0, "K_cost_above_0": ham["K"]["c_ci"][0] > 0,
                "U_margin_not_above_0": not ham["U"]["margin_ci"][0] > 0, "K_minus_U_above_0": diff_ci[0] > 0}
    h3 = bool(enough and all(h3_parts.values()))
    if not h0:  # manipulation check failed: the design says stop, H1-H3 are not testable
        h1 = h1b = h2 = h3 = None
    return {
        "H0": h0, "H1": h1, "H1b": h1b, "H2": h2, "H3": h3,
        "H3_outcome": "not testable (H0 failed)" if not h0 else
        ("inconclusive" if not enough else ("met" if h3 else "not met")),
        "persist": persist, "spread": spread,
        "median_trait_change": {a: float(np.median(v)) for a, v in dtrait.items()},
        "H1_detail": {"spread_diff": spread["K"] - spread["U"], "fisher_p": fisher_p, "mannwhitney_p": mw_ku},
        "H1b_detail": {"mannwhitney_p": mw_kn},
        "H2_detail": {"U_spread": spread["U"], "median_gap_U_minus_UN": med_gap},
        "H3_detail": {"hamilton": ham, "margin_diff_ci": diff_ci, "parts": h3_parts},
    }


def pooled_hamilton(runs: list[dict[str, Any]], rng, draws=2000) -> dict[str, Any]:
    """Robustness: one regression over all cohort rows, interval by resampling runs."""
    per_run = [r["cohort"] for r in runs if r["cohort"]]
    if not per_run:
        return {"analysable": False}
    point = hamilton([x for c in per_run for x in c])
    if not point["analysable"]:
        return point
    margins = []
    for _ in range(draws):
        pick = rng.integers(0, len(per_run), len(per_run))
        res = hamilton([x for i in pick for x in per_run[i]])
        if res["analysable"]:
            margins.append(res["margin"])
    return {**point, "margin_ci": [float(x) for x in np.percentile(margins, [2.5, 97.5])] if margins else None}
