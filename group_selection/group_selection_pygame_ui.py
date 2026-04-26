#!/usr/bin/env python3
"""Live grid viewer for the group_selection package."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m group_selection.group_selection_pygame_ui'."
    )

from interaction_kernel.live_grid_view import run_live_grid_view

from .config.group_selection_config import config as model_config
from .group_selection_model import GroupSelectionModel


def _build_explanation_lines(cfg: dict[str, float]) -> list[str]:
    return [
        "Mechanism: multi-level selection with explicit groups.",
        (
            f"Group count={int(cfg['group_count'])}; "
            f"group-selection interval={int(cfg['group_selection_interval'])} steps."
        ),
        f"Benefit scale B+={float(cfg['B_plus_scale']):.2f}; cost scale C={float(cfg['C_scale']):.2f}.",
        "Each square is one individual.",
        "Blue is low cooperation; orange is high.",
        "Best groups periodically overwrite worst groups.",
    ]


def main() -> None:
    run_live_grid_view(
        model_class=GroupSelectionModel,
        model_config=model_config,
        window_caption="Group Selection Live Grid",
        header_title="Group Selection: Live Trait Grid",
        explanation_builder=_build_explanation_lines,
    )


if __name__ == "__main__":
    main()
