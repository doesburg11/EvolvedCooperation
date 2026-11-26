"""Rung 4b of the indirect-reciprocity ladder (README.md, "Rung 4b"): rung 4a plus mutation, without the shortcut.

Encounters, records, errors, payoffs and reproduction are rung 4a's (`rung4a/model.py`; `play` is reused unchanged).
Two changes only:
  * every generation plays all N * k encounters and reproduces, also when a single strategy remains (rung 4a returned
    the state unchanged then); mutation can reintroduce strategies;
  * mutation after reproduction: from each strategy's offspring count, mutants ~ Binomial(count, mu); each mutant
    becomes one of the two other strategies, the number going to the first of them in the order ALLC, DISC, ALLD
    being Binomial(mutants, 0.5); all transfers applied together. With mu = 0 no mutation draw is made.
Strategy layout as rung 4a: ALLD first, then ALLC, then DISC; trajectories store integer counts (ALLD, ALLC).
"""

import numpy as np
from numba import njit

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a.model import (
    B, C, K, N, NSTATS, S, SHUFFLED, TEST, IMAGE, _seed, play)

__all__ = ["B", "C", "K", "N", "NSTATS", "S", "SHUFFLED", "TEST", "IMAGE", "_seed", "run", "mutate", "mutate_detail", "generation", "AUDIT"]


AUDIT = ("pre_allc", "pre_disc", "pre_alld", "m_allc", "m_disc", "m_alld", "allc_to_disc", "disc_to_allc",
         "alld_to_allc", "encounters")


@njit(cache=True)
def mutate_detail(n_allc, n_disc, n_alld, mu):
    """Mutation with its accounting: returns (n_allc, n_disc, n_alld, m_c, m_d, m_a, c_to_d, d_to_c, a_to_c).
    Order ALLC, DISC, ALLD; the first other strategy of ALLC is DISC, of DISC ALLC, of ALLD ALLC."""
    if mu <= 0.0:
        return n_allc, n_disc, n_alld, 0, 0, 0, 0, 0, 0
    m_c = np.random.binomial(n_allc, mu)
    m_d = np.random.binomial(n_disc, mu)
    m_a = np.random.binomial(n_alld, mu)
    c_to_d = np.random.binomial(m_c, 0.5)   # ALLC -> DISC (first other), rest -> ALLD
    d_to_c = np.random.binomial(m_d, 0.5)   # DISC -> ALLC (first other), rest -> ALLD
    a_to_c = np.random.binomial(m_a, 0.5)   # ALLD -> ALLC (first other), rest -> DISC
    c_to_a = m_c - c_to_d
    d_to_a = m_d - d_to_c
    a_to_d = m_a - a_to_c
    nc = n_allc - m_c + d_to_c + a_to_c
    nd = n_disc - m_d + c_to_d + a_to_d
    na = n_alld - m_a + c_to_a + d_to_a
    return nc, nd, na, m_c, m_d, m_a, c_to_d, d_to_c, a_to_c


@njit(cache=True)
def mutate(n_allc, n_disc, n_alld, mu):
    """Returns (n_allc, n_disc, n_alld, mutants) after mutation."""
    nc, nd, na, m_c, m_d, m_a, _, _, _ = mutate_detail(n_allc, n_disc, n_alld, mu)
    return nc, nd, na, m_c + m_d + m_a


@njit(cache=True)
def generation(n_alld, n_allc, n, k, b, c, q, o, e, a, s, mu, arm, stats, audit_row):
    """Returns (n_alld, n_allc) of the next generation (after reproduction and mutation); fills audit_row
    (pre-mutation offspring counts, mutants per source, transfers to the first other strategy, encounters)."""
    n_disc = n - n_alld - n_allc
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld + n_allc] = False
    is_allc = np.zeros(n, dtype=np.bool_)
    is_allc[n_alld:n_alld + n_allc] = True
    enc0 = stats[16]
    net = play(is_disc, is_allc, k, b, c, q, o, e, a, arm, stats)
    audit_row[9] = stats[16] - enc0
    f = 1.0 + s * net / k
    na = np.random.binomial(n, f[:n_alld].sum() / f.sum())
    nc = 0
    if n_allc > 0 and na < n:
        fc = f[n_alld:n_alld + n_allc].sum()
        fd = f[n_alld + n_allc:].sum()
        nc = np.random.binomial(n - na, fc / (fc + fd))
    nd = n - na - nc
    audit_row[0] = nc
    audit_row[1] = nd
    audit_row[2] = na
    nc, nd, na, m_c, m_d, m_a, c_to_d, d_to_c, a_to_c = mutate_detail(nc, nd, na, mu)
    audit_row[3] = m_c
    audit_row[4] = m_d
    audit_row[5] = m_a
    audit_row[6] = c_to_d
    audit_row[7] = d_to_c
    audit_row[8] = a_to_c
    return na, nc


@njit(cache=True)
def trajectory(n_alld0, n_allc0, n, k, b, c, q, o, e, a, s, mu, arm, gens, stats, stats_g1):
    counts = np.empty((gens + 1, 2), np.int64)      # (ALLD, ALLC) after each generation; DISC = n - both
    audit = np.zeros((gens, 10), np.int64)
    na, nc = n_alld0, n_allc0
    counts[0, 0] = na
    counts[0, 1] = nc
    for g in range(gens):
        st = stats_g1 if g == 0 else stats
        na, nc = generation(na, nc, n, k, b, c, q, o, e, a, s, mu, arm, st, audit[g])
        counts[g + 1, 0] = na
        counts[g + 1, 1] = nc
    return counts, audit


def run(q, o, e, a, mu, start, arm, seed, gens=2000, n=N, k=K, b=B, c=C, s=S):
    """start = (ALLC, DISC, ALLD) shares. Returns (counts per generation [ALLD, ALLC], audit per generation (columns
    AUDIT), stats over generations 2.., stats of generation 1)."""
    if s * c >= 1.0:
        raise ValueError("fitness could become non-positive")
    if not (0.0 < o <= 1.0 and 0.0 <= e < 1.0 and 0.0 <= a < 0.5 and 0.0 <= mu < 1.0):
        raise ValueError("need 0 < o <= 1, 0 <= e < 1, 0 <= a < 0.5 and 0 <= mu < 1")
    xc, xd, xa = start
    if abs(xc + xd + xa - 1.0) > 1e-9:
        raise ValueError("start shares must sum to 1")
    _seed(seed)
    stats, stats_g1 = np.zeros(NSTATS), np.zeros(NSTATS)
    counts, audit = trajectory(int(round(xa * n)), int(round(xc * n)), n, k, b, c, q, o, e, a, s, float(mu), arm,
                                 gens, stats, stats_g1)
    return counts, audit, stats, stats_g1
