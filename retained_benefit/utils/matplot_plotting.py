#!/usr/bin/env python3
"""Matplotlib helpers for the Retained Benefit model."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt


def plot_run_summary(history: dict[str, list[float]], settings: Any) -> None:
    """Plot the main run diagnostics from a completed simulation."""
    steps = history["step"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Retained Benefit Model Summary", fontsize=14)

    ax = axes[0, 0]
    ax.plot(steps, history["mean_cooperation"], color="#8c2d19", linewidth=2.0)
    ax.set_title("Mean Cooperation Trait")
    ax.set_xlabel("Step")
    ax.set_ylabel("Mean h")
    ax.grid(alpha=0.25)

    ax = axes[0, 1]
    ax.plot(steps, history["local_assortment"], color="#1f5aa6", linewidth=2.0)
    ax.set_title("Local Same-Lineage Share")
    ax.set_xlabel("Step")
    ax.set_ylabel("Assortment")
    ax.set_ylim(0.0, 1.0)
    ax.grid(alpha=0.25)

    ax = axes[1, 0]
    ax.plot(steps, history["dominant_lineage_share"], color="#6b8f23", linewidth=2.0)
    ax.set_title("Dominant Lineage Share")
    ax.set_xlabel("Step")
    ax.set_ylabel("Share")
    ax.set_ylim(0.0, 1.0)
    ax.grid(alpha=0.25)

    ax = axes[1, 1]
    ax.plot(steps, history["mean_fitness"], color="#6a3d9a", linewidth=2.0)
    ax.set_title("Mean Fitness")
    ax.set_xlabel("Step")
    ax.set_ylabel("Fitness")
    ax.grid(alpha=0.25)

    footer = (
        "retained="
        f"{settings.retained_benefit_fraction:.2f}, "
        "benefit="
        f"{settings.cooperation_benefit:.2f}, "
        "cost="
        f"{settings.cooperation_cost:.2f}"
    )
    fig.text(0.5, 0.02, footer, ha="center", va="center", fontsize=10)
    fig.tight_layout(rect=(0.0, 0.04, 1.0, 0.96))
    plt.show()
