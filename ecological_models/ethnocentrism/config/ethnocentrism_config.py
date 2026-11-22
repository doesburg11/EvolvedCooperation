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


def run_config(experiment: str) -> dict[str, Any]:
    return {**BASE, **EXPERIMENTS[experiment]}
