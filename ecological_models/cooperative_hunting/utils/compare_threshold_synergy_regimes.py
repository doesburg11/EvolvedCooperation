#!/usr/bin/env python3
"""
Explicit 10000-step comparison for the threshold-synergy hunt family.

No CLI is used. Edit the configuration block below, then run:

  ./.conda/bin/python -m ecological_models.cooperative_hunting.utils.compare_threshold_synergy_regimes

This utility complements `compare_high_cooperation_regimes.py` by focusing on a
human-motivated threshold-synergy hunt rule. The baseline comparator remains a
separate script so the two mechanism families can be rerun independently.
"""

from __future__ import annotations

import contextlib
import csv
import io
import math
import os
import statistics as stats
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.cooperative_hunting.utils.compare_threshold_synergy_regimes'."
    )

from .. import cooperative_hunting as eco


# ============================================================
# COMPARISON CONFIG (edit here)
# ============================================================

steps = 10000
tail_window = 2000
seed_start = 0
seed_count = 5
cooperation_target = 0.50

out_dir = "./ecological_models/cooperative_hunting/images"
name_prefix = "threshold_synergy_regime_compare"

base_overrides: Dict[str, Any] = {
    "simulation_steps": steps,
    "enable_live_pygame_renderer": False,
    "plot_macro_energy_flows": False,
    "plot_trait_selection_diagnostics": False,
}


@dataclass(frozen=True)
class Scenario:
    name: str
    category: str
    description: str
    overrides: Dict[str, Any]


SCENARIOS: List[Scenario] = [
    Scenario(
        name="threshold_synergy_low_start",
        category="bootstrap_failure",
        description=(
            "Threshold-synergy rule under the former low-start emergence "
            "baseline. This tests whether coalition thresholds can bootstrap "
            "from the former near-zero initial trait regime."
        ),
        overrides={
            "hunt_success_rule": "threshold_synergy",
            "threshold_synergy_min_hunters": 2,
            "threshold_synergy_formation_energy_factor": 0.5,
            "threshold_synergy_execution_energy_factor": 0.8,
            "threshold_synergy_success_steepness": 1.0,
            "threshold_synergy_max_success_probability": 0.95,
            "predator_cooperation_cost_per_unit": 0.08,
            "predator_reproduction_probability": 0.04,
            "prey_reproduction_probability": 0.074,
            "initial_predator_count": 85,
            "initial_predator_energy": 2.2,
            "initial_predator_hunt_investment_trait_max": 0.05,
            "initial_prey_count": 575,
        },
    ),
    Scenario(
        name="threshold_synergy_supported_reference",
        category="supported_reference",
        description=(
            "Bootstrap-supported threshold-synergy regime. Predators start "
            "with higher energy, a modestly broader initial trait ceiling, "
            "and lower private cooperation cost so coalition hunts are "
            "reachable."
        ),
        overrides={
            "hunt_success_rule": "threshold_synergy",
            "threshold_synergy_min_hunters": 2,
            "threshold_synergy_formation_energy_factor": 0.5,
            "threshold_synergy_execution_energy_factor": 0.8,
            "threshold_synergy_success_steepness": 1.0,
            "threshold_synergy_max_success_probability": 0.95,
            "predator_cooperation_cost_per_unit": 0.02,
            "predator_reproduction_probability": 0.025,
            "prey_reproduction_probability": 0.082,
            "initial_predator_count": 65,
            "initial_predator_energy": 3.0,
            "initial_predator_hunt_investment_trait_max": 0.15,
            "initial_prey_count": 575,
        },
    ),
    Scenario(
        name="probabilistic_supported_counterfactual",
        category="mechanism_counterfactual",
        description=(
            "Same supported-start ecology as the threshold-synergy reference, "
            "but with the smoother probabilistic hunt rule."
        ),
        overrides={
            "hunt_success_rule": "probabilistic",
            "predator_cooperation_cost_per_unit": 0.02,
            "predator_reproduction_probability": 0.025,
            "prey_reproduction_probability": 0.082,
            "initial_predator_count": 65,
            "initial_predator_energy": 3.0,
            "initial_predator_hunt_investment_trait_max": 0.15,
            "initial_prey_count": 575,
            "base_hunt_success_probability": 0.50,
        },
    ),
    Scenario(
        name="threshold_synergy_supported_equal_split",
        category="payoff_counterfactual",
        description=(
            "Same supported-start threshold-synergy regime, but prey is split "
            "equally rather than contribution-weighted."
        ),
        overrides={
            "hunt_success_rule": "threshold_synergy",
            "threshold_synergy_min_hunters": 2,
            "threshold_synergy_formation_energy_factor": 0.5,
            "threshold_synergy_execution_energy_factor": 0.8,
            "threshold_synergy_success_steepness": 1.0,
            "threshold_synergy_max_success_probability": 0.95,
            "predator_cooperation_cost_per_unit": 0.02,
            "predator_reproduction_probability": 0.025,
            "prey_reproduction_probability": 0.082,
            "initial_predator_count": 65,
            "initial_predator_energy": 3.0,
            "initial_predator_hunt_investment_trait_max": 0.15,
            "initial_prey_count": 575,
            "share_prey_equally": True,
        },
    ),
    Scenario(
        name="threshold_synergy_supported_strict_quorum",
        category="mechanism_counterfactual",
        description=(
            "Same supported-start threshold-synergy regime, but with a "
            "stricter coalition requirement and higher execution threshold."
        ),
        overrides={
            "hunt_success_rule": "threshold_synergy",
            "threshold_synergy_min_hunters": 3,
            "threshold_synergy_formation_energy_factor": 0.6,
            "threshold_synergy_execution_energy_factor": 0.9,
            "threshold_synergy_success_steepness": 1.0,
            "threshold_synergy_max_success_probability": 0.95,
            "predator_cooperation_cost_per_unit": 0.02,
            "predator_reproduction_probability": 0.025,
            "prey_reproduction_probability": 0.082,
            "initial_predator_count": 65,
            "initial_predator_energy": 3.0,
            "initial_predator_hunt_investment_trait_max": 0.15,
            "initial_prey_count": 575,
        },
    ),
]


