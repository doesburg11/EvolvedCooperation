#!/usr/bin/env python3
"""
Active runtime parameters for `retained_benefit_model.py`.

Edit the `config` dict directly. This module follows the repo convention that
the config file is the normal source of truth for the main run.
"""

from __future__ import annotations

from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
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
    "summary_interval_steps": 25,
    "write_log": True,
    "log_output_path": "ecological_models/retained_benefit/data/latest_run.json",
    "show_matplotlib_plots": False,
}


config = dict(DEFAULT_CONFIG)
