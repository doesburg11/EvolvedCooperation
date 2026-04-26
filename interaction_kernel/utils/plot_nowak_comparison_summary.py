#!/usr/bin/env python3
"""Plot mechanism comparison surfaces from a summary CSV file.

Run from repo root:
  ./.conda/bin/python -m interaction_kernel.utils.plot_nowak_comparison_summary

Defaults:
- auto-picks latest compare_all_nowak_mechanisms_*_summary.csv
- writes a PNG figure to interaction_kernel/data/
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

AUTO_PICK_LATEST = True
SUMMARY_CSV_PATH = ""
OUTPUT_DIR = "interaction_kernel/data"


def _resolve_input_path() -> Path:
    if SUMMARY_CSV_PATH:
        path = Path(SUMMARY_CSV_PATH)
        if not path.exists():
            raise FileNotFoundError(f"Configured SUMMARY_CSV_PATH not found: {path}")
        return path

    if not AUTO_PICK_LATEST:
        raise FileNotFoundError("No summary input configured.")

    data_dir = Path(OUTPUT_DIR)
    candidates = sorted(data_dir.glob("compare_all_nowak_mechanisms_*_summary.csv"))
    if not candidates:
        raise FileNotFoundError(
            "No all-five summary CSV found. "
            "Run compare_all_nowak_mechanisms first or set SUMMARY_CSV_PATH."
        )
    return candidates[-1]


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _build_axes(rows: list[dict[str, str]]) -> tuple[list[str], list[float], list[float]]:
    mechanisms = sorted({row["mechanism"] for row in rows})
    benefits = sorted({float(row["benefit_scale"]) for row in rows})
    costs = sorted({float(row["cost_scale"]) for row in rows})
    return mechanisms, benefits, costs


def _to_matrix(
    rows: list[dict[str, str]],
    mechanism: str,
    benefits: list[float],
    costs: list[float],
) -> np.ndarray:
    matrix = np.full((len(costs), len(benefits)), np.nan, dtype=float)
    benefit_index = {value: i for i, value in enumerate(benefits)}
    cost_index = {value: i for i, value in enumerate(costs)}

    for row in rows:
        if row["mechanism"] != mechanism:
            continue
        b = float(row["benefit_scale"])
        c = float(row["cost_scale"])
        value = float(row["mean_final_trait"])
        matrix[cost_index[c], benefit_index[b]] = value

    return matrix


def run_plot() -> dict[str, str]:
    in_path = _resolve_input_path()
    rows = _load_rows(in_path)
    mechanisms, benefits, costs = _build_axes(rows)

    n_mech = len(mechanisms)
    n_cols = 3
    n_rows = int(np.ceil(n_mech / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5.2 * n_cols, 4.1 * n_rows), squeeze=False)

    all_values = [float(row["mean_final_trait"]) for row in rows]
    vmin = min(all_values)
    vmax = max(all_values)

    im = None
    for i, mechanism in enumerate(mechanisms):
        ax = axes[i // n_cols][i % n_cols]
        matrix = _to_matrix(rows, mechanism, benefits, costs)
        im = ax.imshow(matrix, cmap="Blues", vmin=vmin, vmax=vmax, aspect="auto")
        ax.set_title(mechanism)
        ax.set_xlabel("benefit scale (B+)")
        ax.set_ylabel("cost scale (C)")
        ax.set_xticks(range(len(benefits)))
        ax.set_xticklabels([f"{b:.2f}" for b in benefits])
        ax.set_yticks(range(len(costs)))
        ax.set_yticklabels([f"{c:.2f}" for c in costs])

        for r in range(matrix.shape[0]):
            for c in range(matrix.shape[1]):
                if np.isnan(matrix[r, c]):
                    continue
                ax.text(c, r, f"{matrix[r, c]:.3f}", ha="center", va="center", color="#0F3368", fontsize=9)

    for j in range(n_mech, n_rows * n_cols):
        axes[j // n_cols][j % n_cols].axis("off")

    if im is not None:
        cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.9)
        cbar.set_label("mean final trait")

    fig.suptitle("Nowak Mechanism Comparison (mean final trait)")
    fig.subplots_adjust(left=0.06, right=0.93, top=0.90, bottom=0.08, wspace=0.28, hspace=0.32)

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"compare_all_nowak_mechanisms_{stamp}_summary_plot.png"
    fig.savefig(out_path, dpi=180)
    plt.close(fig)

    print(f"[plot_nowak_comparison_summary] input  -> {in_path}")
    print(f"[plot_nowak_comparison_summary] figure -> {out_path}")
    return {
        "input_csv": str(in_path),
        "output_plot": str(out_path),
    }


if __name__ == "__main__":
    run_plot()
