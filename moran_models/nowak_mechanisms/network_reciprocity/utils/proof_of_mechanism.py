#!/usr/bin/env python3
"""Proof-of-mechanism for network reciprocity — spread and maintenance.

Tests Nowak's condition: cooperation spreads and is maintained when b/c > k,
where k is the number of spatial neighbours.

Default grid: 24×24 von Neumann neighbourhood (k=4). Default b/c = 1.0/0.2 = 5.
Condition met: 5 > 4.

Four scenarios:

  maintenance_common_start
    Cooperation starts high (≈ 0.9), von Neumann (k=4), b/c=5 > k.
    Tests ESS: does local clustering maintain cooperation against defector
    invasion?

  spread_from_rare
    Cooperation starts rare (≈ 0.05), same neighbourhood and b/c.
    Tests spread: can cooperator clusters form and expand from a low initial
    frequency?  Stochastic cluster formation means outcomes vary across seeds
    — demonstrating the "Partial" claim in the spread column of Display 2.

  below_bc_k_threshold
    Common start (≈ 0.9), but B_plus_scale=0.5 → b/c=2.5 < k=4.
    Condition violated: cooperation should collapse even when common.
    Proves the b/c > k boundary.

  moore_neighbourhood_ablation
    Common start (≈ 0.9), b/c=5, but neighbourhood switched to Moore (k=8).
    Now b/c=5 < k=8: condition violated by increasing k rather than decreasing
    b/c.  Confirms that k (network degree) is the relevant parameter.

Run from the repo root:
    ./.conda/bin/python -m moran_models.nowak_mechanisms.network_reciprocity.utils.proof_of_mechanism
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from moran_models.nowak_mechanisms.network_reciprocity.config.network_reciprocity_config import config
from moran_models.nowak_mechanisms.network_reciprocity.network_reciprocity_model import run_simulation


SEEDS = [0, 1, 2, 3, 4]
SIMULATION_STEPS = 1000
SUMMARY_INTERVAL_STEPS = 1000
OUT_DIR = Path("moran_models/nowak_mechanisms/network_reciprocity/data")

SUCCESS_FINAL_MEAN_TRAIT = 0.60

SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "maintenance_common_start",
        {
            # b/c=5 > k=4 (von Neumann).  Cooperation starts high — tests ESS.
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
        },
    ),
    (
        "spread_from_rare",
        {
            # b/c=5 > k=4.  Cooperation starts rare — tests whether clusters
            # form and grow.  Stochastic: demonstrates the "Partial" claim.
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
        },
    ),
    (
        "below_bc_k_threshold",
        {
            # B_plus_scale=0.5 → b/c = 0.5/0.2 = 2.5 < k=4.
            # Condition violated: cooperation should collapse from common start.
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
            "B_plus_scale": 0.5,
        },
    ),
    (
        "moore_neighbourhood_ablation",
        {
            # Moore neighbourhood: k=8 > b/c=5.  Same payoffs, larger k —
            # condition violated by network degree, not by payoff ratio.
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
            "neighborhood_mode": "moore",
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
    return {
        "scenario": scenario,
        "seed": seed,
        "success": int(final_trait >= SUCCESS_FINAL_MEAN_TRAIT),
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
    replicate_path = OUT_DIR / f"network_reciprocity_proof_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"network_reciprocity_proof_{stamp}_summary.csv"
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
