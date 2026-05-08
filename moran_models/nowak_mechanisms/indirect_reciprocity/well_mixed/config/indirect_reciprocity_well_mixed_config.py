"""Active runtime parameters for the indirect-reciprocity well-mixed model."""

from __future__ import annotations

from typing import Any

config: dict[str, Any] = {
    # Population size — flat, no spatial structure.
    "n_agents": 400,
    # Simulation horizon.
    "simulation_steps": 2000,
    "summary_interval_steps": 2000,
    # Payoff scaling.  B/C = 5 by default (rb > c trivially met when r → 1).
    "base_fitness": 1.0,
    "B_plus_scale": 1.0,
    "C_scale": 0.2,
    # Reputation channel parameters (same semantics as the spatial model).
    "reputation_default": 0.5,
    "reputation_observation_weight": 0.35,
    "reputation_kernel_bias": 0.10,
    "reputation_kernel_exponent": 1.0,
    # Moran selection and inheritance.
    "selection_temperature": 0.12,
    "mutation_rate": 0.02,
    "mutation_stddev": 0.04,
    # Initial trait distribution.
    "initial_trait_mean": 0.12,
    "initial_trait_stddev": 0.04,
    # Output and reproducibility.
    "random_seed": 0,
    "write_log": True,
    "log_output_path": (
        "moran_models/nowak_mechanisms/indirect_reciprocity/well_mixed/"
        "data/latest_run.json"
    ),
}
