#!/usr/bin/env python3
"""
retained_benefit_model.py

Abstract lattice model for testing a more general cooperation claim:
cooperation is selected when enough of its benefit is routed back toward
cooperators or copies of the cooperative rule.

Run from the repo root with:
  ./.conda/bin/python -m ecological_models.retained_benefit.retained_benefit_model
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from time import strftime
from typing import Any, Mapping

import numpy as np

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m ecological_models.retained_benefit.retained_benefit_model'."
    )

from .config.retained_benefit_config import config as model_config
from .utils.matplot_plotting import plot_run_summary

VON_NEUMANN_OFFSETS: tuple[tuple[int, int], ...] = (
    (0, 0),
    (0, -1),
    (0, 1),
    (-1, 0),
    (1, 0),
)
MOORE_OFFSETS: tuple[tuple[int, int], ...] = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (0, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
)


@dataclass(slots=True)
class Settings:
    grid_width: int = int(model_config["grid_width"])
    grid_height: int = int(model_config["grid_height"])
    toroidal_world: bool = bool(model_config["toroidal_world"])
    neighborhood_mode: str = str(model_config["neighborhood_mode"])
    simulation_steps: int = int(model_config["simulation_steps"])
    base_fitness: float = float(model_config["base_fitness"])
    cooperation_cost: float = float(model_config["cooperation_cost"])
    cooperation_benefit: float = float(model_config["cooperation_benefit"])
    retained_benefit_fraction: float = float(model_config["retained_benefit_fraction"])
    mutation_rate: float = float(model_config["mutation_rate"])
    mutation_stddev: float = float(model_config["mutation_stddev"])
    initial_cooperation_mean: float = float(model_config["initial_cooperation_mean"])
    initial_cooperation_stddev: float = float(model_config["initial_cooperation_stddev"])
    initial_lineage_count: int = int(model_config["initial_lineage_count"])
    initial_lineage_block_size: int = int(model_config["initial_lineage_block_size"])
    random_seed: int | None = model_config["random_seed"]
    summary_interval_steps: int = int(model_config["summary_interval_steps"])
    write_log: bool = bool(model_config["write_log"])
    log_output_path: str = str(model_config["log_output_path"])
    show_matplotlib_plots: bool = bool(model_config["show_matplotlib_plots"])

    def __post_init__(self) -> None:
        if self.grid_width < 1 or self.grid_height < 1:
            raise ValueError("grid dimensions must both be >= 1")
        if self.neighborhood_mode not in {"von_neumann", "moore"}:
            raise ValueError("neighborhood_mode must be 'von_neumann' or 'moore'")
        if self.simulation_steps < 0:
            raise ValueError("simulation_steps must be >= 0")
        if self.base_fitness <= 0.0:
            raise ValueError("base_fitness must be > 0")
        if self.cooperation_cost < 0.0:
            raise ValueError("cooperation_cost must be >= 0")
        if self.cooperation_benefit < 0.0:
            raise ValueError("cooperation_benefit must be >= 0")
        if not 0.0 <= self.retained_benefit_fraction <= 1.0:
            raise ValueError("retained_benefit_fraction must be within [0, 1]")
        if not 0.0 <= self.mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be within [0, 1]")
        if self.mutation_stddev < 0.0:
            raise ValueError("mutation_stddev must be >= 0")
        if not 0.0 <= self.initial_cooperation_mean <= 1.0:
            raise ValueError("initial_cooperation_mean must be within [0, 1]")
        if self.initial_cooperation_stddev < 0.0:
            raise ValueError("initial_cooperation_stddev must be >= 0")
        if self.initial_lineage_count < 1:
            raise ValueError("initial_lineage_count must be >= 1")
        if self.initial_lineage_block_size < 1:
            raise ValueError("initial_lineage_block_size must be >= 1")
        if self.summary_interval_steps < 0:
            raise ValueError("summary_interval_steps must be >= 0")

    @property
    def neighborhood_offsets(self) -> tuple[tuple[int, int], ...]:
        return (
            VON_NEUMANN_OFFSETS
            if self.neighborhood_mode == "von_neumann"
            else MOORE_OFFSETS
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_settings(config_values: Mapping[str, Any] | None = None) -> Settings:
    """Build settings from the active config file or an explicit config mapping."""
    if config_values is None:
        return Settings()

    init_field_names = {item.name for item in fields(Settings) if item.init}
    overrides = {
        key: config_values[key] for key in init_field_names if key in config_values
    }
    return Settings(**overrides)


class RetainedBenefitModel:
    """Lattice model where benefit routing is the central cooperation variable."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.rng = random.Random(self.settings.random_seed)
        self.width = self.settings.grid_width
        self.height = self.settings.grid_height
        self.step_count = 0

        self.lineage = self._initial_lineage_grid()
        self.cooperation = self._initial_cooperation_grid()

        self.history: dict[str, list[float]] = {
            "step": [],
            "mean_cooperation": [],
            "var_cooperation": [],
            "mean_fitness": [],
            "local_assortment": [],
            "dominant_lineage_share": [],
            "lineage_count": [],
        }
        self.last_fitness = np.full((self.height, self.width), self.settings.base_fitness)
        self.record_history()

    def _initial_lineage_grid(self) -> np.ndarray:
        block = self.settings.initial_lineage_block_size
        lineage = np.zeros((self.height, self.width), dtype=np.int32)
        for y0 in range(0, self.height, block):
            for x0 in range(0, self.width, block):
                lineage_id = self.rng.randrange(self.settings.initial_lineage_count)
                y1 = min(self.height, y0 + block)
                x1 = min(self.width, x0 + block)
                lineage[y0:y1, x0:x1] = lineage_id
        return lineage

    def _initial_cooperation_grid(self) -> np.ndarray:
        mean = self.settings.initial_cooperation_mean
        std = self.settings.initial_cooperation_stddev
        cooperation = np.array(
            [
                [
                    self.rng.gauss(mean, std)
                    for _ in range(self.width)
                ]
                for _ in range(self.height)
            ],
            dtype=np.float64,
        )
        return np.clip(cooperation, 0.0, 1.0)

    def _neighborhood_coords(self, x: int, y: int) -> list[tuple[int, int]]:
        coords: list[tuple[int, int]] = []
        for dx, dy in self.settings.neighborhood_offsets:
            nx = x + dx
            ny = y + dy
            if self.settings.toroidal_world:
                nx %= self.width
                ny %= self.height
                coords.append((ny, nx))
            elif 0 <= nx < self.width and 0 <= ny < self.height:
                coords.append((ny, nx))
        return coords

    def _weighted_choice(self, coords: list[tuple[int, int]], weights: list[float]) -> tuple[int, int]:
        total = sum(weights)
        pick = self.rng.random() * total
        running = 0.0
        for coord, weight in zip(coords, weights, strict=True):
            running += weight
            if pick <= running:
                return coord
        return coords[-1]

    def _benefit_and_fitness(self) -> tuple[np.ndarray, float]:
        open_received = np.zeros((self.height, self.width), dtype=np.float64)
        retained_received = np.zeros((self.height, self.width), dtype=np.float64)
        mean_same_lineage_recipients = 0.0
        total_sites = self.width * self.height

        for y in range(self.height):
            for x in range(self.width):
                coords = self._neighborhood_coords(x, y)
                total_benefit = self.settings.cooperation_benefit * self.cooperation[y, x]
                retained_benefit = (
                    self.settings.retained_benefit_fraction * total_benefit
                )
                open_benefit = total_benefit - retained_benefit

                open_share = open_benefit / len(coords)
                lineage_id = int(self.lineage[y, x])
                same_lineage_coords = [
                    (ny, nx) for ny, nx in coords if int(self.lineage[ny, nx]) == lineage_id
                ]
                retained_share = retained_benefit / len(same_lineage_coords)

                mean_same_lineage_recipients += len(same_lineage_coords) / len(coords)
                for ny, nx in coords:
                    open_received[ny, nx] += open_share
                for ny, nx in same_lineage_coords:
                    retained_received[ny, nx] += retained_share

        mean_same_lineage_recipients /= total_sites
        self.last_fitness = (
            self.settings.base_fitness
            + open_received
            + retained_received
            - (self.settings.cooperation_cost * self.cooperation)
        )
        np.maximum(self.last_fitness, 1e-6, out=self.last_fitness)
        return self.last_fitness, mean_same_lineage_recipients

    def _measure_local_assortment(self) -> float:
        same_share_sum = 0.0
        total_sites = self.width * self.height
        for y in range(self.height):
            for x in range(self.width):
                coords = self._neighborhood_coords(x, y)
                lineage_id = int(self.lineage[y, x])
                same_count = sum(
                    1 for ny, nx in coords if int(self.lineage[ny, nx]) == lineage_id
                )
                same_share_sum += same_count / len(coords)
        return same_share_sum / total_sites

    def _dominant_lineage_share(self) -> float:
        unique_lineages, counts = np.unique(self.lineage, return_counts=True)
        if unique_lineages.size == 0:
            return 0.0
        return float(np.max(counts) / counts.sum())

    def record_history(self) -> None:
        local_assortment = self._measure_local_assortment()
        unique_lineages = np.unique(self.lineage)
        self.history["step"].append(float(self.step_count))
        self.history["mean_cooperation"].append(float(np.mean(self.cooperation)))
        self.history["var_cooperation"].append(float(np.var(self.cooperation)))
        self.history["mean_fitness"].append(float(np.mean(self.last_fitness)))
        self.history["local_assortment"].append(float(local_assortment))
        self.history["dominant_lineage_share"].append(self._dominant_lineage_share())
        self.history["lineage_count"].append(float(unique_lineages.size))

    def step(self) -> None:
        fitness, _ = self._benefit_and_fitness()
        next_cooperation = np.empty_like(self.cooperation)
        next_lineage = np.empty_like(self.lineage)

        for y in range(self.height):
            for x in range(self.width):
                coords = self._neighborhood_coords(x, y)
                weights = [float(fitness[ny, nx]) for ny, nx in coords]
                parent_y, parent_x = self._weighted_choice(coords, weights)

                child_trait = float(self.cooperation[parent_y, parent_x])
                if self.rng.random() < self.settings.mutation_rate:
                    child_trait += self.rng.gauss(0.0, self.settings.mutation_stddev)
                next_cooperation[y, x] = min(1.0, max(0.0, child_trait))
                next_lineage[y, x] = self.lineage[parent_y, parent_x]

        self.cooperation = next_cooperation
        self.lineage = next_lineage
        self.step_count += 1
        self._benefit_and_fitness()
        self.record_history()

    def run(self) -> dict[str, Any]:
        print(
            "Running Retained Benefit model with "
            f"grid={self.width}x{self.height}, "
            f"steps={self.settings.simulation_steps}, "
            "retained="
            f"{self.settings.retained_benefit_fraction:.2f}, "
            "benefit="
            f"{self.settings.cooperation_benefit:.2f}, "
            "cost="
            f"{self.settings.cooperation_cost:.2f}, "
            f"seed={self.settings.random_seed}"
        )

        for _ in range(self.settings.simulation_steps):
            self.step()
            if (
                self.settings.summary_interval_steps
                and self.step_count % self.settings.summary_interval_steps == 0
            ):
                print(
                    f"step={self.step_count:04d} "
                    "mean_h="
                    f"{self.history['mean_cooperation'][-1]:.3f} "
                    "assortment="
                    f"{self.history['local_assortment'][-1]:.3f} "
                    "dominant_lineage="
                    f"{self.history['dominant_lineage_share'][-1]:.3f} "
                    "lineages="
                    f"{int(self.history['lineage_count'][-1])}"
                )

        payload = {
            "timestamp": strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.settings.to_dict(),
            "history": self.history,
            "final_summary": {
                "steps": self.step_count,
                "mean_cooperation": self.history["mean_cooperation"][-1],
                "var_cooperation": self.history["var_cooperation"][-1],
                "mean_fitness": self.history["mean_fitness"][-1],
                "local_assortment": self.history["local_assortment"][-1],
                "dominant_lineage_share": self.history["dominant_lineage_share"][-1],
                "lineage_count": int(self.history["lineage_count"][-1]),
            },
            "final_state": {
                "cooperation_grid": self.cooperation.tolist(),
                "lineage_grid": self.lineage.tolist(),
            },
        }

        print("Final summary:")
        print(
            f"steps={payload['final_summary']['steps']} "
            "mean_h="
            f"{payload['final_summary']['mean_cooperation']:.3f} "
            "assortment="
            f"{payload['final_summary']['local_assortment']:.3f} "
            "dominant_lineage="
            f"{payload['final_summary']['dominant_lineage_share']:.3f} "
            "lineages="
            f"{payload['final_summary']['lineage_count']}"
        )

        if self.settings.write_log:
            output_path = Path(self.settings.log_output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"Wrote run log to {output_path}")

        if self.settings.show_matplotlib_plots:
            plot_run_summary(self.history, self.settings)

        return payload


def run_sim(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run the model once and return the output payload."""
    settings = make_settings(config)
    model = RetainedBenefitModel(settings)
    return model.run()


def main() -> None:
    run_sim()


if __name__ == "__main__":
    main()
