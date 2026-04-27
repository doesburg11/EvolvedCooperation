"""Spatial Prisoner's Dilemma package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .spatial_prisoners_dilemma import (
        PrisonerAgent,
        Settings,
        SpatialPrisonersDilemmaModel,
        make_settings,
    )

__all__ = [
    "PrisonerAgent",
    "Settings",
    "SpatialPrisonersDilemmaModel",
    "make_settings",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from .spatial_prisoners_dilemma import (
        PrisonerAgent,
        Settings,
        SpatialPrisonersDilemmaModel,
        make_settings,
    )

    exports = {
        "PrisonerAgent": PrisonerAgent,
        "Settings": Settings,
        "SpatialPrisonersDilemmaModel": SpatialPrisonersDilemmaModel,
        "make_settings": make_settings,
    }
    return exports[name]
