#!/usr/bin/env python3
"""
Frozen configuration for the GitHub Pages spatial-altruism demo.

This module preserves the parameter set used by the website replay as of
2026-04-06. Continue tuning the live model in `altruism_config.py`; update
this file only when you intentionally want the website experiment to change.
"""

from __future__ import annotations

from typing import Any


config: dict[str, Any] = {
    "width": 51,
    "height": 51,
    "torus": True,
    "model_variant": "steady_state",
    "altruistic_probability": 0.39,
    "selfish_probability": 0.39,
    "benefit_from_altruism": 0.468,
    "cost_of_altruism": 0.156,
    "disease": 0.213,
    "harshness": 0.96,
    "uniform_culling_interval": 50,
    "uniform_culling_fraction": 0.5,
    "compact_swath_interval": 50,
    "compact_swath_fraction": 0.5,
    "seed": 1,
    "demo_steps": 400,
    "demo_plot_enabled": False,
    "demo_plot_interval": 0.01,
    "ui_window_width": 600,
    "ui_window_height": 600,
    "ui_plot_height": 300,
    "ui_side_panel_width": 380,
    "ui_frames_per_second": 30,
    "ui_history_visible_default": True,
}
