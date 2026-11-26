"""Rung-5b candidate: rung 5a with a mid-generation, target-specific gossip phase.

The no-gossip arm intentionally follows rung 5a's NumPy random stream exactly.
Gossip has a separate deterministic LCG stream, so it cannot alter encounter,
reproduction or mutation draws merely by consuming randomness.
"""

import numpy as np
from numba import njit

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import model as M

N, B, C, S, K = M.N, M.B, M.C, M.S, M.K
NO_GOSSIP, TARGET_GOSSIP, SHAM_GOSSIP = 0, 1, 2
Q_GOSSIP = 0.8
NST = 37
STATS = M.STATS + ("gossip_attempts", "gossip_changes", "gossip_noops",
                   "refusal_obs_first", "refusal_recgood_first", "refusal_obs_second", "refusal_recgood_second")
STATS = STATS + ("agreement_before", "agreement_after")
AUDIT = M.AUDIT


@njit(cache=True)
def _next(state):
    return state * np.uint64(6364136223846793005) + np.uint64(1442695040888963407)


@njit(cache=True)
def _u01(state):
    return float(state >> np.uint64(11)) * (1.0 / 9007199254740992.0)


@njit(cache=True)
def _gossip_state(seed, generation):
    return np.uint64(seed + 1) * np.uint64(0x9E3779B97F4A7C15) + np.uint64(generation + 1)


@njit(cache=True)
def _eligible_id(pos, source):
    return pos if pos < source else pos + 1


@njit(cache=True)
def agreement_sample(VT, seed, generation):
    """Fixed diagnostic-only sample of 10,000 distinct-role view triples."""
    n = VT.shape[0]
    block = (n - 1) * (n - 2)
    total = n * block
    # A step of total - 1 is coprime to total, hence this is a duplicate-free
    # cyclic traversal.  The seed chooses its origin without touching model RNG.
    start = int(_gossip_state(seed + 104729, generation) % np.uint64(total))
    agree = 0
    for draw in range(10000):
        index = (start - draw) % total
        target = index // block
        rest = index % block
        first = rest // (n - 2)
        if first >= target:
            first += 1
        second = rest % (n - 2)
        lo, hi = (target, first) if target < first else (first, target)
        if second >= lo:
            second += 1
        if second >= hi:
            second += 1
        if VT[target, first] == VT[target, second]:
            agree += 1
    return agree


@njit(cache=True)
def gossip(VT, arm, state, stats):
    """One LCG-driven source phase. Returns state; NO_GOSSIP consumes no draws."""
    n = VT.shape[0]
    if arm == NO_GOSSIP:
        return state
    state = _next(state)
    source = int(state % np.uint64(n))
    perm = np.empty(n - 1, np.int64)
    if arm == SHAM_GOSSIP:
        # Rejection-sampled Fisher--Yates: conditional on no fixed points this
        # is a uniform derangement of the eligible targets.
        valid = False
        while not valid:
            for pos in range(n - 1):
                perm[pos] = pos
            for pos in range(n - 2, 0, -1):
                state = _next(state)
                other = int(_u01(state) * (pos + 1))
                tmp = perm[pos]
                perm[pos] = perm[other]
                perm[other] = tmp
            valid = True
            for pos in range(n - 1):
                if perm[pos] == pos:
                    valid = False
                    break
    for pos in range(n - 1):
        target = _eligible_id(pos, source)
        copied_target = target
        if arm == SHAM_GOSSIP:
            copied_target = _eligible_id(perm[pos], source)
        source_view = VT[copied_target, source]
        for receiver in range(n):
            if receiver == source or receiver == target:
                continue
            state = _next(state)
            if _u01(state) < Q_GOSSIP:
                stats[28] += 1.0
                if VT[target, receiver] != source_view:
                    VT[target, receiver] = source_view
                    stats[29] += 1.0
                else:
                    stats[30] += 1.0
    return state


@njit(cache=True)
def _rounds(VT, rounds, is_disc, is_allc, b, c, q, o, e, a, stats, gen1, gtype, gtype_den, order, until_flip):
    n = VT.shape[0]
    observed = np.zeros(n, dtype=np.bool_)
    flip = np.zeros(n, dtype=np.bool_)
    don_before = np.empty(n, np.uint8)
    rec_before = np.empty(n, np.uint8)
    net = np.zeros(n)
    for _ in range(rounds):
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
            consult_u = np.random.random() if is_disc[i] else 1.0
            fail_u = np.random.random() if e > 0.0 else 1.0
            until_flip = M.draw_masks(n, i, j, o, a, until_flip, observed, flip)
            helped, dg = M.encounter(VT, i, j, is_disc, is_allc, consult_u, fail_u, -1, observed, flip, q, e,
                                     M.TEST, stats, don_before, rec_before)
            if helped:
                net[i] -= c
                net[j] += b
            ti = 1 if is_disc[i] else (0 if is_allc[i] else 2)
            gtype[ti] += dg
            if gen1:
                stats[22] += gtype[0]
                stats[23] += gtype_den[0]
                stats[24] += gtype[1]
                stats[25] += gtype_den[1]
                stats[26] += gtype[2]
                stats[27] += gtype_den[2]
    return net, until_flip


