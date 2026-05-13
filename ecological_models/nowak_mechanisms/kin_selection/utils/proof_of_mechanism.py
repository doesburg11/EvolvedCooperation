#!/usr/bin/env python3
"""Proof-of-mechanism ablations for ecological kin selection.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.utils.proof_of_mechanism
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.kin_selection.utils.proof_of_mechanism'."
    )

from ..config.kin_selection_config import PROOF_SCENARIOS, PROOF_SEEDS
from ..config.kin_selection_config import config as active_config
from ..config.kin_selection_config import resolve_scenario_config
from ..kin_selection_model import run_simulation


OUT_DIR = Path(str(active_config["data_dir"]))


def _finite_float(value: Any) -> float:
    if value is None:
        return math.nan
    value_float = float(value)
    return value_float if math.isfinite(value_float) else math.nan


def _finite_mean(values: list[float]) -> float:
    finite_values = [value for value in values if math.isfinite(value)]
    if not finite_values:
        return math.nan
    return mean(finite_values)


def _last_finite(history: dict[str, list[Any]], key: str) -> float:
    for value in reversed(history[key]):
        value_float = _finite_float(value)
        if math.isfinite(value_float):
            return value_float
    return math.nan


def _run_one(scenario: str, seed: int) -> dict[str, Any]:
    cfg = resolve_scenario_config(scenario, seed)
    payload = run_simulation(cfg)
    summary = payload["summary"]
    history = payload["history"]
    trait_change = float(summary["helping_trait_change"])
    invasion_frequency_change = float(summary["helping_invasion_frequency_change"])
    hamilton_margin_proxy = _last_finite(history, "hamilton_margin_proxy")
    final_population = int(summary["final_population"])
    success = (
        math.isfinite(trait_change)
        and math.isfinite(invasion_frequency_change)
        and trait_change >= float(cfg["proof_success_min_trait_increase"])
        and invasion_frequency_change
        >= float(cfg["proof_success_min_invasion_frequency_increase"])
        and hamilton_margin_proxy > float(cfg["proof_success_min_hamilton_margin_proxy"])
        and final_population >= int(cfg["proof_success_min_final_population"])
    )
    return {
        "scenario": scenario,
        "seed": seed,
        "success": int(success),
        "initial_mean_helping_trait": float(summary["initial_mean_helping_trait"]),
        "final_mean_helping_trait": float(summary["final_mean_helping_trait"]),
        "helping_trait_change": trait_change,
        "initial_helping_invasion_frequency": float(
            summary["initial_helping_invasion_frequency"]
        ),
        "final_helping_invasion_frequency": float(
            summary["final_helping_invasion_frequency"]
        ),
        "helping_invasion_frequency_change": invasion_frequency_change,
        "final_population": final_population,
        "final_juvenile_count": int(summary["final_juvenile_count"]),
        "final_adult_count": int(summary["final_adult_count"]),
        "latest_juvenile_survival_rate": _last_finite(
            history,
            "juvenile_survival_rate",
        ),
        "latest_total_care": _last_finite(history, "total_care"),
        "latest_mean_care_relatedness": _last_finite(
            history,
            "mean_care_relatedness",
        ),
        "latest_mean_available_care_relatedness": _last_finite(
            history,
            "mean_available_care_relatedness",
        ),
        "latest_care_assortment_gain": _last_finite(history, "care_assortment_gain"),
        "latest_kin_care_fraction": _last_finite(history, "kin_care_fraction"),
        "latest_expected_juvenile_survival_benefit": _last_finite(
            history,
            "expected_juvenile_survival_benefit",
        ),
        "latest_benefit_per_care_unit": _last_finite(history, "benefit_per_care_unit"),
        "latest_relatedness_weighted_survival_benefit": _last_finite(
            history,
            "relatedness_weighted_survival_benefit",
        ),
        "latest_total_helper_energy_cost": _last_finite(
            history,
            "total_helper_energy_cost",
        ),
        "latest_expected_helper_reproduction_cost": _last_finite(
            history,
            "expected_helper_reproduction_cost",
        ),
        "latest_hamilton_margin_proxy": hamilton_margin_proxy,
        "latest_fostered_birth_fraction": _last_finite(
            history,
            "fostered_birth_fraction",
        ),
        "mean_lifetime_offspring_rare_helpers": _finite_float(
            summary["mean_lifetime_offspring_rare_helpers"]
        ),
        "mean_lifetime_offspring_residents": _finite_float(
            summary["mean_lifetime_offspring_residents"]
        ),
        "lifetime_offspring_difference_rare_minus_resident": _finite_float(
            summary["lifetime_offspring_difference_rare_minus_resident"]
        ),
        "lifetime_offspring_ratio_rare_to_resident": _finite_float(
            summary["lifetime_offspring_ratio_rare_to_resident"]
        ),
        "lifetime_offspring_rare_helper_count": int(
            summary["lifetime_offspring_rare_helper_count"]
        ),
        "lifetime_offspring_resident_count": int(
            summary["lifetime_offspring_resident_count"]
        ),
        "latest_mean_mate_relatedness": _last_finite(history, "mean_mate_relatedness"),
        "latest_outside_group_mating_fraction": _last_finite(
            history,
            "outside_group_mating_fraction",
        ),
        "latest_close_kin_mate_rejections": int(
            _last_finite(history, "close_kin_mate_rejections")
        ),
    }


def _summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["scenario"])].append(row)

    summary = []
    for scenario, scenario_rows in sorted(grouped.items()):
        summary.append(
            {
                "scenario": scenario,
                "replicate_count": len(scenario_rows),
                "success_rate": mean(float(row["success"]) for row in scenario_rows),
                "mean_initial_helping_trait": mean(
                    float(row["initial_mean_helping_trait"]) for row in scenario_rows
                ),
                "mean_final_helping_trait": _finite_mean(
                    [float(row["final_mean_helping_trait"]) for row in scenario_rows]
                ),
                "mean_helping_trait_change": _finite_mean(
                    [float(row["helping_trait_change"]) for row in scenario_rows]
                ),
                "mean_initial_helping_invasion_frequency": _finite_mean(
                    [
                        float(row["initial_helping_invasion_frequency"])
                        for row in scenario_rows
                    ]
                ),
                "mean_final_helping_invasion_frequency": _finite_mean(
                    [
                        float(row["final_helping_invasion_frequency"])
                        for row in scenario_rows
                    ]
                ),
                "mean_helping_invasion_frequency_change": _finite_mean(
                    [
                        float(row["helping_invasion_frequency_change"])
                        for row in scenario_rows
                    ]
                ),
                "mean_final_population": mean(
                    float(row["final_population"]) for row in scenario_rows
                ),
                "mean_juvenile_survival_rate": _finite_mean(
                    [
                        float(row["latest_juvenile_survival_rate"])
                        for row in scenario_rows
                    ]
                ),
                "mean_care_relatedness": _finite_mean(
                    [
                        float(row["latest_mean_care_relatedness"])
                        for row in scenario_rows
                    ]
                ),
                "mean_available_care_relatedness": _finite_mean(
                    [
                        float(row["latest_mean_available_care_relatedness"])
                        for row in scenario_rows
                    ]
                ),
                "mean_care_assortment_gain": _finite_mean(
                    [
                        float(row["latest_care_assortment_gain"])
                        for row in scenario_rows
                    ]
                ),
                "mean_kin_care_fraction": _finite_mean(
                    [float(row["latest_kin_care_fraction"]) for row in scenario_rows]
                ),
                "mean_expected_juvenile_survival_benefit": _finite_mean(
                    [
                        float(row["latest_expected_juvenile_survival_benefit"])
                        for row in scenario_rows
                    ]
                ),
                "mean_benefit_per_care_unit": _finite_mean(
                    [
                        float(row["latest_benefit_per_care_unit"])
                        for row in scenario_rows
                    ]
                ),
                "mean_relatedness_weighted_survival_benefit": _finite_mean(
                    [
                        float(row["latest_relatedness_weighted_survival_benefit"])
                        for row in scenario_rows
                    ]
                ),
                "mean_total_helper_energy_cost": _finite_mean(
                    [
                        float(row["latest_total_helper_energy_cost"])
                        for row in scenario_rows
                    ]
                ),
                "mean_expected_helper_reproduction_cost": _finite_mean(
                    [
                        float(row["latest_expected_helper_reproduction_cost"])
                        for row in scenario_rows
                    ]
                ),
                "mean_hamilton_margin_proxy": _finite_mean(
                    [
                        float(row["latest_hamilton_margin_proxy"])
                        for row in scenario_rows
                    ]
                ),
                "mean_fostered_birth_fraction": _finite_mean(
                    [
                        float(row["latest_fostered_birth_fraction"])
                        for row in scenario_rows
                    ]
                ),
                "mean_lifetime_offspring_rare_helpers": _finite_mean(
                    [
                        float(row["mean_lifetime_offspring_rare_helpers"])
                        for row in scenario_rows
                    ]
                ),
                "mean_lifetime_offspring_residents": _finite_mean(
                    [
                        float(row["mean_lifetime_offspring_residents"])
                        for row in scenario_rows
                    ]
                ),
                "mean_lifetime_offspring_difference_rare_minus_resident": _finite_mean(
                    [
                        float(
                            row["lifetime_offspring_difference_rare_minus_resident"]
                        )
                        for row in scenario_rows
                    ]
                ),
                "mean_lifetime_offspring_ratio_rare_to_resident": _finite_mean(
                    [
                        float(row["lifetime_offspring_ratio_rare_to_resident"])
                        for row in scenario_rows
                    ]
                ),
                "mean_lifetime_offspring_rare_helper_count": _finite_mean(
                    [
                        float(row["lifetime_offspring_rare_helper_count"])
                        for row in scenario_rows
                    ]
                ),
                "mean_lifetime_offspring_resident_count": _finite_mean(
                    [
                        float(row["lifetime_offspring_resident_count"])
                        for row in scenario_rows
                    ]
                ),
                "mean_mate_relatedness": _finite_mean(
                    [float(row["latest_mean_mate_relatedness"]) for row in scenario_rows]
                ),
                "mean_outside_group_mating_fraction": _finite_mean(
                    [
                        float(row["latest_outside_group_mating_fraction"])
                        for row in scenario_rows
                    ]
                ),
                "mean_close_kin_mate_rejections": _finite_mean(
                    [
                        float(row["latest_close_kin_mate_rejections"])
                        for row in scenario_rows
                    ]
                ),
            }
        )
    return summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Cannot write an empty proof table")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = []
    scenario_names = [name for name, _ in PROOF_SCENARIOS]
    total = len(scenario_names) * len(PROOF_SEEDS)
    index = 0
    for scenario in scenario_names:
        for seed in PROOF_SEEDS:
            index += 1
            print(
                "[ecological_kin_selection_proof] "
                f"run {index}/{total} scenario={scenario} seed={seed}"
            )
            rows.append(_run_one(scenario, seed))

    summary = _summarize(rows)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    replicate_path = OUT_DIR / f"ecological_kin_selection_proof_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"ecological_kin_selection_proof_{stamp}_summary.csv"
    _write_csv(replicate_path, rows)
    _write_csv(summary_path, summary)

    print(f"\n[ecological_kin_selection_proof] replicates -> {replicate_path}")
    print(f"[ecological_kin_selection_proof] summary    -> {summary_path}\n")
    for row in summary:
        print(
            f"{row['scenario']}: "
            f"success_rate={float(row['success_rate']):.2f}  "
            f"delta_h={float(row['mean_helping_trait_change']):.4f}  "
            f"delta_freq={float(row['mean_helping_invasion_frequency_change']):.4f}  "
            f"final_h={float(row['mean_final_helping_trait']):.4f}  "
            f"care_r={float(row['mean_care_relatedness']):.3f}  "
            f"margin={float(row['mean_hamilton_margin_proxy']):.3f}  "
            "lrs_diff="
            f"{float(row['mean_lifetime_offspring_difference_rare_minus_resident']):.3f}"
        )


if __name__ == "__main__":
    main()
