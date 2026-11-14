#!/usr/bin/env python3
"""
Parameters for `stag_hunt_sharing.py` (README.md).

Edit the dicts directly. `MODEL` is one run's world; `SWEEP` lists the values
the sweep crosses, each overriding the key of the same name in `MODEL`;
`RUN` sets seeds, workers and outputs.
"""

from __future__ import annotations

from typing import Any

MODEL: dict[str, Any] = {
    # Square torus, one hunter per cell.
    "grid_size": 64,
    "generations": 3000,
    # Share of stag hunters at the start, placed at random.
    "initial_stag_fraction": 0.05,
    # Hare: a reliable solo payoff, never shared.
    "hare_payoff": 1.0,
    # Stag: needs at least one stag-hunting partner among the 4 nearest
    # neighbours; then caught with this chance.
    "stag_success_probability": 0.8,
    # Expected stag payoff with a partner (success chance x stag payoff),
    # relative to the hare payoff. The stag payoff is derived from it.
    "stag_to_hare_ratio": 1.25,
    # Sharing: this fraction of a caught stag goes to the other hunters
    # within sharing_radius (Chebyshev distance), split evenly, whatever
    # they hunt; "global": everyone else. 0: no sharing.
    "share_fraction": 0.5,
    "sharing_radius": 1,
    # Who receives the shares: "all" hunters within the radius, or only the
    # other "stag" hunters there (caught one or not; a catcher with none
    # near keeps its share).
    "share_target": "all",
    # "linear": fitness = baseline + food. "diminishing": fitness =
    # baseline + 1 - exp(-food / food_scale), so a failed hunt costs more
    # than a lucky one gains (the insurance case).
    "fitness_shape": "diminishing",
    "fitness_baseline": 0.1,
    "food_scale": 1.0,
    # "local": each cell's next hunter is the offspring of a parent drawn
    # from the cell and its 8 neighbours, by fitness (offspring settle near
    # their parents, so neighbours tend to be kin). An integer r: the parent
    # is drawn from the cells within Chebyshev distance r ("local" is 1;
    # wider competition, weaker kin clusters). "global": the parent is
    # drawn from the whole population, by fitness.
    "dispersal": "local",
    # Chance that an offspring switches strategy.
    "mutation_probability": 0.001,
    # Generations at the end averaged for the outcome.
    "measure_last": 1000,
}

SWEEP: dict[str, list[Any]] = {
    "share_fraction": [0.0, 0.25, 0.5, 0.75],
    "sharing_radius": [1, 2, 4, "global"],
    "stag_to_hare_ratio": [0.8, 1.0, 1.25, 1.5, 2.0],
    "fitness_shape": ["linear", "diminishing"],
    "dispersal": ["local", "global"],
    "initial_stag_fraction": [0.05, 0.5],
}

# Targeted sharing and the dispersal scale (README, "Targeted sharing").
SWEEP_TARGETED: dict[str, list[Any]] = {
    "share_fraction": [0.0, 0.25, 0.5, 0.75],
    "share_target": ["all", "stag"],
    "sharing_radius": [1, 4],
    "stag_to_hare_ratio": [0.8, 1.0, 1.25, 1.5, 2.0],
    "fitness_shape": ["linear", "diminishing"],
    "dispersal": [1, 2, 4, "global"],
    "initial_stag_fraction": [0.5],
}

# Targeted sharing with riskier big game (README, "Riskier stags"): the
# deer world's adult hunts rarely succeed.
SWEEP_TARGETED_LOWQ: dict[str, list[Any]] = {
    "share_fraction": [0.0, 0.25, 0.5, 0.75],
    "share_target": ["all", "stag"],
    "stag_success_probability": [0.2, 0.5],
    "stag_to_hare_ratio": [1.0, 1.5, 2.0, 3.0],
    "fitness_shape": ["linear", "diminishing"],
    "dispersal": [1, "global"],
    "initial_stag_fraction": [0.5],
}

# The payoff threshold at the deer world's lifetime q (README, "Payoff
# threshold"): the smallest stag-to-hare ratio at which targeted sharing helps.
SWEEP_THRESHOLD: dict[str, list[Any]] = {
    "share_fraction": [0.0, 0.5, 0.75],
    "share_target": ["stag"],
    "stag_success_probability": [0.3, 0.45, 0.6],
    "stag_to_hare_ratio": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.75],
    "fitness_shape": ["linear", "diminishing"],
    "dispersal": [1, "global"],
    "initial_stag_fraction": [0.5],
}

RUN: dict[str, Any] = {
    "seeds": [1, 2, 3],
    "workers": 16,
    "results_csv": "ecological_models/stag_hunt_sharing/data/sweep.csv",
    "figure": "ecological_models/stag_hunt_sharing/images/sweep.png",
    "targeted_csv": "ecological_models/stag_hunt_sharing/data/sweep_targeted.csv",
    "targeted_figure": "ecological_models/stag_hunt_sharing/images/targeted.png",
    "targeted_lowq_csv": "ecological_models/stag_hunt_sharing/data/sweep_targeted_lowq.csv",
    "threshold_csv": "ecological_models/stag_hunt_sharing/data/sweep_threshold.csv",
    # Fewer workers for this sweep: it shares the CPU with long training runs.
    "threshold_workers": 8,
}

# Selection between groups (groups.py; README, "Selection between groups";
# PredPreyGrass eco_evolutionary_deer_stag_hunt DESIGN_4.md step 0, fixed
# there before any code: 14 groups on a ring, no migration, interval 10,
# diminishing fitness, 20 seeds 0-19, outcome = mean stag share over the last
# 100 generations).
GROUPS: dict[str, Any] = {
    "n_groups": 14,
    "group_size": 16,  # each group a 16 x 16 torus (3584 hunters in all)
    "generations": 3000,
    "measure_last": 100,
    "interval": 10,
    "seeds": list(range(20)),
    "sweep": {
        "fitness_shape": ["diminishing"],
        "stag_success_probability": [0.3, 0.45, 0.6],
        "stag_to_hare_ratio": [1.0, 1.1, 1.2, 1.3, 1.5, 1.75],
        "initial_stag_fraction": [0.05, 0.5],
    },
    "workers": 24,
    "results_csv": "ecological_models/stag_hunt_sharing/data/sweep_groups.csv",
}
