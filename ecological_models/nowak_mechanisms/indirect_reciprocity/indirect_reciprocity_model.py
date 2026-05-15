#!/usr/bin/env python3
"""
Ecological indirect-reciprocity model with public reputation and reputation-gated help.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_model

Mechanism: cooperation evolves because public reputation makes past cooperative
behaviour visible to new partners. Each step, randomly formed donor-recipient pairs
interact: a donor observes the recipient's reputation with probability q and helps
only if reputation >= reputation_threshold. Helping raises the donor's reputation
(observed by the population). High-reputation individuals receive more help, gain
more energy, and reproduce more. Defectors who never help accrue low reputation and
are denied help by all observers.

Nowak's condition: q > c/b.
With defaults (benefit = 0.25, cost = 0.04): c/b = 0.16; q = 0.70 >> 0.16.

The model is fully well-mixed: no spatial coordinates, no group membership, no
kinship structure. The only asymmetric structure is the reputation score — a public,
dynamically updated signal that discriminates cooperators from defectors.

Key distinctions from direct reciprocity:
- Reputation is PUBLIC: all individuals use it, not just a fixed pair.
- No partner fidelity required: new random pairings each step are fine because
  reputation accumulates across many interactions.
- Third-party observation drives cooperation: I help you because your reputation
  tells me you are cooperative, not because you helped me personally.

Key diagnostic: mean_reputation — population mean reputation of adults.
High mean_reputation means most adults are cooperating and being rewarded.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np


if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_model'."
    )

from .config.indirect_reciprocity_config import DEFAULT_CONFIG
from .config.indirect_reciprocity_config import config as active_config
from .config.indirect_reciprocity_config import resolve_config

DEFAULT_STEPS = int(DEFAULT_CONFIG["simulation_steps"])

SEX_FEMALE = "F"
SEX_MALE = "M"
STAGE_JUVENILE = "juvenile"
STAGE_ADULT = "adult"
STAGE_ELDER = "elder"


@dataclass
class Individual:
    id: int
    sex: str
    age: int
    stage: str
    energy: float
    helping_trait: float
    # Public reputation score in [0, 1]. NOT inherited; starts at reputation_initial
    # for all founders and newborns. Updated each step from observed helping behaviour.
    reputation: float
    mother_id: int | None
    father_id: int | None
    born_step: int


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


class EcologicalIndirectReciprocityModel:
    """
    Population model where public reputation drives the spread of cooperation.

    Cooperators pay a per-step energy cost. Donors observe recipients' reputations
    with probability q and help only high-reputation individuals. Helping raises
    the donor's own reputation, making them a preferred recipient for future donors.
    Defectors accrue low reputation and are gradually excluded from receiving help.

    Indirect reciprocity is the only force creating positive assortment — no spatial
    structure, no groups, no kinship. The reputation channel discriminates cooperators
    from defectors across the entire well-mixed population simultaneously.
    """

    def __init__(self, run_config: Mapping[str, Any]):
        self.config = resolve_config(run_config)
        self.rng = np.random.default_rng(self.config["random_seed"])
        self.individuals: list[Individual] = []
        self.next_id = 0
        self.step_index = 0
        self.history: dict[str, list[Any]] = defaultdict(list)
        self.offspring_counts: dict[int, int] = {}
        self.birth_helping_traits: dict[int, float] = {}
        self.initial_mean_helping_trait = 0.0
        self._initialize_population()
        self.initial_mean_helping_trait = self._mean_helping_trait()
        self._record_history(births=0, deaths=0)

    def _initialize_population(self) -> None:
        pairs = int(self.config["initial_founder_pairs"])
        children_per_pair = int(self.config["initial_children_per_pair"])
        for _ in range(pairs):
            mother = self._create_founder(SEX_FEMALE)
            father = self._create_founder(SEX_MALE)
            self.individuals.extend([mother, father])
            for _ in range(children_per_pair):
                child = self._create_child(mother, father, initial_child=True)
                self.individuals.append(child)

    def _create_founder(self, sex: str) -> Individual:
        age = int(
            self.rng.integers(
                int(self.config["initial_adult_age_min"]),
                int(self.config["initial_adult_age_max"]) + 1,
            )
        )
        return Individual(
            id=self._take_id(),
            sex=sex,
            age=age,
            stage=self._stage_for_age(age),
            energy=float(self.config["initial_adult_energy"]),
            helping_trait=self._sample_initial_helping_trait(),
            reputation=float(self.config["reputation_initial"]),
            mother_id=None,
            father_id=None,
            born_step=0,
        )

    def _create_child(
        self,
        mother: Individual,
        father: Individual,
        *,
        initial_child: bool,
    ) -> Individual:
        if initial_child:
            age = int(
                self.rng.integers(
                    int(self.config["initial_child_age_min"]),
                    int(self.config["initial_child_age_max"]) + 1,
                )
            )
            energy = float(self.config["initial_juvenile_energy"])
        else:
            age = 0
            energy = float(self.config["child_energy"])

        helping_trait = 0.5 * (mother.helping_trait + father.helping_trait)
        if self.rng.random() < float(self.config["helping_mutation_probability"]):
            helping_trait += float(
                self.rng.normal(0.0, float(self.config["helping_mutation_stddev"]))
            )

        child = Individual(
            id=self._take_id(),
            sex=self._random_sex(),
            age=age,
            stage=self._stage_for_age(age),
            energy=energy,
            helping_trait=clamp01(helping_trait),
            # Reputation is not inherited; offspring start at the default.
            reputation=float(self.config["reputation_initial"]),
            mother_id=mother.id,
            father_id=father.id,
            born_step=self.step_index,
        )
        self._register_birth(child)
        return child

    def _take_id(self) -> int:
        next_id = self.next_id
        self.next_id += 1
        return next_id

    def _register_birth(self, individual: Individual) -> None:
        self.offspring_counts[individual.id] = 0
        self.birth_helping_traits[individual.id] = individual.helping_trait

    def _sample_initial_helping_trait(self) -> float:
        if self.rng.random() < float(self.config["rare_helper_founder_probability"]):
            return float(self.config["rare_helper_trait_value"])
        return float(
            self.rng.uniform(
                float(self.config["initial_helping_trait_min"]),
                float(self.config["initial_helping_trait_max"]),
            )
        )

    def _random_sex(self) -> str:
        return SEX_FEMALE if self.rng.random() < 0.5 else SEX_MALE

    def _stage_for_age(self, age: int) -> str:
        if age < int(self.config["juvenile_maturity_age"]):
            return STAGE_JUVENILE
        if age >= int(self.config["elder_age"]):
            return STAGE_ELDER
        return STAGE_ADULT

    def step(self) -> None:
        self.step_index += 1
        self._age_and_budget()
        self._conduct_interactions()
        deaths = self._apply_survival()
        reproduction_stats = self._reproduce()
        deaths += self._apply_density_mortality()
        self._record_history(births=reproduction_stats["births"], deaths=deaths)

    def _age_and_budget(self) -> None:
        cost_per_step = float(self.config["helping_cost_per_step"])
        for ind in self.individuals:
            ind.age += 1
            ind.stage = self._stage_for_age(ind.age)
            if ind.stage == STAGE_JUVENILE:
                ind.energy += float(self.config["juvenile_foraging_energy_gain"])
                ind.energy -= float(self.config["juvenile_metabolic_cost"])
            elif ind.stage == STAGE_ADULT:
                ind.energy += float(self.config["adult_foraging_energy_gain"])
                ind.energy -= float(self.config["adult_metabolic_cost"])
                ind.energy -= ind.helping_trait * cost_per_step
            else:
                ind.energy += float(self.config["elder_foraging_energy_gain"])
                ind.energy -= float(self.config["elder_metabolic_cost"])
                ind.energy -= ind.helping_trait * cost_per_step
            ind.energy = min(ind.energy, float(self.config["max_energy"]))

    def _conduct_interactions(self) -> None:
        """Reputation-gated pairwise interactions among adults and elders.

        Each adult-or-elder is both a donor and a recipient in one random
        pairing per step. Donors observe recipient reputation with probability q
        and help only if reputation >= threshold. Reputation is updated from
        each individual's per-step cooperation rate.

        With random_benefit_routing=True: benefits are distributed randomly to
        adults regardless of reputation (mechanism-off ablation).
        """
        q = float(self.config["reputation_observation_prob"])
        threshold = float(self.config["reputation_threshold"])
        benefit = float(self.config["cooperation_benefit_per_step"])
        update_weight = float(self.config["reputation_update_weight"])
        max_energy = float(self.config["max_energy"])
        random_routing = bool(self.config["random_benefit_routing"])

        active = [
            ind for ind in self.individuals
            if ind.stage in {STAGE_ADULT, STAGE_ELDER}
        ]
        if len(active) < 2:
            return

        # Shuffle and form consecutive pairs.
        indices = list(range(len(active)))
        self.rng.shuffle(indices)

        # Track per-step helping for reputation update.
        # eligible_count: times donor observed a recipient AND recipient was above threshold.
        # help_count: times donor actually helped given eligible opportunity.
        # Reputation = rolling mean of (help_count / eligible_count), which converges
        # to helping_trait (not to q * helping_trait).  This ensures cooperators'
        # steady-state reputation exceeds the threshold, making the mechanism viable.
        help_count = {ind.id: 0 for ind in active}
        eligible_count = {ind.id: 0 for ind in active}
        # For random_routing ablation: track raw decision rate for reputation.
        raw_help_count = {ind.id: 0 for ind in active}
        raw_interact_count = {ind.id: 0 for ind in active}

        if random_routing:
            # Ablation: distribute benefits randomly; reputation still updates
            # from raw helping decisions so the signal remains intact.
            for donor in active:
                raw_interact_count[donor.id] += 1
                if self.rng.random() < donor.helping_trait:
                    # Pick random recipient other than self.
                    idx = int(self.rng.integers(0, len(active)))
                    recipient = active[idx]
                    if recipient.id == donor.id and len(active) > 1:
                        idx = (idx + 1) % len(active)
                        recipient = active[idx]
                    recipient.energy = min(max_energy, recipient.energy + benefit)
                    raw_help_count[donor.id] += 1
        else:
            # Normal: reputation-gated pairwise interactions.
            for i in range(0, len(indices) - 1, 2):
                a = active[indices[i]]
                b = active[indices[i + 1]]
                # A-as-donor -> B-as-recipient
                if self.rng.random() < q:          # A observes B's reputation
                    if b.reputation >= threshold:
                        eligible_count[a.id] += 1   # only eligible if recipient above threshold
                        if self.rng.random() < a.helping_trait:
                            b.energy = min(max_energy, b.energy + benefit)
                            help_count[a.id] += 1
                # B-as-donor -> A-as-recipient
                if self.rng.random() < q:          # B observes A's reputation
                    if a.reputation >= threshold:
                        eligible_count[b.id] += 1   # only eligible if recipient above threshold
                        if self.rng.random() < b.helping_trait:
                            a.energy = min(max_energy, a.energy + benefit)
                            help_count[b.id] += 1

        # Update reputations.
        for ind in active:
            if random_routing:
                n = raw_interact_count.get(ind.id, 0)
                if n > 0:
                    rate = raw_help_count[ind.id] / n
                    ind.reputation = clamp01(
                        (1.0 - update_weight) * ind.reputation + update_weight * rate
                    )
            else:
                n = eligible_count.get(ind.id, 0)
                if n > 0:
                    # Conditional rate: P(help | observed AND recipient above threshold).
                    # Converges to helping_trait, allowing threshold-based discrimination.
                    rate = help_count[ind.id] / n
                    ind.reputation = clamp01(
                        (1.0 - update_weight) * ind.reputation + update_weight * rate
                    )

    def _apply_survival(self) -> int:
        adult_surv = float(self.config["adult_survival_probability"])
        elder_surv = float(self.config["elder_survival_probability"])
        juv_base_surv = float(self.config["base_juvenile_survival_probability"])
        max_age = int(self.config["max_age"])

        survivors = []
        deaths = 0
        for ind in self.individuals:
            if ind.age >= max_age or ind.energy <= 0.0:
                deaths += 1
                continue
            if ind.stage == STAGE_JUVENILE:
                if self.rng.random() > juv_base_surv:
                    deaths += 1
                    continue
            elif ind.stage == STAGE_ADULT:
                if self.rng.random() > adult_surv:
                    deaths += 1
                    continue
            else:
                if self.rng.random() > elder_surv:
                    deaths += 1
                    continue
            survivors.append(ind)

        self.individuals = survivors
        return deaths

    def _reproduce(self) -> dict[str, int]:
        female_min = int(self.config["female_min_reproduction_age"])
        female_max = int(self.config["female_max_reproduction_age"])
        male_min = int(self.config["male_min_reproduction_age"])
        male_max = int(self.config["male_max_reproduction_age"])
        repr_prob = float(self.config["female_reproduction_probability"])
        energy_threshold = float(self.config["reproduction_energy_threshold"])
        energy_cost = float(self.config["reproduction_energy_cost"])
        repr_cost_scale = float(self.config["helping_reproduction_cost_scale"])

        eligible_males = [
            ind for ind in self.individuals
            if ind.sex == SEX_MALE
            and male_min <= ind.age <= male_max
            and ind.energy >= energy_threshold
        ]
        # Precompute reputation-weighted male selection probabilities once per step.
        # Females prefer males with higher reputation — the ecological channel through
        # which public reputation creates genetic assortment for cooperation.
        mate_pref_strength = float(self.config["reputation_mate_preference"])
        if eligible_males and mate_pref_strength > 0.0:
            weights = np.array([
                m.reputation * mate_pref_strength + (1.0 - mate_pref_strength)
                for m in eligible_males
            ], dtype=float)
            total = weights.sum()
            if total > 0:
                mate_weights: np.ndarray | None = weights / total
            else:
                mate_weights = None
        else:
            mate_weights = None

        new_children: list[Individual] = []
        births = 0
        for mother in self.individuals:
            if mother.sex != SEX_FEMALE:
                continue
            if not (female_min <= mother.age <= female_max):
                continue
            if mother.energy < energy_threshold:
                continue
            effective_prob = repr_prob * (1.0 - mother.helping_trait * repr_cost_scale)
            if self.rng.random() > effective_prob:
                continue
            if not eligible_males:
                continue
            if mate_weights is not None:
                father_idx = int(self.rng.choice(len(eligible_males), p=mate_weights))
                father = eligible_males[father_idx]
            else:
                father = eligible_males[int(self.rng.integers(0, len(eligible_males)))]
            mother.energy -= energy_cost
            child = self._create_child(mother, father, initial_child=False)
            new_children.append(child)
            births += 1
            if mother.id in self.offspring_counts:
                self.offspring_counts[mother.id] += 1
            if father.id in self.offspring_counts:
                self.offspring_counts[father.id] += 1

        self.individuals.extend(new_children)
        return {"births": births}

    def _apply_density_mortality(self) -> int:
        max_pop = int(self.config["max_population"])
        if len(self.individuals) <= max_pop:
            return 0
        excess = len(self.individuals) - max_pop
        indices = self.rng.choice(len(self.individuals), size=excess, replace=False)
        keep = set(range(len(self.individuals))) - set(indices)
        self.individuals = [self.individuals[i] for i in sorted(keep)]
        return excess

    def _mean_helping_trait(self) -> float:
        if not self.individuals:
            return 0.0
        return float(np.mean([ind.helping_trait for ind in self.individuals]))

    def _compute_metrics(self) -> dict[str, float]:
        adults = [
            ind for ind in self.individuals
            if ind.stage in {STAGE_ADULT, STAGE_ELDER}
        ]
        if not adults:
            return {
                "mean_helping_trait": 0.0,
                "mean_reputation": 0.0,
                "helping_invasion_frequency": 0.0,
            }

        threshold = float(self.config["helping_trait_invasion_threshold"])
        traits = [ind.helping_trait for ind in self.individuals]
        reputations = [ind.reputation for ind in adults]

        return {
            "mean_helping_trait": float(np.mean(traits)),
            "mean_reputation": float(np.mean(reputations)),
            "helping_invasion_frequency": float(
                np.mean([t >= threshold for t in traits])
            ),
        }

    def _record_history(self, *, births: int, deaths: int) -> None:
        metrics = self._compute_metrics()
        self.history["step"].append(self.step_index)
        self.history["population"].append(len(self.individuals))
        self.history["births"].append(births)
        self.history["deaths"].append(deaths)
        for key, value in metrics.items():
            self.history[key].append(value)

    def summary(self) -> dict[str, Any]:
        initial_mean = self.initial_mean_helping_trait
        final_mean = (
            self.history["mean_helping_trait"][-1]
            if self.history["mean_helping_trait"]
            else 0.0
        )
        initial_inv = (
            self.history["helping_invasion_frequency"][0]
            if self.history["helping_invasion_frequency"]
            else 0.0
        )
        final_inv = (
            self.history["helping_invasion_frequency"][-1]
            if self.history["helping_invasion_frequency"]
            else 0.0
        )
        return {
            "helping_trait_change": final_mean - initial_mean,
            "helping_invasion_frequency_change": final_inv - initial_inv,
            "final_population": len(self.individuals),
            "latest_mean_reputation": (
                self.history["mean_reputation"][-1]
                if self.history["mean_reputation"]
                else 0.0
            ),
        }


def run_simulation(run_config: Mapping[str, Any]) -> dict[str, Any]:
    model = EcologicalIndirectReciprocityModel(run_config)
    steps = int(run_config.get("simulation_steps", DEFAULT_STEPS))
    for _ in range(steps):
        model.step()
    payload: dict[str, Any] = {
        "config": dict(run_config),
        "history": dict(model.history),
        "summary": model.summary(),
    }
    if bool(run_config.get("write_latest_run", False)):
        _write_latest_run(payload, str(run_config.get("data_dir", ".")))
    return payload


def _write_latest_run(payload: dict[str, Any], data_dir: str) -> None:
    path = Path(data_dir) / "latest_run.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def main() -> None:
    model = EcologicalIndirectReciprocityModel(active_config)
    steps = int(active_config["simulation_steps"])
    for i in range(steps):
        model.step()
        if (i + 1) % 100 == 0:
            s = model.summary()
            print(
                f"step {i + 1:4d}  pop={len(model.individuals):4d}"
                f"  trait={s['helping_trait_change']:+.4f}"
                f"  inv={s['helping_invasion_frequency_change']:+.4f}"
                f"  rep={s['latest_mean_reputation']:.3f}"
            )
    payload = {
        "config": active_config,
        "history": dict(model.history),
        "summary": model.summary(),
    }
    if bool(active_config.get("write_latest_run", True)):
        _write_latest_run(payload, str(active_config.get("data_dir", ".")))
    s = model.summary()
    print(
        f"\nfinal: trait_Δ={s['helping_trait_change']:+.4f}"
        f"  inv_Δ={s['helping_invasion_frequency_change']:+.4f}"
        f"  pop={s['final_population']}"
        f"  rep={s['latest_mean_reputation']:.3f}"
    )


if __name__ == "__main__":
    main()
