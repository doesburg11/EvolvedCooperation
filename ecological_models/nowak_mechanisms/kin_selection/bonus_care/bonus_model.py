"""Bonus-care kin-selection model (pre-registration: README.md in this folder, commit 4b300ed).

Extends the survival-floor model (floor 0) with:

- random birth slots: eligible females are taken in random order each step, so when the cap leaves fewer slots than
  eligible females, slots go at random instead of to whoever is first in the population list;
- allele mutation (amendment 1): each inherited genome allele becomes a new unique allele with probability
  allele_mutation, so background relatedness reaches a mutation-drift balance instead of drifting up;
- care_counts / care_costs: helper care can be switched off for survival independently of its energy cost.
  Main arms: both on. Neutral arms (K-N, U-N): neither. Cost probe: care costs energy but does not count.

Lifetime births per female are the base model's offspring_counts.
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from ..floor_control.floor_model import FloorKinSelectionModel


class BonusCareModel(FloorKinSelectionModel):
    def __init__(self, run_config: Mapping[str, Any], care_counts: bool = True, allele_mutation: float = 0.0):
        if not 0.0 <= allele_mutation <= 1.0:
            raise ValueError("allele_mutation must be in [0, 1]")
        self.allele_mutation = float(allele_mutation)
        cost = float(run_config.get("care_cost_per_unit", 1.0))
        # FloorKinSelectionModel ties "care not counted" to zero cost; build it with neutral=False and set the
        # counting switch afterwards, so the cost probe can pay for care that does not count.
        super().__init__(run_config, floor=0.0, neutral=False)
        self.neutral = not care_counts
        self.care_counts = bool(care_counts)
        self.care_costs = cost > 0.0

    def _inherit_genome(self, mother_genome, father_genome):
        genome = super()._inherit_genome(mother_genome, father_genome)
        if self.allele_mutation > 0.0:
            hit = self.rng.random(genome.shape) < self.allele_mutation
            n = int(hit.sum())
            if n:
                genome = genome.copy()
                genome[hit] = np.arange(self.next_allele_id, self.next_allele_id + n, dtype=np.int64)
                self.next_allele_id += n
        return genome

    def mean_random_adult_relatedness(self, pairs: int, rng) -> float:
        """Mean genomic relatedness of random pairs of distinct living adults (a separate rng, not the model's)."""
        from ..kin_selection_model import STAGE_ADULT, genetic_relatedness
        adults = [i for i in self.individuals if i.stage == STAGE_ADULT]
        if len(adults) < 2:
            return float("nan")
        vals = []
        for _ in range(pairs):
            a, b = rng.choice(len(adults), 2, replace=False)
            vals.append(genetic_relatedness(adults[a].genome, adults[b].genome))
        return float(np.mean(vals))

    def _reproduce(self):
        order = self.rng.permutation(len(self.individuals))
        self.individuals = [self.individuals[i] for i in order]
        return super()._reproduce()

    def matured_females(self, born_range: tuple[int, int]) -> list[dict[str, float]]:
        """Females born in born_range (inclusive) that reached maturity, with their own h and lifetime births."""
        lo, hi = born_range
        return [{"h": rec["h"], "births": float(self.offspring_counts.get(i, 0))}
                for i, rec in self.birth_record.items()
                if lo <= rec["born"] <= hi and not rec["male"] and i in self._credited]
