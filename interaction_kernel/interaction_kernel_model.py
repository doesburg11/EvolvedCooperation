#!/usr/bin/env python3
"""General interaction-kernel simulation module.

Notation used in this code follows the website theory page closely.

Equation layer:
- B_plus(j): positive effect produced by producer j
- B_minus(j): negative effect produced by producer j
- K_plus(j -> i): positive routing kernel from j to i
- K_minus(j -> i): negative routing kernel from j to i
- R_plus(i): total positive return received by i
- R_minus(i): total negative return received by i
- C(i): private cost paid by i
- W(i): fitness/selection score of i

Vectorized step equations implemented below:
- B_plus = B_plus_scale * h
- B_minus = B_minus_scale * h
- R_plus = K_plus^T @ B_plus
- R_minus = K_minus^T @ B_minus
- W = base_fitness + R_plus - R_minus - C
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .config.interaction_kernel_config import config
from .kernels import build_kin_weighted_kernel, build_uniform_kernel
from .metrics import compute_step_metrics
from .selection import local_replacement_step


def _resolve_runtime_config(raw_cfg: dict[str, Any]) -> dict[str, Any]:
    """Resolve runtime config with backwards-compatible aliases.

    Canonical keys are theory-aligned:
    - B_plus_scale
    - B_minus_scale
    - C_scale

    Legacy aliases supported:
    - positive_output_scale -> B_plus_scale
    - negative_output_scale -> B_minus_scale
    - trait_cost_scale -> C_scale
    """
    cfg = dict(raw_cfg)

    alias_to_canonical = {
        "positive_output_scale": "B_plus_scale",
        "negative_output_scale": "B_minus_scale",
        "trait_cost_scale": "C_scale",
    }
    for legacy_key, canonical_key in alias_to_canonical.items():
        if canonical_key not in cfg and legacy_key in cfg:
            cfg[canonical_key] = cfg[legacy_key]

    required = ("B_plus_scale", "B_minus_scale", "C_scale")
    missing = [key for key in required if key not in cfg]
    if missing:
        raise KeyError(f"Missing required config keys: {missing}")
    return cfg


def _grid_neighbor_indices(
    width: int,
    height: int,
    toroidal: bool,
    mode: str,
    include_self: bool,
) -> list[np.ndarray]:
    if mode not in {"von_neumann", "moore"}:
        raise ValueError(f"Unsupported neighborhood_mode: {mode}")

    if mode == "von_neumann":
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    else:
        offsets = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

    def idx(x: int, y: int) -> int:
        return y * width + x

    neighbors: list[np.ndarray] = []
    for y in range(height):
        for x in range(width):
            local: list[int] = []
            if include_self:
                local.append(idx(x, y))
            for dx, dy in offsets:
                nx, ny = x + dx, y + dy
                if toroidal:
                    nx %= width
                    ny %= height
                    local.append(idx(nx, ny))
                else:
                    if 0 <= nx < width and 0 <= ny < height:
                        local.append(idx(nx, ny))
            neighbors.append(np.array(local, dtype=np.int32))
    return neighbors


def _neighbor_mask(neighbor_indices: list[np.ndarray]) -> np.ndarray:
    n_sites = len(neighbor_indices)
    mask = np.zeros((n_sites, n_sites), dtype=bool)
    for i, nbrs in enumerate(neighbor_indices):
        mask[i, nbrs] = True
    return mask


class InteractionKernelModel:
    """Reusable interaction-kernel engine with theory-aligned symbols.

    State variables:
    - h: trait vector in [0, 1]
    - lineage: inherited identity label per site
    """

    def __init__(self, cfg: dict[str, Any]):
        self.cfg = dict(cfg)
        self.width = int(self.cfg["grid_width"])
        self.height = int(self.cfg["grid_height"])
        self.n_sites = self.width * self.height

        self.rng = np.random.default_rng(int(self.cfg["random_seed"]))

        self.neighbor_indices = _grid_neighbor_indices(
            self.width,
            self.height,
            bool(self.cfg["toroidal_world"]),
            str(self.cfg["neighborhood_mode"]),
            bool(self.cfg["include_self_in_neighborhood"]),
        )
        self.neighbor_mask = _neighbor_mask(self.neighbor_indices)

        mean = float(self.cfg["initial_trait_mean"])
        std = float(self.cfg["initial_trait_stddev"])
        self.h = np.clip(self.rng.normal(mean, std, size=self.n_sites), 0.0, 1.0)

        identity_count = max(1, int(self.cfg["initial_identity_count"]))
        self.lineage = self.rng.integers(0, identity_count, size=self.n_sites, dtype=np.int32)

        self.history: list[dict[str, float]] = []

    def _build_K_plus(self) -> np.ndarray:
        mode = str(self.cfg["positive_kernel_mode"])
        if mode == "uniform":
            return build_uniform_kernel(self.neighbor_mask)
        if mode == "kin_weighted":
            return build_kin_weighted_kernel(
                self.neighbor_mask,
                self.lineage,
                float(self.cfg["kin_weight_same_lineage"]),
                float(self.cfg["kin_weight_other_lineage"]),
            )
        raise ValueError(f"Unsupported positive_kernel_mode: {mode}")

    def _build_K_minus(self) -> np.ndarray:
        mode = str(self.cfg["negative_kernel_mode"])
        if mode == "none":
            return np.zeros((self.n_sites, self.n_sites), dtype=float)
        if mode == "uniform":
            return build_uniform_kernel(self.neighbor_mask)
        raise ValueError(f"Unsupported negative_kernel_mode: {mode}")

    def _compute_B_plus(self) -> np.ndarray:
        """Compute produced positive effect B_plus from trait h."""
        return float(self.cfg["B_plus_scale"]) * self.h

    def _compute_B_minus(self) -> np.ndarray:
        """Compute produced negative effect B_minus from trait h."""
        return float(self.cfg["B_minus_scale"]) * self.h

    def _compute_C(self) -> np.ndarray:
        """Compute private cost C from trait h."""
        return float(self.cfg["C_scale"]) * self.h

    def step(self) -> dict[str, float]:
        """Advance one synchronous step using theory-aligned variables.

        Returns summary metrics for this step.
        """
        K_plus = self._build_K_plus()
        K_minus = self._build_K_minus()

        B_plus = self._compute_B_plus()
        B_minus = self._compute_B_minus()

        R_plus = K_plus.T @ B_plus
        R_minus = K_minus.T @ B_minus

        W = float(self.cfg["base_fitness"]) + R_plus - R_minus - self._compute_C()

        metrics = compute_step_metrics(self.h, R_plus, R_minus, W)
        self.history.append(metrics)

        self.h, self.lineage = local_replacement_step(
            self.h,
            self.lineage,
            W,
            self.neighbor_indices,
            self.rng,
            float(self.cfg["selection_temperature"]),
            float(self.cfg["mutation_rate"]),
            float(self.cfg["mutation_stddev"]),
        )

        return metrics

    def run(self) -> dict[str, Any]:
        n_steps = int(self.cfg["simulation_steps"])
        summary_interval = max(1, int(self.cfg["summary_interval_steps"]))

        for t in range(n_steps):
            step_metrics = self.step()
            if (t + 1) % summary_interval == 0 or t == 0 or (t + 1) == n_steps:
                print(
                    f"[interaction_kernel] step={t + 1:4d}/{n_steps} "
                    f"mean_trait={step_metrics['mean_trait']:.4f} "
                    f"mean_fitness={step_metrics['mean_fitness']:.4f}"
                )

        payload = {
            "config": self.cfg,
            "final_mean_trait": float(np.mean(self.h)),
            "final_std_trait": float(np.std(self.h)),
            "final_identity_count": int(np.unique(self.lineage).size),
            "history": self.history,
        }
        return payload


def _write_log(payload: dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_simulation(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime_cfg = _resolve_runtime_config(config if cfg is None else cfg)
    model = InteractionKernelModel(runtime_cfg)
    payload = model.run()

    if bool(runtime_cfg.get("write_log", True)):
        _write_log(payload, str(runtime_cfg["log_output_path"]))
        print(f"[interaction_kernel] wrote log -> {runtime_cfg['log_output_path']}")
    return payload


if __name__ == "__main__":
    run_simulation()
