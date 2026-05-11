#!/usr/bin/env python3
"""Live grid viewer — kin selection invasion from rare."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.kin_selection_invasion_pygame_ui'."
    )

from moran_models.interaction_kernel.live_grid_view import run_live_grid_view

from .config.kin_selection_config import config as model_config
from .kin_selection_model import KinSelectionModel

invasion_config = dict(model_config)
invasion_config["initial_trait_mean"] = 0.05
invasion_config["initial_trait_stddev"] = 0.02


def _build_explanation_lines(cfg: dict) -> list[str]:
    return [
        "Scenario: rare cooperators (~5%) invading defectors.",
        (
            f"Kin bias: same-lineage weight={float(cfg['kin_weight_same_lineage']):.2f}; "
            f"other-lineage weight={float(cfg['kin_weight_other_lineage']):.2f}."
        ),
        f"b/c = {float(cfg['B_plus_scale']):.2f} / {float(cfg['C_scale']):.2f} = {float(cfg['B_plus_scale']) / float(cfg['C_scale']):.1f}.",
        "Blue = defector (trait 0); orange = cooperator (trait 1).",
        "Cooperators preferentially benefit same-lineage neighbours.",
        "Press R to reset and watch a new invasion.",
    ]


def main() -> None:
    run_live_grid_view(
        model_class=KinSelectionModel,
        model_config=invasion_config,
        window_caption="Kin Selection — Invasion from Rare",
        header_title="Kin Selection: Cooperator Invasion",
        explanation_builder=_build_explanation_lines,
    )


if __name__ == "__main__":
    main()
