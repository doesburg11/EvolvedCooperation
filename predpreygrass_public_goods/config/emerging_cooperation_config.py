#!/usr/bin/env python3
"""
Active runtime parameters for `emerging_cooperation.py`.

Edit the `config` dict directly. Use `random_seed=None` to disable the fixed
seed.

Canonical parameter names are descriptive. Older short names are still accepted
through `LEGACY_CONFIG_ALIASES` so older helper scripts or saved presets do not
break immediately.
"""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    # World geometry and initial populations.
    "grid_width": 60,
    "grid_height": 60,
    "initial_predator_count": 65,
    "initial_prey_count": 575,
    "initial_predator_energy": 1.4,
    "simulation_steps": 1000,
    # Predator energetics and reproduction.
    "predator_metabolic_cost": 0.053,
    "predator_move_cost_per_unit": 0.008,
    "predator_cooperation_cost_per_unit": 0.15,
    "predator_reproduction_energy_threshold": 4.8,
    "predator_reproduction_probability": 0.045,
    "predator_crowding_soft_cap": 800,
    # Trait inheritance and local birth.
    "cooperation_mutation_probability": 0.03,
    "cooperation_mutation_stddev": 0.08,
    "offspring_birth_radius": 1,
    # Hunt structure.
    "prey_detection_radius": 1,
    "hunt_success_rule": "energy_threshold_gate",
    "base_hunt_success_probability": 0.60,
    "hunter_pool_radius": 1,
    "share_prey_equally": True,
    # Logging and diagnostics.
    "log_reward_sharing": False,
    "log_energy_accounting": False,
    "energy_log_interval_steps": 1,
    "energy_invariant_tolerance": 1e-6,
    # Prey energetics and reproduction.
    "prey_move_probability": 0.30,
    "prey_reproduction_probability": 0.086,
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
    "animate": False,
    "animate_simple_grid": False,
    "animation_steps": 500,
    "animation_interval_ms": 40,
    "plot_macro_energy_flows": True,
    "enable_live_pygame_renderer": True,
    "live_render_frames_per_second": 30,
    "live_render_cell_size": 14,
    "clustering_radius": 2,
    "predator_marker_size": 70,
    "predator_marker_edge_width": 1.2,
    "prey_density_overlay_alpha": 0.35,
    "clustering_overlay_alpha": 1.0,
    # Reproducibility and restart behavior.
    "random_seed": 0,
    "restart_after_extinction": False,
    "max_restart_attempts": 60,
}


LEGACY_CONFIG_ALIASES: dict[str, str] = {
    "w": "grid_width",
    "h": "grid_height",
    "pred_init": "initial_predator_count",
    "prey_init": "initial_prey_count",
    "pred_energy_init": "initial_predator_energy",
    "steps": "simulation_steps",
    "metab_pred": "predator_metabolic_cost",
    "move_cost": "predator_move_cost_per_unit",
    "coop_cost": "predator_cooperation_cost_per_unit",
    "birth_thresh_pred": "predator_reproduction_energy_threshold",
    "pred_repro_prob": "predator_reproduction_probability",
    "pred_max": "predator_crowding_soft_cap",
    "mut_rate": "cooperation_mutation_probability",
    "mut_sigma": "cooperation_mutation_stddev",
    "local_birth_r": "offspring_birth_radius",
    "hunt_r": "prey_detection_radius",
    "hunt_rule": "hunt_success_rule",
    "p0": "base_hunt_success_probability",
    "hunter_pool_r": "hunter_pool_radius",
    "equal_split_rewards": "share_prey_equally",
    "log_reward_split": "log_reward_sharing",
    "log_energy_budget": "log_energy_accounting",
    "energy_log_every": "energy_log_interval_steps",
    "energy_invariant_tol": "energy_invariant_tolerance",
    "prey_move_prob": "prey_move_probability",
    "prey_repro_prob": "prey_reproduction_probability",
    "prey_energy_mean": "initial_prey_energy_mean",
    "prey_energy_sigma": "initial_prey_energy_stddev",
    "prey_energy_min": "initial_prey_energy_min",
    "prey_metab": "prey_metabolic_cost",
    "prey_move_cost": "prey_move_cost_per_unit",
    "prey_birth_thresh": "prey_reproduction_energy_threshold",
    "prey_birth_split": "prey_offspring_energy_fraction",
    "prey_bite_size": "prey_grass_intake_per_step",
    "grass_init": "initial_grass_energy",
    "grass_max": "max_grass_energy_per_cell",
    "grass_regrowth": "grass_regrowth_per_step",
    "anim_steps": "animation_steps",
    "anim_interval_ms": "animation_interval_ms",
    "live_render_pygame": "enable_live_pygame_renderer",
    "live_render_fps": "live_render_frames_per_second",
    "clust_r": "clustering_radius",
    "pred_size": "predator_marker_size",
    "pred_edge_linewidth": "predator_marker_edge_width",
    "prey_density_alpha": "prey_density_overlay_alpha",
    "cluster_alpha": "clustering_overlay_alpha",
    "seed": "random_seed",
    "restart_on_extinction": "restart_after_extinction",
    "max_restarts": "max_restart_attempts",
}


def canonicalize_config_key(key: str) -> str:
    """Return the canonical config key for a possibly legacy name."""
    return LEGACY_CONFIG_ALIASES.get(key, key)


def resolve_config(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """
    Merge overrides onto the canonical default config.

    Both canonical and legacy keys are accepted. Supplying both forms of the
    same key in one overrides mapping raises a ValueError to avoid silent
    precedence bugs.
    """

    resolved = dict(DEFAULT_CONFIG)
    if overrides is None:
        return resolved

    seen_raw_keys: dict[str, str] = {}
    for raw_key, value in overrides.items():
        canonical_key = canonicalize_config_key(raw_key)
        if canonical_key not in DEFAULT_CONFIG:
            raise KeyError(f"Unknown config key '{raw_key}'")
        previous_raw_key = seen_raw_keys.get(canonical_key)
        if previous_raw_key is not None and previous_raw_key != raw_key:
            raise ValueError(
                f"Config specifies both '{previous_raw_key}' and '{raw_key}', "
                f"which both map to '{canonical_key}'."
            )
        resolved[canonical_key] = value
        seen_raw_keys[canonical_key] = raw_key
    return resolved


config = dict(DEFAULT_CONFIG)
