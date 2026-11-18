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

# Confirmation test: persistence (README, pre-registered 2026-11-18). Each arm: (version, learning overrides, starts).
CONFIRM_SEEDS = list(range(200, 240))
CONFIRM_ALPHA = 0.2
CONFIRM_ARMS: dict[str, tuple[str, dict[str, Any], tuple[str, ...]]] = {
    "A": ("A", {}, ("rare", "weak")),
    "B": ("B", {}, ("rare", "weak")),
    "C": ("C", {}, ("rare", "weak")),
    "C-nolearn": ("C", {"alpha": 0.0}, ("rare", "weak")),
    "C-frozen": ("C", {"frozen_kin_regard": True}, ("weak",)),
    **{f"D{e:.2f}": ("B", {"alpha": 0.0, "initial_effort": e, "exploration_stddev": 0.0}, ("weak",))
       for e in (0.05, 0.07, 0.10, 0.15, 0.20, 0.30)},
    **{f"N{e:.2f}": ("B", {"alpha": 0.0, "initial_effort": e}, ("weak",)) for e in (0.10, 0.15, 0.20)},
}
CONFIRM_CONSTANT_ARMS = [a for a in CONFIRM_ARMS if a[0] in "DN"] + ["C-nolearn"]  # C-nolearn is N0.05
CONFIRM_CONSTANT_EFFORT = {**{a: float(a[1:]) for a in CONFIRM_ARMS if a[0] in "DN"}, "C-nolearn": 0.05}
CONFIRM_STEPS = 220
CONFIRM_WINDOW = (181, 220)        # persistence: population >= CONFIRM_MIN_POPULATION at every step in this window
CONFIRM_MIN_POPULATION = 100
CONFIRM_COST_STEPS = (1, 60)       # cost per carer step over these steps
CONFIRM_GRID = (0.05, 0.30)
CONFIRM_LONG_ARMS = ("A", "B", "C", "C-nolearn")
CONFIRM_LONG_STEPS = 440
CONFIRM_LONG_WINDOW = (401, 440)
CONFIRM_BOOTSTRAP = 10000
