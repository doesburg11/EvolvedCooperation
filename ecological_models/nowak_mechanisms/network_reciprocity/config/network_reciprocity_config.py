#!/usr/bin/env python3
"""Active parameters for the ecological network-reciprocity model."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    # Runtime and output.
    "random_seed": 0,
    "simulation_steps": 500,
    "write_latest_run": True,
    "data_dir": "ecological_models/nowak_mechanisms/network_reciprocity/data",
    # Initial population structure.
    # Founders are placed near patch_count spatial patch centers in the unit square.
    "initial_patch_count": 16,
    "founder_pairs_per_patch": 4,
    "initial_children_per_pair": 3,
    "initial_adult_age_min": 8,
    "initial_adult_age_max": 18,
    "initial_child_age_min": 0,
    "initial_child_age_max": 3,
    "initial_adult_energy": 12.0,
    "initial_juvenile_energy": 4.0,
    # Radius within which founders are scattered around each patch center.
    "patch_init_radius": 0.06,
    # Helping trait.
    "initial_helping_trait_min": 0.0,
    "initial_helping_trait_max": 0.04,
    "rare_helper_founder_probability": 0.10,
    "rare_helper_trait_value": 0.65,
    "helping_trait_invasion_threshold": 0.10,
    "helping_mutation_probability": 0.20,
    "helping_mutation_stddev": 0.04,
    # -----------------------------------------------------------------------
    # Network reciprocity mechanism.
    # Each adult distributes a fixed energy budget to spatial neighbors;
    # benefits flow within interaction_radius and are split equally per neighbor.
    # The ecological analog of Nowak's b/c > k condition.
    "interaction_radius": 0.12,
    # Total energy benefit delivered by a cooperating adult per step,
    # split equally among neighbors within interaction_radius.
    # Per-neighbor benefit = helping_trait * cooperation_benefit_per_step / n_neighbors.
    "cooperation_benefit_per_step": 0.20,
    # Energy cost paid by adults/elders each step, independent of neighbor count.
    "helping_cost_per_step": 0.04,
    # Reproduction cost: effective_repr_prob = base * (1 - trait * scale).
    # Creates within-neighborhood selection against cooperation (analogous to
    # within-group disadvantage in the group-selection model).
    "helping_reproduction_cost_scale": 0.20,
    # Ablation flag: if True, benefit is distributed uniformly to all individuals
    # rather than to spatial neighbors. Removes spatial routing without changing
    # the total energy delivered. Expected result: cooperation declines.
    "random_benefit_routing": False,
    # -----------------------------------------------------------------------
    # Spatial offspring placement.
    # Offspring are born within offspring_placement_radius of their mother.
    # This is the primary mechanism creating spatial cooperator clusters.
    # Must be kept smaller than interaction_radius for clusters to be self-reinforcing.
    "offspring_placement_radius": 0.07,
    # Ablation flag: if True, offspring are placed uniformly at random across
    # the unit square, preventing cluster formation. Expected result: cooperation declines.
    "random_offspring_placement": False,
    # -----------------------------------------------------------------------
    # Mate choice by spatial proximity.
    "mating_radius": 0.20,
    "same_area_mate_preference_probability": 0.60,
    # -----------------------------------------------------------------------
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
    # -----------------------------------------------------------------------
    # Adult dispersal at maturation (undermines spatial cooperator clusters).
    # High matured dispersal is the primary disruptor of network reciprocity
    # in ecological populations — analogous to high dispersal in the group
    # selection model, and to the high_juvenile_dispersal control in kin selection.
    "matured_dispersal_probability": 0.05,
    # How far a dispersing adult moves from their current position.
    "matured_dispersal_radius": 0.35,
    # -----------------------------------------------------------------------
    # Carrying capacity (density-dependent mortality).
    "max_population": 400,
    # -----------------------------------------------------------------------
    # Proof-of-mechanism thresholds.
    "proof_success_min_trait_increase": 0.010,
    "proof_success_min_invasion_frequency_increase": 0.02,
    "proof_success_min_final_population": 50,
}


PROOF_SEEDS = [0, 1, 2, 3, 4]

PROOF_SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    (
        "network_reciprocity_baseline",
        {},
    ),
    (
        "scattered_offspring",
        # Offspring placed uniformly at random — spatial cooperator clusters cannot form.
        # Cooperation has no local assortment advantage: expected to decline.
        # This is the primary mechanism-off test: offspring placement is load-bearing.
        {"random_offspring_placement": True},
    ),
    (
        "no_spatial_structure",
        # Both random offspring placement AND global mating (no area preference).
        # Removes all spatial reproductive structure simultaneously.
        # Cooperation dilutes through blending inheritance in 4-5 generations.
        {"random_offspring_placement": True, "same_area_mate_preference_probability": 0.0},
    ),
    (
        "cost_too_high",
        # Helping cost so large that cooperators drain energy faster than they forage.
        # Cooperation must decline: mean trait falls even as mutation creates noise.
        {"helping_cost_per_step": 0.20},
    ),
    (
        "tight_clustering",
        # Very small offspring placement radius creates dense cooperator clusters.
        # Cluster members are almost exclusively cooperators → strong local advantage.
        {"offspring_placement_radius": 0.03},
    ),
    (
        "uniform_benefit_routing",
        # Benefits distributed uniformly to all individuals rather than neighbors.
        # Key finding: cooperation still spreads because spatial reproductive assortment
        # (local offspring placement + spatial mating preference) is the primary mechanism.
        # Spatial benefit routing amplifies but does not create the mechanism.
        {"random_benefit_routing": True},
    ),
    (
        "wide_neighborhood",
        # Large interaction radius: benefits diluted across many neighbors, per-neighbor
        # benefit is very small. Cooperation still spreads through spatial reproductive
        # assortment — confirms the mechanism is primarily reproductive, not energetic.
        {"interaction_radius": 0.35},
    ),
    (
        "low_dispersal",
        # No adult dispersal at maturation — cooperator clusters accumulate undisturbed.
        # Amplifies the mechanism by preserving spatial structure across generations.
        {"matured_dispersal_probability": 0.0},
    ),
    (
        "high_matured_dispersal",
        # Maturing adults scatter widely. Cooperation still spreads because adults
        # remain in their new location and reproduce locally after dispersal.
        # Confirms that even partial cluster disruption does not defeat the mechanism.
        {"matured_dispersal_probability": 0.40},
    ),
    (
        "high_benefit",
        # High benefit per cooperator: cluster energy advantage much larger than cost.
        # Amplifies cooperation spread.
        {"cooperation_benefit_per_step": 0.45},
    ),
]


def resolve_config(updates: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a validated config, accepting only canonical config keys."""
    resolved = dict(DEFAULT_CONFIG)
    if updates is not None:
        for key, value in updates.items():
            if key not in DEFAULT_CONFIG:
                raise KeyError(f"Unknown ecological network-reciprocity config key '{key}'")
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
        raise KeyError(f"Unknown ecological network-reciprocity scenario '{scenario_name}'")
    merged = dict(DEFAULT_CONFIG)
    merged.update(scenario_updates)
    merged["random_seed"] = seed
    merged["write_latest_run"] = False
    return resolve_config(merged)


def _validate_config(resolved: Mapping[str, Any]) -> None:
    if int(resolved["simulation_steps"]) < 1:
        raise ValueError("simulation_steps must be >= 1")
    if int(resolved["initial_patch_count"]) < 1:
        raise ValueError("initial_patch_count must be >= 1")
    if int(resolved["founder_pairs_per_patch"]) < 1:
        raise ValueError("founder_pairs_per_patch must be >= 1")
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

    probabilities = [
        "adult_survival_probability",
        "elder_survival_probability",
        "base_juvenile_survival_probability",
        "female_reproduction_probability",
        "same_area_mate_preference_probability",
        "matured_dispersal_probability",
        "helping_mutation_probability",
        "rare_helper_founder_probability",
    ]
    for key in probabilities:
        value = float(resolved[key])
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    nonnegative = [
        "interaction_radius",
        "cooperation_benefit_per_step",
        "helping_cost_per_step",
        "helping_reproduction_cost_scale",
        "offspring_placement_radius",
        "patch_init_radius",
        "mating_radius",
        "matured_dispersal_radius",
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
