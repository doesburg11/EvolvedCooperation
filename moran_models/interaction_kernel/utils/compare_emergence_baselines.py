#!/usr/bin/env python3
"""Compare non-direct Nowak mechanism baselines for cooperation emergence.

Run from repo root:
  ./.conda/bin/python -m moran_models.interaction_kernel.utils.compare_emergence_baselines
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any, Callable

from moran_models.nowak_mechanisms.group_selection.config.group_selection_config import config as group_cfg
from moran_models.nowak_mechanisms.group_selection.group_selection_model import run_simulation as run_group
from moran_models.nowak_mechanisms.indirect_reciprocity.config.indirect_reciprocity_config import config as indirect_cfg
from moran_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_model import (
    run_simulation as run_indirect,
)
from moran_models.nowak_mechanisms.kin_selection.config.kin_selection_config import config as kin_cfg
from moran_models.nowak_mechanisms.kin_selection.kin_selection_model import run_simulation as run_kin
from moran_models.nowak_mechanisms.network_reciprocity.config.network_reciprocity_config import (
    config as network_cfg,
)
from moran_models.nowak_mechanisms.network_reciprocity.network_reciprocity_model import (
    run_simulation as run_network,
)

Runner = Callable[[dict[str, Any] | None], dict[str, Any]]

MECHANISMS: dict[str, tuple[dict[str, Any], Runner]] = {
    "indirect_reciprocity": (indirect_cfg, run_indirect),
    "network_reciprocity": (network_cfg, run_network),
    "group_selection": (group_cfg, run_group),
    "kin_selection": (kin_cfg, run_kin),
}

BENEFIT_SCALES = [0.8, 1.0, 1.2]
COST_SCALES = [0.10, 0.20, 0.30]
SEEDS = list(range(8))
SIMULATION_STEPS = 250
SUMMARY_INTERVAL_STEPS = 250

SUCCESS_FINAL_TRAIT = 0.50
SUCCESS_MIN_GAIN = 0.05

OUT_DIR = Path("moran_models/interaction_kernel/data")


def _initial_mean_trait(payload: dict[str, Any], cfg: dict[str, Any]) -> float:
    history = payload.get("history", [])
    if history:
        return float(history[0]["mean_trait"])
    return float(cfg["initial_trait_mean"])


def _run_single(
    mechanism_name: str,
    base_cfg: dict[str, Any],
    runner: Runner,
    benefit_scale: float,
    cost_scale: float,
    seed: int,
) -> dict[str, float | str | int]:
    cfg = dict(base_cfg)
    cfg.update(
        {
            "B_plus_scale": float(benefit_scale),
            "C_scale": float(cost_scale),
            "random_seed": int(seed),
            "simulation_steps": int(SIMULATION_STEPS),
            "summary_interval_steps": int(SUMMARY_INTERVAL_STEPS),
            "write_log": False,
        }
    )

    payload = runner(cfg)
    initial_mean_trait = _initial_mean_trait(payload, cfg)
    final_mean_trait = float(payload["final_mean_trait"])
    trait_gain = final_mean_trait - initial_mean_trait
    emergence_success = (
        final_mean_trait >= SUCCESS_FINAL_TRAIT and trait_gain >= SUCCESS_MIN_GAIN
    )

    return {
        "mechanism": mechanism_name,
        "benefit_scale": float(benefit_scale),
        "cost_scale": float(cost_scale),
        "seed": int(seed),
        "initial_mean_trait": initial_mean_trait,
        "final_mean_trait": final_mean_trait,
        "trait_gain": trait_gain,
        "final_std_trait": float(payload["final_std_trait"]),
        "final_identity_count": int(payload["final_identity_count"]),
        "emergence_success": int(emergence_success),
    }


def _group_summary(rows: list[dict[str, float | str | int]]) -> list[dict[str, float | str]]:
    grouped: dict[tuple[str, float, float], list[dict[str, float | str | int]]] = {}
    for row in rows:
        key = (
            str(row["mechanism"]),
            float(row["benefit_scale"]),
            float(row["cost_scale"]),
        )
        grouped.setdefault(key, []).append(row)

    summary: list[dict[str, float | str]] = []
    for mechanism_name in MECHANISMS:
        for benefit_scale in BENEFIT_SCALES:
            for cost_scale in COST_SCALES:
                cell_rows = grouped.get((mechanism_name, benefit_scale, cost_scale), [])
                if not cell_rows:
                    continue
                initial_values = [float(row["initial_mean_trait"]) for row in cell_rows]
                final_values = [float(row["final_mean_trait"]) for row in cell_rows]
                gain_values = [float(row["trait_gain"]) for row in cell_rows]
                success_values = [float(row["emergence_success"]) for row in cell_rows]
                summary.append(
                    {
                        "mechanism": mechanism_name,
                        "benefit_scale": benefit_scale,
                        "cost_scale": cost_scale,
                        "replicate_count": len(cell_rows),
                        "mean_initial_trait": fmean(initial_values),
                        "mean_final_trait": fmean(final_values),
                        "std_final_trait": pstdev(final_values) if len(final_values) > 1 else 0.0,
                        "min_final_trait": min(final_values),
                        "max_final_trait": max(final_values),
                        "mean_trait_gain": fmean(gain_values),
                        "success_rate": fmean(success_values),
                    }
                )
    return summary


def _write_csv(path: Path, rows: list[dict[str, float | str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_summary_text(
    path: Path,
    replicate_path: Path,
    summary_path: Path,
    rows: list[dict[str, float | str]],
) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("Emergence baseline comparison for non-direct Nowak mechanisms\n")
        f.write(f"replicates_csv: {replicate_path}\n")
        f.write(f"summary_csv: {summary_path}\n\n")
        f.write(
            "success criterion: mean_final_trait >= "
            f"{SUCCESS_FINAL_TRAIT:.2f} and mean gain from low start >= {SUCCESS_MIN_GAIN:.2f}\n"
        )
        f.write(
            "columns: mechanism, benefit_scale, cost_scale, replicate_count, "
            "mean_initial_trait, mean_final_trait, std_final_trait, "
            "min_final_trait, max_final_trait, mean_trait_gain, success_rate\n\n"
        )
        for row in rows:
            f.write(
                f"{str(row['mechanism']):>22s}  "
                f"B={float(row['benefit_scale']):.2f}  "
                f"C={float(row['cost_scale']):.2f}  "
                f"n={int(row['replicate_count'])}  "
                f"initial={float(row['mean_initial_trait']):.4f}  "
                f"final={float(row['mean_final_trait']):.4f}  "
                f"gain={float(row['mean_trait_gain']):+.4f}  "
                f"success={float(row['success_rate']):.2f}\n"
            )


def run_comparison() -> dict[str, str]:
    rows: list[dict[str, float | str | int]] = []

    total_runs = len(MECHANISMS) * len(BENEFIT_SCALES) * len(COST_SCALES) * len(SEEDS)
    run_i = 0
    for mechanism_name, (base_cfg, runner) in MECHANISMS.items():
        for benefit_scale in BENEFIT_SCALES:
            for cost_scale in COST_SCALES:
                for seed in SEEDS:
                    run_i += 1
                    print(
                        f"[compare_emergence_baselines] run {run_i}/{total_runs} "
                        f"mechanism={mechanism_name} B={benefit_scale:.2f} "
                        f"C={cost_scale:.2f} seed={seed}"
                    )
                    rows.append(
                        _run_single(
                            mechanism_name,
                            base_cfg,
                            runner,
                            benefit_scale,
                            cost_scale,
                            seed,
                        )
                    )

    summary_rows = _group_summary(rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rep_path = OUT_DIR / f"compare_emergence_baselines_{stamp}_replicates.csv"
    sum_path = OUT_DIR / f"compare_emergence_baselines_{stamp}_summary.csv"
    txt_path = OUT_DIR / f"compare_emergence_baselines_{stamp}_summary.txt"

    _write_csv(rep_path, rows)
    _write_csv(sum_path, summary_rows)
    _write_summary_text(txt_path, rep_path, sum_path, summary_rows)

    print(f"[compare_emergence_baselines] wrote replicates -> {rep_path}")
    print(f"[compare_emergence_baselines] wrote summary    -> {sum_path}")
    print(f"[compare_emergence_baselines] wrote text       -> {txt_path}")

    return {
        "replicates_csv": str(rep_path),
        "summary_csv": str(sum_path),
        "summary_text": str(txt_path),
    }


if __name__ == "__main__":
    run_comparison()