def mean_or_nan(values: List[float]) -> float:
    return stats.mean(values) if values else float("nan")


def format_float(value: float) -> str:
    return "nan" if math.isnan(value) else f"{value:.4f}"


def validate_overrides(raw_overrides: Dict[str, Any]) -> Dict[str, Any]:
    validated: Dict[str, Any] = {}
    for raw_key, value in raw_overrides.items():
        if raw_key not in eco.CFG:
            raise ValueError(f"Unknown config key '{raw_key}' in scenario overrides")
        validated[raw_key] = value
    return validated


def validate_scenarios(scenarios: List[Scenario]) -> None:
    seen = set()
    for scenario in scenarios:
        if scenario.name in seen:
            raise ValueError(f"Duplicate scenario name '{scenario.name}'")
        seen.add(scenario.name)
        validate_overrides(scenario.overrides)


def classify_outcome(final_pred_count: int, final_prey_count: int, extinction_step: int | None) -> str:
    if extinction_step is None and final_pred_count > 0 and final_prey_count > 0:
        return "survived"
    if final_prey_count <= 0:
        return "prey_extinction"
    if final_pred_count <= 0:
        return "predator_extinction"
    return "other"


def evaluate_scenario(scenario: Scenario) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    cfg = dict(eco.CFG)
    cfg.update(base_overrides)
    cfg.update(validate_overrides(scenario.overrides))

    replicate_rows: List[Dict[str, Any]] = []
    tail_means: List[float] = []
    final_means: List[float] = []
    extinction_steps: List[float] = []
    final_pred_counts: List[float] = []
    final_prey_counts: List[float] = []
    success_count = 0
    prey_extinction_count = 0
    predator_extinction_count = 0
    goal_hit_count = 0

    for seed in range(seed_start, seed_start + seed_count):
        with contextlib.redirect_stdout(io.StringIO()):
            (
                pred_hist,
                prey_hist,
                mean_hist,
                var_hist,
                success_hist,
                preds_final,
                renderer_closed,
                extinction_step,
            ) = eco.run_sim(seed_override=seed, config=cfg)

        final_pred_count = pred_hist[-1] if pred_hist else 0
        final_prey_count = prey_hist[-1] if prey_hist else 0
        tail_n = min(tail_window, len(mean_hist))
        tail_mean = mean_or_nan(mean_hist[-tail_n:]) if tail_n else float("nan")
        final_mean = mean_hist[-1] if mean_hist else float("nan")
        outcome = classify_outcome(final_pred_count, final_prey_count, extinction_step)
        survived = outcome == "survived"

        if survived:
            success_count += 1
        elif outcome == "prey_extinction":
            prey_extinction_count += 1
        elif outcome == "predator_extinction":
            predator_extinction_count += 1

        if extinction_step is not None:
            extinction_steps.append(float(extinction_step))
        if survived and tail_mean >= cooperation_target:
            goal_hit_count += 1

        tail_means.append(tail_mean)
        final_means.append(final_mean)
        final_pred_counts.append(float(final_pred_count))
        final_prey_counts.append(float(final_prey_count))

        replicate_rows.append(
            {
                "scenario": scenario.name,
                "category": scenario.category,
                "seed": seed,
                "outcome": outcome,
                "survived": int(survived),
                "extinction_step": "" if extinction_step is None else extinction_step,
                "final_pred_count": final_pred_count,
                "final_prey_count": final_prey_count,
                "tail_mean_trait": tail_mean,
                "final_mean_trait": final_mean,
                "goal_hit": int(survived and tail_mean >= cooperation_target),
            }
        )

    summary_row = {
        "scenario": scenario.name,
        "category": scenario.category,
        "description": scenario.description,
        "seed_start": seed_start,
        "seed_count": seed_count,
        "steps": steps,
        "tail_window": tail_window,
        "cooperation_target": cooperation_target,
        "success_count": success_count,
        "success_rate": success_count / seed_count,
        "goal_hit_count": goal_hit_count,
        "goal_hit_rate": goal_hit_count / seed_count,
        "prey_extinction_count": prey_extinction_count,
        "predator_extinction_count": predator_extinction_count,
        "mean_extinction_step": mean_or_nan(extinction_steps),
        "tail_mean_trait_avg": mean_or_nan(tail_means),
        "tail_mean_trait_min": min(tail_means) if tail_means else float("nan"),
        "final_mean_trait_avg": mean_or_nan(final_means),
        "final_pred_count_avg": mean_or_nan(final_pred_counts),
        "final_prey_count_avg": mean_or_nan(final_prey_counts),
    }
    return summary_row, replicate_rows


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty CSV to {path}")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary_text(path: str, rows: List[Dict[str, Any]]) -> None:
    lines = [
        f"Threshold-synergy regime comparison ({seed_count} seeds, {steps} steps, tail_window={tail_window})",
        f"Target: survived run with tail_mean_trait >= {cooperation_target:.2f}",
        "",
    ]
    for row in rows:
        lines.append(
            f"{row['scenario']}: success={row['success_count']}/{seed_count}, "
            f"goal_hits={row['goal_hit_count']}/{seed_count}, "
            f"tail_avg={format_float(row['tail_mean_trait_avg'])}, "
            f"tail_min={format_float(row['tail_mean_trait_min'])}, "
            f"prey_ext={row['prey_extinction_count']}, "
            f"pred_ext={row['predator_extinction_count']}, "
            f"mean_ext_step={format_float(row['mean_extinction_step'])}"
        )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    validate_scenarios(SCENARIOS)
    os.makedirs(out_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_rows: List[Dict[str, Any]] = []
    replicate_rows: List[Dict[str, Any]] = []
    for scenario in SCENARIOS:
        summary_row, scenario_replicates = evaluate_scenario(scenario)
        summary_rows.append(summary_row)
        replicate_rows.extend(scenario_replicates)

    summary_csv = os.path.join(out_dir, f"{name_prefix}_{timestamp}_summary.csv")
    replicate_csv = os.path.join(out_dir, f"{name_prefix}_{timestamp}_replicates.csv")
    summary_txt = os.path.join(out_dir, f"{name_prefix}_{timestamp}_summary.txt")

    write_csv(summary_csv, summary_rows)
    write_csv(replicate_csv, replicate_rows)
    write_summary_text(summary_txt, summary_rows)

    print(
        f"Threshold-synergy regime comparison completed for {len(summary_rows)} scenarios.",
        flush=True,
    )
    for row in summary_rows:
        print(
            f"{row['scenario']}: "
            f"success={row['success_count']}/{seed_count}, "
            f"goal_hits={row['goal_hit_count']}/{seed_count}, "
            f"tail_avg={format_float(row['tail_mean_trait_avg'])}, "
            f"prey_ext={row['prey_extinction_count']}, "
            f"pred_ext={row['predator_extinction_count']}",
            flush=True,
        )
    print(f"Summary CSV: {summary_csv}", flush=True)
    print(f"Replicate CSV: {replicate_csv}", flush=True)
    print(f"Summary TXT: {summary_txt}", flush=True)


if __name__ == "__main__":
    main()
