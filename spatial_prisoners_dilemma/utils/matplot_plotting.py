"""Matplotlib plotting helpers for the spatial Prisoner's Dilemma module."""

from __future__ import annotations

from typing import Mapping, Sequence

import matplotlib.pyplot as plt  # pyright: ignore[reportMissingModuleSource]


def plot_population_history(history: Mapping[str, Sequence[float]]) -> None:
    """Plot population, mean energy, and per-step event counts."""
    steps = history.get("step", [])
    if not steps:
        print("No history available for plotting.")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.0, 8.0), sharex=True)

    ax1.plot(steps, history["population"], label="population", color="black", linewidth=2.0)
    ax1.plot(steps, history["mean_energy"], label="mean energy", color="tab:blue")
    ax1.set_ylabel("Count / energy")
    ax1.set_title("Population and Mean Energy")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.25)

    ax2.plot(steps, history["births"], label="births", color="tab:green")
    ax2.plot(steps, history["deaths_total"], label="deaths", color="tab:red")
    ax2.plot(steps, history["interaction_pairs"], label="interaction pairs", color="tab:purple")
    ax2.plot(steps, history["movement_successes"], label="successful moves", color="tab:orange")
    ax2.set_xlabel("Time step")
    ax2.set_ylabel("Count")
    ax2.set_title("Per-Step Events")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.25)

    fig.tight_layout()
    plt.show()


def plot_strategy_family_history(history: Mapping[str, Sequence[float]]) -> None:
    """Plot same-trait and other-trait strategy counts plus pure vs contingent."""
    steps = history.get("step", [])
    if not steps:
        print("No history available for plotting.")
        return

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10.0, 10.0), sharex=True)

    ax1.plot(steps, history["same_trait_cooperate"], label="Co-op")
    ax1.plot(steps, history["same_trait_defect"], label="Defect")
    ax1.plot(steps, history["same_trait_tit_for_tat"], label="Tit-for-tat")
    ax1.plot(steps, history["same_trait_random"], label="Random")
    ax1.set_ylabel("Agents")
    ax1.set_title("Same-Trait Strategy Family")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.25)

    ax2.plot(steps, history["other_trait_cooperate"], label="Co-op")
    ax2.plot(steps, history["other_trait_defect"], label="Defect")
    ax2.plot(steps, history["other_trait_tit_for_tat"], label="Tit-for-tat")
    ax2.plot(steps, history["other_trait_random"], label="Random")
    ax2.set_ylabel("Agents")
    ax2.set_title("Other-Trait Strategy Family")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.25)

    ax3.plot(steps, history["pure_count"], label="Pure")
    ax3.plot(steps, history["contingent_count"], label="Contingent")
    ax3.set_xlabel("Time step")
    ax3.set_ylabel("Agents")
    ax3.set_title("Pure vs Contingent Strategy Encoding")
    ax3.legend(loc="upper right")
    ax3.grid(True, alpha=0.25)

    fig.tight_layout()
    plt.show()
