#!/usr/bin/env python3
"""
Active runtime parameters for the equal-split `cooperative_hunting.py` counterfactual.

Edit the `config` dict directly. Use `random_seed=None` to disable the fixed
seed.

Canonical parameter names are descriptive and are the only accepted parameter
names for runtime overrides.
"""

from __future__ import annotations

from typing import Any, Mapping

DEFAULT_CONFIG: dict[str, Any] = {
    # World geometry and initial populations.
    "grid_width": 60,
    "grid_height": 60,
    "initial_predator_count": 65,
    "initial_prey_count": 575,
    "initial_predator_energy": 3.0,
    "initial_predator_hunt_investment_trait_min": 0.0,
    "initial_predator_hunt_investment_trait_max": 0.15,
    "simulation_steps": 10000,
    # Predator energetics and reproduction.
    "predator_metabolic_cost": 0.053,
    "predator_move_cost_per_unit": 0.008,
    "predator_cooperation_cost_per_unit": 0.02,
    "predator_reproduction_energy_threshold": 4.8,
    "predator_reproduction_probability": 0.02,
    "predator_crowding_soft_cap": 800,
    # Trait inheritance and local birth.
    "cooperation_mutation_probability": 0.12,
    "cooperation_mutation_stddev": 0.16,
    "offspring_birth_radius": 1,
    # Hunt structure.
    "prey_detection_radius": 1,
    "hunt_success_rule": "threshold_synergy",
    "base_hunt_success_probability": 0.60,
    "hunter_pool_radius": 2,
    "threshold_synergy_min_hunters": 2,
    "threshold_synergy_formation_energy_factor": 0.55,
    "threshold_synergy_execution_energy_factor": 0.85,
    "threshold_synergy_success_steepness": 1.0,
    "threshold_synergy_max_success_probability": 0.80,
    "share_prey_equally": True,
    # Logging and diagnostics.
    "log_reward_sharing": False,
    "log_energy_accounting": False,
    "energy_log_interval_steps": 1,
    "energy_invariant_tolerance": 1e-6,
    # Prey energetics and reproduction.
    "prey_move_probability": 0.30,
    "prey_reproduction_probability": 0.082,
    "initial_prey_energy_mean": 1.1,
    "initial_prey_energy_stddev": 0.25,
    "initial_prey_energy_min": 0.10,
    "prey_metabolic_cost": 0.05,
    "prey_move_cost_per_unit": 0.01,
    "prey_reproduction_energy_threshold": 2.0,
    "prey_offspring_energy_fraction": 0.42,
    "prey_grass_intake_per_step": 0.24,
    # Grass resource field.
    "initial_grass_energy": 0.8,
    "max_grass_energy_per_cell": 3.0,
    "grass_regrowth_per_step": 0.055,
    # Visualization and analysis.
    "plot_macro_energy_flows": True,
    "plot_trait_selection_diagnostics": True,
    "enable_live_pygame_renderer": True,
    "live_render_frames_per_second": 30,
    "live_render_cell_size": 14,
    # Reproducibility and restart behavior.
    "random_seed": 0,
    "restart_after_extinction": False,
    "max_restart_attempts": 60,
}


def resolve_config(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """
    Merge overrides onto the canonical default config.

    Only canonical keys are accepted. Unknown keys raise KeyError.
    """

    resolved = dict(DEFAULT_CONFIG)
    if overrides is None:
        return resolved

    for raw_key, value in overrides.items():
        if raw_key not in DEFAULT_CONFIG:
            raise KeyError(f"Unknown config key '{raw_key}'")
        resolved[raw_key] = value
    return resolved


config = dict(DEFAULT_CONFIG)
