"""Ecological kin-selection model with a survival floor (design: README.md in this folder).

floor f: every juvenile receives f care units of external care, added to helper care before saturation, so survival
is base + benefit * min(f + helper care, saturation). It costs no one energy and does not depend on any trait.

neutral: helper care is not counted toward survival and care costs nothing (care_cost_per_unit must be 0 in the
config), so the helping trait has no effect; only the floor acts.

The model also records, for every individual born after the start, its own helping trait, sex, birth step, its
recruited offspring (offspring that reach maturity), and the effective helper care it received per juvenile step:
min(f + helper care, saturation) - f, averaged over the juvenile survival checks it had.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Mapping

from ..kin_selection_model import STAGE_ADULT, STAGE_JUVENILE, EcologicalKinSelectionModel


class FloorKinSelectionModel(EcologicalKinSelectionModel):
    def __init__(self, run_config: Mapping[str, Any], floor: float = 0.0, neutral: bool = False):
        if floor < 0:
            raise ValueError("floor must be >= 0")
        if neutral and float(run_config.get("care_cost_per_unit", 1.0)) != 0.0:
            raise ValueError("the neutral control needs care_cost_per_unit = 0")
        self.floor = float(floor)
        self.neutral = bool(neutral)
        self.birth_record: dict[int, dict[str, Any]] = {}
        self.care_sum: dict[int, float] = defaultdict(float)
        self.care_checks: dict[int, int] = defaultdict(int)
        self.recruited: dict[int, int] = defaultdict(int)
        self._credited: set[int] = set()
        self.saturated_checks = 0
        self.juvenile_checks = 0
        super().__init__(run_config)

    def _create_child(self, mother, father, *, initial_child: bool):
        child = super()._create_child(mother, father, initial_child=initial_child)
        self.birth_record[child.id] = {"h": float(child.helping_trait), "male": int(child.sex == "M"),
                                       "born": int(self.step_index), "mother": mother.id, "father": father.id}
        return child

    def _apply_survival(self, care_by_juvenile, care_relatedness_by_juvenile):
        sat = float(self.config["care_saturation"])
        care = {}
        for ind in self.individuals:
            if ind.stage != STAGE_JUVENILE:
                continue
            helper = 0.0 if self.neutral else float(care_by_juvenile.get(ind.id, 0.0))
            total = self.floor + helper
            care[ind.id] = total
            self.care_sum[ind.id] += min(total, sat) - min(self.floor, sat)
            self.care_checks[ind.id] += 1
            self.juvenile_checks += 1
            self.saturated_checks += int(total >= sat)
        # relatedness-weighted diagnostics keep only helper care; in the neutral arm there is none
        rel = {} if self.neutral else care_relatedness_by_juvenile
        return super()._apply_survival(care, rel)

    def _apply_maturation_dispersal(self):
        super()._apply_maturation_dispersal()
        maturity = int(self.config["juvenile_maturity_age"])
        for ind in self.individuals:
            if ind.stage == STAGE_ADULT and ind.age >= maturity and ind.id not in self._credited:
                self._credited.add(ind.id)
                rec = self.birth_record.get(ind.id)
                if rec is not None:
                    self.recruited[rec["mother"]] += 1
                    self.recruited[rec["father"]] += 1

    def cohort(self, born_range: tuple[int, int]) -> list[dict[str, float]]:
        """Individuals born in born_range (inclusive) that had at least one juvenile survival check."""
        lo, hi = born_range
        rows = []
        for i, rec in self.birth_record.items():
            if not lo <= rec["born"] <= hi or self.care_checks.get(i, 0) == 0:
                continue
            rows.append({"w": float(self.recruited.get(i, 0)), "h": rec["h"], "male": rec["male"],
                         "s": self.care_sum[i] / self.care_checks[i]})
        return rows

    def excluded_from_cohort(self, born_range: tuple[int, int]) -> int:
        lo, hi = born_range
        return sum(1 for i, rec in self.birth_record.items()
                   if lo <= rec["born"] <= hi and self.care_checks.get(i, 0) == 0)
