#!/usr/bin/env python3
"""
Spatial stag hunt with sharing of big game (README.md).

One hunter per cell of a square torus, each with an inherited strategy,
stag (1) or hare (0). Each generation:

1. Hunting. A hare hunter gets the hare payoff. A stag hunter with at least
   one stag-hunting partner among its 4 nearest neighbours catches a stag
   with stag_success_probability and gets the stag payoff; without a partner,
   nothing.
2. Sharing. Each caught stag gives share_fraction of its payoff to the other
   hunters within sharing_radius (Chebyshev distance; "global": everyone
   else), split evenly among them whatever they hunt; the catcher keeps the
   rest. Hares are never shared. With share_target "stag" the share goes
   only to the other stag hunters within the radius (whether or not they
   caught one): sharing among those who took part in big-game hunting.
3. Fitness from food, linear or with diminishing returns (config).
4. Reproduction. Every cell is refilled at once by the offspring of a parent
   drawn by fitness, from the cells within dispersal radius ("local" is
   radius 1: the cell and its 8 neighbours) or from the whole population
   ("global"); the offspring switches strategy with
   mutation_probability.

Run from the repository root (parameters in config/stag_hunt_sharing_config.py):

    ./.conda/bin/python -m ecological_models.stag_hunt_sharing.stag_hunt_sharing
"""

from __future__ import annotations

import csv
import itertools
from multiprocessing import Pool
from pathlib import Path
from typing import Any

import numpy as np

from .config.stag_hunt_sharing_config import MODEL, RUN, SWEEP

VON_NEUMANN = ((1, 0), (-1, 0), (0, 1), (0, -1))


def block(radius: int) -> tuple[tuple[int, int], ...]:
    """Offsets of the cells within Chebyshev distance radius, self included
    (radius 1: the same order as the original 3 x 3 block)."""
    return tuple((dy, dx) for dy in range(-radius, radius + 1) for dx in range(-radius, radius + 1))


def dispersal_radius(config: dict[str, Any]) -> int | None:
    """None for global dispersal, else the radius ("local" is 1)."""
    d = config["dispersal"]
    return None if d == "global" else 1 if d == "local" else d


def check(config: dict[str, Any]) -> None:
    """Fail fast on settings outside the model."""
    if set(config) != set(MODEL):
        raise ValueError(f"settings differ from MODEL: {sorted(set(config) ^ set(MODEL))}")
    n = config["grid_size"]
    if not isinstance(n, int) or n < 3:
        raise ValueError("grid_size must be an integer of at least 3")
    if not 0 <= config["share_fraction"] <= 1:
        raise ValueError("share_fraction must be in [0, 1]")
    radius = config["sharing_radius"]
    if radius != "global" and not (isinstance(radius, int) and not isinstance(radius, bool) and 1 <= radius and 2 * radius + 1 <= n):
        raise ValueError('sharing_radius must be "global" or an integer from 1 with 2 * radius + 1 <= grid_size')
    if not 0 < config["stag_success_probability"] <= 1 or config["stag_to_hare_ratio"] <= 0 or config["hare_payoff"] <= 0:
        raise ValueError("payoffs and the success probability must be positive (probability at most 1)")
    if config["fitness_shape"] not in ("linear", "diminishing") or config["share_target"] not in ("all", "stag"):
        raise ValueError("unknown fitness_shape or share_target")
    d = config["dispersal"]
    if d not in ("local", "global") and not (isinstance(d, int) and not isinstance(d, bool) and 1 <= d and 2 * d + 1 <= n):
        raise ValueError('dispersal must be "local", "global" or an integer radius from 1 with 2 * radius + 1 <= grid_size')
    if config["fitness_baseline"] <= 0 or config["food_scale"] <= 0:
        raise ValueError("fitness_baseline and food_scale must be positive")
    if not 0 <= config["mutation_probability"] <= 1 or not 0 <= config["initial_stag_fraction"] <= 1:
        raise ValueError("probabilities must be in [0, 1]")
    if not 1 <= config["measure_last"] <= config["generations"]:
        raise ValueError("measure_last must be from 1 to generations")


def stag_payoff(config: dict[str, Any]) -> float:
    return config["stag_to_hare_ratio"] * config["hare_payoff"] / config["stag_success_probability"]


def neighbour_sum(values: np.ndarray, radius: int) -> np.ndarray:
    """Sum over each cell's other cells within Chebyshev distance radius."""
    total = np.zeros_like(values, dtype=float)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy or dx:
                total += np.roll(values, (dy, dx), axis=(-2, -1))
    return total


def food(stag: np.ndarray, caught: np.ndarray, config: dict[str, Any]) -> np.ndarray:
    """Each hunter's food in one generation, given who hunts stag and who
    caught one."""
    value = stag_payoff(config)
    share = config["share_fraction"]
    kept = np.where(stag, caught * value * (1 - share), config["hare_payoff"])
    given = caught * value * share
    radius = config["sharing_radius"]
    if config["share_target"] == "stag":
        # each catcher splits its share evenly among the other stag hunters
        # within the radius; with none there, it keeps the share
        recipients = stag.sum() - stag if radius == "global" else neighbour_sum(stag, radius)
        per = np.divide(given, recipients, out=np.zeros_like(given), where=recipients > 0)
        kept = kept + np.where(recipients > 0, 0.0, given)
        reached = per.sum() - per if radius == "global" else neighbour_sum(per, radius)
        return kept + stag * reached
    if radius == "global":
        others = stag.size - 1
        received = (given.sum() - given) / others
    else:
        received = neighbour_sum(given, radius) / ((2 * radius + 1) ** 2 - 1)
    return kept + received


