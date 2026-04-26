#!/usr/bin/env python3
"""Plot meaning-first comparison figures from a summary CSV file.

Run from repo root:
  ./.conda/bin/python -m interaction_kernel.utils.plot_nowak_comparison_summary

Defaults:
- auto-picks latest compare_all_nowak_mechanisms_*_summary.csv
- writes winner-map and delta-from-network-reciprocity PNG figures to
    interaction_kernel/data/
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import numpy as np

AUTO_PICK_LATEST = True
SUMMARY_CSV_PATH = ""
OUTPUT_DIR = "interaction_kernel/data"
BASELINE_MECHANISM = "network_reciprocity"

MECHANISM_DISPLAY_NAMES = {
    "direct_reciprocity": "Direct Reciprocity",
    "group_selection": "Group Selection",
    "indirect_reciprocity": "Indirect Reciprocity",
    "kin_selection": "Kin Selection",
    "network_reciprocity": "Network Reciprocity",
}

MECHANISM_COLORS = {
    "direct_reciprocity": "#E07A5F",
    "group_selection": "#3D405B",
    "indirect_reciprocity": "#2A9D8F",
    "kin_selection": "#E9C46A",
    "network_reciprocity": "#457B9D",
}


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


def _display_name(mechanism: str) -> str:
    return MECHANISM_DISPLAY_NAMES.get(mechanism, mechanism.replace("_", " ").title())


def _build_mechanism_matrices(
    rows: list[dict[str, str]],
    mechanisms: list[str],
    benefits: list[float],
    costs: list[float],
) -> dict[str, np.ndarray]:
    return {
        mechanism: _to_matrix(rows, mechanism, benefits, costs)
        for mechanism in mechanisms
    }


def _plot_winner_map(
    matrices: dict[str, np.ndarray],
    mechanisms: list[str],
    benefits: list[float],
    costs: list[float],
) -> plt.Figure:
    stack = np.stack([matrices[mechanism] for mechanism in mechanisms], axis=0)
    winner_indices = np.argmax(stack, axis=0)

    cmap = ListedColormap([MECHANISM_COLORS[mechanism] for mechanism in mechanisms])
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.imshow(winner_indices, cmap=cmap, aspect="auto", interpolation="nearest")
    ax.set_title("Winner Map: Highest Mean Final Trait")
    ax.set_xlabel("benefit scale (B+)")
    ax.set_ylabel("cost scale (C)")
    ax.set_xticks(range(len(benefits)))
    ax.set_xticklabels([f"{b:.2f}" for b in benefits])
    ax.set_yticks(range(len(costs)))
    ax.set_yticklabels([f"{c:.2f}" for c in costs])

    legend_handles = [
        Patch(facecolor=MECHANISM_COLORS[mechanism], label=_display_name(mechanism))
        for mechanism in mechanisms
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=2,
        frameon=False,
    )
    fig.subplots_adjust(left=0.11, right=0.98, top=0.88, bottom=0.28)
    return fig


def _plot_delta_panels(
    matrices: dict[str, np.ndarray],
    mechanisms: list[str],
    benefits: list[float],
    costs: list[float],
) -> plt.Figure:
    if BASELINE_MECHANISM not in matrices:
        raise ValueError(f"Baseline mechanism not found in summary CSV: {BASELINE_MECHANISM}")

    baseline = matrices[BASELINE_MECHANISM]
    comparison_mechanisms = [
        mechanism for mechanism in mechanisms if mechanism != BASELINE_MECHANISM
    ]
    deltas = {
        mechanism: matrices[mechanism] - baseline
        for mechanism in comparison_mechanisms
    }
    max_abs_delta = max(float(np.nanmax(np.abs(delta))) for delta in deltas.values())

    n_panels = len(comparison_mechanisms)
    n_cols = 2
    n_rows = int(np.ceil(n_panels / n_cols))
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(6.0 * n_cols, 4.1 * n_rows),
        squeeze=False,
    )

    image = None
    for index, mechanism in enumerate(comparison_mechanisms):
        ax = axes[index // n_cols][index % n_cols]
        image = ax.imshow(
            deltas[mechanism],
            cmap="RdBu_r",
            vmin=-max_abs_delta,
            vmax=max_abs_delta,
            aspect="auto",
            interpolation="nearest",
        )
        ax.set_title(f"{_display_name(mechanism)} - {_display_name(BASELINE_MECHANISM)}")
        ax.set_xlabel("benefit scale (B+)")
        ax.set_ylabel("cost scale (C)")
        ax.set_xticks(range(len(benefits)))
        ax.set_xticklabels([f"{b:.2f}" for b in benefits])
        ax.set_yticks(range(len(costs)))
        ax.set_yticklabels([f"{c:.2f}" for c in costs])

    for index in range(n_panels, n_rows * n_cols):
        axes[index // n_cols][index % n_cols].axis("off")

    if image is not None:
        cbar = fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.9)
        cbar.set_label("delta mean final trait")

    fig.suptitle("Mechanism Advantage Over Network Reciprocity")
    fig.subplots_adjust(left=0.07, right=0.94, top=0.90, bottom=0.08, wspace=0.24, hspace=0.28)
    return fig


def run_plot() -> dict[str, str]:
    in_path = _resolve_input_path()
    rows = _load_rows(in_path)
    mechanisms, benefits, costs = _build_axes(rows)
    matrices = _build_mechanism_matrices(rows, mechanisms, benefits, costs)

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    winner_path = out_dir / f"compare_all_nowak_mechanisms_{stamp}_winner_map.png"
    delta_path = out_dir / f"compare_all_nowak_mechanisms_{stamp}_delta_vs_network.png"

    winner_fig = _plot_winner_map(matrices, mechanisms, benefits, costs)
    winner_fig.savefig(winner_path, dpi=180)
    plt.close(winner_fig)

    delta_fig = _plot_delta_panels(matrices, mechanisms, benefits, costs)
    delta_fig.savefig(delta_path, dpi=180)
    plt.close(delta_fig)

    print(f"[plot_nowak_comparison_summary] input  -> {in_path}")
    print(f"[plot_nowak_comparison_summary] winner -> {winner_path}")
    print(f"[plot_nowak_comparison_summary] delta  -> {delta_path}")
    return {
        "input_csv": str(in_path),
        "winner_plot": str(winner_path),
        "delta_plot": str(delta_path),
    }


if __name__ == "__main__":
    run_plot()
