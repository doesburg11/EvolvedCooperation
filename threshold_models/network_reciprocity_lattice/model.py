"""Cooperators on a 10 x 10 torus with death-birth updating (Ohtsuki et al. 2006).

Pre-registration: threshold_models/network_reciprocity_lattice/README.md

Donation game with accumulated payoffs: a cooperator pays c per neighbour and gives b to each neighbour; it never
receives its own benefit. Fitness f = 1 - w + w * payoff. Each step a uniformly chosen site dies and its k neighbours
compete for it with probability proportional to fitness (payoffs from the current configuration, the dying site
included). A run starts with one cooperator among defectors and ends at fixation or extinction.
"""

from __future__ import annotations

import numpy as np
from numba import njit

VON_NEUMANN = ((0, 1), (1, 0), (0, -1), (-1, 0))
MOORE = ((0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1))


def lattice(side: int, neighbourhood: str) -> np.ndarray:
    """Neighbour table (N, k) of a side x side torus."""
    offsets = {"von_neumann": VON_NEUMANN, "moore": MOORE}[neighbourhood]
    n = side * side
    table = np.empty((n, len(offsets)), dtype=np.int64)
    for site in range(n):
        x, y = divmod(site, side)
        for j, (dx, dy) in enumerate(offsets):
            table[site, j] = ((x + dx) % side) * side + (y + dy) % side
    return table


def threshold(n: int, k: int) -> float:
    """Finite-N death-birth threshold b*/c = (N - 2)/(N/k - 2) (Chen 2013)."""
    return (n - 2) / (n / k - 2)


@njit(cache=False)
def payoff(site, s, nc, b, c, k):
    return b * nc[site] - c * k * s[site]


@njit(cache=False)
def choose_parent(dying, s, nc, nbr, b, c, w, k, u):
    """Index (0..k-1) of the neighbour that wins the empty site, given a uniform draw u in [0, 1)."""
    total = 0.0
    for j in range(k):
        total += 1.0 - w + w * payoff(nbr[dying, j], s, nc, b, c, k)
    target = u * total
    acc = 0.0
    for j in range(k):
        acc += 1.0 - w + w * payoff(nbr[dying, j], s, nc, b, c, k)
        if target < acc:
            return j
    return k - 1


@njit(cache=False)
def db_step(s, nc, nbr, b, c, w, k):
    """One death-birth step; updates s and nc in place; returns the change in the number of cooperators."""
    n = s.shape[0]
    dying = np.random.randint(n)
    parent = nbr[dying, choose_parent(dying, s, nc, nbr, b, c, w, k, np.random.random())]
    new = s[parent]
    if new == s[dying]:
        return 0
    delta = 1 if new == 1 else -1
    s[dying] = new
    for j in range(k):
        nc[nbr[dying, j]] += delta
    return delta


@njit(cache=False)
def init_state(nbr, k, start):
    n = nbr.shape[0]
    s = np.zeros(n, dtype=np.int64)
    nc = np.zeros(n, dtype=np.int64)
    s[start] = 1
    for j in range(k):
        nc[nbr[start, j]] += 1
    return s, nc


@njit(cache=False)
def run_one(nbr, b, c, w, seed):
    """One fixation run; returns True if cooperators fix."""
    np.random.seed(seed)
    n, k = nbr.shape
    s, nc = init_state(nbr, k, np.random.randint(n))
    count = 1
    while 0 < count < n:
        count += db_step(s, nc, nbr, b, c, w, k)
    return count == n


@njit(cache=False)
def run_cell(nbr, b, c, w, seed0, runs):
    """Number of fixations in `runs` runs with seeds seed0 .. seed0 + runs - 1."""
    fixed = 0
    for r in range(runs):
        if run_one(nbr, b, c, w, seed0 + r):
            fixed += 1
    return fixed
