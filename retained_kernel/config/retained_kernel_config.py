#!/usr/bin/env python3
"""
Active runtime parameters for `retained_kernel_model.py`.

Edit the `config` dict directly. This package follows the repo convention that
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
    # Kernel rule.
    "base_fitness": 1.0,
    "trait_cost_scale": 0.10,
    "trait_output_scale": 0.30,
    "retention_fraction": 0.35,
    # Trait inheritance.
    "mutation_rate": 0.02,
    "mutation_stddev": 0.05,
    # Initial state.
    "initial_trait_mean": 0.12,
    "initial_trait_stddev": 0.04,
    "initial_identity_count": 24,
    "initial_identity_block_size": 6,
    # Output and reproducibility.
    "random_seed": 0,
    "summary_interval_steps": 25,
    "write_log": True,
    "log_output_path": "retained_kernel/data/latest_run.json",
    "show_matplotlib_plots": False,
}


config = dict(DEFAULT_CONFIG)
