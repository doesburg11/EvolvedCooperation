#!/usr/bin/env python3
"""Live grid viewer for the network_reciprocity package."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m moran_models.nowak_mechanisms.network_reciprocity.network_reciprocity_pygame_ui'."
    )

from moran_models.interaction_kernel.live_grid_view import run_live_grid_view

from .config.network_reciprocity_config import config as model_config
from .network_reciprocity_model import NetworkReciprocityModel


def _build_explanation_lines(cfg: dict[str, float]) -> list[str]:
    return [
        "Mechanism: network reciprocity through local graph structure.",
        "Positive returns are shared uniformly across each local neighborhood.",
        f"Benefit scale B+={float(cfg['B_plus_scale']):.2f}; cost scale C={float(cfg['C_scale']):.2f}.",
        "Each square is one individual.",
        "Blue is low cooperation; orange is high.",
        "Local clusters can protect cooperating lineages from invasion.",
    ]


def main() -> None:
    run_live_grid_view(
        model_class=NetworkReciprocityModel,
        model_config=model_config,
        window_caption="Network Reciprocity Live Grid",
        header_title="Network Reciprocity: Live Trait Grid",
        explanation_builder=_build_explanation_lines,
    )


if __name__ == "__main__":
    main()
