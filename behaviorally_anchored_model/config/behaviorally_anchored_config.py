#!/usr/bin/env python3
"""Active parameters for the behaviorally anchored model."""

from __future__ import annotations

import math
from typing import Any, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    # Runtime and output.
    "random_seed": 0,
    "simulation_steps": 500,
    "proof_simulation_steps": 250,
    "write_latest_run": True,
    "data_dir": "behaviorally_anchored_model/data",
    # Initial population structure.
    "initial_founder_pairs": 64,
    "initial_children_per_pair": 3,
    "initial_adult_age_min": 18,
    "initial_adult_age_max": 36,
    "initial_child_age_min": 0,
    "initial_child_age_max": 11,
    "initial_adult_energy": 12.0,
    "initial_juvenile_energy": 4.0,
    # Helping trait (heritable, evolving).
    "initial_helping_trait_min": 0.0,
    "initial_helping_trait_max": 0.04,
    "rare_helper_founder_probability": 0.10,
    "rare_helper_trait_value": 0.65,
    "helping_trait_invasion_threshold": 0.10,
    "helping_mutation_probability": 0.20,
    "helping_mutation_stddev": 0.04,
    # -----------------------------------------------------------------------
    # Capacity 1: Reputation sensitivity (indirect reciprocity).
    # Donors observe recipient reputation with probability q and route energy
    # selectively to high-reputation individuals (Nowak q > c/b condition).
    # High-reputation males are preferred as mates — genetic assortment channel.
    # Ablation: reputation_mate_preference=0, random_benefit_routing=True.
    # -----------------------------------------------------------------------
    "reputation_observation_prob": 0.70,
    "reputation_threshold": 0.50,
    "reputation_initial": 0.65,
    "reputation_update_weight": 0.10,
    "random_benefit_routing": False,
    "reputation_mate_preference": 0.80,
    # -----------------------------------------------------------------------
    # Capacity 2: Norm enforcement.
    # Adults with reputation significantly below the population mean incur a
    # social energy penalty (collective exclusion / third-party sanctioning).
    # Ablation: norm_enforcement_strength=0.
    # -----------------------------------------------------------------------
    "norm_enforcement_strength": 0.50,
    "norm_violation_penalty": 0.15,
    "norm_detection_sensitivity": 0.25,
    # -----------------------------------------------------------------------
    # Capacity 3: Bands (group selection).
    # group_id now means concrete band membership. Bands have territory centers,
    # attract members weakly, can receive migrants, fission when large, fuse
    # when small, and bias interaction/mate choice through group_bias and
    # group_mate_preference. Inter-band conflict transfers energy from
    # less-cooperative to more-cooperative bands every conflict_interval steps.
    # Ablation (identity only): group_bias=0, group_mate_preference=0.
    # Ablation (conflict only): conflict_interval=0.
    # Full ablation: all group/band routing, migration, fission/fusion, and
    # conflict controls to 0.
    # -----------------------------------------------------------------------
    "n_groups": 4,
    "band_territory_radius": 34.0,
    "band_member_attraction": 0.04,
    "band_territory_update_weight": 0.02,
    "group_migration_probability": 0.004,
    "band_migration_min_age": 12,
    "band_fission_interval": 30,
    "band_fission_size_threshold": 150,
    "band_fission_min_size": 45,
    "band_fission_dispersal_std": 22.0,
    "band_fusion_interval": 40,
    "band_fusion_size_threshold": 12,
    "band_fusion_distance": 24.0,
    "group_bias": 0.30,
    "group_mate_preference": 0.30,
    "interband_marriage_preference": 0.15,
    "interband_marriage_distance": 42.0,
    "conflict_interval": 20,
    "conflict_winner_bonus": 0.80,
    "conflict_loser_penalty": 0.40,
    # Hunter-gatherer territorial competition is soft here: overlapping bands
    # usually avoid and displace rather than defend hard borders. Contests
    # become more likely only when overlap coincides with local resource
    # scarcity.
    "territorial_overlap_start_fraction": 0.05,
    "territorial_avoidance_strength": 0.15,
    "territorial_scarcity_threshold": 0.55,
    "territorial_conflict_probability": 0.035,
    "territorial_conflict_scarcity_weight": 0.08,
    "territorial_conflict_energy_penalty": 0.20,
    "territorial_displacement_distance": 3.5,
    # -----------------------------------------------------------------------
    # Capacity 4: Kin recognition, households, and child rearing.
    # Agents preferentially route interactions toward kin (siblings, parents,
    # offspring — individuals sharing a parent). Households are co-resident
    # family/camp units with a moving residence point. Adults and elders provide
    # costly care to nearby juveniles, with parent, kin, spouse, co-parent, and
    # household membership biasing which juveniles receive care. Parents also
    # transfer surplus harvested food to their own nearby juveniles. Juveniles
    # receive a survival bonus from living parents and adult household caregivers.
    # Kin/household clusters form through pedigree, residence, and maturity
    # dispersal.
    # Ablation: kin/spouse/household/care effects are set to 0.
    # -----------------------------------------------------------------------
    "kin_bias": 0.30,
    "kin_mate_preference": 0.40,
    "spouse_bond_probability": 1.0,
    "spouse_mate_preference": 5.0,
    "spouse_reciprocity_bond_probability": 0.75,
    "spouse_reciprocity_bond_persistence_probability": 0.95,
    "spouse_reciprocity_bond_radius": 24.0,
    "spouse_household_join_probability": 0.85,
    "initial_spouse_dispersal_std": 4.0,
    "juvenile_household_attraction": 0.35,
    "subadult_household_attraction": 0.20,
    "adult_household_attraction": 0.12,
    "elder_household_attraction": 0.08,
    "household_residence_update_weight": 0.25,
    "maturity_new_household_probability": 0.35,
    "maturity_household_dispersal_std": 12.0,
    "household_single_living_parent_survival_bonus": 0.02,
    "household_two_living_parent_survival_bonus": 0.05,
    "household_caregiver_survival_bonus_per_adult": 0.01,
    "household_caregiver_survival_bonus_max": 0.04,
    "parent_food_transfer_capacity": 0.90,
    "parent_food_transfer_energy_reserve": 6.0,
    "parent_food_transfer_radius": 24.0,
    "parent_food_transfer_household_weight_bonus": 1.0,
    "juvenile_food_survival_benefit": 0.05,
    "juvenile_food_survival_saturation": 0.65,
    "juvenile_no_food_survival_penalty": 0.005,
    "child_rearing_radius": 18.0,
    "child_rearing_care_capacity_per_helper": 0.85,
    "child_rearing_cost_per_care": 0.04,
    "child_rearing_helper_energy_reserve": 4.0,
    "child_rearing_survival_benefit": 0.12,
    "child_rearing_saturation": 0.65,
    "child_rearing_baseline_weight": 0.03,
    "child_rearing_parent_weight_bonus": 4.0,
    "child_rearing_kin_weight_bonus": 2.0,
    "child_rearing_household_member_weight_bonus": 0.8,
    "child_rearing_spouse_parent_weight_bonus": 1.5,
    "child_rearing_coparent_near_weight_bonus": 2.0,
    # -----------------------------------------------------------------------
    # Capacity 5: Spatial awareness (network reciprocity).
    # Agents have heritable spatial coordinates. Offspring are placed near their
    # mother (dispersal_std controls spread). Interactions can be biased toward
    # spatial neighbors (spatial_bias), and males within spatial_mate_radius
    # receive a mate-choice weight bonus (spatial_mate_preference).
    # Ablation: spatial_bias=0, spatial_mate_preference=0.
    # -----------------------------------------------------------------------
    "space_width": 100.0,
    # When True, space_width is derived from n_groups and band_territory_radius
    # so that initial band territories do not overlap. The stored space_width
    # value is ignored in that case. grass_grid_size is also scaled to keep
    # grass cell density constant on the larger landscape.
    "space_width_auto": True,
    "offspring_dispersal_std": 8.0,
    "juvenile_movement_step_std": 1.10,
    "subadult_movement_step_std": 0.95,
    "adult_movement_step_std": 0.80,
    "elder_movement_step_std": 0.35,
    "interaction_radius": 15.0,
    "spatial_bias": 0.30,
    "spatial_mate_radius": 20.0,
    "spatial_mate_preference": 0.50,
    # -----------------------------------------------------------------------
    # Capacity 6: Reciprocity bonds (direct reciprocity).
    # Adults form stable dyadic reciprocity bonds. Bonded agents interact
    # preferentially over strangers. Conditional cooperation
    # (reciprocity_weight) reduces cooperation toward non-reciprocating
    # bondmates. Differential dissolution (leave_weight) increases dissolution
    # probability when reciprocity_bond_memory is low.
    # Ablation: reciprocity_bond_persistence_probability=0 (all bonds dissolve
    # immediately, no direct-reciprocity bond fidelity).
    # -----------------------------------------------------------------------
    "reciprocity_bond_persistence_probability": 0.85,
    "reciprocity_bond_formation_radius": 20.0,
    "reciprocity_bond_dissolution_radius": 30.0,
    "reciprocity_weight": 0.60,
    "leave_weight": 0.50,
    "memory_smoothing": 0.20,
    # -----------------------------------------------------------------------
    # Capacity 7: Social learning.
    # Subadults and adults can copy nearby demonstrators. Demonstrators are
    # weighted by reputation and energy, and learners update a bounded
    # within-lifetime adjustment around their inherited helping trait. This
    # keeps genetic inheritance and cultural/individual learning separate.
    # Ablation: social_learning_probability=0.
    # -----------------------------------------------------------------------
    "social_learning_probability": 0.18,
    "social_learning_radius": 24.0,
    "social_learning_rate": 0.12,
    "social_learning_reputation_weight": 1.00,
    "social_learning_success_weight": 0.60,
    "social_learning_max_adjustment": 0.35,
    # -----------------------------------------------------------------------
    # Energy mechanics.
    "cooperation_benefit_per_step": 0.25,
    "helping_cost_per_step": 0.04,
    "helping_reproduction_cost_scale": 0.10,
    # Local grass ecology. Subadult, adult, and elder foraging gains below are
    # interpreted as maximum grass harvest per step, so crowded cells can become
    # depleted.
    "grass_grid_size": 25,
    "grass_max_per_cell": 2.0,
    "grass_initial_fraction": 1.0,
    "grass_regrowth_per_step": 0.18,
    "grass_harvest_radius": 8.0,
    # -----------------------------------------------------------------------
    # Life history.
    "juvenile_dependency_age": 12,
    "adult_maturity_age": 18,
    "elder_age": 55,
    "max_age": 85,
    "juvenile_metabolic_cost": 0.08,
    "subadult_metabolic_cost": 0.11,
    "adult_metabolic_cost": 0.12,
    "elder_metabolic_cost": 0.15,
    "juvenile_foraging_energy_gain": 0.03,
    "subadult_foraging_energy_gain": 0.16,
    "adult_foraging_energy_gain": 0.40,
    "elder_foraging_energy_gain": 0.24,
    "max_energy": 18.0,
    "subadult_survival_probability": 0.998,
    "adult_survival_probability": 0.999,
    "elder_survival_probability": 0.995,
    "base_juvenile_survival_probability": 0.88,
    # Sexual reproduction.
    "female_reproduction_probability": 0.90,
    "female_min_reproduction_age": 18,
    "female_max_reproduction_age": 45,
    "male_min_reproduction_age": 20,
    "male_max_reproduction_age": 60,
    "reproduction_energy_threshold": 3.5,
    "reproduction_energy_cost": 0.6,
    "child_energy": 4.0,
    # -----------------------------------------------------------------------
    # Density ecology.
    # density_target_population is not a hard cap. Crowding above this target
    # reduces reproduction and survival through soft density pressure.
    "density_target_population": 400,
    "density_reproduction_pressure": 4.0,
    "density_survival_pressure": 0.25,
    # -----------------------------------------------------------------------
    # Proof-of-mechanism thresholds.
    "proof_success_min_trait_increase": 0.010,
    "proof_success_min_invasion_frequency_increase": 0.02,
    "proof_success_min_final_population": 50,
}


