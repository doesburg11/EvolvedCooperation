"""Active runtime parameters for the pure direct-reciprocity well-mixed model."""

from __future__ import annotations

from typing import Any


config: dict[str, Any] = {
    # Population size (flat, no spatial structure).
    "n_sites": 200,
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
    # Re-encounter probability: probability that an existing pair stays together
    # next step. 0.0 = full reshuffle (no direct reciprocity). 0.9 = agents stay
    # with the same partner ~10 steps on average, enabling direct reciprocity.
    "partner_persistence_probability": 0.9,
    # Initial strategy mix.
    "initial_strategy_frequencies": {
        "ALLD": 0.55,
        "ALLC": 0.05,
        "TFT": 0.15,
        "GTFT": 0.15,
        "WSLS": 0.10,
    },
    "initial_strategy_layout": "random",
    "rare_invaders_frequency": 0.05,
    "invader_strategy_frequencies": {
        "TFT": 0.34,
        "GTFT": 0.33,
        "WSLS": 0.33,
    },
    "initial_lineage_count": 18,
    # Output and reproducibility.
    "random_seed": 0,
    "summary_interval_steps": 20,
    "write_log": True,
    "log_output_path": (
        "moran_models/nowak_mechanisms/direct_reciprocity/well_mixed/"
        "data/latest_run.json"
    ),
}
