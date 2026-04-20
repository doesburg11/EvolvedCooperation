#!/usr/bin/env python3
"""
Frozen configuration for the GitHub Pages Retained Benefit demo.

This module preserves the parameter set used by the website replay as of
2026-04-20. Continue tuning the live model in
`retained_benefit_config.py`; update this file only when you intentionally
want the website experiment to change.
"""

from __future__ import annotations

from typing import Any


config: dict[str, Any] = {
    # World geometry.
    "grid_width": 72,
    "grid_height": 72,
    "toroidal_world": True,
    "neighborhood_mode": "von_neumann",
    # Simulation horizon.
    "simulation_steps": 250,
    # Cooperation rule.
    "base_fitness": 1.0,
    "cooperation_cost": 0.10,
    "cooperation_benefit": 0.30,
    "retained_benefit_fraction": 0.35,
    # Trait inheritance.
    "mutation_rate": 0.02,
    "mutation_stddev": 0.05,
    # Initial state.
    "initial_cooperation_mean": 0.12,
    "initial_cooperation_stddev": 0.04,
    "initial_lineage_count": 24,
    "initial_lineage_block_size": 6,
    # Output and reproducibility.
    "random_seed": 0,
    "summary_interval_steps": 0,
    "write_log": False,
    "show_matplotlib_plots": False,
}
