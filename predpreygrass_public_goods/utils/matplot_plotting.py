"""
Matplotlib plotting helpers for the public-goods predator-prey model.
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
