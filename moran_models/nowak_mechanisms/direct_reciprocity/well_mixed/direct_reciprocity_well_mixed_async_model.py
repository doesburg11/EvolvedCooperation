#!/usr/bin/env python3
"""Asynchronous well-mixed direct-reciprocity Moran model.

This variant keeps the same pair persistence, repeated pair games, strategy
rules, and pair-specific memory as the synchronous well-mixed model. It differs
only in replacement: each step chooses one parent from the whole population by
fitness and one uniformly random death site to overwrite.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .config.direct_reciprocity_well_mixed_async_config import config
from .direct_reciprocity_well_mixed_model import (
    COOPERATE,
    STRATEGY_NAMES,
    DirectReciprocityWellMixedModel,
)


class DirectReciprocityWellMixedAsyncModel(DirectReciprocityWellMixedModel):
    """Well-mixed direct reciprocity with one-birth/one-death replacement."""

    name = "direct_reciprocity_well_mixed_async"

    def _global_softmax_probabilities(self, fitness: np.ndarray) -> np.ndarray:
        temperature = max(float(self.cfg["selection_temperature"]), 1e-9)
        centered = (fitness - float(fitness.max())) / temperature
        exp_values = np.exp(centered)
        denominator = float(exp_values.sum())
        if denominator <= 0.0:
            return np.full_like(exp_values, 1.0 / len(exp_values), dtype=float)
        return exp_values / denominator

    def _copy_parent_memory_to_death_site(self, parent: int, death: int) -> None:
        old_action = self.last_action.copy()
        old_payoff = self.last_payoff.copy()
        self.last_action[death, :] = old_action[parent, :]
        self.last_action[:, death] = old_action[:, parent]
        self.last_payoff[death, :] = old_payoff[parent, :]
        self.last_payoff[:, death] = old_payoff[:, parent]

    def _reset_death_site_memory(self, death: int) -> None:
        self.last_action[death, :] = COOPERATE
        self.last_action[:, death] = COOPERATE
        self.last_payoff[death, :] = float(self.cfg["wsls_aspiration_payoff"])
        self.last_payoff[:, death] = float(self.cfg["wsls_aspiration_payoff"])

    def _apply_moran_replacement(self, fitness: np.ndarray) -> None:
        parent_probabilities = self._global_softmax_probabilities(fitness)
        parent = int(self.rng.choice(self.n_sites, p=parent_probabilities))
        death = int(self.rng.integers(0, self.n_sites))

        inherited_strategy = int(self.strategy[parent])
        mutated = self.rng.random() < float(self.cfg["mutation_rate"])
        if mutated:
            offset = int(self.rng.integers(1, len(STRATEGY_NAMES)))
            inherited_strategy = (inherited_strategy + offset) % len(STRATEGY_NAMES)

        replacement_changed_identity = parent != death or mutated
        self.strategy[death] = inherited_strategy
        self.lineage[death] = self.lineage[parent]

        if not replacement_changed_identity:
            return

        if bool(self.cfg["reset_memory_on_replacement"]):
            self._reset_death_site_memory(death)
        else:
            self._copy_parent_memory_to_death_site(parent, death)


def _write_log(payload: dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_simulation() -> dict[str, Any]:
    runtime_cfg = dict(config)
    model = DirectReciprocityWellMixedAsyncModel(runtime_cfg)
    payload = model.run()

    if bool(runtime_cfg.get("write_log", True)):
        _write_log(payload, str(runtime_cfg["log_output_path"]))
        print(f"[direct_reciprocity_well_mixed_async] wrote log -> {runtime_cfg['log_output_path']}")
    return payload


if __name__ == "__main__":
    run_simulation()
