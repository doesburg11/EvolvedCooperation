#!/usr/bin/env python3
"""Proof-of-mechanism for Nowak's binary pairwise indirect reciprocity model.

Tests Nowak's exact condition: cooperation spreads when q > c/b.
With b=1.0 and c=0.2, the critical threshold is q = 0.2.

Four scenarios:

  maintenance_common_start
    q=0.80, init=0.9.  Tests ESS: reputation channel sustains cooperation
    when already common.

  spread_from_rare_high_q
    q=0.80 > c/b=0.20, init=0.05.  Nowak's "Yes" condition: reputation
    discrimination is strong enough that cooperators (high rep) are
    preferentially helped, giving them a fitness advantage over defectors
    (low rep, receive no help).  Cooperation should spread.

  spread_from_rare_low_q
    q=0.05 < c/b=0.20, init=0.05.  Nowak's "No" condition: reputation is
    rarely observed, so cooperators and defectors receive nearly the same
    help.  Cooperators pay cost c without compensation → eliminated.

  no_reputation_gating_ablation
    q=1.0 (always observe), threshold=0.0 (all recipients above threshold),
    init=0.9.  Removes all gating: every agent is helped regardless of
    reputation.  Defectors receive benefit without paying cost — they invade
    and cooperation collapses.  Proves that reputation-gated access, not
    reputation tracking alone, is the mechanism.

Run from the repo root:
    ./.conda/bin/python -m moran_models.nowak_mechanisms.indirect_reciprocity.well_mixed_binary.utils.proof_of_mechanism
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from moran_models.nowak_mechanisms.indirect_reciprocity.well_mixed_binary.config.indirect_reciprocity_binary_config import config
from moran_models.nowak_mechanisms.indirect_reciprocity.well_mixed_binary.indirect_reciprocity_binary_model import run_simulation


SEEDS = [0, 1, 2, 3, 4]
SIMULATION_STEPS = 2000
SUMMARY_INTERVAL_STEPS = 2000
OUT_DIR = Path("moran_models/nowak_mechanisms/indirect_reciprocity/well_mixed_binary/data")

SUCCESS_FINAL_MEAN_TRAIT = 0.60

# c/b = 0.2; q_high = 0.80 >> threshold; q_low = 0.05 < threshold.
SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "maintenance_common_start",
        {
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
            "reputation_observation_prob": 0.80,
        },
    ),
    (
        "spread_from_rare_high_q",
        {
            # q=0.80 > c/b=0.20 → Nowak's condition satisfied → should spread.
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
            "reputation_observation_prob": 0.80,
        },
    ),
    (
        "spread_from_rare_low_q",
        {
            # q=0.05 < c/b=0.20 → Nowak's condition violated → should fail.
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
            "reputation_observation_prob": 0.05,
        },
    ),
    (
        "no_reputation_gating_ablation",
        {
            # q=1.0, threshold=0.0: all recipients helped regardless of rep.
            # No gating → defectors receive b without paying c.
            # Start 50/50 cooperators/defectors so the fitness difference acts immediately.
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
            "initial_defector_fraction": 0.5,
            "reputation_observation_prob": 1.0,
            "reputation_threshold": 0.0,
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
        "final_mean_reputation": float(payload["final_mean_reputation"]),
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
                "mean_final_reputation": mean(
                    float(r["final_mean_reputation"]) for r in scenario_rows
                ),
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
    replicate_path = OUT_DIR / f"indirect_reciprocity_binary_proof_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"indirect_reciprocity_binary_proof_{stamp}_summary.csv"
    _write_csv(replicate_path, rows)
    _write_csv(summary_path, summary)

    print(f"\n[proof_of_mechanism] replicates -> {replicate_path}")
    print(f"[proof_of_mechanism] summary    -> {summary_path}\n")
    for row in summary:
        print(
            f"{row['scenario']}: "
            f"success_rate={float(row['success_rate']):.2f}  "
            f"mean_trait={float(row['mean_final_trait']):.3f}  "
            f"mean_rep={float(row['mean_final_reputation']):.3f}"
        )


if __name__ == "__main__":
    main()
