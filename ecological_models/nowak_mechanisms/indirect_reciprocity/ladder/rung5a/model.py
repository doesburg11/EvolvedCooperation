"""Rung 5a of the indirect-reciprocity ladder (README.md, "Rung 5a"): rung 4b with private views.

There is no public record. VT[t, w] is observer w's view of target t (1 = good); the whole matrix is reset to good at
the start of every generation. In each encounter (donor d, recipient r):
  * a DISC consults with probability q its own view VT[r, d] (shuffled arm: VT[z, d] of a uniformly random z other
    than d and r) and intends to help if that view is good; a DISC that does not consult intends to help; ALLC always
    intends to help, ALLD never; an intended help fails with probability e;
  * every individual other than d and r observes independently with probability o and sets its view of the donor:
    standing: good if the donor helped, otherwise good iff its own view of the recipient (read before this act) is
    bad; image scoring: good iff the donor helped; the assigned view is flipped with probability a per observer
    (drawn exactly as independent Bernoulli trials via geometric gaps).
The model checks every act against the stored views (`check_act`): observers' views of the donor equal the rule,
everyone else's views of the donor and all views of the recipient are unchanged. Reproduction and mutation are
rung 4b's (shared code). Encounters, order of play and payoffs follow rung 4a.
"""

import numpy as np
from numba import njit

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b.model import mutate_detail

N, B, C, S, K = 1000, 3.0, 1.0, 0.1, 10
TEST, SHUFFLED, IMAGE = 0, 1, 2
NST = 28
STATS = ("check_mismatch", "sanity_violations", "encounters", "helps", "consult_disc", "consult_good",
         "allc_intends", "observations", "flips", "intent_refusal_obs", "intent_refusal_obs_recgood",
         "shuffled_refusal_obs", "shuffled_refusal_obs_recgood", "exec_fail", "disc_turns",
         "consult_alld", "consult_alld_good", "consult_disc_rec", "consult_disc_rec_good", "consult_allc",
         "consult_allc_good", "intent_refusals", "goodview_allc", "views_allc", "goodview_disc", "views_disc",
         "goodview_alld", "views_alld")
AUDIT = ("pre_allc", "pre_disc", "pre_alld", "m_allc", "m_disc", "m_alld", "allc_to_disc", "disc_to_allc",
         "alld_to_allc", "encounters")


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
def _geom(a):
    """Number of Bernoulli(a) failures before the next success."""
    u = np.random.random()
    while u == 0.0:
        u = np.random.random()
    return int(np.floor(np.log(u) / np.log(1.0 - a)))


@njit(cache=True)
def apply_act(VT, d, r, helped, observed, flip, image):
    """Assessment of one act given the observation and flip masks (scripted-testable). Returns observations."""
    n = VT.shape[0]
    rec = VT[r]
    don = VT[d]
    cnt = 0
    for w in range(n):
        if observed[w]:
            cnt += 1
            if image:
                g = helped
            else:
                g = helped or (rec[w] == 0)
            if flip[w]:
                g = not g
            don[w] = 1 if g else 0
    return cnt


@njit(cache=True)
def check_act(VT, d, r, helped, observed, flip, image, don_before, rec_before):
    """Number of stored views that differ from the rule (0 if the act was applied correctly)."""
    n = VT.shape[0]
    bad = 0
    for w in range(n):
        if VT[r, w] != rec_before[w]:
            bad += 1
        if observed[w]:
            if w == d or w == r:
                bad += 1
            g = helped if image else (helped or (rec_before[w] == 0))
            if flip[w]:
                g = not g
            if VT[d, w] != (1 if g else 0):
                bad += 1
        elif VT[d, w] != don_before[w]:
            bad += 1
    return bad


