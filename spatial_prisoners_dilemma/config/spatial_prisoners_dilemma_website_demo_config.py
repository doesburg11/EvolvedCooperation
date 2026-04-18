#!/usr/bin/env python3
"""
Frozen configuration for the GitHub Pages spatial Prisoner's Dilemma demo.

This module preserves the parameter set used by the website replay as of
2026-04-18. Continue tuning the live model in
`spatial_prisoners_dilemma_config.py`; update this file only when you
intentionally want the website experiment to change.
"""

from __future__ import annotations

from typing import Any


config: dict[str, Any] = {
    # World geometry and population scale.
    "grid_width": 60,
    "grid_height": 60,
    "initial_agent_fraction": 0.16,
    "carrying_capacity_fraction": 0.50,
    "simulation_steps": 200,
    # Per-step ecology.
    "cost_of_living": 1.0,
    "travel_cost": 0.5,
    "reproduce_min_energy": 100.0,
    "reproduce_cost": 50.0,
    "reproduction_inheritance": 0.0,
    "max_children_per_step": 1,
    # Prisoner's Dilemma payoffs.
    "payoff_cc": 3.0,
    "payoff_cd": -1.0,
    "payoff_dc": 5.0,
    "payoff_dd": 0.0,
    # Energy and noise.
    "max_energy": 150.0,
    "initial_energy_mean": 50.0,
    "initial_energy_stddev": 10.0,
    "initial_energy_min": 5.0,
    "env_noise": 0.0,
    # Trait and strategy structure.
    "trait_count": 4,
    "pure_strategy": False,
    "strategy_per_trait": False,
    "mutation_rate": 0.0,
    "strategy_weights": {
        "always_cooperate": 0.25,
        "always_defect": 0.25,
        "tit_for_tat": 0.25,
        "random": 0.25,
    },
    # Output and reproducibility.
    "random_seed": 0,
    "summary_interval_steps": 0,
    "write_log": False,
    "show_matplotlib_plots": False,
}