PROOF_SEEDS = [0, 1, 2]

# Ablation helpers (repeated sets of keys for clean scenario definitions).
_REP_OFF = {"reputation_mate_preference": 0.0, "random_benefit_routing": True}
_NORM_OFF = {"norm_enforcement_strength": 0.0}
_GROUP_OFF = {
    "band_member_attraction": 0.0,
    "group_migration_probability": 0.0,
    "band_fission_interval": 0,
    "band_fusion_interval": 0,
    "group_bias": 0.0,
    "group_mate_preference": 0.0,
    "interband_marriage_preference": 0.0,
    "conflict_interval": 0,
    "territorial_avoidance_strength": 0.0,
    "territorial_conflict_probability": 0.0,
    "territorial_conflict_scarcity_weight": 0.0,
    "territorial_conflict_energy_penalty": 0.0,
    "territorial_displacement_distance": 0.0,
}
_KIN_OFF = {
    "kin_bias": 0.0,
    "kin_mate_preference": 0.0,
    "spouse_bond_probability": 0.0,
    "spouse_mate_preference": 0.0,
    "spouse_reciprocity_bond_probability": 0.0,
    "spouse_reciprocity_bond_persistence_probability": 0.0,
    "spouse_household_join_probability": 0.0,
    "juvenile_household_attraction": 0.0,
    "subadult_household_attraction": 0.0,
    "adult_household_attraction": 0.0,
    "elder_household_attraction": 0.0,
    "household_residence_update_weight": 0.0,
    "maturity_new_household_probability": 0.0,
    "household_single_living_parent_survival_bonus": 0.0,
    "household_two_living_parent_survival_bonus": 0.0,
    "household_caregiver_survival_bonus_per_adult": 0.0,
    "household_caregiver_survival_bonus_max": 0.0,
    "parent_food_transfer_capacity": 0.0,
    "juvenile_food_survival_benefit": 0.0,
    "juvenile_no_food_survival_penalty": 0.0,
    "child_rearing_care_capacity_per_helper": 0.0,
    "child_rearing_survival_benefit": 0.0,
    "child_rearing_parent_weight_bonus": 0.0,
    "child_rearing_kin_weight_bonus": 0.0,
    "child_rearing_household_member_weight_bonus": 0.0,
    "child_rearing_spouse_parent_weight_bonus": 0.0,
    "child_rearing_coparent_near_weight_bonus": 0.0,
}
_SPATIAL_OFF = {"spatial_bias": 0.0, "spatial_mate_preference": 0.0}
_DR_OFF = {"reciprocity_bond_persistence_probability": 0.0}
_SOCIAL_LEARNING_OFF = {"social_learning_probability": 0.0}


