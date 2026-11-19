"""Scoring for ladder steps 0-1 (README). Pure functions, unit-tested."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from scipy.stats import fisher_exact, mannwhitneyu


def successes(rows: Sequence[dict[str, Any]]) -> int:
    return int(sum(r["success"] for r in rows))


def fisher_greater(a: int, n_a: int, b: int, n_b: int) -> float:
    return float(fisher_exact([[a, n_a - a], [b, n_b - b]], alternative="greater")[1])


def check_seeds(rows, seeds) -> None:
    got = sorted(r["seed"] for r in rows)
    if got != sorted(seeds):
        raise ValueError(f"arm has seeds {got}, expected {sorted(seeds)}")


def compare(kin_rows, nobias_rows, min_kin: int, min_diff: int | None, alpha: float = 0.05) -> dict[str, Any]:
    k, u = successes(kin_rows), successes(nobias_rows)
    p = fisher_greater(k, len(kin_rows), u, len(nobias_rows))
    ok = k >= min_kin and p < alpha and (min_diff is None or k - u >= min_diff)
    mw = float(mannwhitneyu([r["final_mean_trait"] for r in kin_rows], [r["final_mean_trait"] for r in nobias_rows],
                            alternative="greater").pvalue)
    return {"kin": k, "nobias": u, "fisher_p": p, "mannwhitney_p": mw, "met": bool(ok)}


def score_t0a(arms: dict[str, list]) -> dict[str, Any]:
    c = compare(arms["A-kin"], arms["A-nobias"], 15, None)
    below = successes(arms["A-below"])
    return {**c, "below_maintained": below, "met": bool(c["met"] and below <= 2)}


def score_t0b(arms: dict[str, list], nobias_trigger: int) -> dict[str, Any]:
    below = successes(arms["S-below"])
    primary = compare(arms["S-kin"], arms["S-nobias"], 15, 8)
    out = {"primary_B1": primary, "below_maintained": below,
           "low_b_triggered": successes(arms["S-nobias"]) >= nobias_trigger}
    if out["low_b_triggered"]:
        low = compare(arms["S-kin-0.6"], arms["S-nobias-0.6"], 12, 8)
        out["low_B0.6"] = low
        out["scored_at_B"] = 0.6
        out["met"] = bool(low["met"] and below <= 2)
    else:
        out["scored_at_B"] = 1.0
        out["met"] = bool(primary["met"] and below <= 2)
    return out


def score_t1(arms: dict[str, list], min_kin: int) -> dict[str, Any]:
    c = compare(arms["G-kin"], arms["G-nobias"], min_kin, 8)
    below = successes(arms["G-below"])
    return {**c, "below_maintained": below, "met": bool(c["met"] and below <= 2)}


def choose_mu(rows: Sequence[dict[str, Any]], mus: Sequence[float]) -> dict[str, Any]:
    """rows: per (mu, seed) with mean genomic and label contrast. Closest mean contrast; ties -> lower mu."""
    label = float(np.mean([r["label_contrast"] for r in rows]))
    gaps = {}
    for mu in mus:
        g = [r["genome_contrast"] for r in rows if r["mu"] == mu]
        gaps[mu] = abs(float(np.mean(g)) - label)
    low = min(gaps.values())
    best = min(m for m in mus if gaps[m] <= low + 1e-12)
    return {"mu_star": best, "label_contrast": label, "gaps": gaps}


def score_t0c(kin_rows, nobias_rows, below_rows, alpha: float) -> dict[str, Any]:
    """T0c: kin >= 15/20, >= 8 more than no-bias with one-sided Fisher p < alpha, below maintained <= 2/20."""
    c = compare(kin_rows, nobias_rows, 15, 8, alpha)
    below = successes(below_rows)
    return {**c, "alpha": alpha, "below_maintained": below, "met": bool(c["met"] and below <= 2)}
