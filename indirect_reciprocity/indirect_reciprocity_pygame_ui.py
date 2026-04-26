#!/usr/bin/env python3
"""Live grid viewer for the indirect_reciprocity package."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m indirect_reciprocity.indirect_reciprocity_pygame_ui'."
    )

from interaction_kernel.live_grid_view import run_live_grid_view

from .config.indirect_reciprocity_config import config as model_config
from .indirect_reciprocity_model import IndirectReciprocityModel


def _build_explanation_lines(cfg: dict[str, float]) -> list[str]:
    return [
        "Mechanism: indirect reciprocity through public reputation.",
        (
            f"Observation weight={float(cfg['reputation_observation_weight']):.2f}; "
            f"kernel bias={float(cfg['reputation_kernel_bias']):.2f}."
        ),
        f"Benefit scale B+={float(cfg['B_plus_scale']):.2f}; cost scale C={float(cfg['C_scale']):.2f}.",
        "Each square is one individual.",
        "Blue is low cooperation; orange is high.",
        "Better-reputed recipients receive more routed help.",
    ]


def main() -> None:
    run_live_grid_view(
        model_class=IndirectReciprocityModel,
        model_config=model_config,
        window_caption="Indirect Reciprocity Live Grid",
        header_title="Indirect Reciprocity: Live Trait Grid",
        explanation_builder=_build_explanation_lines,
    )


if __name__ == "__main__":
    main()
