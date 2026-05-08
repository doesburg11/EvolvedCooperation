#!/usr/bin/env python3
"""Proof-of-mechanism checks for kin selection — spread and maintenance.

Four scenarios, each run over multiple seeds:

  maintenance_common_start
    Cooperation starts high (trait ≈ 0.9). Tests that kin-biased routing
    maintains cooperation against drift/mutation pressure (ESS condition).

  spread_from_rare_kin_bias
    Cooperation starts rare (trait ≈ 0.05). Tests that kin-biased routing
    allows cooperation to spread from rare — the key claim of the spread column.

  no_kin_bias_ablation
    Same rare start, but kin weights are equal (well-mixed). Tests that kin
    bias specifically, not just repeated interaction, is the spread mechanism.

  below_hamiltons_rule
    Common start, but B_plus_scale set so B/C < 1 (rb < c violated).
    Tests that Hamilton's rule failing causes cooperation to collapse even
    when it starts common — ESS boundary proof.

Run from the repo root:
    ./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.utils.proof_of_mechanism
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from moran_models.nowak_mechanisms.kin_selection.config.kin_selection_config import config
from moran_models.nowak_mechanisms.kin_selection.kin_selection_model import run_simulation


SEEDS = [0, 1, 2, 3, 4]
SIMULATION_STEPS = 1000
SUMMARY_INTERVAL_STEPS = 1000
OUT_DIR = Path("moran_models/nowak_mechanisms/kin_selection/data")

SUCCESS_FINAL_MEAN_TRAIT = 0.60

SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "maintenance_common_start",
        {
            # Cooperation starts high. Tests ESS: does kin selection maintain it?
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
        },
    ),
    (
        "spread_from_rare_kin_bias",
        {
            # Cooperation starts rare. Tests spread: does kin bias allow invasion?
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
        },
    ),
    (
        "no_kin_bias_ablation",
        {
            # Rare start, equal kin weights → well-mixed. Cooperation should not spread.
            # Proves kin bias is the mechanism, not repeated interaction alone.
            "initial_trait_mean": 0.05,
            "initial_trait_stddev": 0.02,
            "kin_weight_same_lineage": 0.5,
            "kin_weight_other_lineage": 0.5,
        },
    ),
    (
        "below_hamiltons_rule",
        {
            # Common start, but B/C = 0.25 (B_plus_scale=0.05, C_scale=0.2).
            # rb > c violated → cooperation should collapse even from high start.
            "initial_trait_mean": 0.9,
            "initial_trait_stddev": 0.05,
            "B_plus_scale": 0.05,
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
    replicate_path = OUT_DIR / f"kin_selection_proof_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"kin_selection_proof_{stamp}_summary.csv"
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
