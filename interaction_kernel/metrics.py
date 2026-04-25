"""Run-level metrics for interaction_kernel."""

from __future__ import annotations

import numpy as np


def compute_step_metrics(
    trait: np.ndarray,
    positive_return: np.ndarray,
    negative_return: np.ndarray,
    fitness: np.ndarray,
) -> dict[str, float]:
    """Return compact scalar metrics for one simulation step."""
    return {
        "mean_trait": float(np.mean(trait)),
        "std_trait": float(np.std(trait)),
        "mean_positive_return": float(np.mean(positive_return)),
        "mean_negative_return": float(np.mean(negative_return)),
        "mean_fitness": float(np.mean(fitness)),
    }
