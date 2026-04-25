"""Kernel construction helpers for interaction_kernel.

The module keeps kernel construction explicit so mechanisms can be swapped by
configuration instead of rewriting the simulation core.
"""

from __future__ import annotations

import numpy as np


def normalize_rows(weights: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Return row-normalized nonnegative weights."""
    clipped = np.clip(weights, 0.0, None)
    row_sums = clipped.sum(axis=1, keepdims=True)
    safe = np.where(row_sums > eps, row_sums, 1.0)
    return clipped / safe


def build_uniform_kernel(neighbor_mask: np.ndarray) -> np.ndarray:
    """Build a kernel that assigns equal weight to each allowed recipient."""
    weights = neighbor_mask.astype(float)
    return normalize_rows(weights)


def build_kin_weighted_kernel(
    neighbor_mask: np.ndarray,
    lineage: np.ndarray,
    same_lineage_weight: float,
    other_lineage_weight: float,
) -> np.ndarray:
    """Build a lineage-sensitive positive kernel.

    Rows are producers and columns are recipients.
    """
    same = (lineage[:, None] == lineage[None, :]).astype(float)
    weights = other_lineage_weight + (same_lineage_weight - other_lineage_weight) * same
    weights = weights * neighbor_mask.astype(float)
    return normalize_rows(weights)
