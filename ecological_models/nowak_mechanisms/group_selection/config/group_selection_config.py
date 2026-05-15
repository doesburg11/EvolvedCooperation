#!/usr/bin/env python3
"""Active parameters for the ecological group-selection model."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    # Runtime and output.
    "random_seed": 0,
    "simulation_steps": 500,
    "write_latest_run": True,
    "data_dir": "ecological_models/nowak_mechanisms/group_selection/data",
    # Initial population structure.
    "initial_group_count": 16,
    "founder_pairs_per_group": 4,
    "initial_children_per_pair": 3,
    "initial_adult_age_min": 8,
    "initial_adult_age_max": 18,
    "initial_child_age_min": 0,
    "initial_child_age_max": 3,
    "initial_adult_energy": 12.0,
    "initial_juvenile_energy": 4.0,
    # Helping trait.
    "initial_helping_trait_min": 0.0,
    "initial_helping_trait_max": 0.04,
    # Higher than kin selection (0.03) because group selection requires cooperators
    # seeded across multiple groups simultaneously to create between-group variance.
    "rare_helper_founder_probability": 0.12,
    "rare_helper_trait_value": 0.65,
    "helping_trait_invasion_threshold": 0.10,
    "helping_mutation_probability": 0.20,
    "helping_mutation_stddev": 0.04,
    # Direct energy cost of cooperative behavior paid each step by adults/elders.
    "helping_cost_per_step": 0.02,
    # Reproduction cost: cooperators spend time on group activities rather than
    # mating/courtship. effective_repr_prob = base * (1 - trait * scale).
    # This is the primary within-group disadvantage: at scale=0.40, a full cooperator
    # (trait=0.65) reproduces at 74% of a resident's rate, creating genuine
    # within-group selection against cooperation.
    "helping_reproduction_cost_scale": 0.25,
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
    # Fixed juvenile survival (no care dependency in group selection model).
    "base_juvenile_survival_probability": 0.92,
    # Sexual reproduction.
    "female_reproduction_probability": 0.35,
    "female_min_reproduction_age": 6,
    "female_max_reproduction_age": 45,
    "male_min_reproduction_age": 6,
    "male_max_reproduction_age": 55,
    "reproduction_energy_threshold": 7.0,
    "reproduction_energy_cost": 1.0,
    "child_energy": 3.5,
    "same_group_mate_preference_probability": 0.65,
    # Offspring born into a random other group (models infant fostering / raiding capture).
    "offspring_dispersal_probability": 0.0,
    # Young adults who disperse at maturation. High dispersal homogenises groups,
    # reducing between-group variance and weakening group selection.
    "matured_dispersal_probability": 0.05,
    # Carrying capacity (density-dependent mortality, not Moran replacement).
    "max_population": 400,
    # -----------------------------------------------------------------------
    # Group selection mechanism.
    # Mirrors the Moran group_selection_interval. Every conflict_interval steps
    # one conflict event is drawn. Set very high (e.g. 9999) to disable.
    "conflict_interval": 25,
    # Fraction of the losing group's adults affected per conflict event.
    "conflict_replacement_fraction": 0.30,
    # Gaussian noise on each group's combat-effectiveness score.
    "conflict_noise_stddev": 0.02,
    # Scales the mean helping-trait advantage in the combat score.
    "conflict_winner_advantage_scale": 1.5,
    # Energy bonus given to all winner-group adults after a successful conflict.
    # Models territorial/resource gains from winning inter-group competition.
    # This is the primary benefit that makes group selection work: cooperative groups
    # grow faster after winning, and so their traits spread through reproduction.
    "conflict_winner_energy_bonus": 2.0,
    # Groups with fewer members than this are absorbed by the winner.
    "min_viable_group_size": 3,
    # Groups exceeding this total size split into two daughter groups.
    "fission_threshold": 50,
    # -----------------------------------------------------------------------
    # Warfare addon (ecological analog of grandmother effect in kin selection).
    # When enabled, losing-group adults affected by conflict can die rather than
    # just emigrating to the winner — models lethal inter-group raiding.
    # Bowles (2006) showed that warfare lethality is a key amplifier of
    # between-group selection pressure.
    "enable_warfare": True,
    "warfare_lethality": 0.10,
    # -----------------------------------------------------------------------
    # Group public goods addon (off by default).
    # When enabled, adults contribute helping_trait * contribution_rate * energy
    # to a group pool each step. The pool is multiplied and redistributed equally.
    # This adds within-group collective benefit on top of the conflict mechanism.
    "enable_group_public_goods": False,
    "public_goods_contribution_rate": 0.10,
    "public_goods_multiplier": 2.0,
    # -----------------------------------------------------------------------
    # Proof-of-mechanism thresholds.
    "proof_success_min_trait_increase": 0.015,
    "proof_success_min_invasion_frequency_increase": 0.02,
    "proof_success_min_final_population": 50,
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
        "group_selection_baseline",
        {},
    ),
    (
        "group_selection_off",
        # Conflict interval so large it never fires within simulation_steps.
        {"conflict_interval": 9999},
    ),
    (
        "warfare_off",
        {"enable_warfare": False},
    ),
    (
        "warfare_high_lethality",
        {"enable_warfare": True, "warfare_lethality": 0.40},
    ),
    (
        "high_conflict_frequency",
        {"conflict_interval": 10},
    ),
    (
        "low_conflict_frequency",
        {"conflict_interval": 100},
    ),
    (
        "many_small_groups",
        # More groups → higher between-group variance → stronger group selection.
        {"initial_group_count": 32, "founder_pairs_per_group": 2},
    ),
    (
        "few_large_groups",
        # Fewer groups → lower between-group variance → weaker group selection.
        {"initial_group_count": 4, "founder_pairs_per_group": 8},
    ),
    (
        "high_dispersal",
        # High maturation dispersal mixes groups → reduces between-group variance.
        {"matured_dispersal_probability": 0.50},
    ),
    (
        "cost_too_high",
        # Helping so costly that within-group disadvantage overwhelms group benefit.
        {"helping_cost_per_step": 0.15},
    ),
    (
        "group_public_goods_on",
        {"enable_group_public_goods": True},
    ),
]


def resolve_config(updates: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a validated config, accepting only canonical config keys."""
    resolved = dict(DEFAULT_CONFIG)
    if updates is not None:
        for key, value in updates.items():
            if key not in DEFAULT_CONFIG:
                raise KeyError(f"Unknown ecological group-selection config key '{key}'")
            resolved[key] = value
    _validate_config(resolved)
    return resolved


