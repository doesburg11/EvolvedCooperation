"""Traulsen and Nowak (2006) multilevel selection model (pre-registration: README.md).

State: for each of m groups, its size s and number of cooperators i. Within a group, pi_C = b(i - 1) - c(s - 1) and
pi_D = b i; fitness 1 - w + w * pi. Each step one individual of the whole population reproduces in proportion to
fitness and its offspring joins its group; a group that reaches size n splits with probability p (another group,
chosen uniformly, dies) or else loses a uniformly chosen member.
"""

from __future__ import annotations

import numpy as np
from numba import njit


def threshold(n: int, m: int) -> float:
    """Finite-m threshold b*/c = 1 + n/(m - 2) (Nowak 2006, SOM)."""
    return 1 + n / (m - 2)


@njit(cache=False)
def fitnesses(i, s, b, c, w):
    """(group total fitness, cooperator fitness, defector fitness) for a group of size s with i cooperators."""
    f_c = 1.0 - w + w * (b * (i - 1) - c * (s - 1))
    f_d = 1.0 - w + w * (b * i)
    return i * f_c + (s - i) * f_d, f_c, f_d


@njit(cache=False)
def split(ic, sz, g, n):
    """Split full group g into two non-empty daughters; a uniformly chosen other group is replaced by daughter 2."""
    m = ic.shape[0]
    k = 0
    while k < 1 or k > n - 1:
        k = np.random.binomial(n, 0.5)
    c1 = np.random.hypergeometric(ic[g], n - ic[g], k) if 0 < ic[g] < n else (k if ic[g] == n else 0)
    h = np.random.randint(m - 1)
    if h >= g:
        h += 1
    ic[h] = ic[g] - c1
    sz[h] = n - k
    ic[g] = c1
    sz[g] = k


@njit(cache=False)
def step(ic, sz, n, b, c, w, p):
    m = ic.shape[0]
    totals = np.empty(m)
    total = 0.0
    for g in range(m):
        f_g, _, _ = fitnesses(ic[g], sz[g], b, c, w)
        totals[g] = f_g
        total += f_g
    u = np.random.random() * total
    g = 0
    acc = totals[0]
    while u >= acc and g < m - 1:
        g += 1
        acc += totals[g]
    _, f_c, f_d = fitnesses(ic[g], sz[g], b, c, w)
    p_coop = ic[g] * f_c / (ic[g] * f_c + (sz[g] - ic[g]) * f_d)
    if np.random.random() < p_coop:
        ic[g] += 1
    sz[g] += 1
    if sz[g] >= n:
        if np.random.random() < p:
            split(ic, sz, g, n)
        else:
            if np.random.random() * sz[g] < ic[g]:
                ic[g] -= 1
            sz[g] -= 1


@njit(cache=False)
def initial_state(n, m):
    ic = np.zeros(m, dtype=np.int64)
    sz = np.full(m, n - 1, dtype=np.int64)
    ic[np.random.randint(m)] = 1
    return ic, sz


@njit(cache=False)
def run_one(n, m, b, c, w, p, seed):
    """One fixation run from a single cooperator; True if cooperators fix."""
    np.random.seed(seed)
    ic, sz = initial_state(n, m)
    while True:
        step(ic, sz, n, b, c, w, p)
        coop = ic.sum()
        if coop == 0:
            return False
        if coop == sz.sum():
            return True


@njit(cache=False)
def run_cell(n, m, b, c, w, p, seed0, runs):
    fixed = 0
    for r in range(runs):
        if run_one(n, m, b, c, w, p, seed0 + r):
            fixed += 1
    return fixed
