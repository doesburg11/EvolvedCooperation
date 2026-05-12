#!/usr/bin/env python3
"""Proof-of-mechanism for kin selection in isolation — well-mixed population.

Tests whether kin-biased routing alone (without spatial structure) can spread
cooperation from rare. The spatial kin selection model confounds kin bias with
network reciprocity (local replacement on a grid). This model removes that
confound by using a fully connected population where every site is a neighbor
of every other site and replacement is global.

Three scenarios:

  spread_from_rare_kin_bias
    Cooperation starts rare (trait ≈ 0.05), fully connected population with
    kin-biased routing. The key test: does kin bias alone carry cooperation
    from rare without any spatial clustering?

  spread_from_rare_no_kin_bias
    Same rare start, fully connected, but equal kin weights (uniform routing).
    Pure well-mixed baseline. Cooperation should not spread — confirms the
    model is not trivially cooperative.

  maintenance_common_start
    Cooperation starts high (trait ≈ 0.9), fully connected, kin-biased.
    Tests ESS: does kin selection maintain cooperation once common, even
    without spatial structure?

Run from the repo root:
    ./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.well_mixed.utils.proof_of_mechanism
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from moran_models.nowak_mechanisms.kin_selection.kin_selection_model import run_simulation
from moran_models.nowak_mechanisms.kin_selection.well_mixed.config.kin_selection_well_mixed_config import (
    config,
)

SEEDS = [0, 1, 2, 3, 4]
SIMULATION_STEPS = 1000
SUMMARY_INTERVAL_STEPS = 1000
OUT_DIR = Path("moran_models/nowak_mechanisms/kin_selection/well_mixed/data")

SUCCESS_FINAL_MEAN_TRAIT = 0.60

SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "spread_from_rare_kin_bias",
        {
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
        },
    ),
    (
        "spread_from_rare_no_kin_bias",
        {
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
            "kin_weight_same_lineage": 0.5,
            "kin_weight_other_lineage": 0.5,
        },
    ),
    (
        "maintenance_common_start",
        {
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
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
    final_trait = float(payload["final_mean_trait"])
    success = final_trait >= SUCCESS_FINAL_MEAN_TRAIT
    return {
        "scenario": scenario,
        "seed": seed,
        "success": int(success),
        "final_mean_trait": final_trait,
        "final_std_trait": float(payload["final_std_trait"]),
        "final_identity_count": int(payload["final_identity_count"]),
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
                "success_rate": mean(float(r["success"]) for r in scenario_rows),
                "mean_final_trait": mean(float(r["final_mean_trait"]) for r in scenario_rows),
                "mean_final_std_trait": mean(float(r["final_std_trait"]) for r in scenario_rows),
            }
        )
    return summary


def main() -> None:
    rows = []
    total = len(SCENARIOS) * len(SEEDS)
    idx = 0
    for scenario, updates in SCENARIOS:
        for seed in SEEDS:
            idx += 1
            print(f"[proof_of_mechanism] run {idx}/{total} scenario={scenario} seed={seed}")
            rows.append(_run_one(scenario, updates, seed))

    summary = _summarize(rows)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    replicate_path = OUT_DIR / f"kin_selection_well_mixed_proof_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"kin_selection_well_mixed_proof_{stamp}_summary.csv"
    _write_csv(replicate_path, rows)
    _write_csv(summary_path, summary)

    print(f"\n[proof_of_mechanism] replicates -> {replicate_path}")
    print(f"[proof_of_mechanism] summary    -> {summary_path}\n")
    for row in summary:
        print(
            f"{row['scenario']}: "
            f"success_rate={float(row['success_rate']):.2f}  "
            f"mean_trait={float(row['mean_final_trait']):.3f}"
        )


if __name__ == "__main__":
    main()
