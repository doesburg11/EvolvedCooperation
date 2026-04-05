#!/usr/bin/env python3
"""
Explicit 10000-step comparison of payoff and ecology counterfactuals.

No CLI is used. Edit the configuration block below, then run:

  ./.conda/bin/python -m predpreygrass_cooperative_hunting_equal_split.utils.compare_high_cooperation_regimes

This utility is meant to answer a narrow question:

- can the model sustain long-horizon coexistence while pushing the mean hunt
  investment trait above a target threshold?

It compares a small set of named regimes under the same seed block and writes:

- a scenario-level summary CSV,
- a replicate-level CSV,
- a short text summary.
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
        "predpreygrass_cooperative_hunting_equal_split.utils.compare_high_cooperation_regimes'."
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

out_dir = "./predpreygrass_cooperative_hunting_equal_split/images"
name_prefix = "high_cooperation_regime_compare"

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
        name="active_baseline",
        category="baseline",
        description="Current active defaults evaluated at a 10000-step horizon.",
        overrides={},
    ),
    Scenario(
        name="high_trait_candidate",
        category="reference_high_trait",
        description=(
            "Best current >0.5 mean-trait candidate found so far; used as the "
            "reference high-cooperation but collapse-prone regime."
        ),
        overrides={
            "predator_cooperation_cost_per_unit": 0.04,
            "base_hunt_success_probability": 0.50,
            "prey_reproduction_probability": 0.082,
            "predator_reproduction_probability": 0.025,
            "initial_predator_count": 65,
        },
    ),
    Scenario(
        name="equal_split_counterfactual",
        category="payoff_mechanism",
        description=(
            "Same ecology as the high-trait reference, but prey is split "
            "equally instead of contribution-weighted."
        ),
        overrides={
            "predator_cooperation_cost_per_unit": 0.04,
            "base_hunt_success_probability": 0.50,
            "prey_reproduction_probability": 0.082,
            "predator_reproduction_probability": 0.025,
            "initial_predator_count": 65,
            "share_prey_equally": True,
        },
    ),
    Scenario(
        name="threshold_gate_counterfactual",
        category="payoff_mechanism",
        description=(
            "Same ecology as the high-trait reference, but the hunt rule is "
            "the harder energy-threshold gate."
        ),
        overrides={
            "predator_cooperation_cost_per_unit": 0.04,
            "base_hunt_success_probability": 0.50,
            "prey_reproduction_probability": 0.082,
            "predator_reproduction_probability": 0.025,
            "initial_predator_count": 65,
            "hunt_success_rule": "energy_threshold_gate",
        },
    ),
    Scenario(
        name="more_initial_prey_support",
        category="ecological_support",
        description=(
            "Same payoff mechanism as the high-trait reference, with a larger "
            "initial prey pool."
        ),
        overrides={
            "predator_cooperation_cost_per_unit": 0.04,
            "base_hunt_success_probability": 0.50,
            "prey_reproduction_probability": 0.082,
            "predator_reproduction_probability": 0.025,
            "initial_predator_count": 65,
            "initial_prey_count": 650,
        },
    ),
    Scenario(
        name="more_grass_support",
        category="ecological_support",
        description=(
            "Same payoff mechanism as the high-trait reference, with faster "
            "grass regrowth for prey."
        ),
        overrides={
            "predator_cooperation_cost_per_unit": 0.04,
            "base_hunt_success_probability": 0.50,
            "prey_reproduction_probability": 0.082,
            "predator_reproduction_probability": 0.025,
            "initial_predator_count": 65,
            "grass_regrowth_per_step": 0.06,
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
        f"High-cooperation regime comparison ({seed_count} seeds, {steps} steps, tail_window={tail_window})",
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
        f"High-cooperation regime comparison completed for {len(summary_rows)} scenarios.",
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
