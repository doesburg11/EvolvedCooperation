"""Heatmaps of the sweep (stag_hunt_sharing.py): the final share of stag
hunters, averaged over seeds, by share fraction (x) and stag-to-hare ratio
(y); one panel per sharing radius (columns) and fitness shape x dispersal
(rows); one figure per initial stag fraction (suffix _start<fraction>)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ..config.stag_hunt_sharing_config import SWEEP, SWEEP_TARGETED


def table(rows: list[dict[str, Any]]) -> dict[tuple, float]:
    """Mean stag fraction per condition, over seeds. Rows with share
    fraction 0 stand for every radius (the radius plays no part)."""
    cells = defaultdict(list)
    zero_radii = {str(row["sharing_radius"]) for row in rows if float(row["share_fraction"]) == 0}
    if len(zero_radii) > 1:
        raise ValueError(f"share-0 rows must come from one radius (conditions()), not {sorted(zero_radii)}")
    for row in rows:
        radii = SWEEP["sharing_radius"] if float(row["share_fraction"]) == 0 else [row["sharing_radius"]]
        for radius in radii:
            key = (float(row["initial_stag_fraction"]), row["fitness_shape"], row["dispersal"], str(radius), float(row["share_fraction"]), float(row["stag_to_hare_ratio"]))
            cells[key].append(float(row["stag_fraction"]))
    return {key: float(np.mean(values)) for key, values in cells.items()}


def plot(rows: list[dict[str, Any]], figure: str) -> list[Path]:
    means = table(rows)
    shares, ratios = SWEEP["share_fraction"], SWEEP["stag_to_hare_ratio"]
    radii = [str(r) for r in SWEEP["sharing_radius"]]
    panels = [(f, d) for f in SWEEP["fitness_shape"] for d in SWEEP["dispersal"]]
    written = []
    for start in SWEEP["initial_stag_fraction"]:
        fig, axes = plt.subplots(len(panels), len(radii), figsize=(3.1 * len(radii), 2.7 * len(panels)), sharex=True, sharey=True, constrained_layout=True)
        image = None
        for i, (shape, dispersal) in enumerate(panels):
            for j, radius in enumerate(radii):
                ax = axes[i, j]
                grid = np.array([[means.get((start, shape, dispersal, radius, s, r), np.nan) for s in shares] for r in ratios])
                image = ax.imshow(grid, origin="lower", cmap="Blues", vmin=0, vmax=1, aspect="auto")
                for (y, x), value in np.ndenumerate(grid):
                    if not np.isnan(value):
                        ax.text(x, y, f"{value:.2f}", ha="center", va="center", fontsize=7, color="white" if value > 0.6 else "#222222")
                ax.set_xticks(range(len(shares)), [f"{s:g}" for s in shares])
                ax.set_yticks(range(len(ratios)), [f"{r:g}" for r in ratios])
                if i == 0:
                    ax.set_title(f"sharing radius {radius}", fontsize=9)
                if j == 0:
                    ax.set_ylabel(f"{shape}, {dispersal}\nstag / hare payoff", fontsize=8)
                if i == len(panels) - 1:
                    ax.set_xlabel("share fraction s", fontsize=8)
        fig.colorbar(image, ax=axes, shrink=0.6, label="final share of stag hunters")
        fig.suptitle(f"Stag hunt with sharing: final share of stag hunters (start {start:g})", fontsize=11)
        path = Path(figure).with_name(f"{Path(figure).stem}_start{start:g}{Path(figure).suffix}")
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=130)
        plt.close(fig)
        written.append(path)
    return written


def table_targeted(rows: list[dict[str, Any]]) -> dict[tuple, float]:
    """Mean stag fraction per condition of SWEEP_TARGETED, over seeds. Rows
    with share fraction 0 stand for every target and radius."""
    cells = defaultdict(list)
    zero = {(row["share_target"], str(row["sharing_radius"])) for row in rows if float(row["share_fraction"]) == 0}
    if len(zero) > 1:
        raise ValueError(f"share-0 rows must come from one target and radius (conditions()), not {sorted(zero)}")
    for row in rows:
        zero_row = float(row["share_fraction"]) == 0
        targets = SWEEP_TARGETED["share_target"] if zero_row else [row["share_target"]]
        radii = SWEEP_TARGETED["sharing_radius"] if zero_row else [row["sharing_radius"]]
        for target in targets:
            for radius in radii:
                key = (row["fitness_shape"], str(row["dispersal"]), target, str(radius), float(row["share_fraction"]), float(row["stag_to_hare_ratio"]))
                cells[key].append(float(row["stag_fraction"]))
    return {key: float(np.mean(values)) for key, values in cells.items()}


def plot_targeted(rows: list[dict[str, Any]], figure: str) -> list[Path]:
    """One figure per sharing radius: rows fitness shape x share target,
    columns dispersal; each panel share fraction (x) by ratio (y)."""
    means = table_targeted(rows)
    shares, ratios = SWEEP_TARGETED["share_fraction"], SWEEP_TARGETED["stag_to_hare_ratio"]
    dispersals = [str(d) for d in SWEEP_TARGETED["dispersal"]]
    panels = [(f, t) for f in SWEEP_TARGETED["fitness_shape"] for t in SWEEP_TARGETED["share_target"]]
    written = []
    for radius in [str(r) for r in SWEEP_TARGETED["sharing_radius"]]:
        fig, axes = plt.subplots(len(panels), len(dispersals), figsize=(3.1 * len(dispersals), 2.7 * len(panels)), sharex=True, sharey=True, constrained_layout=True)
        image = None
        for i, (shape, target) in enumerate(panels):
            for j, dispersal in enumerate(dispersals):
                ax = axes[i, j]
                grid = np.array([[means.get((shape, dispersal, target, radius, s, r), np.nan) for s in shares] for r in ratios])
                image = ax.imshow(grid, origin="lower", cmap="Blues", vmin=0, vmax=1, aspect="auto")
                for (y, x), value in np.ndenumerate(grid):
                    if not np.isnan(value):
                        ax.text(x, y, f"{value:.2f}", ha="center", va="center", fontsize=7, color="white" if value > 0.6 else "#222222")
                ax.set_xticks(range(len(shares)), [f"{s:g}" for s in shares])
                ax.set_yticks(range(len(ratios)), [f"{r:g}" for r in ratios])
                if i == 0:
                    ax.set_title(f"dispersal {dispersal}", fontsize=9)
                if j == 0:
                    ax.set_ylabel(f"{shape}, shared with {target}\nstag / hare payoff", fontsize=8)
                if i == len(panels) - 1:
                    ax.set_xlabel("share fraction s", fontsize=8)
        fig.colorbar(image, ax=axes, shrink=0.6, label="final share of stag hunters")
        fig.suptitle(f"Targeted sharing: final share of stag hunters (sharing radius {radius}, start 0.5)", fontsize=11)
        path = Path(figure).with_name(f"{Path(figure).stem}_radius{radius}{Path(figure).suffix}")
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=130)
        plt.close(fig)
        written.append(path)
    return written
