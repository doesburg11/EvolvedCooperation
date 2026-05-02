#!/usr/bin/env python3
"""Compare synchronous and asynchronous replacement in the well-mixed model.

Edit constants in this file, then run from the repo root:

./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.utils.proof_sync_vs_async_replacement
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from ..config.direct_reciprocity_well_mixed_async_config import config as async_config
from ..config.direct_reciprocity_well_mixed_config import config as sync_config
from ..direct_reciprocity_well_mixed_async_model import DirectReciprocityWellMixedAsyncModel
from ..direct_reciprocity_well_mixed_model import DirectReciprocityWellMixedModel


SEEDS = [0, 1, 2, 3, 4]
SIMULATION_STEPS = 5000
SUMMARY_INTERVAL_STEPS = 5000
BURN_IN_FRACTION = 0.20
OUT_DIR = Path("moran_models/nowak_mechanisms/direct_reciprocity/well_mixed/data")

SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario": "sync_current_selection",
        "replacement": "synchronous_global",
        "model_class": DirectReciprocityWellMixedModel,
        "base_config": sync_config,
        "updates": {
            "partner_persistence_probability": 0.9,
            "selection_temperature": 0.18,
            "rounds_per_pair_per_step": 3,
        },
    },
    {
        "scenario": "sync_weak_selection",
        "replacement": "synchronous_global",
        "model_class": DirectReciprocityWellMixedModel,
        "base_config": sync_config,
        "updates": {
            "partner_persistence_probability": 0.9,
            "selection_temperature": 1.0,
            "rounds_per_pair_per_step": 3,
        },
    },
    {
        "scenario": "async_weak_selection",
        "replacement": "one_birth_one_death",
        "model_class": DirectReciprocityWellMixedAsyncModel,
        "base_config": async_config,
        "updates": {
            "partner_persistence_probability": 0.9,
            "selection_temperature": 1.0,
            "rounds_per_pair_per_step": 3,
        },
    },
    {
        "scenario": "async_weak_selection_no_memory",
        "replacement": "one_birth_one_death",
        "model_class": DirectReciprocityWellMixedAsyncModel,
        "base_config": async_config,
        "updates": {
            "partner_persistence_probability": 0.9,
            "selection_temperature": 1.0,
            "rounds_per_pair_per_step": 3,
            "memory_enabled": False,
        },
    },
    {
        "scenario": "async_weak_selection_no_persistence",
        "replacement": "one_birth_one_death",
        "model_class": DirectReciprocityWellMixedAsyncModel,
        "base_config": async_config,
        "updates": {
            "partner_persistence_probability": 0.0,
            "selection_temperature": 1.0,
            "rounds_per_pair_per_step": 3,
        },
    },
    {
        "scenario": "async_weak_selection_one_round",
        "replacement": "one_birth_one_death",
        "model_class": DirectReciprocityWellMixedAsyncModel,
        "base_config": async_config,
        "updates": {
            "partner_persistence_probability": 0.9,
            "selection_temperature": 1.0,
            "rounds_per_pair_per_step": 1,
        },
    },
]


def _time_average(history: list[dict[str, float]], key: str) -> float:
    start = int(len(history) * BURN_IN_FRACTION)
    values = [float(row[key]) for row in history[start:]]
    return float(mean(values)) if values else 0.0


def _run_one(scenario: dict[str, Any], seed: int) -> dict[str, Any]:
    cfg = dict(scenario["base_config"])
    cfg.update(dict(scenario["updates"]))
    cfg.update(
        {
            "random_seed": seed,
            "simulation_steps": SIMULATION_STEPS,
            "summary_interval_steps": SUMMARY_INTERVAL_STEPS,
            "write_log": False,
        }
    )

    model = scenario["model_class"](cfg)
    for _ in range(SIMULATION_STEPS):
        model.step()

    final = model.history[-1] if model.history else {}
    return {
        "scenario": scenario["scenario"],
        "replacement": scenario["replacement"],
        "seed": seed,
        "simulation_steps": SIMULATION_STEPS,
        "burn_in_fraction": BURN_IN_FRACTION,
        "partner_persistence_probability": float(cfg["partner_persistence_probability"]),
        "selection_temperature": float(cfg["selection_temperature"]),
        "rounds_per_pair_per_step": int(cfg["rounds_per_pair_per_step"]),
        "memory_enabled": int(bool(cfg["memory_enabled"])),
        "mean_cooperation_after_burn_in": _time_average(model.history, "mean_cooperation_rate"),
        "mean_ALLD_after_burn_in": _time_average(model.history, "ALLD_frequency"),
        "mean_reciprocal_after_burn_in": _time_average(model.history, "reciprocal_strategy_frequency"),
        "final_mean_cooperation_rate": float(final.get("mean_cooperation_rate", 0.0)),
        "final_ALLD_frequency": float(final.get("ALLD_frequency", 0.0)),
        "final_reciprocal_strategy_frequency": float(final.get("reciprocal_strategy_frequency", 0.0)),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["scenario"])].append(row)

    summary = []
    for scenario, scenario_rows in sorted(grouped.items()):
        coop_values = [float(row["mean_cooperation_after_burn_in"]) for row in scenario_rows]
        final_values = [float(row["final_mean_cooperation_rate"]) for row in scenario_rows]
        alld_values = [float(row["mean_ALLD_after_burn_in"]) for row in scenario_rows]
        reciprocal_values = [float(row["mean_reciprocal_after_burn_in"]) for row in scenario_rows]
        first = scenario_rows[0]
        summary.append(
            {
                "scenario": scenario,
                "replacement": first["replacement"],
                "replicate_count": len(scenario_rows),
                "simulation_steps": first["simulation_steps"],
                "partner_persistence_probability": first["partner_persistence_probability"],
                "selection_temperature": first["selection_temperature"],
                "rounds_per_pair_per_step": first["rounds_per_pair_per_step"],
                "memory_enabled": first["memory_enabled"],
                "mean_cooperation_after_burn_in": mean(coop_values),
                "std_cooperation_after_burn_in": pstdev(coop_values),
                "mean_final_cooperation_rate": mean(final_values),
                "mean_ALLD_after_burn_in": mean(alld_values),
                "mean_reciprocal_after_burn_in": mean(reciprocal_values),
            }
        )
    return summary


def main() -> None:
    rows = []
    total_runs = len(SCENARIOS) * len(SEEDS)
    run_index = 0
    for scenario in SCENARIOS:
        for seed in SEEDS:
            run_index += 1
            print(
                "[proof_sync_vs_async_replacement] "
                f"run {run_index}/{total_runs} scenario={scenario['scenario']} seed={seed}",
                flush=True,
            )
            rows.append(_run_one(scenario, seed))

    summary = _summarize(rows)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    replicate_path = OUT_DIR / f"direct_reciprocity_replacement_comparison_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"direct_reciprocity_replacement_comparison_{stamp}_summary.csv"
    _write_csv(replicate_path, rows)
    _write_csv(summary_path, summary)

    print(f"[proof_sync_vs_async_replacement] wrote replicates -> {replicate_path}")
    print(f"[proof_sync_vs_async_replacement] wrote summary    -> {summary_path}")
    for row in summary:
        print(
            f"{row['scenario']}: replacement={row['replacement']} "
            f"coop={float(row['mean_cooperation_after_burn_in']):.3f} "
            f"final={float(row['mean_final_cooperation_rate']):.3f} "
            f"ALLD={float(row['mean_ALLD_after_burn_in']):.3f} "
            f"reciprocal={float(row['mean_reciprocal_after_burn_in']):.3f}"
        )


if __name__ == "__main__":
    main()
