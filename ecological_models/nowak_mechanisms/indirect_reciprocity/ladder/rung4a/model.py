"""Rung 4a of the indirect-reciprocity ladder (README.md, "Rung 4a"): rung 3b plus unconditional cooperators.

Three strategies, laid out ALLD first, then ALLC, then DISC. ALLC never consults and always intends to help; its
intended helps fail with probability e, and its acts are observed (o), assessed by the arm's norm and flipped (a) like
anyone's. Everything else as rung 3b (see rung3b/model.py). Reproduction: n_ALLD ~ Binomial(N, ALLD share of total
fitness) exactly as rung 3b; then, only if ALLC are present and not all offspring are ALLD,
n_ALLC ~ Binomial(N - n_ALLD, ALLC fitness / (ALLC + DISC fitness)); the rest DISC. A run stops only when a single
strategy remains. With no ALLC every draw and rule is rung 3b's.
"""

import numpy as np
from numba import njit

N, B, C, S, K = 1000, 3.0, 1.0, 0.1, 10
TEST, SHUFFLED, IMAGE = 0, 1, 2
NSTATS = 18


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
def play(is_disc, is_allc, k, b, c, q, o, e, a, arm, stats):
    """One generation's encounters; net payoff per individual (not yet divided by k).

    stats (float64[18]); 0-11 as rung 3b (DISC-specific where rung 3b was; 1/2 now count ALLD recipients only):
    0 sanity violations (test arm: observed cooperator act -> bad after <=> qualifying failure XOR flip;
    unobserved act -> unchanged), 1 consulting-DISC encounters with an ALLD recipient, 2 of those with the ALLD good,
    3 helps, 4 consulting-DISC encounters with a DISC recipient, 5 of those good, 6 DISC qualifying failures while
    consulting, 7 DISC qualifying failures while not consulting, 8 DISC assessed bad, 9 flips to good, 10 flips to
    bad, 11 flips of ALLD records; 12 consulting-DISC encounters with an ALLC recipient, 13 of those good, 14 ALLC
    qualifying failures, 15 ALLC assessed bad, 16 encounters, 17 ALLC intended helps.
    """
    n = is_disc.shape[0]
    net = np.zeros(n)
    good = np.ones(n, dtype=np.bool_)
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
            stats[16] += 1.0
            rec_good = good[j]
            intends = False
            consulted = False
            if is_disc[i]:
                if np.random.random() < q:
                    consulted = True
                    if arm == SHUFFLED:
                        intends = good[_other(n, i, j)]
                    else:
                        intends = rec_good
                    if is_disc[j]:
                        stats[4] += 1.0
                        if rec_good:
                            stats[5] += 1.0
                    elif is_allc[j]:
                        stats[12] += 1.0
                        if rec_good:
                            stats[13] += 1.0
                    else:
                        stats[1] += 1.0
                        if rec_good:
                            stats[2] += 1.0
                else:
                    intends = True
            elif is_allc[i]:
                intends = True
                stats[17] += 1.0
            failed = False
            if intends and e > 0.0:
                failed = np.random.random() < e
            helps = intends and not failed
            if helps:
                net[i] -= c
                net[j] += b
                stats[3] += 1.0
            seen = True if o >= 1.0 else np.random.random() < o
            before = good[i]
            flipped = False
            if seen:
                if arm == IMAGE:
                    new = helps
                else:
                    new = True if helps else (not rec_good)  # simple standing
                if a > 0.0:
                    flipped = np.random.random() < a
                if flipped:
                    new = not new
                    if new:
                        stats[9] += 1.0
                    else:
                        stats[10] += 1.0
                    if not is_disc[i] and not is_allc[i]:
                        stats[11] += 1.0
                good[i] = new
            elif arm == TEST and good[i] != before:
                stats[0] += 1.0
            if is_disc[i] or is_allc[i]:
                new_bad = seen and not good[i]
                qualifying = seen and intends and failed and rec_good
                if is_disc[i]:
                    if new_bad:
                        stats[8] += 1.0
                    if qualifying:
                        if consulted:
                            stats[6] += 1.0
                        else:
                            stats[7] += 1.0
                else:
                    if new_bad:
                        stats[15] += 1.0
                    if qualifying:
                        stats[14] += 1.0
                if arm == TEST and seen and new_bad != (qualifying != flipped):
                    stats[0] += 1.0
    return net


@njit(cache=True)
def generation(n_alld, n_allc, n, k, b, c, q, o, e, a, s, arm, stats):
    """Returns (n_alld, n_allc) of the next generation."""
    n_disc = n - n_alld - n_allc
    if (n_alld == n) or (n_allc == n) or (n_disc == n):
        return n_alld, n_allc
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld + n_allc] = False
    is_allc = np.zeros(n, dtype=np.bool_)
    is_allc[n_alld:n_alld + n_allc] = True
    net = play(is_disc, is_allc, k, b, c, q, o, e, a, arm, stats)
    f = 1.0 + s * net / k
    na = np.random.binomial(n, f[:n_alld].sum() / f.sum())
    nc = 0
    if n_allc > 0 and na < n:
        fc = f[n_alld:n_alld + n_allc].sum()
        fd = f[n_alld + n_allc:].sum()
        nc = np.random.binomial(n - na, fc / (fc + fd))
    return na, nc


@njit(cache=True)
def trajectory(n_alld0, n_allc0, n, k, b, c, q, o, e, a, s, arm, gens, stats, stats_g1):
    out = np.empty((gens + 1, 3))  # shares ALLD, ALLC, DISC after each generation
    na, nc = n_alld0, n_allc0
    out[0, 0] = na / n
    out[0, 1] = nc / n
    out[0, 2] = (n - na - nc) / n
    for g in range(gens):
        st = stats_g1 if g == 0 else stats
        na, nc = generation(na, nc, n, k, b, c, q, o, e, a, s, arm, st)
        out[g + 1, 0] = na / n
        out[g + 1, 1] = nc / n
        out[g + 1, 2] = (n - na - nc) / n
    return out


def run(q, o, e, a, start, arm, seed, gens=500, n=N, k=K, b=B, c=C, s=S):
    """start = (ALLC, DISC, ALLD) shares. Returns (shares per generation [ALLD, ALLC, DISC], stats, stats_g1)."""
    if s * c >= 1.0:
        raise ValueError("fitness could become non-positive")
    if not (0.0 < o <= 1.0 and 0.0 <= e < 1.0 and 0.0 <= a < 0.5):
        raise ValueError("need 0 < o <= 1, 0 <= e < 1 and 0 <= a < 0.5")
    xc, xd, xa = start
    if abs(xc + xd + xa - 1.0) > 1e-9:
        raise ValueError("start shares must sum to 1")
    _seed(seed)
    stats, stats_g1 = np.zeros(NSTATS), np.zeros(NSTATS)
    tr = trajectory(int(round(xa * n)), int(round(xc * n)), n, k, b, c, q, o, e, a, s, arm, gens, stats, stats_g1)
    return tr, stats, stats_g1
