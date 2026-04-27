"""Active runtime parameters for the indirect-reciprocity model."""

from __future__ import annotations

from moran_models.interaction_kernel.config.interaction_kernel_config import DEFAULT_CONFIG


config = dict(DEFAULT_CONFIG)
config.update(
    {
        "positive_kernel_mode": "reputation_weighted",
        "negative_kernel_mode": "none",
        "B_plus_scale": 1.0,
        "B_minus_scale": 0.0,
        "C_scale": 0.2,
        "reputation_default": 0.5,
        "reputation_observation_weight": 0.35,
        "reputation_kernel_bias": 0.10,
        "reputation_kernel_exponent": 1.0,
        "indirect_reciprocity_mode": "public_reputation_weighted",
        "log_output_path": "moran_models/nowak_mechanisms/indirect_reciprocity/data/latest_run.json",
    }
)
