"""Active runtime parameters for the binary indirect reciprocity well-mixed model.

Nowak's key condition: cooperation spreads when q > c/b.
With these defaults: c/b = 0.2 / 1.0 = 0.2,  so q_threshold = 0.2.
"""

from __future__ import annotations

from typing import Any

config: dict[str, Any] = {
    # Population size — flat, no spatial structure.
    "n_agents": 400,
    # Simulation horizon.
    "simulation_steps": 2000,
    "summary_interval_steps": 2000,
    # Nowak's binary payoff parameters.  c/b = 0.2 → Nowak's condition: q > 0.2.
    "base_fitness": 1.0,
    "b_benefit": 1.0,
    "c_cost": 0.2,
    # Reputation observation probability q.  Varied per scenario to test Nowak's condition.
    "reputation_observation_prob": 0.8,
    # Reputation threshold: donor helps recipient only if rep_j >= this value.
    "reputation_threshold": 0.5,
    # How quickly reputation tracks observed helping behaviour.
    "reputation_default": 0.5,
    "reputation_observation_weight": 0.30,
    # Moran selection and inheritance.
    "selection_temperature": 0.12,
    "mutation_rate": 0.02,
    "mutation_stddev": 0.04,
    # Initial trait distribution.
    "initial_trait_mean": 0.9,
    "initial_trait_stddev": 0.05,
    # Output and reproducibility.
    "random_seed": 0,
    "write_log": True,
    "log_output_path": (
        "moran_models/nowak_mechanisms/indirect_reciprocity/well_mixed_binary/"
        "data/latest_run.json"
    ),
}
