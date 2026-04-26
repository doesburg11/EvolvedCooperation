#!/usr/bin/env python3
"""
Sweep kin-selection model over kin bias ratio and benefit/cost ratio.
Writes replicate CSV, aggregate CSV, contour PNG, surface PNG, and TXT
interpretation.

Run from repo root:
  ./.conda/bin/python -m kin_selection.utils.sweep_kin_selection_phase
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from kin_selection.kin_selection_model import run_simulation
from kin_selection.config.kin_selection_config import config as base_config

OUTPUT_DIR = "kin_selection/data"
N_REPLICATES = 10
SIM_STEPS = 1000

KIN_BIAS_RATIOS = [8.0, 10.0, 12.0, 14.0, 16.0]
BENEFIT_COST_RATIOS = [3.5, 3.75, 4.0, 4.25, 4.5, 4.75]

KIN_WEIGHT_OTHER_LINEAGE = 1.0
C_SCALE = 0.2
MUTATION_RATE = 0.02


def _sweep_grid():
    for kin_bias_ratio in KIN_BIAS_RATIOS:
        for benefit_cost_ratio in BENEFIT_COST_RATIOS:
            yield {
                "kin_bias_ratio": kin_bias_ratio,
                "benefit_cost_ratio": benefit_cost_ratio,
                "kin_weight_same_lineage": kin_bias_ratio * KIN_WEIGHT_OTHER_LINEAGE,
                "kin_weight_other_lineage": KIN_WEIGHT_OTHER_LINEAGE,
                "B_plus_scale": benefit_cost_ratio * C_SCALE,
                "C_scale": C_SCALE,
                "mutation_rate": MUTATION_RATE,
            }


def _build_phase_matrix(rows: list[dict[str, float]]) -> np.ndarray:
    phase_matrix = np.full(
        (len(KIN_BIAS_RATIOS), len(BENEFIT_COST_RATIOS)),
        np.nan,
        dtype=float,
    )
    for i, kin_bias_ratio in enumerate(KIN_BIAS_RATIOS):
        for j, benefit_cost_ratio in enumerate(BENEFIT_COST_RATIOS):
            vals = [
                float(r["mean_final_trait"])
                for r in rows
                if float(r["kin_bias_ratio"]) == kin_bias_ratio
                and float(r["benefit_cost_ratio"]) == benefit_cost_ratio
            ]
            if vals:
                phase_matrix[i, j] = float(np.mean(vals))
    return phase_matrix


def _build_aggregate_rows(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    aggregate_rows = []
    for kin_bias_ratio in KIN_BIAS_RATIOS:
        for benefit_cost_ratio in BENEFIT_COST_RATIOS:
            cell_rows = [
                r
                for r in rows
                if float(r["kin_bias_ratio"]) == kin_bias_ratio
                and float(r["benefit_cost_ratio"]) == benefit_cost_ratio
            ]
            values = np.array(
                [float(r["mean_final_trait"]) for r in cell_rows],
                dtype=float,
            )
            if len(values) == 0:
                continue

            aggregate_rows.append(
                {
                    "kin_bias_ratio": kin_bias_ratio,
                    "benefit_cost_ratio": benefit_cost_ratio,
                    "n_replicates": len(values),
                    "mean_final_trait": float(np.mean(values)),
                    "std_final_trait_across_replicates": float(np.std(values)),
                    "min_final_trait_across_replicates": float(np.min(values)),
                    "max_final_trait_across_replicates": float(np.max(values)),
                }
            )
    return aggregate_rows


def _write_phase_chart(phase_matrix: np.ndarray, png_path: Path) -> None:
    x, y = np.meshgrid(BENEFIT_COST_RATIOS, KIN_BIAS_RATIOS)
    fig, ax = plt.subplots(figsize=(7.5, 5.6))
    filled = ax.contourf(
        x,
        y,
        phase_matrix,
        levels=np.linspace(0.0, 1.0, 21),
        cmap="viridis",
        vmin=0.0,
        vmax=1.0,
    )

    min_val = float(np.nanmin(phase_matrix))
    max_val = float(np.nanmax(phase_matrix))
    contour_levels = [
        level for level in (0.25, 0.50, 0.75) if min_val <= level <= max_val
    ]
    if contour_levels:
        lines = ax.contour(
            x,
            y,
            phase_matrix,
            levels=contour_levels,
            colors="white",
            linewidths=1.2,
        )
        ax.clabel(lines, inline=True, fmt="%.2f", fontsize=8)

    for i, kin_bias_ratio in enumerate(KIN_BIAS_RATIOS):
        for j, benefit_cost_ratio in enumerate(BENEFIT_COST_RATIOS):
            ax.text(
                benefit_cost_ratio,
                kin_bias_ratio,
                f"{phase_matrix[i, j]:.2f}",
                ha="center",
                va="center",
                color="black",
                fontsize=8,
                bbox={
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.70,
                    "pad": 1.0,
                },
            )

    ax.set_title(f"Kin selection mean cooperation after {SIM_STEPS} steps")
    ax.set_xlabel("benefit/cost ratio (B+ / C)")
    ax.set_ylabel("kin bias ratio (same-lineage / other-lineage)")
    ax.set_xticks(BENEFIT_COST_RATIOS)
    ax.set_yticks(KIN_BIAS_RATIOS)
    ax.set_xlim(BENEFIT_COST_RATIOS[0] - 0.15, BENEFIT_COST_RATIOS[-1] + 0.15)
    ax.set_ylim(KIN_BIAS_RATIOS[0] - 0.7, KIN_BIAS_RATIOS[-1] + 0.9)
    cbar = fig.colorbar(filled, ax=ax)
    cbar.set_label("mean final cooperation")
    fig.tight_layout()
    fig.savefig(png_path, dpi=180)
    plt.close(fig)


def _write_surface_chart(phase_matrix: np.ndarray, png_path: Path) -> None:
    x, y = np.meshgrid(BENEFIT_COST_RATIOS, KIN_BIAS_RATIOS)
    fig = plt.figure(figsize=(8.0, 6.0))
    ax = fig.add_subplot(111, projection="3d")
    surface = ax.plot_surface(
        x,
        y,
        phase_matrix,
        cmap="viridis",
        vmin=0.0,
        vmax=1.0,
        edgecolor="black",
        linewidth=0.25,
        antialiased=True,
    )
    ax.contour(
        x,
        y,
        phase_matrix,
        zdir="z",
        offset=0.0,
        levels=[0.25, 0.50, 0.75],
        colors="black",
        linewidths=0.8,
    )
    ax.set_title(f"Kin selection cooperation surface after {SIM_STEPS} steps")
    ax.set_xlabel("benefit/cost ratio (B+ / C)")
    ax.set_ylabel("kin bias ratio")
    ax.set_zlabel("mean final cooperation")
    ax.set_xticks(BENEFIT_COST_RATIOS)
    ax.set_yticks(KIN_BIAS_RATIOS)
    ax.set_xlim(BENEFIT_COST_RATIOS[0], BENEFIT_COST_RATIOS[-1])
    ax.set_ylim(KIN_BIAS_RATIOS[0], KIN_BIAS_RATIOS[-1])
    ax.set_zlim(0.0, 1.0)
    ax.view_init(elev=28, azim=-132)
    cbar = fig.colorbar(surface, ax=ax, shrink=0.72, pad=0.10)
    cbar.set_label("mean final cooperation")
    fig.tight_layout()
    fig.savefig(png_path, dpi=180)
    plt.close(fig)


def run_sweep():
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = out_dir / f"kin_selection_phase_{stamp}_summary.csv"
    aggregate_csv_path = out_dir / f"kin_selection_phase_{stamp}_aggregate.csv"
    txt_path = out_dir / f"kin_selection_phase_{stamp}_summary.txt"
    png_path = out_dir / f"kin_selection_phase_{stamp}_phase_map.png"
    surface_png_path = out_dir / f"kin_selection_phase_{stamp}_surface.png"

    fieldnames = [
        "kin_bias_ratio",
        "benefit_cost_ratio",
        "kin_weight_same_lineage",
        "kin_weight_other_lineage",
        "B_plus_scale",
        "C_scale",
        "mutation_rate",
        "replicate",
        "mean_final_trait",
        "std_final_trait",
        "min_final_trait",
        "max_final_trait",
    ]
    rows = []
    for params in _sweep_grid():
        for rep in range(N_REPLICATES):
            cfg = dict(base_config)
            cfg.update(params)
            cfg["random_seed"] = 1000 + rep
            cfg["simulation_steps"] = SIM_STEPS
            cfg["summary_interval_steps"] = SIM_STEPS
            cfg["write_log"] = False
            result = run_simulation(cfg)
            history_means = [float(h["mean_trait"]) for h in result["history"] if "mean_trait" in h]
            rows.append({
                **params,
                "replicate": rep,
                "mean_final_trait": result["final_mean_trait"],
                "std_final_trait": result["final_std_trait"],
                "min_final_trait": np.min(history_means) if history_means else np.nan,
                "max_final_trait": np.max(history_means) if history_means else np.nan,
            })
            print(
                "[sweep] "
                f"kin_bias_ratio={params['kin_bias_ratio']:.2f} "
                f"benefit_cost_ratio={params['benefit_cost_ratio']:.2f} "
                f"rep={rep} -> mean={result['final_mean_trait']:.3f}",
                flush=True,
            )

    # Write CSV
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    aggregate_rows = _build_aggregate_rows(rows)
    aggregate_fieldnames = [
        "kin_bias_ratio",
        "benefit_cost_ratio",
        "n_replicates",
        "mean_final_trait",
        "std_final_trait_across_replicates",
        "min_final_trait_across_replicates",
        "max_final_trait_across_replicates",
    ]
    with aggregate_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=aggregate_fieldnames)
        writer.writeheader()
        writer.writerows(aggregate_rows)

    phase_matrix = _build_phase_matrix(rows)
    _write_phase_chart(phase_matrix, png_path)
    _write_surface_chart(phase_matrix, surface_png_path)

    # Write TXT summary
    with txt_path.open("w", encoding="utf-8") as f:
        f.write("Kin selection phase sweep\n")
        f.write(f"Replicate CSV: {csv_path}\n")
        f.write(f"Aggregate CSV: {aggregate_csv_path}\n")
        f.write(f"2D PNG: {png_path}\n")
        f.write(f"3D PNG: {surface_png_path}\n\n")
        f.write("Parameter grid: kin_bias_ratio x benefit_cost_ratio\n")
        f.write(f"Simulation steps: {SIM_STEPS}\n")
        f.write(f"Replicates per cell: {N_REPLICATES}\n")
        f.write(f"Fixed C_scale: {C_SCALE}\n")
        f.write(f"Fixed kin_weight_other_lineage: {KIN_WEIGHT_OTHER_LINEAGE}\n")
        f.write(f"Each cell: mean final trait over {N_REPLICATES} replicates\n\n")
        f.write("Cells with mean final trait > 0.5:\n")
        for i, kin_bias_ratio in enumerate(KIN_BIAS_RATIOS):
            for j, benefit_cost_ratio in enumerate(BENEFIT_COST_RATIOS):
                val = phase_matrix[i, j]
                if val > 0.5:
                    f.write(
                        f"  kin_bias_ratio={kin_bias_ratio:.2f} "
                        f"benefit_cost_ratio={benefit_cost_ratio:.2f} -> {val:.2f}\n"
                    )

        f.write("\nLowest benefit/cost ratio with mean final trait > 0.5 by kin bias:\n")
        for i, kin_bias_ratio in enumerate(KIN_BIAS_RATIOS):
            above_threshold = [
                BENEFIT_COST_RATIOS[j]
                for j, val in enumerate(phase_matrix[i])
                if val > 0.5
            ]
            if above_threshold:
                f.write(
                    f"  kin_bias_ratio={kin_bias_ratio:.2f}: "
                    f"{min(above_threshold):.2f}\n"
                )
            else:
                f.write(f"  kin_bias_ratio={kin_bias_ratio:.2f}: none in grid\n")

    print(f"[sweep_kin_selection_phase] CSV  -> {csv_path}", flush=True)
    print(f"[sweep_kin_selection_phase] AGG  -> {aggregate_csv_path}", flush=True)
    print(f"[sweep_kin_selection_phase] PNG  -> {png_path}", flush=True)
    print(f"[sweep_kin_selection_phase] 3D   -> {surface_png_path}", flush=True)
    print(f"[sweep_kin_selection_phase] TXT  -> {txt_path}", flush=True)


if __name__ == "__main__":
    run_sweep()
