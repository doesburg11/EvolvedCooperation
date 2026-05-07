#!/usr/bin/env python3
"""Kin-clustering scaffold for direct reciprocity.

A direct structural parallel to the spatial-clustering scaffold, replacing the
2D grid topology with a kin-biased interaction graph.  Agents are assigned to
lineages at initialization.  Interaction pairs are drawn with a bias toward
same-lineage partners (kin_interaction_fraction), creating the genetic-clustering
analog of the geographic clustering produced by the grid.

Two mechanisms work in sequence:
  - Kin clustering (origin): same-lineage interaction bias creates the
    protected founding environment that lets TFT meet TFT before ALLD can
    exploit it — the genetic equivalent of spatial clustering.
  - Direct reciprocity (maintenance): partner memory and repeated rounds
    sustain cooperation within established pairs once cooperation is common.

The interaction graph is static (built once from initial lineage assignment).
Replacement follows the same graph: each agent's replacement candidates are its
interaction neighbors plus self, exactly as in the spatial-clustering scaffold
where replacement is local to the grid neighborhood.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from moran_models.interaction_kernel.core.selection import sample_local_parent_indices

from .config.kin_clustering_config import config


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


class KinClusteringScaffoldModel:
    """Moran model with kin-biased interaction graph and direct reciprocity."""

    name = "direct_reciprocity_kin_clustering"

    def __init__(self, cfg: dict[str, Any]):
        self.cfg = dict(cfg)
        self.n_agents = int(self.cfg["n_agents"])
        self.rng = np.random.default_rng(int(self.cfg["random_seed"]))

        n_lineages = max(1, int(self.cfg["n_lineages"]))
        self.lineage = self.rng.integers(0, n_lineages, size=self.n_agents, dtype=np.int32)

        # Build kin-biased interaction graph (static — derived from initial lineages).
        self._adjacency: list[set[int]] = self._build_adjacency()
        self.interaction_pairs: list[tuple[int, int]] = self._pairs_from_adjacency()
        self.replacement_neighbors: list[np.ndarray] = self._replacement_from_adjacency()

        self.strategy = self._initialize_strategies()

        self.last_action = np.full(
            (self.n_agents, self.n_agents),
            COOPERATE,
            dtype=np.int8,
        )
        self.last_payoff = np.full(
            (self.n_agents, self.n_agents),
            float(self.cfg["wsls_aspiration_payoff"]),
            dtype=float,
        )
        self.latest_payoff = np.zeros(self.n_agents, dtype=float)
        self.latest_fitness = np.full(self.n_agents, float(self.cfg["base_fitness"]), dtype=float)
        self.history: list[dict[str, float]] = []
        self.step_index = 0

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_adjacency(self) -> list[set[int]]:
        """Build kin-biased interaction adjacency from initial lineage assignment."""
        n_partners = int(self.cfg["n_partners_per_agent"])
        kin_fraction = float(self.cfg["kin_interaction_fraction"])
        n_kin = max(0, int(round(kin_fraction * n_partners)))
        n_stranger = n_partners - n_kin

        adj: list[set[int]] = [set() for _ in range(self.n_agents)]

        lineage_members: dict[int, list[int]] = {}
        for i in range(self.n_agents):
            lineage_members.setdefault(int(self.lineage[i]), []).append(i)

        for i in range(self.n_agents):
            lin_i = int(self.lineage[i])
            same = [j for j in lineage_members[lin_i] if j != i]
            diff = [j for j in range(self.n_agents) if int(self.lineage[j]) != lin_i]

            if n_kin > 0 and same:
                candidates = [j for j in same if j not in adj[i]]
                k = min(n_kin, len(candidates))
                if k > 0:
                    for j in self.rng.choice(candidates, size=k, replace=False).tolist():
                        adj[i].add(j)
                        adj[j].add(i)

            if n_stranger > 0 and diff:
                candidates = [j for j in diff if j not in adj[i]]
                s = min(n_stranger, len(candidates))
                if s > 0:
                    for j in self.rng.choice(candidates, size=s, replace=False).tolist():
                        adj[i].add(j)
                        adj[j].add(i)

        return adj

    def _pairs_from_adjacency(self) -> list[tuple[int, int]]:
        pairs: set[tuple[int, int]] = set()
        for i, neighbors in enumerate(self._adjacency):
            for j in neighbors:
                pairs.add((i, j) if i < j else (j, i))
        return sorted(pairs)

    def _replacement_from_adjacency(self) -> list[np.ndarray]:
        """Replacement neighborhood = interaction neighbors + self (if configured)."""
        include_self = bool(self.cfg.get("include_self_in_replacement_neighborhood", True))
        neighborhoods = []
        for i in range(self.n_agents):
            nbrs = set(self._adjacency[i])
            if include_self:
                nbrs.add(i)
            neighborhoods.append(np.array(sorted(nbrs), dtype=np.int32))
        return neighborhoods

    # ------------------------------------------------------------------
    # Strategy initialization
    # ------------------------------------------------------------------

    def _initialize_strategies(self) -> np.ndarray:
        layout = str(self.cfg.get("initial_strategy_layout", "random"))
        if layout == "reciprocal_lineage":
            return self._initialize_reciprocal_lineage()
        if layout != "random":
            raise ValueError(f"Unsupported initial_strategy_layout: {layout!r}")

        raw_freqs = dict(self.cfg["initial_strategy_frequencies"])
        weights = np.array(
            [float(raw_freqs.get(name, 0.0)) for name in STRATEGY_NAMES],
            dtype=float,
        )
        total = float(weights.sum())
        if total <= 0.0:
            raise ValueError("initial_strategy_frequencies must have positive total weight")
        return self.rng.choice(len(STRATEGY_NAMES), size=self.n_agents, p=weights / total).astype(np.int8)

    def _initialize_reciprocal_lineage(self) -> np.ndarray:
        """One lineage starts as a reciprocal mix; all others start as ALLD.

        Selects the lineage whose size is closest to
        cluster_reciprocal_frequency * n_agents — the kin-selection analog of
        the spatial cluster used in the spatial-clustering scaffold.
        """
        strategies = np.full(self.n_agents, STRATEGY_IDS["ALLD"], dtype=np.int8)

        lineage_members: dict[int, list[int]] = {}
        for i in range(self.n_agents):
            lineage_members.setdefault(int(self.lineage[i]), []).append(i)

        target_size = max(1, int(round(self.n_agents * float(self.cfg.get("cluster_reciprocal_frequency", 0.05)))))
        chosen_lineage = min(lineage_members, key=lambda lin: abs(len(lineage_members[lin]) - target_size))
        cluster_cells = lineage_members[chosen_lineage]

        raw_mix = dict(self.cfg.get("cluster_strategy_frequencies", {"TFT": 0.34, "GTFT": 0.33, "WSLS": 0.33}))
        weights = np.array(
            [float(raw_mix.get(name, 0.0)) for name in STRATEGY_NAMES],
            dtype=float,
        )
        total = float(weights.sum())
        if total <= 0.0:
            raise ValueError("cluster_strategy_frequencies must have positive total weight")
        strategies[cluster_cells] = self.rng.choice(
            len(STRATEGY_NAMES),
            size=len(cluster_cells),
            p=weights / total,
        ).astype(np.int8)
        return strategies

    # ------------------------------------------------------------------
    # Strategy mutation
    # ------------------------------------------------------------------

    def _mutate_strategies(self, strategy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mutation_rate = float(self.cfg["mutation_rate"])
        mutate_mask = self.rng.random(self.n_agents) < mutation_rate
        next_strategy = strategy.copy()
        strategy_count = len(STRATEGY_NAMES)
        for idx in np.where(mutate_mask)[0]:
            current = int(next_strategy[idx])
            offset = int(self.rng.integers(1, strategy_count))
            next_strategy[idx] = (current + offset) % strategy_count
        return next_strategy, mutate_mask

    # ------------------------------------------------------------------
    # Interaction logic (identical to spatial-clustering scaffold)
    # ------------------------------------------------------------------

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
                int(last_action[partner, actor]) if bool(self.cfg["memory_enabled"]) else COOPERATE
            )
            action = COOPERATE if partner_previous == COOPERATE else DEFECT
        elif strategy == STRATEGY_IDS["GTFT"]:
            partner_previous = (
                int(last_action[partner, actor]) if bool(self.cfg["memory_enabled"]) else COOPERATE
            )
            if partner_previous == COOPERATE:
                action = COOPERATE
            else:
                action = COOPERATE if self.rng.random() < float(self.cfg["gtft_forgiveness_probability"]) else DEFECT
        elif strategy == STRATEGY_IDS["WSLS"]:
            if bool(self.cfg["memory_enabled"]):
                own_previous = int(last_action[actor, partner])
                previous_payoff = float(last_payoff[actor, partner])
            else:
                own_previous = COOPERATE
                previous_payoff = float(self.cfg["wsls_aspiration_payoff"])
            action = own_previous if previous_payoff >= float(self.cfg["wsls_aspiration_payoff"]) else (DEFECT if own_previous == COOPERATE else COOPERATE)
        else:
            raise ValueError(f"Unknown strategy id: {strategy}")

        if float(self.cfg["action_error_probability"]) > 0.0 and self.rng.random() < float(self.cfg["action_error_probability"]):
            action = DEFECT if action == COOPERATE else COOPERATE
        return action

    def _pair_payoff(self, action_i: int, action_j: int) -> tuple[float, float]:
        T = float(self.cfg["temptation_payoff"])
        R = float(self.cfg["reward_payoff"])
        P = float(self.cfg["punishment_payoff"])
        S = float(self.cfg["sucker_payoff"])
        if action_i == COOPERATE and action_j == COOPERATE:
            return R, R
        if action_i == COOPERATE and action_j == DEFECT:
            return S, T
        if action_i == DEFECT and action_j == COOPERATE:
            return T, S
        return P, P

    def _play_pair_games(self) -> tuple[np.ndarray, float]:
        payoff = np.zeros(self.n_agents, dtype=float)
        action_memory = self.last_action.copy()
        payoff_memory = self.last_payoff.copy()
        cooperation_count = 0
        action_count = 0
        interaction_count = np.zeros(self.n_agents, dtype=float)
        rounds_per_step = max(1, int(self.cfg["rounds_per_pair_per_step"]))

        for _ in range(rounds_per_step):
            next_action_memory = action_memory.copy()
            next_payoff_memory = payoff_memory.copy()
            for i, j in self.interaction_pairs:
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
        return payoff, cooperation_count / max(1, action_count)

    # ------------------------------------------------------------------
    # Moran replacement (identical structure to spatial-clustering scaffold)
    # ------------------------------------------------------------------

    def _apply_moran_replacement(self, fitness: np.ndarray) -> None:
        parent_indices = sample_local_parent_indices(
            fitness,
            self.replacement_neighbors,
            self.rng,
            float(self.cfg["selection_temperature"]),
        )
        inherited_strategy = self.strategy[parent_indices].astype(np.int8, copy=True)
        next_strategy, mutate_mask = self._mutate_strategies(inherited_strategy)
        next_lineage = self.lineage[parent_indices].astype(self.lineage.dtype, copy=True)

        if bool(self.cfg["reset_memory_on_replacement"]):
            persisted = (parent_indices == np.arange(self.n_agents)) & (~mutate_mask)
            next_action = np.full_like(self.last_action, COOPERATE)
            next_payoff = np.full_like(self.last_payoff, float(self.cfg["wsls_aspiration_payoff"]))
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

    # ------------------------------------------------------------------
    # Metrics and run loop
    # ------------------------------------------------------------------

    def _strategy_frequency(self, strategy_id: int) -> float:
        return float(np.mean(self.strategy == strategy_id))

    def _metrics(self, payoff: np.ndarray, fitness: np.ndarray, cooperation_rate: float) -> dict[str, float]:
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
            name: float(count / self.n_agents)
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
    model = KinClusteringScaffoldModel(runtime_cfg)
    payload = model.run()

    if bool(runtime_cfg.get("write_log", True)):
        _write_log(payload, str(runtime_cfg["log_output_path"]))
        print(f"[direct_reciprocity_kin_clustering] wrote log -> {runtime_cfg['log_output_path']}")
    return payload


if __name__ == "__main__":
    run_simulation()
