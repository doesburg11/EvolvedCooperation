"""Shared Moran interaction engine for Nowak-style cooperation mechanisms."""

from __future__ import annotations

from typing import Any

import numpy as np

from .mechanisms import ExtraState, MoranMechanism
from .metrics import compute_step_metrics
from .selection import local_replacement_step
from .space import grid_neighbor_indices, neighbor_mask_from_indices


class MoranInteractionEngine:
    """Reusable Moran engine with pluggable mechanism logic."""

    def __init__(self, cfg: dict[str, Any], mechanism: MoranMechanism):
        self.cfg = dict(cfg)
        self.mechanism = mechanism

        self.width = int(self.cfg["grid_width"])
        self.height = int(self.cfg["grid_height"])
        self.n_sites = self.width * self.height
        self.rng = np.random.default_rng(int(self.cfg["random_seed"]))

        self.neighbor_indices = grid_neighbor_indices(
            self.width,
            self.height,
            bool(self.cfg["toroidal_world"]),
            str(self.cfg["neighborhood_mode"]),
            bool(self.cfg["include_self_in_neighborhood"]),
        )
        self.neighbor_mask = neighbor_mask_from_indices(self.neighbor_indices)

        mean = float(self.cfg["initial_trait_mean"])
        std = float(self.cfg["initial_trait_stddev"])
        self.h = np.clip(self.rng.normal(mean, std, size=self.n_sites), 0.0, 1.0)

        identity_count = max(1, int(self.cfg["initial_identity_count"]))
        self.lineage = self.rng.integers(0, identity_count, size=self.n_sites, dtype=np.int32)
        self.extra_state: ExtraState = self.mechanism.initialize_extra_state(
            self.cfg,
            self.n_sites,
            self.rng,
        )
        self.step_index = 0
        self.history: list[dict[str, float]] = []

    def step(self) -> dict[str, float]:
        """Advance one synchronous Moran step and return summary metrics."""
        K_plus = self.mechanism.build_positive_kernel(
            self.neighbor_mask,
            self.lineage,
            self.extra_state,
            self.cfg,
        )
        K_minus = self.mechanism.build_negative_kernel(
            self.neighbor_mask,
            self.lineage,
            self.extra_state,
            self.cfg,
        )

        B_plus = self.mechanism.compute_positive_output(self.h, self.extra_state, self.cfg)
        B_minus = self.mechanism.compute_negative_output(self.h, self.extra_state, self.cfg)
        C = self.mechanism.compute_private_cost(self.h, self.extra_state, self.cfg)

        R_plus = K_plus.T @ B_plus
        R_minus = K_minus.T @ B_minus
        W = float(self.cfg["base_fitness"]) + R_plus - R_minus - C

        step_context = {
            "step_index": np.array([self.step_index], dtype=np.int32),
            "trait": self.h.copy(),
            "lineage": self.lineage.copy(),
            "B_plus": B_plus.copy(),
            "B_minus": B_minus.copy(),
            "R_plus": R_plus.copy(),
            "R_minus": R_minus.copy(),
            "fitness": W.copy(),
            **{key: values.copy() for key, values in self.extra_state.items()},
        }

        metrics = compute_step_metrics(self.h, R_plus, R_minus, W)
        self.history.append(metrics)

        self.h, self.lineage, parent_indices = local_replacement_step(
            self.h,
            self.lineage,
            W,
            self.neighbor_indices,
            self.rng,
            float(self.cfg["selection_temperature"]),
            float(self.cfg["mutation_rate"]),
            float(self.cfg["mutation_stddev"]),
        )
        self.extra_state = self.mechanism.inherit_extra_state(
            self.extra_state,
            parent_indices,
            step_context,
            self.rng,
            self.cfg,
        )
        self.h, self.lineage, self.extra_state = self.mechanism.post_reproduction_update(
            self.h,
            self.lineage,
            self.extra_state,
            step_context,
            self.rng,
            self.cfg,
        )
        self.step_index += 1
        return metrics

    def run(self) -> dict[str, Any]:
        """Run the configured number of steps and return a result payload."""
        n_steps = int(self.cfg["simulation_steps"])
        summary_interval = max(1, int(self.cfg["summary_interval_steps"]))

        for t in range(n_steps):
            step_metrics = self.step()
            if (t + 1) % summary_interval == 0 or t == 0 or (t + 1) == n_steps:
                print(
                    f"[{self.mechanism.name}] step={t + 1:4d}/{n_steps} "
                    f"mean_trait={step_metrics['mean_trait']:.4f} "
                    f"mean_fitness={step_metrics['mean_fitness']:.4f}"
                )

        return {
            "config": self.cfg,
            "mechanism": self.mechanism.name,
            "final_mean_trait": float(np.mean(self.h)),
            "final_std_trait": float(np.std(self.h)),
            "final_identity_count": int(np.unique(self.lineage).size),
            "history": self.history,
        }
