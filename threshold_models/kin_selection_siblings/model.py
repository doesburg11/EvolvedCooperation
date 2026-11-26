"""Sibling alarm-call model (after Primer 2021) for testing Hamilton's rule.

Pre-registration and amendment A1: threshold_models/kin_selection_siblings/README.md

One generation: every puddle (n siblings) visits a random tree; on a predator tree one random member notices the
predator. A coward noticer survives and the other n - 1 are eaten; an altruist noticer saves the other n - 1 and dies
with probability c. A uniformly random subset of survivors fills the homes (asexual: one parent per home, one
puddle of n clones; sexual: one pair per home, `puddles_per_home` puddles of n full siblings, each child copying a
parent chosen uniformly). Haploid, one locus, no mutation, non-overlapping generations.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

COWARD, ALTRUIST = 0, 1


@dataclass(frozen=True)
class Params:
    sexual: bool
    n: int  # puddle size (siblings per puddle)
    c: float  # death probability of an alarm-sounding altruist noticer
    homes: int  # asexual: parents; sexual: pairs
    puddles_per_home: int
    trees: int = 100
    a: float = 0.25  # fraction of trees with a predator (exactly round(a * trees) trees)

    @property
    def r(self) -> float:
        return 0.5 if self.sexual else 1.0

    @property
    def b(self) -> int:
        return self.n - 1

    @property
    def attack_probability(self) -> float:
        return round(self.a * self.trees) / self.trees


def hamilton(p: Params) -> float:
    """b * r - c."""
    return p.b * p.r - p.c


def naive(p: Params, f: float) -> float:
    """b * p - c with p = r + (1 - r) f, the probability that a sibling carries the allele."""
    return p.b * (p.r + (1.0 - p.r) * f) - p.c


def predicted_change(p: Params, f: float) -> float:
    """Exact expected one-generation change f' - f (README, Theory)."""
    a = p.attack_probability
    survivors_attacked = f * (p.b + 1.0 - p.c) + (1.0 - f)
    denominator = (1.0 - a) * p.n + a * survivors_attacked
    return a * f * (1.0 - f) * hamilton(p) / denominator


def predator_trees(p: Params, rng: np.random.Generator) -> np.ndarray:
    k = round(p.a * p.trees)
    trees = np.zeros(p.trees, dtype=bool)
    trees[rng.choice(p.trees, size=k, replace=False)] = True
    return trees


def founders(p: Params, f0: float, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Founding puddles. Returns (alleles, origin); origin = index of the parent (0/1) each child copied."""
    n_puddles = p.homes * p.puddles_per_home
    if not p.sexual:
        alleles = (rng.random(n_puddles) < f0).astype(np.int8)
        return np.repeat(alleles[:, None], p.n, axis=1), np.zeros((n_puddles, p.n), dtype=np.int8)
    parents = (rng.random((n_puddles, 2)) < f0).astype(np.int8)
    origin = rng.integers(0, 2, size=(n_puddles, p.n)).astype(np.int8)
    return np.take_along_axis(parents, origin, axis=1), origin


def generation(
    groups: np.ndarray,
    origin: np.ndarray,
    p: Params,
    predators: np.ndarray,
    rng: np.random.Generator,
    stats: dict[str, int] | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    """One generation. `stats` (if given) accumulates pairs, ibd pairs and altruist siblings over alarm events."""
    n_groups = groups.shape[0]
    rows = np.arange(n_groups)
    attacked = predators[rng.integers(p.trees, size=n_groups)]
    noticer = rng.integers(p.n, size=n_groups)
    noticer_allele = groups[rows, noticer]
    alive = np.ones(groups.shape, dtype=bool)

    coward = attacked & (noticer_allele == COWARD)
    alive[coward] = False
    alive[rows[coward], noticer[coward]] = True

    altruist = attacked & (noticer_allele == ALTRUIST)
    alarm_rows = rows[altruist]
    alarm_noticer = noticer[altruist]
    dies = rng.random(alarm_rows.size) < p.c
    alive[alarm_rows[dies], alarm_noticer[dies]] = False

    if stats is not None and alarm_rows.size:
        sibling = np.ones((alarm_rows.size, p.n), dtype=bool)
        sibling[np.arange(alarm_rows.size), alarm_noticer] = False
        sib_alleles = groups[alarm_rows][sibling]
        sib_origin = origin[alarm_rows][sibling]
        noticer_origin = np.repeat(origin[alarm_rows, alarm_noticer], p.n - 1)
        stats["pairs"] += int(sib_alleles.size)
        stats["ibd"] += int(np.sum(sib_origin == noticer_origin))
        stats["sib_altruist"] += int(sib_alleles.sum())

    survivors = groups[alive]
    rng.shuffle(survivors)
    info: dict[str, object] = {"n_survivors": int(survivors.size)}

    if not p.sexual:
        parents = survivors[: p.homes]
        parents_rep = np.repeat(parents, p.puddles_per_home)
        new_groups = np.repeat(parents_rep[:, None], p.n, axis=1)
        new_origin = np.zeros(new_groups.shape, dtype=np.int8)
        info["parents"] = parents
        return new_groups, new_origin, info

    n_pairs = min(survivors.size, 2 * p.homes) // 2
    pairs = survivors[: 2 * n_pairs].reshape(n_pairs, 2)
    pairs_rep = np.repeat(pairs, p.puddles_per_home, axis=0)
    new_origin = rng.integers(0, 2, size=(pairs_rep.shape[0], p.n)).astype(np.int8)
    new_groups = np.take_along_axis(pairs_rep, new_origin, axis=1)
    info["pairs"] = pairs_rep
    return new_groups, new_origin, info


def run_trajectory(p: Params, f0: float, generations: int, seed: int) -> np.ndarray:
    """Altruist frequency of the puddles entering the forest, generations 0..generations."""
    rng = np.random.default_rng(seed)
    predators = predator_trees(p, rng)
    groups, origin = founders(p, f0, rng)
    freqs = np.empty(generations + 1)
    for g in range(generations + 1):
        freqs[g] = groups.mean() if groups.size else np.nan
        if g < generations:
            groups, origin, _ = generation(groups, origin, p, predators, rng)
    return freqs


def run_one_generation(p: Params, f0: float, seed: int, stats: dict[str, int]) -> tuple[float, float]:
    """(founder frequency, next-generation frequency) from fresh founders."""
    rng = np.random.default_rng(seed)
    predators = predator_trees(p, rng)
    groups, origin = founders(p, f0, rng)
    f_before = float(groups.mean())
    new_groups, _, _ = generation(groups, origin, p, predators, rng, stats)
    return f_before, float(new_groups.mean())
