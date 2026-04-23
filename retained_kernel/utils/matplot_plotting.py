#!/usr/bin/env python3
"""Matplotlib helpers for the retained-kernel module."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt


def plot_run_summary(history: dict[str, list[float]], settings: Any) -> None:
    """Plot the main run diagnostics from a completed kernel simulation."""
    steps = history["step"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Retained Kernel Summary", fontsize=14)

    ax = axes[0, 0]
    ax.plot(steps, history["mean_trait"], color="#8c2d19", linewidth=2.0)
    ax.set_title("Mean Trait Value")
    ax.set_xlabel("Step")
    ax.set_ylabel("Mean trait")
    ax.grid(alpha=0.25)

    ax = axes[0, 1]
    ax.plot(steps, history["local_match_share"], color="#1f5aa6", linewidth=2.0)
    ax.set_title("Local Identity-Match Share")
    ax.set_xlabel("Step")
    ax.set_ylabel("Match share")
    ax.set_ylim(0.0, 1.0)
    ax.grid(alpha=0.25)

    ax = axes[1, 0]
    ax.plot(
        steps,
        history["dominant_identity_share"],
        color="#6b8f23",
        linewidth=2.0,
    )
    ax.set_title("Dominant Identity Share")
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
        "retention="
        f"{settings.retention_fraction:.2f}, "
        "output="
        f"{settings.trait_output_scale:.2f}, "
        "cost="
        f"{settings.trait_cost_scale:.2f}"
    )
    fig.text(0.5, 0.02, footer, ha="center", va="center", fontsize=10)
    fig.tight_layout(rect=(0.0, 0.04, 1.0, 0.96))
    plt.show()
