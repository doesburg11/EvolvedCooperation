"""Runtime parameters for the asynchronous well-mixed direct-reciprocity model."""

from __future__ import annotations

from typing import Any

from .direct_reciprocity_well_mixed_config import config as base_config


config: dict[str, Any] = dict(base_config)
config.update(
    {
        # One-birth/one-death replacement needs a longer horizon than the
        # synchronous model because each step changes at most one site.
        "simulation_steps": 5000,
        "summary_interval_steps": 500,
        # Keep the direct-reciprocity test condition fixed: persistent partners
        # create high re-encounter probability without spatial clustering.
        "partner_persistence_probability": 0.9,
        # Weaker selection prevents a single early ALLD advantage from sweeping
        # the population before reciprocal pair histories can accumulate.
        "selection_temperature": 1.0,
        "log_output_path": (
            "moran_models/nowak_mechanisms/direct_reciprocity/well_mixed/"
            "data/latest_async_run.json"
        ),
    }
)