@njit(cache=True)
def generation(n_alld, n_allc, n, k, b, c, q, o, e, a, s, mu, arm, seed, generation_index, stats, audit_row,
               VT, gen1):
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld + n_allc] = False
    is_allc = np.zeros(n, dtype=np.bool_)
    is_allc[n_alld:n_alld + n_allc] = True
    VT[:, :] = 1
    for t in range(n):
        VT[t, t] = 0
    n_allc_now, n_disc = np.sum(is_allc), np.sum(is_disc)
    gtype_den = np.array([float((n - 1) * n_allc_now), float((n - 1) * n_disc),
                          float((n - 1) * (n - n_allc_now - n_disc))])
    gtype = gtype_den.copy()
    order = np.arange(n)
    until_flip = M._geom(a) if a > 0.0 else -1
    refusal_before, recgood_before = stats[9], stats[10]
    net, until_flip = _rounds(VT, k // 2, is_disc, is_allc, b, c, q, o, e, a, stats, gen1, gtype, gtype_den, order,
                              until_flip)
    stats[31] += stats[9] - refusal_before
    stats[32] += stats[10] - recgood_before
    stats[35] += agreement_sample(VT, seed, generation_index)
    state = gossip(VT, arm, _gossip_state(seed, generation_index), stats)
    stats[36] += agreement_sample(VT, seed, generation_index)
    refusal_before, recgood_before = stats[9], stats[10]
    second, until_flip = _rounds(VT, k - k // 2, is_disc, is_allc, b, c, q, o, e, a, stats, gen1, gtype, gtype_den,
                                 order, until_flip)
    net += second
    stats[33] += stats[9] - refusal_before
    stats[34] += stats[10] - recgood_before
    audit_row[9] = n * k
    f = 1.0 + s * net / k
    na = np.random.binomial(n, f[:n_alld].sum() / f.sum())
    nc = 0
    if n_allc > 0 and na < n:
        fc = f[n_alld:n_alld + n_allc].sum()
        fd = f[n_alld + n_allc:].sum()
        nc = np.random.binomial(n - na, fc / (fc + fd))
    nd = n - na - nc
    audit_row[0], audit_row[1], audit_row[2] = nc, nd, na
    nc, nd, na, m_c, m_d, m_a, c_to_d, d_to_c, a_to_c = M.mutate_detail(nc, nd, na, mu)
    audit_row[3], audit_row[4], audit_row[5] = m_c, m_d, m_a
    audit_row[6], audit_row[7], audit_row[8] = c_to_d, d_to_c, a_to_c
    return na, nc


@njit(cache=True)
def chunk(na, nc, g0, g1, counts, audit, n, k, b, c, q, o, e, a, s, mu, arm, seed, stats, stats_g1, VT):
    for g in range(g0, g1):
        st = stats_g1 if g == 0 else stats
        na, nc = generation(na, nc, n, k, b, c, q, o, e, a, s, mu, arm, seed, g, st, audit[g], VT, g == 0)
        counts[g + 1, 0], counts[g + 1, 1] = na, nc
    return na, nc


def run(q, o, e, a, mu, start, arm, seed, gens=2000, n=N, k=K, b=B, c=C, s=S, heartbeat=None, every=100):
    if k != 10:
        raise ValueError("rung 5b is registered only for ten encounter rounds")
    M._seed(seed)
    stats, stats_g1 = np.zeros(NST), np.zeros(NST)
    counts, audit = np.empty((gens + 1, 2), np.int64), np.zeros((gens, 10), np.int64)
    xc, xd, xa = start
    na, nc = int(round(xa * n)), int(round(xc * n))
    counts[0, 0], counts[0, 1] = na, nc
    VT = np.ones((n, n), np.uint8)
    for g0 in range(0, gens, every):
        g1 = min(gens, g0 + every)
        na, nc = chunk(na, nc, g0, g1, counts, audit, n, k, b, c, q, o, e, a, s, float(mu), arm, seed, stats,
                       stats_g1, VT)
        if heartbeat is not None:
            heartbeat(g1)
    return counts, audit, stats, stats_g1
