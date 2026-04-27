#!/usr/bin/env python3
"""Live grid viewer for the kin_selection package."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.kin_selection_pygame_ui'."
    )

from moran_models.interaction_kernel.live_grid_view import run_live_grid_view

from .config.kin_selection_config import config as model_config
from .kin_selection_model import KinSelectionModel


def _build_explanation_lines(cfg: dict[str, float]) -> list[str]:
    return [
        "Mechanism: kin selection through lineage-biased positive routing.",
        (
            f"Same-lineage weight={float(cfg['kin_weight_same_lineage']):.2f}; "
            f"other-lineage weight={float(cfg['kin_weight_other_lineage']):.2f}."
        ),
        f"Benefit scale B+={float(cfg['B_plus_scale']):.2f}; cost scale C={float(cfg['C_scale']):.2f}.",
        "Each square is one individual.",
        "Blue is low cooperation; orange is high.",
        "Help is directed more strongly toward same-lineage neighbors.",
    ]


def main() -> None:
    run_live_grid_view(
        model_class=KinSelectionModel,
        model_config=model_config,
        window_caption="Kin Selection Live Grid",
        header_title="Kin Selection: Live Trait Grid",
        explanation_builder=_build_explanation_lines,
    )


if __name__ == "__main__":
    main()
