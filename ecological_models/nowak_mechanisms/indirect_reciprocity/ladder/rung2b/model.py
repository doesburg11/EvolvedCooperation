"""Rung 2b of the indirect-reciprocity ladder (README.md, "Rung 2b"): rung 2 with partial observation.

As rung 2 (public good/bad record, good at birth, random donor order per round, k rounds, simple standing,
shuffled control), except that each act is observed with probability o, drawn per act independently of
consultation. An observed act updates the donor's record (simple standing, using the recipient's true record at
that moment); an unobserved act leaves it unchanged. With o = 1 no observation draw is made.
"""

import numpy as np
from numba import njit

N, B, C, S, K = 1000, 3.0, 1.0, 0.1, 10
TEST, SHUFFLED = 0, 1


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
def play(is_disc, k, b, c, q, o, arm, stats):
    """One generation's encounters; net payoff per individual (not yet divided by k).

    stats (float64[6]): 0 DISC assessed bad (observed act), 1 consulting-DISC encounters with an ALLD recipient,
    2 of those with the ALLD's record good, 3 helps, 4 ALLD with no observed act by the end of the generation,
    5 ALLD at the start of the generation.
    """
    n = is_disc.shape[0]
    net = np.zeros(n)
    good = np.ones(n, dtype=np.bool_)
    observed_once = np.zeros(n, dtype=np.bool_)
    order = np.arange(n)
    for _ in range(k):
        for x in range(n - 1, 0, -1):
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
            seen = True if o >= 1.0 else np.random.random() < o
            if seen:
                new = True if helps else (not good[j])  # simple standing
                if is_disc[i] and not new:
                    stats[0] += 1.0
                good[i] = new
                observed_once[i] = True
    for i in range(n):
        if not is_disc[i]:
            stats[5] += 1.0
            if not observed_once[i]:
                stats[4] += 1.0
    return net


@njit(cache=True)
def generation(n_alld, n, k, b, c, q, o, s, arm, stats):
    if n_alld == 0 or n_alld == n:
        return n_alld
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld] = False
    net = play(is_disc, k, b, c, q, o, arm, stats)
    f = 1.0 + s * net / k
    return np.random.binomial(n, f[:n_alld].sum() / f.sum())


@njit(cache=True)
def trajectory(n_alld0, n, k, b, c, q, o, s, arm, gens, stats, stats_g1):
    out = np.empty(gens + 1)
    x = n_alld0
    out[0] = 1.0 - x / n
    for g in range(gens):
        st = stats_g1 if g == 0 else stats
        x = generation(x, n, k, b, c, q, o, s, arm, st)
        out[g + 1] = 1.0 - x / n
    return out


def run(q, o, start_disc, arm, seed, gens=500, n=N, k=K, b=B, c=C, s=S):
    """Returns (DISC share after each generation, stats from generation 2 on, stats of generation 1)."""
    if s * c >= 1.0:
        raise ValueError("fitness could become non-positive")
    if not 0.0 < o <= 1.0:
        raise ValueError("o must be in (0, 1]")
    _seed(seed)
    stats, stats_g1 = np.zeros(6), np.zeros(6)
    tr = trajectory(int(round((1.0 - start_disc) * n)), n, k, b, c, q, o, s, arm, gens, stats, stats_g1)
    return tr, stats, stats_g1
