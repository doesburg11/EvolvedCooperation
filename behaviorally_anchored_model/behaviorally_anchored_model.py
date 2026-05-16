#!/usr/bin/env python3
"""
Behaviorally anchored model: human cooperation capacities in a family ecology.

Run from the repository root with:
  ./.conda/bin/python -m behaviorally_anchored_model.behaviorally_anchored_model

The bottom-up ecological models identified the load-bearing channel for each
classic cooperation mechanism. This behaviorally anchored model asks how
human-like cooperation changes when agents carry multiple social capacities
inside a demographic ecology with family bonds, households, local movement,
grass foraging, parent food transfer, reproduction, child rearing, social
learning, and density pressure.

Website counterpart:
  https://humanbehaviorpatterns.org/history-of-human-cooperation-and-competition

Core social/ecological capacities:

  1. Reputation sensitivity (indirect reciprocity): public reputation gates
     energy routing; high-reputation males preferred as mates.

  2. Norm enforcement: adults with reputation far below the population mean
     incur a social energy penalty (third-party sanctioning).

  3. Bands (group selection): agents belong to concrete residential bands
     with territory centers. Bands bias interaction routing and mate choice,
     can receive migrants, fission when large, fuse when small, and enter
     inter-band conflict.

  4. Kin recognition and child rearing (kin selection): agents route
     interactions preferentially toward kin (siblings, parents, offspring);
     kin males get a mate-choice weight bonus; co-parents can form persistent
     spouse bonds and households; adults and elders can invest costly care in
     nearby juveniles, biased toward their own children, spouse-linked children,
     household members, and kin; parents can pass surplus harvested food to
     their own juveniles.

  5. Spatial awareness (network reciprocity): heritable spatial coordinates;
     offspring placed near mother; agents move locally during life; spatial
     neighbors preferred for interactions and mate choice.

  6. Reciprocity bonds (direct reciprocity): stable dyadic social bonds;
     local bond formation, conditional cooperation based on bond memory,
     and differential dissolution.

  7. Social learning: subadults, adults, and elders can copy nearby
     demonstrators. Copying changes a bounded within-lifetime adjustment to
     cooperative behavior without rewriting the inherited trait.

Routing priority for unbonded interactions: kin > spatial > band > random.
Mate weight: reputation × band × inter-band marriage × spatial × kin × spouse.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np


if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m behaviorally_anchored_model.behaviorally_anchored_model'."
    )

from .config.behaviorally_anchored_config import DEFAULT_CONFIG
from .config.behaviorally_anchored_config import config as active_config
from .config.behaviorally_anchored_config import resolve_config

DEFAULT_STEPS = int(DEFAULT_CONFIG["simulation_steps"])

SEX_FEMALE = "F"
SEX_MALE = "M"
STAGE_JUVENILE = "juvenile"
STAGE_SUBADULT = "subadult"
STAGE_ADULT = "adult"
STAGE_ELDER = "elder"


@dataclass
class Individual:
    id: int
    sex: str
    age: int
    stage: str
    energy: float
    helping_trait: float      # heritable, evolves
    learned_helping_adjustment: float  # within-lifetime social learning
    reputation: float         # public, not inherited
    group_id: int             # concrete band membership
    x: float                  # spatial coordinate (network reciprocity)
    y: float
    household_id: int         # co-resident family/camp unit
    spouse_id: int | None             # persistent co-parent pair bond
    reciprocity_bond_id: int | None    # current direct-reciprocity bondmate
    reciprocity_bond_memory: float     # rolling mean of bondmate cooperation
    mother_id: int | None
    father_id: int | None
    born_step: int


@dataclass
class Household:
    id: int
    x: float
    y: float
    founded_step: int


@dataclass
class Band:
    id: int
    x: float
    y: float
    radius: float
    founded_step: int


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


class BehaviorallyAnchoredModel:
    """
    Population model testing how human-like social structure changes
    cooperation from a rare 10% foothold.

    Demographic backbone: age structure, energy budget, blending inheritance,
    grass-limited foraging, dependent juveniles, non-reproductive subadults,
    parent-to-child food transfer, household co-residence, child rearing, and
    density-dependent survival.
    """

    def __init__(self, run_config: Mapping[str, Any]):
        self.config = resolve_config(run_config)
        self.rng = np.random.default_rng(self.config["random_seed"])
        self.individuals: list[Individual] = []
        self.households: dict[int, Household] = {}
        self.bands: dict[int, Band] = {}
        self.next_id = 0
        self.next_household_id = 0
        self.next_band_id = 0
        self.step_index = 0
        self.history: dict[str, list[Any]] = defaultdict(list)
        self.offspring_counts: dict[int, int] = {}
        self.birth_helping_traits: dict[int, float] = {}
        self.initial_mean_helping_trait = 0.0
        self.grass = self._initialize_grass()
        self._grass_harvest_offsets = self._build_grass_harvest_offsets()
        self._kin_index: dict[int, list[Individual]] = {}
        self.last_helping_events = 0
        self.last_helping_opportunities = 0
        self.last_realized_helping_rate = math.nan
        self.last_social_learning_events = 0
        self.last_mean_learned_helping_adjustment = 0.0
        self.last_mean_effective_helping = 0.0
        self.last_mean_grass_fraction = self._mean_grass_fraction()
        self.last_grass_harvest = 0.0
        self.last_parent_food_transfer = 0.0
        self.last_parent_food_by_juvenile: dict[int, float] = {}
        self.last_fed_juvenile_count = 0
        self.last_fed_juvenile_fraction = math.nan
        self.last_mean_juvenile_food_survival_effect = math.nan
        self.last_juvenile_survival_rate = math.nan
        self.last_total_child_rearing_care = 0.0
        self.last_mean_child_rearing_care = 0.0
        self.last_mean_child_rearing_relatedness = math.nan
        self.last_kin_child_rearing_fraction = math.nan
        self.last_parent_child_rearing_fraction = math.nan
        self.last_household_child_rearing_fraction = math.nan
        self.last_spouse_child_rearing_fraction = math.nan
        self.last_coparent_near_child_rearing_fraction = math.nan
        self.last_child_care_by_juvenile: dict[int, float] = {}
        self.last_cared_juvenile_count = 0
        self.last_cared_juvenile_fraction = math.nan
        self.last_mean_household_survival_bonus = math.nan
        self.last_two_living_parent_juvenile_fraction = math.nan
        self.last_household_caregiver_juvenile_fraction = math.nan
        self.last_maturity_dispersals = 0
        self.last_band_migrations = 0
        self.last_band_fissions = 0
        self.last_band_fusions = 0
        self.last_interband_marriages = 0
        self.total_band_migrations = 0
        self.total_band_fissions = 0
        self.total_band_fusions = 0
        self.total_interband_marriages = 0
        self._initialize_bands()
        self._initialize_population()
        self.initial_mean_helping_trait = self._mean_helping_trait()
        self._record_history(births=0, deaths=0)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialize_bands(self) -> None:
        """Seed initial band territories across the toroidal landscape."""
        n_bands = int(self.config["n_groups"])
        width = float(self.config["space_width"])
        radius = float(self.config["band_territory_radius"])
        center = width / 2.0
        orbit = width * 0.32
        for idx in range(n_bands):
            angle = 2.0 * math.pi * idx / n_bands
            jitter = radius * 0.20
            x = center + math.cos(angle) * orbit + float(self.rng.normal(0.0, jitter))
            y = center + math.sin(angle) * orbit + float(self.rng.normal(0.0, jitter))
            self._create_band(x % width, y % width, radius)

    def _create_band(self, x: float, y: float, radius: float | None = None) -> int:
        width = float(self.config["space_width"])
        band_id = self.next_band_id
        self.next_band_id += 1
        self.bands[band_id] = Band(
            id=band_id,
            x=float(x) % width,
            y=float(y) % width,
            radius=float(self.config["band_territory_radius"]) if radius is None else radius,
            founded_step=self.step_index,
        )
        return band_id

    def _choose_band_id(self) -> int:
        if not self.bands:
            raise RuntimeError("At least one band must exist before creating people.")
        return int(self.rng.choice(sorted(self.bands)))

    def _initialize_population(self) -> None:
        pairs = int(self.config["initial_founder_pairs"])
        children_per_pair = int(self.config["initial_children_per_pair"])
        for _ in range(pairs):
            band_id = self._choose_band_id()
            mother = self._create_founder(SEX_FEMALE, band_id=band_id)
            household_id = self._create_household(mother.x, mother.y)
            mother.household_id = household_id
            father = self._create_founder(SEX_MALE, band_id=band_id)
            father.household_id = household_id
            self._place_near(father, mother, float(self.config["initial_spouse_dispersal_std"]))
            if self._form_spouse_bond(mother, father):
                self._try_form_spouse_reciprocity_bond(mother, father)
            self.individuals.extend([mother, father])
            for _ in range(children_per_pair):
                self.individuals.append(self._create_child(mother, father, initial_child=True))

    def _create_founder(self, sex: str, *, band_id: int | None = None) -> Individual:
        width = float(self.config["space_width"])
        if band_id is None:
            band_id = self._choose_band_id()
        band = self.bands[band_id]
        dispersal = max(1.0, band.radius * 0.70)
        age = int(self.rng.integers(
            int(self.config["initial_adult_age_min"]),
            int(self.config["initial_adult_age_max"]) + 1,
        ))
        return Individual(
            id=self._take_id(),
            sex=sex,
            age=age,
            stage=self._stage_for_age(age),
            energy=float(self.config["initial_adult_energy"]),
            helping_trait=self._sample_initial_helping_trait(),
            learned_helping_adjustment=0.0,
            reputation=float(self.config["reputation_initial"]),
            group_id=band_id,
            x=(band.x + float(self.rng.normal(0.0, dispersal))) % width,
            y=(band.y + float(self.rng.normal(0.0, dispersal))) % width,
            household_id=-1,
            spouse_id=None,
            reciprocity_bond_id=None,
            reciprocity_bond_memory=1.0,
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
        width = float(self.config["space_width"])
        dispersal = float(self.config["offspring_dispersal_std"])

        age = int(self.rng.integers(
            int(self.config["initial_child_age_min"]),
            int(self.config["initial_child_age_max"]) + 1,
        )) if initial_child else 0
        energy = float(self.config["initial_juvenile_energy"]) if initial_child else float(self.config["child_energy"])

        helping_trait = 0.5 * (mother.helping_trait + father.helping_trait)
        if self.rng.random() < float(self.config["helping_mutation_probability"]):
            helping_trait += float(self.rng.normal(0.0, float(self.config["helping_mutation_stddev"])))

        # Children are born into the mother's residential band. Later migration
        # is handled as an individual life-history event, not as random newborn
        # reassignment.
        group_id = mother.group_id

        cx = (mother.x + float(self.rng.normal(0.0, dispersal))) % width
        cy = (mother.y + float(self.rng.normal(0.0, dispersal))) % width

        child = Individual(
            id=self._take_id(),
            sex=SEX_FEMALE if self.rng.random() < 0.5 else SEX_MALE,
            age=age,
            stage=self._stage_for_age(age),
            energy=energy,
            helping_trait=clamp01(helping_trait),
            learned_helping_adjustment=0.0,
            reputation=float(self.config["reputation_initial"]),
            group_id=group_id,
            x=cx,
            y=cy,
            household_id=mother.household_id,
            spouse_id=None,
            reciprocity_bond_id=None,
            reciprocity_bond_memory=1.0,
            mother_id=mother.id,
            father_id=father.id,
            born_step=self.step_index,
        )
        self.offspring_counts[child.id] = 0
        self.birth_helping_traits[child.id] = child.helping_trait
        return child

    def _create_household(self, x: float, y: float) -> int:
        width = float(self.config["space_width"])
        household_id = self.next_household_id
        self.next_household_id += 1
        self.households[household_id] = Household(
            id=household_id,
            x=float(x) % width,
            y=float(y) % width,
            founded_step=self.step_index,
        )
        return household_id

    def _maybe_form_new_household_at_maturity(self, ind: Individual) -> None:
        if self.rng.random() > float(self.config["maturity_new_household_probability"]):
            return
        width = float(self.config["space_width"])
        dispersal = float(self.config["maturity_household_dispersal_std"])
        x = (ind.x + float(self.rng.normal(0.0, dispersal))) % width
        y = (ind.y + float(self.rng.normal(0.0, dispersal))) % width
        ind.x = x
        ind.y = y
        ind.household_id = self._create_household(x, y)
        self.last_maturity_dispersals += 1

    def _join_household(self, ind: Individual, household_id: int) -> None:
        if household_id not in self.households:
            return
        ind.household_id = household_id

    def _prune_households(self) -> None:
        live_household_ids = {i.household_id for i in self.individuals}
        for household_id in list(self.households):
            if household_id not in live_household_ids:
                del self.households[household_id]

    def _place_near(self, ind: Individual, reference: Individual, dispersal_std: float) -> None:
        width = float(self.config["space_width"])
        ind.x = (reference.x + float(self.rng.normal(0.0, dispersal_std))) % width
        ind.y = (reference.y + float(self.rng.normal(0.0, dispersal_std))) % width

    def _take_id(self) -> int:
        nid = self.next_id
        self.next_id += 1
        return nid

    def _sample_initial_helping_trait(self) -> float:
        if self.rng.random() < float(self.config["rare_helper_founder_probability"]):
            return float(self.config["rare_helper_trait_value"])
        return float(self.rng.uniform(
            float(self.config["initial_helping_trait_min"]),
            float(self.config["initial_helping_trait_max"]),
        ))

    @staticmethod
    def _effective_helping(ind: Individual) -> float:
        return clamp01(ind.helping_trait + ind.learned_helping_adjustment)

    def _stage_for_age(self, age: int) -> str:
        if age < int(self.config["juvenile_dependency_age"]):
            return STAGE_JUVENILE
        if age < int(self.config["adult_maturity_age"]):
            return STAGE_SUBADULT
        if age >= int(self.config["elder_age"]):
            return STAGE_ELDER
        return STAGE_ADULT

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self) -> None:
        self.step_index += 1
        self._age_and_budget()
        self._move_individuals()
        self._migrate_between_bands()
        self._update_household_residences()
        self._update_band_territories()
        self._regrow_grass()
        self._forage_grass_and_feed_juveniles()
        self._kin_index = self._build_kin_index()
        self._update_reciprocity_bonds()
        self._conduct_interactions()
        self._apply_norm_enforcement()
        self._apply_social_learning()
        conflict_interval = int(self.config["conflict_interval"])
        if conflict_interval > 0 and self.step_index % conflict_interval == 0:
            self._apply_group_conflict()
        child_care = self._provide_child_rearing()
        deaths = self._apply_survival(child_care)
        self._clear_dead_reciprocity_bonds()
        self._clear_dead_spouse_bonds()
        self._prune_households()
        stats = self._reproduce()
        self._update_household_residences()
        self._prune_households()
        self._update_band_dynamics()
        self._update_band_territories()
        self._record_history(births=stats["births"], deaths=deaths)

    # ------------------------------------------------------------------
    # Age and energy budget
    # ------------------------------------------------------------------

    def _age_and_budget(self) -> None:
        cost = float(self.config["helping_cost_per_step"])
        max_e = float(self.config["max_energy"])
        self.last_maturity_dispersals = 0
        self.last_band_migrations = 0
        self.last_band_fissions = 0
        self.last_band_fusions = 0
        self.last_interband_marriages = 0
        for ind in self.individuals:
            old_stage = ind.stage
            ind.age += 1
            ind.stage = self._stage_for_age(ind.age)
            if old_stage in {STAGE_JUVENILE, STAGE_SUBADULT} and ind.stage == STAGE_ADULT:
                self._maybe_form_new_household_at_maturity(ind)
            if ind.stage == STAGE_JUVENILE:
                ind.energy += float(self.config["juvenile_foraging_energy_gain"])
                ind.energy -= float(self.config["juvenile_metabolic_cost"])
            elif ind.stage == STAGE_SUBADULT:
                ind.energy -= float(self.config["subadult_metabolic_cost"])
            elif ind.stage == STAGE_ADULT:
                ind.energy -= float(self.config["adult_metabolic_cost"])
                ind.energy -= self._effective_helping(ind) * cost
            else:
                ind.energy -= float(self.config["elder_metabolic_cost"])
                ind.energy -= self._effective_helping(ind) * cost
            ind.energy = min(ind.energy, max_e)

    # ------------------------------------------------------------------
    # Local grass foraging and parent food transfer
    # ------------------------------------------------------------------

    def _initialize_grass(self) -> np.ndarray:
        grid_size = int(self.config["grass_grid_size"])
        max_grass = float(self.config["grass_max_per_cell"])
        initial_fraction = float(self.config["grass_initial_fraction"])
        return np.full(
            (grid_size, grid_size),
            max_grass * initial_fraction,
            dtype=float,
        )

    def _mean_grass_fraction(self) -> float:
        max_grass = float(self.config["grass_max_per_cell"])
        if max_grass <= 0.0:
            return math.nan
        return float(np.mean(self.grass) / max_grass)

    def _regrow_grass(self) -> None:
        max_grass = float(self.config["grass_max_per_cell"])
        regrowth = float(self.config["grass_regrowth_per_step"])
        if max_grass <= 0.0 or regrowth <= 0.0:
            self.last_mean_grass_fraction = self._mean_grass_fraction()
            return
        np.minimum(self.grass + regrowth, max_grass, out=self.grass)
        self.last_mean_grass_fraction = self._mean_grass_fraction()

    def _build_grass_harvest_offsets(self) -> list[tuple[float, int, int]]:
        width = float(self.config["space_width"])
        grid_size = int(self.config["grass_grid_size"])
        radius = float(self.config["grass_harvest_radius"])
        if radius <= 0.0:
            return [(0.0, 0, 0)]
        cell_size = width / grid_size
        inclusion_radius = radius + cell_size * math.sqrt(2.0) * 0.5
        span = int(math.ceil(inclusion_radius / cell_size))
        offsets: list[tuple[float, int, int]] = []
        for dr in range(-span, span + 1):
            for dc in range(-span, span + 1):
                distance = math.sqrt((dr * cell_size) ** 2 + (dc * cell_size) ** 2)
                if distance <= inclusion_radius:
                    offsets.append((distance, dr, dc))
        return sorted(offsets)

    def _grass_cell_for_position(self, x: float, y: float) -> tuple[int, int]:
        width = float(self.config["space_width"])
        grid_size = int(self.config["grass_grid_size"])
        col = int((x % width) / width * grid_size) % grid_size
        row = int((y % width) / width * grid_size) % grid_size
        return row, col

    def _harvest_grass_at(self, x: float, y: float, capacity: float) -> float:
        max_grass = float(self.config["grass_max_per_cell"])
        if max_grass <= 0.0 or capacity <= 0.0:
            return 0.0
        remaining = capacity
        harvested = 0.0
        for _, row, col in self._grass_cells_for_harvest(x, y):
            if remaining <= 0.0:
                break
            available = float(self.grass[row, col])
            if available <= 0.0:
                continue
            take = min(remaining, available)
            self.grass[row, col] = available - take
            harvested += take
            remaining -= take
        return harvested

    def _grass_cells_for_harvest(self, x: float, y: float) -> list[tuple[float, int, int]]:
        grid_size = int(self.config["grass_grid_size"])
        row, col = self._grass_cell_for_position(x, y)
        return [
            (distance, (row + dr) % grid_size, (col + dc) % grid_size)
            for distance, dr, dc in self._grass_harvest_offsets
        ]

    def _forage_grass_and_feed_juveniles(self) -> None:
        max_e = float(self.config["max_energy"])
        harvest_capacity = {
            STAGE_SUBADULT: float(self.config["subadult_foraging_energy_gain"]),
            STAGE_ADULT: float(self.config["adult_foraging_energy_gain"]),
            STAGE_ELDER: float(self.config["elder_foraging_energy_gain"]),
        }
        self.last_grass_harvest = 0.0
        self.last_parent_food_transfer = 0.0
        self.last_parent_food_by_juvenile = {}
        self.last_fed_juvenile_count = 0
        self.last_fed_juvenile_fraction = math.nan

        for ind in self.individuals:
            if ind.stage not in harvest_capacity:
                continue
            capacity = min(harvest_capacity[ind.stage], max(0.0, max_e - ind.energy))
            harvested = self._harvest_grass_at(ind.x, ind.y, capacity)
            if harvested <= 0.0:
                continue
            ind.energy = min(max_e, ind.energy + harvested)
            self.last_grass_harvest += harvested

        self.last_mean_grass_fraction = self._mean_grass_fraction()
        self._feed_juveniles_from_parent_surplus()

    def _feed_juveniles_from_parent_surplus(self) -> None:
        transfer_capacity = float(self.config["parent_food_transfer_capacity"])
        if transfer_capacity <= 0.0:
            juveniles = [i for i in self.individuals if i.stage == STAGE_JUVENILE]
            self.last_fed_juvenile_fraction = 0.0 if juveniles else math.nan
            return

        radius = float(self.config["parent_food_transfer_radius"])
        reserve = float(self.config["parent_food_transfer_energy_reserve"])
        household_bonus = float(self.config["parent_food_transfer_household_weight_bonus"])
        max_e = float(self.config["max_energy"])
        juveniles = [i for i in self.individuals if i.stage == STAGE_JUVENILE]
        if not juveniles:
            return

        juveniles_by_parent: dict[int, list[Individual]] = defaultdict(list)
        for juvenile in juveniles:
            for parent_id in (juvenile.mother_id, juvenile.father_id):
                if parent_id is not None:
                    juveniles_by_parent[parent_id].append(juvenile)

        food_by_juvenile: dict[int, float] = defaultdict(float)
        total_transfer = 0.0
        for parent in self.individuals:
            if parent.stage not in {STAGE_ADULT, STAGE_ELDER}:
                continue
            own_juveniles = juveniles_by_parent.get(parent.id, [])
            if not own_juveniles:
                continue
            surplus = max(0.0, parent.energy - reserve)
            budget = min(transfer_capacity, surplus)
            if budget <= 0.0:
                continue

            candidates: list[Individual] = []
            weights: list[float] = []
            for juvenile in own_juveniles:
                if juvenile.energy >= max_e:
                    continue
                distance = self._toroidal_distance(parent, juvenile)
                if radius > 0.0 and distance > radius:
                    continue
                proximity_w = max(0.05, 1.0 - distance / radius) if radius > 0.0 else 1.0
                household_w = (
                    1.0 + household_bonus
                    if parent.household_id == juvenile.household_id
                    else 1.0
                )
                candidates.append(juvenile)
                weights.append(proximity_w * household_w)

            if not candidates:
                continue
            weights_arr = np.array(weights, dtype=float)
            total_weight = float(weights_arr.sum())
            if total_weight <= 0.0:
                continue

            for juvenile, weight in zip(candidates, weights_arr):
                amount = budget * float(weight) / total_weight
                accepted = min(amount, max(0.0, max_e - juvenile.energy))
                if accepted <= 0.0:
                    continue
                juvenile.energy += accepted
                parent.energy -= accepted
                food_by_juvenile[juvenile.id] += accepted
                total_transfer += accepted

        self.last_parent_food_transfer = total_transfer
        self.last_parent_food_by_juvenile = dict(food_by_juvenile)
        self.last_fed_juvenile_count = len(food_by_juvenile)
        self.last_fed_juvenile_fraction = len(food_by_juvenile) / len(juveniles)

    # ------------------------------------------------------------------
    # Lifetime movement
    # ------------------------------------------------------------------

    def _move_individuals(self) -> None:
        """Move living agents by random walk plus household and band attraction."""
        width = float(self.config["space_width"])
        movement_std = {
            STAGE_JUVENILE: float(self.config["juvenile_movement_step_std"]),
            STAGE_SUBADULT: float(self.config["subadult_movement_step_std"]),
            STAGE_ADULT: float(self.config["adult_movement_step_std"]),
            STAGE_ELDER: float(self.config["elder_movement_step_std"]),
        }
        household_attraction = {
            STAGE_JUVENILE: float(self.config["juvenile_household_attraction"]),
            STAGE_SUBADULT: float(self.config["subadult_household_attraction"]),
            STAGE_ADULT: float(self.config["adult_household_attraction"]),
            STAGE_ELDER: float(self.config["elder_household_attraction"]),
        }

        for ind in self.individuals:
            step_std = movement_std[ind.stage]
            if step_std > 0.0:
                ind.x = (ind.x + float(self.rng.normal(0.0, step_std))) % width
                ind.y = (ind.y + float(self.rng.normal(0.0, step_std))) % width
            household = self.households.get(ind.household_id)
            attraction = household_attraction[ind.stage]
            if household is not None and attraction > 0.0:
                self._move_individual_toward(ind, household.x, household.y, attraction)
            band = self.bands.get(ind.group_id)
            band_attraction = float(self.config["band_member_attraction"])
            if band is not None and band_attraction > 0.0:
                dist = self._toroidal_distance_to_xy(ind.x, ind.y, band.x, band.y)
                if dist > band.radius:
                    self._move_individual_toward(ind, band.x, band.y, band_attraction)

    def _move_individual_toward(
        self,
        ind: Individual,
        target_x: float,
        target_y: float,
        fraction: float,
    ) -> None:
        width = float(self.config["space_width"])
        dx = self._toroidal_delta(ind.x, target_x)
        dy = self._toroidal_delta(ind.y, target_y)
        ind.x = (ind.x + dx * fraction) % width
        ind.y = (ind.y + dy * fraction) % width

    def _move_household_toward(
        self,
        household: Household,
        target_x: float,
        target_y: float,
        fraction: float,
    ) -> None:
        width = float(self.config["space_width"])
        dx = self._toroidal_delta(household.x, target_x)
        dy = self._toroidal_delta(household.y, target_y)
        household.x = (household.x + dx * fraction) % width
        household.y = (household.y + dy * fraction) % width

    def _move_band_toward(
        self,
        band: Band,
        target_x: float,
        target_y: float,
        fraction: float,
    ) -> None:
        width = float(self.config["space_width"])
        dx = self._toroidal_delta(band.x, target_x)
        dy = self._toroidal_delta(band.y, target_y)
        band.x = (band.x + dx * fraction) % width
        band.y = (band.y + dy * fraction) % width

    def _toroidal_delta(self, origin: float, target: float) -> float:
        width = float(self.config["space_width"])
        delta = target - origin
        if abs(delta) > width / 2.0:
            delta -= math.copysign(width, delta)
        return delta

    def _toroidal_mean_position(self, members: list[Individual]) -> tuple[float, float]:
        width = float(self.config["space_width"])
        angles_x = np.array([i.x / width * 2.0 * math.pi for i in members])
        angles_y = np.array([i.y / width * 2.0 * math.pi for i in members])
        mean_x = math.atan2(float(np.sin(angles_x).mean()), float(np.cos(angles_x).mean()))
        mean_y = math.atan2(float(np.sin(angles_y).mean()), float(np.cos(angles_y).mean()))
        if mean_x < 0.0:
            mean_x += 2.0 * math.pi
        if mean_y < 0.0:
            mean_y += 2.0 * math.pi
        return mean_x / (2.0 * math.pi) * width, mean_y / (2.0 * math.pi) * width

    def _update_household_residences(self) -> None:
        update_weight = float(self.config["household_residence_update_weight"])
        if update_weight <= 0.0:
            return

        by_household: dict[int, list[Individual]] = defaultdict(list)
        for ind in self.individuals:
            if ind.household_id in self.households:
                by_household[ind.household_id].append(ind)

        for household_id, members in by_household.items():
            household = self.households[household_id]
            anchors = [i for i in members if i.stage in {STAGE_ADULT, STAGE_ELDER}]
            if not anchors:
                anchors = members
            target_x, target_y = self._toroidal_mean_position(anchors)
            self._move_household_toward(household, target_x, target_y, update_weight)

    # ------------------------------------------------------------------
    # Band territory, migration, and fission/fusion
    # ------------------------------------------------------------------

    def _band_members(self) -> dict[int, list[Individual]]:
        by_band: dict[int, list[Individual]] = {band_id: [] for band_id in self.bands}
        for ind in self.individuals:
            by_band.setdefault(ind.group_id, []).append(ind)
        return by_band

    def _update_band_territories(self) -> None:
        update_weight = float(self.config["band_territory_update_weight"])
        if update_weight <= 0.0:
            return

        by_band = self._band_members()
        for band_id, band in self.bands.items():
            members = by_band.get(band_id, [])
            if not members:
                continue
            anchors = [i for i in members if i.stage in {STAGE_SUBADULT, STAGE_ADULT, STAGE_ELDER}]
            if not anchors:
                anchors = members
            target_x, target_y = self._toroidal_mean_position(anchors)
            self._move_band_toward(band, target_x, target_y, update_weight)

    def _migrate_between_bands(self) -> None:
        migration_prob = float(self.config["group_migration_probability"])
        if migration_prob <= 0.0 or len(self.bands) < 2:
            return
        min_age = int(self.config["band_migration_min_age"])
        by_band = self._band_members()
        band_sizes = {band_id: len(members) for band_id, members in by_band.items()}

        for ind in self.individuals:
            if ind.age < min_age:
                continue
            if self.rng.random() > migration_prob:
                continue
            target = self._choose_migration_band(ind, band_sizes)
            if target is None or target == ind.group_id:
                continue
            old_band = ind.group_id
            ind.group_id = target
            self.last_band_migrations += 1
            self.total_band_migrations += 1
            band_sizes[target] = band_sizes.get(target, 0) + 1
            band_sizes[old_band] = max(0, band_sizes.get(old_band, 0) - 1)

    def _choose_migration_band(
        self,
        ind: Individual,
        band_sizes: Mapping[int, int],
    ) -> int | None:
        candidates = [band for band in self.bands.values() if band.id != ind.group_id]
        if not candidates:
            return None
        weights = []
        for band in candidates:
            dist = self._toroidal_distance_to_xy(ind.x, ind.y, band.x, band.y)
            distance_w = math.exp(-dist / max(1.0, band.radius))
            size_w = 1.0 / math.sqrt(1.0 + band_sizes.get(band.id, 0))
            weights.append(distance_w * size_w)
        total = float(sum(weights))
        if total <= 0.0:
            return int(candidates[int(self.rng.integers(0, len(candidates)))].id)
        idx = int(self.rng.choice(len(candidates), p=np.array(weights, dtype=float) / total))
        return candidates[idx].id

    def _update_band_dynamics(self) -> None:
        self._prune_empty_bands()
        fission_interval = int(self.config["band_fission_interval"])
        if fission_interval > 0 and self.step_index % fission_interval == 0:
            self._apply_band_fissions()
        fusion_interval = int(self.config["band_fusion_interval"])
        if fusion_interval > 0 and self.step_index % fusion_interval == 0:
            self._apply_band_fusions()
        self._prune_empty_bands()

    def _prune_empty_bands(self) -> None:
        if len(self.bands) <= 1:
            return
        live_band_ids = {i.group_id for i in self.individuals}
        for band_id in list(self.bands):
            if len(self.bands) <= 1:
                break
            if band_id not in live_band_ids:
                del self.bands[band_id]

    def _apply_band_fissions(self) -> None:
        threshold = int(self.config["band_fission_size_threshold"])
        min_size = int(self.config["band_fission_min_size"])
        dispersal = float(self.config["band_fission_dispersal_std"])
        width = float(self.config["space_width"])
        by_band = self._band_members()
        for band_id in list(self.bands):
            members = by_band.get(band_id, [])
            if len(members) < threshold:
                continue
            n_move = max(min_size, len(members) // 3)
            n_move = min(n_move, len(members) - min_size)
            if n_move < min_size:
                continue

            source = self.bands[band_id]
            angle = float(self.rng.uniform(0.0, 2.0 * math.pi))
            daughter_x = (source.x + math.cos(angle) * dispersal) % width
            daughter_y = (source.y + math.sin(angle) * dispersal) % width
            daughter_id = self._create_band(daughter_x, daughter_y, source.radius)

            ranked = sorted(
                members,
                key=lambda ind: self._toroidal_distance_to_xy(ind.x, ind.y, source.x, source.y),
                reverse=True,
            )
            for ind in ranked[:n_move]:
                ind.group_id = daughter_id
            self.last_band_fissions += 1
            self.total_band_fissions += 1

    def _apply_band_fusions(self) -> None:
        threshold = int(self.config["band_fusion_size_threshold"])
        max_distance = float(self.config["band_fusion_distance"])
        for band_id in list(self.bands):
            if len(self.bands) <= 1 or band_id not in self.bands:
                continue
            members = [i for i in self.individuals if i.group_id == band_id]
            if len(members) > threshold:
                continue
            target_id = self._nearest_band_id(band_id, max_distance=max_distance)
            if target_id is None:
                continue
            for ind in members:
                ind.group_id = target_id
            del self.bands[band_id]
            self.last_band_fusions += 1
            self.total_band_fusions += 1

    def _nearest_band_id(self, band_id: int, *, max_distance: float | None = None) -> int | None:
        source = self.bands.get(band_id)
        if source is None:
            return None
        nearest_id: int | None = None
        nearest_distance = math.inf
        for candidate in self.bands.values():
            if candidate.id == band_id:
                continue
            dist = self._toroidal_distance_to_xy(source.x, source.y, candidate.x, candidate.y)
            if max_distance is not None and dist > max_distance:
                continue
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_id = candidate.id
        return nearest_id

    # ------------------------------------------------------------------
    # Kin index (built once per step from pedigree)
    # ------------------------------------------------------------------

    def _build_kin_index(self) -> dict[int, list[Individual]]:
        """Return mapping: adult_id -> list of adult kin (siblings, parents, offspring)."""
        active = [i for i in self.individuals if i.stage in {STAGE_ADULT, STAGE_ELDER}]
        active_ids = {i.id for i in active}
        id_to_ind = {i.id: i for i in active}

        by_mother: dict[int, list[Individual]] = defaultdict(list)
        by_father: dict[int, list[Individual]] = defaultdict(list)
        for ind in active:
            if ind.mother_id is not None:
                by_mother[ind.mother_id].append(ind)
            if ind.father_id is not None:
                by_father[ind.father_id].append(ind)

        result: dict[int, list[Individual]] = {}
        for ind in active:
            kin: set[int] = set()
            if ind.mother_id is not None:
                for s in by_mother[ind.mother_id]:
                    kin.add(s.id)
            if ind.father_id is not None:
                for s in by_father[ind.father_id]:
                    kin.add(s.id)
            if ind.mother_id in active_ids:
                kin.add(ind.mother_id)  # type: ignore[arg-type]
            if ind.father_id in active_ids:
                kin.add(ind.father_id)  # type: ignore[arg-type]
            for child in by_mother.get(ind.id, []):
                kin.add(child.id)
            for child in by_father.get(ind.id, []):
                kin.add(child.id)
            kin.discard(ind.id)
            result[ind.id] = [id_to_ind[k] for k in kin if k in id_to_ind]
        return result

    # ------------------------------------------------------------------
    # Spatial index (per-step, used in interactions and reproduction)
    # ------------------------------------------------------------------

    def _build_spatial_index(self, active: list[Individual]) -> dict[int, list[Individual]]:
        """Return mapping: adult_id -> list of adults within interaction_radius."""
        if len(active) < 2:
            return {}
        radius = float(self.config["interaction_radius"])
        width = float(self.config["space_width"])

        xs = np.array([i.x for i in active])
        ys = np.array([i.y for i in active])
        dx = np.abs(xs[:, np.newaxis] - xs[np.newaxis, :])
        dy = np.abs(ys[:, np.newaxis] - ys[np.newaxis, :])
        dx = np.minimum(dx, width - dx)
        dy = np.minimum(dy, width - dy)
        dist = np.sqrt(dx * dx + dy * dy)

        result: dict[int, list[Individual]] = {}
        for i, ind in enumerate(active):
            neighbors = [active[j] for j in np.where((dist[i] <= radius) & (dist[i] > 0))[0]]
            result[ind.id] = neighbors
        return result

    def _toroidal_distance(self, a: Individual, b: Individual) -> float:
        return self._toroidal_distance_to_xy(a.x, a.y, b.x, b.y)

    def _toroidal_distance_to_xy(
        self,
        ax: float,
        ay: float,
        bx: float,
        by: float,
    ) -> float:
        width = float(self.config["space_width"])
        dx = abs(ax - bx)
        dy = abs(ay - by)
        dx = min(dx, width - dx)
        dy = min(dy, width - dy)
        return math.sqrt(dx * dx + dy * dy)

    # ------------------------------------------------------------------
    # Spouse bonds (persistent co-parent pair bonds)
    # ------------------------------------------------------------------

    def _form_spouse_bond(self, a: Individual, b: Individual) -> bool:
        if a.id == b.id:
            return False
        if self.rng.random() > float(self.config["spouse_bond_probability"]):
            return False

        by_id = {i.id: i for i in self.individuals}
        by_id[a.id] = a
        by_id[b.id] = b

        for person, new_spouse in ((a, b), (b, a)):
            old_spouse_id = person.spouse_id
            if old_spouse_id is None or old_spouse_id == new_spouse.id:
                continue
            old_spouse = by_id.get(old_spouse_id)
            if old_spouse is not None and old_spouse.spouse_id == person.id:
                return False
            person.spouse_id = None

        a.spouse_id = b.id
        b.spouse_id = a.id
        return True

    def _try_form_spouse_reciprocity_bond(self, a: Individual, b: Individual) -> bool:
        if a.reciprocity_bond_id == b.id and b.reciprocity_bond_id == a.id:
            return True
        if a.reciprocity_bond_id is not None or b.reciprocity_bond_id is not None:
            return False
        if self.rng.random() > float(self.config["spouse_reciprocity_bond_probability"]):
            return False
        if self._toroidal_distance(a, b) > float(self.config["spouse_reciprocity_bond_radius"]):
            return False
        a.reciprocity_bond_id = b.id
        b.reciprocity_bond_id = a.id
        a.reciprocity_bond_memory = 1.0
        b.reciprocity_bond_memory = 1.0
        return True

    def _clear_dead_spouse_bonds(self) -> None:
        alive_ids = {i.id for i in self.individuals}
        by_id = {i.id: i for i in self.individuals}
        for ind in self.individuals:
            if ind.spouse_id is None:
                continue
            spouse = by_id.get(ind.spouse_id)
            if spouse is None or spouse.id not in alive_ids or spouse.spouse_id != ind.id:
                ind.spouse_id = None

    # ------------------------------------------------------------------
    # Direct reciprocity: reciprocity-bond management
    # ------------------------------------------------------------------

    def _update_reciprocity_bonds(self) -> None:
        """Dissolve low-quality bonds; match unbonded adults into new pairs."""
        base_p = float(self.config["reciprocity_bond_persistence_probability"])
        formation_radius = float(self.config["reciprocity_bond_formation_radius"])
        dissolution_radius = float(self.config["reciprocity_bond_dissolution_radius"])
        leave_w = float(self.config["leave_weight"])
        spouse_persistence = float(self.config["spouse_reciprocity_bond_persistence_probability"])

        active = {i.id: i for i in self.individuals if i.stage in {STAGE_ADULT, STAGE_ELDER}}

        # Dissolve reciprocity bonds.
        dissolved: set[int] = set()
        for ind in active.values():
            if ind.reciprocity_bond_id is None:
                continue
            if ind.id in dissolved:
                continue
            bondmate = active.get(ind.reciprocity_bond_id)
            if bondmate is None:
                ind.reciprocity_bond_id = None
                continue
            distance = self._toroidal_distance(ind, bondmate)
            effective_p = base_p * max(
                0.0,
                1.0 - leave_w * (1.0 - ind.reciprocity_bond_memory),
            )
            if ind.spouse_id == bondmate.id and bondmate.spouse_id == ind.id:
                effective_p = max(effective_p, spouse_persistence)
            if distance > dissolution_radius or self.rng.random() > effective_p:
                ind.reciprocity_bond_id = None
                bondmate.reciprocity_bond_id = None
                dissolved.add(ind.id)
                dissolved.add(bondmate.id)

        # Match newly unbonded adults into new pairs.
        if base_p > 0.0:
            self._match_spouse_reciprocity_bonds(active)
            unbonded = [i for i in active.values() if i.reciprocity_bond_id is None]
            self.rng.shuffle(unbonded)  # type: ignore[arg-type]
            available = {i.id: i for i in unbonded}
            for a in unbonded:
                if a.id not in available:
                    continue
                candidates = [
                    b for b in available.values()
                    if b.id != a.id and self._toroidal_distance(a, b) <= formation_radius
                ]
                if not candidates:
                    continue
                b = candidates[int(self.rng.integers(0, len(candidates)))]
                a.reciprocity_bond_id = b.id
                b.reciprocity_bond_id = a.id
                a.reciprocity_bond_memory = 1.0
                b.reciprocity_bond_memory = 1.0
                del available[a.id]
                del available[b.id]

    def _match_spouse_reciprocity_bonds(self, active: Mapping[int, Individual]) -> None:
        pairs: list[tuple[Individual, Individual]] = []
        seen: set[frozenset[int]] = set()
        for ind in active.values():
            if ind.spouse_id is None or ind.reciprocity_bond_id is not None:
                continue
            spouse = active.get(ind.spouse_id)
            if (
                spouse is None
                or spouse.spouse_id != ind.id
                or spouse.reciprocity_bond_id is not None
            ):
                continue
            key = frozenset((ind.id, spouse.id))
            if key in seen:
                continue
            seen.add(key)
            pairs.append((ind, spouse))

        self.rng.shuffle(pairs)  # type: ignore[arg-type]
        for a, b in pairs:
            if a.reciprocity_bond_id is None and b.reciprocity_bond_id is None:
                self._try_form_spouse_reciprocity_bond(a, b)

    def _clear_dead_reciprocity_bonds(self) -> None:
        alive_ids = {i.id for i in self.individuals}
        for ind in self.individuals:
            if (
                ind.reciprocity_bond_id is not None
                and ind.reciprocity_bond_id not in alive_ids
            ):
                ind.reciprocity_bond_id = None

    # ------------------------------------------------------------------
    # Interactions (all five routing channels)
    # ------------------------------------------------------------------

    def _conduct_interactions(self) -> None:
        """Per-step energy routing through six combined channels.

        Bonded adults use direct reciprocity (interact with their bondmate).
        Unbonded adults use layered priority: kin → spatial → group → random.
        Reputation gating is applied on top of the selected recipient for
        non-bond interactions (unless random_benefit_routing=True).
        """
        q = float(self.config["reputation_observation_prob"])
        threshold = float(self.config["reputation_threshold"])
        benefit = float(self.config["cooperation_benefit_per_step"])
        update_weight = float(self.config["reputation_update_weight"])
        max_e = float(self.config["max_energy"])
        random_routing = bool(self.config["random_benefit_routing"])
        rw = float(self.config["reciprocity_weight"])
        kin_bias = float(self.config["kin_bias"])
        spatial_bias = float(self.config["spatial_bias"])
        group_bias = float(self.config["group_bias"])
        self.last_helping_events = 0
        self.last_helping_opportunities = 0
        self.last_realized_helping_rate = math.nan

        active = [i for i in self.individuals if i.stage in {STAGE_ADULT, STAGE_ELDER}]
        if len(active) < 2:
            return

        id_to_ind = {i.id: i for i in active}
        by_group: dict[int, list[Individual]] = defaultdict(list)
        for ind in active:
            by_group[ind.group_id].append(ind)
        spatial_neighbors = self._build_spatial_index(active)

        help_count: dict[int, int] = {i.id: 0 for i in active}
        eligible_count: dict[int, int] = {i.id: 0 for i in active}
        bondmate_helped_me: dict[int, bool] = {}

        for donor in active:
            # --- Direct reciprocity (bonded) ---
            if donor.reciprocity_bond_id is not None:
                bondmate = id_to_ind.get(donor.reciprocity_bond_id)
                if bondmate is not None:
                    eff = self._effective_helping(donor) * max(
                        0.0,
                        1.0 - rw * (1.0 - donor.reciprocity_bond_memory),
                    )
                    eligible_count[donor.id] += 1
                    if self.rng.random() < eff:
                        bondmate.energy = min(max_e, bondmate.energy + benefit)
                        help_count[donor.id] += 1
                        bondmate_helped_me[bondmate.id] = True
                    continue

            # --- Unbonded: layered recipient selection ---
            all_others = [m for m in active if m.id != donor.id]
            candidates: list[Individual] | None = None

            if kin_bias > 0.0:
                kin = self._kin_index.get(donor.id, [])
                if kin and self.rng.random() < kin_bias:
                    candidates = kin

            if candidates is None and spatial_bias > 0.0:
                nearby = spatial_neighbors.get(donor.id, [])
                if nearby and self.rng.random() < spatial_bias:
                    candidates = nearby

            if candidates is None and group_bias > 0.0:
                in_group = [m for m in by_group[donor.group_id] if m.id != donor.id]
                if in_group and self.rng.random() < group_bias:
                    candidates = in_group

            if candidates is None:
                candidates = all_others
            if not candidates:
                continue

            recipient = candidates[int(self.rng.integers(0, len(candidates)))]

            if random_routing:
                eligible_count[donor.id] += 1
                if self.rng.random() < self._effective_helping(donor):
                    recipient.energy = min(max_e, recipient.energy + benefit)
                    help_count[donor.id] += 1
            else:
                if self.rng.random() < q:
                    if recipient.reputation >= threshold:
                        eligible_count[donor.id] += 1
                        if self.rng.random() < self._effective_helping(donor):
                            recipient.energy = min(max_e, recipient.energy + benefit)
                            help_count[donor.id] += 1

        # Update reciprocity-bond memories.
        smoothing = float(self.config["memory_smoothing"])
        for ind in active:
            if ind.reciprocity_bond_id is not None:
                got_helped = bondmate_helped_me.get(ind.id, False)
                ind.reciprocity_bond_memory = clamp01(
                    (1.0 - smoothing) * ind.reciprocity_bond_memory
                    + smoothing * float(got_helped)
                )

        # Update reputations.
        for ind in active:
            n = eligible_count[ind.id]
            if n > 0:
                ind.reputation = clamp01(
                    (1.0 - update_weight) * ind.reputation
                    + update_weight * (help_count[ind.id] / n)
                )

        self.last_helping_events = sum(help_count.values())
        self.last_helping_opportunities = sum(eligible_count.values())
        if self.last_helping_opportunities > 0:
            self.last_realized_helping_rate = (
                self.last_helping_events / self.last_helping_opportunities
            )

    # ------------------------------------------------------------------
    # Norm enforcement and social learning
    # ------------------------------------------------------------------

    def _apply_norm_enforcement(self) -> None:
        strength = float(self.config["norm_enforcement_strength"])
        if strength <= 0.0:
            return
        penalty = float(self.config["norm_violation_penalty"])
        sensitivity = float(self.config["norm_detection_sensitivity"])
        adults = [i for i in self.individuals if i.stage in {STAGE_ADULT, STAGE_ELDER}]
        if not adults:
            return
        mean_rep = float(np.mean([i.reputation for i in adults]))
        floor = mean_rep - sensitivity
        for ind in adults:
            if ind.reputation < floor:
                ind.energy -= penalty * strength

    def _apply_social_learning(self) -> None:
        probability = float(self.config["social_learning_probability"])
        if probability <= 0.0:
            self.last_social_learning_events = 0
            self.last_mean_learned_helping_adjustment = self._mean_learned_helping_adjustment()
            self.last_mean_effective_helping = self._mean_effective_helping()
            return

        radius = float(self.config["social_learning_radius"])
        rate = float(self.config["social_learning_rate"])
        reputation_w = float(self.config["social_learning_reputation_weight"])
        success_w = float(self.config["social_learning_success_weight"])
        max_adjustment = float(self.config["social_learning_max_adjustment"])
        max_e = float(self.config["max_energy"])
        learners = [
            i for i in self.individuals
            if i.stage in {STAGE_SUBADULT, STAGE_ADULT, STAGE_ELDER}
        ]
        demonstrators = [
            i for i in learners
            if i.stage in {STAGE_ADULT, STAGE_ELDER}
        ]
        events = 0
        if rate <= 0.0 or max_adjustment <= 0.0 or len(demonstrators) < 2:
            self.last_social_learning_events = 0
            self.last_mean_learned_helping_adjustment = self._mean_learned_helping_adjustment()
            self.last_mean_effective_helping = self._mean_effective_helping()
            return

        for learner in learners:
            if self.rng.random() > probability:
                continue
            candidates: list[Individual] = []
            weights: list[float] = []
            for demonstrator in demonstrators:
                if demonstrator.id == learner.id:
                    continue
                if radius > 0.0 and self._toroidal_distance(learner, demonstrator) > radius:
                    continue
                reputation_score = max(0.0, demonstrator.reputation)
                success_score = max(0.0, demonstrator.energy) / max(1.0, max_e)
                weight = (
                    1.0
                    + reputation_w * reputation_score
                    + success_w * min(1.0, success_score)
                )
                if weight <= 0.0:
                    continue
                candidates.append(demonstrator)
                weights.append(weight)
            if not candidates:
                continue

            weights_arr = np.array(weights, dtype=float)
            demonstrator = candidates[
                int(self.rng.choice(len(candidates), p=weights_arr / float(weights_arr.sum())))
            ]
            target = self._effective_helping(demonstrator)
            current = self._effective_helping(learner)
            learner.learned_helping_adjustment += rate * (target - current)
            learner.learned_helping_adjustment = max(
                -max_adjustment,
                min(max_adjustment, learner.learned_helping_adjustment),
            )
            events += 1

        self.last_social_learning_events = events
        self.last_mean_learned_helping_adjustment = self._mean_learned_helping_adjustment()
        self.last_mean_effective_helping = self._mean_effective_helping()

    # ------------------------------------------------------------------
    # Band selection: inter-band conflict
    # ------------------------------------------------------------------

    def _apply_group_conflict(self) -> None:
        """Two bands compete: higher mean effective helping wins an energy transfer."""
        winner_bonus = float(self.config["conflict_winner_bonus"])
        loser_penalty = float(self.config["conflict_loser_penalty"])

        by_group: dict[int, list[Individual]] = defaultdict(list)
        for ind in self.individuals:
            if ind.stage in {STAGE_ADULT, STAGE_ELDER}:
                by_group[ind.group_id].append(ind)

        populated = [g for g, members in by_group.items() if len(members) >= 2]
        if len(populated) < 2:
            return

        idxs = self.rng.choice(len(populated), size=2, replace=False)
        g1, g2 = populated[int(idxs[0])], populated[int(idxs[1])]
        m1 = float(np.mean([self._effective_helping(i) for i in by_group[g1]]))
        m2 = float(np.mean([self._effective_helping(i) for i in by_group[g2]]))

        if m1 >= m2:
            winner, loser = by_group[g1], by_group[g2]
        else:
            winner, loser = by_group[g2], by_group[g1]

        for ind in winner:
            ind.energy = min(float(self.config["max_energy"]), ind.energy + winner_bonus)
        for ind in loser:
            ind.energy -= loser_penalty

    # ------------------------------------------------------------------
    # Child rearing
    # ------------------------------------------------------------------

    def _provide_child_rearing(self) -> dict[int, float]:
        """Adults and elders invest costly care in nearby juveniles.

        The amount a helper can invest is proportional to its helping trait.
        Recipient choice is local, then weighted toward parent-child and other
        close kin relations. The returned map is consumed by juvenile survival.
        """
        self.last_total_child_rearing_care = 0.0
        self.last_mean_child_rearing_care = 0.0
        self.last_mean_child_rearing_relatedness = math.nan
        self.last_kin_child_rearing_fraction = math.nan
        self.last_parent_child_rearing_fraction = math.nan
        self.last_household_child_rearing_fraction = math.nan
        self.last_spouse_child_rearing_fraction = math.nan
        self.last_coparent_near_child_rearing_fraction = math.nan
        self.last_child_care_by_juvenile = {}
        self.last_cared_juvenile_count = 0
        self.last_cared_juvenile_fraction = math.nan

        radius = float(self.config["child_rearing_radius"])
        capacity = float(self.config["child_rearing_care_capacity_per_helper"])
        if radius <= 0.0 or capacity <= 0.0:
            return {}

        juveniles = [i for i in self.individuals if i.stage == STAGE_JUVENILE]
        helpers = [
            i for i in self.individuals
            if i.stage in {STAGE_ADULT, STAGE_ELDER}
            and i.energy > float(self.config["child_rearing_helper_energy_reserve"])
        ]
        if not juveniles or not helpers:
            return {}

        by_id = {i.id: i for i in self.individuals}
        cost_per_care = float(self.config["child_rearing_cost_per_care"])
        reserve = float(self.config["child_rearing_helper_energy_reserve"])
        baseline_w = float(self.config["child_rearing_baseline_weight"])
        parent_bonus = float(self.config["child_rearing_parent_weight_bonus"])
        kin_bonus = float(self.config["child_rearing_kin_weight_bonus"])
        household_bonus = float(self.config["child_rearing_household_member_weight_bonus"])
        spouse_parent_bonus = float(self.config["child_rearing_spouse_parent_weight_bonus"])
        coparent_near_bonus = float(self.config["child_rearing_coparent_near_weight_bonus"])

        care_by_juvenile: dict[int, float] = defaultdict(float)
        total_care = 0.0
        kin_care = 0.0
        parent_care = 0.0
        household_care = 0.0
        spouse_parent_care = 0.0
        coparent_near_care = 0.0
        weighted_relatedness = 0.0

        for helper in helpers:
            care_budget = self._effective_helping(helper) * capacity
            if care_budget <= 0.0:
                continue
            if cost_per_care > 0.0:
                affordable_care = max(0.0, (helper.energy - reserve) / cost_per_care)
                care_budget = min(care_budget, affordable_care)
            if care_budget <= 0.0:
                continue

            candidates: list[Individual] = []
            weights: list[float] = []
            relatednesses: list[float] = []
            parent_flags: list[bool] = []
            household_flags: list[bool] = []
            spouse_parent_flags: list[bool] = []
            coparent_near_flags: list[bool] = []

            for juvenile in juveniles:
                distance = self._toroidal_distance(helper, juvenile)
                if distance > radius:
                    continue
                relatedness, is_parent = self._child_care_relatedness(helper, juvenile, by_id)
                spouse_is_parent = (
                    helper.spouse_id is not None
                    and helper.spouse_id in {juvenile.mother_id, juvenile.father_id}
                )
                same_household = helper.household_id == juvenile.household_id
                spouse = by_id.get(helper.spouse_id) if helper.spouse_id is not None else None
                coparent_near = (
                    is_parent
                    and spouse_is_parent
                    and spouse is not None
                    and self._toroidal_distance(spouse, juvenile) <= radius
                )
                proximity_w = max(0.05, 1.0 - distance / radius)
                weight = (
                    baseline_w
                    + kin_bonus * relatedness
                    + (parent_bonus if is_parent else 0.0)
                    + (household_bonus if same_household else 0.0)
                    + (spouse_parent_bonus if spouse_is_parent else 0.0)
                    + (coparent_near_bonus if coparent_near else 0.0)
                ) * proximity_w
                if weight <= 0.0:
                    continue
                candidates.append(juvenile)
                weights.append(weight)
                relatednesses.append(relatedness)
                parent_flags.append(is_parent)
                household_flags.append(same_household)
                spouse_parent_flags.append(spouse_is_parent)
                coparent_near_flags.append(coparent_near)

            if not candidates:
                continue

            weights_arr = np.array(weights, dtype=float)
            total_weight = float(weights_arr.sum())
            if total_weight <= 0.0:
                continue
            idx = int(self.rng.choice(len(candidates), p=weights_arr / total_weight))
            recipient = candidates[idx]
            relatedness = relatednesses[idx]
            is_parent = parent_flags[idx]
            same_household = household_flags[idx]
            spouse_is_parent = spouse_parent_flags[idx]
            coparent_near = coparent_near_flags[idx]

            care_by_juvenile[recipient.id] += care_budget
            helper.energy -= care_budget * cost_per_care
            total_care += care_budget
            weighted_relatedness += care_budget * relatedness
            if relatedness > 0.0:
                kin_care += care_budget
            if is_parent:
                parent_care += care_budget
            if same_household:
                household_care += care_budget
            if spouse_is_parent:
                spouse_parent_care += care_budget
            if coparent_near:
                coparent_near_care += care_budget

        self.last_total_child_rearing_care = total_care
        self.last_mean_child_rearing_care = total_care / len(juveniles)
        self.last_child_care_by_juvenile = dict(care_by_juvenile)
        self.last_cared_juvenile_count = len(care_by_juvenile)
        self.last_cared_juvenile_fraction = len(care_by_juvenile) / len(juveniles)
        if total_care > 0.0:
            self.last_mean_child_rearing_relatedness = weighted_relatedness / total_care
            self.last_kin_child_rearing_fraction = kin_care / total_care
            self.last_parent_child_rearing_fraction = parent_care / total_care
            self.last_household_child_rearing_fraction = household_care / total_care
            self.last_spouse_child_rearing_fraction = spouse_parent_care / total_care
            self.last_coparent_near_child_rearing_fraction = coparent_near_care / total_care
        return dict(care_by_juvenile)

    def _child_care_relatedness(
        self,
        helper: Individual,
        juvenile: Individual,
        by_id: Mapping[int, Individual],
    ) -> tuple[float, bool]:
        """Approximate pedigree relatedness used for child-care allocation."""
        juvenile_parents = {
            parent_id
            for parent_id in (juvenile.mother_id, juvenile.father_id)
            if parent_id is not None
        }
        if helper.id in juvenile_parents:
            return 0.5, True

        relatedness = 0.0
        helper_parents = {
            parent_id
            for parent_id in (helper.mother_id, helper.father_id)
            if parent_id is not None
        }
        shared_parent_count = len(helper_parents & juvenile_parents)
        if shared_parent_count >= 2:
            relatedness = max(relatedness, 0.5)
        elif shared_parent_count == 1:
            relatedness = max(relatedness, 0.25)

        for parent_id in juvenile_parents:
            parent = by_id.get(parent_id)
            if parent is None:
                continue
            grandparent_ids = {
                grandparent_id
                for grandparent_id in (parent.mother_id, parent.father_id)
                if grandparent_id is not None
            }
            if helper.id in grandparent_ids:
                relatedness = max(relatedness, 0.25)

        return relatedness, False

    # ------------------------------------------------------------------
    # Survival
    # ------------------------------------------------------------------

    def _apply_survival(self, care_by_juvenile: Mapping[int, float]) -> int:
        adult_s = float(self.config["adult_survival_probability"])
        subadult_s = float(self.config["subadult_survival_probability"])
        elder_s = float(self.config["elder_survival_probability"])
        juv_s = float(self.config["base_juvenile_survival_probability"])
        care_benefit = float(self.config["child_rearing_survival_benefit"])
        care_saturation = float(self.config["child_rearing_saturation"])
        food_benefit = float(self.config["juvenile_food_survival_benefit"])
        food_saturation = float(self.config["juvenile_food_survival_saturation"])
        no_food_penalty = float(self.config["juvenile_no_food_survival_penalty"])
        max_age = int(self.config["max_age"])
        density_scale = self._density_survival_scale()
        survivors = []
        deaths = 0
        juvenile_trials = 0
        juvenile_survivors = 0
        food_survival_effect_total = 0.0
        household_bonus_total = 0.0
        two_living_parent_count = 0
        household_caregiver_count = 0
        by_id = {i.id: i for i in self.individuals}
        caregivers_by_household: dict[int, list[Individual]] = defaultdict(list)
        for caregiver in self.individuals:
            if (
                caregiver.stage in {STAGE_ADULT, STAGE_ELDER}
                and caregiver.energy > 0.0
                and caregiver.household_id in self.households
            ):
                caregivers_by_household[caregiver.household_id].append(caregiver)

        for ind in self.individuals:
            is_juvenile = ind.stage == STAGE_JUVENILE
            if is_juvenile:
                juvenile_trials += 1
            if ind.age >= max_age or ind.energy <= 0.0:
                deaths += 1
                continue
            if is_juvenile:
                care = max(0.0, float(care_by_juvenile.get(ind.id, 0.0)))
                if care_saturation > 0.0:
                    care_bonus = care_benefit * (care / (care + care_saturation))
                else:
                    care_bonus = care_benefit if care > 0.0 else 0.0
                food = max(0.0, float(self.last_parent_food_by_juvenile.get(ind.id, 0.0)))
                if food_saturation > 0.0:
                    fed_fraction = food / (food + food_saturation)
                else:
                    fed_fraction = 1.0 if food > 0.0 else 0.0
                food_effect = food_benefit * fed_fraction - no_food_penalty * (1.0 - fed_fraction)
                food_survival_effect_total += food_effect
                household_bonus, living_parents, household_caregivers = (
                    self._household_juvenile_survival_bonus(
                        ind,
                        by_id,
                        caregivers_by_household,
                    )
                )
                household_bonus_total += household_bonus
                if living_parents >= 2:
                    two_living_parent_count += 1
                if household_caregivers > 0:
                    household_caregiver_count += 1
                survival_p = clamp01(
                    (juv_s + care_bonus + household_bonus + food_effect) * density_scale
                )
                if self.rng.random() > survival_p:
                    deaths += 1
                    continue
            elif ind.stage == STAGE_SUBADULT:
                if self.rng.random() > subadult_s * density_scale:
                    deaths += 1
                    continue
            elif ind.stage == STAGE_ADULT:
                if self.rng.random() > adult_s * density_scale:
                    deaths += 1
                    continue
            else:
                if self.rng.random() > elder_s * density_scale:
                    deaths += 1
                    continue
            if is_juvenile:
                juvenile_survivors += 1
            survivors.append(ind)
        self.individuals = survivors
        self.last_juvenile_survival_rate = (
            juvenile_survivors / juvenile_trials
            if juvenile_trials > 0
            else math.nan
        )
        self.last_mean_juvenile_food_survival_effect = (
            food_survival_effect_total / juvenile_trials
            if juvenile_trials > 0
            else math.nan
        )
        self.last_mean_household_survival_bonus = (
            household_bonus_total / juvenile_trials
            if juvenile_trials > 0
            else math.nan
        )
        self.last_two_living_parent_juvenile_fraction = (
            two_living_parent_count / juvenile_trials
            if juvenile_trials > 0
            else math.nan
        )
        self.last_household_caregiver_juvenile_fraction = (
            household_caregiver_count / juvenile_trials
            if juvenile_trials > 0
            else math.nan
        )
        return deaths

    def _household_juvenile_survival_bonus(
        self,
        juvenile: Individual,
        by_id: Mapping[int, Individual],
        caregivers_by_household: Mapping[int, list[Individual]],
    ) -> tuple[float, int, int]:
        parent_ids = {
            parent_id
            for parent_id in (juvenile.mother_id, juvenile.father_id)
            if parent_id is not None
        }
        living_parent_count = sum(1 for parent_id in parent_ids if parent_id in by_id)

        if living_parent_count >= 2:
            parent_bonus = float(self.config["household_two_living_parent_survival_bonus"])
        elif living_parent_count == 1:
            parent_bonus = float(self.config["household_single_living_parent_survival_bonus"])
        else:
            parent_bonus = 0.0

        caregivers = caregivers_by_household.get(juvenile.household_id, [])
        caregiver_count = len(caregivers)
        caregiver_bonus = min(
            float(self.config["household_caregiver_survival_bonus_max"]),
            caregiver_count * float(self.config["household_caregiver_survival_bonus_per_adult"]),
        )
        return parent_bonus + caregiver_bonus, living_parent_count, caregiver_count

    # ------------------------------------------------------------------
    # Reproduction (all mate-preference channels combined)
    # ------------------------------------------------------------------

    def _reproduce(self) -> dict[str, int]:
        """Mate weights combine reputation, band, spatial, and kin preferences
        multiplicatively:
          w = rep_w × band_w × interband_w × spatial_w × kin_w
        where each factor is 1 + pref_strength if condition met, baseline otherwise.
        """
        female_min = int(self.config["female_min_reproduction_age"])
        female_max = int(self.config["female_max_reproduction_age"])
        male_min = int(self.config["male_min_reproduction_age"])
        male_max = int(self.config["male_max_reproduction_age"])
        repr_prob = float(self.config["female_reproduction_probability"])
        density_reproduction_scale = self._density_reproduction_scale()
        e_thresh = float(self.config["reproduction_energy_threshold"])
        e_cost = float(self.config["reproduction_energy_cost"])
        cost_scale = float(self.config["helping_reproduction_cost_scale"])
        rep_pref = float(self.config["reputation_mate_preference"])
        grp_pref = float(self.config["group_mate_preference"])
        interband_pref = float(self.config["interband_marriage_preference"])
        interband_radius = float(self.config["interband_marriage_distance"])
        kin_pref = float(self.config["kin_mate_preference"])
        spatial_pref = float(self.config["spatial_mate_preference"])
        spouse_pref = float(self.config["spouse_mate_preference"])
        spatial_radius = float(self.config["spatial_mate_radius"])
        width = float(self.config["space_width"])

        eligible_males = [
            i for i in self.individuals
            if i.sex == SEX_MALE
            and male_min <= i.age <= male_max
            and i.energy >= e_thresh
        ]
        if not eligible_males:
            return {"births": 0}

        male_xs = np.array([m.x for m in eligible_males])
        male_ys = np.array([m.y for m in eligible_males])

        new_children: list[Individual] = []
        births = 0

        for mother in self.individuals:
            if mother.sex != SEX_FEMALE:
                continue
            if not (female_min <= mother.age <= female_max):
                continue
            if mother.energy < e_thresh:
                continue
            effective_repr_prob = (
                repr_prob
                * density_reproduction_scale
                * (1.0 - self._effective_helping(mother) * cost_scale)
            )
            if self.rng.random() > effective_repr_prob:
                continue

            # Compute spatial distances to eligible males (toroidal).
            dx = np.abs(male_xs - mother.x)
            dy = np.abs(male_ys - mother.y)
            dx = np.minimum(dx, width - dx)
            dy = np.minimum(dy, width - dy)
            dists = np.sqrt(dx * dx + dy * dy)

            mother_kin_ids = {k.id for k in self._kin_index.get(mother.id, [])}

            weights = np.ones(len(eligible_males))
            mother_band = self.bands.get(mother.group_id)
            for idx, m in enumerate(eligible_males):
                rep_w = m.reputation * rep_pref + (1.0 - rep_pref)
                same_band = m.group_id == mother.group_id
                grp_w = (1.0 + grp_pref) if same_band else 1.0
                interband_w = 1.0
                father_band = self.bands.get(m.group_id)
                if not same_band and interband_pref > 0.0:
                    bands_close = False
                    if mother_band is not None and father_band is not None:
                        bands_close = (
                            self._toroidal_distance_to_xy(
                                mother_band.x,
                                mother_band.y,
                                father_band.x,
                                father_band.y,
                            )
                            <= interband_radius
                        )
                    if bands_close or dists[idx] <= interband_radius:
                        interband_w = 1.0 + interband_pref
                spatial_w = (1.0 + spatial_pref) if dists[idx] <= spatial_radius else 1.0
                kin_w = (1.0 + kin_pref) if m.id in mother_kin_ids else 1.0
                spouse_w = (1.0 + spouse_pref) if mother.spouse_id == m.id else 1.0
                weights[idx] = rep_w * grp_w * interband_w * spatial_w * kin_w * spouse_w

            total = float(weights.sum())
            if total <= 0.0:
                father = eligible_males[int(self.rng.integers(0, len(eligible_males)))]
            else:
                father_idx = int(self.rng.choice(len(eligible_males), p=weights / total))
                father = eligible_males[father_idx]

            mother.energy -= e_cost
            interband_pair = mother.group_id != father.group_id
            already_spouses = mother.spouse_id == father.id and father.spouse_id == mother.id
            child = self._create_child(mother, father, initial_child=False)
            spouse_linked = self._form_spouse_bond(mother, father) or mother.spouse_id == father.id
            if interband_pair and spouse_linked and not already_spouses:
                self.last_interband_marriages += 1
                self.total_interband_marriages += 1
            if spouse_linked:
                if self.rng.random() < float(self.config["spouse_household_join_probability"]):
                    old_father_band = father.group_id
                    self._join_household(father, mother.household_id)
                    if old_father_band != mother.group_id:
                        father.group_id = mother.group_id
                        self.last_band_migrations += 1
                        self.total_band_migrations += 1
                self._try_form_spouse_reciprocity_bond(mother, father)
            new_children.append(child)
            births += 1
            if mother.id in self.offspring_counts:
                self.offspring_counts[mother.id] += 1
            if father.id in self.offspring_counts:
                self.offspring_counts[father.id] += 1

        self.individuals.extend(new_children)
        return {"births": births}

    # ------------------------------------------------------------------
    # Density ecology
    # ------------------------------------------------------------------

    def _density_fraction(self) -> float:
        target = int(self.config["density_target_population"])
        return len(self.individuals) / target

    def _density_reproduction_scale(self) -> float:
        crowding = max(0.0, self._density_fraction() - 1.0)
        pressure = float(self.config["density_reproduction_pressure"])
        return float(math.exp(-pressure * crowding))

    def _density_survival_scale(self) -> float:
        crowding = max(0.0, self._density_fraction() - 1.0)
        pressure = float(self.config["density_survival_pressure"])
        return float(math.exp(-pressure * crowding))

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _mean_helping_trait(self) -> float:
        if not self.individuals:
            return 0.0
        return float(np.mean([i.helping_trait for i in self.individuals]))

    def _mean_learned_helping_adjustment(self) -> float:
        if not self.individuals:
            return 0.0
        return float(np.mean([i.learned_helping_adjustment for i in self.individuals]))

    def _mean_effective_helping(self) -> float:
        if not self.individuals:
            return 0.0
        return float(np.mean([self._effective_helping(i) for i in self.individuals]))

    def _spouse_pair_counts(self) -> tuple[int, int]:
        by_id = {i.id: i for i in self.individuals}
        spouse_pairs = 0
        spouse_reciprocity_pairs = 0
        seen: set[frozenset[int]] = set()
        for ind in self.individuals:
            if ind.spouse_id is None:
                continue
            spouse = by_id.get(ind.spouse_id)
            if spouse is None or spouse.spouse_id != ind.id:
                continue
            key = frozenset((ind.id, spouse.id))
            if key in seen:
                continue
            seen.add(key)
            spouse_pairs += 1
            if ind.reciprocity_bond_id == spouse.id and spouse.reciprocity_bond_id == ind.id:
                spouse_reciprocity_pairs += 1
        return spouse_pairs, spouse_reciprocity_pairs

    def _household_metrics(self) -> tuple[int, float, float]:
        if not self.households:
            return 0, 0.0, 0.0
        sizes: dict[int, int] = {household_id: 0 for household_id in self.households}
        juvenile_counts: dict[int, int] = {household_id: 0 for household_id in self.households}
        for ind in self.individuals:
            if ind.household_id not in sizes:
                continue
            sizes[ind.household_id] += 1
            if ind.stage == STAGE_JUVENILE:
                juvenile_counts[ind.household_id] += 1
        nonempty_sizes = [size for size in sizes.values() if size > 0]
        nonempty_juveniles = [
            juvenile_counts[household_id]
            for household_id, size in sizes.items()
            if size > 0
        ]
        if not nonempty_sizes:
            return 0, 0.0, 0.0
        return (
            len(nonempty_sizes),
            float(np.mean(nonempty_sizes)),
            float(np.mean(nonempty_juveniles)),
        )

    def _stage_counts(self) -> tuple[int, int, int, int]:
        counts = {
            STAGE_JUVENILE: 0,
            STAGE_SUBADULT: 0,
            STAGE_ADULT: 0,
            STAGE_ELDER: 0,
        }
        for ind in self.individuals:
            if ind.stage in counts:
                counts[ind.stage] += 1
        return (
            counts[STAGE_JUVENILE],
            counts[STAGE_SUBADULT],
            counts[STAGE_ADULT],
            counts[STAGE_ELDER],
        )

    def _group_counts(self) -> dict[int, int]:
        counts = {band_id: 0 for band_id in self.bands}
        for ind in self.individuals:
            counts[ind.group_id] = counts.get(ind.group_id, 0) + 1
        return dict(sorted(counts.items()))

    def _compute_metrics(self) -> dict[str, float]:
        adults = [i for i in self.individuals if i.stage in {STAGE_ADULT, STAGE_ELDER}]
        spouse_pairs, spouse_reciprocity_pairs = self._spouse_pair_counts()
        household_count, mean_household_size, mean_household_juveniles = self._household_metrics()
        juvenile_count, subadult_count, adult_count, elder_count = self._stage_counts()
        group_counts = self._group_counts()
        nonempty_band_sizes = [count for count in group_counts.values() if count > 0]
        mean_band_size = float(np.mean(nonempty_band_sizes)) if nonempty_band_sizes else 0.0
        if not adults:
            return {
                "mean_helping_trait": 0.0,
                "mean_effective_helping": 0.0,
                "mean_learned_helping_adjustment": 0.0,
                "social_learning_events": float(self.last_social_learning_events),
                "mean_reputation": 0.0,
                "helping_invasion_frequency": 0.0,
                "realized_helping_rate": self.last_realized_helping_rate,
                "helping_events": float(self.last_helping_events),
                "helping_opportunities": float(self.last_helping_opportunities),
                "norm_violation_rate": 0.0,
                "mean_reciprocity_bond_memory": 0.0,
                "mean_grass_fraction": self.last_mean_grass_fraction,
                "grass_harvest": self.last_grass_harvest,
                "parent_food_transfer": self.last_parent_food_transfer,
                "fed_juvenile_count": float(self.last_fed_juvenile_count),
                "fed_juvenile_fraction": self.last_fed_juvenile_fraction,
                "mean_juvenile_food_survival_effect": (
                    self.last_mean_juvenile_food_survival_effect
                ),
                "juvenile_survival_rate": self.last_juvenile_survival_rate,
                "juvenile_count": float(juvenile_count),
                "subadult_count": float(subadult_count),
                "adult_count": float(adult_count),
                "elder_count": float(elder_count),
                "total_child_rearing_care": self.last_total_child_rearing_care,
                "mean_child_rearing_care": self.last_mean_child_rearing_care,
                "mean_child_rearing_relatedness": self.last_mean_child_rearing_relatedness,
                "kin_child_rearing_fraction": self.last_kin_child_rearing_fraction,
                "parent_child_rearing_fraction": self.last_parent_child_rearing_fraction,
                "household_child_rearing_fraction": self.last_household_child_rearing_fraction,
                "spouse_child_rearing_fraction": self.last_spouse_child_rearing_fraction,
                "coparent_near_child_rearing_fraction": (
                    self.last_coparent_near_child_rearing_fraction
                ),
                "cared_juvenile_count": float(self.last_cared_juvenile_count),
                "cared_juvenile_fraction": self.last_cared_juvenile_fraction,
                "spouse_bond_pairs": float(spouse_pairs),
                "spouse_reciprocity_bond_pairs": float(spouse_reciprocity_pairs),
                "household_count": float(household_count),
                "mean_household_size": mean_household_size,
                "mean_household_juveniles": mean_household_juveniles,
                "mean_household_survival_bonus": self.last_mean_household_survival_bonus,
                "two_living_parent_juvenile_fraction": (
                    self.last_two_living_parent_juvenile_fraction
                ),
                "household_caregiver_juvenile_fraction": (
                    self.last_household_caregiver_juvenile_fraction
                ),
                "maturity_dispersals": float(self.last_maturity_dispersals),
                "band_count": float(len(nonempty_band_sizes)),
                "mean_band_size": mean_band_size,
                "band_migrations": float(self.last_band_migrations),
                "band_fissions": float(self.last_band_fissions),
                "band_fusions": float(self.last_band_fusions),
                "interband_marriages": float(self.last_interband_marriages),
                "cumulative_band_migrations": float(self.total_band_migrations),
                "cumulative_band_fissions": float(self.total_band_fissions),
                "cumulative_band_fusions": float(self.total_band_fusions),
                "cumulative_interband_marriages": float(self.total_interband_marriages),
                **{
                    f"band_{gid}_count": float(count)
                    for gid, count in group_counts.items()
                },
            }
        threshold = float(self.config["helping_trait_invasion_threshold"])
        sensitivity = float(self.config["norm_detection_sensitivity"])
        traits = [i.helping_trait for i in self.individuals]
        effective_traits = [self._effective_helping(i) for i in self.individuals]
        reps = [i.reputation for i in adults]
        mean_rep = float(np.mean(reps))

        bonded = [i for i in adults if i.reciprocity_bond_id is not None]
        mean_bond_memory = (
            float(np.mean([i.reciprocity_bond_memory for i in bonded]))
            if bonded
            else math.nan
        )

        return {
            "mean_helping_trait": float(np.mean(traits)),
            "mean_effective_helping": float(np.mean(effective_traits)),
            "mean_learned_helping_adjustment": self._mean_learned_helping_adjustment(),
            "social_learning_events": float(self.last_social_learning_events),
            "mean_reputation": mean_rep,
            "helping_invasion_frequency": float(np.mean([t >= threshold for t in traits])),
            "realized_helping_rate": self.last_realized_helping_rate,
            "helping_events": float(self.last_helping_events),
            "helping_opportunities": float(self.last_helping_opportunities),
            "norm_violation_rate": float(np.mean([i.reputation < mean_rep - sensitivity for i in adults])),
            "mean_reciprocity_bond_memory": mean_bond_memory,
            "mean_grass_fraction": self.last_mean_grass_fraction,
            "grass_harvest": self.last_grass_harvest,
            "parent_food_transfer": self.last_parent_food_transfer,
            "fed_juvenile_count": float(self.last_fed_juvenile_count),
            "fed_juvenile_fraction": self.last_fed_juvenile_fraction,
            "mean_juvenile_food_survival_effect": (
                self.last_mean_juvenile_food_survival_effect
            ),
            "juvenile_survival_rate": self.last_juvenile_survival_rate,
            "juvenile_count": float(juvenile_count),
            "subadult_count": float(subadult_count),
            "adult_count": float(adult_count),
            "elder_count": float(elder_count),
            "total_child_rearing_care": self.last_total_child_rearing_care,
            "mean_child_rearing_care": self.last_mean_child_rearing_care,
            "mean_child_rearing_relatedness": self.last_mean_child_rearing_relatedness,
            "kin_child_rearing_fraction": self.last_kin_child_rearing_fraction,
            "parent_child_rearing_fraction": self.last_parent_child_rearing_fraction,
            "household_child_rearing_fraction": self.last_household_child_rearing_fraction,
            "spouse_child_rearing_fraction": self.last_spouse_child_rearing_fraction,
            "coparent_near_child_rearing_fraction": self.last_coparent_near_child_rearing_fraction,
            "cared_juvenile_count": float(self.last_cared_juvenile_count),
            "cared_juvenile_fraction": self.last_cared_juvenile_fraction,
            "spouse_bond_pairs": float(spouse_pairs),
            "spouse_reciprocity_bond_pairs": float(spouse_reciprocity_pairs),
            "household_count": float(household_count),
            "mean_household_size": mean_household_size,
            "mean_household_juveniles": mean_household_juveniles,
            "mean_household_survival_bonus": self.last_mean_household_survival_bonus,
            "two_living_parent_juvenile_fraction": self.last_two_living_parent_juvenile_fraction,
            "household_caregiver_juvenile_fraction": (
                self.last_household_caregiver_juvenile_fraction
            ),
            "maturity_dispersals": float(self.last_maturity_dispersals),
            "band_count": float(len(nonempty_band_sizes)),
            "mean_band_size": mean_band_size,
            "band_migrations": float(self.last_band_migrations),
            "band_fissions": float(self.last_band_fissions),
            "band_fusions": float(self.last_band_fusions),
            "interband_marriages": float(self.last_interband_marriages),
            "cumulative_band_migrations": float(self.total_band_migrations),
            "cumulative_band_fissions": float(self.total_band_fissions),
            "cumulative_band_fusions": float(self.total_band_fusions),
            "cumulative_interband_marriages": float(self.total_interband_marriages),
            **{
                f"band_{gid}_count": float(count)
                for gid, count in group_counts.items()
            },
        }

    def _record_history(self, *, births: int, deaths: int) -> None:
        m = self._compute_metrics()
        current_len = len(self.history["step"])
        current_band_keys = {
            key for key in m
            if self._is_band_count_history_key(key)
        }
        known_band_keys = {
            key for key in self.history
            if self._is_band_count_history_key(key)
        }
        for key in current_band_keys - known_band_keys:
            self.history[key].extend([0.0] * current_len)
        for key in known_band_keys - current_band_keys:
            m[key] = 0.0
        self.history["step"].append(self.step_index)
        self.history["population"].append(len(self.individuals))
        self.history["births"].append(births)
        self.history["deaths"].append(deaths)
        for k, v in m.items():
            self.history[k].append(v)

    @staticmethod
    def _is_band_count_history_key(key: str) -> bool:
        parts = key.split("_")
        return (
            len(parts) == 3
            and parts[0] == "band"
            and parts[1].isdigit()
            and parts[2] == "count"
        )

    def summary(self) -> dict[str, Any]:
        initial_mean = self.initial_mean_helping_trait
        final_mean = self.history["mean_helping_trait"][-1] if self.history["mean_helping_trait"] else 0.0
        initial_inv = self.history["helping_invasion_frequency"][0] if self.history["helping_invasion_frequency"] else 0.0
        final_inv = self.history["helping_invasion_frequency"][-1] if self.history["helping_invasion_frequency"] else 0.0
        band_count_keys = sorted(
            (key for key in self.history if self._is_band_count_history_key(key)),
            key=lambda key: int(key.split("_")[1]),
        )
        latest_band_counts = {
            int(key.split("_")[1]): (self.history[key][-1] if self.history[key] else 0.0)
            for key in band_count_keys
        }
        return {
            "helping_trait_change": final_mean - initial_mean,
            "helping_invasion_frequency_change": final_inv - initial_inv,
            "final_population": len(self.individuals),
            "latest_mean_effective_helping": (
                self.history["mean_effective_helping"][-1]
                if self.history["mean_effective_helping"]
                else 0.0
            ),
            "latest_mean_learned_helping_adjustment": (
                self.history["mean_learned_helping_adjustment"][-1]
                if self.history["mean_learned_helping_adjustment"]
                else 0.0
            ),
            "latest_social_learning_events": (
                self.history["social_learning_events"][-1]
                if self.history["social_learning_events"]
                else 0.0
            ),
            "latest_mean_reputation": self.history["mean_reputation"][-1] if self.history["mean_reputation"] else 0.0,
            "latest_norm_violation_rate": self.history["norm_violation_rate"][-1] if self.history["norm_violation_rate"] else 0.0,
            "latest_mean_reciprocity_bond_memory": (
                self.history["mean_reciprocity_bond_memory"][-1]
                if self.history["mean_reciprocity_bond_memory"]
                else math.nan
            ),
            "latest_realized_helping_rate": self.history["realized_helping_rate"][-1] if self.history["realized_helping_rate"] else math.nan,
            "latest_helping_events": self.history["helping_events"][-1] if self.history["helping_events"] else 0.0,
            "latest_helping_opportunities": self.history["helping_opportunities"][-1] if self.history["helping_opportunities"] else 0.0,
            "latest_mean_grass_fraction": (
                self.history["mean_grass_fraction"][-1]
                if self.history["mean_grass_fraction"]
                else math.nan
            ),
            "latest_grass_harvest": (
                self.history["grass_harvest"][-1]
                if self.history["grass_harvest"]
                else 0.0
            ),
            "latest_parent_food_transfer": (
                self.history["parent_food_transfer"][-1]
                if self.history["parent_food_transfer"]
                else 0.0
            ),
            "latest_fed_juvenile_count": (
                self.history["fed_juvenile_count"][-1]
                if self.history["fed_juvenile_count"]
                else 0.0
            ),
            "latest_fed_juvenile_fraction": (
                self.history["fed_juvenile_fraction"][-1]
                if self.history["fed_juvenile_fraction"]
                else math.nan
            ),
            "latest_mean_juvenile_food_survival_effect": (
                self.history["mean_juvenile_food_survival_effect"][-1]
                if self.history["mean_juvenile_food_survival_effect"]
                else math.nan
            ),
            "latest_juvenile_survival_rate": (
                self.history["juvenile_survival_rate"][-1]
                if self.history["juvenile_survival_rate"]
                else math.nan
            ),
            "latest_juvenile_count": (
                self.history["juvenile_count"][-1]
                if self.history["juvenile_count"]
                else 0.0
            ),
            "latest_subadult_count": (
                self.history["subadult_count"][-1]
                if self.history["subadult_count"]
                else 0.0
            ),
            "latest_adult_count": (
                self.history["adult_count"][-1]
                if self.history["adult_count"]
                else 0.0
            ),
            "latest_elder_count": (
                self.history["elder_count"][-1]
                if self.history["elder_count"]
                else 0.0
            ),
            "latest_band_counts": latest_band_counts,
            "latest_band_count": (
                self.history["band_count"][-1]
                if self.history["band_count"]
                else 0.0
            ),
            "latest_mean_band_size": (
                self.history["mean_band_size"][-1]
                if self.history["mean_band_size"]
                else 0.0
            ),
            "latest_band_migrations": (
                self.history["band_migrations"][-1]
                if self.history["band_migrations"]
                else 0.0
            ),
            "latest_band_fissions": (
                self.history["band_fissions"][-1]
                if self.history["band_fissions"]
                else 0.0
            ),
            "latest_band_fusions": (
                self.history["band_fusions"][-1]
                if self.history["band_fusions"]
                else 0.0
            ),
            "latest_interband_marriages": (
                self.history["interband_marriages"][-1]
                if self.history["interband_marriages"]
                else 0.0
            ),
            "latest_cumulative_band_migrations": (
                self.history["cumulative_band_migrations"][-1]
                if self.history["cumulative_band_migrations"]
                else 0.0
            ),
            "latest_cumulative_band_fissions": (
                self.history["cumulative_band_fissions"][-1]
                if self.history["cumulative_band_fissions"]
                else 0.0
            ),
            "latest_cumulative_band_fusions": (
                self.history["cumulative_band_fusions"][-1]
                if self.history["cumulative_band_fusions"]
                else 0.0
            ),
            "latest_cumulative_interband_marriages": (
                self.history["cumulative_interband_marriages"][-1]
                if self.history["cumulative_interband_marriages"]
                else 0.0
            ),
            "latest_total_child_rearing_care": (
                self.history["total_child_rearing_care"][-1]
                if self.history["total_child_rearing_care"]
                else 0.0
            ),
            "latest_mean_child_rearing_care": (
                self.history["mean_child_rearing_care"][-1]
                if self.history["mean_child_rearing_care"]
                else 0.0
            ),
            "latest_mean_child_rearing_relatedness": (
                self.history["mean_child_rearing_relatedness"][-1]
                if self.history["mean_child_rearing_relatedness"]
                else math.nan
            ),
            "latest_kin_child_rearing_fraction": (
                self.history["kin_child_rearing_fraction"][-1]
                if self.history["kin_child_rearing_fraction"]
                else math.nan
            ),
            "latest_parent_child_rearing_fraction": (
                self.history["parent_child_rearing_fraction"][-1]
                if self.history["parent_child_rearing_fraction"]
                else math.nan
            ),
            "latest_household_child_rearing_fraction": (
                self.history["household_child_rearing_fraction"][-1]
                if self.history["household_child_rearing_fraction"]
                else math.nan
            ),
            "latest_spouse_child_rearing_fraction": (
                self.history["spouse_child_rearing_fraction"][-1]
                if self.history["spouse_child_rearing_fraction"]
                else math.nan
            ),
            "latest_coparent_near_child_rearing_fraction": (
                self.history["coparent_near_child_rearing_fraction"][-1]
                if self.history["coparent_near_child_rearing_fraction"]
                else math.nan
            ),
            "latest_cared_juvenile_count": (
                self.history["cared_juvenile_count"][-1]
                if self.history["cared_juvenile_count"]
                else 0.0
            ),
            "latest_cared_juvenile_fraction": (
                self.history["cared_juvenile_fraction"][-1]
                if self.history["cared_juvenile_fraction"]
                else math.nan
            ),
            "latest_spouse_bond_pairs": (
                self.history["spouse_bond_pairs"][-1]
                if self.history["spouse_bond_pairs"]
                else 0.0
            ),
            "latest_spouse_reciprocity_bond_pairs": (
                self.history["spouse_reciprocity_bond_pairs"][-1]
                if self.history["spouse_reciprocity_bond_pairs"]
                else 0.0
            ),
            "latest_household_count": (
                self.history["household_count"][-1]
                if self.history["household_count"]
                else 0.0
            ),
            "latest_mean_household_size": (
                self.history["mean_household_size"][-1]
                if self.history["mean_household_size"]
                else 0.0
            ),
            "latest_mean_household_juveniles": (
                self.history["mean_household_juveniles"][-1]
                if self.history["mean_household_juveniles"]
                else 0.0
            ),
            "latest_mean_household_survival_bonus": (
                self.history["mean_household_survival_bonus"][-1]
                if self.history["mean_household_survival_bonus"]
                else math.nan
            ),
            "latest_two_living_parent_juvenile_fraction": (
                self.history["two_living_parent_juvenile_fraction"][-1]
                if self.history["two_living_parent_juvenile_fraction"]
                else math.nan
            ),
            "latest_household_caregiver_juvenile_fraction": (
                self.history["household_caregiver_juvenile_fraction"][-1]
                if self.history["household_caregiver_juvenile_fraction"]
                else math.nan
            ),
            "latest_maturity_dispersals": (
                self.history["maturity_dispersals"][-1]
                if self.history["maturity_dispersals"]
                else 0.0
            ),
        }


# ------------------------------------------------------------------
# Run helpers
# ------------------------------------------------------------------

def run_simulation(run_config: Mapping[str, Any]) -> dict[str, Any]:
    model = BehaviorallyAnchoredModel(run_config)
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
    model = BehaviorallyAnchoredModel(active_config)
    steps = int(active_config["simulation_steps"])
    for i in range(steps):
        model.step()
        if (i + 1) % 100 == 0:
            s = model.summary()
            help_rate = s["latest_realized_helping_rate"]
            help_str = f"{help_rate:.3f}" if math.isfinite(help_rate) else "nan"
            juv_survival = s["latest_juvenile_survival_rate"]
            juv_str = f"{juv_survival:.3f}" if math.isfinite(juv_survival) else "nan"
            print(
                f"step {i+1:4d}  pop={len(model.individuals):4d}"
                f"  trait={s['helping_trait_change']:+.4f}"
                f"  eff={s['latest_mean_effective_helping']:.3f}"
                f"  inv={s['helping_invasion_frequency_change']:+.4f}"
                f"  rep={s['latest_mean_reputation']:.3f}"
                f"  help={help_str}"
                f"  grass={s['latest_mean_grass_fraction']:.3f}"
                f"  harvest={s['latest_grass_harvest']:.2f}"
                f"  food={s['latest_parent_food_transfer']:.2f}"
                f"  care={s['latest_total_child_rearing_care']:.2f}"
                f"  cared={s['latest_cared_juvenile_count']:.0f}"
                f"  hh={s['latest_household_count']:.0f}"
                f"  bands={s['latest_band_count']:.0f}"
                f"  spouses={s['latest_spouse_bond_pairs']:.0f}"
                f"  juv={juv_str}"
                f"  bm={s['latest_mean_reciprocity_bond_memory']:.3f}"
            )
    if bool(active_config.get("write_latest_run", True)):
        _write_latest_run(
            {"config": active_config, "history": dict(model.history), "summary": model.summary()},
            str(active_config.get("data_dir", ".")),
        )
    s = model.summary()
    print(
        f"\nfinal: trait_Δ={s['helping_trait_change']:+.4f}"
        f"  eff={s['latest_mean_effective_helping']:.3f}"
        f"  inv_Δ={s['helping_invasion_frequency_change']:+.4f}"
        f"  pop={s['final_population']}"
        f"  rep={s['latest_mean_reputation']:.3f}"
        f"  help={s['latest_realized_helping_rate']:.3f}"
        f"  grass={s['latest_mean_grass_fraction']:.3f}"
        f"  food={s['latest_parent_food_transfer']:.2f}"
        f"  care={s['latest_total_child_rearing_care']:.2f}"
        f"  hh={s['latest_household_count']:.0f}"
        f"  bands={s['latest_band_count']:.0f}"
        f"  spouses={s['latest_spouse_bond_pairs']:.0f}"
    )


if __name__ == "__main__":
    main()
