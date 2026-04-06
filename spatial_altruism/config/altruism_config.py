#!/usr/bin/env python3
"""
Active runtime parameters for `altruism_model.py`.

Edit the `config` dict directly. These keys are the canonical runtime
configuration for the spatial altruism model and its interactive UI.
"""

from __future__ import annotations

from typing import Any, Mapping

DEFAULT_CONFIG: dict[str, Any] = {
    # World geometry and altruism dynamics.
    "width": 51,
    "height": 51,
    "torus": True,
    "altruistic_probability": 0.39,
    "selfish_probability": 0.39,
    "benefit_from_altruism": 0.468,
    "cost_of_altruism": 0.156,
    "disease": 0.213,
    "harshness": 0.96,
    "seed": None,
    # Default non-UI demo run.
    "demo_steps": 400,
    "demo_plot_enabled": True,
    "demo_plot_interval": 0.01,
    # Interactive UI layout.
    "ui_window_width": 600,
    "ui_window_height": 600,
    "ui_plot_height": 300,
    "ui_side_panel_width": 380,
    "ui_frames_per_second": 30,
    "ui_history_visible_default": True,
}


def resolve_config(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """
    Merge overrides onto the canonical default config.

    Only canonical keys are accepted. Unknown keys raise KeyError.
    """

    resolved = dict(DEFAULT_CONFIG)
    if overrides is None:
        return resolved

    for raw_key, value in overrides.items():
        if raw_key not in DEFAULT_CONFIG:
            raise KeyError(f"Unknown config key '{raw_key}'")
        resolved[raw_key] = value
    return resolved


config = dict(DEFAULT_CONFIG)
