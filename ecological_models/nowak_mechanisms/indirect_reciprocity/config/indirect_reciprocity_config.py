#!/usr/bin/env python3
"""Active parameters for the ecological indirect-reciprocity model."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_CONFIG: dict[str, Any] = {
    # Runtime and output.
    "random_seed": 0,
    "simulation_steps": 500,
    "write_latest_run": True,
    "data_dir": "ecological_models/nowak_mechanisms/indirect_reciprocity/data",
    # Initial population structure.
    # Well-mixed: no spatial coordinates, no group structure.
    "initial_founder_pairs": 64,
    "initial_children_per_pair": 3,
    "initial_adult_age_min": 8,
    "initial_adult_age_max": 18,
    "initial_child_age_min": 0,
    "initial_child_age_max": 3,
    "initial_adult_energy": 12.0,
    "initial_juvenile_energy": 4.0,
    # Helping trait (heritable).
    "initial_helping_trait_min": 0.0,
    "initial_helping_trait_max": 0.04,
    "rare_helper_founder_probability": 0.10,
    "rare_helper_trait_value": 0.65,
    "helping_trait_invasion_threshold": 0.10,
    "helping_mutation_probability": 0.20,
    "helping_mutation_stddev": 0.04,
    # -----------------------------------------------------------------------
    # Indirect reciprocity mechanism.
    # Cooperation evolves because public reputation makes past cooperative
    # behaviour visible to new partners. Donors observe a recipient's
    # reputation with probability q (reputation_observation_prob) and
    # help only if reputation >= reputation_threshold.
    # Nowak's condition: q > c/b.
    # With cooperation_benefit = 0.25 and helping_cost = 0.04: c/b = 0.16.
    # Default q = 0.70 >> 0.16, so the condition is well satisfied.
    #
    # Ecological channel: in addition to energy routing, public reputation
    # acts as a mate-quality signal. Females select males proportionally to
    # reputation (reputation_mate_preference = 1.0), so high-reputation
    # cooperators sire more offspring. This assortative genetic channel is
    # required for invasion from rare with blending inheritance; it mirrors
    # the spatial-placement assortment in the network reciprocity model.
    # -----------------------------------------------------------------------
    # Probability that a donor observes the recipient's reputation score
    # before deciding to help (Nowak's parameter q).
    # Must exceed c/b for cooperation to invade: q > helping_cost / cooperation_benefit.
    "reputation_observation_prob": 0.70,
    # Minimum reputation a recipient must have for the donor to help.
    # Acts as a discrimination gate: donors refuse to help low-reputation
    # individuals even if they observe their reputation.
    "reputation_threshold": 0.50,
    # Starting reputation for all individuals (founders and newborns).
    # Set to 0.65 (near cooperator steady state) so cooperators remain
    # above threshold during the initial reputation-build-up period.
    "reputation_initial": 0.65,
    # Exponential moving-average weight for reputation update each step.
    # new_rep = (1 - weight) * old_rep + weight * cooperation_rate_this_step
    # Slower update (0.10) prevents single-step misses from dropping
    # cooperators below threshold — required with one pairing per step.
    "reputation_update_weight": 0.10,
    # Ablation flag: if True, benefits are distributed to random adults
    # rather than to reputation-gated recipients.
    # Removes the discriminative routing that makes indirect reciprocity work.
    # Expected result: cooperation declines (defectors free-ride equally).
    "random_benefit_routing": False,
    # Strength of reputation-based mate preference [0, 1].
    # 1.0: males selected proportionally to reputation (full preference).
    # 0.0: random mate choice regardless of reputation.
    # Ecological channel: public reputation creates genetic assortment —
    # high-rep males sire more offspring, clustering cooperation in lineages.
    "reputation_mate_preference": 1.0,
    # -----------------------------------------------------------------------
    # Energy mechanics.
    "cooperation_benefit_per_step": 0.25,
    "helping_cost_per_step": 0.04,
    # Reproduction cost: effective_repr_prob = base * (1 - trait * scale).
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
    # Carrying capacity.
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
        "indirect_reciprocity_baseline",
        # Both channels active: reputation routes energy to cooperators AND
        # high-rep males are preferred as mates. Cooperation expected to invade.
        {},
    ),
    (
        "random_benefit_routing",
        # Energy channel ablated: benefits distributed randomly to any adult.
        # Reputation-based mate preference remains fully intact.
        # Tests whether the GENETIC channel (mate preference) alone is sufficient
        # to spread cooperation — expected to pass (Nowak energy routing is not
        # required when reputation-weighted mating creates genetic assortment).
        {"random_benefit_routing": True},
    ),
    (
        "no_mate_preference",
        # Genetic channel ablated: mate choice is random regardless of reputation.
        # Energy routing to high-rep cooperators remains intact.
        # Tests whether ENERGY routing alone is sufficient — expected to FAIL
        # (invasion from rare is impossible without assortative reproduction
        # in a well-mixed model with blending inheritance).
        {"reputation_mate_preference": 0.0},
    ),
    (
        "impossible_threshold",
        # Reputation threshold set to 0.99: no individual can sustain reputation
        # at or above this value, so eligible_count is always 0, reputation never
        # updates, and everyone keeps the initial reputation (0.65).
        # Effect: both channels broken simultaneously —
        #   energy routing: nobody meets threshold, no help given;
        #   mate preference: all males have identical reputation, mating is random.
        # Cleaner double-ablation than random_routing + no_mate_preference.
        {"reputation_threshold": 0.99},
    ),
    (
        "no_mate_preference_low_q",
        # Both channels weak: q = 0.05 (energy routing condition violated,
        # q << c/b = 0.10) AND no mate preference.
        # Reputation barely builds; neither channel is active.
        {"reputation_mate_preference": 0.0, "reputation_observation_prob": 0.05},
    ),
    (
        "cost_too_high",
        # Helping cost (0.20) overwhelms both channels: metabolic penalty
        # exceeds any energy advantage from reputation routing or extra offspring.
        # Cooperation must decline regardless of mechanism.
        {"helping_cost_per_step": 0.20},
    ),
    (
        "high_observation_prob",
        # q = 0.95: reputation observed almost always.
        # Both energy routing and mate-preference signal are maximally sharp;
        # reputation divergence is fastest, cooperation spreads strongest.
        {"reputation_observation_prob": 0.95},
    ),
    (
        "fast_reputation_update",
        # Reputation tracks helping behaviour very quickly (weight = 0.50).
        # Defectors detected and excluded faster; cooperators' reputations
        # build within a few steps and attract mates immediately.
        {"reputation_update_weight": 0.50},
    ),
    (
        "slow_reputation_update",
        # Reputation updates slowly (weight = 0.05).
        # Reputation signal is sluggish; discrimination is delayed.
        # Tests whether mechanism still works when reputation builds gradually.
        {"reputation_update_weight": 0.05},
    ),
    (
        "no_reproduction_cost",
        # Reproduction cost removed: cooperation trait carries no reproductive
        # penalty beyond metabolic cost.
        # Tests that reputation-based benefit (not cost removal) drives spread.
        {"helping_reproduction_cost_scale": 0.0},
    ),
]


def resolve_config(updates: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a validated config, accepting only canonical config keys."""
    resolved = dict(DEFAULT_CONFIG)
    if updates is not None:
        for key, value in updates.items():
            if key not in DEFAULT_CONFIG:
                raise KeyError(f"Unknown ecological indirect-reciprocity config key '{key}'")
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
        raise KeyError(f"Unknown ecological indirect-reciprocity scenario '{scenario_name}'")
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
        "reputation_observation_prob",
        "helping_mutation_probability",
        "rare_helper_founder_probability",
        "reputation_update_weight",
    ]
    for key in probabilities:
        value = float(resolved[key])
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{key} must be within [0, 1]")

    if not 0.0 <= float(resolved["reputation_mate_preference"]) <= 1.0:
        raise ValueError("reputation_mate_preference must be within [0, 1]")

    nonnegative = [
        "cooperation_benefit_per_step",
        "helping_cost_per_step",
        "helping_reproduction_cost_scale",
        "reputation_threshold",
        "reputation_initial",
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
