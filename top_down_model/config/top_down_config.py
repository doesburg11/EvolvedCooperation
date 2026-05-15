#!/usr/bin/env python3
"""Active parameters for the top-down cooperation model."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    # Runtime and output.
    "random_seed": 0,
    "simulation_steps": 500,
    "write_latest_run": True,
    "data_dir": "top_down_model/data",
    # Initial population structure.
    "initial_founder_pairs": 64,
    "initial_children_per_pair": 3,
    "initial_adult_age_min": 8,
    "initial_adult_age_max": 18,
    "initial_child_age_min": 0,
    "initial_child_age_max": 3,
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
    # Capacity 3: Group identity (group selection).
    # Heritable group membership biases both interaction routing (group_bias)
    # and mate choice (group_mate_preference). Inter-group conflict transfers
    # energy from less-cooperative to more-cooperative groups every
    # conflict_interval steps.
    # Ablation (identity only): group_bias=0, group_mate_preference=0.
    # Ablation (conflict only): conflict_interval=0.
    # Full ablation: all three to 0.
    # -----------------------------------------------------------------------
    "n_groups": 4,
    "group_migration_probability": 0.05,
    "group_bias": 0.30,
    "group_mate_preference": 0.30,
    "conflict_interval": 20,
    "conflict_winner_bonus": 0.80,
    "conflict_loser_penalty": 0.40,
    # -----------------------------------------------------------------------
    # Capacity 4: Kin recognition (kin selection).
    # Agents preferentially route interactions toward kin (siblings, parents,
    # offspring — individuals sharing a parent). kin_mate_preference gives a
    # weight bonus to kin males during reproduction.
    # Kin clusters form naturally through pedigree over generations.
    # Ablation: kin_bias=0, kin_mate_preference=0.
    # -----------------------------------------------------------------------
    "kin_bias": 0.30,
    "kin_mate_preference": 0.40,
    # -----------------------------------------------------------------------
    # Capacity 5: Spatial awareness (network reciprocity).
    # Agents have heritable spatial coordinates. Offspring are placed near their
    # mother (dispersal_std controls spread). Interactions can be biased toward
    # spatial neighbors (spatial_bias), and males within spatial_mate_radius
    # receive a mate-choice weight bonus (spatial_mate_preference).
    # Ablation: spatial_bias=0, spatial_mate_preference=0.
    # -----------------------------------------------------------------------
    "space_width": 100.0,
    "offspring_dispersal_std": 8.0,
    "interaction_radius": 15.0,
    "spatial_bias": 0.30,
    "spatial_mate_radius": 20.0,
    "spatial_mate_preference": 0.50,
    # -----------------------------------------------------------------------
    # Capacity 6: Partner fidelity (direct reciprocity).
    # Adults form stable dyadic partnerships. Partners interact preferentially
    # over strangers. Conditional cooperation (reciprocity_weight) reduces
    # cooperation toward non-reciprocating partners. Differential dissolution
    # (leave_weight) increases dissolution probability when partner_memory is low.
    # Ablation: partner_persistence_probability=0 (all partnerships dissolve
    # immediately, no partner fidelity).
    # -----------------------------------------------------------------------
    "partner_persistence_probability": 0.85,
    "reciprocity_weight": 0.60,
    "leave_weight": 0.50,
    "memory_smoothing": 0.20,
    # -----------------------------------------------------------------------
    # Energy mechanics.
    "cooperation_benefit_per_step": 0.25,
    "helping_cost_per_step": 0.04,
    "helping_reproduction_cost_scale": 0.10,
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
    # Carrying capacity.
    "max_population": 400,
    # -----------------------------------------------------------------------
    # Proof-of-mechanism thresholds.
    "proof_success_min_trait_increase": 0.010,
    "proof_success_min_invasion_frequency_increase": 0.02,
    "proof_success_min_final_population": 50,
}


PROOF_SEEDS = [0, 1, 2, 3, 4]

# Ablation helpers (repeated sets of keys for clean scenario definitions).
_REP_OFF = {"reputation_mate_preference": 0.0, "random_benefit_routing": True}
_NORM_OFF = {"norm_enforcement_strength": 0.0}
_GROUP_OFF = {"group_bias": 0.0, "group_mate_preference": 0.0, "conflict_interval": 0}
_KIN_OFF = {"kin_bias": 0.0, "kin_mate_preference": 0.0}
_SPATIAL_OFF = {"spatial_bias": 0.0, "spatial_mate_preference": 0.0}
_DR_OFF = {"partner_persistence_probability": 0.0}


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
        "top_down_baseline",
        # All six capacities active. Cooperation expected to invade strongly.
        {},
    ),
    (
        "no_norm_enforcement",
        # Norm enforcement off; all other capacities active.
        _NORM_OFF,
    ),
    (
        "no_direct_reciprocity",
        # Partnerships dissolve immediately (no partner fidelity).
        # All other capacities remain active.
        _DR_OFF,
    ),
    (
        "no_kin_selection",
        # Kin routing and kin mate preference off.
        _KIN_OFF,
    ),
    (
        "no_network_reciprocity",
        # Spatial routing and spatial mate preference off.
        _SPATIAL_OFF,
    ),
    (
        "no_group_conflict",
        # Inter-group conflict off (conflict_interval=0); group identity
        # (routing + mate preference) remains active.
        {"conflict_interval": 0},
    ),
    # ------------------------------------------------------------------
    # Single-mechanism scenarios (each capacity alone).
    # ------------------------------------------------------------------
    (
        "reputation_only",
        # Only reputation sensitivity active (indirect reciprocity baseline).
        # Mirrors the ecological indirect-reciprocity model.
        _merge(_NORM_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF),
    ),
    (
        "kin_selection_only",
        # Only kin routing and kin mate preference active.
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _SPATIAL_OFF, _DR_OFF),
    ),
    (
        "network_reciprocity_only",
        # Only spatial routing and spatial mate preference active.
        # At combined-model parameters (spatial_bias=0.30, spatial_mate_pref=0.50),
        # spatial clustering alone is insufficient for invasion from rare.
        # Prediction: cooperation stays flat or declines (inverted).
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _KIN_OFF, _DR_OFF),
    ),
    (
        "group_selection_only",
        # Only group identity + conflict active.
        # At combined-model parameters (group_bias=0.30, group_mate_pref=0.30),
        # group identity alone is insufficient for invasion from rare.
        # Prediction: cooperation stays flat or declines (inverted).
        _merge(_REP_OFF, _NORM_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF),
    ),
    (
        "direct_reciprocity_only",
        # Only partner fidelity active. No genetic reproductive assortment channel.
        # Mirrors the ecological direct-reciprocity model (too weak to invade alone).
        # Prediction: cooperation stays flat or declines (inverted).
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF),
    ),
    (
        "strong_all_channels",
        # All capacities amplified.
        {
            "norm_enforcement_strength": 1.0,
            "group_bias": 0.60,
            "group_mate_preference": 0.60,
            "conflict_winner_bonus": 1.50,
            "kin_bias": 0.60,
            "kin_mate_preference": 0.80,
            "spatial_bias": 0.60,
            "spatial_mate_preference": 0.90,
            "partner_persistence_probability": 0.92,
        },
    ),
    # ------------------------------------------------------------------
    # Inverted scenarios (cooperation expected to stay flat or decline).
    # ------------------------------------------------------------------
    (
        "norm_enforcement_only",
        # Only norm enforcement active: energy pressure on defectors but no
        # genetic reproductive assortment channel. Bottom-up prediction: decline.
        _merge(_REP_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF),
    ),
    (
        "all_capacities_off",
        # Every capacity ablated. Pure demographic baseline.
        _merge(_REP_OFF, _NORM_OFF, _GROUP_OFF, _KIN_OFF, _SPATIAL_OFF, _DR_OFF),
    ),
    (
        "cost_too_high",
        # Helping cost (0.40) overwhelms all channels — cooperators lose net energy
        # even with full foraging (0.32 foraging − 0.12 metabolic − 0.40×trait > 0
        # only for trait < 0.50). The combined model cannot compensate.
        # Prediction: cooperation declines (inverted control).
        {"helping_cost_per_step": 0.40},
    ),
]


def resolve_config(updates: Mapping[str, Any] | None = None) -> dict[str, Any]:
    resolved = dict(DEFAULT_CONFIG)
    if updates is not None:
        for key, value in updates.items():
            if key not in DEFAULT_CONFIG:
                raise KeyError(f"Unknown top-down config key '{key}'")
            resolved[key] = value
    _validate_config(resolved)
    return resolved


def resolve_scenario_config(scenario_name: str, seed: int) -> dict[str, Any]:
    scenario_updates = None
    for candidate_name, updates in PROOF_SCENARIOS:
        if candidate_name == scenario_name:
            scenario_updates = updates
            break
    if scenario_updates is None:
        raise KeyError(f"Unknown top-down scenario '{scenario_name}'")
    merged = dict(DEFAULT_CONFIG)
    merged.update(scenario_updates)
    merged["random_seed"] = seed
    merged["write_latest_run"] = False
    return resolve_config(merged)


def _validate_config(resolved: Mapping[str, Any]) -> None:
    if int(resolved["simulation_steps"]) < 1:
        raise ValueError("simulation_steps must be >= 1")
    if int(resolved["initial_founder_pairs"]) < 1:
        raise ValueError("initial_founder_pairs must be >= 1")
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
    if int(resolved["n_groups"]) < 1:
        raise ValueError("n_groups must be >= 1")
    if float(resolved["space_width"]) <= 0.0:
        raise ValueError("space_width must be > 0")
    if int(resolved["conflict_interval"]) < 0:
        raise ValueError("conflict_interval must be >= 0")

    for key in [
        "adult_survival_probability",
        "elder_survival_probability",
        "base_juvenile_survival_probability",
        "female_reproduction_probability",
        "reputation_observation_prob",
        "helping_mutation_probability",
        "rare_helper_founder_probability",
        "reputation_update_weight",
        "group_migration_probability",
        "memory_smoothing",
    ]:
        if not 0.0 <= float(resolved[key]) <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    for key in [
        "reputation_mate_preference",
        "group_bias", "group_mate_preference",
        "norm_enforcement_strength",
        "kin_bias", "kin_mate_preference",
        "spatial_bias", "spatial_mate_preference",
        "reciprocity_weight", "leave_weight",
        "partner_persistence_probability",
    ]:
        if not 0.0 <= float(resolved[key]) <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    for key in [
        "cooperation_benefit_per_step", "helping_cost_per_step",
        "helping_reproduction_cost_scale", "reputation_threshold",
        "reputation_initial", "initial_adult_energy", "initial_juvenile_energy",
        "helping_mutation_stddev", "juvenile_metabolic_cost", "adult_metabolic_cost",
        "elder_metabolic_cost", "juvenile_foraging_energy_gain",
        "adult_foraging_energy_gain", "elder_foraging_energy_gain", "max_energy",
        "reproduction_energy_threshold", "reproduction_energy_cost", "child_energy",
        "rare_helper_trait_value", "helping_trait_invasion_threshold",
        "norm_violation_penalty", "norm_detection_sensitivity",
        "offspring_dispersal_std", "interaction_radius", "spatial_mate_radius",
        "conflict_winner_bonus", "conflict_loser_penalty",
    ]:
        if float(resolved[key]) < 0.0:
            raise ValueError(f"{key} must be >= 0")

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
    child_max = int(resolved["initial_child_age_max"])
    if int(resolved["initial_child_age_min"]) > child_max:
        raise ValueError("initial_child_age_min must be <= initial_child_age_max")
    if child_max >= int(resolved["juvenile_maturity_age"]):
        raise ValueError("initial_child_age_max must be below juvenile_maturity_age")


config = dict(DEFAULT_CONFIG)
