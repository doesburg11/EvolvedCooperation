"""Selection and inheritance helpers shared across Moran mechanisms."""

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


def sample_local_parent_indices(
    fitness: np.ndarray,
    neighbor_indices: list[np.ndarray],
    rng: np.random.Generator,
    selection_temperature: float,
) -> np.ndarray:
    """Return the sampled parent index for each focal site."""
    parent_indices = np.empty(len(neighbor_indices), dtype=np.int32)
    for i, neighborhood in enumerate(neighbor_indices):
        local_fitness = fitness[neighborhood]
        probs = _local_softmax_probabilities(local_fitness, selection_temperature)
        parent_pos = int(rng.choice(len(neighborhood), p=probs))
        parent_indices[i] = int(neighborhood[parent_pos])
    return parent_indices


def inherit_trait_and_lineage(
    trait: np.ndarray,
    lineage: np.ndarray,
    parent_indices: np.ndarray,
    rng: np.random.Generator,
    mutation_rate: float,
    mutation_stddev: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Inherit scalar trait and lineage along sampled parent indices."""
    next_trait = trait[parent_indices].astype(float, copy=True)
    next_lineage = lineage[parent_indices].astype(lineage.dtype, copy=True)

    mutate_mask = rng.random(len(parent_indices)) < mutation_rate
    if np.any(mutate_mask):
        next_trait[mutate_mask] += rng.normal(0.0, mutation_stddev, size=int(np.sum(mutate_mask)))
    next_trait = np.clip(next_trait, 0.0, 1.0)
    return next_trait, next_lineage


def local_replacement_step(
    trait: np.ndarray,
    lineage: np.ndarray,
    fitness: np.ndarray,
    neighbor_indices: list[np.ndarray],
    rng: np.random.Generator,
    selection_temperature: float,
    mutation_rate: float,
    mutation_stddev: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Perform one local replacement/update step and return parent indices."""
    parent_indices = sample_local_parent_indices(
        fitness,
        neighbor_indices,
        rng,
        selection_temperature,
    )
    next_trait, next_lineage = inherit_trait_and_lineage(
        trait,
        lineage,
        parent_indices,
        rng,
        mutation_rate,
        mutation_stddev,
    )
    return next_trait, next_lineage, parent_indices
