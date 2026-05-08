#!/usr/bin/env python3
"""Well-mixed indirect reciprocity model with reputation channel and no spatial structure.

Unlike the grid-based indirect_reciprocity_model, this model uses a flat population
with global interaction and global Moran replacement. There is no spatial neighborhood:
each agent's cooperative benefit is distributed to ALL other agents weighted by
reputation, and any agent can replace any other.

This isolates the reputation channel from the network-reciprocity effect that a
spatial grid would otherwise provide, allowing a clean test of Nowak's theoretical
claim that indirect reciprocity cannot spread from rare in a well-mixed population.

Payoff per step
---------------
Agent i produces benefit  B_i = B_plus_scale * h_i
and pays cost             C_i = C_scale * h_i.

The benefit B_i is distributed across all agents j weighted by their reputation:

    received[j] = sum_i  B_i * w_j / sum_k w_k

where  w_j = reputation_kernel_bias + reputation_j ^ reputation_kernel_exponent.

This is the mean-field (N → ∞) limit of the per-row-normalized routing kernel
used in the spatial engine. With no spatial assortment, the only path to a
cooperation advantage is through the reputation → routing feedback loop.

Reputation update
-----------------
After payoffs are resolved but before replacement:

    rep_new = (1 - obs_weight) * rep + obs_weight * h

Offspring inherit their parent's reputation; mutation perturbs the trait only.

Moran replacement
-----------------
Synchronous: for every position, a parent is sampled from the GLOBAL pool using
softmax-fitness proportionate selection (temperature-controlled). This matches the
synchronous update used by the direct-reciprocity well-mixed model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from moran_models.interaction_kernel.core.selection import sample_local_parent_indices

from .config.indirect_reciprocity_well_mixed_config import config


class IndirectReciprocityWellMixedModel:
    """Well-mixed indirect reciprocity — reputation channel, no grid."""

    name = "indirect_reciprocity_well_mixed"

    def __init__(self, cfg: dict[str, Any]):
        self.cfg = dict(cfg)
        self.n = int(self.cfg["n_agents"])
        self.rng = np.random.default_rng(int(self.cfg["random_seed"]))

        # Global replacement neighborhood: every agent sees every other.
        self._global_neighbors = [np.arange(self.n, dtype=np.int32)] * self.n

        # Trait and reputation initialisation.
        mean = float(self.cfg["initial_trait_mean"])
        std = float(self.cfg["initial_trait_stddev"])
        self.h = np.clip(self.rng.normal(mean, std, self.n), 0.0, 1.0)
        self.rep = np.full(self.n, float(self.cfg["reputation_default"]), dtype=float)

        self.history: list[dict[str, float]] = []
        self.step_index = 0

    def _routing_weights(self) -> np.ndarray:
        bias = float(self.cfg["reputation_kernel_bias"])
        exponent = float(self.cfg["reputation_kernel_exponent"])
        return bias + np.power(np.clip(self.rep, 0.0, 1.0), exponent)

    def _compute_payoffs(self) -> np.ndarray:
        """Mean-field payoff: received[j] = total_benefit * w_j / total_weight."""
        B = float(self.cfg["B_plus_scale"]) * self.h
        C = float(self.cfg["C_scale"]) * self.h
        w = self._routing_weights()
        total_w = float(w.sum())
        if total_w <= 0.0:
            received = np.zeros(self.n, dtype=float)
        else:
            received = float(B.sum()) * w / total_w
        return float(self.cfg["base_fitness"]) + received - C

    def _update_reputation(self) -> None:
        obs_weight = float(self.cfg["reputation_observation_weight"])
        self.rep = np.clip(
            (1.0 - obs_weight) * self.rep + obs_weight * self.h,
            0.0,
            1.0,
        )

    def _moran_replacement(self, fitness: np.ndarray) -> None:
        parent_indices = sample_local_parent_indices(
            fitness,
            self._global_neighbors,
            self.rng,
            float(self.cfg["selection_temperature"]),
        )
        next_h = self.h[parent_indices].copy()
        mutation_rate = float(self.cfg["mutation_rate"])
        mutation_std = float(self.cfg["mutation_stddev"])
        mutate_mask = self.rng.random(self.n) < mutation_rate
        if np.any(mutate_mask):
            next_h[mutate_mask] += self.rng.normal(
                0.0, mutation_std, size=int(np.sum(mutate_mask))
            )
        self.h = np.clip(next_h, 0.0, 1.0)
        self.rep = self.rep[parent_indices].copy()

    def step(self) -> dict[str, float]:
        fitness = self._compute_payoffs()
        self._update_reputation()
        self._moran_replacement(fitness)
        metrics = {
            "step": float(self.step_index + 1),
            "mean_trait": float(np.mean(self.h)),
            "mean_reputation": float(np.mean(self.rep)),
            "mean_fitness": float(np.mean(fitness)),
        }
        self.history.append(metrics)
        self.step_index += 1
        return metrics

    def run(self) -> dict[str, Any]:
        n_steps = int(self.cfg["simulation_steps"])
        interval = max(1, int(self.cfg["summary_interval_steps"]))
        for t in range(n_steps):
            m = self.step()
            if (t + 1) % interval == 0 or t == 0 or (t + 1) == n_steps:
                print(
                    f"[{self.name}] step={t + 1:4d}/{n_steps} "
                    f"mean_trait={m['mean_trait']:.4f} "
                    f"mean_rep={m['mean_reputation']:.4f}"
                )
        return {
            "final_mean_trait": float(np.mean(self.h)),
            "final_std_trait": float(np.std(self.h)),
            "final_mean_reputation": float(np.mean(self.rep)),
            "history": self.history,
        }


def _write_log(payload: dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_simulation(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime_cfg = dict(config if cfg is None else cfg)
    model = IndirectReciprocityWellMixedModel(runtime_cfg)
    payload = model.run()
    if bool(runtime_cfg.get("write_log", True)):
        _write_log(payload, str(runtime_cfg["log_output_path"]))
        print(f"[indirect_reciprocity_well_mixed] wrote log -> {runtime_cfg['log_output_path']}")
    return payload


if __name__ == "__main__":
    run_simulation()
