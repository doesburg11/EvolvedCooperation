#!/usr/bin/env python3
"""
Ecological direct-reciprocity model with dyadic partnerships and partner memory.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.direct_reciprocity.direct_reciprocity_model

Mechanism: cooperation evolves through repeated dyadic encounters. Partner
fidelity creates temporal assortment — stable partnerships persist across many
steps. Memory of partner cooperation enables conditional strategies: cooperators
reduce cooperation toward non-reciprocating partners (reciprocity_weight) and
dissolve those partnerships faster (leave_weight). Together, cooperators filter
through short-lived bad partnerships and maintain long, mutually beneficial ones.

The ecological analog of Nowak's direct-reciprocity condition w > cost_threshold:
cooperation pays when the effective re-encounter rate (controlled by
partner_persistence_probability) is high enough that coop-coop partnership
energy surplus outweighs the cost of initial encounters with non-cooperators.

Model is well-mixed: no spatial coordinates, no group structure, no kinship.
The only structure is the dyadic partnership graph that evolves via
partnership dissolution and reformation.

Key diagnostic: mean_reciprocity_quality — the population-mean of partner_memory
for adults in active partnerships. High values indicate that the average active
partnership is one where both partners are reciprocating.
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
        "ecological_models.nowak_mechanisms.direct_reciprocity.direct_reciprocity_model'."
    )

from .config.direct_reciprocity_config import DEFAULT_CONFIG
from .config.direct_reciprocity_config import config as active_config
from .config.direct_reciprocity_config import resolve_config

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
    partner_id: int | None
    # Rolling mean of partner's effective cooperation [0, 1].
    # 1.0 = partner always cooperated fully; 0.0 = partner never cooperated.
    # Initialised at 1.0 (optimistic start) for each new partnership.
    partner_memory: float
    mother_id: int | None
    father_id: int | None
    born_step: int


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


class EcologicalDirectReciprocityModel:
    """
    Population model where dyadic partner reciprocity drives cooperation.

    Cooperators pay a per-step energy cost (individual disadvantage).
    Partners who reciprocate enable energy surplus; conditional dissolution
    lets cooperators exit non-reciprocating partnerships and seek better ones.
    Direct reciprocity is the only force creating assortment — no spatial
    structure, no group membership, no kinship discrimination.
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
            partner_id=None,
            partner_memory=1.0,
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
            partner_id=None,
            partner_memory=1.0,
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
        trait_min = float(self.config["initial_helping_trait_min"])
        trait_max = float(self.config["initial_helping_trait_max"])
        return float(self.rng.uniform(trait_min, trait_max))

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
        self._update_partnerships()
        self._partnership_interaction()
        deaths = self._apply_survival()
        self._clean_partnerships_after_deaths()
        reproduction_stats = self._reproduce()
        deaths += self._apply_density_mortality()
        self._record_history(births=reproduction_stats["births"], deaths=deaths)

    def _age_and_budget(self) -> None:
        cost_per_step = float(self.config["helping_cost_per_step"])
        for individual in self.individuals:
            individual.age += 1
            individual.stage = self._stage_for_age(individual.age)
            if individual.stage == STAGE_JUVENILE:
                individual.energy += float(self.config["juvenile_foraging_energy_gain"])
                individual.energy -= float(self.config["juvenile_metabolic_cost"])
            elif individual.stage == STAGE_ADULT:
                individual.energy += float(self.config["adult_foraging_energy_gain"])
                individual.energy -= float(self.config["adult_metabolic_cost"])
                individual.energy -= individual.helping_trait * cost_per_step
            else:
                individual.energy += float(self.config["elder_foraging_energy_gain"])
                individual.energy -= float(self.config["elder_metabolic_cost"])
                individual.energy -= individual.helping_trait * cost_per_step
            individual.energy = min(individual.energy, float(self.config["max_energy"]))

    def _update_partnerships(self) -> None:
        """Dissolve stale partnerships; form new ones for unpartnered adults."""
        base_persistence = float(self.config["partner_persistence_probability"])
        leave_weight = float(self.config["leave_weight"])
        memory_off = bool(self.config["memory_off"])
        random_assign = bool(self.config["random_partner_assignment"])

        id_map = {ind.id: ind for ind in self.individuals}

        if random_assign:
            # Dissolve all partnerships every step.
            for ind in self.individuals:
                ind.partner_id = None
                ind.partner_memory = 1.0
        else:
            # Stochastic dissolution influenced by partner memory.
            dissolved: set[int] = set()
            for ind in self.individuals:
                if ind.partner_id is None or ind.id in dissolved:
                    continue
                partner = id_map.get(ind.partner_id)
                if partner is None:
                    ind.partner_id = None
                    continue

                if memory_off:
                    effective_persistence = base_persistence
                else:
                    # Cooperators leave bad partners faster.
                    effective_persistence = base_persistence * (
                        1.0 - leave_weight * (1.0 - ind.partner_memory)
                    )
                    effective_persistence = max(0.0, min(1.0, effective_persistence))

                # Dissolve if this individual decides to leave.
                if self.rng.random() > effective_persistence:
                    dissolved.add(ind.id)
                    dissolved.add(partner.id)

            for ind in self.individuals:
                if ind.id in dissolved:
                    ind.partner_id = None
                    ind.partner_memory = 1.0

        # Match unpartnered adults and elders into new pairs.
        unpartnered = [
            ind
            for ind in self.individuals
            if ind.stage in {STAGE_ADULT, STAGE_ELDER} and ind.partner_id is None
        ]
        indices = list(range(len(unpartnered)))
        self.rng.shuffle(indices)
        for i in range(0, len(indices) - 1, 2):
            a = unpartnered[indices[i]]
            b = unpartnered[indices[i + 1]]
            a.partner_id = b.id
            b.partner_id = a.id
            a.partner_memory = 1.0
            b.partner_memory = 1.0

    def _partnership_interaction(self) -> None:
        """Exchange benefits between partners; update partner memories."""
        benefit = float(self.config["cooperation_benefit_per_step"])
        reciprocity_weight = float(self.config["reciprocity_weight"])
        memory_smoothing = float(self.config["memory_smoothing"])
        memory_off = bool(self.config["memory_off"])
        max_energy = float(self.config["max_energy"])

        id_map = {ind.id: ind for ind in self.individuals}
        visited: set[int] = set()

        for ind in self.individuals:
            if ind.stage not in {STAGE_ADULT, STAGE_ELDER}:
                continue
            if ind.partner_id is None or ind.id in visited:
                continue
            partner = id_map.get(ind.partner_id)
            if partner is None:
                ind.partner_id = None
                continue

            visited.add(ind.id)
            visited.add(partner.id)

            # Effective cooperation for each individual.
            if memory_off:
                a_eff = ind.helping_trait
                b_eff = partner.helping_trait
            else:
                a_eff = ind.helping_trait * (
                    1.0 - reciprocity_weight * (1.0 - ind.partner_memory)
                )
                b_eff = partner.helping_trait * (
                    1.0 - reciprocity_weight * (1.0 - partner.partner_memory)
                )

            # Transfer benefit to partner.
            partner.energy = min(max_energy, partner.energy + a_eff * benefit)
            ind.energy = min(max_energy, ind.energy + b_eff * benefit)

            # Update partner memories (rolling average of partner's effective coop).
            if not memory_off:
                ind.partner_memory = (
                    (1.0 - memory_smoothing) * ind.partner_memory
                    + memory_smoothing * b_eff
                )
                partner.partner_memory = (
                    (1.0 - memory_smoothing) * partner.partner_memory
                    + memory_smoothing * a_eff
                )

    def _apply_survival(self) -> int:
        """Remove dead individuals; return count of deaths."""
        adult_surv = float(self.config["adult_survival_probability"])
        elder_surv = float(self.config["elder_survival_probability"])
        juv_base_surv = float(self.config["base_juvenile_survival_probability"])
        max_age = int(self.config["max_age"])

        survivors = []
        deaths = 0
        for ind in self.individuals:
            if ind.age >= max_age:
                deaths += 1
                continue
            if ind.energy <= 0.0:
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

    def _clean_partnerships_after_deaths(self) -> None:
        """Clear partner_id references to dead individuals."""
        live_ids = {ind.id for ind in self.individuals}
        for ind in self.individuals:
            if ind.partner_id is not None and ind.partner_id not in live_ids:
                ind.partner_id = None
                ind.partner_memory = 1.0

    def _reproduce(self) -> dict[str, int]:
        """Sexual reproduction: females choose random eligible males."""
        female_min = int(self.config["female_min_reproduction_age"])
        female_max = int(self.config["female_max_reproduction_age"])
        male_min = int(self.config["male_min_reproduction_age"])
        male_max = int(self.config["male_max_reproduction_age"])
        repr_prob = float(self.config["female_reproduction_probability"])
        energy_threshold = float(self.config["reproduction_energy_threshold"])
        energy_cost = float(self.config["reproduction_energy_cost"])
        repr_cost_scale = float(self.config["helping_reproduction_cost_scale"])

        eligible_males = [
            ind
            for ind in self.individuals
            if ind.sex == SEX_MALE
            and male_min <= ind.age <= male_max
            and ind.energy >= energy_threshold
        ]

        new_children: list[Individual] = []
        births = 0
        for mother in self.individuals:
            if mother.sex != SEX_FEMALE:
                continue
            if not (female_min <= mother.age <= female_max):
                continue
            if mother.energy < energy_threshold:
                continue
            # Reproduction probability reduced by helping trait.
            effective_prob = repr_prob * (
                1.0 - mother.helping_trait * repr_cost_scale
            )
            if self.rng.random() > effective_prob:
                continue
            if not eligible_males:
                continue
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
        """Trim population to max_population via random removal."""
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
        """Compute per-step diagnostics for direct reciprocity."""
        adults = [
            ind for ind in self.individuals
            if ind.stage in {STAGE_ADULT, STAGE_ELDER}
        ]
        if not adults:
            return {
                "mean_helping_trait": 0.0,
                "mean_reciprocity_quality": 0.0,
                "mean_partnership_rate": 0.0,
                "helping_invasion_frequency": 0.0,
            }

        threshold = float(self.config["helping_trait_invasion_threshold"])
        traits = [ind.helping_trait for ind in self.individuals]
        memories = [
            ind.partner_memory
            for ind in adults
            if ind.partner_id is not None
        ]
        partnered = [ind for ind in adults if ind.partner_id is not None]

        return {
            "mean_helping_trait": float(np.mean(traits)),
            "mean_reciprocity_quality": float(np.mean(memories)) if memories else 0.0,
            "mean_partnership_rate": len(partnered) / max(len(adults), 1),
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
            "latest_mean_reciprocity_quality": (
                self.history["mean_reciprocity_quality"][-1]
                if self.history["mean_reciprocity_quality"]
                else 0.0
            ),
            "latest_mean_partnership_rate": (
                self.history["mean_partnership_rate"][-1]
                if self.history["mean_partnership_rate"]
                else 0.0
            ),
        }


def run_simulation(run_config: Mapping[str, Any]) -> dict[str, Any]:
    model = EcologicalDirectReciprocityModel(run_config)
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
    model = EcologicalDirectReciprocityModel(active_config)
    steps = int(active_config["simulation_steps"])
    for i in range(steps):
        model.step()
        if (i + 1) % 100 == 0:
            s = model.summary()
            print(
                f"step {i + 1:4d}  pop={len(model.individuals):4d}"
                f"  trait={s['helping_trait_change']:+.4f}"
                f"  inv={s['helping_invasion_frequency_change']:+.4f}"
                f"  quality={s['latest_mean_reciprocity_quality']:.3f}"
                f"  partnered={s['latest_mean_partnership_rate']:.2f}"
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
        f"  quality={s['latest_mean_reciprocity_quality']:.3f}"
    )


if __name__ == "__main__":
    main()
