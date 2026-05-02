#!/usr/bin/env python3
"""Proof of the stability-vs-invasion asymmetry in well-mixed direct reciprocity.

Demonstrates that:
  1. coop_majority_no_allc — cooperators already common: ALLD cannot invade, cooperation maintained.
  2. coop_majority_with_allc — same majority with exploitable ALLC included.
  3. alld_majority — ALLD majority (default start): cooperation emerges in some seeds only.
  4. small_reciprocal_foothold — 5% reciprocal in 95% ALLD: stochastic basin crossing.
  5. single_tft_invader — one TFT mutant in 199 ALLD: literal rare invasion test.

This directly shows that the Nowak condition w > (T-R)/(T-P) describes stability
(resisting ALLD invasion when cooperators are common), not invasion (spreading
from rare into an ALLD-majority population).

All scenarios use async one-birth/one-death replacement, weak selection
(temperature = 1.0), p = 0.9, memory enabled, and no recurrent mutation.
This isolates whether the initial reciprocal population can spread without new
strategy types being introduced later.

Run from the repository root:
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.utils.proof_stability_vs_invasion
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from ..config.direct_reciprocity_well_mixed_async_config import config as async_config
from ..direct_reciprocity_well_mixed_async_model import DirectReciprocityWellMixedAsyncModel


SEEDS = list(range(100))
SIMULATION_STEPS = 5000
SUMMARY_INTERVAL_STEPS = 5000
BURN_IN_FRACTION = 0.20
FINAL_COOPERATION_SUCCESS_THRESHOLD = 0.60
FINAL_RECIPROCAL_SUCCESS_THRESHOLD = 0.50
FINAL_ALLD_SUCCESS_THRESHOLD = 0.25
OUT_DIR = Path("moran_models/nowak_mechanisms/direct_reciprocity/well_mixed/data")

_BASE: dict[str, Any] = {
    "partner_persistence_probability": 0.9,
    "selection_temperature": 1.0,
    "rounds_per_pair_per_step": 3,
    "mutation_rate": 0.0,
}

_SINGLE_INVADER_FREQUENCY = 1.0 / float(async_config["n_sites"])

SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario": "coop_majority_no_allc",
        "description": "95 % reciprocal, 5 % ALLD, 0 % ALLC — clean stability test",
        "updates": {
            **_BASE,
            "initial_strategy_layout": "random",
            "initial_strategy_frequencies": {
                "ALLD": 0.05,
                "ALLC": 0.00,
                "TFT": 0.32,
                "GTFT": 0.36,
                "WSLS": 0.27,
            },
        },
    },
    {
        "scenario": "coop_majority_with_allc",
        "description": "90 % reciprocal, 5 % ALLD, 5 % ALLC — ALLC confound",
        "updates": {
            **_BASE,
            "initial_strategy_layout": "random",
            "initial_strategy_frequencies": {
                "ALLD": 0.05,
                "ALLC": 0.05,
                "TFT": 0.30,
                "GTFT": 0.35,
                "WSLS": 0.25,
            },
        },
    },
    {
        "scenario": "alld_majority",
        "description": "55 % ALLD start — default mix, cooperation emerges in some seeds",
        "updates": {
            **_BASE,
            "initial_strategy_layout": "random",
            "initial_strategy_frequencies": {
                "ALLD": 0.55,
                "ALLC": 0.05,
                "TFT": 0.15,
                "GTFT": 0.15,
                "WSLS": 0.10,
            },
        },
    },
    {
        "scenario": "small_reciprocal_foothold",
        "description": "5 % reciprocal in 95 % ALLD — stochastic finite-population basin crossing",
        "updates": {
            **_BASE,
            "initial_strategy_layout": "small_reciprocal_foothold",
            "small_reciprocal_foothold_frequency": 0.05,
            "foothold_strategy_frequencies": {
                "TFT": 0.34,
                "GTFT": 0.33,
                "WSLS": 0.33,
            },
        },
    },
    {
        "scenario": "single_tft_invader",
        "description": "1 TFT in 199 ALLD — literal rare-mutant invasion test",
        "updates": {
            **_BASE,
            "initial_strategy_layout": "small_reciprocal_foothold",
            "small_reciprocal_foothold_frequency": _SINGLE_INVADER_FREQUENCY,
            "foothold_strategy_frequencies": {
                "TFT": 1.00,
            },
        },
    },
]


def _time_average(history: list[dict[str, float]], key: str) -> float:
    start = int(len(history) * BURN_IN_FRACTION)
    values = [float(row[key]) for row in history[start:]]
    return float(mean(values)) if values else 0.0


def _run_one(scenario: dict[str, Any], seed: int) -> dict[str, Any]:
    cfg = dict(async_config)
    cfg.update(dict(scenario["updates"]))
    cfg.update(
        {
            "random_seed": seed,
            "simulation_steps": SIMULATION_STEPS,
            "summary_interval_steps": SIMULATION_STEPS,
            "write_log": False,
        }
    )
    model = DirectReciprocityWellMixedAsyncModel(cfg)
    for _ in range(SIMULATION_STEPS):
        model.step()

    final = model.history[-1] if model.history else {}
    final_mean_cooperation_rate = float(final.get("mean_cooperation_rate", 0.0))
    final_reciprocal_strategy_frequency = float(
        final.get("reciprocal_strategy_frequency", 0.0)
    )
    final_ALLD_frequency = float(final.get("ALLD_frequency", 0.0))
    final_threshold_success = (
        final_mean_cooperation_rate >= FINAL_COOPERATION_SUCCESS_THRESHOLD
        and final_reciprocal_strategy_frequency >= FINAL_RECIPROCAL_SUCCESS_THRESHOLD
        and final_ALLD_frequency <= FINAL_ALLD_SUCCESS_THRESHOLD
    )
    return {
        "scenario": scenario["scenario"],
        "seed": seed,
        "simulation_steps": SIMULATION_STEPS,
        "burn_in_fraction": BURN_IN_FRACTION,
        "partner_persistence_probability": float(cfg["partner_persistence_probability"]),
        "selection_temperature": float(cfg["selection_temperature"]),
        "rounds_per_pair_per_step": int(cfg["rounds_per_pair_per_step"]),
        "mean_cooperation_after_burn_in": _time_average(model.history, "mean_cooperation_rate"),
        "mean_ALLD_after_burn_in": _time_average(model.history, "ALLD_frequency"),
        "mean_reciprocal_after_burn_in": _time_average(model.history, "reciprocal_strategy_frequency"),
        "final_mean_cooperation_rate": final_mean_cooperation_rate,
        "final_ALLD_frequency": final_ALLD_frequency,
        "final_reciprocal_strategy_frequency": final_reciprocal_strategy_frequency,
        "final_threshold_success": int(final_threshold_success),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["scenario"])].append(row)

    summary = []
    for scenario_name, scenario_rows in sorted(grouped.items()):
        coop_values = [float(r["mean_cooperation_after_burn_in"]) for r in scenario_rows]
        final_values = [float(r["final_mean_cooperation_rate"]) for r in scenario_rows]
        alld_values = [float(r["mean_ALLD_after_burn_in"]) for r in scenario_rows]
        reciprocal_values = [float(r["mean_reciprocal_after_burn_in"]) for r in scenario_rows]
        success_values = [int(r["final_threshold_success"]) for r in scenario_rows]
        first = scenario_rows[0]
        summary.append(
            {
                "scenario": scenario_name,
                "replicate_count": len(scenario_rows),
                "simulation_steps": first["simulation_steps"],
                "partner_persistence_probability": first["partner_persistence_probability"],
                "selection_temperature": first["selection_temperature"],
                "rounds_per_pair_per_step": first["rounds_per_pair_per_step"],
                "mean_cooperation_after_burn_in": mean(coop_values),
                "std_cooperation_after_burn_in": pstdev(coop_values),
                "mean_final_cooperation_rate": mean(final_values),
                "mean_ALLD_after_burn_in": mean(alld_values),
                "mean_reciprocal_after_burn_in": mean(reciprocal_values),
                "final_threshold_success_count": sum(success_values),
                "final_threshold_success_fraction": mean(success_values),
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
                "[proof_stability_vs_invasion] "
                f"run {run_index}/{total_runs} scenario={scenario['scenario']} seed={seed}",
                flush=True,
            )
            rows.append(_run_one(scenario, seed))

    summary = _summarize(rows)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    replicate_path = OUT_DIR / f"direct_reciprocity_stability_vs_invasion_{stamp}_replicates.csv"
    summary_path = OUT_DIR / f"direct_reciprocity_stability_vs_invasion_{stamp}_summary.csv"
    _write_csv(replicate_path, rows)
    _write_csv(summary_path, summary)

    print(f"\n[proof_stability_vs_invasion] wrote replicates -> {replicate_path}")
    print(f"[proof_stability_vs_invasion] wrote summary    -> {summary_path}\n")
    for row in summary:
        print(
            f"  {row['scenario']:20s}  coop={float(row['mean_cooperation_after_burn_in']):.3f}"
            f" ± {float(row['std_cooperation_after_burn_in']):.3f}"
            f"  final={float(row['mean_final_cooperation_rate']):.3f}"
            f"  ALLD={float(row['mean_ALLD_after_burn_in']):.3f}"
            f"  success={int(row['final_threshold_success_count'])}/{int(row['replicate_count'])}"
        )


if __name__ == "__main__":
    main()
