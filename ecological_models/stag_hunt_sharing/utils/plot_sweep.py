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

from ..config.stag_hunt_sharing_config import SWEEP


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
