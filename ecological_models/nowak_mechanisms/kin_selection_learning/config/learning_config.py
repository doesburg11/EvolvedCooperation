"""Parameters for kin selection with learned helping (see ../README.md, the pre-registered design).

Runtime modules take no command-line parameters; everything is set here.
"""
from __future__ import annotations

from typing import Any

VERSIONS = ("A", "B", "C")  # A genetic, B selfish learner, C kin-regard learner

LEARNING: dict[str, Any] = {
    "initial_effort": 0.05,       # learned effort at maturity, not inherited
    "exploration_stddev": 0.1,    # action noise sigma
    "baseline_rate": 0.1,         # running reward baseline step size
    "juvenile_energy_value": 4.5,  # V: child_energy 3.5 + reproduction_energy_cost 1.0
    "alpha": None,                # learning rate, fixed by utils/calibrate_alpha.py before step 1
}

# Step 0: cost calibration, version A only, existing rare-helper start.
STEP0_COSTS = [0.03, 0.1, 0.2, 0.3, 0.45, 0.6]
STEP0_SEEDS = list(range(20))
STEP0_BAND = (0.30, 0.70)
STEP0_TARGET = 0.50

# Learning-rate calibration (stand-alone, no outcome data).
ALPHA_CANDIDATES = [0.1, 0.2, 0.3, 0.5, 1.0]
ALPHA_STEPS = 30
ALPHA_TOY_CARERS = 1       # one learner: measures learning speed, not free riding
ALPHA_TOY_JUVENILES = 2
ALPHA_TOLERANCE = 0.1      # k high: within this of the toy's reward-maximizing effort
ALPHA_LOW_EFFORT = 0.1     # k = 0, starting at 0.5: below this

# Step 1.
STEP1_SEEDS = list(range(100, 140))
STEP1_BASELINE_STEP = 20
STEP1_MIN_EXPRESSED_INCREASE = 0.015
STEP1_MIN_FINAL_POPULATION = 100

STARTS: dict[str, dict[str, Any]] = {
    "rare": {},  # the existing rare-founder start
    "weak": {"rare_helper_founder_probability": 0.0},
}

WORKERS = 8
DATA_DIR = "ecological_models/nowak_mechanisms/kin_selection_learning/data"