def fitness(meal: np.ndarray, config: dict[str, Any]) -> np.ndarray:
    if config["fitness_shape"] == "linear":
        return config["fitness_baseline"] + meal
    return config["fitness_baseline"] + 1 - np.exp(-meal / config["food_scale"])


def hunt(stag: np.ndarray, rng: np.random.Generator, config: dict[str, Any]) -> np.ndarray:
    """1 where a stag hunter with a partner among its 4 neighbours caught a
    stag."""
    partner = np.zeros_like(stag, dtype=bool)
    for shift in VON_NEUMANN:
        partner |= np.roll(stag, shift, axis=(-2, -1)).astype(bool)
    success = rng.random(stag.shape) < config["stag_success_probability"]
    return (stag.astype(bool) & partner & success).astype(float)


def reproduce(stag: np.ndarray, fit: np.ndarray, rng: np.random.Generator, config: dict[str, Any]) -> np.ndarray:
    """The next generation's strategies (module docstring, step 4)."""
    radius = dispersal_radius(config)
    if radius is None:
        parents = rng.choice(stag.size, size=stag.size, p=(fit / fit.sum()).ravel())
        child = stag.ravel()[parents].reshape(stag.shape)
    else:
        offsets = block(radius)
        weights = np.stack([np.roll(fit, shift, axis=(-2, -1)) for shift in offsets])
        strategies = np.stack([np.roll(stag, shift, axis=(-2, -1)) for shift in offsets])
        cumulative = np.cumsum(weights, axis=0)
        draw = rng.random(stag.shape) * cumulative[-1]
        pick = np.minimum((cumulative < draw).sum(axis=0), len(offsets) - 1)
        child = np.take_along_axis(strategies, pick[None], axis=0)[0]
    flip = rng.random(stag.shape) < config["mutation_probability"]
    return np.where(flip, 1 - child, child).astype(np.int8)


def run(config: dict[str, Any], seed: int) -> dict[str, float]:
    """One run: the mean stag fraction over the last measure_last
    generations, and the mean food of stag and of hare hunters there,
    each conditional on that strategy being present (a generation without
    it is skipped, so near extinction these food means rest on few
    generations and hunters)."""
    check(config)
    rng = np.random.default_rng(seed)
    n = config["grid_size"]
    stag = (rng.random((n, n)) < config["initial_stag_fraction"]).astype(np.int8)
    fractions, stag_food, hare_food = [], [], []
    start = config["generations"] - config["measure_last"]
    for generation in range(config["generations"]):
        caught = hunt(stag, rng, config)
        meal = food(stag, caught, config)
        if generation >= start:
            fractions.append(stag.mean())
            if stag.any():
                stag_food.append(meal[stag == 1].mean())
            if not stag.all():
                hare_food.append(meal[stag == 0].mean())
        stag = reproduce(stag, fitness(meal, config), rng, config)
    return {
        "stag_fraction": float(np.mean(fractions)),
        "stag_food": float(np.mean(stag_food)) if stag_food else float("nan"),
        "hare_food": float(np.mean(hare_food)) if hare_food else float("nan"),
    }


def conditions(sweep: dict[str, list[Any]] | None = None) -> list[dict[str, Any]]:
    """Every combination in a sweep (default SWEEP); with share_fraction 0
    the sharing radius and target play no part, so only their first listed
    values are kept."""
    sweep = SWEEP if sweep is None else sweep
    keys = list(sweep)
    out = []
    for values in itertools.product(*(sweep[k] for k in keys)):
        setting = dict(zip(keys, values))
        if setting.get("share_fraction") == 0 and any(
            k in sweep and setting[k] != sweep[k][0] for k in ("sharing_radius", "share_target")
        ):
            continue
        out.append(setting)
    return out


def _job(job: tuple[dict[str, Any], int]) -> dict[str, Any]:
    setting, seed = job
    return {**setting, "seed": seed, **run({**MODEL, **setting}, seed)}


def sweep(
    grid: dict[str, list[Any]] | None = None, results_csv: str | None = None, workers: int | None = None
) -> list[dict[str, Any]]:
    jobs = [(setting, seed) for setting in conditions(grid) for seed in RUN["seeds"]]
    with Pool(workers or RUN["workers"]) as pool:
        rows = pool.map(_job, jobs, chunksize=4)
    path = Path(results_csv or RUN["results_csv"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    import sys

    if sys.argv[1:] == ["targeted"]:
        from .config.stag_hunt_sharing_config import SWEEP_TARGETED
        from .utils.plot_sweep import plot_targeted

        rows = sweep(SWEEP_TARGETED, RUN["targeted_csv"])
        print(f"{len(rows)} runs written to {RUN['targeted_csv']}")
        for path in plot_targeted(rows, RUN["targeted_figure"]):
            print(f"figure: {path}")
        return
    if sys.argv[1:] == ["targeted_lowq"]:
        from .config.stag_hunt_sharing_config import SWEEP_TARGETED_LOWQ

        rows = sweep(SWEEP_TARGETED_LOWQ, RUN["targeted_lowq_csv"])
        print(f"{len(rows)} runs written to {RUN['targeted_lowq_csv']}")
        return
    if sys.argv[1:] == ["threshold"]:
        from .config.stag_hunt_sharing_config import SWEEP_THRESHOLD

        rows = sweep(SWEEP_THRESHOLD, RUN["threshold_csv"], RUN["threshold_workers"])
        print(f"{len(rows)} runs written to {RUN['threshold_csv']}")
        return
    if sys.argv[1:]:
        raise SystemExit("usage: ... stag_hunt_sharing [targeted | targeted_lowq | threshold]")
    rows = sweep()
    print(f"{len(rows)} runs written to {RUN['results_csv']}")
    from .utils.plot_sweep import plot

    for path in plot(rows, RUN["figure"]):
        print(f"figure: {path}")


if __name__ == "__main__":
    main()
