"""Rung 3b of the indirect-reciprocity ladder (README.md, "Rung 3b"): rung 3a plus assessment errors.

As rung 2b (public good/bad record, good at birth, random donor order, k rounds, each act observed with probability
o, consultation with probability q, shuffled control), except that an intended help fails with probability e
(drawn per intended help; no cost, no benefit; assessed as a refusal). Intended refusals get no error draw; with
e = 0 no error draw is made, so the run is rung 2b exactly. Arms: TEST and SHUFFLED use simple standing (help ->
good; refuse good -> bad; refuse bad -> good); IMAGE decides as TEST but assesses help -> good, any refusal -> bad.

Rung 3b addition: when an act is observed, the assigned record is flipped with probability a (drawn per observed
act, for every individual, after the observation draw). With a = 0 no flip draw is made (rung 3a exactly).
"""

import numpy as np
from numba import njit

N, B, C, S, K = 1000, 3.0, 1.0, 0.1, 10
TEST, SHUFFLED, IMAGE = 0, 1, 2
NSTATS = 12


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
def play(is_disc, k, b, c, q, o, e, a, arm, stats):
    """One generation's encounters; net payoff per individual (not yet divided by k).

    stats (float64[9]): 0 sanity violations (test arm: DISC new record bad <=> observed & intended help & failed &
    recipient good), 1 consulting-DISC encounters with an ALLD recipient, 2 of those with the ALLD good, 3 helps
    given, 4 consulting-DISC encounters with a DISC recipient, 5 of those with the DISC good, 6 qualifying failures
    while consulting, 7 qualifying failures while not consulting, 8 DISC assessed bad, 9 flips to good,
    10 flips to bad, 11 flips of ALLD records. Sanity (test arm): observed DISC act -> (bad after <=> qualifying
    failure XOR flipped); unobserved act (anyone) -> record unchanged.
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
                    else:
                        stats[1] += 1.0
                        if rec_good:
                            stats[2] += 1.0
                else:
                    intends = True
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
                    if not is_disc[i]:
                        stats[11] += 1.0
                good[i] = new
            elif arm == TEST and good[i] != before:
                stats[0] += 1.0
            if is_disc[i]:
                new_bad = seen and not good[i]
                if new_bad:
                    stats[8] += 1.0
                qualifying = seen and intends and failed and rec_good
                if qualifying:
                    if consulted:
                        stats[6] += 1.0
                    else:
                        stats[7] += 1.0
                if arm == TEST and seen and new_bad != (qualifying != flipped):
                    stats[0] += 1.0
    return net


@njit(cache=True)
def generation(n_alld, n, k, b, c, q, o, e, a, s, arm, stats):
    if n_alld == 0 or n_alld == n:
        return n_alld
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld] = False
    net = play(is_disc, k, b, c, q, o, e, a, arm, stats)
    f = 1.0 + s * net / k
    return np.random.binomial(n, f[:n_alld].sum() / f.sum())


@njit(cache=True)
def trajectory(n_alld0, n, k, b, c, q, o, e, a, s, arm, gens, stats, stats_g1):
    out = np.empty(gens + 1)
    x = n_alld0
    out[0] = 1.0 - x / n
    for g in range(gens):
        st = stats_g1 if g == 0 else stats
        x = generation(x, n, k, b, c, q, o, e, a, s, arm, st)
        out[g + 1] = 1.0 - x / n
    return out


def run(q, o, e, a, start_disc, arm, seed, gens=500, n=N, k=K, b=B, c=C, s=S):
    """Returns (DISC share after each generation, stats from generation 2 on, stats of generation 1)."""
    if s * c >= 1.0:
        raise ValueError("fitness could become non-positive")
    if not (0.0 < o <= 1.0 and 0.0 <= e < 1.0 and 0.0 <= a < 0.5):
        raise ValueError("need 0 < o <= 1, 0 <= e < 1 and 0 <= a < 0.5")
    _seed(seed)
    stats, stats_g1 = np.zeros(NSTATS), np.zeros(NSTATS)
    tr = trajectory(int(round((1.0 - start_disc) * n)), n, k, b, c, q, o, e, a, s, arm, gens, stats, stats_g1)
    return tr, stats, stats_g1
