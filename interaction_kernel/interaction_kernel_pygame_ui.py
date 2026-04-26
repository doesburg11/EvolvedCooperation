#!/usr/bin/env python3
"""Live grid viewer for interaction_kernel."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m interaction_kernel.interaction_kernel_pygame_ui'."
    )

from .config.interaction_kernel_config import config as model_config
from .interaction_kernel_model import InteractionKernelModel
from .live_grid_view import run_live_grid_view


def _build_explanation_lines(cfg: dict[str, float]) -> list[str]:
    positive_mode = str(cfg["positive_kernel_mode"])
    same_w = float(cfg["kin_weight_same_lineage"])
    other_w = float(cfg["kin_weight_other_lineage"])
    b_plus_scale = float(cfg["B_plus_scale"])
    c_scale = float(cfg["C_scale"])

    if positive_mode == "kin_weighted":
        mechanism_line = "Mechanism: kin-weighted positive kernel (kin selection ON)."
        weight_line = f"Same-lineage weight={same_w:.2f}; other-lineage weight={other_w:.2f}."
    else:
        mechanism_line = "Mechanism: uniform positive kernel (kin selection OFF)."
        weight_line = "All eligible neighbors receive equal positive weight."

    return [
        mechanism_line,
        weight_line,
        f"Benefit scale B+={b_plus_scale:.2f}; cost scale C={c_scale:.2f}.",
        "Each square is one individual.",
        "Blue is low cooperation; orange is high.",
        "Fitter local parents are copied more often.",
    ]


def main() -> None:
    run_live_grid_view(
        model_class=InteractionKernelModel,
        model_config=model_config,
        window_caption="Interaction Kernel Live Grid",
        header_title="Interaction Kernel: Live Trait Grid",
        explanation_builder=_build_explanation_lines,
    )


if __name__ == "__main__":
    main()
