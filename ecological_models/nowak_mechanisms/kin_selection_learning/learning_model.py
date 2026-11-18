"""Kin selection with learned helping (design: README.md in this folder).

Version A is the unchanged ecological kin-selection model. In versions B and C every adult and elder acts with a
learned care effort instead of its inherited helping trait:

    eps ~ N(0, sigma),  a = clamp01(e + eps)       care budget = a * care_capacity (as h * care_capacity before)
    r = -(care energy cost paid this step) - k * V * (household juveniles that died this step)
    e <- clamp01(e + alpha * ((r - b) / s) * eps / sigma),   b <- b + beta * (r - b)
    s = care_cost_per_unit * capacity + k * V        (the learner's maximum stake per step and unit effort;
                                                      capacity includes the grandmother multiplier)

Dividing by s puts the kin term (about ten times the cost term) and the cost term on one scale, so one learning
rate serves both kinds of learner; unlike a running-spread normalization it does not blow pure noise up to full-size
steps when a learner's reward hardly depends on its action. The update uses the unclipped noise eps (the Gaussian
score function, clipping treated as part of the world): with the clipped a - e instead, a drifting baseline pushes
effort to 0 or 1 even when the reward carries no signal. The first reward only sets b.

A learner learns (updates e and b) only on steps where it could help: rearing dependency and care benefit are on, it
is above the helper energy reserve and its group has a juvenile, the base model's conditions for giving care. On other steps its action has no consequence and
its reward would be noise.

k = 0 in B (selfish learner). In C, k is the individual's inherited helping_trait, which the base model inherits
and mutates exactly as before, so in C the inherited trait is the kin-regard weight and never sets care directly.
e starts at initial_effort the first step an individual is an adult or elder and is not inherited.

Options used by the confirmation test (README): alpha = 0 means no updates (effort stays at initial_effort, so with
exploration_stddev 0 every carer acts at a constant effort); frozen_kin_regard = True makes every child draw its
helping_trait (k in C) from the founder distribution instead of from its parents, so k is not heritable.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Mapping

import numpy as np

from ..kin_selection.kin_selection_model import (
    SEX_FEMALE,
    STAGE_ADULT,
    STAGE_ELDER,
    STAGE_JUVENILE,
    EcologicalKinSelectionModel,
    clamp01,
)


class LearnedHelpingModel(EcologicalKinSelectionModel):
    def __init__(self, run_config: Mapping[str, Any], version: str, learning: Mapping[str, Any]):
        if version not in ("A", "B", "C"):
            raise ValueError(f"version must be A, B or C (got {version!r})")
        if version != "A" and learning.get("alpha") is None:
            raise ValueError("learning['alpha'] must be set for versions B and C")
        self.version = version
        self.learning = dict(learning)
        self.effort: dict[int, float] = {}
        self.baseline: dict[int, float | None] = {}
        self._pending: dict[int, tuple[float, float, float, float]] = {}  # id -> (action, effort, care cost, eps)
        self._household_juveniles: dict[int, set[int]] = {}
        self._last_mean_action = math.nan
        # separate stream for frozen k draws, so C-frozen shares C's main random stream
        self._frozen_rng = np.random.default_rng([int(run_config.get("random_seed", 0)), 7919])
        super().__init__(run_config)

    # ---- helpers -------------------------------------------------------------------------------------------
    def _is_carer(self, individual) -> bool:
        return individual.stage in (STAGE_ADULT, STAGE_ELDER)

    def capacity(self, individual) -> float:
        """Care capacity at effort 1, as in the base care rule (grandmothers get the multiplier)."""
        cap = float(self.config["care_capacity_per_helper"])
        if (bool(self.config["enable_grandmother_effects"]) and individual.sex == SEX_FEMALE
                and individual.stage == STAGE_ELDER):
            cap *= float(self.config["grandmother_care_capacity_multiplier"])
        return cap

    def kin_regard(self, individual) -> float:
        return float(individual.helping_trait) if self.version == "C" else 0.0

    def mean_expressed_helping(self) -> float:
        carers = [i for i in self.individuals if self._is_carer(i)]
        if not carers:
            return math.nan
        if self.version == "A":
            return float(np.mean([i.helping_trait for i in carers]))
        e0 = float(self.learning["initial_effort"])
        return float(np.mean([self.effort.get(i.id, e0) for i in carers]))

    # ---- overridden steps ----------------------------------------------------------------------------------
    def _provide_care(self):
        if self.version == "A":
            return super()._provide_care()
        sigma = float(self.learning["exploration_stddev"])
        cost_per_unit = float(self.config["care_cost_per_unit"])
        e0 = float(self.learning["initial_effort"])
        genes, energy_before = {}, {}
        self._pending = {}
        reserve = float(self.config["helper_energy_reserve"])
        care_matters = bool(self.config["enable_rearing_dependency"]) and bool(self.config["enable_care_benefit"])
        groups_with_juveniles = (
            {i.group_id for i in self.individuals if i.stage == STAGE_JUVENILE} if care_matters else set()
        )
        for ind in self.individuals:
            if not self._is_carer(ind):
                continue
            if ind.energy <= reserve or ind.group_id not in groups_with_juveniles:
                self.effort.setdefault(ind.id, e0)  # no chance to help: acts at e, no learning this step
                self.baseline.setdefault(ind.id, None)
                genes[ind.id] = ind.helping_trait
                ind.helping_trait = self.effort[ind.id]
                continue
            e = self.effort.setdefault(ind.id, e0)
            self.baseline.setdefault(ind.id, None)
            eps = float(self.rng.normal(0.0, sigma))
            action = clamp01(e + eps)
            genes[ind.id] = ind.helping_trait
            energy_before[ind.id] = ind.energy
            ind.helping_trait = action  # the base care rule reads helping_trait as the care effort
            self._pending[ind.id] = (action, e, 0.0, eps)
        try:
            result = super()._provide_care()
        finally:
            for ind in self.individuals:
                if ind.id in genes:
                    ind.helping_trait = genes[ind.id]
        acts = [v[0] for v in self._pending.values()]
        self._last_mean_action = float(np.mean(acts)) if acts else math.nan
        for ind in self.individuals:
            if ind.id in self._pending:
                action, e, _, eps = self._pending[ind.id]
                # _provide_care changes energy only by the care cost
                self._pending[ind.id] = (action, e, energy_before[ind.id] - ind.energy, eps)
        return result

    def _apply_survival(self, care_by_juvenile, care_relatedness_by_juvenile):
        if self.version == "A":
            return super()._apply_survival(care_by_juvenile, care_relatedness_by_juvenile)
        before: dict[int, set[int]] = defaultdict(set)
        for ind in self.individuals:
            if ind.stage == STAGE_JUVENILE and ind.household_id is not None:
                before[ind.household_id].add(ind.id)
        result = super()._apply_survival(care_by_juvenile, care_relatedness_by_juvenile)
        alive = {ind.id for ind in self.individuals}
        deaths = {h: sum(1 for j in ids if j not in alive) for h, ids in before.items()}
        self._learn(deaths)
        return result

    def _create_child(self, mother, father, *, initial_child: bool):
        child = super()._create_child(mother, father, initial_child=initial_child)
        if self.learning.get("frozen_kin_regard", False):
            if self._frozen_rng.random() < float(self.config["rare_helper_founder_probability"]):
                child.helping_trait = float(self.config["rare_helper_trait_value"])
            else:
                child.helping_trait = float(self._frozen_rng.uniform(float(self.config["initial_helping_trait_min"]),
                                                                     float(self.config["initial_helping_trait_max"])))
        return child

    def _learn(self, household_deaths: Mapping[int, int]) -> None:
        if float(self.learning["alpha"]) == 0.0:  # no updates (and no division by a zero sigma)
            self._pending = {}
            return
        sigma = float(self.learning["exploration_stddev"])
        cost_per_unit = float(self.config["care_cost_per_unit"])
        alpha = float(self.learning["alpha"])
        beta = float(self.learning["baseline_rate"])
        value = float(self.learning["juvenile_energy_value"])
        for ind in self.individuals:  # survivors only; dead learners are dropped below
            if ind.id not in self._pending:
                continue
            action, e, cost, eps = self._pending[ind.id]
            lost = household_deaths.get(ind.household_id, 0) if ind.household_id is not None else 0
            reward = -cost - self.kin_regard(ind) * value * lost
            b = self.baseline[ind.id]
            if b is None:
                self.baseline[ind.id] = reward
                continue
            stake = cost_per_unit * self.capacity(ind) + self.kin_regard(ind) * value
            self.effort[ind.id] = clamp01(e + alpha * ((reward - b) / stake) * eps / sigma)
            self.baseline[ind.id] = b + beta * (reward - b)
        alive = {ind.id for ind in self.individuals}
        for d in (self.effort, self.baseline):
            for i in [i for i in d if i not in alive]:
                del d[i]
        self._pending = {}

    def _record_history(self, **kwargs):
        super()._record_history(**kwargs)
        self.history["mean_expressed_helping"].append(self.mean_expressed_helping())
        # realized mean action of carers that could help this step (B/C only; nan for A or no such carer)
        self.history["mean_care_action"].append(self._last_mean_action)
        self._last_mean_action = math.nan


def run_version(run_config: Mapping[str, Any], version: str, learning: Mapping[str, Any]) -> dict[str, Any]:
    model = LearnedHelpingModel({**run_config, "write_latest_run": False}, version, learning)
    return model.run()
