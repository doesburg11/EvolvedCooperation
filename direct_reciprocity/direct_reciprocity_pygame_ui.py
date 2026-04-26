#!/usr/bin/env python3
"""Live grid viewer for the direct_reciprocity package."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m direct_reciprocity.direct_reciprocity_pygame_ui'."
    )

from interaction_kernel.live_grid_view import run_live_grid_view

from .config.direct_reciprocity_config import config as model_config
from .direct_reciprocity_model import DirectReciprocityModel


def _build_explanation_lines(cfg: dict[str, float]) -> list[str]:
    return [
        "Mechanism: direct reciprocity through remembered received help.",
        (
            f"Memory decay={float(cfg['memory_decay']):.2f}; "
            f"expression gain={float(cfg['memory_expression_gain']):.2f}."
        ),
        f"Benefit scale B+={float(cfg['B_plus_scale']):.2f}; cost scale C={float(cfg['C_scale']):.2f}.",
        "Each square is one individual.",
        "Blue is low cooperation; orange is high.",
        "Sites that were helped recently tend to help more next round.",
    ]


def main() -> None:
    run_live_grid_view(
        model_class=DirectReciprocityModel,
        model_config=model_config,
        window_caption="Direct Reciprocity Live Grid",
        header_title="Direct Reciprocity: Live Trait Grid",
        explanation_builder=_build_explanation_lines,
    )


if __name__ == "__main__":
    main()
