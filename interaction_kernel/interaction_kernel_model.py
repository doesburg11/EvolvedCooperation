#!/usr/bin/env python3
"""General interaction-kernel simulation module.

This package remains the canonical config-driven interaction-kernel entrypoint.
The reusable Moran engine now lives in ``interaction_kernel.core`` so named
mechanism packages can share the same selection, space, and metrics code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config.interaction_kernel_config import config
from .core.engine import MoranInteractionEngine
from .core.mechanisms import ConfigDrivenKernelMechanism


def _resolve_runtime_config(raw_cfg: dict[str, Any]) -> dict[str, Any]:
    """Resolve runtime config with backwards-compatible aliases.

    Canonical keys are theory-aligned:
    - B_plus_scale
    - B_minus_scale
    - C_scale

    Legacy aliases supported:
    - positive_output_scale -> B_plus_scale
    - negative_output_scale -> B_minus_scale
    - trait_cost_scale -> C_scale
    """
    cfg = dict(raw_cfg)

    alias_to_canonical = {
        "positive_output_scale": "B_plus_scale",
        "negative_output_scale": "B_minus_scale",
        "trait_cost_scale": "C_scale",
    }
    for legacy_key, canonical_key in alias_to_canonical.items():
        if canonical_key not in cfg and legacy_key in cfg:
            cfg[canonical_key] = cfg[legacy_key]

    required = ("B_plus_scale", "B_minus_scale", "C_scale")
    missing = [key for key in required if key not in cfg]
    if missing:
        raise KeyError(f"Missing required config keys: {missing}")
    return cfg


class InteractionKernelModel(MoranInteractionEngine):
    """Reusable interaction-kernel engine with theory-aligned symbols.

    State variables:
    - h: trait vector in [0, 1]
    - lineage: inherited identity label per site
    """

    def __init__(self, cfg: dict[str, Any]):
        super().__init__(cfg, ConfigDrivenKernelMechanism())


def _write_log(payload: dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_simulation(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime_cfg = _resolve_runtime_config(config if cfg is None else cfg)
    model = InteractionKernelModel(runtime_cfg)
    payload = model.run()

    if bool(runtime_cfg.get("write_log", True)):
        _write_log(payload, str(runtime_cfg["log_output_path"]))
        print(f"[interaction_kernel] wrote log -> {runtime_cfg['log_output_path']}")
    return payload


if __name__ == "__main__":
    run_simulation()
