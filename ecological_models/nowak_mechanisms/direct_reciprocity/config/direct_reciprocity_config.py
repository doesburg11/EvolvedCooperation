#!/usr/bin/env python3
"""Active parameters for the ecological direct-reciprocity model."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    # Runtime and output.
    "random_seed": 0,
    "simulation_steps": 500,
    "write_latest_run": True,
    "data_dir": "ecological_models/nowak_mechanisms/direct_reciprocity/data",
    # Initial population structure.
    # Well-mixed: no spatial coordinates. Founders initialised flat.
    "initial_founder_pairs": 64,
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
    "rare_helper_founder_probability": 0.10,
    "rare_helper_trait_value": 0.65,
    "helping_trait_invasion_threshold": 0.10,
    "helping_mutation_probability": 0.20,
    "helping_mutation_stddev": 0.04,
    # -----------------------------------------------------------------------
    # Direct reciprocity mechanism.
    # Cooperation evolves through repeated dyadic encounters: partner fidelity
    # creates the opportunity for reciprocity; memory of partner cooperation
    # enables conditional strategies; differential dissolution lets cooperators
    # exit non-reciprocating partnerships.
    # -----------------------------------------------------------------------
    # Probability a partnership survives each step.
    # Mean partnership duration = 1 / (1 - partner_persistence_probability).
    # Default 0.92 → mean ~12.5 steps. Long enough for productive coop-coop
    # partnerships to accumulate energy advantage.
    "partner_persistence_probability": 0.92,
    # How strongly cooperation is conditioned on partner memory.
    # effective_coop = helping_trait * (1 - reciprocity_weight * (1 - partner_memory))
    # 0.0 = unconditional; 1.0 = full withholding when partner never cooperates.
    "reciprocity_weight": 0.70,
    # How strongly partner memory influences dissolution probability.
    # effective_persistence = base_persistence * (1 - leave_weight * (1 - partner_memory))
    # 0.0 = flat dissolution; positive = dissolve bad partnerships faster.
    "leave_weight": 0.60,
    # How fast partner memory updates (exponential moving average).
    # new_memory = (1 - smoothing) * old_memory + smoothing * partner_effective_coop
    # 0.20 = moderate tracking speed; low values make memory inertial.
    "memory_smoothing": 0.20,
    # Ablation flag: if True, partner_memory is frozen at 1.0 throughout.
    # This disables both conditional cooperation AND memory-based dissolution,
    # making all interactions unconditional. Expected result: cooperation declines
    # because cooperators cannot exit non-reciprocating partnerships.
    "memory_off": False,
    # Ablation flag: if True, partnerships are reassigned randomly each step.
    # Removes partner fidelity: no repeated encounters, no accumulated memory.
    # Expected result: cooperation declines because temporal assortment is gone.
    "random_partner_assignment": False,
    # -----------------------------------------------------------------------
    # Energy mechanics.
    # Total benefit delivered to partner per step per unit of effective cooperation.
    # Coop-coop pair net energy gain: trait * (benefit - cost) per step.
    # Must exceed cost for coop-coop partnership to be energetically viable.
    "cooperation_benefit_per_step": 0.22,
    # Energy cost paid each step by adults/elders per unit of helping_trait.
    # Paid regardless of whether a partnership interaction occurs.
    "helping_cost_per_step": 0.04,
    # Reproduction cost: effective_repr_prob = base * (1 - trait * scale).
    "helping_reproduction_cost_scale": 0.20,
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
    # Sexual reproduction (well-mixed: no spatial or group mating preference).
    "female_reproduction_probability": 0.35,
    "female_min_reproduction_age": 6,
    "female_max_reproduction_age": 45,
    "male_min_reproduction_age": 6,
    "male_max_reproduction_age": 55,
    "reproduction_energy_threshold": 7.0,
    "reproduction_energy_cost": 1.0,
    "child_energy": 3.5,
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
        "direct_reciprocity_baseline",
        {},
    ),
    (
        "memory_off",
        # All memory mechanisms disabled: cooperation is unconditional and
        # dissolution is flat. Without partner assortment, cooperators cannot
        # preferentially stay with other cooperators.
        # Expected to show reduced or absent cooperation spread.
        {"memory_off": True},
    ),
    (
        "random_partners",
        # Partners reshuffled every step: no repeated encounters, no history.
        # Cooperation cannot be sustained reciprocally in dyadic pairs.
        # Primary mechanism-off test: partner fidelity is load-bearing.
        {"random_partner_assignment": True},
    ),
    (
        "no_direct_reciprocity",
        # Both partner fidelity removed AND memory disabled.
        # Complete ablation of all direct-reciprocity features.
        {"random_partner_assignment": True, "memory_off": True},
    ),
    (
        "cost_too_high",
        # Helping cost so large that cooperators drain energy faster than they
        # gain from partnerships. Cooperation must decline regardless of mechanism.
        {"helping_cost_per_step": 0.20},
    ),
    (
        "long_partnerships",
        # Moderately high persistence: partnerships last ~25 steps on average.
        # Amplifies mechanism: coop-coop pairs accumulate substantially more
        # energy surplus. Very high persistence (0.99) HURTS cooperation because
        # cooperators cannot escape non-reciprocating partners fast enough —
        # the high base persistence overwhelms the differential-dissolution signal.
        # This reveals an optimal range for partnership duration.
        {"partner_persistence_probability": 0.97},
    ),
    (
        "short_partnerships",
        # Low persistence: partnerships last ~3 steps on average.
        # Weakens the mechanism; may still work if leave_weight is intact.
        {"partner_persistence_probability": 0.65},
    ),
    (
        "high_reciprocity_weight",
        # Strong conditional response: almost no cooperation with defectors.
        # Maximises protection from exploitation while in a bad partnership.
        {"reciprocity_weight": 0.95},
    ),
    (
        "strong_leave_weight",
        # Rapid dissolution of bad partnerships: exit defector pairs in ~1 step.
        # Cooperators rapidly filter through partners to find other cooperators.
        {"leave_weight": 0.90},
    ),
    (
        "no_reproduction_cost",
        # Reproduction cost removed: cooperators reproduce at the same base rate
        # as non-cooperators, removing one selective disadvantage.
        # Tests whether partnership dynamics alone (not cost-of-being-cooperative)
        # are sufficient to spread cooperation — they are.
        # High benefit (cooperation_benefit_per_step = 0.40) does NOT amplify
        # the mechanism: it amplifies defector exploitation of cooperators
        # more than it amplifies mutual coop-coop benefit, because rare cooperators
        # are initially paired mostly with defectors.
        {"helping_reproduction_cost_scale": 0.0},
    ),
]


def resolve_config(updates: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a validated config, accepting only canonical config keys."""
    resolved = dict(DEFAULT_CONFIG)
    if updates is not None:
        for key, value in updates.items():
            if key not in DEFAULT_CONFIG:
                raise KeyError(f"Unknown ecological direct-reciprocity config key '{key}'")
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
        raise KeyError(f"Unknown ecological direct-reciprocity scenario '{scenario_name}'")
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

    probabilities = [
        "adult_survival_probability",
        "elder_survival_probability",
        "base_juvenile_survival_probability",
        "female_reproduction_probability",
        "partner_persistence_probability",
        "helping_mutation_probability",
        "rare_helper_founder_probability",
    ]
    for key in probabilities:
        value = float(resolved[key])
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    nonnegative = [
        "cooperation_benefit_per_step",
        "helping_cost_per_step",
        "helping_reproduction_cost_scale",
        "reciprocity_weight",
        "leave_weight",
        "memory_smoothing",
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
