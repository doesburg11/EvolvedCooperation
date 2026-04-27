"""Active runtime parameters for the kin-selection wrapper."""

from __future__ import annotations

from moran_models.interaction_kernel.config.interaction_kernel_config import DEFAULT_CONFIG


config = dict(DEFAULT_CONFIG)
config.update(
    {
        "positive_kernel_mode": "kin_weighted",
        "negative_kernel_mode": "none",
        "B_plus_scale": 1.0,
        "B_minus_scale": 0.0,
        "C_scale": 0.2,
        "kin_weight_same_lineage": 0.8,
        "kin_weight_other_lineage": 0.2,
        "log_output_path": "moran_models/nowak_mechanisms/kin_selection/data/latest_run.json",
    }
)
