"""Active runtime parameters for the kin-clustering scaffold."""

from __future__ import annotations

from typing import Any


config: dict[str, Any] = {
    # Population size and kin structure.
    "n_agents": 576,
    "n_lineages": 24,
    "include_self_in_replacement_neighborhood": True,
    # Kin-interaction graph.
    # Each agent has n_partners_per_agent fixed interaction partners.
    # kin_interaction_fraction of those are drawn from the same lineage at init.
    "n_partners_per_agent": 4,
    "kin_interaction_fraction": 0.8,
    # Simulation horizon.
    "simulation_steps": 1000,
    "rounds_per_pair_per_step": 3,
    # Prisoner's Dilemma payoffs.
    # Standard order: T > R > P > S.
    "temptation_payoff": 1.7,
    "reward_payoff": 1.0,
    "punishment_payoff": 0.0,
    "sucker_payoff": -0.5,
    "base_fitness": 1.0,
    "normalize_payoff_by_interactions": False,
    # Moran selection and strategy mutation.
    "selection_temperature": 0.18,
    "mutation_rate": 0.01,
    # Strategy-rule parameters.
    "gtft_forgiveness_probability": 0.25,
    "wsls_aspiration_payoff": 1.0,
    "action_error_probability": 0.0,
    "memory_enabled": True,
    "reset_memory_on_replacement": True,
    # Initial strategy mix.
    # Keys must match strategy names in kin_clustering_model.py.
    "initial_strategy_frequencies": {
        "ALLD": 0.55,
        "ALLC": 0.05,
        "TFT": 0.15,
        "GTFT": 0.15,
        "WSLS": 0.10,
    },
    "initial_strategy_layout": "random",
    # Used when initial_strategy_layout == "reciprocal_lineage".
    # Selects the lineage whose size is closest to cluster_reciprocal_frequency * n_agents.
    "cluster_reciprocal_frequency": 0.05,
    "cluster_strategy_frequencies": {
        "TFT": 0.34,
        "GTFT": 0.33,
        "WSLS": 0.33,
    },
    # Output and reproducibility.
    "random_seed": 0,
    "summary_interval_steps": 20,
    "write_log": True,
    "log_output_path": (
        "moran_models/nowak_mechanisms/direct_reciprocity/scaffolds/kin_clustering/"
        "data/latest_run.json"
    ),
}