def _merge(*dicts: dict) -> dict:
    result: dict = {}
    for d in dicts:
        result.update(d)
    return result


PROOF_SCENARIOS: list[tuple[str, dict[str, Any]]] = [
    # ------------------------------------------------------------------
    # Baseline and single-ablation scenarios (positive: expect invasion).
    # ------------------------------------------------------------------
    (
        "behaviorally_anchored_baseline",
        # All seven capacities active. Cooperation expected to invade strongly.
        {},
    ),
    (
        "no_social_learning",
        # Social learning off; inherited traits, reputation, norms, bands, kin,
        # spatial structure, and direct reciprocity remain active.
        _SOCIAL_LEARNING_OFF,
    ),
    (
        "no_norm_enforcement",
        # Norm enforcement off; all other capacities active.
        _NORM_OFF,
    ),
    (
        "no_direct_reciprocity",
        # Reciprocity bonds dissolve immediately (no direct-reciprocity fidelity).
        # All other capacities remain active.
        _DR_OFF,
    ),
    (
        "no_kin_selection",
        # Kin, spouse, household, child-care, and parent-food channels off.
        # Population replacement remains possible under the tuned baseline, so
        # this isolates whether other capacities can still carry cooperation.
        _KIN_OFF,
    ),
    (
        "no_network_reciprocity",
        # Spatial routing and spatial mate preference off.
        _SPATIAL_OFF,
    ),
    (
        "no_group_conflict",
        # Inter-band conflict off (conflict_interval=0); band routing,
        # same-band mate preference, migration, and fission/fusion remain active.
        {"conflict_interval": 0},
    ),
    # ------------------------------------------------------------------
    # Single-mechanism scenarios (each capacity alone).
    # ------------------------------------------------------------------
    (
        "reputation_only",
        # Only reputation sensitivity active (indirect reciprocity baseline).
        # Mirrors the ecological indirect-reciprocity model.
        _merge(_NORM_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF, _SOCIAL_LEARNING_OFF),
    ),
    (
        "kin_selection_only",
        # Only kin routing and kin mate preference active.
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _SPATIAL_OFF, _DR_OFF, _SOCIAL_LEARNING_OFF),
    ),
    (
        "network_reciprocity_only",
        # Only spatial routing and spatial mate preference active.
        # At combined-model parameters (spatial_bias=0.30, spatial_mate_pref=0.50),
        # spatial clustering alone is insufficient for invasion from rare.
        # Prediction: cooperation stays flat or declines (inverted).
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _KIN_OFF, _DR_OFF, _SOCIAL_LEARNING_OFF),
    ),
    (
        "group_selection_only",
        # Only band identity, territory dynamics, and conflict active.
        # At combined-model parameters (group_bias=0.30, group_mate_pref=0.30),
        # band identity alone is insufficient for invasion from rare.
        # Prediction: cooperation stays flat or declines (inverted).
        _merge(_REP_OFF, _NORM_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF, _SOCIAL_LEARNING_OFF),
    ),
    (
        "direct_reciprocity_only",
        # Only reciprocity-bond fidelity active. No genetic reproductive assortment channel.
        # Mirrors the ecological direct-reciprocity model (too weak to invade alone).
        # Prediction: cooperation stays flat or declines (inverted).
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF, _SOCIAL_LEARNING_OFF),
    ),
    (
        "social_learning_only",
        # Only within-lifetime copying is active. It can change behavior inside a
        # generation, but it has no direct genetic assortment channel by itself.
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF),
    ),
    (
        "strong_all_channels",
        # All capacities amplified.
        {
            "norm_enforcement_strength": 1.0,
            "group_bias": 0.60,
            "group_mate_preference": 0.60,
            "conflict_winner_bonus": 1.50,
            "territorial_avoidance_strength": 0.06,
            "territorial_conflict_probability": 0.06,
            "kin_bias": 0.60,
            "kin_mate_preference": 0.80,
            "spatial_bias": 0.60,
            "spatial_mate_preference": 0.90,
            "reciprocity_bond_persistence_probability": 0.92,
            "social_learning_probability": 0.30,
            "social_learning_rate": 0.20,
        },
    ),
    # ------------------------------------------------------------------
    # Inverted scenarios (cooperation expected to stay flat or decline).
    # ------------------------------------------------------------------
    (
        "norm_enforcement_only",
        # Only norm enforcement active: energy pressure on defectors but no
        # genetic reproductive assortment channel. Bottom-up prediction: decline.
        _merge(_REP_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF, _SOCIAL_LEARNING_OFF),
    ),
    (
        "all_capacities_off",
        # Every capacity ablated. Pure demographic baseline.
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF, _SOCIAL_LEARNING_OFF),
    ),
    (
        "cost_too_high",
        # Helping cost (1.00) overwhelms all channels, including social
        # learning-amplified effective helping. The combined model cannot
        # compensate.
        # Prediction: cooperation declines (inverted control).
        {"helping_cost_per_step": 1.00},
    ),
]


