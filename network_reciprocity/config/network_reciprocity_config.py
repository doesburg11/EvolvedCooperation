"""Active runtime parameters for the network-reciprocity wrapper."""

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
        "initial_identity_count": 1,
        "log_output_path": "network_reciprocity/data/latest_run.json",
    }
)
