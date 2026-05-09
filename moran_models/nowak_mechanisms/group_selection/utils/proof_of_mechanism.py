#!/usr/bin/env python3
"""Proof-of-mechanism for group selection — spread and maintenance.

Tests Nowak's condition: cooperation is favoured when between-group selection
is strong enough to overcome within-group defector advantage (m/n > c/b).

Default setup: 24×24 grid, 8 groups of 72 agents, group replacement every
25 steps.  b/c = 1.0/0.2 = 5.

Every group_selection_interval steps the group with the highest mean fitness
(most cooperators) overwrites the group with the lowest mean fitness.

Four scenarios:

  maintenance_common_start
    Cooperation starts high (≈ 0.9).  Tests ESS: does between-group copying
    prevent defectors from eroding a cooperative population?

  spread_from_rare
    Cooperation starts rare (≈ 0.05).  Tests the "Possible" claim: can
    group selection carry cooperation from rare when between-group events
    occasionally copy a cooperator-rich group over a defector-rich group?
    Outcome is stochastic across seeds.

  moore_no_groups_ablation
    Moore neighbourhood (k=8 > b/c=5) disables the spatial clustering
    advantage; group_selection_interval=99999 disables between-group
    copying.  Both mechanisms removed: cooperation should collapse.
    Baseline for the next scenario.

  moore_with_group_selection
    Same Moore neighbourhood (spatial structure broken) but group selection
    active (interval=25).  Tests whether between-group copying alone can
    enable cooperation even when the spatial mechanism cannot.  A clean
    isolation: any cooperation that emerges here is due to group selection,
    not spatial assortment.

Run from the repo root:
    ./.conda/bin/python -m moran_models.nowak_mechanisms.group_selection.utils.proof_of_mechanism
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from moran_models.nowak_mechanisms.group_selection.config.group_selection_config import config
from moran_models.nowak_mechanisms.group_selection.group_selection_model import run_simulation


SEEDS = [0, 1, 2, 3, 4]
SIMULATION_STEPS = 1000
SUMMARY_INTERVAL_STEPS = 1000
OUT_DIR = Path("moran_models/nowak_mechanisms/group_selection/data")

SUCCESS_FINAL_MEAN_TRAIT = 0.60

SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "maintenance_common_start",
        {
            # Cooperation starts high.  Group selection keeps defectors out.
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
        },
    ),
    (
        "spread_from_rare",
        {
            # Cooperation starts rare.  Group selection may carry a lucky
            # cooperator-rich group to fixation — stochastic, "Possible".
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
        },
    ),
    (
        "moore_no_groups_ablation",
        {
            # Moore neighbourhood (k=8 > b/c=5) breaks spatial clustering.
            # interval=99999 disables group copying.  Both mechanisms off:
            # cooperation should fail from any starting point.
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
            "neighborhood_mode": "moore",
            "group_selection_interval": 99999,
        },
    ),
    (
        "moore_with_group_selection",
        {
            # Moore neighbourhood (spatial advantage disabled) + group
            # selection active.  Any spread is due to between-group copying,
            # not spatial assortment — clean isolation of the mechanism.
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
    replicate_path = OUT_DIR / f"group_selection_proof_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"group_selection_proof_{stamp}_summary.csv"
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
