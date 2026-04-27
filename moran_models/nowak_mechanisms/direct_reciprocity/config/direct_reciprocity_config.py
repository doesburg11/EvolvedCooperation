"""Active runtime parameters for the direct-reciprocity model."""

from __future__ import annotations

from moran_models.interaction_kernel.config.interaction_kernel_config import DEFAULT_CONFIG


config = dict(DEFAULT_CONFIG)
config.update(
    {
        "positive_kernel_mode": "uniform",
        "negative_kernel_mode": "none",
        "B_plus_scale": 1.0,
        "B_minus_scale": 0.0,
        "C_scale": 0.2,
        "encounter_memory_length": 1,
        "direct_reciprocity_mode": "received_help_memory",
        "memory_initial": 0.0,
        "memory_decay": 0.35,
        "memory_baseline_expression": 0.35,
        "memory_expression_gain": 0.85,
        "reset_memory_on_mutation": False,
        "log_output_path": "moran_models/nowak_mechanisms/direct_reciprocity/data/latest_run.json",
    }
)
