"""Compatibility re-export for the canonical core selection helpers."""

from .core.selection import (
    inherit_trait_and_lineage,
    local_replacement_step,
    sample_local_parent_indices,
)

__all__ = [
    "sample_local_parent_indices",
    "inherit_trait_and_lineage",
    "local_replacement_step",
]
