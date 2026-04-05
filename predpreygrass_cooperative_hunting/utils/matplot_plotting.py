"""
Matplotlib plotting helpers for the cooperative-hunting predator-prey model.
"""

from __future__ import annotations

from typing import Dict, List

import matplotlib.pyplot as plt  # pyright: ignore[reportMissingModuleSource]
import numpy as np


def plot_lv_style(pred_hist: List[int], prey_hist: List[int]) -> None:
    plt.figure()
    plt.plot(prey_hist, label="Prey")
    plt.plot(pred_hist, label="Predators")
    plt.xlabel("Time step")
    plt.ylabel("Count")
    plt.title("Population oscillations (Lotka-Volterra style)")
    plt.legend()
    plt.show()

    plt.figure()
    plt.plot(prey_hist, pred_hist)
    plt.xlabel("Prey count")
    plt.ylabel("Predator count")
    plt.title("Phase plot (Predators vs Prey)")
    plt.show()


def plot_trait_evolution(
    mean_hunt_investment_trait_hist: List[float],
    var_hunt_investment_trait_hist: List[float],
) -> None:
    plt.figure()
    plt.plot(mean_hunt_investment_trait_hist)
    plt.xlabel("Time step")
    plt.ylabel("Mean hunt investment trait")
    plt.title("Trait evolution: mean hunt investment trait over time")
    plt.ylim(0, 1)
    plt.show()

    plt.figure()
    plt.plot(var_hunt_investment_trait_hist)
    plt.xlabel("Time step")
    plt.ylabel("Variance of hunt investment trait")
    plt.title("Trait evolution: variance over time")
    plt.show()


def plot_macro_energy_flows(flow_hist: Dict[str, List[float]]) -> None:
    """Plot macro energy flow channels per tick plus net balance diagnostics."""
    steps = len(flow_hist.get("grass_regen", []))
    if steps == 0:
        print("No energy-flow history available for plotting.")
        return

    t = np.arange(1, steps + 1)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10.0, 9.2), sharex=True)

    ax1.plot(t, flow_hist["grass_regen"], label="photosynthesis -> grass")
    ax1.plot(t, flow_hist["grass_to_prey"], label="grass -> prey")
    ax1.plot(t, flow_hist["prey_to_pred"], label="prey -> predator")
    ax1.plot(t, flow_hist["prey_decay"], label="prey -> decay")
    ax1.plot(t, flow_hist["pred_decay"], label="predator -> decay")
    ax1.set_ylabel("Energy per tick")
    ax1.set_title("Macro Energy Flows Per Tick")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.grid(True, alpha=0.25)

    ax2.plot(t, flow_hist["prey_to_pred"], label="hunt income")
    ax2.plot(t, flow_hist["pred_coop_loss"], label="cooperation cost")
    ax2.plot(
        t,
        flow_hist["coop_net_hunt_return"],
        label="net after coop",
        color="black",
        linewidth=2.0,
    )
    ax2.axhline(0.0, color="gray", linewidth=1.0, alpha=0.7)
    ax2.set_ylabel("Energy per tick")
    ax2.set_title("Cooperation Cost vs Hunt Income")
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, alpha=0.25)

    ax3.plot(t, flow_hist["grass_stock"], label="grass energy stock")
    ax3.plot(t, flow_hist["prey_stock"], label="prey energy stock")
    ax3.plot(t, flow_hist["pred_stock"], label="predator energy stock")
    ax3.plot(
        t,
        flow_hist["total_stock"],
        label="total energy stock (sum)",
        color="black",
        linewidth=2.0,
    )
    ax3.set_xlabel("Time step")
    ax3.set_ylabel("Energy stock")
    ax3.set_title("Net Balance (Cumulative Energy Stocks)")
    ax3.legend(loc="upper right", fontsize=9)
    ax3.grid(True, alpha=0.25)

    fig.tight_layout()
    plt.show()


def plot_trait_selection_diagnostics(
    trait_selection_hist: Dict[str, List[float]],
    final_traits: List[float],
) -> None:
    """Plot distribution-shape and event-conditioned selection diagnostics."""
    steps = len(trait_selection_hist.get("mean_trait", []))
    if steps == 0:
        print("No trait-selection history available for plotting.")
        return

    t = np.arange(1, steps + 1)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10.0, 10.0))

    mean_trait = np.asarray(trait_selection_hist["mean_trait"], dtype=float)
    p10_trait = np.asarray(trait_selection_hist["trait_p10"], dtype=float)
    p50_trait = np.asarray(trait_selection_hist["trait_p50"], dtype=float)
    p90_trait = np.asarray(trait_selection_hist["trait_p90"], dtype=float)

    ax1.fill_between(t, p10_trait, p90_trait, alpha=0.22, color="tab:blue", label="p10-p90")
    ax1.plot(t, mean_trait, color="tab:blue", linewidth=2.0, label="mean")
    ax1.plot(t, p50_trait, color="tab:orange", linewidth=1.5, label="median")
    ax1.set_ylabel("Trait value")
    ax1.set_title("Trait Distribution Envelope Over Time")
    ax1.set_ylim(0.0, 1.0)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, alpha=0.25)

    def plot_optional_series(values: List[float], label: str, color: str) -> None:
        series = np.asarray(values, dtype=float)
        if np.isfinite(series).any():
            ax2.plot(t, series, label=label, color=color, linewidth=1.8)

    plot_optional_series(
        trait_selection_hist["successful_hunter_selection_diff"],
        "successful hunters - population mean",
        "tab:green",
    )
    plot_optional_series(
        trait_selection_hist["reproducing_parent_selection_diff"],
        "reproducing parents - population mean",
        "tab:orange",
    )
    plot_optional_series(
        trait_selection_hist["dead_predator_selection_diff"],
        "dead predators - population mean",
        "tab:red",
    )
    ax2.axhline(0.0, color="gray", linewidth=1.0, alpha=0.7)
    ax2.set_xlabel("Time step")
    ax2.set_ylabel("Trait differential")
    ax2.set_title("Per-Step Selection Differential")
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, alpha=0.25)

    if final_traits:
        final_arr = np.asarray(final_traits, dtype=float)
        bins = min(30, max(8, int(np.sqrt(len(final_arr)))))
        ax3.hist(final_arr, bins=bins, range=(0.0, 1.0), color="tab:purple", alpha=0.8)
        ax3.axvline(final_arr.mean(), color="black", linewidth=1.8, label="final mean")
        ax3.axvline(float(np.median(final_arr)), color="tab:orange", linewidth=1.5, label="final median")
        ax3.legend(loc="upper right", fontsize=9)
    else:
        ax3.text(0.5, 0.5, "No surviving predators in final state", ha="center", va="center")
    ax3.set_xlabel("Hunt investment trait")
    ax3.set_ylabel("Predator count")
    ax3.set_title("Final Predator Trait Distribution")
    ax3.set_xlim(0.0, 1.0)
    ax3.grid(True, alpha=0.25)

    fig.tight_layout()
    plt.show()