def resolve_scenario_config(scenario_name: str, seed: int) -> dict[str, Any]:
    """Build one proof scenario config from the named scenario table entry."""
    scenario_updates = None
    for candidate_name, updates in PROOF_SCENARIOS:
        if candidate_name == scenario_name:
            scenario_updates = updates
            break
    if scenario_updates is None:
        raise KeyError(f"Unknown ecological group-selection scenario '{scenario_name}'")
    merged = dict(DEFAULT_CONFIG)
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
    if int(resolved["juvenile_maturity_age"]) < 1:
        raise ValueError("juvenile_maturity_age must be >= 1")
    if int(resolved["elder_age"]) <= int(resolved["juvenile_maturity_age"]):
        raise ValueError("elder_age must be greater than juvenile_maturity_age")
    if int(resolved["max_age"]) <= int(resolved["elder_age"]):
        raise ValueError("max_age must be greater than elder_age")
    if int(resolved["max_population"]) < 1:
        raise ValueError("max_population must be >= 1")
    if int(resolved["conflict_interval"]) < 1:
        raise ValueError("conflict_interval must be >= 1")
    if int(resolved["min_viable_group_size"]) < 1:
        raise ValueError("min_viable_group_size must be >= 1")
    if int(resolved["fission_threshold"]) < 2:
        raise ValueError("fission_threshold must be >= 2")

    probabilities = [
        "adult_survival_probability",
        "elder_survival_probability",
        "base_juvenile_survival_probability",
        "female_reproduction_probability",
        "same_group_mate_preference_probability",
        "offspring_dispersal_probability",
        "matured_dispersal_probability",
        "helping_mutation_probability",
        "rare_helper_founder_probability",
        "warfare_lethality",
        "public_goods_contribution_rate",
    ]
    for key in probabilities:
        value = float(resolved[key])
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    nonnegative = [
        "helping_reproduction_cost_scale",
        "initial_adult_energy",
        "initial_juvenile_energy",
        "helping_mutation_stddev",
        "helping_cost_per_step",
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
        "conflict_noise_stddev",
        "conflict_winner_advantage_scale",
        "conflict_winner_energy_bonus",
        "public_goods_multiplier",
        "rare_helper_trait_value",
        "helping_trait_invasion_threshold",
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
