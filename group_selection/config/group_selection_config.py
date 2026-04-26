"""Active runtime parameters for the group-selection model."""

from __future__ import annotations

from interaction_kernel.config.interaction_kernel_config import DEFAULT_CONFIG


config = dict(DEFAULT_CONFIG)
config.update(
    {
        "positive_kernel_mode": "uniform",
        "negative_kernel_mode": "none",
        "B_plus_scale": 1.0,
        "B_minus_scale": 0.0,
        "C_scale": 0.2,
        "group_count": 8,
        "group_selection_interval": 25,
        "group_selection_mode": "copy_best_group_into_worst_group",
        "log_output_path": "group_selection/data/latest_run.json",
    }
)