def _auto_space_width(resolved: dict[str, Any]) -> None:
    """Compute space_width so initial band territories don't overlap.

    Bands are placed in a ring at orbit = width * 0.32.  The chord between
    adjacent centres is 2 * orbit * sin(π / n_groups).  Setting that chord
    equal to 2 * territory_radius (touching) and adding 20 % breathing room
    gives the minimum grid width where territories are non-overlapping.

    For a single band any width >= 3 * radius is fine.
    grass_grid_size is rescaled proportionally to keep cell density constant.
    """
    n = int(resolved["n_groups"])
    r = float(resolved["band_territory_radius"])
    orbit_fraction = 0.32  # must match _initialize_bands
    if n == 1:
        w = r * 3.0
    else:
        w = r / (orbit_fraction * math.sin(math.pi / n)) * 1.2
    resolved["space_width"] = w
    base_width = float(DEFAULT_CONFIG["space_width"])
    base_grass = int(DEFAULT_CONFIG["grass_grid_size"])
    resolved["grass_grid_size"] = max(1, round(base_grass * (w / base_width)))


def resolve_config(updates: Mapping[str, Any] | None = None) -> dict[str, Any]:
    resolved = dict(DEFAULT_CONFIG)
    if updates is not None:
        for key, value in updates.items():
            if key not in DEFAULT_CONFIG:
                raise KeyError(f"Unknown behaviorally anchored config key '{key}'")
            resolved[key] = value
    if resolved["space_width_auto"]:
        _auto_space_width(resolved)
    _validate_config(resolved)
    return resolved


