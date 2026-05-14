#!/usr/bin/env python3
"""
Active parameters for the ecological kin-selection model.

Edit `config` and the proof scenario definitions directly. Runtime modules do
not accept command-line parameters.
"""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    # Runtime and output.
    "random_seed": 0,
    "simulation_steps": 220,
    "summary_interval_steps": 20,
    "write_latest_run": True,
    "data_dir": "ecological_models/nowak_mechanisms/kin_selection/data",
    # Initial family-structured population.
    "initial_group_count": 16,
    "founder_pairs_per_group": 2,
    "initial_children_per_pair": 2,
    "genome_loci": 64,
    "initial_adult_age_min": 8,
    "initial_adult_age_max": 18,
    "initial_child_age_min": 0,
    "initial_child_age_max": 3,
    "initial_adult_energy": 12.0,
    "initial_juvenile_energy": 4.0,
    "initial_helping_trait_min": 0.0,
    "initial_helping_trait_max": 0.04,
    "rare_helper_founder_probability": 0.03,
    "rare_helper_trait_value": 0.65,
    "helping_trait_invasion_threshold": 0.10,
    # Trait inheritance.
    "helping_mutation_probability": 0.20,
    "helping_mutation_stddev": 0.04,
    # Life history.
    "juvenile_maturity_age": 5,
    "elder_age": 38,
    "max_age": 75,
    "juvenile_metabolic_cost": 0.08,
    "adult_metabolic_cost": 0.12,
    "elder_metabolic_cost": 0.15,
    "juvenile_foraging_energy_gain": 0.03,
    "adult_foraging_energy_gain": 0.32,
    "elder_foraging_energy_gain": 0.20,
    "max_energy": 18.0,
    "adult_survival_probability": 0.999,
    "elder_survival_probability": 0.995,
    # Sexual reproduction.
    "female_reproduction_probability": 0.35,
    "female_min_reproduction_age": 6,
    "female_max_reproduction_age": 45,
    "male_min_reproduction_age": 6,
    "male_max_reproduction_age": 55,
    "reproduction_energy_threshold": 7.0,
    "reproduction_energy_cost": 1.0,
    "child_energy": 3.5,
    "max_mate_relatedness": 0.10,
    "same_group_mate_preference_probability": 0.65,
    "offspring_dispersal_probability": 0.0,
    "foster_to_nonparent_group_probability": 0.0,
    "matured_dispersal_probability": 0.0,
    # Carrying capacity. This is density mortality, not Moran replacement.
    "max_population": 320,
    # Juvenile rearing and kin-biased care.
    "enable_rearing_dependency": True,
    "enable_care_benefit": True,
    "enable_relatedness_bias": True,
    "shuffle_relatedness_for_care": False,
    "base_juvenile_survival_probability": 0.35,
    "rearing_independent_juvenile_survival_probability": 0.98,
    "care_benefit_to_survival": 0.75,
    "care_saturation": 0.9,
    "care_capacity_per_helper": 2.5,
    "care_cost_per_unit": 0.03,
    "helper_energy_reserve": 3.0,
    "care_baseline_weight": 0.02,
    "kin_bias_strength": 7.0,
    "kin_relatedness_threshold": 0.125,
    "enable_grandmother_effects": True,
    "grandmother_care_capacity_multiplier": 1.45,
    "grandmother_household_weight_bonus": 0.40,
    # Proof-of-mechanism thresholds.
    "proof_success_min_trait_increase": 0.015,
    "proof_success_min_invasion_frequency_increase": 0.02,
    "proof_success_min_hamilton_margin_proxy": 0.0,
    "proof_success_min_final_population": 100,
    # Live grid viewer.
    "live_viewer_frames_per_second": 10,
    "live_viewer_cell_size": 12,
    "live_viewer_group_columns": 4,
    "live_viewer_group_cell_columns": 8,
    "live_viewer_group_cell_rows": 8,
}


PROOF_SEEDS = [0, 1, 2, 3, 4]

PROOF_SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "kin_biased_rearing",
        {},
    ),
    (
        "kin_biased_rearing_grandmother_off",
        {
            "enable_grandmother_effects": False,
        },
    ),
    (
        "kin_biased_rearing_grandmother_on",
        {
            "enable_grandmother_effects": True,
        },
    ),
    (
        "no_relatedness_bias",
        {
            "enable_relatedness_bias": False,
            "initial_group_count": 4,
            "founder_pairs_per_group": 8,
        },
    ),
    (
        "shuffled_relatedness",
        {
            "shuffle_relatedness_for_care": True,
        },
    ),
    (
        "no_rearing_dependency",
        {
            "enable_rearing_dependency": False,
            "enable_care_benefit": False,
        },
    ),
    (
        "unrelated_rearing_groups",
        {
            "foster_to_nonparent_group_probability": 1.0,
            "offspring_dispersal_probability": 0.0,
            "matured_dispersal_probability": 0.85,
        },
    ),
    (
        "cost_too_high",
        {
            "care_cost_per_unit": 0.75,
        },
    ),
    (
        "high_juvenile_dispersal",
        {
            "offspring_dispersal_probability": 0.70,
            "matured_dispersal_probability": 0.85,
        },
    ),
]


