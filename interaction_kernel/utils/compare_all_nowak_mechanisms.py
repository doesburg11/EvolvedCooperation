#!/usr/bin/env python3
"""Compare all five Nowak mechanism wrappers under matched parameter sweeps.

Run from repo root:
  ./.conda/bin/python -m interaction_kernel.utils.compare_all_nowak_mechanisms
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any

from direct_reciprocity.config.direct_reciprocity_config import config as direct_cfg
from direct_reciprocity.direct_reciprocity_model import run_simulation as run_direct
from group_selection.config.group_selection_config import config as group_cfg
from group_selection.group_selection_model import run_simulation as run_group
from indirect_reciprocity.config.indirect_reciprocity_config import config as indirect_cfg
from indirect_reciprocity.indirect_reciprocity_model import run_simulation as run_indirect
from kin_selection.config.kin_selection_config import config as kin_cfg
from kin_selection.kin_selection_model import run_simulation as run_kin
from network_reciprocity.config.network_reciprocity_config import config as net_cfg
from network_reciprocity.network_reciprocity_model import run_simulation as run_network

MECHANISMS: dict[str, tuple[dict[str, Any], Any]] = {
    "kin_selection": (kin_cfg, run_kin),
    "network_reciprocity": (net_cfg, run_network),
    "direct_reciprocity": (direct_cfg, run_direct),
    "indirect_reciprocity": (indirect_cfg, run_indirect),
    "group_selection": (group_cfg, run_group),
}

BENEFIT_SCALES = [0.8, 1.0, 1.2]
COST_SCALES = [0.10, 0.20, 0.30]
SEEDS = list(range(8))
SIMULATION_STEPS = 250
SUMMARY_INTERVAL_STEPS = 250


def _run_single(
    mechanism_name: str,
    base_cfg: dict[str, Any],
    runner: Any,
    benefit_scale: float,
    cost_scale: float,
    seed: int,
) -> dict[str, float | str | int]:
    cfg = dict(base_cfg)
    cfg["B_plus_scale"] = float(benefit_scale)
    cfg["C_scale"] = float(cost_scale)
    cfg["random_seed"] = int(seed)
    cfg["simulation_steps"] = int(SIMULATION_STEPS)
    cfg["summary_interval_steps"] = int(SUMMARY_INTERVAL_STEPS)
    cfg["write_log"] = False

    payload = runner(cfg)
    return {
        "mechanism": mechanism_name,
        "benefit_scale": float(benefit_scale),
        "cost_scale": float(cost_scale),
        "seed": int(seed),
        "final_mean_trait": float(payload["final_mean_trait"]),
        "final_std_trait": float(payload["final_std_trait"]),
    }


def _group_summary(rows: list[dict[str, float | str | int]]) -> list[dict[str, float | str]]:
    grouped: dict[tuple[str, float, float], list[float]] = {}
    for row in rows:
        key = (
            str(row["mechanism"]),
            float(row["benefit_scale"]),
            float(row["cost_scale"]),
        )
        grouped.setdefault(key, []).append(float(row["final_mean_trait"]))

    summary: list[dict[str, float | str]] = []
    for (mechanism, benefit_scale, cost_scale), values in sorted(grouped.items()):
        summary.append(
            {
                "mechanism": mechanism,
                "benefit_scale": benefit_scale,
                "cost_scale": cost_scale,
                "replicate_count": len(values),
                "mean_final_trait": fmean(values),
                "std_final_trait": pstdev(values) if len(values) > 1 else 0.0,
                "min_final_trait": min(values),
                "max_final_trait": max(values),
            }
        )
    return summary


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
                        f"[compare_all_nowak_mechanisms] run {run_i}/{total_runs} "
                        f"mechanism={mechanism_name} B={benefit_scale:.2f} C={cost_scale:.2f} seed={seed}"
                    )
                    row = _run_single(
                        mechanism_name,
                        base_cfg,
                        runner,
                        benefit_scale,
                        cost_scale,
                        seed,
                    )
                    rows.append(row)

    summary_rows = _group_summary(rows)

    out_dir = Path("interaction_kernel/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rep_path = out_dir / f"compare_all_nowak_mechanisms_{stamp}_replicates.csv"
    sum_path = out_dir / f"compare_all_nowak_mechanisms_{stamp}_summary.csv"
    txt_path = out_dir / f"compare_all_nowak_mechanisms_{stamp}_summary.txt"

    with rep_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "mechanism",
                "benefit_scale",
                "cost_scale",
                "seed",
                "final_mean_trait",
                "final_std_trait",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with sum_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "mechanism",
                "benefit_scale",
                "cost_scale",
                "replicate_count",
                "mean_final_trait",
                "std_final_trait",
                "min_final_trait",
                "max_final_trait",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    with txt_path.open("w", encoding="utf-8") as f:
        f.write("All Nowak mechanisms comparison (matched sweep)\n")
        f.write(f"replicates_csv: {rep_path}\n")
        f.write(f"summary_csv: {sum_path}\n\n")
        f.write(
            "columns: mechanism, benefit_scale, cost_scale, replicate_count, "
            "mean_final_trait, std_final_trait, min_final_trait, max_final_trait\n\n"
        )
        for row in summary_rows:
            f.write(
                f"{row['mechanism']:>20s}  B={float(row['benefit_scale']):.2f} "
                f"C={float(row['cost_scale']):.2f}  n={int(row['replicate_count'])}  "
                f"mean={float(row['mean_final_trait']):.4f}  "
                f"std={float(row['std_final_trait']):.4f}\n"
            )

    print(f"[compare_all_nowak_mechanisms] wrote replicates -> {rep_path}")
    print(f"[compare_all_nowak_mechanisms] wrote summary    -> {sum_path}")
    print(f"[compare_all_nowak_mechanisms] wrote text       -> {txt_path}")

    return {
        "replicates_csv": str(rep_path),
        "summary_csv": str(sum_path),
        "summary_text": str(txt_path),
    }


if __name__ == "__main__":
    run_comparison()
