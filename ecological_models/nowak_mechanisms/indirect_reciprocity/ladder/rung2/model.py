"""Rung 2 of the indirect-reciprocity ladder (README.md, "Rung 2"): reputation earned from actions.

Public good/bad record, everyone good at birth. Each generation: k rounds; in each round donors act one at a time
in a new uniform random order, each to a recipient drawn uniformly from the other N - 1. A DISC donor consults with
probability q (per encounter): not consulting -> helps; consulting -> helps iff the seen record is good. Test arm:
the seen record is the recipient's. Shuffled arm: the record of a uniform individual other than donor and
recipient. ALLD never helps. Every act is observed; the donor's record is updated at once from the act and the
recipient's true record at that moment:
  simple standing (test and shuffled arms): help -> good; refuse good -> bad; refuse bad -> good.
  image scoring (reported arm): help -> good; refuse -> bad. (Decision as in the test arm.)
Help costs c, gives b. Fitness 1 + s * net / k; next ALLD count ~ Binomial(N, ALLD share of total fitness).
"""

import numpy as np
from numba import njit

N, B, C, S, K = 1000, 3.0, 1.0, 0.1, 10
TEST, SHUFFLED, IMAGE = 0, 1, 2


@njit(cache=True)
def _seed(seed):
    np.random.seed(seed)


@njit(cache=True)
def _other(n, excl1, excl2):
    lo, hi = min(excl1, excl2), max(excl1, excl2)
    x = np.random.randint(0, n - 2)
    if x >= lo:
        x += 1
    if x >= hi:
        x += 1
    return x


@njit(cache=True)
def play(is_disc, k, b, c, q, arm, stats):
    """One generation's encounters. Returns net payoff per individual (not yet divided by k).

    stats (float64[4]): 0 DISC-bad assignments (a DISC donor assessed bad), 1 consulting-DISC encounters with an
    ALLD recipient, 2 of those in which the ALLD's record was good, 3 helps given.
    """
    n = is_disc.shape[0]
    net = np.zeros(n)
    good = np.ones(n, dtype=np.bool_)
    order = np.arange(n)
    for _ in range(k):
        for x in range(n - 1, 0, -1):  # new uniform donor order each round
            y = np.random.randint(0, x + 1)
            tmp = order[x]
            order[x] = order[y]
            order[y] = tmp
        for idx in range(n):
            i = order[idx]
            j = np.random.randint(0, n - 1)
            if j >= i:
                j += 1
            helps = False
            if is_disc[i]:
                if np.random.random() < q:
                    if arm == SHUFFLED:
                        helps = good[_other(n, i, j)]
                    else:
                        helps = good[j]
                    if not is_disc[j]:
                        stats[1] += 1.0
                        if good[j]:
                            stats[2] += 1.0
                else:
                    helps = True
            if helps:
                net[i] -= c
                net[j] += b
                stats[3] += 1.0
                new = True
            elif arm == IMAGE:
                new = False
            else:
                new = not good[j]  # simple standing: refusing a bad recipient is justified
            if is_disc[i] and not new:
                stats[0] += 1.0
            good[i] = new
    return net


@njit(cache=True)
def generation(n_alld, n, k, b, c, q, s, arm, stats):
    if n_alld == 0 or n_alld == n:
        return n_alld
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld] = False
    net = play(is_disc, k, b, c, q, arm, stats)
    f = 1.0 + s * net / k
    return np.random.binomial(n, f[:n_alld].sum() / f.sum())


@njit(cache=True)
def trajectory(n_alld0, n, k, b, c, q, s, arm, gens, stats):
    out = np.empty(gens + 1)
    x = n_alld0
    out[0] = 1.0 - x / n
    for g in range(gens):
        x = generation(x, n, k, b, c, q, s, arm, stats)
        out[g + 1] = 1.0 - x / n
    return out


def run(q, start_disc, arm, seed, gens=500, n=N, k=K, b=B, c=C, s=S):
    """Returns (DISC share after each generation, stats summed over the run)."""
    if s * c >= 1.0:
        raise ValueError("fitness could become non-positive")
    _seed(seed)
    stats = np.zeros(4)
    tr = trajectory(int(round((1.0 - start_disc) * n)), n, k, b, c, q, s, arm, gens, stats)
    return tr, stats