def resolve_scenario_config(scenario_name: str, seed: int) -> dict[str, Any]:
    scenario_updates = None
    for candidate_name, updates in PROOF_SCENARIOS:
        if candidate_name == scenario_name:
            scenario_updates = updates
            break
    if scenario_updates is None:
        raise KeyError(f"Unknown behaviorally anchored scenario '{scenario_name}'")
    merged = dict(DEFAULT_CONFIG)
    merged.update(scenario_updates)
    merged["random_seed"] = seed
    merged["simulation_steps"] = int(merged["proof_simulation_steps"])
    merged["write_latest_run"] = False
    return resolve_config(merged)


def _validate_config(resolved: Mapping[str, Any]) -> None:
    if int(resolved["simulation_steps"]) < 1:
        raise ValueError("simulation_steps must be >= 1")
    if int(resolved["proof_simulation_steps"]) < 1:
        raise ValueError("proof_simulation_steps must be >= 1")
    if int(resolved["initial_founder_pairs"]) < 1:
        raise ValueError("initial_founder_pairs must be >= 1")
    if int(resolved["initial_children_per_pair"]) < 0:
        raise ValueError("initial_children_per_pair must be >= 0")
    if int(resolved["juvenile_dependency_age"]) < 1:
        raise ValueError("juvenile_dependency_age must be >= 1")
    if int(resolved["adult_maturity_age"]) <= int(resolved["juvenile_dependency_age"]):
        raise ValueError("adult_maturity_age must be greater than juvenile_dependency_age")
    if int(resolved["elder_age"]) <= int(resolved["adult_maturity_age"]):
        raise ValueError("elder_age must be greater than adult_maturity_age")
    if int(resolved["max_age"]) <= int(resolved["elder_age"]):
        raise ValueError("max_age must be greater than elder_age")
    if int(resolved["density_target_population"]) < 1:
        raise ValueError("density_target_population must be >= 1")
    if int(resolved["grass_grid_size"]) < 1:
        raise ValueError("grass_grid_size must be >= 1")
    if int(resolved["n_groups"]) < 1:
        raise ValueError("n_groups must be >= 1")
    if int(resolved["band_migration_min_age"]) < 0:
        raise ValueError("band_migration_min_age must be >= 0")
    if int(resolved["band_fission_size_threshold"]) < 2:
        raise ValueError("band_fission_size_threshold must be >= 2")
    if int(resolved["band_fission_min_size"]) < 1:
        raise ValueError("band_fission_min_size must be >= 1")
    if int(resolved["band_fusion_size_threshold"]) < 1:
        raise ValueError("band_fusion_size_threshold must be >= 1")
    if float(resolved["space_width"]) <= 0.0:
        raise ValueError("space_width must be > 0")
    if int(resolved["conflict_interval"]) < 0:
        raise ValueError("conflict_interval must be >= 0")
    if int(resolved["band_fission_interval"]) < 0:
        raise ValueError("band_fission_interval must be >= 0")
    if int(resolved["band_fusion_interval"]) < 0:
        raise ValueError("band_fusion_interval must be >= 0")

    for key in [
        "adult_survival_probability",
        "subadult_survival_probability",
        "elder_survival_probability",
        "base_juvenile_survival_probability",
        "female_reproduction_probability",
        "reputation_observation_prob",
        "helping_mutation_probability",
        "rare_helper_founder_probability",
        "reputation_update_weight",
        "group_migration_probability",
        "band_member_attraction",
        "band_territory_update_weight",
        "memory_smoothing",
        "social_learning_probability",
        "social_learning_rate",
        "child_rearing_survival_benefit",
        "juvenile_food_survival_benefit",
        "juvenile_no_food_survival_penalty",
        "spouse_bond_probability",
        "spouse_reciprocity_bond_probability",
        "spouse_reciprocity_bond_persistence_probability",
        "spouse_household_join_probability",
        "juvenile_household_attraction",
        "subadult_household_attraction",
        "adult_household_attraction",
        "elder_household_attraction",
        "household_residence_update_weight",
        "maturity_new_household_probability",
        "grass_initial_fraction",
        "territorial_avoidance_strength",
    ]:
        if not 0.0 <= float(resolved[key]) <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    for key in [
        "reputation_mate_preference",
        "group_bias", "group_mate_preference",
        "interband_marriage_preference",
        "norm_enforcement_strength",
        "kin_bias", "kin_mate_preference",
        "spatial_bias", "spatial_mate_preference",
        "reciprocity_weight", "leave_weight",
        "reciprocity_bond_persistence_probability",
        "social_learning_reputation_weight", "social_learning_success_weight",
        "territorial_overlap_start_fraction",
        "territorial_scarcity_threshold",
        "territorial_conflict_probability",
        "territorial_conflict_scarcity_weight",
    ]:
        if not 0.0 <= float(resolved[key]) <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    for key in [
        "cooperation_benefit_per_step", "helping_cost_per_step",
        "helping_reproduction_cost_scale", "reputation_threshold",
        "reputation_initial", "initial_adult_energy", "initial_juvenile_energy",
        "helping_mutation_stddev", "juvenile_metabolic_cost", "adult_metabolic_cost",
        "subadult_metabolic_cost", "elder_metabolic_cost", "juvenile_foraging_energy_gain",
        "subadult_foraging_energy_gain",
        "adult_foraging_energy_gain", "elder_foraging_energy_gain", "max_energy",
        "reproduction_energy_threshold", "reproduction_energy_cost", "child_energy",
        "rare_helper_trait_value", "helping_trait_invasion_threshold",
        "norm_violation_penalty", "norm_detection_sensitivity",
        "offspring_dispersal_std", "interaction_radius", "spatial_mate_radius",
        "band_territory_radius", "band_fission_dispersal_std",
        "band_fusion_distance", "interband_marriage_distance",
        "conflict_winner_bonus", "conflict_loser_penalty",
        "territorial_conflict_energy_penalty", "territorial_displacement_distance",
        "density_reproduction_pressure", "density_survival_pressure",
        "juvenile_movement_step_std", "subadult_movement_step_std", "adult_movement_step_std",
        "elder_movement_step_std", "reciprocity_bond_formation_radius",
        "reciprocity_bond_dissolution_radius",
        "spouse_mate_preference", "spouse_reciprocity_bond_radius",
        "initial_spouse_dispersal_std",
        "maturity_new_household_probability", "maturity_household_dispersal_std",
        "household_single_living_parent_survival_bonus",
        "household_two_living_parent_survival_bonus",
        "household_caregiver_survival_bonus_per_adult",
        "household_caregiver_survival_bonus_max",
        "parent_food_transfer_capacity", "parent_food_transfer_energy_reserve",
        "parent_food_transfer_radius", "parent_food_transfer_household_weight_bonus",
        "juvenile_food_survival_saturation",
        "child_rearing_radius", "child_rearing_care_capacity_per_helper",
        "child_rearing_cost_per_care", "child_rearing_helper_energy_reserve",
        "child_rearing_saturation", "child_rearing_baseline_weight",
        "child_rearing_parent_weight_bonus", "child_rearing_kin_weight_bonus",
        "child_rearing_household_member_weight_bonus",
        "child_rearing_spouse_parent_weight_bonus",
        "child_rearing_coparent_near_weight_bonus",
        "grass_max_per_cell", "grass_regrowth_per_step", "grass_harvest_radius",
        "social_learning_radius", "social_learning_max_adjustment",
    ]:
        if float(resolved[key]) < 0.0:
            raise ValueError(f"{key} must be >= 0")

    if (
        float(resolved["reciprocity_bond_dissolution_radius"])
        < float(resolved["reciprocity_bond_formation_radius"])
    ):
        raise ValueError(
            "reciprocity_bond_dissolution_radius must be >= "
            "reciprocity_bond_formation_radius"
        )
    if (
        float(resolved["household_two_living_parent_survival_bonus"])
        < float(resolved["household_single_living_parent_survival_bonus"])
    ):
        raise ValueError(
            "household_two_living_parent_survival_bonus must be >= "
            "household_single_living_parent_survival_bonus"
        )

    trait_min = float(resolved["initial_helping_trait_min"])
    trait_max = float(resolved["initial_helping_trait_max"])
    if not 0.0 <= trait_min <= trait_max <= 1.0:
        raise ValueError("initial_helping_trait bounds violated")
    inv_thresh = float(resolved["helping_trait_invasion_threshold"])
    rare_trait = float(resolved["rare_helper_trait_value"])
    if trait_max >= inv_thresh:
        raise ValueError("initial_helping_trait_max must be below helping_trait_invasion_threshold")
    if not trait_max < inv_thresh <= rare_trait <= 1.0:
        raise ValueError("invasion_threshold and rare_helper_trait_value bounds violated")

    if int(resolved["initial_adult_age_min"]) > int(resolved["initial_adult_age_max"]):
        raise ValueError("initial_adult_age_min must be <= initial_adult_age_max")
    if int(resolved["initial_adult_age_min"]) < int(resolved["adult_maturity_age"]):
        raise ValueError("initial_adult_age_min must be >= adult_maturity_age")
    child_max = int(resolved["initial_child_age_max"])
    if int(resolved["initial_child_age_min"]) > child_max:
        raise ValueError("initial_child_age_min must be <= initial_child_age_max")
    if child_max >= int(resolved["juvenile_dependency_age"]):
        raise ValueError("initial_child_age_max must be below juvenile_dependency_age")
    if int(resolved["female_min_reproduction_age"]) < int(resolved["adult_maturity_age"]):
        raise ValueError("female_min_reproduction_age must be >= adult_maturity_age")
    if int(resolved["male_min_reproduction_age"]) < int(resolved["adult_maturity_age"]):
        raise ValueError("male_min_reproduction_age must be >= adult_maturity_age")


config = dict(DEFAULT_CONFIG)
