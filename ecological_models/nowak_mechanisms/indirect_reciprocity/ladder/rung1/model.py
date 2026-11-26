"""Rung 1 of the indirect-reciprocity ladder (README.md): sampled, sequential encounters, oracle-label reputation.

Each generation: k rounds; in each round every individual is donor once to a recipient drawn uniformly from the
other N - 1. A DISC donor "knows" with probability q (drawn per encounter). Test arm: knowing reveals the
recipient's label; DISC helps a DISC recipient always and an ALLD recipient only when not knowing. Shuffled arm:
knowing reveals the label of a uniform random individual other than donor and recipient (drawn per encounter), and
the donor helps if that label is DISC; not knowing -> help. ALLD never helps. Help costs c, gives b.
Fitness 1 + s * (benefits - costs) / k; next generation's ALLD count ~ Binomial(N, ALLD share of total fitness).
"""

import numpy as np
from numba import njit

N, B, C, S, K = 1000, 3.0, 1.0, 0.1, 10


@njit(cache=True)
def _seed(seed):
    np.random.seed(seed)


@njit(cache=True)
def _other(n, excl1, excl2):
    """Uniform index in range(n) excluding two distinct indices."""
    lo, hi = min(excl1, excl2), max(excl1, excl2)
    x = np.random.randint(0, n - 2)
    if x >= lo:
        x += 1
    if x >= hi:
        x += 1
    return x


@njit(cache=True)
def payoffs(is_disc, k, b, c, q, shuffled):
    """Net payoff per individual over one generation's k rounds (not yet divided by k)."""
    n = is_disc.shape[0]
    net = np.zeros(n)
    for _ in range(k):
        for i in range(n):
            j = np.random.randint(0, n - 1)
            if j >= i:
                j += 1
            if not is_disc[i]:
                continue
            knows = np.random.random() < q
            if not knows:
                helps = True
            elif shuffled:
                helps = is_disc[_other(n, i, j)]
            else:
                helps = is_disc[j]
            if helps:
                net[i] -= c
                net[j] += b
    return net


@njit(cache=True)
def generation(n_alld, n, k, b, c, q, s, shuffled):
    if n_alld == 0 or n_alld == n:
        return n_alld
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld] = False
    net = payoffs(is_disc, k, b, c, q, shuffled)
    f = 1.0 + s * net / k
    fa = f[:n_alld].sum()
    return np.random.binomial(n, fa / f.sum())


@njit(cache=True)
def trajectory(n_alld0, n, k, b, c, q, s, shuffled, gens):
    out = np.empty(gens + 1)
    x = n_alld0
    out[0] = 1.0 - x / n
    for g in range(gens):
        x = generation(x, n, k, b, c, q, s, shuffled)
        out[g + 1] = 1.0 - x / n
    return out  # DISC share after each generation


def run(q, start_disc, shuffled, seed, gens=500, n=N, k=K, b=B, c=C, s=S):
    if s * c >= 1.0:  # worst case: a DISC helps in all k turns and receives nothing -> fitness 1 - s*c
        raise ValueError("fitness could become non-positive")
    _seed(seed)
    n_alld0 = int(round((1.0 - start_disc) * n))
    return trajectory(n_alld0, n, k, b, c, q, s, shuffled, gens)
