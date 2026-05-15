#!/usr/bin/env python3
"""
Ecological group-selection model with inter-group conflict and group fission.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.group_selection.group_selection_model

Mechanism: cooperation evolves because cooperative groups win inter-group
conflicts (warfare / raiding). Within groups, cooperators pay an energy cost
and are individually disadvantaged. Between groups, higher mean helping trait
raises combat effectiveness. Group selection is the only force that can
spread the cooperative trait.

Two addons mirror the grandmother effect in the kin-selection ecological model:
  - enable_warfare: losers can die (not just emigrate) during conflict events,
    strengthening between-group selection pressure.
  - enable_group_public_goods: within-group collective-action game on top of
    the conflict mechanism, adding realism at the cost of parsimony.

The key diagnostic is helping_trait_qst (between-group / total variance),
the multilevel-selection analog of Wright's Fst. High Qst means groups are
differentiating in cooperation level, which is required for group selection
to operate.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np


if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.group_selection.group_selection_model'."
    )

from .config.group_selection_config import config as active_config
from .config.group_selection_config import resolve_config


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
    group_id: int
    energy: float
    helping_trait: float
    mother_id: int | None
    father_id: int | None
    born_step: int


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


class EcologicalGroupSelectionModel:
    """
    Population model where inter-group conflict drives the spread of cooperation.

    Cooperators pay a per-step energy cost (within-group disadvantage).
    Groups with higher mean helping trait win conflicts and absorb members of
    losing groups (between-group advantage). Group fission prevents any single
    group from dominating by size.
    """

    def __init__(self, run_config: Mapping[str, Any]):
        self.config = resolve_config(run_config)
        self.rng = np.random.default_rng(self.config["random_seed"])
        self.individuals: list[Individual] = []
        self.next_id = 0
        self.next_group_id = 0
        self.step_index = 0
        self.history: dict[str, list[Any]] = defaultdict(list)
        self.offspring_counts: dict[int, int] = {}
        self.birth_helping_traits: dict[int, float] = {}
        self.death_ages: dict[int, int] = {}
        self.initial_mean_helping_trait = 0.0
        self._initialize_population()
        self.initial_mean_helping_trait = self._mean_helping_trait()
        group_metrics = self._compute_group_metrics()
        self._record_history(
            births=0,
            deaths=0,
            warfare_deaths=0,
            emigrations=0,
            conflict_occurred=False,
            cooperative_win=False,
            fission_count=0,
            group_extinctions=0,
            total_public_goods_contribution=0.0,
            **group_metrics,
        )

    def _initialize_population(self) -> None:
        group_count = int(self.config["initial_group_count"])
        pairs_per_group = int(self.config["founder_pairs_per_group"])
        children_per_pair = int(self.config["initial_children_per_pair"])

        for _ in range(group_count):
            group_id = self._take_group_id()
            for _ in range(pairs_per_group):
                mother = self._create_founder(SEX_FEMALE, group_id)
                father = self._create_founder(SEX_MALE, group_id)
                self.individuals.extend([mother, father])
                for _ in range(children_per_pair):
                    child = self._create_child(mother, father, initial_child=True)
                    self.individuals.append(child)

    def _create_founder(self, sex: str, group_id: int) -> Individual:
        age = int(
            self.rng.integers(
                int(self.config["initial_adult_age_min"]),
                int(self.config["initial_adult_age_max"]) + 1,
            )
        )
        founder = Individual(
            id=self._take_id(),
            sex=sex,
            age=age,
            stage=self._stage_for_age(age),
            group_id=group_id,
            energy=float(self.config["initial_adult_energy"]),
            helping_trait=self._sample_initial_helping_trait(),
            mother_id=None,
            father_id=None,
            born_step=0,
        )
        self._register_birth(founder)
        return founder

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

        group_id = mother.group_id
        dispersal_probability = float(self.config["offspring_dispersal_probability"])
        if dispersal_probability > 0.0 and self.rng.random() < dispersal_probability:
            group_id = self._random_other_group(mother.group_id)

        child = Individual(
            id=self._take_id(),
            sex=self._random_sex(),
            age=age,
            stage=self._stage_for_age(age),
            group_id=group_id,
            energy=energy,
            helping_trait=clamp01(helping_trait),
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

    def _take_group_id(self) -> int:
        next_id = self.next_group_id
        self.next_group_id += 1
        return next_id

    def _register_birth(self, individual: Individual) -> None:
        self.offspring_counts[individual.id] = 0
        self.birth_helping_traits[individual.id] = individual.helping_trait

    def _register_death(self, individual: Individual) -> None:
        self.death_ages[individual.id] = individual.age

    def _sample_initial_helping_trait(self) -> float:
        if self.rng.random() < float(self.config["rare_helper_founder_probability"]):
            return float(self.config["rare_helper_trait_value"])
        trait_min = float(self.config["initial_helping_trait_min"])
        trait_max = float(self.config["initial_helping_trait_max"])
        return float(self.rng.uniform(trait_min, trait_max))

    def _random_sex(self) -> str:
        return SEX_FEMALE if self.rng.random() < 0.5 else SEX_MALE

    def _random_other_group(self, current_group_id: int) -> int:
        active_group_ids = list({ind.group_id for ind in self.individuals})
        choices = [g for g in active_group_ids if g != current_group_id]
        if not choices:
            return current_group_id
        return int(self.rng.choice(choices))

    def _stage_for_age(self, age: int) -> str:
        if age < int(self.config["juvenile_maturity_age"]):
            return STAGE_JUVENILE
        if age >= int(self.config["elder_age"]):
            return STAGE_ELDER
        return STAGE_ADULT

    def step(self) -> None:
        self.step_index += 1
        self._age_and_budget()
        public_goods_stats = self._apply_group_public_goods()
        deaths, survival_stats = self._apply_survival()
        self._apply_maturation_dispersal()
        reproduction_stats = self._reproduce()
        deaths += self._apply_density_mortality()

        conflict_stats: dict[str, Any] = {
            "conflict_occurred": False,
            "cooperative_win": False,
            "warfare_deaths": 0,
            "emigrations": 0,
            "group_extinctions": 0,
        }
        if self.step_index % int(self.config["conflict_interval"]) == 0:
            conflict_stats = self._intergroup_conflict()
            deaths += conflict_stats["warfare_deaths"]

        fission_count = self._group_fission()
        group_metrics = self._compute_group_metrics()

        self._record_history(
            births=reproduction_stats["births"],
            deaths=deaths,
            warfare_deaths=conflict_stats["warfare_deaths"],
            emigrations=conflict_stats["emigrations"],
            conflict_occurred=conflict_stats["conflict_occurred"],
            cooperative_win=conflict_stats["cooperative_win"],
            fission_count=fission_count,
            group_extinctions=conflict_stats["group_extinctions"],
            total_public_goods_contribution=public_goods_stats[
                "total_public_goods_contribution"
            ],
            **group_metrics,
        )

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

    def _apply_group_public_goods(self) -> dict[str, float]:
        if not bool(self.config["enable_group_public_goods"]):
            return {"total_public_goods_contribution": 0.0}

        contribution_rate = float(self.config["public_goods_contribution_rate"])
        multiplier = float(self.config["public_goods_multiplier"])
        max_energy = float(self.config["max_energy"])

        groups: dict[int, list[Individual]] = defaultdict(list)
        for ind in self.individuals:
            if ind.stage in {STAGE_ADULT, STAGE_ELDER}:
                groups[ind.group_id].append(ind)

        total_contribution = 0.0
        for members in groups.values():
            if not members:
                continue
            pool = sum(
                ind.helping_trait * max(0.0, ind.energy) * contribution_rate
                for ind in members
            )
            for ind in members:
                ind.energy -= ind.helping_trait * max(0.0, ind.energy) * contribution_rate
            benefit_per_member = pool * multiplier / len(members)
            for ind in members:
                ind.energy = min(ind.energy + benefit_per_member, max_energy)
            total_contribution += pool

        return {"total_public_goods_contribution": total_contribution}

    def _apply_survival(self) -> tuple[int, dict[str, float]]:
        survivors = []
        deaths = 0
        juvenile_checks = 0
        juvenile_survivors = 0
        base_juvenile_survival = float(self.config["base_juvenile_survival_probability"])

        for individual in self.individuals:
            if individual.energy <= 0.0 or individual.age > int(self.config["max_age"]):
                self._register_death(individual)
                deaths += 1
                continue

            if individual.stage == STAGE_JUVENILE:
                juvenile_checks += 1
                if self.rng.random() > base_juvenile_survival:
                    self._register_death(individual)
                    deaths += 1
                    continue
                juvenile_survivors += 1
            elif individual.stage == STAGE_ADULT:
                if self.rng.random() > float(self.config["adult_survival_probability"]):
                    self._register_death(individual)
                    deaths += 1
                    continue
            else:
                if self.rng.random() > float(self.config["elder_survival_probability"]):
                    self._register_death(individual)
                    deaths += 1
                    continue

            survivors.append(individual)

        self.individuals = survivors
        survival_rate = (
            juvenile_survivors / juvenile_checks if juvenile_checks > 0 else math.nan
        )
        return deaths, {"juvenile_survival_rate": survival_rate}

    def _apply_maturation_dispersal(self) -> None:
        for individual in self.individuals:
            individual.stage = self._stage_for_age(individual.age)
            if (
                individual.stage == STAGE_ADULT
                and individual.age == int(self.config["juvenile_maturity_age"])
                and self.rng.random() < float(self.config["matured_dispersal_probability"])
            ):
                individual.group_id = self._random_other_group(individual.group_id)

    def _reproduce(self) -> dict[str, Any]:
        if len(self.individuals) >= int(self.config["max_population"]):
            return {"births": 0}

        adult_males: list[Individual] = []
        adult_females: list[Individual] = []
        for individual in self.individuals:
            if individual.stage != STAGE_ADULT:
                continue
            if individual.sex == SEX_MALE:
                if (
                    int(self.config["male_min_reproduction_age"])
                    <= individual.age
                    <= int(self.config["male_max_reproduction_age"])
                ):
                    adult_males.append(individual)
            elif (
                int(self.config["female_min_reproduction_age"])
                <= individual.age
                <= int(self.config["female_max_reproduction_age"])
                and individual.energy >= float(self.config["reproduction_energy_threshold"])
            ):
                adult_females.append(individual)

        base_repr_prob = float(self.config["female_reproduction_probability"])
        repr_cost_scale = float(self.config["helping_reproduction_cost_scale"])

        births: list[Individual] = []
        for mother in adult_females:
            if len(self.individuals) + len(births) >= int(self.config["max_population"]):
                break
            effective_repr_prob = base_repr_prob * max(
                0.0, 1.0 - mother.helping_trait * repr_cost_scale
            )
            if self.rng.random() > effective_repr_prob:
                continue
            father = self._choose_father(mother, adult_males)
            if father is None:
                continue
            mother.energy -= float(self.config["reproduction_energy_cost"])
            child = self._create_child(mother, father, initial_child=False)
            births.append(child)
            self.offspring_counts[mother.id] += 1
            self.offspring_counts[father.id] += 1

        self.individuals.extend(births)
        return {"births": len(births)}

    def _choose_father(
        self,
        mother: Individual,
        adult_males: list[Individual],
    ) -> Individual | None:
        if not adult_males:
            return None
        same_group = [m for m in adult_males if m.group_id == mother.group_id]
        other_group = [m for m in adult_males if m.group_id != mother.group_id]
        if same_group and (
            not other_group
            or self.rng.random() < float(self.config["same_group_mate_preference_probability"])
        ):
            candidates = same_group
        elif other_group:
            candidates = other_group
        else:
            candidates = same_group
        return candidates[int(self.rng.integers(0, len(candidates)))]

    def _apply_density_mortality(self) -> int:
        max_population = int(self.config["max_population"])
        excess = len(self.individuals) - max_population
        if excess <= 0:
            return 0
        jitter = self.rng.random(len(self.individuals)) * 0.01
        ranked = sorted(
            zip(self.individuals, jitter),
            key=lambda item: (item[0].energy + item[1], item[0].age),
        )
        removed_ids = {ind.id for ind, _ in ranked[:excess]}
        for ind, _ in ranked[:excess]:
            self._register_death(ind)
        self.individuals = [ind for ind in self.individuals if ind.id not in removed_ids]
        return excess

    def _intergroup_conflict(self) -> dict[str, Any]:
        """
        Draw one inter-group conflict event.

        Two groups compete. The group with higher mean helping trait (plus
        Gaussian noise) wins. A fraction of the losing group's adults either
        emigrate to the winner's group or die (if warfare is enabled).
        Groups that fall below min_viable_group_size are fully absorbed.

        This is the ecological analog of the Moran model's
        'copy_best_group_into_worst_group' operation, with probabilistic
        noise and demographic realism.
        """
        combatants: dict[int, list[Individual]] = defaultdict(list)
        for ind in self.individuals:
            if ind.stage in {STAGE_ADULT, STAGE_ELDER}:
                combatants[ind.group_id].append(ind)

        active_group_ids = [g for g, members in combatants.items() if members]
        if len(active_group_ids) < 2:
            return {
                "conflict_occurred": False,
                "cooperative_win": False,
                "warfare_deaths": 0,
                "emigrations": 0,
                "group_extinctions": 0,
            }

        g_a, g_b = self.rng.choice(active_group_ids, size=2, replace=False)
        noise_stddev = float(self.config["conflict_noise_stddev"])
        advantage_scale = float(self.config["conflict_winner_advantage_scale"])

        def combat_score(group_id: int) -> float:
            traits = [ind.helping_trait for ind in combatants[group_id]]
            mean_trait = float(np.mean(traits)) if traits else 0.0
            return mean_trait * advantage_scale + float(self.rng.normal(0.0, noise_stddev))

        score_a = combat_score(g_a)
        score_b = combat_score(g_b)

        mean_a = float(np.mean([ind.helping_trait for ind in combatants[g_a]]))
        mean_b = float(np.mean([ind.helping_trait for ind in combatants[g_b]]))

        if score_a >= score_b:
            winner_id, loser_id = g_a, g_b
            cooperative_win = mean_a >= mean_b
        else:
            winner_id, loser_id = g_b, g_a
            cooperative_win = mean_b >= mean_a

        loser_fighters = list(combatants[loser_id])
        n_affected = max(1, int(len(loser_fighters) * float(self.config["conflict_replacement_fraction"])))
        n_affected = min(n_affected, len(loser_fighters))
        affected_indices = self.rng.choice(len(loser_fighters), size=n_affected, replace=False)
        affected = [loser_fighters[i] for i in affected_indices]

        enable_warfare = bool(self.config["enable_warfare"])
        warfare_lethality = float(self.config["warfare_lethality"])
        warfare_deaths = 0
        emigrations = 0
        dead_ids: set[int] = set()

        for ind in affected:
            if enable_warfare and self.rng.random() < warfare_lethality:
                dead_ids.add(ind.id)
                self._register_death(ind)
                warfare_deaths += 1
            else:
                ind.group_id = winner_id
                emigrations += 1

        if dead_ids:
            self.individuals = [ind for ind in self.individuals if ind.id not in dead_ids]

        # Winner group resource bonus: all winner adults gain energy, boosting
        # their reproduction rate and growing the cooperative group faster.
        winner_energy_bonus = float(self.config["conflict_winner_energy_bonus"])
        max_energy = float(self.config["max_energy"])
        if winner_energy_bonus > 0.0:
            for ind in self.individuals:
                if ind.group_id == winner_id and ind.stage in {STAGE_ADULT, STAGE_ELDER}:
                    ind.energy = min(ind.energy + winner_energy_bonus, max_energy)

        # Absorb groups that have shrunk below the viability threshold.
        group_extinctions = 0
        min_viable = int(self.config["min_viable_group_size"])
        loser_remaining = [ind for ind in self.individuals if ind.group_id == loser_id]
        if len(loser_remaining) < min_viable:
            for ind in loser_remaining:
                ind.group_id = winner_id
            group_extinctions = 1

        return {
            "conflict_occurred": True,
            "cooperative_win": cooperative_win,
            "warfare_deaths": warfare_deaths,
            "emigrations": emigrations,
            "group_extinctions": group_extinctions,
        }

    def _group_fission(self) -> int:
        """
        Split any group that exceeds fission_threshold into two daughter groups.

        Fission prevents runaway size inequality, keeps between-group variance
        non-trivial, and models the ethnographic regularity that hunter-gatherer
        bands split when they grow too large to coordinate.
        """
        threshold = int(self.config["fission_threshold"])
        groups: dict[int, list[Individual]] = defaultdict(list)
        for ind in self.individuals:
            groups[ind.group_id].append(ind)

        fissions = 0
        for group_id, members in list(groups.items()):
            if len(members) > threshold:
                new_group_id = self._take_group_id()
                shuffled = list(members)
                self.rng.shuffle(shuffled)
                for ind in shuffled[: len(shuffled) // 2]:
                    ind.group_id = new_group_id
                fissions += 1

        return fissions

    def _compute_group_metrics(self) -> dict[str, float | int]:
        """
        Compute group-level statistics including the Qst analog for helping trait.

        helping_trait_qst = between_group_variance / (between_group_variance +
        within_group_variance). Ranges 0 (no group differentiation) to 1 (all
        variation between groups). High Qst is required for group selection to
        operate — it is the ecological model's primary diagnostic.
        """
        groups: dict[int, list[float]] = defaultdict(list)
        for ind in self.individuals:
            groups[ind.group_id].append(ind.helping_trait)

        group_count = len(groups)
        if group_count == 0:
            return {
                "group_count": 0,
                "mean_group_size": math.nan,
                "group_size_variance": math.nan,
                "between_group_helping_variance": math.nan,
                "within_group_helping_variance": math.nan,
                "helping_trait_qst": math.nan,
            }

        group_sizes = [len(traits) for traits in groups.values()]
        group_means = [float(np.mean(traits)) for traits in groups.values()]

        mean_group_size = float(np.mean(group_sizes))
        group_size_variance = float(np.var(group_sizes)) if group_count > 1 else 0.0

        if group_count < 2:
            return {
                "group_count": group_count,
                "mean_group_size": mean_group_size,
                "group_size_variance": group_size_variance,
                "between_group_helping_variance": math.nan,
                "within_group_helping_variance": math.nan,
                "helping_trait_qst": math.nan,
            }

        between_var = float(np.var(group_means))
        within_vars = [
            float(np.var(traits)) for traits in groups.values() if len(traits) > 1
        ]
        within_var = float(np.mean(within_vars)) if within_vars else 0.0
        total_var = between_var + within_var
        qst = between_var / total_var if total_var > 0.0 else math.nan

        return {
            "group_count": group_count,
            "mean_group_size": mean_group_size,
            "group_size_variance": group_size_variance,
            "between_group_helping_variance": between_var,
            "within_group_helping_variance": within_var,
            "helping_trait_qst": qst,
        }

    def _record_history(
        self,
        *,
        births: int,
        deaths: int,
        warfare_deaths: int,
        emigrations: int,
        conflict_occurred: bool,
        cooperative_win: bool,
        fission_count: int,
        group_extinctions: int,
        total_public_goods_contribution: float,
        group_count: int,
        mean_group_size: float,
        group_size_variance: float,
        between_group_helping_variance: float,
        within_group_helping_variance: float,
        helping_trait_qst: float,
    ) -> None:
        population = len(self.individuals)
        juvenile_count = sum(1 for ind in self.individuals if ind.stage == STAGE_JUVENILE)
        adult_count = sum(1 for ind in self.individuals if ind.stage == STAGE_ADULT)
        elder_count = population - juvenile_count - adult_count

        self.history["step"].append(self.step_index)
        self.history["population"].append(population)
        self.history["juvenile_count"].append(juvenile_count)
        self.history["adult_count"].append(adult_count)
        self.history["elder_count"].append(elder_count)
        self.history["births"].append(int(births))
        self.history["deaths"].append(int(deaths))
        self.history["warfare_deaths"].append(int(warfare_deaths))
        self.history["emigrations"].append(int(emigrations))
        self.history["conflict_occurred"].append(bool(conflict_occurred))
        self.history["cooperative_win"].append(bool(cooperative_win))
        self.history["fission_count"].append(int(fission_count))
        self.history["group_extinctions"].append(int(group_extinctions))
        self.history["mean_helping_trait"].append(self._mean_helping_trait())
        self.history["adult_mean_helping_trait"].append(
            self._mean_helping_trait(stage=STAGE_ADULT)
        )
        self.history["helping_invasion_frequency"].append(
            self._helping_invasion_frequency()
        )
        self.history["adult_helping_invasion_frequency"].append(
            self._helping_invasion_frequency(stage=STAGE_ADULT)
        )
        self.history["mean_energy"].append(self._mean_energy())
        self.history["group_count"].append(int(group_count))
        self.history["mean_group_size"].append(float(mean_group_size))
        self.history["group_size_variance"].append(float(group_size_variance))
        self.history["between_group_helping_variance"].append(
            float(between_group_helping_variance)
        )
        self.history["within_group_helping_variance"].append(
            float(within_group_helping_variance)
        )
        self.history["helping_trait_qst"].append(float(helping_trait_qst))
        self.history["total_public_goods_contribution"].append(
            float(total_public_goods_contribution)
        )

    def _mean_helping_trait(self, stage: str | None = None) -> float:
        values = [
            ind.helping_trait
            for ind in self.individuals
            if stage is None or ind.stage == stage
        ]
        if not values:
            return math.nan
        return float(np.mean(values))

    def _helping_invasion_frequency(self, stage: str | None = None) -> float:
        values = [
            ind.helping_trait
            for ind in self.individuals
            if stage is None or ind.stage == stage
        ]
        if not values:
            return math.nan
        threshold = float(self.config["helping_trait_invasion_threshold"])
        return sum(1 for v in values if v >= threshold) / len(values)

    def _mean_energy(self) -> float:
        if not self.individuals:
            return math.nan
        return float(np.mean([ind.energy for ind in self.individuals]))

    def _observed_age(self, individual_id: int) -> int:
        if individual_id in self.death_ages:
            return self.death_ages[individual_id]
        for ind in self.individuals:
            if ind.id == individual_id:
                return ind.age
        return 0

    def _lifetime_reproductive_success_stats(self) -> dict[str, float | int]:
        threshold = float(self.config["helping_trait_invasion_threshold"])
        maturity_age = int(self.config["juvenile_maturity_age"])
        rare_counts = []
        resident_counts = []
        for individual_id, birth_trait in self.birth_helping_traits.items():
            if self._observed_age(individual_id) < maturity_age:
                continue
            count = int(self.offspring_counts.get(individual_id, 0))
            if birth_trait >= threshold:
                rare_counts.append(count)
            else:
                resident_counts.append(count)

        rare_mean = float(np.mean(rare_counts)) if rare_counts else math.nan
        resident_mean = float(np.mean(resident_counts)) if resident_counts else math.nan
        lrs_difference = (
            rare_mean - resident_mean
            if math.isfinite(rare_mean) and math.isfinite(resident_mean)
            else math.nan
        )
        lrs_ratio = (
            rare_mean / resident_mean
            if math.isfinite(rare_mean) and resident_mean > 0.0
            else math.nan
        )
        return {
            "mean_lifetime_offspring_rare_helpers": rare_mean,
            "mean_lifetime_offspring_residents": resident_mean,
            "lifetime_offspring_difference_rare_minus_resident": lrs_difference,
            "lifetime_offspring_ratio_rare_to_resident": lrs_ratio,
            "lifetime_offspring_rare_helper_count": len(rare_counts),
            "lifetime_offspring_resident_count": len(resident_counts),
        }

    def _last_finite_history(self, key: str) -> float:
        for value in reversed(self.history[key]):
            if value is None:
                continue
            try:
                value_float = float(value)
                if math.isfinite(value_float):
                    return value_float
            except (TypeError, ValueError):
                continue
        return math.nan

    def run(self) -> dict[str, Any]:
        while self.step_index < int(self.config["simulation_steps"]) and self.individuals:
            self.step()
        return self.to_payload()

    def to_payload(self) -> dict[str, Any]:
        return {
            "summary": self.final_summary(),
            "history": dict(self.history),
        }

    def final_summary(self) -> dict[str, Any]:
        final_mean = self._mean_helping_trait()
        final_population = len(self.individuals)
        final_juveniles = sum(1 for ind in self.individuals if ind.stage == STAGE_JUVENILE)
        final_adults = sum(1 for ind in self.individuals if ind.stage == STAGE_ADULT)
        final_elders = final_population - final_juveniles - final_adults
        lrs_stats = self._lifetime_reproductive_success_stats()
        total_conflicts = sum(1 for v in self.history["conflict_occurred"] if v)
        cooperative_wins = sum(
            1
            for occurred, won in zip(
                self.history["conflict_occurred"], self.history["cooperative_win"]
            )
            if occurred and won
        )
        return {
            "steps_done": self.step_index,
            "initial_mean_helping_trait": self.initial_mean_helping_trait,
            "final_mean_helping_trait": final_mean,
            "helping_trait_change": (
                final_mean - self.initial_mean_helping_trait
                if math.isfinite(final_mean)
                else math.nan
            ),
            "initial_helping_invasion_frequency": self.history[
                "helping_invasion_frequency"
            ][0],
            "final_helping_invasion_frequency": self._helping_invasion_frequency(),
            "helping_invasion_frequency_change": (
                self._helping_invasion_frequency()
                - self.history["helping_invasion_frequency"][0]
            ),
            "final_population": final_population,
            "final_juvenile_count": final_juveniles,
            "final_adult_count": final_adults,
            "final_elder_count": final_elders,
            "final_mean_energy": self._mean_energy(),
            "total_conflicts": total_conflicts,
            "cooperative_win_fraction": (
                cooperative_wins / total_conflicts if total_conflicts > 0 else math.nan
            ),
            "total_warfare_deaths": sum(self.history["warfare_deaths"]),
            "total_fissions": sum(self.history["fission_count"]),
            "total_group_extinctions": sum(self.history["group_extinctions"]),
            "latest_group_count": self._last_finite_history("group_count"),
            "latest_mean_group_size": self._last_finite_history("mean_group_size"),
            "latest_between_group_helping_variance": self._last_finite_history(
                "between_group_helping_variance"
            ),
            "latest_within_group_helping_variance": self._last_finite_history(
                "within_group_helping_variance"
            ),
            "latest_helping_trait_qst": self._last_finite_history("helping_trait_qst"),
            **lrs_stats,
        }


def run_simulation(run_config: Mapping[str, Any]) -> dict[str, Any]:
    """Run one ecological group-selection simulation from a resolved config."""
    model = EcologicalGroupSelectionModel(run_config)
    payload = model.run()
    if bool(model.config["write_latest_run"]):
        _write_latest_run(model.config, payload)
    return payload


def _write_latest_run(run_config: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    output_dir = Path(str(run_config["data_dir"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "latest_run.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(_json_ready(payload), handle, indent=2, sort_keys=False)
        handle.write("\n")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def main() -> None:
    payload = run_simulation(resolve_config(active_config))
    summary = payload["summary"]
    print("[ecological_group_selection] final summary")
    print(f"steps_done={summary['steps_done']}")
    print(f"final_population={summary['final_population']}")
    print(
        "mean_helping_trait="
        f"{summary['initial_mean_helping_trait']:.4f}"
        " -> "
        f"{summary['final_mean_helping_trait']:.4f}"
    )
    print(f"helping_trait_change={summary['helping_trait_change']:.4f}")
    print(
        "helping_invasion_frequency="
        f"{summary['initial_helping_invasion_frequency']:.4f}"
        " -> "
        f"{summary['final_helping_invasion_frequency']:.4f}"
    )
    print(f"total_conflicts={summary['total_conflicts']}")
    print(
        f"cooperative_win_fraction={summary['cooperative_win_fraction']:.4f}"
        if math.isfinite(summary["cooperative_win_fraction"])
        else "cooperative_win_fraction=nan"
    )
    print(f"total_warfare_deaths={summary['total_warfare_deaths']}")
    print(f"latest_group_count={summary['latest_group_count']:.0f}")
    print(f"latest_helping_trait_qst={summary['latest_helping_trait_qst']:.4f}")
    print(
        "mean_lifetime_offspring="
        f"rare_helpers {summary['mean_lifetime_offspring_rare_helpers']:.4f}"
        " vs residents "
        f"{summary['mean_lifetime_offspring_residents']:.4f}"
    )


if __name__ == "__main__":
    main()
