"""Parameters for the bonus-care kin-selection test (README pre-registration, commit 4b300ed).

Runtime modules take no command-line parameters; everything is set here. Thresholds shared with the floor test
(population >= 100, spread rule, cohort >= 50, >= 30 analysable runs, 10,000 bootstrap draws) come from the floor
config, whose values the pre-registration reuses unchanged.
"""
from __future__ import annotations

from typing import Any

COST = 0.016                         # care_cost_per_unit: full effort (capacity 2.5) costs 0.04 energy per step
STEPS = 800
WINDOW = (761, 800)                  # persistence: population >= 100 at every step in this window

COMMON: dict[str, Any] = {"female_reproduction_probability": 0.9}   # births limited by energy, not by chance

REARING: dict[str, dict[str, Any]] = {
    "K": {},                                                        # kin rearing, no dispersal
    "U": {"foster_to_nonparent_group_probability": 1.0, "offspring_dispersal_probability": 0.0,
          "matured_dispersal_probability": 0.0},                    # fostering only
}

# Step -1 (amendment 1): allele mutation rate, no helpers, U rearing, one cell that sits at the cap.
STEPM1_MU = [0.005, 0.01, 0.02, 0.05]
STEPM1_CELL = (0.5, 0.9)              # (reproduction_energy_cost, p0)
STEPM1_SEEDS = list(range(5))
STEPM1_SAMPLE_STEPS = list(range(700, 801, 20))
STEPM1_PAIRS = 200
STEPM1_MAX_BACKGROUND = 0.03

# Step 0: life-history grid with a no-helper control.
STEP0_REPRO_COSTS = [1.0, 0.7, 0.5, 0.35]     # reproduction_energy_cost
STEP0_P0 = [0.65, 0.7, 0.75, 0.8, 0.85, 0.9]  # base_juvenile_survival_probability
STEP0_SEEDS = list(range(20))
STEP0_REARING = ("K", "U")
NO_HELPER = {"initial_helping_trait_min": 0.0, "initial_helping_trait_max": 0.0,
             "rare_helper_founder_probability": 0.0, "helping_mutation_probability": 0.0}

# Cost probe in the chosen cell: half the founders at h 0.65, half at 0, no mutation; care costs but does not count.
PROBE_SEEDS = list(range(20))
PROBE_FOUNDERS = {"initial_helping_trait_min": 0.0, "initial_helping_trait_max": 0.0,
                  "rare_helper_founder_probability": 0.5, "rare_helper_trait_value": 0.65,
                  "helping_mutation_probability": 0.0}
PROBE_MIN_KAPPA = 0.05
FEMALE_BIRTH_STEPS = (50, 735)       # matured females whose reproductive life ends inside the run (probe, fecundity)

# Main test. Each arm: (rearing, helping acts).
MAIN_SEEDS = list(range(400, 440))
ARMS: dict[str, tuple[str, bool]] = {"K": ("K", True), "U": ("U", True), "K-N": ("K", False), "U-N": ("U", False)}
COHORT_BIRTH_STEPS = (50, 735)
H0B_MAX_U_RELATEDNESS = 0.05
H0B_MAX_FRACTION_OF_K = 1 / 3
HAMILTON_R = 0.25                    # theory screen's r for the recorded best-case margin

WORKERS = 8
DATA_DIR = "ecological_models/nowak_mechanisms/kin_selection/bonus_care/data"
