#!/usr/bin/env python3
"""Invasion trajectory plot for kin selection.

Runs rare-cooperator simulations under two conditions:
  - With kin bias (kin_weight_same_lineage=0.8, kin_weight_other_lineage=0.2)
  - No kin bias ablation (equal weights, well-mixed routing)

Plots per-step mean cooperation for each seed as thin lines, with a bold
ensemble mean and ±1 std shaded band. Shows how cooperation invades a
defector-dominated population over 1000 steps.

Run from repo root:
    ./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.utils.plot_invasion_trajectories
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from moran_models.nowak_mechanisms.kin_selection.config.kin_selection_config import config as base_config
from moran_models.nowak_mechanisms.kin_selection.kin_selection_model import run_simulation


SEEDS = [0, 1, 2, 3, 4]
SIM_STEPS = 1000
OUT_DIR = Path("moran_models/nowak_mechanisms/kin_selection/data")
STATIC_PATH = Path(
    "moran_models/nowak_mechanisms/kin_selection/data"
)
WEBSITE_STATIC = Path(
    "/home/doesburg/Projects/human-cooperation-site/static/img/evolved-cooperation/kin-selection"
)

CONDITIONS = [
    (
        "With kin bias",
        {
            "kin_weight_same_lineage": 0.8,
            "kin_weight_other_lineage": 0.2,
        },
        "#2166ac",   # blue
    ),
    (
        "No kin bias (ablation)",
        {
            "kin_weight_same_lineage": 0.2,
            "kin_weight_other_lineage": 0.2,
        },
        "#d6604d",   # red-orange
    ),
]

RARE_START = {
    "initial_trait_mean": 0.05,
    "initial_trait_stddev": 0.02,
    "simulation_steps": SIM_STEPS,
    "summary_interval_steps": 1,
    "write_log": False,
}


def _run_condition(overrides: dict) -> list[list[float]]:
    trajectories = []
    for seed in SEEDS:
        cfg = dict(base_config)
        cfg.update(RARE_START)
        cfg.update(overrides)
        cfg["random_seed"] = seed
        result = run_simulation(cfg)
        traj = [float(h["mean_trait"]) for h in result["history"] if "mean_trait" in h]
        trajectories.append(traj)
        print(f"  seed={seed}  final={traj[-1]:.3f}")
    return trajectories


def _plot(all_trajectories: list[tuple[str, list[list[float]], str]], png_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))

    steps = list(range(SIM_STEPS + 1))

    for label, trajectories, colour in all_trajectories:
        arr = np.array(trajectories)
        mean = arr.mean(axis=0)
        std = arr.std(axis=0)

        for traj in trajectories:
            ax.plot(steps[:len(traj)], traj, color=colour, alpha=0.25, linewidth=0.8)

        ax.plot(steps[:len(mean)], mean, color=colour, linewidth=2.2, label=label)
        ax.fill_between(
            steps[:len(mean)],
            np.clip(mean - std, 0, 1),
            np.clip(mean + std, 0, 1),
            color=colour,
            alpha=0.15,
        )

    ax.axhline(0.05, color="black", linewidth=0.9, linestyle="--", label="Starting frequency (5%)")
    ax.set_xlim(0, SIM_STEPS)
    ax.set_ylim(-0.02, 1.05)
    ax.set_xlabel("Simulation step")
    ax.set_ylabel("Mean cooperation frequency")
    ax.set_title("Kin selection: invasion from rare (5 seeds per condition)")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(png_path, dpi=180)
    plt.close(fig)
    print(f"[plot_invasion_trajectories] PNG -> {png_path}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    png_path = OUT_DIR / f"kin_selection_invasion_trajectories_{stamp}.png"

    all_trajectories = []
    for label, overrides, colour in CONDITIONS:
        print(f"\n[plot_invasion_trajectories] condition: {label}")
        trajectories = _run_condition(overrides)
        all_trajectories.append((label, trajectories, colour))

    _plot(all_trajectories, png_path)

    website_png = WEBSITE_STATIC / "kin_selection_invasion_trajectories.png"
    shutil.copy(png_path, website_png)
    print(f"[plot_invasion_trajectories] copied -> {website_png}")


if __name__ == "__main__":
    main()
