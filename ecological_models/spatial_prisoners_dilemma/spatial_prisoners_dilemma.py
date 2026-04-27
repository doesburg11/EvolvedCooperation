#!/usr/bin/env python3
"""
spatial_prisoners_dilemma.py

CPU-side spatial Prisoner's Dilemma ecology with local interaction, movement,
reproduction, death, mutation, and strategy inheritance.

Run from the repo root with:
  ./.conda/bin/python -m ecological_models.spatial_prisoners_dilemma.spatial_prisoners_dilemma
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from time import strftime
from typing import Any, Mapping

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m ecological_models.spatial_prisoners_dilemma.spatial_prisoners_dilemma'."
    )

from .config.spatial_prisoners_dilemma_config import config as model_config
from .utils.matplot_plotting import (
    plot_population_history,
    plot_strategy_family_history,
)


STRATEGY_COOPERATE = 0
STRATEGY_DEFECT = 1
STRATEGY_TIT_FOR_TAT = 2
STRATEGY_RANDOM = 3

PD_COOPERATE = 0
PD_DEFECT = 1

SEARCH_NO_ACTION = -1
SEARCH_RESPOND = 0
SEARCH_CHALLENGE = 1

DIRECTIONS: tuple[tuple[int, int], ...] = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)
INVERSE_DIRECTION_INDEX: tuple[int, ...] = (7, 6, 5, 4, 3, 2, 1, 0)

STRATEGY_LABELS = {
    STRATEGY_COOPERATE: "Co-op",
    STRATEGY_DEFECT: "Defect",
    STRATEGY_TIT_FOR_TAT: "Tit-for-tat",
    STRATEGY_RANDOM: "Random",
}
STRATEGY_HISTORY_KEYS = {
    STRATEGY_COOPERATE: "cooperate",
    STRATEGY_DEFECT: "defect",
    STRATEGY_TIT_FOR_TAT: "tit_for_tat",
    STRATEGY_RANDOM: "random",
}
STRATEGY_NAME_TO_ID = {
    "always_cooperate": STRATEGY_COOPERATE,
    "always_defect": STRATEGY_DEFECT,
    "tit_for_tat": STRATEGY_TIT_FOR_TAT,
    "random": STRATEGY_RANDOM,
}

STRATEGY_BIN_LABELS: dict[int, str] = {}
for same_id, same_label in STRATEGY_LABELS.items():
    for other_id, other_label in STRATEGY_LABELS.items():
        strategy_id = same_id * 10 + other_id
        if same_id == other_id:
            STRATEGY_BIN_LABELS[strategy_id] = f"{same_label} pure"
        else:
            STRATEGY_BIN_LABELS[strategy_id] = (
                f"{same_label} contingent ({other_label.lower()})"
            )


@dataclass(slots=True)
class Settings:
    grid_width: int = int(model_config["grid_width"])
    grid_height: int = int(model_config["grid_height"])
    initial_agent_fraction: float = float(model_config["initial_agent_fraction"])
    carrying_capacity_fraction: float = float(model_config["carrying_capacity_fraction"])
    simulation_steps: int = int(model_config["simulation_steps"])
    cost_of_living: float = float(model_config["cost_of_living"])
    travel_cost: float = float(model_config["travel_cost"])
    reproduce_min_energy: float = float(model_config["reproduce_min_energy"])
    reproduce_cost: float = float(model_config["reproduce_cost"])
    reproduction_inheritance: float = float(model_config["reproduction_inheritance"])
    max_children_per_step: int = int(model_config["max_children_per_step"])
    payoff_cc: float = float(model_config["payoff_cc"])
    payoff_cd: float = float(model_config["payoff_cd"])
    payoff_dc: float = float(model_config["payoff_dc"])
    payoff_dd: float = float(model_config["payoff_dd"])
    max_energy: float = float(model_config["max_energy"])
    initial_energy_mean: float = float(model_config["initial_energy_mean"])
    initial_energy_stddev: float = float(model_config["initial_energy_stddev"])
    initial_energy_min: float = float(model_config["initial_energy_min"])
    env_noise: float = float(model_config["env_noise"])
    trait_count: int = int(model_config["trait_count"])
    pure_strategy: bool = bool(model_config["pure_strategy"])
    strategy_per_trait: bool = bool(model_config["strategy_per_trait"])
    mutation_rate: float = float(model_config["mutation_rate"])
    strategy_weights: dict[str, float] = field(
        default_factory=lambda: dict(model_config["strategy_weights"])
    )
    random_seed: int | None = model_config["random_seed"]
    summary_interval_steps: int = int(model_config["summary_interval_steps"])
    write_log: bool = bool(model_config["write_log"])
    log_output_path: str = str(model_config["log_output_path"])
    show_matplotlib_plots: bool = bool(model_config["show_matplotlib_plots"])

    max_agent_spaces: int = field(init=False)
    initial_agent_count: int = field(init=False)
    agent_hard_limit: int = field(init=False)

    def __post_init__(self) -> None:
        if self.grid_width < 1 or self.grid_height < 1:
            raise ValueError("grid dimensions must both be >= 1")
        if not 0.0 <= self.initial_agent_fraction <= 1.0:
            raise ValueError("initial_agent_fraction must be within [0, 1]")
        if not 0.0 < self.carrying_capacity_fraction <= 1.0:
            raise ValueError("carrying_capacity_fraction must be within (0, 1]")
        if self.simulation_steps < 0:
            raise ValueError("simulation_steps must be >= 0")
        if self.cost_of_living < 0.0:
            raise ValueError("cost_of_living must be >= 0")
        if self.travel_cost < 0.0:
            raise ValueError("travel_cost must be >= 0")
        if self.reproduce_min_energy < 0.0:
            raise ValueError("reproduce_min_energy must be >= 0")
        if self.reproduce_cost < 0.0:
            raise ValueError("reproduce_cost must be >= 0")
        if self.max_children_per_step < 1:
            raise ValueError("max_children_per_step must be >= 1")
        if self.max_energy <= 0.0:
            raise ValueError("max_energy must be > 0")
        if self.initial_energy_min < 0.0:
            raise ValueError("initial_energy_min must be >= 0")
        if self.initial_energy_stddev < 0.0:
            raise ValueError("initial_energy_stddev must be >= 0")
        if not 0.0 <= self.env_noise <= 1.0:
            raise ValueError("env_noise must be within [0, 1]")
        if self.trait_count < 1:
            raise ValueError("trait_count must be >= 1")
        if self.pure_strategy and self.strategy_per_trait:
            raise ValueError(
                "pure_strategy and strategy_per_trait cannot both be true; "
                "choose one encoding mode."
            )
        if not 0.0 <= self.mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be within [0, 1]")
        if self.summary_interval_steps < 0:
            raise ValueError("summary_interval_steps must be >= 0")

        expected_keys = set(STRATEGY_NAME_TO_ID)
        actual_keys = set(self.strategy_weights)
        if actual_keys != expected_keys:
            raise ValueError(
                "strategy_weights must contain exactly these keys: "
                f"{sorted(expected_keys)}"
            )
        if sum(self.strategy_weights.values()) <= 0.0:
            raise ValueError("strategy_weights must sum to a positive value")

        self.max_agent_spaces = self.grid_width * self.grid_height
        raw_initial = int(self.max_agent_spaces * self.initial_agent_fraction)
        if self.initial_agent_fraction > 0.0:
            self.initial_agent_count = max(1, raw_initial)
        else:
            self.initial_agent_count = 0
        self.agent_hard_limit = max(
            self.initial_agent_count,
            int(self.max_agent_spaces * self.carrying_capacity_fraction),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_settings(config_values: Mapping[str, Any] | None = None) -> Settings:
    """Build settings from the active config file or an explicit config mapping."""
    if config_values is None:
        return Settings()

    init_field_names = {
        item.name for item in fields(Settings) if item.init
    }
    overrides = {
        key: config_values[key] for key in init_field_names if key in config_values
    }
    return Settings(**overrides)


@dataclass(slots=True)
class PrisonerAgent:
    id: int
    x: int
    y: int
    energy: float
    trait: int
    strategies: tuple[int, ...]
    strategy_id: int
    game_memory_ids: list[int | None] = field(
        default_factory=lambda: [None] * len(DIRECTIONS)
    )
    game_memory_choices: list[int] = field(
        default_factory=lambda: [PD_COOPERATE] * len(DIRECTIONS)
    )
    is_newborn: bool = False


@dataclass(slots=True)
class SearchState:
    roll: float
    neighbour_ids: tuple[int | None, ...]
    my_actions: tuple[int, ...]
    num_neighbours: int


def wrap(value: int, limit: int) -> int:
    return value % limit


class SpatialPrisonersDilemmaModel:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.rng = random.Random(self.settings.random_seed)
        self.agents: list[PrisonerAgent] = []
        self.next_agent_id = 0
        self.step_index = 0
        self.history: dict[str, list[Any]] = {
            "step": [],
            "population": [],
            "mean_energy": [],
            "births": [],
            "deaths_total": [],
            "play_deaths": [],
            "movement_deaths": [],
            "cost_deaths": [],
            "cull_deaths": [],
            "movement_attempts": [],
            "movement_successes": [],
            "interaction_pairs": [],
            "total_games": [],
            "cooperate_actions": [],
            "defect_actions": [],
            "pure_count": [],
            "contingent_count": [],
            "strategy_bin_counts": [],
        }
        for suffix in STRATEGY_HISTORY_KEYS.values():
            self.history[f"same_trait_{suffix}"] = []
            self.history[f"other_trait_{suffix}"] = []
        self._initialize_population()
        self._record_snapshot(
            {
                "births": 0,
                "play_deaths": 0,
                "movement_deaths": 0,
                "cost_deaths": 0,
                "cull_deaths": 0,
                "movement_attempts": 0,
                "movement_successes": 0,
                "interaction_pairs": 0,
                "total_games": 0,
                "cooperate_actions": 0,
                "defect_actions": 0,
            }
        )

    def _initialize_population(self) -> None:
        chosen_cells = self.rng.sample(
            range(self.settings.max_agent_spaces),
            self.settings.initial_agent_count,
        )
        for cell_index in chosen_cells:
            x = cell_index % self.settings.grid_width
            y = cell_index // self.settings.grid_width
            trait = self.rng.randrange(self.settings.trait_count)
            strategies = self._initial_strategies_for_trait(trait)
            self.agents.append(
                PrisonerAgent(
                    id=self._next_id(),
                    x=x,
                    y=y,
                    energy=self._sample_initial_energy(),
                    trait=trait,
                    strategies=strategies,
                    strategy_id=self._compute_strategy_id(trait, strategies),
                )
            )

    def _next_id(self) -> int:
        value = self.next_agent_id
        self.next_agent_id += 1
        return value

    def _sample_initial_energy(self) -> float:
        energy = max(
            self.settings.initial_energy_min,
            self.rng.gauss(
                self.settings.initial_energy_mean,
                self.settings.initial_energy_stddev,
            ),
        )
        return min(energy, self.settings.max_energy)

    def _weighted_strategy_draw(self) -> int:
        strategy_names = tuple(self.settings.strategy_weights)
        weights = tuple(self.settings.strategy_weights[name] for name in strategy_names)
        chosen = self.rng.choices(strategy_names, weights=weights, k=1)[0]
        return STRATEGY_NAME_TO_ID[chosen]

    def _initial_strategies_for_trait(self, own_trait: int) -> tuple[int, ...]:
        if self.settings.pure_strategy:
            strategy = self._weighted_strategy_draw()
            return tuple(strategy for _ in range(self.settings.trait_count))

        if self.settings.strategy_per_trait:
            return tuple(
                self._weighted_strategy_draw() for _ in range(self.settings.trait_count)
            )

        own_strategy = self._weighted_strategy_draw()
        other_strategy = self._weighted_strategy_draw()
        return tuple(
            own_strategy if trait_index == own_trait else other_strategy
            for trait_index in range(self.settings.trait_count)
        )

    def _compute_strategy_id(
        self,
        own_trait: int,
        strategies: tuple[int, ...],
    ) -> int:
        own_strategy = strategies[own_trait]
        other_strategy = own_strategy
        for trait_index, strategy in enumerate(strategies):
            if trait_index != own_trait:
                other_strategy = strategy
                break
        return own_strategy * 10 + other_strategy

    def _mutate_strategy(self, strategy_id: int) -> int:
        new_strategy = strategy_id
        while new_strategy == strategy_id:
            new_strategy = self.rng.randrange(len(STRATEGY_LABELS))
        return new_strategy

    def _inherit_strategies(self, parent: PrisonerAgent) -> tuple[int, ...]:
        if self.settings.pure_strategy:
            child_strategy = parent.strategies[0]
            if self.rng.random() < self.settings.mutation_rate:
                child_strategy = self._mutate_strategy(child_strategy)
            return tuple(child_strategy for _ in range(self.settings.trait_count))

        if self.settings.strategy_per_trait:
            inherited: list[int] = []
            for strategy in parent.strategies:
                child_strategy = strategy
                if self.rng.random() < self.settings.mutation_rate:
                    child_strategy = self._mutate_strategy(child_strategy)
                inherited.append(child_strategy)
            return tuple(inherited)

        own_strategy = parent.strategies[parent.trait]
        other_strategy = own_strategy
        for trait_index, strategy in enumerate(parent.strategies):
            if trait_index != parent.trait:
                other_strategy = strategy
                break
        if self.rng.random() < self.settings.mutation_rate:
            own_strategy = self._mutate_strategy(own_strategy)
        if self.rng.random() < self.settings.mutation_rate:
            other_strategy = self._mutate_strategy(other_strategy)
        return tuple(
            own_strategy if trait_index == parent.trait else other_strategy
            for trait_index in range(self.settings.trait_count)
        )

    def _neighbor_position(self, x: int, y: int, direction_index: int) -> tuple[int, int]:
        dx, dy = DIRECTIONS[direction_index]
        return (
            wrap(x + dx, self.settings.grid_width),
            wrap(y + dy, self.settings.grid_height),
        )

    def _search_neighbourhoods(
        self,
        agents_by_id: dict[int, PrisonerAgent],
    ) -> dict[int, SearchState]:
        occupancy = {(agent.x, agent.y): agent for agent in agents_by_id.values()}
        rolls = {agent.id: self.rng.random() for agent in agents_by_id.values()}
        search_states: dict[int, SearchState] = {}

        for agent in agents_by_id.values():
            neighbour_ids: list[int | None] = []
            my_actions: list[int] = []
            neighbour_count = 0
            my_roll = rolls[agent.id]
            for direction_index in range(len(DIRECTIONS)):
                nx, ny = self._neighbor_position(agent.x, agent.y, direction_index)
                neighbour = occupancy.get((nx, ny))
                if neighbour is None:
                    neighbour_ids.append(None)
                    my_actions.append(SEARCH_NO_ACTION)
                    continue

                neighbour_count += 1
                neighbour_ids.append(neighbour.id)
                neighbour_roll = rolls[neighbour.id]
                if my_roll > neighbour_roll or (
                    my_roll == neighbour_roll and agent.id > neighbour.id
                ):
                    my_actions.append(SEARCH_CHALLENGE)
                else:
                    my_actions.append(SEARCH_RESPOND)

            search_states[agent.id] = SearchState(
                roll=my_roll,
                neighbour_ids=tuple(neighbour_ids),
                my_actions=tuple(my_actions),
                num_neighbours=neighbour_count,
            )

        return search_states

    def _decide_pd_choice(
        self,
        agent: PrisonerAgent,
        strategy_id: int,
        memory_slot: int,
        opponent_id: int,
    ) -> int:
        if strategy_id == STRATEGY_COOPERATE:
            cooperate = True
        elif strategy_id == STRATEGY_DEFECT:
            cooperate = False
        elif strategy_id == STRATEGY_TIT_FOR_TAT:
            cooperate = True
            if agent.game_memory_ids[memory_slot] == opponent_id:
                cooperate = agent.game_memory_choices[memory_slot] == PD_COOPERATE
        elif strategy_id == STRATEGY_RANDOM:
            cooperate = self.rng.random() > 0.5
        else:
            raise ValueError(f"unknown strategy id {strategy_id}")

        if self.rng.random() < self.settings.env_noise:
            cooperate = not cooperate
        return PD_COOPERATE if cooperate else PD_DEFECT

    def _pair_payoff_deltas(
        self,
        challenger_choice: int,
        responder_choice: int,
    ) -> tuple[float, float]:
        if challenger_choice == PD_COOPERATE and responder_choice == PD_COOPERATE:
            return self.settings.payoff_cc, self.settings.payoff_cc
        if challenger_choice == PD_DEFECT and responder_choice == PD_DEFECT:
            return self.settings.payoff_dd, self.settings.payoff_dd
        if challenger_choice == PD_DEFECT and responder_choice == PD_COOPERATE:
            return self.settings.payoff_dc, self.settings.payoff_cd
        return self.settings.payoff_cd, self.settings.payoff_dc

    def _resolve_play_subrounds(
        self,
        agents_by_id: dict[int, PrisonerAgent],
        search_states: dict[int, SearchState],
    ) -> tuple[dict[int, int], dict[str, int]]:
        games_played = {agent_id: 0 for agent_id in agents_by_id}
        summary = {
            "play_deaths": 0,
            "interaction_pairs": 0,
            "total_games": 0,
            "cooperate_actions": 0,
            "defect_actions": 0,
        }
        alive_ids = set(agents_by_id)

        for direction_index in range(len(DIRECTIONS)):
            starting_energy = {
                agent_id: agents_by_id[agent_id].energy for agent_id in alive_ids
            }
            energy_delta: dict[int, float] = defaultdict(float)
            games_delta: dict[int, int] = defaultdict(int)
            memory_updates: list[tuple[int, int, int, int]] = []

            for challenger_id in list(alive_ids):
                search_state = search_states[challenger_id]
                if search_state.my_actions[direction_index] != SEARCH_CHALLENGE:
                    continue
                responder_id = search_state.neighbour_ids[direction_index]
                if responder_id is None or responder_id not in alive_ids:
                    continue

                responder_memory_slot = INVERSE_DIRECTION_INDEX[direction_index]
                challenger = agents_by_id[challenger_id]
                responder = agents_by_id[responder_id]
                challenger_strategy = challenger.strategies[responder.trait]
                responder_strategy = responder.strategies[challenger.trait]

                challenger_choice = self._decide_pd_choice(
                    challenger,
                    challenger_strategy,
                    direction_index,
                    responder_id,
                )
                responder_choice = self._decide_pd_choice(
                    responder,
                    responder_strategy,
                    responder_memory_slot,
                    challenger_id,
                )

                challenger_gain, responder_gain = self._pair_payoff_deltas(
                    challenger_choice,
                    responder_choice,
                )
                energy_delta[challenger_id] += challenger_gain
                energy_delta[responder_id] += responder_gain
                games_delta[challenger_id] += 1
                games_delta[responder_id] += 1
                summary["interaction_pairs"] += 1
                summary["cooperate_actions"] += int(challenger_choice == PD_COOPERATE)
                summary["cooperate_actions"] += int(responder_choice == PD_COOPERATE)
                summary["defect_actions"] += int(challenger_choice == PD_DEFECT)
                summary["defect_actions"] += int(responder_choice == PD_DEFECT)

                if challenger_strategy == STRATEGY_TIT_FOR_TAT:
                    memory_updates.append(
                        (challenger_id, direction_index, responder_id, responder_choice)
                    )
                if responder_strategy == STRATEGY_TIT_FOR_TAT:
                    memory_updates.append(
                        (
                            responder_id,
                            responder_memory_slot,
                            challenger_id,
                            challenger_choice,
                        )
                    )

            touched_agents = set(games_delta) | set(energy_delta)
            dead_ids: list[int] = []
            for agent_id in touched_agents:
                agent = agents_by_id[agent_id]
                agent.energy = min(
                    self.settings.max_energy,
                    starting_energy[agent_id] + energy_delta.get(agent_id, 0.0),
                )
                games_played[agent_id] += games_delta.get(agent_id, 0)
                if agent.energy <= 0.0:
                    dead_ids.append(agent_id)

            for agent_id, memory_slot, opponent_id, opponent_choice in memory_updates:
                if agent_id in agents_by_id:
                    agent = agents_by_id[agent_id]
                    agent.game_memory_ids[memory_slot] = opponent_id
                    agent.game_memory_choices[memory_slot] = opponent_choice

            for dead_id in dead_ids:
                if dead_id in agents_by_id:
                    del agents_by_id[dead_id]
                    alive_ids.discard(dead_id)
                    summary["play_deaths"] += 1

        summary["total_games"] = sum(games_played.values())
        return games_played, summary

    def _resolve_movement(
        self,
        agents_by_id: dict[int, PrisonerAgent],
        games_played: dict[int, int],
    ) -> dict[str, int]:
        summary = {
            "movement_attempts": 0,
            "movement_successes": 0,
            "movement_deaths": 0,
        }
        occupancy = {(agent.x, agent.y): agent.id for agent in agents_by_id.values()}
        requests: dict[tuple[int, int], list[tuple[float, int]]] = defaultdict(list)

        for agent_id in list(agents_by_id):
            if games_played.get(agent_id, 0) > 0:
                continue
            agent = agents_by_id.get(agent_id)
            if agent is None:
                continue

            summary["movement_attempts"] += 1
            agent.energy -= self.settings.travel_cost
            if agent.energy <= 0.0:
                del agents_by_id[agent_id]
                summary["movement_deaths"] += 1
                continue

            start_index = self.rng.randrange(len(DIRECTIONS))
            chosen_target: tuple[int, int] | None = None
            for offset in range(len(DIRECTIONS)):
                direction_index = (start_index + offset) % len(DIRECTIONS)
                target = self._neighbor_position(agent.x, agent.y, direction_index)
                if target not in occupancy:
                    chosen_target = target
                    break
            if chosen_target is None:
                continue
            requests[chosen_target].append((self.rng.random(), agent_id))

        for target, contenders in requests.items():
            _, winner_id = max(contenders, key=lambda item: (item[0], item[1]))
            winner = agents_by_id.get(winner_id)
            if winner is None:
                continue
            old_position = (winner.x, winner.y)
            if target in occupancy:
                continue
            occupancy.pop(old_position, None)
            winner.x, winner.y = target
            occupancy[target] = winner_id
            summary["movement_successes"] += 1

        return summary

    def _next_reproduction_direction(
        self,
        parent: PrisonerAgent,
        occupancy: dict[tuple[int, int], int],
        parent_state: dict[str, int | float],
    ) -> int | None:
        while int(parent_state["scan_offset"]) < len(DIRECTIONS):
            direction_index = (
                int(parent_state["start_index"]) + int(parent_state["scan_offset"])
            ) % len(DIRECTIONS)
            parent_state["scan_offset"] = int(parent_state["scan_offset"]) + 1
            target = self._neighbor_position(parent.x, parent.y, direction_index)
            if target not in occupancy:
                return direction_index
        return None

    def _make_child(
        self,
        parent: PrisonerAgent,
        x: int,
        y: int,
    ) -> PrisonerAgent:
        if 0.0 < self.settings.reproduction_inheritance <= 1.0:
            child_energy = self.settings.reproduction_inheritance * parent.energy
        else:
            child_energy = self._sample_initial_energy()
        child_energy = max(self.settings.initial_energy_min, child_energy)
        child_energy = min(self.settings.max_energy, child_energy)
        child_strategies = self._inherit_strategies(parent)
        return PrisonerAgent(
            id=self._next_id(),
            x=x,
            y=y,
            energy=child_energy,
            trait=parent.trait,
            strategies=child_strategies,
            strategy_id=self._compute_strategy_id(parent.trait, child_strategies),
            is_newborn=True,
        )

    def _resolve_reproduction(
        self,
        agents_by_id: dict[int, PrisonerAgent],
    ) -> dict[str, int]:
        summary = {"births": 0}
        if not agents_by_id or len(agents_by_id) >= self.settings.agent_hard_limit:
            return summary

        occupancy = {(agent.x, agent.y): agent.id for agent in agents_by_id.values()}
        parent_state: dict[int, dict[str, int | float]] = {}
        for agent in agents_by_id.values():
            if agent.energy >= self.settings.reproduce_min_energy:
                parent_state[agent.id] = {
                    "start_index": self.rng.randrange(len(DIRECTIONS)),
                    "scan_offset": 0,
                    "claim_roll": self.rng.random(),
                    "spawned": 0,
                }

        newborns: list[PrisonerAgent] = []
        for _ in range(len(DIRECTIONS)):
            if len(agents_by_id) + len(newborns) >= self.settings.agent_hard_limit:
                break

            claims: dict[tuple[int, int], list[tuple[float, int, int]]] = defaultdict(list)
            any_claim = False
            for parent_id, state in parent_state.items():
                parent = agents_by_id.get(parent_id)
                if parent is None:
                    continue
                if parent.energy < self.settings.reproduce_min_energy:
                    continue
                if int(state["spawned"]) >= self.settings.max_children_per_step:
                    continue

                direction_index = self._next_reproduction_direction(
                    parent,
                    occupancy,
                    state,
                )
                if direction_index is None:
                    continue
                target = self._neighbor_position(parent.x, parent.y, direction_index)
                claims[target].append(
                    (float(state["claim_roll"]), parent_id, direction_index)
                )
                any_claim = True

            if not any_claim:
                break

            for target, contenders in claims.items():
                if len(agents_by_id) + len(newborns) >= self.settings.agent_hard_limit:
                    break
                _, winner_id, _ = max(contenders, key=lambda item: (item[0], item[1]))
                parent = agents_by_id.get(winner_id)
                if parent is None:
                    continue
                state = parent_state[winner_id]
                if parent.energy < self.settings.reproduce_min_energy:
                    continue
                if int(state["spawned"]) >= self.settings.max_children_per_step:
                    continue
                if target in occupancy:
                    continue

                parent.energy -= self.settings.reproduce_cost
                child = self._make_child(parent, target[0], target[1])
                newborns.append(child)
                occupancy[target] = child.id
                state["spawned"] = int(state["spawned"]) + 1
                summary["births"] += 1

        for child in newborns:
            agents_by_id[child.id] = child

        return summary

    def _apply_environmental_punishment(
        self,
        agents_by_id: dict[int, PrisonerAgent],
    ) -> tuple[dict[int, PrisonerAgent], dict[str, int]]:
        summary = {"cost_deaths": 0, "cull_deaths": 0}
        survivors: dict[int, PrisonerAgent] = {}

        for index, (agent_id, agent) in enumerate(agents_by_id.items()):
            if index >= self.settings.agent_hard_limit:
                summary["cull_deaths"] += 1
                continue
            if agent.is_newborn:
                agent.is_newborn = False
                survivors[agent_id] = agent
                continue

            if agent.energy > self.settings.max_energy:
                agent.energy = self.settings.max_energy
            agent.energy -= self.settings.cost_of_living
            if agent.energy <= 0.0:
                summary["cost_deaths"] += 1
                continue
            survivors[agent_id] = agent

        return survivors, summary

    def _strategy_family_counts(
        self,
    ) -> tuple[dict[int, int], dict[int, int], dict[str, int], int, int]:
        same_trait_counts = {strategy_id: 0 for strategy_id in STRATEGY_LABELS}
        other_trait_counts = {strategy_id: 0 for strategy_id in STRATEGY_LABELS}
        strategy_bin_counts = {
            label: 0 for label in STRATEGY_BIN_LABELS.values()
        }

        pure_count = 0
        for agent in self.agents:
            same_trait_strategy = agent.strategy_id // 10
            other_trait_strategy = agent.strategy_id % 10
            same_trait_counts[same_trait_strategy] += 1
            other_trait_counts[other_trait_strategy] += 1
            strategy_bin_counts[STRATEGY_BIN_LABELS[agent.strategy_id]] += 1
            if same_trait_strategy == other_trait_strategy:
                pure_count += 1

        contingent_count = len(self.agents) - pure_count
        return (
            same_trait_counts,
            other_trait_counts,
            strategy_bin_counts,
            pure_count,
            contingent_count,
        )

    def _mean_energy(self) -> float:
        if not self.agents:
            return 0.0
        return sum(agent.energy for agent in self.agents) / len(self.agents)

    def _record_snapshot(self, summary: dict[str, int]) -> None:
        same_trait_counts, other_trait_counts, strategy_bin_counts, pure_count, contingent_count = (
            self._strategy_family_counts()
        )

        self.history["step"].append(self.step_index)
        self.history["population"].append(len(self.agents))
        self.history["mean_energy"].append(self._mean_energy())
        self.history["births"].append(summary["births"])
        deaths_total = (
            summary["play_deaths"]
            + summary["movement_deaths"]
            + summary["cost_deaths"]
            + summary["cull_deaths"]
        )
        self.history["deaths_total"].append(deaths_total)
        self.history["play_deaths"].append(summary["play_deaths"])
        self.history["movement_deaths"].append(summary["movement_deaths"])
        self.history["cost_deaths"].append(summary["cost_deaths"])
        self.history["cull_deaths"].append(summary["cull_deaths"])
        self.history["movement_attempts"].append(summary["movement_attempts"])
        self.history["movement_successes"].append(summary["movement_successes"])
        self.history["interaction_pairs"].append(summary["interaction_pairs"])
        self.history["total_games"].append(summary["total_games"])
        self.history["cooperate_actions"].append(summary["cooperate_actions"])
        self.history["defect_actions"].append(summary["defect_actions"])
        self.history["pure_count"].append(pure_count)
        self.history["contingent_count"].append(contingent_count)
        self.history["strategy_bin_counts"].append(strategy_bin_counts)

        for strategy_id, suffix in STRATEGY_HISTORY_KEYS.items():
            self.history[f"same_trait_{suffix}"].append(same_trait_counts[strategy_id])
            self.history[f"other_trait_{suffix}"].append(other_trait_counts[strategy_id])

    def _print_step_summary(self, summary: dict[str, int]) -> None:
        total_deaths = (
            summary["play_deaths"]
            + summary["movement_deaths"]
            + summary["cost_deaths"]
            + summary["cull_deaths"]
        )
        print(
            "step="
            f"{self.step_index:04d} "
            f"population={len(self.agents):4d} "
            f"mean_energy={self._mean_energy():7.2f} "
            f"births={summary['births']:3d} "
            f"deaths={total_deaths:3d} "
            f"pairs={summary['interaction_pairs']:4d} "
            f"moves={summary['movement_successes']:3d}/{summary['movement_attempts']:3d}"
        )

    def step(self) -> bool:
        if not self.agents:
            return False

        agents_by_id = {agent.id: agent for agent in self.agents}
        search_states = self._search_neighbourhoods(agents_by_id)
        games_played, play_summary = self._resolve_play_subrounds(
            agents_by_id,
            search_states,
        )
        movement_summary = self._resolve_movement(agents_by_id, games_played)
        reproduction_summary = self._resolve_reproduction(agents_by_id)
        agents_by_id, punishment_summary = self._apply_environmental_punishment(agents_by_id)

        self.agents = list(agents_by_id.values())
        self.step_index += 1
        summary = {
            "births": reproduction_summary["births"],
            "play_deaths": play_summary["play_deaths"],
            "movement_deaths": movement_summary["movement_deaths"],
            "cost_deaths": punishment_summary["cost_deaths"],
            "cull_deaths": punishment_summary["cull_deaths"],
            "movement_attempts": movement_summary["movement_attempts"],
            "movement_successes": movement_summary["movement_successes"],
            "interaction_pairs": play_summary["interaction_pairs"],
            "total_games": play_summary["total_games"],
            "cooperate_actions": play_summary["cooperate_actions"],
            "defect_actions": play_summary["defect_actions"],
        }
        self._record_snapshot(summary)
        return bool(self.agents)

    def run(self, steps: int | None = None) -> dict[str, list[Any]]:
        total_steps = self.settings.simulation_steps if steps is None else steps
        while self.step_index < total_steps and self.agents:
            alive = self.step()
            latest_summary = {
                key: self.history[key][-1]
                for key in (
                    "births",
                    "play_deaths",
                    "movement_deaths",
                    "cost_deaths",
                    "cull_deaths",
                    "movement_attempts",
                    "movement_successes",
                    "interaction_pairs",
                )
            }
            if self.settings.summary_interval_steps and (
                self.step_index % self.settings.summary_interval_steps == 0 or not alive
            ):
                self._print_step_summary(latest_summary)
            if not alive:
                break
        return self.history

    def final_summary(self) -> dict[str, Any]:
        same_trait_counts, other_trait_counts, strategy_bin_counts, pure_count, contingent_count = (
            self._strategy_family_counts()
        )
        return {
            "steps_completed": self.step_index,
            "population": len(self.agents),
            "mean_energy": round(self._mean_energy(), 6),
            "same_trait_strategy_counts": {
                STRATEGY_LABELS[strategy_id]: count
                for strategy_id, count in same_trait_counts.items()
            },
            "other_trait_strategy_counts": {
                STRATEGY_LABELS[strategy_id]: count
                for strategy_id, count in other_trait_counts.items()
            },
            "pure_count": pure_count,
            "contingent_count": contingent_count,
            "strategy_bin_counts": strategy_bin_counts,
        }

    def export_run_log(self, output_path: str | None = None) -> Path:
        path = Path(output_path or self.settings.log_output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.settings.to_dict(),
            "history": self.history,
            "final_summary": self.final_summary(),
            "final_population": [
                {
                    "id": agent.id,
                    "x": agent.x,
                    "y": agent.y,
                    "energy": round(agent.energy, 6),
                    "trait": agent.trait,
                    "strategy_id": agent.strategy_id,
                    "strategies": [STRATEGY_LABELS[strategy] for strategy in agent.strategies],
                }
                for agent in self.agents
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path


def main() -> None:
    settings = make_settings()
    model = SpatialPrisonersDilemmaModel(settings)
    print(
        "Running spatial Prisoner's Dilemma with "
        f"grid={settings.grid_width}x{settings.grid_height}, "
        f"initial_agents={settings.initial_agent_count}, "
        f"hard_limit={settings.agent_hard_limit}, "
        f"seed={settings.random_seed}"
    )
    model.run()
    final_summary = model.final_summary()
    print("Final summary:")
    print(
        f"steps={final_summary['steps_completed']} "
        f"population={final_summary['population']} "
        f"mean_energy={final_summary['mean_energy']:.3f}"
    )
    print(
        "same-trait strategies: "
        + ", ".join(
            f"{label}={count}"
            for label, count in final_summary["same_trait_strategy_counts"].items()
        )
    )
    print(
        "other-trait strategies: "
        + ", ".join(
            f"{label}={count}"
            for label, count in final_summary["other_trait_strategy_counts"].items()
        )
    )

    if settings.write_log:
        log_path = model.export_run_log()
        print(f"Wrote run log to {log_path}")

    if settings.show_matplotlib_plots:
        plot_population_history(model.history)
        plot_strategy_family_history(model.history)


if __name__ == "__main__":
    main()