@njit(cache=True)
def encounter(VT, i, j, is_disc, is_allc, consult_u, fail_u, z, observed, flip, q, e, arm, stats, don_before,
              rec_before):
    """One encounter given its random draws (consult_u, fail_u uniform; z the shuffled target; observation and flip
    masks): decision, assessment, stored-view check and diagnostics. Returns (helped, delta of good views of i)."""
    n = VT.shape[0]
    image = arm == IMAGE
    stats[2] += 1.0
    intends = False
    consulted = False
    view_bad = False
    if is_disc[i]:
        stats[14] += 1.0
        if consult_u < q:
            consulted = True
            stats[4] += 1.0
            v = VT[z, i] if arm == SHUFFLED else VT[j, i]
            intends = v == 1
            view_bad = not intends
            if intends:
                stats[5] += 1.0
            if not is_disc[j] and not is_allc[j]:
                stats[15] += 1.0
                if VT[j, i] == 1:
                    stats[16] += 1.0
            elif is_disc[j]:
                stats[17] += 1.0
                if VT[j, i] == 1:
                    stats[18] += 1.0
            else:
                stats[19] += 1.0
                if VT[j, i] == 1:
                    stats[20] += 1.0
        else:
            intends = True
    elif is_allc[i]:
        intends = True
        stats[6] += 1.0
    failed = intends and fail_u < e
    helped = intends and not failed
    if failed:
        stats[13] += 1.0
    if consulted and view_bad:
        stats[21] += 1.0
    if helped:
        stats[3] += 1.0
    g_before = 0
    for w in range(n):
        don_before[w] = VT[i, w]
        rec_before[w] = VT[j, w]
        g_before += VT[i, w]
    cnt = apply_act(VT, i, j, helped, observed, flip, image)
    stats[7] += cnt
    mism = check_act(VT, i, j, helped, observed, flip, image, don_before, rec_before)
    stats[0] += mism
    if mism > 0:
        raise ValueError("stored-view check failed")
    coop = is_disc[i] or is_allc[i]
    g_after = 0
    for w in range(n):
        g_after += VT[i, w]
        if not observed[w]:
            continue
        if flip[w]:
            stats[8] += 1.0
        rec_good = rec_before[w] == 1
        if consulted and view_bad:
            if arm == SHUFFLED:
                stats[11] += 1.0
                if rec_good:
                    stats[12] += 1.0
            else:
                stats[9] += 1.0
                if rec_good:
                    stats[10] += 1.0
        if arm == TEST and coop:
            violation = is_allc[i] and not intends
            intentional = consulted and view_bad and VT[j, i] == 0 and is_disc[i]
            cause = (failed and rec_good) or (intentional and rec_good)
            if (VT[i, w] == 0) != (cause != flip[w]):
                violation = True
            if violation:
                stats[1] += 1.0
                raise ValueError("private-standing sanity rule violated")
    return helped, g_after - g_before


@njit(cache=True)
def draw_masks(n, i, j, o, a, until_flip, observed, flip):
    """Observation mask (each w other than i and j with probability o; exact fair bits for o = 0.5) and flip mask
    (independent Bernoulli(a) per observation via geometric gaps carried across acts). Returns the new gap."""
    for w in range(n):
        observed[w] = False
        flip[w] = False
    if o >= 1.0:
        for w in range(n):
            observed[w] = True
    elif o == 0.5:
        w = 0
        while w < n:
            bits = np.random.randint(0, 1 << 62)
            for t in range(62):
                if w >= n:
                    break
                observed[w] = (bits >> t) & 1 == 1
                w += 1
    else:
        for w in range(n):
            observed[w] = np.random.random() < o
    observed[i] = False
    observed[j] = False
    if a > 0.0:
        for w in range(n):
            if observed[w]:
                if until_flip == 0:
                    flip[w] = True
                    until_flip = _geom(a)
                else:
                    until_flip -= 1
    return until_flip


