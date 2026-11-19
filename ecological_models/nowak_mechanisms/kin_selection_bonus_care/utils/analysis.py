"""Scoring for the bonus-care test (README pre-registration). Pure functions on run rows, unit-tested.

H0, H1, H1b, H2 and H3 use the floor test's scoring unchanged; this adds the step-0 rule, the cost probe and H0b.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np

from ...kin_selection_floor_control.utils.analysis import score as floor_score
from ..config.bonus_config import H0B_MAX_FRACTION_OF_K, H0B_MAX_U_RELATEDNESS, HAMILTON_R


def choose_mu(rows, mus, n_seeds, max_background) -> float | None:
    """Lowest mu at which every seed survives and the seeds' mean background relatedness is <= max_background."""
    for mu in sorted(mus):
        sel = [r for r in rows if r["mu"] == mu]
        if len(sel) == n_seeds and all(r["survived"] for r in sel):
            if float(np.mean([r["background_relatedness"] for r in sel])) <= max_background:
                return mu
    return None


def choose_cell(rows, costs, p0s, rearings, n_seeds) -> tuple[float, float] | None:
    """Lowest p0 whose no-helper control persists in all seeds in every rearing mode; ties -> highest cost."""
    for p0 in sorted(p0s):
        for cost in sorted(costs, reverse=True):
            if all(sum(r["persists"] for r in rows if r["p0"] == p0 and r["repro_cost"] == cost
                       and r["rearing"] == q) == n_seeds for q in rearings):
                return cost, p0
    return None


def kappa(runs: Sequence[Sequence[dict[str, float]]]) -> dict[str, Any]:
    """Minus the slope of (lifetime births / that run's mean births) on own h, pooled over runs' matured females."""
    h, y = [], []
    for females in runs:
        b = np.array([f["births"] for f in females], float)
        if len(b) == 0 or b.mean() <= 0:
            continue
        h.extend(f["h"] for f in females)
        y.extend(b / b.mean())
    h, y = np.asarray(h, float), np.asarray(y, float)
    if len(h) < 2 or h.var() == 0:
        return {"kappa": math.nan, "n_females": int(len(h))}
    slope = float(np.cov(y, h, ddof=0)[0, 1] / h.var())
    return {"kappa": -slope, "n_females": int(len(h))}


def best_case_margin(p0: float, kap: float, r: float = HAMILTON_R) -> float:
    """Theory screen: r * (1 - p0^4) / p0^4 - kappa (care lifts juvenile survival over 4 checks to 1)."""
    s0 = p0 ** 4
    return r * (1 - s0) / s0 - kap


def care_weighted_relatedness(total_care: Sequence[float], mean_rel: Sequence[float]) -> float:
    """Per run: sum(total care x mean care relatedness) / sum(total care) over steps with care."""
    num = den = 0.0
    for c, r in zip(total_care, mean_rel):
        if c > 0 and math.isfinite(r):
            num += c * r
            den += c
    return num / den if den > 0 else math.nan


def h0b(k_values: Sequence[float], u_values: Sequence[float]) -> dict[str, Any]:
    k = float(np.nanmean(k_values)) if np.isfinite(k_values).any() else math.nan
    u = float(np.nanmean(u_values)) if np.isfinite(u_values).any() else math.nan
    met = bool(math.isfinite(k) and math.isfinite(u) and u <= H0B_MAX_U_RELATEDNESS and u <= H0B_MAX_FRACTION_OF_K * k)
    return {"H0b": met, "K_care_relatedness": k, "U_care_relatedness": u}


def score(main: dict[str, list[dict[str, Any]]], rng=None) -> dict[str, Any]:
    out = floor_score(main, rng)
    rel = h0b([r["care_weighted_relatedness"] for r in main["K"]],
              [r["care_weighted_relatedness"] for r in main["U"]])
    out["H0b"] = rel["H0b"]
    out["H0b_detail"] = rel
    if out["H0"] and not rel["H0b"]:  # manipulation check failed: H1-H3 not testable
        out["H1"] = out["H1b"] = out["H2"] = out["H3"] = None
        out["H3_outcome"] = "not testable (H0b failed)"
    return out
