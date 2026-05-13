#!/usr/bin/env python3
"""
Ecological kin-selection model with sexual reproduction and juvenile rearing.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.kin_selection_model
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
        "ecological_models.nowak_mechanisms.kin_selection.kin_selection_model'."
    )

from .config.kin_selection_config import config as active_config
from .config.kin_selection_config import resolve_config


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
    genome: np.ndarray
    helping_trait: float
    mother_id: int | None
    father_id: int | None
    born_step: int
    fostered_from_birth: bool


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def genetic_relatedness(genome_a: np.ndarray, genome_b: np.ndarray) -> float:
    """
    Fraction of diploid alleles shared identical-by-descent.

    Variables:
    - `genome_a`: first individual's inherited alleles, shaped `(loci, 2)`.
    - `genome_b`: second individual's inherited alleles, shaped `(loci, 2)`.
    - `loci`: number of independent genetic positions.
    - return value: shared allele copies divided by `2 * loci`.

    Expected values are approximate for stochastic relatives: parent-child
    around 0.5, full siblings around 0.5, half siblings around 0.25, and
    unrelated founders near 0.
    """

    if genome_a.shape != genome_b.shape:
        raise ValueError("genomes must have the same shape")
    if genome_a.ndim != 2 or genome_a.shape[1] != 2:
        raise ValueError("genomes must be diploid arrays shaped (loci, 2)")

    shared = 0
    for locus_a, locus_b in zip(genome_a, genome_b):
        remaining = [int(locus_b[0]), int(locus_b[1])]
        for allele in locus_a:
            allele_int = int(allele)
            if allele_int in remaining:
                shared += 1
                remaining.remove(allele_int)
    return shared / float(2 * genome_a.shape[0])


class EcologicalKinSelectionModel:
    """Population model where kin-biased rearing can change demography."""

    def __init__(self, run_config: Mapping[str, Any]):
        self.config = resolve_config(run_config)
        self.rng = np.random.default_rng(self.config["random_seed"])
        self.individuals: list[Individual] = []
        self.next_id = 0
        self.next_allele_id = 0
        self.step_index = 0
        self.history: dict[str, list[Any]] = defaultdict(list)
        self.relatedness_cache: dict[tuple[int, int], float] = {}
        self.offspring_counts: dict[int, int] = {}
        self.birth_helping_traits: dict[int, float] = {}
        self.death_ages: dict[int, int] = {}
        self.initial_mean_helping_trait = 0.0
        self._initialize_population()
        self.initial_mean_helping_trait = self._mean_helping_trait()
        self._record_history(
            births=0,
            deaths=0,
            juvenile_survival_rate=math.nan,
            total_care=0.0,
            mean_care_relatedness=math.nan,
            mean_available_care_relatedness=math.nan,
            care_assortment_gain=math.nan,
            kin_care_fraction=math.nan,
            expected_juvenile_survival_benefit=0.0,
            benefit_per_care_unit=math.nan,
            relatedness_weighted_survival_benefit=0.0,
            total_helper_energy_cost=0.0,
            expected_helper_reproduction_cost=0.0,
            hamilton_margin_proxy=math.nan,
            fostered_birth_fraction=math.nan,
            mean_mate_relatedness=math.nan,
            outside_group_mating_fraction=math.nan,
            close_kin_mate_rejections=0,
        )

    def _initialize_population(self) -> None:
        group_count = int(self.config["initial_group_count"])
        pairs_per_group = int(self.config["founder_pairs_per_group"])
        children_per_pair = int(self.config["initial_children_per_pair"])

        for group_id in range(group_count):
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
            genome=self._new_founder_genome(),
            helping_trait=self._sample_initial_helping_trait(),
            mother_id=None,
            father_id=None,
            born_step=0,
            fostered_from_birth=False,
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

        genome = self._inherit_genome(mother.genome, father.genome)
        group_id = mother.group_id
        fostered_from_birth = False
        foster_probability = float(self.config["foster_to_nonparent_group_probability"])
        dispersal_probability = float(self.config["offspring_dispersal_probability"])
        if foster_probability > 0.0 and self.rng.random() < foster_probability:
            group_id = self._random_nonparent_group(mother.group_id, father.group_id)
            fostered_from_birth = group_id not in {mother.group_id, father.group_id}
        elif dispersal_probability > 0.0 and self.rng.random() < dispersal_probability:
            group_id = self._random_other_group(mother.group_id)

        child = Individual(
            id=self._take_id(),
            sex=self._random_sex(),
            age=age,
            stage=self._stage_for_age(age),
            group_id=group_id,
            energy=energy,
            genome=genome,
            helping_trait=clamp01(helping_trait),
            mother_id=mother.id,
            father_id=father.id,
            born_step=self.step_index,
            fostered_from_birth=fostered_from_birth,
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

    def _register_death(self, individual: Individual) -> None:
        self.death_ages[individual.id] = individual.age

    def _new_founder_genome(self) -> np.ndarray:
        loci = int(self.config["genome_loci"])
        start = self.next_allele_id
        stop = start + 2 * loci
        self.next_allele_id = stop
        return np.arange(start, stop, dtype=np.int64).reshape((loci, 2))

    def _inherit_genome(self, mother_genome: np.ndarray, father_genome: np.ndarray) -> np.ndarray:
        loci = mother_genome.shape[0]
        maternal_indices = self.rng.integers(0, 2, size=loci)
        paternal_indices = self.rng.integers(0, 2, size=loci)
        maternal = mother_genome[np.arange(loci), maternal_indices]
        paternal = father_genome[np.arange(loci), paternal_indices]
        return np.column_stack([maternal, paternal]).astype(np.int64, copy=False)

    def _sample_initial_helping_trait(self) -> float:
        if self.rng.random() < float(self.config["rare_helper_founder_probability"]):
            return float(self.config["rare_helper_trait_value"])

        trait_min = float(self.config["initial_helping_trait_min"])
        trait_max = float(self.config["initial_helping_trait_max"])
        return float(self.rng.uniform(trait_min, trait_max))

    def _random_sex(self) -> str:
        return SEX_FEMALE if self.rng.random() < 0.5 else SEX_MALE

    def _random_other_group(self, current_group_id: int) -> int:
        group_count = int(self.config["initial_group_count"])
        if group_count == 1:
            return current_group_id
        choices = [group_id for group_id in range(group_count) if group_id != current_group_id]
        return int(self.rng.choice(choices))

    def _random_nonparent_group(self, mother_group_id: int, father_group_id: int) -> int:
        group_count = int(self.config["initial_group_count"])
        if group_count == 1:
            return mother_group_id
        choices = [
            group_id
            for group_id in range(group_count)
            if group_id not in {mother_group_id, father_group_id}
        ]
        if not choices:
            choices = [
                group_id for group_id in range(group_count) if group_id != mother_group_id
            ]
        if not choices:
            return mother_group_id
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
        care_by_juvenile, care_relatedness_by_juvenile, care_stats = self._provide_care()
        deaths, juvenile_survival_rate, survival_stats = self._apply_survival(
            care_by_juvenile,
            care_relatedness_by_juvenile,
        )
        self._apply_maturation_dispersal()
        reproduction_stats = self._reproduce()
        deaths += self._apply_density_mortality()
        hamilton_margin_proxy = (
            survival_stats["relatedness_weighted_survival_benefit"]
            - care_stats["expected_helper_reproduction_cost"]
        )
        self._record_history(
            births=reproduction_stats["births"],
            deaths=deaths,
            juvenile_survival_rate=juvenile_survival_rate,
            total_care=care_stats["total_care"],
            mean_care_relatedness=care_stats["mean_care_relatedness"],
            mean_available_care_relatedness=care_stats[
                "mean_available_care_relatedness"
            ],
            care_assortment_gain=care_stats["care_assortment_gain"],
            kin_care_fraction=care_stats["kin_care_fraction"],
            expected_juvenile_survival_benefit=survival_stats[
                "expected_juvenile_survival_benefit"
            ],
            benefit_per_care_unit=survival_stats["benefit_per_care_unit"],
            relatedness_weighted_survival_benefit=survival_stats[
                "relatedness_weighted_survival_benefit"
            ],
            total_helper_energy_cost=care_stats["total_helper_energy_cost"],
            expected_helper_reproduction_cost=care_stats[
                "expected_helper_reproduction_cost"
            ],
            hamilton_margin_proxy=hamilton_margin_proxy,
            fostered_birth_fraction=reproduction_stats["fostered_birth_fraction"],
            mean_mate_relatedness=reproduction_stats["mean_mate_relatedness"],
            outside_group_mating_fraction=reproduction_stats["outside_group_mating_fraction"],
            close_kin_mate_rejections=reproduction_stats["close_kin_mate_rejections"],
        )

    def _age_and_budget(self) -> None:
        for individual in self.individuals:
            individual.age += 1
            individual.stage = self._stage_for_age(individual.age)
            if individual.stage == STAGE_JUVENILE:
                individual.energy += float(self.config["juvenile_foraging_energy_gain"])
                individual.energy -= float(self.config["juvenile_metabolic_cost"])
            elif individual.stage == STAGE_ADULT:
                individual.energy += float(self.config["adult_foraging_energy_gain"])
                individual.energy -= float(self.config["adult_metabolic_cost"])
            else:
                individual.energy += float(self.config["elder_foraging_energy_gain"])
                individual.energy -= float(self.config["elder_metabolic_cost"])
            individual.energy = min(individual.energy, float(self.config["max_energy"]))

    def _provide_care(
        self,
    ) -> tuple[dict[int, float], dict[int, float], dict[str, float]]:
        juveniles_by_group: dict[int, list[Individual]] = defaultdict(list)
        helpers_by_group: dict[int, list[Individual]] = defaultdict(list)

        for individual in self.individuals:
            if individual.stage == STAGE_JUVENILE:
                juveniles_by_group[individual.group_id].append(individual)
            elif individual.stage in {STAGE_ADULT, STAGE_ELDER}:
                if individual.energy > float(self.config["helper_energy_reserve"]):
                    helpers_by_group[individual.group_id].append(individual)

        relatedness_cache: dict[tuple[int, int], float] = {}
        shuffled_genomes = self._shuffled_relatedness_genomes()
        care_by_juvenile: dict[int, float] = defaultdict(float)
        care_relatedness_by_juvenile: dict[int, float] = defaultdict(float)
        total_care = 0.0
        weighted_relatedness_sum = 0.0
        baseline_relatedness_sum = 0.0
        baseline_care_sum = 0.0
        kin_care = 0.0
        total_helper_energy_cost = 0.0
        expected_helper_reproduction_cost = 0.0

        if not bool(self.config["enable_rearing_dependency"]):
            return {}, {}, {
                "total_care": 0.0,
                "mean_care_relatedness": math.nan,
                "mean_available_care_relatedness": math.nan,
                "care_assortment_gain": math.nan,
                "kin_care_fraction": math.nan,
                "total_helper_energy_cost": 0.0,
                "expected_helper_reproduction_cost": 0.0,
            }

        for group_id, helpers in helpers_by_group.items():
            juveniles = juveniles_by_group.get(group_id, [])
            if not juveniles:
                continue
            for helper in helpers:
                available_energy = max(
                    0.0,
                    helper.energy - float(self.config["helper_energy_reserve"]),
                )
                care_budget = min(
                    helper.helping_trait * float(self.config["care_capacity_per_helper"]),
                    available_energy / max(float(self.config["care_cost_per_unit"]), 1e-12),
                )
                if care_budget <= 0.0:
                    continue

                helper_energy_before = helper.energy
                female_reproduction_before = self._is_reproductively_eligible_female(
                    helper,
                    helper_energy_before,
                )
                weights = []
                true_relatedness = []
                for juvenile in juveniles:
                    true_r = self._relatedness(helper, juvenile, relatedness_cache)
                    true_relatedness.append(true_r)
                    if bool(self.config["enable_relatedness_bias"]):
                        scoring_genome = shuffled_genomes.get(juvenile.id, juvenile.genome)
                        score_r = genetic_relatedness(helper.genome, scoring_genome)
                        weight = (
                            float(self.config["care_baseline_weight"])
                            + float(self.config["kin_bias_strength"]) * score_r
                        )
                    else:
                        weight = 1.0
                    weights.append(max(0.0, weight))

                weight_sum = sum(weights)
                if weight_sum <= 0.0:
                    continue

                baseline_care = care_budget / len(juveniles)
                for true_r in true_relatedness:
                    baseline_care_sum += baseline_care
                    baseline_relatedness_sum += baseline_care * true_r

                for juvenile, weight, true_r in zip(juveniles, weights, true_relatedness):
                    care = care_budget * weight / weight_sum
                    care_by_juvenile[juvenile.id] += care
                    care_relatedness_by_juvenile[juvenile.id] += care * true_r
                    total_care += care
                    weighted_relatedness_sum += care * true_r
                    if true_r >= float(self.config["kin_relatedness_threshold"]):
                        kin_care += care

                helper_energy_cost = care_budget * float(self.config["care_cost_per_unit"])
                helper.energy -= helper_energy_cost
                total_helper_energy_cost += helper_energy_cost
                female_reproduction_after = self._is_reproductively_eligible_female(
                    helper,
                    helper.energy,
                )
                if female_reproduction_before and not female_reproduction_after:
                    expected_helper_reproduction_cost += float(
                        self.config["female_reproduction_probability"]
                    )

        mean_care_relatedness = (
            weighted_relatedness_sum / total_care if total_care > 0.0 else math.nan
        )
        mean_available_care_relatedness = (
            baseline_relatedness_sum / baseline_care_sum
            if baseline_care_sum > 0.0
            else math.nan
        )
        care_assortment_gain = (
            mean_care_relatedness - mean_available_care_relatedness
            if math.isfinite(mean_care_relatedness)
            and math.isfinite(mean_available_care_relatedness)
            else math.nan
        )
        kin_care_fraction = kin_care / total_care if total_care > 0.0 else math.nan
        return care_by_juvenile, care_relatedness_by_juvenile, {
            "total_care": total_care,
            "mean_care_relatedness": mean_care_relatedness,
            "mean_available_care_relatedness": mean_available_care_relatedness,
            "care_assortment_gain": care_assortment_gain,
            "kin_care_fraction": kin_care_fraction,
            "total_helper_energy_cost": total_helper_energy_cost,
            "expected_helper_reproduction_cost": expected_helper_reproduction_cost,
        }

    def _shuffled_relatedness_genomes(self) -> dict[int, np.ndarray]:
        if not bool(self.config["shuffle_relatedness_for_care"]):
            return {}
        if len(self.individuals) < 2:
            return {}
        genomes = [individual.genome for individual in self.individuals]
        shuffled_indices = self.rng.permutation(len(genomes))
        return {
            individual.id: genomes[int(shuffled_index)]
            for individual, shuffled_index in zip(self.individuals, shuffled_indices)
        }

    def _relatedness(
        self,
        actor: Individual,
        recipient: Individual,
        cache: dict[tuple[int, int], float],
    ) -> float:
        key = (min(actor.id, recipient.id), max(actor.id, recipient.id))
        if key not in self.relatedness_cache:
            self.relatedness_cache[key] = genetic_relatedness(actor.genome, recipient.genome)
        cache[(actor.id, recipient.id)] = self.relatedness_cache[key]
        return self.relatedness_cache[key]

    def _apply_survival(
        self,
        care_by_juvenile: Mapping[int, float],
        care_relatedness_by_juvenile: Mapping[int, float],
    ) -> tuple[int, float, dict[str, float]]:
        survivors = []
        deaths = 0
        juvenile_checks = 0
        juvenile_survivors = 0
        expected_juvenile_survival_benefit = 0.0
        relatedness_weighted_survival_benefit = 0.0

        for individual in self.individuals:
            if individual.energy <= 0.0 or individual.age > int(self.config["max_age"]):
                self._register_death(individual)
                deaths += 1
                continue

            if individual.stage == STAGE_JUVENILE:
                juvenile_checks += 1
                if bool(self.config["enable_rearing_dependency"]):
                    raw_care = float(care_by_juvenile.get(individual.id, 0.0))
                    care = min(raw_care, float(self.config["care_saturation"]))
                    survival_without_care = float(
                        self.config["base_juvenile_survival_probability"]
                    )
                    care_benefit = (
                        float(self.config["care_benefit_to_survival"]) * care
                        if bool(self.config["enable_care_benefit"])
                        else 0.0
                    )
                    survival_probability = clamp01(
                        survival_without_care + care_benefit
                    )
                    realized_benefit = max(
                        0.0,
                        survival_probability - survival_without_care,
                    )
                    expected_juvenile_survival_benefit += realized_benefit
                    if raw_care > 0.0 and realized_benefit > 0.0:
                        weighted_r = (
                            float(care_relatedness_by_juvenile.get(individual.id, 0.0))
                            / raw_care
                        )
                        relatedness_weighted_survival_benefit += (
                            realized_benefit * weighted_r
                        )
                else:
                    survival_probability = float(
                        self.config["rearing_independent_juvenile_survival_probability"]
                    )
                if self.rng.random() > survival_probability:
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
        total_care = sum(float(care) for care in care_by_juvenile.values())
        benefit_per_care_unit = (
            expected_juvenile_survival_benefit / total_care
            if total_care > 0.0
            else math.nan
        )
        return deaths, survival_rate, {
            "expected_juvenile_survival_benefit": expected_juvenile_survival_benefit,
            "benefit_per_care_unit": benefit_per_care_unit,
            "relatedness_weighted_survival_benefit": (
                relatedness_weighted_survival_benefit
            ),
        }

    def _is_reproductively_eligible_female(
        self,
        individual: Individual,
        energy: float,
    ) -> bool:
        return (
            individual.sex == SEX_FEMALE
            and individual.stage == STAGE_ADULT
            and int(self.config["female_min_reproduction_age"])
            <= individual.age
            <= int(self.config["female_max_reproduction_age"])
            and energy >= float(self.config["reproduction_energy_threshold"])
        )

    def _apply_maturation_dispersal(self) -> None:
        for individual in self.individuals:
            previous_group = individual.group_id
            individual.stage = self._stage_for_age(individual.age)
            if (
                individual.stage == STAGE_ADULT
                and individual.age == int(self.config["juvenile_maturity_age"])
                and self.rng.random() < float(self.config["matured_dispersal_probability"])
            ):
                individual.group_id = self._random_other_group(previous_group)

    def _reproduce(self) -> dict[str, float | int]:
        if len(self.individuals) >= int(self.config["max_population"]):
            return {
                "births": 0,
                "fostered_birth_fraction": math.nan,
                "mean_mate_relatedness": math.nan,
                "outside_group_mating_fraction": math.nan,
                "close_kin_mate_rejections": 0,
            }

        adult_males = []
        adult_females = []
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

        births = []
        mate_relatedness_sum = 0.0
        outside_group_matings = 0
        close_kin_mate_rejections = 0
        mate_count = 0
        fostered_births = 0
        relatedness_cache: dict[tuple[int, int], float] = {}

        for mother in adult_females:
            if len(self.individuals) + len(births) >= int(self.config["max_population"]):
                break
            if self.rng.random() > float(self.config["female_reproduction_probability"]):
                continue
            father, mating_stats = self._choose_father(
                mother,
                adult_males,
                relatedness_cache,
            )
            close_kin_mate_rejections += mating_stats["close_kin_mate_rejections"]
            if father is None:
                continue
            mother.energy -= float(self.config["reproduction_energy_cost"])
            child = self._create_child(mother, father, initial_child=False)
            births.append(child)
            self.offspring_counts[mother.id] += 1
            self.offspring_counts[father.id] += 1
            if child.fostered_from_birth:
                fostered_births += 1
            mate_relatedness_sum += float(mating_stats["mate_relatedness"])
            if father.group_id != mother.group_id:
                outside_group_matings += 1
            mate_count += 1

        self.individuals.extend(births)
        return {
            "births": len(births),
            "fostered_birth_fraction": (
                fostered_births / len(births) if births else math.nan
            ),
            "mean_mate_relatedness": (
                mate_relatedness_sum / mate_count if mate_count > 0 else math.nan
            ),
            "outside_group_mating_fraction": (
                outside_group_matings / mate_count if mate_count > 0 else math.nan
            ),
            "close_kin_mate_rejections": close_kin_mate_rejections,
        }

    def _choose_father(
        self,
        mother: Individual,
        adult_males: list[Individual],
        relatedness_cache: dict[tuple[int, int], float],
    ) -> tuple[Individual | None, dict[str, float | int]]:
        max_mate_relatedness = float(self.config["max_mate_relatedness"])
        same_group_candidates = []
        outside_group_candidates = []
        close_kin_mate_rejections = 0

        for male in adult_males:
            mate_relatedness = self._relatedness(mother, male, relatedness_cache)
            if mate_relatedness > max_mate_relatedness:
                close_kin_mate_rejections += 1
                continue
            candidate = (male, mate_relatedness)
            if male.group_id == mother.group_id:
                same_group_candidates.append(candidate)
            else:
                outside_group_candidates.append(candidate)

        if not same_group_candidates and not outside_group_candidates:
            return None, {
                "mate_relatedness": math.nan,
                "close_kin_mate_rejections": close_kin_mate_rejections,
            }

        if same_group_candidates and outside_group_candidates:
            if self.rng.random() < float(self.config["same_group_mate_preference_probability"]):
                candidates = same_group_candidates
            else:
                candidates = outside_group_candidates
        else:
            candidates = same_group_candidates or outside_group_candidates

        father, mate_relatedness = candidates[int(self.rng.integers(0, len(candidates)))]
        return father, {
            "mate_relatedness": mate_relatedness,
            "close_kin_mate_rejections": close_kin_mate_rejections,
        }

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
        removed_ids = {individual.id for individual, _ in ranked[:excess]}
        for individual, _ in ranked[:excess]:
            self._register_death(individual)
        self.individuals = [
            individual for individual in self.individuals if individual.id not in removed_ids
        ]
        return excess

    def _record_history(
        self,
        *,
        births: int,
        deaths: int,
        juvenile_survival_rate: float,
        total_care: float,
        mean_care_relatedness: float,
        mean_available_care_relatedness: float,
        care_assortment_gain: float,
        kin_care_fraction: float,
        expected_juvenile_survival_benefit: float,
        benefit_per_care_unit: float,
        relatedness_weighted_survival_benefit: float,
        total_helper_energy_cost: float,
        expected_helper_reproduction_cost: float,
        hamilton_margin_proxy: float,
        fostered_birth_fraction: float,
        mean_mate_relatedness: float,
        outside_group_mating_fraction: float,
        close_kin_mate_rejections: int,
    ) -> None:
        population = len(self.individuals)
        juvenile_count = sum(1 for individual in self.individuals if individual.stage == STAGE_JUVENILE)
        adult_count = sum(1 for individual in self.individuals if individual.stage == STAGE_ADULT)
        elder_count = population - juvenile_count - adult_count

        self.history["step"].append(self.step_index)
        self.history["population"].append(population)
        self.history["juvenile_count"].append(juvenile_count)
        self.history["adult_count"].append(adult_count)
        self.history["elder_count"].append(elder_count)
        self.history["births"].append(int(births))
        self.history["deaths"].append(int(deaths))
        self.history["mean_helping_trait"].append(self._mean_helping_trait())
        self.history["adult_mean_helping_trait"].append(self._mean_helping_trait(stage=STAGE_ADULT))
        self.history["helping_invasion_frequency"].append(
            self._helping_invasion_frequency()
        )
        self.history["adult_helping_invasion_frequency"].append(
            self._helping_invasion_frequency(stage=STAGE_ADULT)
        )
        self.history["mean_energy"].append(self._mean_energy())
        self.history["juvenile_survival_rate"].append(juvenile_survival_rate)
        self.history["total_care"].append(float(total_care))
        self.history["mean_care_relatedness"].append(float(mean_care_relatedness))
        self.history["mean_available_care_relatedness"].append(
            float(mean_available_care_relatedness)
        )
        self.history["care_assortment_gain"].append(float(care_assortment_gain))
        self.history["kin_care_fraction"].append(float(kin_care_fraction))
        self.history["expected_juvenile_survival_benefit"].append(
            float(expected_juvenile_survival_benefit)
        )
        self.history["benefit_per_care_unit"].append(float(benefit_per_care_unit))
        self.history["relatedness_weighted_survival_benefit"].append(
            float(relatedness_weighted_survival_benefit)
        )
        self.history["total_helper_energy_cost"].append(float(total_helper_energy_cost))
        self.history["expected_helper_reproduction_cost"].append(
            float(expected_helper_reproduction_cost)
        )
        self.history["hamilton_margin_proxy"].append(float(hamilton_margin_proxy))
        self.history["fostered_birth_fraction"].append(float(fostered_birth_fraction))
        self.history["mean_mate_relatedness"].append(float(mean_mate_relatedness))
        self.history["outside_group_mating_fraction"].append(float(outside_group_mating_fraction))
        self.history["close_kin_mate_rejections"].append(int(close_kin_mate_rejections))

    def _mean_helping_trait(self, stage: str | None = None) -> float:
        values = [
            individual.helping_trait
            for individual in self.individuals
            if stage is None or individual.stage == stage
        ]
        if not values:
            return math.nan
        return float(np.mean(values))

    def _helping_invasion_frequency(self, stage: str | None = None) -> float:
        values = [
            individual.helping_trait
            for individual in self.individuals
            if stage is None or individual.stage == stage
        ]
        if not values:
            return math.nan
        threshold = float(self.config["helping_trait_invasion_threshold"])
        above_threshold = sum(1 for value in values if value >= threshold)
        return above_threshold / len(values)

    def _mean_energy(self) -> float:
        if not self.individuals:
            return math.nan
        return float(np.mean([individual.energy for individual in self.individuals]))

    def _observed_age(self, individual_id: int) -> int:
        if individual_id in self.death_ages:
            return self.death_ages[individual_id]
        for individual in self.individuals:
            if individual.id == individual_id:
                return individual.age
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
            value_float = float(value)
            if math.isfinite(value_float):
                return value_float
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
        final_juveniles = sum(
            1 for individual in self.individuals if individual.stage == STAGE_JUVENILE
        )
        final_adults = sum(
            1 for individual in self.individuals if individual.stage == STAGE_ADULT
        )
        final_elders = final_population - final_juveniles - final_adults
        lrs_stats = self._lifetime_reproductive_success_stats()
        return {
            "steps_done": self.step_index,
            "initial_mean_helping_trait": self.initial_mean_helping_trait,
            "final_mean_helping_trait": final_mean,
            "helping_trait_change": final_mean - self.initial_mean_helping_trait
            if math.isfinite(final_mean)
            else math.nan,
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
            "latest_juvenile_survival_rate": self._last_finite_history(
                "juvenile_survival_rate"
            ),
            "latest_total_care": self._last_finite_history("total_care"),
            "latest_mean_care_relatedness": self._last_finite_history(
                "mean_care_relatedness"
            ),
            "latest_mean_available_care_relatedness": self._last_finite_history(
                "mean_available_care_relatedness"
            ),
            "latest_care_assortment_gain": self._last_finite_history(
                "care_assortment_gain"
            ),
            "latest_kin_care_fraction": self._last_finite_history("kin_care_fraction"),
            "latest_expected_juvenile_survival_benefit": self._last_finite_history(
                "expected_juvenile_survival_benefit"
            ),
            "latest_benefit_per_care_unit": self._last_finite_history(
                "benefit_per_care_unit"
            ),
            "latest_relatedness_weighted_survival_benefit": self._last_finite_history(
                "relatedness_weighted_survival_benefit"
            ),
            "latest_total_helper_energy_cost": self._last_finite_history(
                "total_helper_energy_cost"
            ),
            "latest_expected_helper_reproduction_cost": self._last_finite_history(
                "expected_helper_reproduction_cost"
            ),
            "latest_hamilton_margin_proxy": self._last_finite_history(
                "hamilton_margin_proxy"
            ),
            "latest_fostered_birth_fraction": self._last_finite_history(
                "fostered_birth_fraction"
            ),
            **lrs_stats,
            "latest_mean_mate_relatedness": self._last_finite_history(
                "mean_mate_relatedness"
            ),
            "latest_outside_group_mating_fraction": self._last_finite_history(
                "outside_group_mating_fraction"
            ),
            "latest_close_kin_mate_rejections": self._last_finite_history(
                "close_kin_mate_rejections"
            ),
        }


def run_simulation(run_config: Mapping[str, Any]) -> dict[str, Any]:
    """Run one ecological kin-selection simulation from a resolved config."""

    model = EcologicalKinSelectionModel(run_config)
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
    print("[ecological_kin_selection] final summary")
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
    print(f"latest_juvenile_survival_rate={summary['latest_juvenile_survival_rate']:.4f}")
    print(f"latest_mean_care_relatedness={summary['latest_mean_care_relatedness']:.4f}")
    print(
        "latest_mean_available_care_relatedness="
        f"{summary['latest_mean_available_care_relatedness']:.4f}"
    )
    print(f"latest_care_assortment_gain={summary['latest_care_assortment_gain']:.4f}")
    print(f"latest_kin_care_fraction={summary['latest_kin_care_fraction']:.4f}")
    print(
        "latest_expected_juvenile_survival_benefit="
        f"{summary['latest_expected_juvenile_survival_benefit']:.4f}"
    )
    print(f"latest_benefit_per_care_unit={summary['latest_benefit_per_care_unit']:.4f}")
    print(
        "latest_expected_helper_reproduction_cost="
        f"{summary['latest_expected_helper_reproduction_cost']:.4f}"
    )
    print(f"latest_hamilton_margin_proxy={summary['latest_hamilton_margin_proxy']:.4f}")
    print(
        "mean_lifetime_offspring="
        f"rare_helpers {summary['mean_lifetime_offspring_rare_helpers']:.4f}"
        " vs residents "
        f"{summary['mean_lifetime_offspring_residents']:.4f}"
    )
    print(
        "lifetime_offspring_difference_rare_minus_resident="
        f"{summary['lifetime_offspring_difference_rare_minus_resident']:.4f}"
    )
    print(f"latest_fostered_birth_fraction={summary['latest_fostered_birth_fraction']:.4f}")
    print(f"latest_mean_mate_relatedness={summary['latest_mean_mate_relatedness']:.4f}")
    print(f"latest_outside_group_mating_fraction={summary['latest_outside_group_mating_fraction']:.4f}")


if __name__ == "__main__":
    main()
