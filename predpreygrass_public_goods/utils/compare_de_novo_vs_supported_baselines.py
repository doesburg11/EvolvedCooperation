#!/usr/bin/env python3
"""
Explicit 2x2 comparison of de novo low-start vs supported-start baselines.

No CLI is used. Edit the configuration block below, then run:

  ./.conda/bin/python -m predpreygrass_public_goods.utils.compare_de_novo_vs_supported_baselines

This utility isolates two design dimensions:

- start regime: de novo low-start vs bootstrap-supported start
- hunt mechanism: probabilistic vs threshold-synergy

The goal is to separate genuine low-start emergence from outcomes that require
initial scaffolding before coordinated hunting becomes feasible.
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
        "predpreygrass_public_goods.utils.compare_de_novo_vs_supported_baselines'."
    )

from .. import emerging_cooperation as eco


# ============================================================
# COMPARISON CONFIG (edit here)
# ============================================================

steps = 10000
tail_window = 2000
seed_start = 0
seed_count = 5
cooperation_target = 0.50

out_dir = "./predpreygrass_public_goods/images"
name_prefix = "de_novo_vs_supported_baselines"

base_overrides: Dict[str, Any] = {
    "simulation_steps": steps,
    "enable_live_pygame_renderer": False,
    "plot_macro_energy_flows": False,
    "plot_trait_selection_diagnostics": False,
}


@dataclass(frozen=True)
class Scenario:
    name: str
    row_group: str
    column_group: str
    description: str
    overrides: Dict[str, Any]


SCENARIOS: List[Scenario] = [
    Scenario(
        name="low_start_probabilistic",
        row_group="de_novo_low_start",
        column_group="probabilistic",
        description=(
            "Former de novo low-start emergence baseline: near-zero initial "
            "trait range and the smoother probabilistic hunt rule."
        ),
        overrides={
            "initial_predator_count": 85,
            "initial_prey_count": 575,
            "initial_predator_energy": 2.2,
            "initial_predator_hunt_investment_trait_min": 0.0,
            "initial_predator_hunt_investment_trait_max": 0.05,
            "predator_cooperation_cost_per_unit": 0.08,
            "predator_reproduction_probability": 0.04,
            "cooperation_mutation_probability": 0.12,
            "cooperation_mutation_stddev": 0.16,
            "hunt_success_rule": "probabilistic",
            "base_hunt_success_probability": 0.60,
            "hunter_pool_radius": 2,
            "share_prey_equally": False,
            "prey_reproduction_probability": 0.074,
        },
    ),
    Scenario(
        name="low_start_threshold_synergy",
        row_group="de_novo_low_start",
        column_group="threshold_synergy",
        description=(
            "Same low-start regime as the former de novo baseline, but with "
            "threshold-synergy hunting."
        ),
        overrides={
            "initial_predator_count": 85,
            "initial_prey_count": 575,
            "initial_predator_energy": 2.2,
            "initial_predator_hunt_investment_trait_min": 0.0,
            "initial_predator_hunt_investment_trait_max": 0.05,
            "predator_cooperation_cost_per_unit": 0.08,
            "predator_reproduction_probability": 0.04,
            "cooperation_mutation_probability": 0.12,
            "cooperation_mutation_stddev": 0.16,
            "hunt_success_rule": "threshold_synergy",
            "base_hunt_success_probability": 0.60,
            "hunter_pool_radius": 2,
            "threshold_synergy_min_hunters": 2,
            "threshold_synergy_formation_energy_factor": 0.5,
            "threshold_synergy_execution_energy_factor": 0.8,
            "threshold_synergy_success_steepness": 1.0,
            "threshold_synergy_max_success_probability": 0.95,
            "share_prey_equally": False,
            "prey_reproduction_probability": 0.074,
        },
    ),
    Scenario(
        name="supported_start_probabilistic",
        row_group="bootstrap_supported_start",
        column_group="probabilistic",
        description=(
            "Supported-start regime with the smoother probabilistic hunt rule. "
            "This tests whether scaffolding alone is enough."
        ),
        overrides={
            "initial_predator_count": 65,
            "initial_prey_count": 575,
            "initial_predator_energy": 3.0,
            "initial_predator_hunt_investment_trait_min": 0.0,
            "initial_predator_hunt_investment_trait_max": 0.15,
            "predator_cooperation_cost_per_unit": 0.02,
            "predator_reproduction_probability": 0.025,
            "cooperation_mutation_probability": 0.12,
            "cooperation_mutation_stddev": 0.16,
            "hunt_success_rule": "probabilistic",
            "base_hunt_success_probability": 0.50,
            "hunter_pool_radius": 2,
            "share_prey_equally": False,
            "prey_reproduction_probability": 0.082,
        },
    ),
    Scenario(
        name="supported_start_threshold_synergy",
        row_group="bootstrap_supported_start",
        column_group="threshold_synergy",
        description=(
            "Supported-start regime with threshold-synergy hunting. This is "
            "the current supported threshold baseline."
        ),
        overrides={
            "initial_predator_count": 65,
            "initial_prey_count": 575,
            "initial_predator_energy": 3.0,
            "initial_predator_hunt_investment_trait_min": 0.0,
            "initial_predator_hunt_investment_trait_max": 0.15,
            "predator_cooperation_cost_per_unit": 0.02,
            "predator_reproduction_probability": 0.025,
            "cooperation_mutation_probability": 0.12,
            "cooperation_mutation_stddev": 0.16,
            "hunt_success_rule": "threshold_synergy",
            "base_hunt_success_probability": 0.60,
            "hunter_pool_radius": 2,
            "threshold_synergy_min_hunters": 2,
            "threshold_synergy_formation_energy_factor": 0.5,
            "threshold_synergy_execution_energy_factor": 0.8,
            "threshold_synergy_success_steepness": 1.0,
            "threshold_synergy_max_success_probability": 0.95,
            "share_prey_equally": False,
            "prey_reproduction_probability": 0.082,
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
                "row_group": scenario.row_group,
                "column_group": scenario.column_group,
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
        "row_group": scenario.row_group,
        "column_group": scenario.column_group,
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
        f"De novo vs supported baseline matrix ({seed_count} seeds, {steps} steps, tail_window={tail_window})",
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
        f"De novo vs supported baseline matrix completed for {len(summary_rows)} scenarios.",
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
