"""Parameters for the survival-floor kin-selection test (README, pre-registered 2026-11-18).

Runtime modules take no command-line parameters; everything is set here.
"""
from __future__ import annotations

from typing import Any

COST = 0.03                         # care_cost_per_unit
STEPS = 220
WINDOW = (181, 220)                 # persistence: population >= MIN_POPULATION at every step in this window
MIN_POPULATION = 100
SPREAD_MIN_TRAIT_INCREASE = 0.015   # base proof rule, without its Hamilton-margin proxy
SPREAD_MIN_FREQUENCY_INCREASE = 0.02

REARING: dict[str, dict[str, Any]] = {
    "K": {},                                                        # base default: kin rearing, no dispersal
    "U": {"foster_to_nonparent_group_probability": 1.0, "offspring_dispersal_probability": 0.0,
          "matured_dispersal_probability": 0.0},                    # fostering only
    "U-disp": {"foster_to_nonparent_group_probability": 1.0, "offspring_dispersal_probability": 0.0,
               "matured_dispersal_probability": 0.85},              # base unrelated_rearing_groups settings
}

# Step 0: floor calibration with a no-helper control.
STEP0_FLOORS = [0.05, 0.1, 0.15, 0.2, 0.3, 0.4]
STEP0_SEEDS = list(range(20))
STEP0_REARING = ("K", "U")
NO_HELPER = {"initial_helping_trait_min": 0.0, "initial_helping_trait_max": 0.0,
             "rare_helper_founder_probability": 0.0, "helping_mutation_probability": 0.0}

# Main test. Each arm: (rearing, uses floor, neutral).
MAIN_SEEDS = list(range(300, 340))
ARMS: dict[str, tuple[str, bool, bool]] = {
    "K": ("K", True, False),
    "U": ("U", True, False),
    "K-N": ("K", True, True),
    "U-N": ("U", True, True),
    "K0": ("K", False, False),
    "U-disp0": ("U-disp", False, False),
    "U-disp": ("U-disp", True, False),
}
COHORT_BIRTH_STEPS = (20, 144)
MIN_COHORT = 50
MIN_ANALYSABLE_RUNS = 30
BOOTSTRAP = 10000

WORKERS = 8
DATA_DIR = "ecological_models/nowak_mechanisms/kin_selection_floor_control/data"
