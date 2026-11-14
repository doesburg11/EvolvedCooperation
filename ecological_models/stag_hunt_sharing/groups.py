#!/usr/bin/env python3
"""
Selection between groups in the spatial stag hunt (README.md, "Selection
between groups"; PredPreyGrass eco_evolutionary_deer_stag_hunt DESIGN_4.md,
step 0).

The population is n_groups separate square tori of group_size cells, one
hunter per cell, with no sharing (share_fraction 0). Within each group,
hunting, fitness and reproduction are stag_hunt_sharing's (local dispersal:
a parent is drawn from the cell and its 8 neighbours, inside the group).
Groups never interact except through the group rule. The groups sit on a
ring: group g's neighbours are g - 1 and g + 1 (mod n_groups).

Group rules (applied after each generation's reproduction):

- "none": no rule; the groups evolve apart.
- "R" (referee): every interval generations the group with the lowest mean
  fitness over those generations is replaced by a copy of the group with the
  highest (ties: random).
- "F" (fission): each group accumulates its summed fitness (the stand-in for
  births). When a group's sum reaches K, it splits: its copy refounds the
  weaker of its two ring neighbours (lower mean fitness per hunter-generation
  since that neighbour's own last founding; ties random), only if that
  neighbour is also weaker than the splitter (its mean fitness since its own
  last founding); the splitter's sum resets either way. K = interval x
  group cells x the fitness of a hare hunter, so an all-hare group splits
  every interval generations, R's pace. Several splits in one generation are
  handled in ring order; a group refounded in a generation is not a source
  in it.

A copy is exact (strategies only, cell by cell); a refounded group's
accumulators restart.

Run from the repository root:

    ./.conda/bin/python -m ecological_models.stag_hunt_sharing.groups
"""

from __future__ import annotations

import csv
import itertools
from multiprocessing import Pool
from pathlib import Path
from typing import Any

import numpy as np

from .config.stag_hunt_sharing_config import GROUPS, MODEL
from .stag_hunt_sharing import check, fitness, food, hunt, reproduce

RULES = ("none", "R", "F")


def group_config(setting: dict[str, Any]) -> dict[str, Any]:
    """One group's stag_hunt_sharing settings, checked."""
    config = {**MODEL, "share_fraction": 0.0, "dispersal": "local", "grid_size": GROUPS["group_size"], **setting}
    check(config)
    if config["share_fraction"] != 0 or config["dispersal"] != "local" or config["grid_size"] != GROUPS["group_size"]:
        raise ValueError("groups run without sharing, with local dispersal and with GROUPS' group size")
    return config


def hare_fitness(config: dict[str, Any]) -> float:
    return float(fitness(np.array([config["hare_payoff"]]), config)[0])


def _argmin_random(values: np.ndarray, rng: np.random.Generator, candidates=None) -> int:
    idx = np.arange(len(values)) if candidates is None else np.asarray(candidates)
    v = values[idx]
    best = idx[np.flatnonzero(v == v.min())]
    return int(rng.choice(best))


def _argmax_random(values: np.ndarray, rng: np.random.Generator, candidates=None) -> int:
    return _argmin_random(-values, rng, candidates)


def referee(stag, window_fitness, rng):
    """R: lowest mean fitness replaced by highest. Returns (source, sink)
    or None when every group is tied."""
    if np.all(window_fitness == window_fitness[0]):
        return None
    sink = _argmin_random(window_fitness, rng)
    source = _argmax_random(window_fitness, rng)
    stag[sink] = stag[source]
    return source, sink


def fission(stag, total, rate_sum, rate_count, k, rng):
    """F: every group whose summed fitness reached k splits, in ring order.
    total: summed fitness since the group's last split or founding;
    rate_sum / rate_count: summed fitness and hunter-generations since the
    group's own last founding. Returns the list of (source, sink) events."""
    n = len(stag)
    events, refounded = [], set()
    for g in range(n):
        if total[g] < k or g in refounded:
            continue
        total[g] = 0.0
        rate = rate_sum / np.maximum(rate_count, 1)
        left, right = (g - 1) % n, (g + 1) % n
        sink = _argmin_random(rate, rng, [left, right]) if left != right else left
        if rate[sink] < rate[g]:
            stag[sink] = stag[g]
            total[sink] = rate_sum[sink] = rate_count[sink] = 0.0
            refounded.add(sink)
            events.append((g, sink))
    return events


def run(setting: dict[str, Any], rule: str, seed: int) -> dict[str, Any]:
    """One run: the mean stag share over the last measure_last generations
    (whole population), the final between-group variance share of stag
    (Q_ST-like: variance of group means / total variance) and the number of
    group events."""
    if rule not in RULES:
        raise ValueError(f"rule must be one of {RULES}")
    config = group_config(setting)
    n, size = GROUPS["n_groups"], config["grid_size"]
    generations, last, interval = GROUPS["generations"], GROUPS["measure_last"], GROUPS["interval"]
    rng = np.random.default_rng(seed)
    stag = (rng.random((n, size, size)) < config["initial_stag_fraction"]).astype(np.int8)
    k = interval * size * size * hare_fitness(config)
    window = np.zeros(n)
    total, rate_sum, rate_count = np.zeros(n), np.zeros(n), np.zeros(n)
    shares, events = [], 0
    for generation in range(generations):
        caught = hunt(stag, rng, config)
        fit = fitness(food(stag, caught, config), config)
        per_group = fit.sum(axis=(1, 2))
        if generation >= generations - last:
            shares.append(stag.mean())
        stag = reproduce(stag, fit, rng, config)
        if rule == "R":
            window += per_group
            if (generation + 1) % interval == 0:
                events += referee(stag, window, rng) is not None
                window[:] = 0.0
        elif rule == "F":
            total += per_group
            rate_sum += per_group
            rate_count += size * size
            events += len(fission(stag, total, rate_sum, rate_count, k, rng))
    means = stag.mean(axis=(1, 2))
    p = stag.mean()
    return {
        "stag_fraction": float(np.mean(shares)),
        "final_stag_fraction": float(p),
        "between_group_share": float(means.var() / (p * (1 - p))) if 0 < p < 1 else float("nan"),
        "events": int(events),
    }


def _job(job):
    setting, rule, seed = job
    return {**setting, "rule": rule, "seed": seed, **run(setting, rule, seed)}


def jobs(sweep: dict[str, list[Any]] | None = None) -> list[tuple[dict[str, Any], str, int]]:
    sweep = GROUPS["sweep"] if sweep is None else sweep
    keys = list(sweep)
    settings = [dict(zip(keys, values)) for values in itertools.product(*(sweep[key] for key in keys))]
    return [(s, rule, seed) for s in settings for rule in RULES for seed in GROUPS["seeds"]]


def sweep(results_csv: str | None = None, workers: int | None = None) -> list[dict[str, Any]]:
    with Pool(workers or GROUPS["workers"]) as pool:
        rows = pool.map(_job, jobs(), chunksize=2)
    path = Path(results_csv or GROUPS["results_csv"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    import sys

    if sys.argv[1:]:
        raise SystemExit("usage: ... stag_hunt_sharing.groups (settings in config GROUPS)")
    rows = sweep()
    print(f"{len(rows)} runs written to {GROUPS['results_csv']}")


if __name__ == "__main__":
    main()
