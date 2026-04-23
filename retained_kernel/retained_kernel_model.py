#!/usr/bin/env python3
"""
retained_kernel_model.py

General retained-feedback kernel for local trait selection.

Run from the repo root with:
  ./.conda/bin/python -m retained_kernel.retained_kernel_model
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from time import strftime
from typing import Any

import numpy as np

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m retained_kernel.retained_kernel_model'."
    )

from .config.retained_kernel_config import config as model_config
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
    trait_cost_scale: float = float(model_config["trait_cost_scale"])
    trait_output_scale: float = float(model_config["trait_output_scale"])
    retention_fraction: float = float(model_config["retention_fraction"])
    mutation_rate: float = float(model_config["mutation_rate"])
    mutation_stddev: float = float(model_config["mutation_stddev"])
    initial_trait_mean: float = float(model_config["initial_trait_mean"])
    initial_trait_stddev: float = float(model_config["initial_trait_stddev"])
    initial_identity_count: int = int(model_config["initial_identity_count"])
    initial_identity_block_size: int = int(model_config["initial_identity_block_size"])
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
        if self.trait_cost_scale < 0.0:
            raise ValueError("trait_cost_scale must be >= 0")
        if self.trait_output_scale < 0.0:
            raise ValueError("trait_output_scale must be >= 0")
        if not 0.0 <= self.retention_fraction <= 1.0:
            raise ValueError("retention_fraction must be within [0, 1]")
        if not 0.0 <= self.mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be within [0, 1]")
        if self.mutation_stddev < 0.0:
            raise ValueError("mutation_stddev must be >= 0")
        if not 0.0 <= self.initial_trait_mean <= 1.0:
            raise ValueError("initial_trait_mean must be within [0, 1]")
        if self.initial_trait_stddev < 0.0:
            raise ValueError("initial_trait_stddev must be >= 0")
        if self.initial_identity_count < 1:
            raise ValueError("initial_identity_count must be >= 1")
        if self.initial_identity_block_size < 1:
            raise ValueError("initial_identity_block_size must be >= 1")
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


class RetainedKernelModel:
    """
    Abstract local-selection kernel with one continuous trait and one identity tag.

    The kernel is intentionally generic: each site emits trait-scaled output,
    keeps a retained fraction for identity-matching recipients, distributes the
    remaining output openly across the neighborhood, and then performs local
    fitness-proportional replacement.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.rng = random.Random(self.settings.random_seed)
        self.width = self.settings.grid_width
        self.height = self.settings.grid_height
        self.step_count = 0

        self.identity = self._initial_identity_grid()
        self.trait = self._initial_trait_grid()

        self.history: dict[str, list[float]] = {
            "step": [],
            "mean_trait": [],
            "var_trait": [],
            "mean_fitness": [],
            "local_match_share": [],
            "dominant_identity_share": [],
            "identity_count": [],
        }
        self.last_fitness = np.full((self.height, self.width), self.settings.base_fitness)
        self.record_history()

    def _initial_identity_grid(self) -> np.ndarray:
        block = self.settings.initial_identity_block_size
        identity = np.zeros((self.height, self.width), dtype=np.int32)
        for y0 in range(0, self.height, block):
            for x0 in range(0, self.width, block):
                identity_id = self.rng.randrange(self.settings.initial_identity_count)
                y1 = min(self.height, y0 + block)
                x1 = min(self.width, x0 + block)
                identity[y0:y1, x0:x1] = identity_id
        return identity

    def _initial_trait_grid(self) -> np.ndarray:
        mean = self.settings.initial_trait_mean
        std = self.settings.initial_trait_stddev
        trait = np.array(
            [
                [self.rng.gauss(mean, std) for _ in range(self.width)]
                for _ in range(self.height)
            ],
            dtype=np.float64,
        )
        return np.clip(trait, 0.0, 1.0)

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

    def _weighted_choice(
        self,
        coords: list[tuple[int, int]],
        weights: list[float],
    ) -> tuple[int, int]:
        total = sum(weights)
        pick = self.rng.random() * total
        running = 0.0
        for coord, weight in zip(coords, weights, strict=True):
            running += weight
            if pick <= running:
                return coord
        return coords[-1]

    def _apply_retained_kernel(self) -> np.ndarray:
        open_received = np.zeros((self.height, self.width), dtype=np.float64)
        retained_received = np.zeros((self.height, self.width), dtype=np.float64)

        for y in range(self.height):
            for x in range(self.width):
                coords = self._neighborhood_coords(x, y)
                gross_output = self.settings.trait_output_scale * self.trait[y, x]
                retained_output = self.settings.retention_fraction * gross_output
                open_output = gross_output - retained_output

                open_share = open_output / len(coords)
                identity_id = int(self.identity[y, x])
                matched_coords = [
                    (ny, nx)
                    for ny, nx in coords
                    if int(self.identity[ny, nx]) == identity_id
                ]
                retained_share = retained_output / len(matched_coords)

                for ny, nx in coords:
                    open_received[ny, nx] += open_share
                for ny, nx in matched_coords:
                    retained_received[ny, nx] += retained_share

        self.last_fitness = (
            self.settings.base_fitness
            + open_received
            + retained_received
            - (self.settings.trait_cost_scale * self.trait)
        )
        np.maximum(self.last_fitness, 1e-6, out=self.last_fitness)
        return self.last_fitness

    def _measure_local_match_share(self) -> float:
        same_share_sum = 0.0
        total_sites = self.width * self.height
        for y in range(self.height):
            for x in range(self.width):
                coords = self._neighborhood_coords(x, y)
                identity_id = int(self.identity[y, x])
                same_count = sum(
                    1 for ny, nx in coords if int(self.identity[ny, nx]) == identity_id
                )
                same_share_sum += same_count / len(coords)
        return same_share_sum / total_sites

    def _dominant_identity_share(self) -> float:
        unique_identities, counts = np.unique(self.identity, return_counts=True)
        if unique_identities.size == 0:
            return 0.0
        return float(np.max(counts) / counts.sum())

    def record_history(self) -> None:
        unique_identities = np.unique(self.identity)
        self.history["step"].append(float(self.step_count))
        self.history["mean_trait"].append(float(np.mean(self.trait)))
        self.history["var_trait"].append(float(np.var(self.trait)))
        self.history["mean_fitness"].append(float(np.mean(self.last_fitness)))
        self.history["local_match_share"].append(
            float(self._measure_local_match_share())
        )
        self.history["dominant_identity_share"].append(
            self._dominant_identity_share()
        )
        self.history["identity_count"].append(float(unique_identities.size))

    def step(self) -> None:
        fitness = self._apply_retained_kernel()
        next_trait = np.empty_like(self.trait)
        next_identity = np.empty_like(self.identity)

        for y in range(self.height):
            for x in range(self.width):
                coords = self._neighborhood_coords(x, y)
                weights = [float(fitness[ny, nx]) for ny, nx in coords]
                parent_y, parent_x = self._weighted_choice(coords, weights)

                child_trait = float(self.trait[parent_y, parent_x])
                if self.rng.random() < self.settings.mutation_rate:
                    child_trait += self.rng.gauss(0.0, self.settings.mutation_stddev)
                next_trait[y, x] = min(1.0, max(0.0, child_trait))
                next_identity[y, x] = self.identity[parent_y, parent_x]

        self.trait = next_trait
        self.identity = next_identity
        self.step_count += 1
        self._apply_retained_kernel()
        self.record_history()

    def run(self) -> dict[str, Any]:
        print(
            "Running Retained Kernel with "
            f"grid={self.width}x{self.height}, "
            f"steps={self.settings.simulation_steps}, "
            "retention="
            f"{self.settings.retention_fraction:.2f}, "
            "output="
            f"{self.settings.trait_output_scale:.2f}, "
            "cost="
            f"{self.settings.trait_cost_scale:.2f}, "
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
                    "mean_trait="
                    f"{self.history['mean_trait'][-1]:.3f} "
                    "match_share="
                    f"{self.history['local_match_share'][-1]:.3f} "
                    "dominant_identity="
                    f"{self.history['dominant_identity_share'][-1]:.3f} "
                    "identities="
                    f"{int(self.history['identity_count'][-1])}"
                )

        payload = {
            "timestamp": strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.settings.to_dict(),
            "history": self.history,
            "final_summary": {
                "steps": self.step_count,
                "mean_trait": self.history["mean_trait"][-1],
                "var_trait": self.history["var_trait"][-1],
                "mean_fitness": self.history["mean_fitness"][-1],
                "local_match_share": self.history["local_match_share"][-1],
                "dominant_identity_share": self.history["dominant_identity_share"][-1],
                "identity_count": int(self.history["identity_count"][-1]),
            },
            "final_state": {
                "trait_grid": self.trait.tolist(),
                "identity_grid": self.identity.tolist(),
            },
        }

        print("Final summary:")
        print(
            f"steps={payload['final_summary']['steps']} "
            "mean_trait="
            f"{payload['final_summary']['mean_trait']:.3f} "
            "match_share="
            f"{payload['final_summary']['local_match_share']:.3f} "
            "dominant_identity="
            f"{payload['final_summary']['dominant_identity_share']:.3f} "
            "identities="
            f"{payload['final_summary']['identity_count']}"
        )

        if self.settings.write_log:
            output_path = Path(self.settings.log_output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"Wrote run log to {output_path}")

        if self.settings.show_matplotlib_plots:
            plot_run_summary(self.history, self.settings)

        return payload


def run_sim(settings: Settings | None = None) -> dict[str, Any]:
    """Run the kernel once and return the output payload."""
    model = RetainedKernelModel(settings or Settings())
    return model.run()


def main() -> None:
    run_sim()


if __name__ == "__main__":
    main()
