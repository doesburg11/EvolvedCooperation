"""Verdicts for the pre-registered retained-fraction sweep (module README, "Pre-registration: retained-fraction sweep").

Run from the repository root after `run_r_sweep`:

    ./.conda/bin/python -m ecological_models.retained_benefit.utils.analyze_r_sweep

Reads `data/r_sweep/runs.csv` and writes `data/r_sweep/verdict.json`. The rules below are the registered ones.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

if not __package__:
    raise SystemExit(
        "Run from the repo root with "
        "'./.conda/bin/python -m ecological_models.retained_benefit.utils.analyze_r_sweep'."
    )

from scipy import stats

from .run_r_sweep import BC_RATIOS, COST, OUT_DIR, R_LEVELS, SEEDS, STEPS, build_arms

ALPHA = 0.01


def direct_payoff(bc: float, r: float, same_lineage_sites: int, neighborhood_size: int = 5) -> float:
    """Net direct payoff per unit trait from the producer's own output only (von Neumann incl. self).

    Open share: (1-r) b / neighborhood_size. Retained share: r b / same_lineage_sites (self is always one of them).
    """
    b = bc * COST
    return (1 - r) * b / neighborhood_size + r * b / same_lineage_sites - COST


def paired_one_sided(a: list[float], b: list[float], greater: bool) -> float:
    """One-sided paired t-test on seed-matched differences a_s - b_s (amendment A1).

    Returns NaN (undefined, counted as not significant) when fewer than two pairs exist or every difference
    is identical, checked on the values themselves rather than through a floating-point variance.
    """
    diffs = [x - y for x, y in zip(a, b, strict=True)]
    if len(diffs) < 2 or len(set(diffs)) == 1:
        return math.nan
    alt = "greater" if greater else "less"
    return float(stats.ttest_rel(a, b, alternative=alt).pvalue)


def classify(cell: list[float], neutral: list[float]) -> tuple[str, float, float]:
    """'rise', 'decline' or 'flat' against the seed-matched neutral arm; undefined p counts as not significant."""
    p_up = paired_one_sided(cell, neutral, greater=True)
    p_down = paired_one_sided(cell, neutral, greater=False)
    mean_diff = sum(cell) / len(cell) - sum(neutral) / len(neutral)
    if mean_diff > 0 and p_up < ALPHA:
        return "rise", mean_diff, p_up
    if mean_diff < 0 and p_down < ALPHA:
        return "decline", mean_diff, p_down
    defined = [p for p in (p_up, p_down) if not math.isnan(p)]
    return "flat", mean_diff, (min(defined) if defined else math.nan)


NUMERIC = ("bc", "r", "benefit", "cost", "initial_mean_cooperation", "final_mean_cooperation",
           "tail_mean_cooperation", "final_var_cooperation", "final_local_assortment",
           "final_dominant_lineage_share", "final_lineage_count", "seconds")


def _num(value, kind=float):
    """Parse a CSV field; malformed or blank values become NaN (float) or None (int) and fail validity later."""
    try:
        return kind(value)
    except (TypeError, ValueError):
        return math.nan if kind is float else None


def load_runs(path: Path) -> list[dict]:
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for k in NUMERIC:
            if k in row:
                row[k] = _num(row[k])
        row["seed"] = _num(row.get("seed"), int)
        row["steps"] = _num(row.get("steps"), int)
    return rows


def validity(rows: list[dict], manifest: dict) -> dict:
    arms = {a["arm"]: a for a in build_arms()}
    expected = {(name, s) for name in arms for s in SEEDS}
    keys = [(r.get("arm"), r.get("seed")) for r in rows]
    metadata_ok = all(
        r.get("arm") in arms
        and all(isinstance(r.get(k), (int, float)) and math.isclose(float(r[k]), float(arms[r["arm"]][k]), abs_tol=1e-12)
                for k in ("bc", "r", "benefit", "cost"))
        for r in rows
    )
    outcomes_ok = all(
        isinstance(r.get("tail_mean_cooperation"), float) and math.isfinite(r["tail_mean_cooperation"])
        and 0.0 <= r["tail_mean_cooperation"] <= 1.0 for r in rows
    )
    return {
        "replay_exact": isinstance(manifest, dict) and isinstance(manifest.get("replay_check"), dict)
        and manifest["replay_check"].get("replay_exact") is True,
        "all_runs_present": set(keys) == expected and len(keys) == len(expected),
        "arm_metadata_match": metadata_ok,
        "all_full_length": all(r.get("steps") == STEPS for r in rows),
        "outcomes_in_range": outcomes_ok,
    }


def _null(x):
    """JSON-safe: NaN becomes null."""
    if isinstance(x, float) and math.isnan(x):
        return None
    if isinstance(x, dict):
        return {k: _null(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_null(v) for v in x]
    return x


def analyze(rows: list[dict], manifest: dict) -> dict:
    valid = validity(rows, manifest)
    if not all(valid.values()):
        return {"validity": valid, "verdicts": {k: "invalid" for k in ("P1", "P2", "P3", "P4")},
                "interpretation": "invalid", "details": {}, "exploratory_r_star": {}, "cells": {}}

    by_arm: dict[str, list[float]] = {}
    for row in sorted(rows, key=lambda r: (r["arm"], r["seed"])):  # seed order makes the pairing explicit
        by_arm.setdefault(row["arm"], []).append(row["tail_mean_cooperation"])
    neutral = by_arm["neutral"]

    cells = {}
    for bc in BC_RATIOS:
        for r in R_LEVELS:
            arm = f"bc{bc}_r{r:.1f}"
            label, diff, p = classify(by_arm[arm], neutral)
            cells[arm] = {"bc": bc, "r": r, "mean": sum(by_arm[arm]) / len(by_arm[arm]), "diff_vs_neutral": diff,
                          "p": p, "class": label,
                          "direct_payoff_lone": direct_payoff(bc, r, 1), "direct_payoff_own_lineage": direct_payoff(bc, r, 5)}

    # P1: b/c = 8 -> every r cell rises.
    p1_rises = sum(cells[f"bc8_r{r:.1f}"]["class"] == "rise" for r in R_LEVELS)
    p1 = "met" if p1_rises == len(R_LEVELS) else "not met"
    # P2: b/c = 3, r = 0 -> the cell does not rise.
    p2 = "met" if cells["bc3_r0.0"]["class"] != "rise" else "not met"
    p2_undefined = cells["bc3_r0.0"]["p"] is None or (isinstance(cells["bc3_r0.0"]["p"], float) and math.isnan(cells["bc3_r0.0"]["p"]))
    # P3: b/c = 3, r = 1.0 above r = 0.0 (seed-matched, one-sided p < ALPHA).
    p3_p = paired_one_sided(by_arm["bc3_r1.0"], by_arm["bc3_r0.0"], greater=True)
    p3_diff = cells["bc3_r1.0"]["mean"] - cells["bc3_r0.0"]["mean"]
    p3 = "met" if (p3_diff > 0 and p3_p < ALPHA) else "not met"
    # P4 (amendment A1): b/c = 3, r = 1.0 rises above neutral.
    p4 = "met" if cells["bc3_r1.0"]["class"] == "rise" else "not met"
    # Narrowed reading (amendment A2): full retention improved on zero retention and exceeded neutral, while zero
    # retention showed no significant rise. This is consistent with, but does not establish, that retention is needed.
    needs_retention = "consistent" if (p2, p3, p4) == ("met", "met", "met") else "not consistent"

    # Exploratory: smallest sampled r from which every higher-r cell rises (a grid statistic, not a threshold).
    r_star = {}
    for bc in BC_RATIOS:
        found = None
        for r in R_LEVELS:
            if all(cells[f"bc{bc}_r{q:.1f}"]["class"] == "rise" for q in R_LEVELS if q >= r):
                found = r
                break
        r_star[str(bc)] = found

    return _null({"validity": valid, "verdicts": {"P1": p1, "P2": p2, "P3": p3, "P4": p4},
                  "interpretation": {"consistent_with_needing_retention_at_bc3": needs_retention},
                  "details": {"P1_rising_cells": p1_rises, "P2_p_undefined": p2_undefined,
                              "P3_diff": p3_diff, "P3_p": p3_p, "neutral_mean": sum(neutral) / len(neutral)},
                  "exploratory_r_star": r_star, "cells": cells})


def main() -> None:
    rows = load_runs(OUT_DIR / "runs.csv")
    manifest = json.loads((OUT_DIR / "manifest.json").read_text())
    result = analyze(rows, manifest)
    (OUT_DIR / "verdict.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({k: result[k] for k in ("validity", "verdicts", "interpretation", "details", "exploratory_r_star")}, indent=2))
    print(f"{'cell':<12}{'mean':>8}{'diff':>9}{'p':>10}  class   lone   own")
    for arm, c in result["cells"].items():
        p = "undef" if c["p"] is None else f"{c['p']:.2g}"
        print(f"{arm:<12}{c['mean']:8.4f}{c['diff_vs_neutral']:9.4f}{p:>10}  {c['class']:<7}"
              f"{c['direct_payoff_lone']:6.3f}{c['direct_payoff_own_lineage']:6.3f}")


if __name__ == "__main__":
    main()
