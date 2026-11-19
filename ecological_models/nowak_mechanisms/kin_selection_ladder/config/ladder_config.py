"""Parameters for ladder steps 0-1 (README pre-registration, commit 4c5fefb). No command-line parameters."""
from __future__ import annotations

from typing import Any

from moran_models.nowak_mechanisms.kin_selection.config.kin_selection_config import config as MORAN_CONFIG

STEPS = 1000
SEEDS = list(range(20))
SUCCESS_FINAL_MEAN_TRAIT = 0.60
RARE = {"initial_trait_mean": 0.05, "initial_trait_stddev": 0.02}
COMMON = {"initial_trait_mean": 0.9, "initial_trait_stddev": 0.05}
UNIFORM = {"kin_weight_same_lineage": 0.5, "kin_weight_other_lineage": 0.5}
BELOW_B = 0.05
LOW_B = 0.6                      # conditional lower-benefit diagnostic
NOBIAS_TRIGGER = 8               # S-nobias successes at B = 1.0 that trigger the B = 0.6 scoring

# arm -> (mechanism kwargs, config updates)
STEP0_ARMS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "A-kin": ({"self_in_routing": True, "kin": "label"}, {**RARE}),
    "A-nobias": ({"self_in_routing": True, "kin": "label"}, {**RARE, **UNIFORM}),
    "A-below": ({"self_in_routing": True, "kin": "label"}, {**COMMON, "B_plus_scale": BELOW_B}),
    "S-kin": ({"self_in_routing": False, "kin": "label"}, {**RARE}),
    "S-nobias": ({"self_in_routing": False, "kin": "label"}, {**RARE, **UNIFORM}),
    "S-below": ({"self_in_routing": False, "kin": "label"}, {**COMMON, "B_plus_scale": BELOW_B}),
}
STEP0_LOW_ARMS = {
    "S-kin-0.6": ({"self_in_routing": False, "kin": "label"}, {**RARE, "B_plus_scale": LOW_B}),
    "S-nobias-0.6": ({"self_in_routing": False, "kin": "label"}, {**RARE, **UNIFORM, "B_plus_scale": LOW_B}),
}

# Step 1 calibration: neutral (h = 0) runs.
CAL_MU = [0.001, 0.003, 0.01, 0.03]
CAL_SEEDS = list(range(5))
CAL_SAMPLE_STEPS = list(range(100, 1001, 50))
CAL_RANDOM_PAIRS = 2000
CAL_PAIR_SEED = 12345
NEUTRAL = {"initial_trait_mean": 0.0, "initial_trait_stddev": 0.0, "mutation_rate": 0.0}  # h stays 0: equal fitness
ATTEMPT2_MU_DIVISOR = 10

WORKERS = 8
DATA_DIR = "ecological_models/nowak_mechanisms/kin_selection_ladder/data"


def run_config(seed: int, updates: dict[str, Any], steps: int = STEPS) -> dict[str, Any]:
    cfg = dict(MORAN_CONFIG)
    cfg.update(updates)
    cfg.update({"random_seed": seed, "simulation_steps": steps, "summary_interval_steps": 10**9, "write_log": False})
    return cfg

# Step 0c (half-step, pre-registered 1252e8f): self at its own routing weight, 3000 steps.
STEPS_0C = 3000
W_SELF_ATTEMPT1 = 0.2
W_SELF_ATTEMPT2 = 0.5
FISHER_ALPHA_ATTEMPT2 = 0.025
STEP0C_ARMS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "H-kin": ({"self_in_routing": True, "kin": "label", "self_weight": W_SELF_ATTEMPT1}, {**RARE}),
    "H-nobias": ({"self_in_routing": True, "kin": "label"}, {**RARE, **UNIFORM}),
    "H-below": ({"self_in_routing": True, "kin": "label", "self_weight": W_SELF_ATTEMPT1},
                {**COMMON, "B_plus_scale": BELOW_B}),
    "A-kin-3k": ({"self_in_routing": True, "kin": "label"}, {**RARE}),
}
STEP0C_ATTEMPT2_ARMS = {
    "H2-kin": ({"self_in_routing": True, "kin": "label", "self_weight": W_SELF_ATTEMPT2}, {**RARE}),
    "H2-below": ({"self_in_routing": True, "kin": "label", "self_weight": W_SELF_ATTEMPT2},
                 {**COMMON, "B_plus_scale": BELOW_B}),
}

# Step 0d (pre-registered 697928d): local versus global-competitor replacement, uniform routing, 3000 steps.
SAMPLE_STEPS_0D = list(range(500, 3001, 500))
SUSTAINED_FROM = 2500
STEP0D_ARMS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "V-local": ({"self_in_routing": True, "kin": "label"}, {**RARE, **UNIFORM}),
    "V-global": ({"self_in_routing": True, "kin": "label", "replacement": "global"}, {**RARE, **UNIFORM}),
    "V-below": ({"self_in_routing": True, "kin": "label"}, {**COMMON, **UNIFORM, "B_plus_scale": BELOW_B}),
    "V-null": ({"self_in_routing": True, "kin": "label", "replacement": "global"},
               {**RARE, **UNIFORM, "B_plus_scale": 0.0, "C_scale": 0.0}),
}
