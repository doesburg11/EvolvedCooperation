#!/usr/bin/env python3
"""Network-reciprocity Moran model built on the shared interaction core."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from moran_models.interaction_kernel.core.engine import MoranInteractionEngine
from moran_models.interaction_kernel.core.mechanisms import NetworkReciprocityMechanism

from .config.network_reciprocity_config import config


class NetworkReciprocityModel(MoranInteractionEngine):
    """Named network-reciprocity model using local graph structure."""

    def __init__(self, cfg: dict[str, Any]):
        super().__init__(cfg, NetworkReciprocityMechanism())


def _write_log(payload: dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_simulation(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime_cfg = dict(config if cfg is None else cfg)
    model = NetworkReciprocityModel(runtime_cfg)
    payload = model.run()

    if bool(runtime_cfg.get("write_log", True)):
        _write_log(payload, str(runtime_cfg["log_output_path"]))
        print(f"[network_reciprocity] wrote log -> {runtime_cfg['log_output_path']}")
    return payload


if __name__ == "__main__":
    run_simulation()