def resolve_config(updates: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a validated config, accepting only canonical config keys."""

    resolved = dict(DEFAULT_CONFIG)
    if updates is not None:
        for key, value in updates.items():
            if key not in DEFAULT_CONFIG:
                raise KeyError(f"Unknown ecological kin-selection config key '{key}'")
            resolved[key] = value

    _validate_config(resolved)
    return resolved


def resolve_scenario_config(scenario_name: str, seed: int) -> dict[str, Any]:
    """Build one proof scenario config from the named config-table entry."""

    scenario_updates = None
    for candidate_name, updates in PROOF_SCENARIOS:
        if candidate_name == scenario_name:
            scenario_updates = updates
            break

    if scenario_updates is None:
        raise KeyError(f"Unknown ecological kin-selection scenario '{scenario_name}'")

    merged = dict(config)
    merged.update(scenario_updates)
    merged["random_seed"] = seed
    merged["write_latest_run"] = False
    return resolve_config(merged)


def _validate_config(resolved: Mapping[str, Any]) -> None:
    if int(resolved["simulation_steps"]) < 1:
        raise ValueError("simulation_steps must be >= 1")
    if int(resolved["initial_group_count"]) < 1:
        raise ValueError("initial_group_count must be >= 1")
    if int(resolved["founder_pairs_per_group"]) < 1:
        raise ValueError("founder_pairs_per_group must be >= 1")
    if int(resolved["initial_children_per_pair"]) < 0:
        raise ValueError("initial_children_per_pair must be >= 0")
    if int(resolved["genome_loci"]) < 1:
        raise ValueError("genome_loci must be >= 1")
    if int(resolved["juvenile_maturity_age"]) < 1:
        raise ValueError("juvenile_maturity_age must be >= 1")
    if int(resolved["elder_age"]) <= int(resolved["juvenile_maturity_age"]):
        raise ValueError("elder_age must be greater than juvenile_maturity_age")
    if int(resolved["max_age"]) <= int(resolved["elder_age"]):
        raise ValueError("max_age must be greater than elder_age")
    if int(resolved["max_population"]) < 1:
        raise ValueError("max_population must be >= 1")
    if int(resolved["live_viewer_frames_per_second"]) < 1:
        raise ValueError("live_viewer_frames_per_second must be >= 1")
    if int(resolved["live_viewer_cell_size"]) < 2:
        raise ValueError("live_viewer_cell_size must be >= 2")
    if int(resolved["live_viewer_group_columns"]) < 1:
        raise ValueError("live_viewer_group_columns must be >= 1")
    if int(resolved["live_viewer_group_cell_columns"]) < 1:
        raise ValueError("live_viewer_group_cell_columns must be >= 1")
    if int(resolved["live_viewer_group_cell_rows"]) < 1:
        raise ValueError("live_viewer_group_cell_rows must be >= 1")

    probabilities = [
        "adult_survival_probability",
        "elder_survival_probability",
        "female_reproduction_probability",
        "max_mate_relatedness",
        "same_group_mate_preference_probability",
        "offspring_dispersal_probability",
        "foster_to_nonparent_group_probability",
        "matured_dispersal_probability",
        "base_juvenile_survival_probability",
        "rearing_independent_juvenile_survival_probability",
        "helping_mutation_probability",
        "rare_helper_founder_probability",
    ]
    for key in probabilities:
        value = float(resolved[key])
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    nonnegative = [
        "initial_adult_energy",
        "initial_juvenile_energy",
        "helping_mutation_stddev",
        "juvenile_metabolic_cost",
        "adult_metabolic_cost",
        "elder_metabolic_cost",
        "juvenile_foraging_energy_gain",
        "adult_foraging_energy_gain",
        "elder_foraging_energy_gain",
        "max_energy",
        "reproduction_energy_threshold",
        "reproduction_energy_cost",
        "child_energy",
        "care_benefit_to_survival",
        "care_saturation",
        "care_capacity_per_helper",
        "care_cost_per_unit",
        "helper_energy_reserve",
        "care_baseline_weight",
        "kin_bias_strength",
        "kin_relatedness_threshold",
        "grandmother_care_capacity_multiplier",
        "grandmother_household_weight_bonus",
        "rare_helper_trait_value",
        "helping_trait_invasion_threshold",
        "proof_success_min_invasion_frequency_increase",
        "proof_success_min_hamilton_margin_proxy",
    ]
    for key in nonnegative:
        if float(resolved[key]) < 0.0:
            raise ValueError(f"{key} must be >= 0")

    trait_min = float(resolved["initial_helping_trait_min"])
    trait_max = float(resolved["initial_helping_trait_max"])
    if not 0.0 <= trait_min <= trait_max <= 1.0:
        raise ValueError(
            "initial_helping_trait_min and initial_helping_trait_max must satisfy "
            "0 <= min <= max <= 1"
        )
    rare_trait = float(resolved["rare_helper_trait_value"])
    invasion_threshold = float(resolved["helping_trait_invasion_threshold"])
    if trait_max >= invasion_threshold:
        raise ValueError(
            "initial_helping_trait_max must be below helping_trait_invasion_threshold"
        )
    if not trait_max < invasion_threshold <= rare_trait <= 1.0:
        raise ValueError(
            "helping_trait_invasion_threshold and rare_helper_trait_value must satisfy "
            "initial_max < threshold <= rare_trait <= 1"
        )

    adult_age_min = int(resolved["initial_adult_age_min"])
    adult_age_max = int(resolved["initial_adult_age_max"])
    if adult_age_min > adult_age_max:
        raise ValueError("initial_adult_age_min must be <= initial_adult_age_max")

    child_age_min = int(resolved["initial_child_age_min"])
    child_age_max = int(resolved["initial_child_age_max"])
    if child_age_min > child_age_max:
        raise ValueError("initial_child_age_min must be <= initial_child_age_max")
    if child_age_max >= int(resolved["juvenile_maturity_age"]):
        raise ValueError("initial_child_age_max must be below juvenile_maturity_age")


config = dict(DEFAULT_CONFIG)
