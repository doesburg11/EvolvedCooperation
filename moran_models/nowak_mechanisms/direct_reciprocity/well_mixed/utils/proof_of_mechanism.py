#!/usr/bin/env python3
"""Run direct-reciprocity well-mixed proof-of-mechanism checks.

Edit constants in this file, then run from the repo root:

./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.utils.proof_of_mechanism
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from ..config.direct_reciprocity_well_mixed_config import config
from ..direct_reciprocity_well_mixed_model import run_simulation


SEEDS = [0, 1, 2, 3, 4]
SIMULATION_STEPS = 500
SUMMARY_INTERVAL_STEPS = 500
OUT_DIR = Path("moran_models/nowak_mechanisms/direct_reciprocity/well_mixed/data")

SUCCESS_COOPERATION_RATE = 0.60
SUCCESS_RECIPROCAL_FREQUENCY = 0.50
SUCCESS_ALLD_MAX = 0.25

SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "default_mixed_start",
        {},
    ),
    (
        "rare_invaders_start",
        {
            "initial_strategy_layout": "rare_invaders",
            "rare_invaders_frequency": 0.05,
        },
    ),
    (
        "no_memory_ablation",
        {
            "initial_strategy_layout": "rare_invaders",
            "rare_invaders_frequency": 0.05,
            "memory_enabled": False,
        },
    ),
    (
        "one_round_ablation",
        {
            "initial_strategy_layout": "rare_invaders",
            "rare_invaders_frequency": 0.05,
            "rounds_per_pair_per_step": 1,
        },
    ),
]


def _run_one(scenario: str, updates: dict[str, Any], seed: int) -> dict[str, Any]:
    cfg = dict(config)
    cfg.update(updates)
    cfg.update(
        {
            "random_seed": seed,
            "simulation_steps": SIMULATION_STEPS,
            "summary_interval_steps": SUMMARY_INTERVAL_STEPS,
            "write_log": False,
        }
    )
    payload = run_simulation(cfg)
    success = (
        payload["final_mean_cooperation_rate"] >= SUCCESS_COOPERATION_RATE
        and payload["final_reciprocal_strategy_frequency"] >= SUCCESS_RECIPROCAL_FREQUENCY
        and payload["final_ALLD_frequency"] <= SUCCESS_ALLD_MAX
    )
    return {
        "scenario": scenario,
        "seed": seed,
        "success": int(success),
        "final_mean_cooperation_rate": payload["final_mean_cooperation_rate"],
        "final_reciprocal_strategy_frequency": payload["final_reciprocal_strategy_frequency"],
        "final_ALLD_frequency": payload["final_ALLD_frequency"],
        **{
            f"final_{name}_frequency": value
            for name, value in payload["final_strategy_frequencies"].items()
        },
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
        summary.append(
            {
                "scenario": scenario,
                "replicate_count": len(scenario_rows),
                "success_rate": mean(float(row["success"]) for row in scenario_rows),
                "mean_final_cooperation_rate": mean(
                    float(row["final_mean_cooperation_rate"]) for row in scenario_rows
                ),
                "mean_final_reciprocal_strategy_frequency": mean(
                    float(row["final_reciprocal_strategy_frequency"]) for row in scenario_rows
                ),
                "mean_final_ALLD_frequency": mean(
                    float(row["final_ALLD_frequency"]) for row in scenario_rows
                ),
            }
        )
    return summary


def main() -> None:
    rows = []
    total_runs = len(SCENARIOS) * len(SEEDS)
    run_index = 0
    for scenario, updates in SCENARIOS:
        for seed in SEEDS:
            run_index += 1
            print(f"[proof_of_mechanism] run {run_index}/{total_runs} scenario={scenario} seed={seed}")
            rows.append(_run_one(scenario, updates, seed))

    summary = _summarize(rows)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    replicate_path = OUT_DIR / f"direct_reciprocity_well_mixed_proof_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"direct_reciprocity_well_mixed_proof_{stamp}_summary.csv"
    _write_csv(replicate_path, rows)
    _write_csv(summary_path, summary)

    print(f"[proof_of_mechanism] wrote replicates -> {replicate_path}")
    print(f"[proof_of_mechanism] wrote summary    -> {summary_path}")
    for row in summary:
        print(
            f"{row['scenario']}: success_rate={float(row['success_rate']):.2f} "
            f"coop={float(row['mean_final_cooperation_rate']):.3f} "
            f"reciprocal={float(row['mean_final_reciprocal_strategy_frequency']):.3f} "
            f"ALLD={float(row['mean_final_ALLD_frequency']):.3f}"
        )


if __name__ == "__main__":
    main()
