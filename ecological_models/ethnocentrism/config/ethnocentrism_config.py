"""Parameters for the Python port of the NetLogo Ethnocentrism model (Wilensky 2003, after Hammond & Axelrod).

Single source of truth; no command-line parameters. BASE matches the NetLogo slider defaults and
"Experiment 104"; EXPERIMENTS lists the one-parameter changes of the NetLogo BehaviorSpace experiments 105-113.
"""
from __future__ import annotations

from typing import Any

BASE: dict[str, Any] = {
    "width": 51,                      # NetLogo max-pxcor 50, min-pxcor 0 -> 51 columns, torus
    "height": 51,
    "ticks": 2000,
    "setup": "empty",                 # "empty" (setup-empty) or "full" (setup-full)
    "immigrants_per_day": 1,
    "immigrant_chance_cooperate_with_same": 0.5,
    "immigrant_chance_cooperate_with_different": 0.5,
    "initial_ptr": 0.12,
    "cost_of_giving": 0.01,
    "gain_of_receiving": 0.03,
    "mutation_rate": 0.005,
    "death_rate": 0.10,
    "n_colors": 4,
    "colour_inheritance": "inherited",  # "inherited" (NetLogo) or "random": child colour uniform, independent of parent
    "dispersal": 0.0,                   # probability a child is placed in a random empty cell anywhere (0 = NetLogo)
    "lineage_sample_every": 100,      # pedigree metrics on all neighbour pairs every this many ticks (and at the end)
}

# NetLogo experiment name -> changes to BASE (from the model's <experiments> block).
EXPERIMENTS: dict[str, dict[str, Any]] = {
    "104": {},
    "105": {"width": 101, "height": 101},
    "106": {"ticks": 4000},
    "107": {"ticks": 1000},
    "108": {"width": 26, "height": 26},
    "109": {"cost_of_giving": 0.02},
    "110": {"mutation_rate": 0.0025},
    "111": {"mutation_rate": 0.01},
    "113": {"immigrants_per_day": 2},
}

SEEDS = list(range(30))
WORKERS = 24
NETLOGO_RESULTS_DIR = "/home/doesburg/simulation_results/hammond_axelrod_ethnocentrism"   # netlogo_exp<NNN>/table.csv
DATA_DIR = "ecological_models/ethnocentrism/data"

# NetLogo reporters compared with the port (pre-registered in README.md).
CHECK_METRICS = ["cc-percent", "cd-percent", "dc-percent", "dd-percent",
                 "last100coop-percent", "last100consist-ethno-percent",
                 "last100coopown-percent", "last100defother-percent", "last100meetown-percent"]
CHECK_ALPHA = 0.001                   # flag a metric/experiment if Welch p below this (fixed cutoff; 0.05/81 = 0.0006)
CHECK_MAX_ABS_DIFF = 0.05             # ... and the mean difference is larger than 5 percentage points
NETLOGO_RUNS = 10                     # runs per NetLogo experiment table
EXPECT_MIN_SEEDS = 27                 # lineage expectations E1/E2: met in at least this many of the 30 seeds


# Random-colour experiment (pre-registered in README.md, 2026-11-22): Experiment 104 with and without the
# colour-descent link, same seeds, run in the same batch.
RANDOM_COLOUR_BASE = "104"
RANDOM_COLOUR_CONDITIONS: dict[str, dict[str, Any]] = {"inherited": {"colour_inheritance": "inherited"},
                                                       "random": {"colour_inheritance": "random"}}
# independent RNG streams per arm; the inherited seeds are those of the committed port run (exact replay check)
RANDOM_COLOUR_SEEDS: dict[str, list[int]] = {"inherited": list(range(30)), "random": list(range(1000, 1030))}
RANDOM_COLOUR_DIR = "ecological_models/ethnocentrism/data/random_colour"
RC_MIN_DROP = 0.10                    # H1: ethnocentric share at least 10 points lower under random colour ...
RC_ALPHA = 0.001                      # ... and two-sided Welch p below this
RC_MANIP_MAX_MEAN_GAP = 0.05          # manipulation check: |mean signed founder-share gap| below this ...
RC_MANIP_MAX_MEAN_ABS_GAP = 0.10      # ... and mean of per-seed |gap| below this (cancelling gaps cannot pass)

# Lower-viscosity experiment (pre-registered in README.md, 2026-11-22): Experiment 104 x dispersal x colour rule.
DISPERSAL_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]
VISC_DIR = "ecological_models/ethnocentrism/data/viscosity"
VISC_SEED_OFFSET = {"inherited": 0, "random": 1000}   # seeds: 10000 * level index + offset + 0..29 (level 0 = earlier runs)
VISC_N_SEEDS = 30
VISC_MIN_FOUNDER_DROP = 0.20          # manipulation check: neighbour same-founder share falls by at least this, d 0 -> 1
VISC_H1_MIN_DROP = 0.20               # H1: random colour, cooperation at d=1 at least 20 points below d=0
VISC_H2_MIN_DIFF = 0.10               # H2: d=1, cooperation inherited minus random at least 10 points
VISC_ALPHA = 0.001                    # two-sided Welch p below this


def run_config(experiment: str) -> dict[str, Any]:
    return {**BASE, **EXPERIMENTS[experiment]}
