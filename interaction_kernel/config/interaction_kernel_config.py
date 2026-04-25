#!/usr/bin/env python3
"""Active runtime parameters for `interaction_kernel_model.py`.

Edit the `config` dict directly. This module follows the repo convention that
the config file is the primary source of truth for runs.
"""

from __future__ import annotations

from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    # World geometry.
    "grid_width": 24,
    "grid_height": 24,
    "toroidal_world": True,
    "neighborhood_mode": "von_neumann",  # "von_neumann" or "moore"
    "include_self_in_neighborhood": True,
    # Simulation horizon.
    "simulation_steps": 80,
    # Produced effects and private cost.
    # Theory mapping:
    # B_plus = B_plus_scale * h
    # B_minus = B_minus_scale * h
    # C = C_scale * h
    "base_fitness": 1.0,
    "B_plus_scale": 0.30,
    "B_minus_scale": 0.00,
    "C_scale": 0.10,
    # Kernel modes.
    # K_plus routes B_plus, K_minus routes B_minus.
    "positive_kernel_mode": "kin_weighted",  # "uniform" or "kin_weighted"
    "negative_kernel_mode": "uniform",  # "none" or "uniform"
    # Kin weighting for the positive kernel.
    "kin_weight_same_lineage": 1.0,
    "kin_weight_other_lineage": 0.25,
    # Selection and inheritance.
    "selection_temperature": 0.12,
    "mutation_rate": 0.02,
    "mutation_stddev": 0.04,
    # Initial state.
    "initial_trait_mean": 0.12,
    "initial_trait_stddev": 0.04,
    "initial_identity_count": 18,
    # Output and reproducibility.
    "random_seed": 0,
    "summary_interval_steps": 20,
    "write_log": True,
    "log_output_path": "interaction_kernel/data/latest_run.json",
}


config = dict(DEFAULT_CONFIG)
