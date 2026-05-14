#!/usr/bin/env python3
"""Grid search for grandmother-effect parameters in ecological kin selection.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.utils.grandmother_grid_search
"""

from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.kin_selection.utils.grandmother_grid_search'."
    )

from ..config.kin_selection_config import config as active_config
from ..kin_selection_model import run_simulation


OUT_DIR = Path(str(active_config["data_dir"]))

# Parameter sweep definition.
SEEDS = list(range(20))
CAPACITY_MULTIPLIERS = [1.15, 1.30, 1.45, 1.60]
HOUSEHOLD_WEIGHT_BONUSES = [0.10, 0.25, 0.40, 0.55]


def _finite_mean(values: list[float]) -> float:
    finite_values = [value for value in values if math.isfinite(value)]
    if not finite_values:
        return math.nan
    return mean(finite_values)


def _score(success_rate: float, household_care_fraction: float) -> float:
    if not math.isfinite(success_rate):
        return -math.inf
    if not math.isfinite(household_care_fraction):
        return -math.inf
    # Balance proof robustness and stronger family-priority care.
    return (0.7 * success_rate) + (0.3 * household_care_fraction)


def _run_one(multiplier: float, bonus: float) -> dict[str, Any]:
    trait_changes: list[float] = []
    invasion_changes: list[float] = []
    hamilton_margins: list[float] = []
    final_populations: list[float] = []
    household_care_fractions: list[float] = []
    grandmother_care_fractions: list[float] = []
    grandmother_household_care_fractions: list[float] = []
    success_count = 0

    for seed in SEEDS:
        run_config = {
            "random_seed": seed,
            "write_latest_run": False,
            "enable_grandmother_effects": True,
            "grandmother_care_capacity_multiplier": multiplier,
            "grandmother_household_weight_bonus": bonus,
        }
        payload = run_simulation(run_config)
        summary = payload["summary"]

        trait_change = float(summary["helping_trait_change"])
        invasion_change = float(summary["helping_invasion_frequency_change"])
        hamilton_margin = float(summary["latest_hamilton_margin_proxy"])
        final_population = float(summary["final_population"])
        household_care_fraction = float(summary["latest_household_care_fraction"])
        grandmother_care_fraction = float(summary["latest_grandmother_care_fraction"])
        grandmother_household_care_fraction = float(
            summary["latest_grandmother_household_care_fraction"]
        )

        trait_changes.append(trait_change)
        invasion_changes.append(invasion_change)
        hamilton_margins.append(hamilton_margin)
        final_populations.append(final_population)
        household_care_fractions.append(household_care_fraction)
        grandmother_care_fractions.append(grandmother_care_fraction)
        grandmother_household_care_fractions.append(grandmother_household_care_fraction)

        is_success = (
            math.isfinite(trait_change)
            and math.isfinite(invasion_change)
            and trait_change >= float(active_config["proof_success_min_trait_increase"])
            and invasion_change
            >= float(active_config["proof_success_min_invasion_frequency_increase"])
            and hamilton_margin > float(active_config["proof_success_min_hamilton_margin_proxy"])
            and final_population >= float(active_config["proof_success_min_final_population"])
        )
        success_count += int(is_success)

    success_rate = success_count / len(SEEDS)
    mean_household_care_fraction = _finite_mean(household_care_fractions)
    return {
        "seed_count": len(SEEDS),
        "grandmother_care_capacity_multiplier": multiplier,
        "grandmother_household_weight_bonus": bonus,
        "success_rate": success_rate,
        "mean_helping_trait_change": _finite_mean(trait_changes),
        "mean_helping_invasion_frequency_change": _finite_mean(invasion_changes),
        "mean_hamilton_margin_proxy": _finite_mean(hamilton_margins),
        "mean_final_population": _finite_mean(final_populations),
        "mean_household_care_fraction": mean_household_care_fraction,
        "mean_grandmother_care_fraction": _finite_mean(grandmother_care_fractions),
        "mean_grandmother_household_care_fraction": _finite_mean(
            grandmother_household_care_fractions
        ),
        "composite_score": _score(success_rate, mean_household_care_fraction),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Cannot write empty grid-search table")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows: list[dict[str, Any]] = []
    total = len(CAPACITY_MULTIPLIERS) * len(HOUSEHOLD_WEIGHT_BONUSES)
    index = 0

    for multiplier in CAPACITY_MULTIPLIERS:
        for bonus in HOUSEHOLD_WEIGHT_BONUSES:
            index += 1
            print(
                "[ecological_kin_selection_grandmother_grid] "
                f"run {index}/{total} multiplier={multiplier:.2f} bonus={bonus:.2f}"
            )
            rows.append(_run_one(multiplier, bonus))

    rows = sorted(rows, key=lambda row: float(row["composite_score"]), reverse=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    table_path = OUT_DIR / f"ecological_kin_selection_grandmother_grid_{stamp}.csv"
    _write_csv(table_path, rows)

    print(f"\n[ecological_kin_selection_grandmother_grid] table -> {table_path}\n")
    top_n = min(5, len(rows))
    print("Top configurations:")
    for row in rows[:top_n]:
        print(
            "  "
            f"mult={float(row['grandmother_care_capacity_multiplier']):.2f} "
            f"bonus={float(row['grandmother_household_weight_bonus']):.2f} "
            f"success={float(row['success_rate']):.2f} "
            f"hh_care={float(row['mean_household_care_fraction']):.3f} "
            f"gma_care={float(row['mean_grandmother_care_fraction']):.3f} "
            f"score={float(row['composite_score']):.3f}"
        )


if __name__ == "__main__":
    main()
