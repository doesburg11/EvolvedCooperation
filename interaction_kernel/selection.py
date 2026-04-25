"""Selection and inheritance helpers for interaction_kernel."""

from __future__ import annotations

import numpy as np


def _local_softmax_probabilities(values: np.ndarray, temperature: float) -> np.ndarray:
    """Convert local values into a probability vector."""
    temp = max(float(temperature), 1e-9)
    centered = (values - float(values.max())) / temp
    exp_vals = np.exp(centered)
    denom = float(exp_vals.sum())
    if denom <= 0.0:
        return np.full_like(exp_vals, 1.0 / len(exp_vals))
    return exp_vals / denom


def local_replacement_step(
    trait: np.ndarray,
    lineage: np.ndarray,
    fitness: np.ndarray,
    neighbor_indices: list[np.ndarray],
    rng: np.random.Generator,
    selection_temperature: float,
    mutation_rate: float,
    mutation_stddev: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Perform one local replacement/update step.

    Each site selects a parent from its neighborhood proportional to local
    softmax fitness.
    """
    n_sites = len(trait)
    next_trait = np.empty_like(trait)
    next_lineage = np.empty_like(lineage)

    for i in range(n_sites):
        neighborhood = neighbor_indices[i]
        local_fitness = fitness[neighborhood]
        probs = _local_softmax_probabilities(local_fitness, selection_temperature)
        parent_pos = int(rng.choice(len(neighborhood), p=probs))
        parent_idx = int(neighborhood[parent_pos])

        inherited_trait = float(trait[parent_idx])
        if rng.random() < mutation_rate:
            inherited_trait += float(rng.normal(0.0, mutation_stddev))
        next_trait[i] = np.clip(inherited_trait, 0.0, 1.0)
        next_lineage[i] = lineage[parent_idx]

    return next_trait, next_lineage
