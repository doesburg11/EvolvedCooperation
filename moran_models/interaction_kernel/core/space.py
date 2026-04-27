"""Spatial helpers shared by interaction-kernel mechanism packages."""

from __future__ import annotations

import numpy as np


def grid_neighbor_indices(
    width: int,
    height: int,
    toroidal: bool,
    mode: str,
    include_self: bool,
) -> list[np.ndarray]:
    """Return neighborhood indices for each site in the grid."""
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
                elif 0 <= nx < width and 0 <= ny < height:
                    local.append(idx(nx, ny))
            neighbors.append(np.array(local, dtype=np.int32))
    return neighbors


def neighbor_mask_from_indices(neighbor_indices: list[np.ndarray]) -> np.ndarray:
    """Build a dense neighbor mask from precomputed neighborhood indices."""
    n_sites = len(neighbor_indices)
    mask = np.zeros((n_sites, n_sites), dtype=bool)
    for i, nbrs in enumerate(neighbor_indices):
        mask[i, nbrs] = True
    return mask
