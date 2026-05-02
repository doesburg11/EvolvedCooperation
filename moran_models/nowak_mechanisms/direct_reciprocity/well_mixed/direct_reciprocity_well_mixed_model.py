#!/usr/bin/env python3
"""Pure direct-reciprocity Moran model with well-mixed population and repeated pair games.

Unlike the spatial sibling (direct_reciprocity_pair_game), this model uses no grid.
Each step, agents are paired uniformly at random, so cooperation can only be sustained
by pair memory and repeated interaction — not by spatial clustering.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from moran_models.interaction_kernel.core.selection import sample_local_parent_indices

from .config.direct_reciprocity_well_mixed_config import config


COOPERATE = 1
DEFECT = 0

STRATEGY_NAMES = ("ALLC", "ALLD", "TFT", "GTFT", "WSLS")
STRATEGY_IDS = {name: i for i, name in enumerate(STRATEGY_NAMES)}
RECIPROCAL_STRATEGIES = frozenset(
    {
        STRATEGY_IDS["TFT"],
        STRATEGY_IDS["GTFT"],
        STRATEGY_IDS["WSLS"],
    }
)


class DirectReciprocityWellMixedModel:
    """Well-mixed Moran model with strategy rules and pair-specific action memory."""

    name = "direct_reciprocity_well_mixed"

    def __init__(self, cfg: dict[str, Any]):
        self.cfg = dict(cfg)
        self.n_sites = int(self.cfg["n_sites"])
        self.rng = np.random.default_rng(int(self.cfg["random_seed"]))

        # Global replacement neighborhood: every site can replace every other.
        self._global_neighbors = [
            np.arange(self.n_sites, dtype=np.int32)
        ] * self.n_sites

        self.strategy = self._initialize_strategies()
        identity_count = max(1, int(self.cfg["initial_lineage_count"]))
        self.lineage = self.rng.integers(0, identity_count, size=self.n_sites, dtype=np.int32)

        self.last_action = np.full(
            (self.n_sites, self.n_sites),
            COOPERATE,
            dtype=np.int8,
        )
        self.last_payoff = np.full(
            (self.n_sites, self.n_sites),
            float(self.cfg["wsls_aspiration_payoff"]),
            dtype=float,
        )
        self.latest_payoff = np.zeros(self.n_sites, dtype=float)
        self.latest_fitness = np.full(self.n_sites, float(self.cfg["base_fitness"]), dtype=float)
        self.current_pairs: list[tuple[int, int]] = []
        self.history: list[dict[str, float]] = []
        self.step_index = 0

    def _initialize_strategies(self) -> np.ndarray:
        layout = str(self.cfg.get("initial_strategy_layout", "random"))
        if layout == "rare_invaders":
            return self._initialize_rare_invaders()
        if layout != "random":
            raise ValueError(f"Unsupported initial_strategy_layout: {layout}")

        raw_freqs = dict(self.cfg["initial_strategy_frequencies"])
        weights = np.array(
            [float(raw_freqs.get(name, 0.0)) for name in STRATEGY_NAMES],
            dtype=float,
        )
        total = float(weights.sum())
        if total <= 0.0:
            raise ValueError("initial_strategy_frequencies must contain positive total weight")
        weights = weights / total
        return self.rng.choice(len(STRATEGY_NAMES), size=self.n_sites, p=weights).astype(np.int8)

    def _initialize_rare_invaders(self) -> np.ndarray:
        strategies = np.full(self.n_sites, STRATEGY_IDS["ALLD"], dtype=np.int8)
        invader_fraction = float(self.cfg.get("rare_invaders_frequency", 0.05))
        n_invaders = max(1, min(self.n_sites, int(round(self.n_sites * invader_fraction))))
        invader_sites = self.rng.choice(self.n_sites, size=n_invaders, replace=False)

        raw_mix = dict(
            self.cfg.get(
                "invader_strategy_frequencies",
                {"TFT": 0.34, "GTFT": 0.33, "WSLS": 0.33},
            )
        )
        weights = np.array(
            [float(raw_mix.get(name, 0.0)) for name in STRATEGY_NAMES],
            dtype=float,
        )
        total = float(weights.sum())
        if total <= 0.0:
            raise ValueError("invader_strategy_frequencies must contain positive total weight")
        weights = weights / total
        strategies[invader_sites] = self.rng.choice(
            len(STRATEGY_NAMES),
            size=n_invaders,
            p=weights,
        ).astype(np.int8)
        return strategies

    def _mutate_strategies(self, strategy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mutation_rate = float(self.cfg["mutation_rate"])
        mutate_mask = self.rng.random(self.n_sites) < mutation_rate
        next_strategy = strategy.copy()
        strategy_count = len(STRATEGY_NAMES)
        for idx in np.where(mutate_mask)[0]:
            current = int(next_strategy[idx])
            offset = int(self.rng.integers(1, strategy_count))
            next_strategy[idx] = (current + offset) % strategy_count
        return next_strategy, mutate_mask

    def _choose_action(
        self,
        actor: int,
        partner: int,
        last_action: np.ndarray,
        last_payoff: np.ndarray,
    ) -> int:
        strategy = int(self.strategy[actor])
        if strategy == STRATEGY_IDS["ALLC"]:
            action = COOPERATE
        elif strategy == STRATEGY_IDS["ALLD"]:
            action = DEFECT
        elif strategy == STRATEGY_IDS["TFT"]:
            partner_previous = (
                int(last_action[partner, actor])
                if bool(self.cfg["memory_enabled"])
                else COOPERATE
            )
            action = COOPERATE if partner_previous == COOPERATE else DEFECT
        elif strategy == STRATEGY_IDS["GTFT"]:
            partner_previous = (
                int(last_action[partner, actor])
                if bool(self.cfg["memory_enabled"])
                else COOPERATE
            )
            if partner_previous == COOPERATE:
                action = COOPERATE
            else:
                forgiveness = float(self.cfg["gtft_forgiveness_probability"])
                action = COOPERATE if self.rng.random() < forgiveness else DEFECT
        elif strategy == STRATEGY_IDS["WSLS"]:
            if bool(self.cfg["memory_enabled"]):
                own_previous = int(last_action[actor, partner])
                previous_payoff = float(last_payoff[actor, partner])
            else:
                own_previous = COOPERATE
                previous_payoff = float(self.cfg["wsls_aspiration_payoff"])
            if previous_payoff >= float(self.cfg["wsls_aspiration_payoff"]):
                action = own_previous
            else:
                action = DEFECT if own_previous == COOPERATE else COOPERATE
        else:
            raise ValueError(f"Unknown strategy id: {strategy}")

        error_probability = float(self.cfg["action_error_probability"])
        if error_probability > 0.0 and self.rng.random() < error_probability:
            action = DEFECT if action == COOPERATE else COOPERATE
        return action

    def _pair_payoff(self, action_i: int, action_j: int) -> tuple[float, float]:
        temptation = float(self.cfg["temptation_payoff"])
        reward = float(self.cfg["reward_payoff"])
        punishment = float(self.cfg["punishment_payoff"])
        sucker = float(self.cfg["sucker_payoff"])

        if action_i == COOPERATE and action_j == COOPERATE:
            return reward, reward
        if action_i == COOPERATE and action_j == DEFECT:
            return sucker, temptation
        if action_i == DEFECT and action_j == COOPERATE:
            return temptation, sucker
        return punishment, punishment

    def _sample_interaction_pairs(self) -> list[tuple[int, int]]:
        """Sample pairs, optionally persisting existing partnerships."""
        p = float(self.cfg.get("partner_persistence_probability", 0.0))

        if p <= 0.0 or not self.current_pairs:
            indices = self.rng.permutation(self.n_sites)
            self.current_pairs = [
                (int(indices[i]), int(indices[i + 1]))
                for i in range(0, self.n_sites - 1, 2)
            ]
            return self.current_pairs

        kept: list[tuple[int, int]] = []
        freed: list[int] = []
        for i, j in self.current_pairs:
            if self.rng.random() < p:
                kept.append((i, j))
            else:
                freed.extend([i, j])

        if freed:
            shuffled = self.rng.permutation(freed)
            kept.extend(
                (int(shuffled[k]), int(shuffled[k + 1]))
                for k in range(0, len(shuffled) - 1, 2)
            )

        self.current_pairs = kept
        return kept

    def _play_pair_games(self) -> tuple[np.ndarray, float]:
        payoff = np.zeros(self.n_sites, dtype=float)
        action_memory = self.last_action.copy()
        payoff_memory = self.last_payoff.copy()
        cooperation_count = 0
        action_count = 0
        interaction_count = np.zeros(self.n_sites, dtype=float)
        rounds_per_step = max(1, int(self.cfg["rounds_per_pair_per_step"]))

        # Sample fresh pairs once per step; play multiple rounds with those same partners.
        interaction_pairs = self._sample_interaction_pairs()

        for _ in range(rounds_per_step):
            next_action_memory = action_memory.copy()
            next_payoff_memory = payoff_memory.copy()
            for i, j in interaction_pairs:
                action_i = self._choose_action(i, j, action_memory, payoff_memory)
                action_j = self._choose_action(j, i, action_memory, payoff_memory)
                payoff_i, payoff_j = self._pair_payoff(action_i, action_j)

                payoff[i] += payoff_i
                payoff[j] += payoff_j
                interaction_count[i] += 1.0
                interaction_count[j] += 1.0
                cooperation_count += int(action_i == COOPERATE) + int(action_j == COOPERATE)
                action_count += 2

                next_action_memory[i, j] = action_i
                next_action_memory[j, i] = action_j
                next_payoff_memory[i, j] = payoff_i
                next_payoff_memory[j, i] = payoff_j

            action_memory = next_action_memory
            payoff_memory = next_payoff_memory

        if bool(self.cfg["normalize_payoff_by_interactions"]):
            safe_count = np.where(interaction_count > 0.0, interaction_count, 1.0)
            payoff = payoff / safe_count

        self.last_action = action_memory
        self.last_payoff = payoff_memory
        cooperation_rate = cooperation_count / max(1, action_count)
        return payoff, cooperation_rate

    def _apply_moran_replacement(self, fitness: np.ndarray) -> None:
        parent_indices = sample_local_parent_indices(
            fitness,
            self._global_neighbors,
            self.rng,
            float(self.cfg["selection_temperature"]),
        )
        inherited_strategy = self.strategy[parent_indices].astype(np.int8, copy=True)
        next_strategy, mutate_mask = self._mutate_strategies(inherited_strategy)
        next_lineage = self.lineage[parent_indices].astype(self.lineage.dtype, copy=True)

        if bool(self.cfg["reset_memory_on_replacement"]):
            persisted = (parent_indices == np.arange(self.n_sites)) & (~mutate_mask)
            next_action = np.full_like(self.last_action, COOPERATE)
            next_payoff = np.full_like(
                self.last_payoff,
                float(self.cfg["wsls_aspiration_payoff"]),
            )
            persisted_indices = np.where(persisted)[0]
            if persisted_indices.size > 0:
                idx = np.ix_(persisted_indices, persisted_indices)
                next_action[idx] = self.last_action[idx]
                next_payoff[idx] = self.last_payoff[idx]
        else:
            next_action = self.last_action[parent_indices, :][:, parent_indices].copy()
            next_payoff = self.last_payoff[parent_indices, :][:, parent_indices].copy()

        self.strategy = next_strategy
        self.lineage = next_lineage
        self.last_action = next_action
        self.last_payoff = next_payoff
        # Pairs persist across replacement steps; memory reset already handles
        # the case where a replaced site starts fresh with its persistent partner.

    def _strategy_frequency(self, strategy_id: int) -> float:
        return float(np.mean(self.strategy == strategy_id))

    def _metrics(
        self,
        payoff: np.ndarray,
        fitness: np.ndarray,
        cooperation_rate: float,
    ) -> dict[str, float]:
        metrics = {
            "step": float(self.step_index + 1),
            "mean_cooperation_rate": float(cooperation_rate),
            "mean_payoff": float(np.mean(payoff)),
            "mean_fitness": float(np.mean(fitness)),
            "std_fitness": float(np.std(fitness)),
            "reciprocal_strategy_frequency": float(
                np.mean(np.isin(self.strategy, list(RECIPROCAL_STRATEGIES)))
            ),
            "ALLD_frequency": self._strategy_frequency(STRATEGY_IDS["ALLD"]),
        }
        for strategy_id, name in enumerate(STRATEGY_NAMES):
            metrics[f"{name}_frequency"] = self._strategy_frequency(strategy_id)
        return metrics

    def step(self) -> dict[str, float]:
        payoff, cooperation_rate = self._play_pair_games()
        fitness = float(self.cfg["base_fitness"]) + payoff
        self.latest_payoff = payoff.copy()
        self.latest_fitness = fitness.copy()
        metrics = self._metrics(payoff, fitness, cooperation_rate)
        self.history.append(metrics)
        self._apply_moran_replacement(fitness)
        self.step_index += 1
        return metrics

    def run(self) -> dict[str, Any]:
        n_steps = int(self.cfg["simulation_steps"])
        summary_interval = max(1, int(self.cfg["summary_interval_steps"]))

        for t in range(n_steps):
            step_metrics = self.step()
            if (t + 1) % summary_interval == 0 or t == 0 or (t + 1) == n_steps:
                print(
                    f"[{self.name}] step={t + 1:4d}/{n_steps} "
                    f"coop_rate={step_metrics['mean_cooperation_rate']:.4f} "
                    f"reciprocal={step_metrics['reciprocal_strategy_frequency']:.4f} "
                    f"ALLD={step_metrics['ALLD_frequency']:.4f}"
                )

        final_counts = {
            name: int(np.sum(self.strategy == strategy_id))
            for strategy_id, name in enumerate(STRATEGY_NAMES)
        }
        final_frequencies = {
            name: float(count / self.n_sites)
            for name, count in final_counts.items()
        }
        return {
            "config": self.cfg,
            "mechanism": self.name,
            "strategy_names": list(STRATEGY_NAMES),
            "final_strategy_counts": final_counts,
            "final_strategy_frequencies": final_frequencies,
            "final_reciprocal_strategy_frequency": float(
                sum(final_frequencies[name] for name in ("TFT", "GTFT", "WSLS"))
            ),
            "final_ALLD_frequency": final_frequencies["ALLD"],
            "final_mean_cooperation_rate": (
                float(self.history[-1]["mean_cooperation_rate"]) if self.history else 0.0
            ),
            "history": self.history,
        }


def _write_log(payload: dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_simulation(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime_cfg = dict(config if cfg is None else cfg)
    model = DirectReciprocityWellMixedModel(runtime_cfg)
    payload = model.run()

    if bool(runtime_cfg.get("write_log", True)):
        _write_log(payload, str(runtime_cfg["log_output_path"]))
        print(f"[direct_reciprocity_well_mixed] wrote log -> {runtime_cfg['log_output_path']}")
    return payload


if __name__ == "__main__":
    run_simulation()
