#!/usr/bin/env python3
"""Proof-of-mechanism checks for indirect reciprocity — spread and maintenance.

Four scenarios test the two table claims (spread from rare = No, maintenance = Yes):

  maintenance_common_start
    Cooperation starts high (trait ≈ 0.9). Tests ESS: does reputation-weighted
    routing sustain cooperation against drift/mutation pressure?

  spread_from_rare
    Cooperation starts rare (trait ≈ 0.05). Tests the spread claim: reputation
    routing requires an existing cooperative base to bootstrap — rare cooperators
    earn no reputation advantage over defectors before being outcompeted.

  no_reputation_routing_ablation
    Common start, but reputation kernel exponent set to 0 so all recipients are
    weighted equally regardless of reputation. Tests that the reputation channel
    is the mechanism responsible for maintenance.

  majority_cooperative_start
    Cooperation starts at 50%. Tests the bootstrapping threshold: if reputation
    routing needs a cooperative majority to function, spread from 50% should
    succeed where spread from 5% fails.

Run from the repo root:
    ./.conda/bin/python -m moran_models.nowak_mechanisms.indirect_reciprocity.utils.proof_of_mechanism
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from moran_models.nowak_mechanisms.indirect_reciprocity.config.indirect_reciprocity_config import config
from moran_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_model import run_simulation


SEEDS = [0, 1, 2, 3, 4]
SIMULATION_STEPS = 1000
SUMMARY_INTERVAL_STEPS = 1000
OUT_DIR = Path("moran_models/nowak_mechanisms/indirect_reciprocity/data")

SUCCESS_FINAL_MEAN_TRAIT = 0.60

SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "maintenance_common_start",
        {
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
        },
    ),
    (
        "spread_from_rare",
        {
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
        },
    ),
    (
        "no_reputation_routing_ablation",
        {
            # reputation_kernel_exponent=0 → reputation^0 = 1 for all agents
            # → all recipients weighted equally → reputation channel disabled.
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
            "reputation_kernel_exponent": 0.0,
        },
    ),
    (
        "majority_cooperative_start",
        {
            # Start at 50%: tests whether the reputation system can bootstrap
            # from a cooperative majority that spread from rare cannot provide.
            "initial_trait_mean": 0.50,
            "initial_trait_stddev": 0.10,
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
    replicate_path = OUT_DIR / f"indirect_reciprocity_proof_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"indirect_reciprocity_proof_{stamp}_summary.csv"
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
