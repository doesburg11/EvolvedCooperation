#!/usr/bin/env python3
"""
Top-down cooperation model: all five Nowak mechanisms as cognitive capacities.

Run from the repository root with:
  ./.conda/bin/python -m top_down_model.top_down_model

The bottom-up ecological models identified the load-bearing channel for each
Nowak mechanism. This top-down model asks: given that agents already possess
all five human cognitive capacities simultaneously, which are load-bearing for
cooperation to spread from a rare 10% foothold, and which are dispensable?

Six capacities (the five Nowak mechanisms plus norm enforcement):

  1. Reputation sensitivity (indirect reciprocity): public reputation gates
     energy routing; high-reputation males preferred as mates.

  2. Norm enforcement: adults with reputation far below the population mean
     incur a social energy penalty (third-party sanctioning).

  3. Group identity (group selection): heritable group membership biases
     interaction routing and mate choice; inter-group conflict transfers
     energy from less- to more-cooperative groups.

  4. Kin recognition (kin selection): agents route interactions preferentially
     toward kin (siblings, parents, offspring); kin males get a mate-choice
     weight bonus.

  5. Spatial awareness (network reciprocity): heritable spatial coordinates;
     offspring placed near mother; spatial neighbors preferred for interactions
     and mate choice.

  6. Partner fidelity (direct reciprocity): stable dyadic partnerships;
     conditional cooperation based on partner memory; differential dissolution.

Routing priority for unpartnered interactions: kin > spatial > group > random.
Mate weight: reputation × group × spatial × kin (multiplicative combination).
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
        "'./.conda/bin/python -m top_down_model.top_down_model'."
    )

from .config.top_down_config import DEFAULT_CONFIG
from .config.top_down_config import config as active_config
from .config.top_down_config import resolve_config

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
    helping_trait: float      # heritable, evolves
    reputation: float         # public, not inherited
    group_id: int             # inherited from mother with migration
    x: float                  # spatial coordinate (network reciprocity)
    y: float
    partner_id: int | None    # current partnership partner (direct reciprocity)
    partner_memory: float     # rolling mean of partner's cooperation (direct reciprocity)
    mother_id: int | None
    father_id: int | None
    born_step: int


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


class TopDownCooperationModel:
    """
    Population model testing which of six human cognitive capacities are
    load-bearing for cooperation to invade from a rare 10% foothold.

    Demographic backbone: age structure, energy budget, blending inheritance,
    density mortality — identical across all six ecological bottom-up models.
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
        self._kin_index: dict[int, list[Individual]] = {}
        self._initialize_population()
        self.initial_mean_helping_trait = self._mean_helping_trait()
        self._record_history(births=0, deaths=0)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialize_population(self) -> None:
        pairs = int(self.config["initial_founder_pairs"])
        children_per_pair = int(self.config["initial_children_per_pair"])
        for _ in range(pairs):
            mother = self._create_founder(SEX_FEMALE)
            father = self._create_founder(SEX_MALE)
            father.group_id = mother.group_id
            self.individuals.extend([mother, father])
            for _ in range(children_per_pair):
                self.individuals.append(self._create_child(mother, father, initial_child=True))

    def _create_founder(self, sex: str) -> Individual:
        width = float(self.config["space_width"])
        n_groups = int(self.config["n_groups"])
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
            reputation=float(self.config["reputation_initial"]),
            group_id=int(self.rng.integers(0, n_groups)),
            x=float(self.rng.uniform(0.0, width)),
            y=float(self.rng.uniform(0.0, width)),
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
        width = float(self.config["space_width"])
        n_groups = int(self.config["n_groups"])
        dispersal = float(self.config["offspring_dispersal_std"])
        migration_prob = float(self.config["group_migration_probability"])

        age = int(self.rng.integers(
            int(self.config["initial_child_age_min"]),
            int(self.config["initial_child_age_max"]) + 1,
        )) if initial_child else 0
        energy = float(self.config["initial_juvenile_energy"]) if initial_child else float(self.config["child_energy"])

        helping_trait = 0.5 * (mother.helping_trait + father.helping_trait)
        if self.rng.random() < float(self.config["helping_mutation_probability"]):
            helping_trait += float(self.rng.normal(0.0, float(self.config["helping_mutation_stddev"])))

        group_id = (
            int(self.rng.integers(0, n_groups))
            if n_groups > 1 and self.rng.random() < migration_prob
            else mother.group_id
        )

        cx = (mother.x + float(self.rng.normal(0.0, dispersal))) % width
        cy = (mother.y + float(self.rng.normal(0.0, dispersal))) % width

        child = Individual(
            id=self._take_id(),
            sex=SEX_FEMALE if self.rng.random() < 0.5 else SEX_MALE,
            age=age,
            stage=self._stage_for_age(age),
            energy=energy,
            helping_trait=clamp01(helping_trait),
            reputation=float(self.config["reputation_initial"]),
            group_id=group_id,
            x=cx,
            y=cy,
            partner_id=None,
            partner_memory=1.0,
            mother_id=mother.id,
            father_id=father.id,
            born_step=self.step_index,
        )
        self.offspring_counts[child.id] = 0
        self.birth_helping_traits[child.id] = child.helping_trait
        return child

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

    def _stage_for_age(self, age: int) -> str:
        if age < int(self.config["juvenile_maturity_age"]):
            return STAGE_JUVENILE
        if age >= int(self.config["elder_age"]):
            return STAGE_ELDER
        return STAGE_ADULT

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self) -> None:
        self.step_index += 1
        self._age_and_budget()
        self._kin_index = self._build_kin_index()
        self._update_partnerships()
        self._conduct_interactions()
        self._apply_norm_enforcement()
        conflict_interval = int(self.config["conflict_interval"])
        if conflict_interval > 0 and self.step_index % conflict_interval == 0:
            self._apply_group_conflict()
        deaths = self._apply_survival()
        self._clear_dead_partnerships()
        stats = self._reproduce()
        deaths += self._apply_density_mortality()
        self._record_history(births=stats["births"], deaths=deaths)

    # ------------------------------------------------------------------
    # Age and energy budget
    # ------------------------------------------------------------------

    def _age_and_budget(self) -> None:
        cost = float(self.config["helping_cost_per_step"])
        max_e = float(self.config["max_energy"])
        for ind in self.individuals:
            ind.age += 1
            ind.stage = self._stage_for_age(ind.age)
            if ind.stage == STAGE_JUVENILE:
                ind.energy += float(self.config["juvenile_foraging_energy_gain"])
                ind.energy -= float(self.config["juvenile_metabolic_cost"])
            elif ind.stage == STAGE_ADULT:
                ind.energy += float(self.config["adult_foraging_energy_gain"])
                ind.energy -= float(self.config["adult_metabolic_cost"])
                ind.energy -= ind.helping_trait * cost
            else:
                ind.energy += float(self.config["elder_foraging_energy_gain"])
                ind.energy -= float(self.config["elder_metabolic_cost"])
                ind.energy -= ind.helping_trait * cost
            ind.energy = min(ind.energy, max_e)

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

    # ------------------------------------------------------------------
    # Direct reciprocity: partnership management
    # ------------------------------------------------------------------

    def _update_partnerships(self) -> None:
        """Dissolve low-quality partnerships; match unpartnered adults into new pairs."""
        base_p = float(self.config["partner_persistence_probability"])
        leave_w = float(self.config["leave_weight"])

        active = {i.id: i for i in self.individuals if i.stage in {STAGE_ADULT, STAGE_ELDER}}

        # Dissolve partnerships.
        dissolved: set[int] = set()
        for ind in active.values():
            if ind.partner_id is None:
                continue
            if ind.id in dissolved:
                continue
            partner = active.get(ind.partner_id)
            if partner is None:
                ind.partner_id = None
                continue
            effective_p = base_p * max(0.0, 1.0 - leave_w * (1.0 - ind.partner_memory))
            if self.rng.random() > effective_p:
                ind.partner_id = None
                partner.partner_id = None
                dissolved.add(ind.id)
                dissolved.add(partner.id)

        # Match newly unpartnered adults into new pairs.
        if base_p > 0.0:
            unpartnered = [i for i in active.values() if i.partner_id is None]
            self.rng.shuffle(unpartnered)  # type: ignore[arg-type]
            for k in range(0, len(unpartnered) - 1, 2):
                a = unpartnered[k]
                b = unpartnered[k + 1]
                a.partner_id = b.id
                b.partner_id = a.id
                a.partner_memory = 1.0
                b.partner_memory = 1.0

    def _clear_dead_partnerships(self) -> None:
        alive_ids = {i.id for i in self.individuals}
        for ind in self.individuals:
            if ind.partner_id is not None and ind.partner_id not in alive_ids:
                ind.partner_id = None

    # ------------------------------------------------------------------
    # Interactions (all five routing channels)
    # ------------------------------------------------------------------

    def _conduct_interactions(self) -> None:
        """Per-step energy routing through six combined channels.

        Partnered adults use direct reciprocity (interact with partner).
        Unpartnered adults use layered priority: kin → spatial → group → random.
        Reputation gating is applied on top of the selected recipient for
        non-partnership interactions (unless random_benefit_routing=True).
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
        partner_helped_me: dict[int, bool] = {}

        for donor in active:
            # --- Direct reciprocity (partnered) ---
            if donor.partner_id is not None:
                partner = id_to_ind.get(donor.partner_id)
                if partner is not None:
                    eff = donor.helping_trait * max(0.0, 1.0 - rw * (1.0 - donor.partner_memory))
                    eligible_count[donor.id] += 1
                    if self.rng.random() < eff:
                        partner.energy = min(max_e, partner.energy + benefit)
                        help_count[donor.id] += 1
                        partner_helped_me[partner.id] = True
                    continue

            # --- Unpartnered: layered recipient selection ---
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
                if self.rng.random() < donor.helping_trait:
                    recipient.energy = min(max_e, recipient.energy + benefit)
                    help_count[donor.id] += 1
            else:
                if self.rng.random() < q:
                    if recipient.reputation >= threshold:
                        eligible_count[donor.id] += 1
                        if self.rng.random() < donor.helping_trait:
                            recipient.energy = min(max_e, recipient.energy + benefit)
                            help_count[donor.id] += 1

        # Update partner memories.
        smoothing = float(self.config["memory_smoothing"])
        for ind in active:
            if ind.partner_id is not None:
                got_helped = partner_helped_me.get(ind.id, False)
                ind.partner_memory = clamp01(
                    (1.0 - smoothing) * ind.partner_memory + smoothing * float(got_helped)
                )

        # Update reputations.
        for ind in active:
            n = eligible_count[ind.id]
            if n > 0:
                ind.reputation = clamp01(
                    (1.0 - update_weight) * ind.reputation
                    + update_weight * (help_count[ind.id] / n)
                )

    # ------------------------------------------------------------------
    # Norm enforcement
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

    # ------------------------------------------------------------------
    # Group selection: inter-group conflict
    # ------------------------------------------------------------------

    def _apply_group_conflict(self) -> None:
        """Two groups compete: higher mean helping_trait wins an energy transfer."""
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
        m1 = float(np.mean([i.helping_trait for i in by_group[g1]]))
        m2 = float(np.mean([i.helping_trait for i in by_group[g2]]))

        if m1 >= m2:
            winner, loser = by_group[g1], by_group[g2]
        else:
            winner, loser = by_group[g2], by_group[g1]

        for ind in winner:
            ind.energy = min(float(self.config["max_energy"]), ind.energy + winner_bonus)
        for ind in loser:
            ind.energy -= loser_penalty

    # ------------------------------------------------------------------
    # Survival
    # ------------------------------------------------------------------

    def _apply_survival(self) -> int:
        adult_s = float(self.config["adult_survival_probability"])
        elder_s = float(self.config["elder_survival_probability"])
        juv_s = float(self.config["base_juvenile_survival_probability"])
        max_age = int(self.config["max_age"])
        survivors = []
        deaths = 0
        for ind in self.individuals:
            if ind.age >= max_age or ind.energy <= 0.0:
                deaths += 1
                continue
            if ind.stage == STAGE_JUVENILE:
                if self.rng.random() > juv_s:
                    deaths += 1
                    continue
            elif ind.stage == STAGE_ADULT:
                if self.rng.random() > adult_s:
                    deaths += 1
                    continue
            else:
                if self.rng.random() > elder_s:
                    deaths += 1
                    continue
            survivors.append(ind)
        self.individuals = survivors
        return deaths

    # ------------------------------------------------------------------
    # Reproduction (all four mate-preference channels combined)
    # ------------------------------------------------------------------

    def _reproduce(self) -> dict[str, int]:
        """Mate weights combine reputation, group, spatial, and kin preferences
        multiplicatively:
          w = rep_w × grp_w × spatial_w × kin_w
        where each factor is 1 + pref_strength if condition met, baseline otherwise.
        """
        female_min = int(self.config["female_min_reproduction_age"])
        female_max = int(self.config["female_max_reproduction_age"])
        male_min = int(self.config["male_min_reproduction_age"])
        male_max = int(self.config["male_max_reproduction_age"])
        repr_prob = float(self.config["female_reproduction_probability"])
        e_thresh = float(self.config["reproduction_energy_threshold"])
        e_cost = float(self.config["reproduction_energy_cost"])
        cost_scale = float(self.config["helping_reproduction_cost_scale"])
        rep_pref = float(self.config["reputation_mate_preference"])
        grp_pref = float(self.config["group_mate_preference"])
        kin_pref = float(self.config["kin_mate_preference"])
        spatial_pref = float(self.config["spatial_mate_preference"])
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
            if self.rng.random() > repr_prob * (1.0 - mother.helping_trait * cost_scale):
                continue

            # Compute spatial distances to eligible males (toroidal).
            dx = np.abs(male_xs - mother.x)
            dy = np.abs(male_ys - mother.y)
            dx = np.minimum(dx, width - dx)
            dy = np.minimum(dy, width - dy)
            dists = np.sqrt(dx * dx + dy * dy)

            mother_kin_ids = {k.id for k in self._kin_index.get(mother.id, [])}

            weights = np.ones(len(eligible_males))
            for idx, m in enumerate(eligible_males):
                rep_w = m.reputation * rep_pref + (1.0 - rep_pref)
                grp_w = (1.0 + grp_pref) if m.group_id == mother.group_id else 1.0
                spatial_w = (1.0 + spatial_pref) if dists[idx] <= spatial_radius else 1.0
                kin_w = (1.0 + kin_pref) if m.id in mother_kin_ids else 1.0
                weights[idx] = rep_w * grp_w * spatial_w * kin_w

            total = float(weights.sum())
            if total <= 0.0:
                father = eligible_males[int(self.rng.integers(0, len(eligible_males)))]
            else:
                father_idx = int(self.rng.choice(len(eligible_males), p=weights / total))
                father = eligible_males[father_idx]

            mother.energy -= e_cost
            child = self._create_child(mother, father, initial_child=False)
            new_children.append(child)
            births += 1
            if mother.id in self.offspring_counts:
                self.offspring_counts[mother.id] += 1
            if father.id in self.offspring_counts:
                self.offspring_counts[father.id] += 1

        self.individuals.extend(new_children)
        return {"births": births}

    # ------------------------------------------------------------------
    # Density mortality
    # ------------------------------------------------------------------

    def _apply_density_mortality(self) -> int:
        max_pop = int(self.config["max_population"])
        if len(self.individuals) <= max_pop:
            return 0
        excess = len(self.individuals) - max_pop
        indices = self.rng.choice(len(self.individuals), size=excess, replace=False)
        keep = sorted(set(range(len(self.individuals))) - set(indices))
        self.individuals = [self.individuals[i] for i in keep]
        return excess

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _mean_helping_trait(self) -> float:
        if not self.individuals:
            return 0.0
        return float(np.mean([i.helping_trait for i in self.individuals]))

    def _compute_metrics(self) -> dict[str, float]:
        adults = [i for i in self.individuals if i.stage in {STAGE_ADULT, STAGE_ELDER}]
        if not adults:
            return {
                "mean_helping_trait": 0.0,
                "mean_reputation": 0.0,
                "helping_invasion_frequency": 0.0,
                "norm_violation_rate": 0.0,
                "mean_partner_memory": 0.0,
            }
        threshold = float(self.config["helping_trait_invasion_threshold"])
        sensitivity = float(self.config["norm_detection_sensitivity"])
        traits = [i.helping_trait for i in self.individuals]
        reps = [i.reputation for i in adults]
        mean_rep = float(np.mean(reps))

        partnered = [i for i in adults if i.partner_id is not None]
        mean_pm = float(np.mean([i.partner_memory for i in partnered])) if partnered else math.nan

        return {
            "mean_helping_trait": float(np.mean(traits)),
            "mean_reputation": mean_rep,
            "helping_invasion_frequency": float(np.mean([t >= threshold for t in traits])),
            "norm_violation_rate": float(np.mean([i.reputation < mean_rep - sensitivity for i in adults])),
            "mean_partner_memory": mean_pm,
        }

    def _record_history(self, *, births: int, deaths: int) -> None:
        m = self._compute_metrics()
        self.history["step"].append(self.step_index)
        self.history["population"].append(len(self.individuals))
        self.history["births"].append(births)
        self.history["deaths"].append(deaths)
        for k, v in m.items():
            self.history[k].append(v)

    def summary(self) -> dict[str, Any]:
        initial_mean = self.initial_mean_helping_trait
        final_mean = self.history["mean_helping_trait"][-1] if self.history["mean_helping_trait"] else 0.0
        initial_inv = self.history["helping_invasion_frequency"][0] if self.history["helping_invasion_frequency"] else 0.0
        final_inv = self.history["helping_invasion_frequency"][-1] if self.history["helping_invasion_frequency"] else 0.0
        return {
            "helping_trait_change": final_mean - initial_mean,
            "helping_invasion_frequency_change": final_inv - initial_inv,
            "final_population": len(self.individuals),
            "latest_mean_reputation": self.history["mean_reputation"][-1] if self.history["mean_reputation"] else 0.0,
            "latest_norm_violation_rate": self.history["norm_violation_rate"][-1] if self.history["norm_violation_rate"] else 0.0,
            "latest_mean_partner_memory": self.history["mean_partner_memory"][-1] if self.history["mean_partner_memory"] else math.nan,
        }


# ------------------------------------------------------------------
# Run helpers
# ------------------------------------------------------------------

def run_simulation(run_config: Mapping[str, Any]) -> dict[str, Any]:
    model = TopDownCooperationModel(run_config)
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
    model = TopDownCooperationModel(active_config)
    steps = int(active_config["simulation_steps"])
    for i in range(steps):
        model.step()
        if (i + 1) % 100 == 0:
            s = model.summary()
            print(
                f"step {i+1:4d}  pop={len(model.individuals):4d}"
                f"  trait={s['helping_trait_change']:+.4f}"
                f"  inv={s['helping_invasion_frequency_change']:+.4f}"
                f"  rep={s['latest_mean_reputation']:.3f}"
                f"  pm={s['latest_mean_partner_memory']:.3f}"
            )
    if bool(active_config.get("write_latest_run", True)):
        _write_latest_run(
            {"config": active_config, "history": dict(model.history), "summary": model.summary()},
            str(active_config.get("data_dir", ".")),
        )
    s = model.summary()
    print(
        f"\nfinal: trait_Δ={s['helping_trait_change']:+.4f}"
        f"  inv_Δ={s['helping_invasion_frequency_change']:+.4f}"
        f"  pop={s['final_population']}"
        f"  rep={s['latest_mean_reputation']:.3f}"
    )


if __name__ == "__main__":
    main()