@njit(cache=True)
def play(is_disc, is_allc, k, b, c, q, o, e, a, arm, stats, VT, gen1):
    """One generation's encounters with private views; net payoff per individual (not yet divided by k).
    With gen1, stats[22..27] accumulate after every encounter the good views held about each strategy and the
    number of views (an encounter-time average over generation 1)."""
    n = is_disc.shape[0]
    net = np.zeros(n)
    VT[:, :] = 1
    for t in range(n):
        VT[t, t] = 0                      # no self-views (never read)
    order = np.arange(n)
    observed = np.zeros(n, dtype=np.bool_)
    flip = np.zeros(n, dtype=np.bool_)
    don_before = np.empty(n, np.uint8)
    rec_before = np.empty(n, np.uint8)
    n_allc = 0
    n_disc = 0
    for t in range(n):
        if is_disc[t]:
            n_disc += 1
        elif is_allc[t]:
            n_allc += 1
    n_alld = n - n_allc - n_disc
    gtype = np.array([float((n - 1) * n_allc), float((n - 1) * n_disc), float((n - 1) * n_alld)])
    until_flip = _geom(a) if a > 0.0 else -1
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
            consult_u = np.random.random() if is_disc[i] else 1.0
            z = _other(n, i, j) if (arm == SHUFFLED and is_disc[i] and consult_u < q) else -1
            fail_u = np.random.random() if e > 0.0 else 1.0
            until_flip = draw_masks(n, i, j, o, a, until_flip, observed, flip)
            helped, dg = encounter(VT, i, j, is_disc, is_allc, consult_u, fail_u, z, observed, flip, q, e, arm,
                                   stats, don_before, rec_before)
            if helped:
                net[i] -= c
                net[j] += b
            ti = 1 if is_disc[i] else (0 if is_allc[i] else 2)
            gtype[ti] += dg
            if gen1:
                stats[22] += gtype[0]
                stats[23] += (n - 1) * n_allc
                stats[24] += gtype[1]
                stats[25] += (n - 1) * n_disc
                stats[26] += gtype[2]
                stats[27] += (n - 1) * n_alld
    return net


@njit(cache=True)
def generation(n_alld, n_allc, n, k, b, c, q, o, e, a, s, mu, arm, stats, audit_row, VT, gen1):
    """Returns (n_alld, n_allc) of the next generation; reproduction and mutation exactly as rung 4b."""
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld + n_allc] = False
    is_allc = np.zeros(n, dtype=np.bool_)
    is_allc[n_alld:n_alld + n_allc] = True
    enc0 = stats[2]
    net = play(is_disc, is_allc, k, b, c, q, o, e, a, arm, stats, VT, gen1)
    audit_row[9] = stats[2] - enc0
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
def chunk(na, nc, g0, g1, counts, audit, n, k, b, c, q, o, e, a, s, mu, arm, stats, stats_g1, VT):
    """Generations g0..g1-1 (0-based); writes counts[g + 1] and audit[g]."""
    for g in range(g0, g1):
        st = stats_g1 if g == 0 else stats
        na, nc = generation(na, nc, n, k, b, c, q, o, e, a, s, mu, arm, st, audit[g], VT, g == 0)
        counts[g + 1, 0] = na
        counts[g + 1, 1] = nc
    return na, nc


def run(q, o, e, a, mu, start, arm, seed, gens=2000, n=N, k=K, b=B, c=C, s=S, heartbeat=None, every=100):
    """start = (ALLC, DISC, ALLD). Returns (counts [ALLD, ALLC] per generation, audit, stats gens 2.., stats gen 1).
    heartbeat(g) is called every `every` generations (from Python; the random stream continues across chunks)."""
    if s * c >= 1.0:
        raise ValueError("fitness could become non-positive")
    if not (0.0 < o <= 1.0 and 0.0 <= e < 1.0 and 0.0 <= a < 0.5 and 0.0 <= mu < 1.0):
        raise ValueError("bad parameters")
    xc, xd, xa = start
    if abs(xc + xd + xa - 1.0) > 1e-9:
        raise ValueError("start shares must sum to 1")
    _seed(seed)
    stats, stats_g1 = np.zeros(NST), np.zeros(NST)
    counts = np.empty((gens + 1, 2), np.int64)
    audit = np.zeros((gens, 10), np.int64)
    na, nc = int(round(xa * n)), int(round(xc * n))
    counts[0, 0], counts[0, 1] = na, nc
    VT = np.ones((n, n), np.uint8)
    for g0 in range(0, gens, every):
        g1 = min(gens, g0 + every)
        na, nc = chunk(na, nc, g0, g1, counts, audit, n, k, b, c, q, o, e, a, s, float(mu), arm, stats, stats_g1, VT)
        if heartbeat is not None:
            heartbeat(g1)
    return counts, audit, stats, stats_g1
