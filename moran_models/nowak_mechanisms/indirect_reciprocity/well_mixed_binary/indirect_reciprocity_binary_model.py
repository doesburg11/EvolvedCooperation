#!/usr/bin/env python3
"""Binary pairwise indirect reciprocity model — Nowak's exact formulation.

Unlike the continuous reputation-routing model, this implements the binary
help/no-help decision that underlies Nowak's theoretical condition q > c/b.

Mechanism
---------
Each step, N donor–recipient pairings are sampled uniformly.  For each pair:

  1. Donor i observes recipient j's reputation with probability q
     (the "reputation observation probability").
  2. If i observes j's reputation AND rep_j >= threshold:
         i helps j with probability h_i  (i's cooperativeness trait)
         Cost -c to i, benefit +b to j.
  3. If i does not observe j's reputation, or rep_j < threshold: no help.

Reputation update
-----------------
After all pairings, each agent i's reputation is updated as an exponential
moving average of its observed helping rate during the step:

    rep_new = (1 - w) * rep + w * (help_count / donor_count)

Agents not selected as donors this step retain their current reputation.

Moran replacement
-----------------
Synchronous, global softmax fitness-proportionate selection.  Offspring
inherit parent's (h, rep); mutation perturbs the trait only.

Nowak's condition
-----------------
For cooperation to invade and be maintained in a well-mixed population:
    q > c / b

With defaults c=0.2, b=1.0, the critical q = 0.2.
- q = 0.80 (>> 0.2): cooperation spreads from rare and is maintained.
- q = 0.05 (<  0.2): defectors dominate; cooperation cannot invade.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from moran_models.interaction_kernel.core.selection import sample_local_parent_indices

from .config.indirect_reciprocity_binary_config import config


class IndirectReciprocityBinaryModel:
    """Binary pairwise indirect reciprocity — Nowak's q > c/b model."""

    name = "indirect_reciprocity_binary"

    def __init__(self, cfg: dict[str, Any]):
        self.cfg = dict(cfg)
        self.n = int(self.cfg["n_agents"])
        self.rng = np.random.default_rng(int(self.cfg["random_seed"]))

        # Global replacement: every agent can replace every other.
        self._global_neighbors = [np.arange(self.n, dtype=np.int32)] * self.n

        # Trait h_i ∈ [0,1]: probability that i helps when conditions are met.
        mean = float(self.cfg["initial_trait_mean"])
        std = float(self.cfg["initial_trait_stddev"])
        cooperators = np.clip(self.rng.normal(mean, std, self.n), 0.0, 1.0)
        defector_fraction = float(self.cfg.get("initial_defector_fraction", 0.0))
        if defector_fraction > 0.0:
            n_def = int(round(self.n * defector_fraction))
            cooperators[:n_def] = 0.0
            self.rng.shuffle(cooperators)
        self.h = cooperators

        # Reputation rep_i ∈ [0,1]: public image, updated by observed helping.
        self.rep = np.full(self.n, float(self.cfg["reputation_default"]), dtype=float)

        self.history: list[dict[str, float]] = []
        self.step_index = 0

    def _pairings_and_payoffs(self) -> np.ndarray:
        n = self.n
        q = float(self.cfg["reputation_observation_prob"])
        threshold = float(self.cfg["reputation_threshold"])
        b = float(self.cfg["b_benefit"])
        c = float(self.cfg["c_cost"])
        obs_weight = float(self.cfg["reputation_observation_weight"])

        # Sample N donor-recipient pairs uniformly (avoid self-pairing).
        donors = self.rng.integers(0, n, size=n)
        recipients = self.rng.integers(0, n, size=n)
        same = donors == recipients
        recipients[same] = (recipients[same] + 1) % n

        # Step 1: donor observes recipient's reputation with probability q.
        knows_rep = self.rng.random(n) < q

        # Step 2: recipient's reputation passes threshold?
        rep_good = self.rep[recipients] >= threshold

        # Step 3: donor decides to help (prob h_i) when both conditions hold.
        will_help = self.rng.random(n) < self.h[donors]
        helped = knows_rep & rep_good & will_help

        # Payoffs.
        payoff = np.full(n, float(self.cfg["base_fitness"]))
        np.add.at(payoff, donors[helped], -c)
        np.add.at(payoff, recipients[helped], b)

        # Reputation update — standing rule: only count interactions where the
        # donor observed a good-reputation recipient (i.e. the donor HAD information
        # and the recipient deserved help).  Non-help due to unknown recipient rep
        # or bad recipient rep is NOT a reputation penalty for the donor.
        observable = knows_rep & rep_good
        help_sum = np.zeros(n)
        observable_count = np.zeros(n, dtype=np.int32)
        np.add.at(help_sum, donors[observable], helped[observable].astype(float))
        np.add.at(observable_count, donors[observable], 1)

        active = observable_count > 0
        obs_rate = np.where(active, help_sum / np.maximum(observable_count, 1), self.rep)
        self.rep = np.clip(
            np.where(active, (1.0 - obs_weight) * self.rep + obs_weight * obs_rate, self.rep),
            0.0,
            1.0,
        )

        return payoff

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
        fitness = self._pairings_and_payoffs()
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
    model = IndirectReciprocityBinaryModel(runtime_cfg)
    payload = model.run()
    if bool(runtime_cfg.get("write_log", True)):
        _write_log(payload, str(runtime_cfg["log_output_path"]))
        print(f"[indirect_reciprocity_binary] wrote log -> {runtime_cfg['log_output_path']}")
    return payload


if __name__ == "__main__":
    run_simulation()
