#!/usr/bin/env python3
"""Live grid viewer for the continuous spatial-memory scaffold."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "moran_models.nowak_mechanisms.direct_reciprocity.scaffolds.continuous_spatial_memory."
        "continuous_spatial_memory_pygame_ui'."
    )

from moran_models.interaction_kernel.live_grid_view import run_live_grid_view

from .config.continuous_spatial_memory_config import config as model_config
from .continuous_spatial_memory_model import ContinuousSpatialMemoryModel


def _build_explanation_lines(cfg: dict[str, float]) -> list[str]:
    return [
        "Mechanism: direct reciprocity through pair-specific neighbor memory.",
        (
            f"Memory decay={float(cfg['memory_decay']):.2f}; "
            f"expression gain={float(cfg['memory_expression_gain']):.2f}."
        ),
        f"Benefit scale B+={float(cfg['B_plus_scale']):.2f}; cost scale C={float(cfg['C_scale']):.2f}.",
        "Each square is one individual.",
        "Blue is low cooperation; orange is high.",
        "Sites preferentially return help to neighbors that helped them before.",
        "This is spatially scaffolded by local routing and local replacement.",
    ]


def main() -> None:
    run_live_grid_view(
        model_class=ContinuousSpatialMemoryModel,
        model_config=model_config,
        window_caption="Continuous Spatial-Memory Scaffold",
        header_title="Direct Reciprocity Scaffold: Continuous Spatial Memory",
        explanation_builder=_build_explanation_lines,
    )


if __name__ == "__main__":
    main()
