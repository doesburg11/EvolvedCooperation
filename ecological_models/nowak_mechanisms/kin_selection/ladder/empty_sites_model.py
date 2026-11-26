"""Individual-based empty-site island model after Alizon and Taylor (2008), for STEP5_EMPTY_SITES.md.

P patches of n sites, each empty or holding one asexual breeder. Continuous time, exact stochastic simulation with
thinning:
  * every breeder dies at rate k (trait-independent);
  * breeder j attempts a birth at rate f_j = 1 - c*h_j + (gifts received by j); candidates are drawn uniformly
    among breeders and accepted with probability f_j / f_max;
  * the offspring stays in the parent's patch if that patch holds at most `stay_max` breeders (the paper's ESS
    switch at n = 10, k = 0.5: stay if i <= 5), otherwise it goes to a uniformly random patch (own included); it
    lands on a uniformly random site of that patch and settles only if the site is empty (else it dies);
  * clonal inheritance: h mutates with probability mu by N(0, sd) clipped to [0, 1]; a neutral marker mutates to a
    new unique value with probability u; every breeder has a unique id and its parent's id.

Gift modes (each donor d gives b*h_d in total, shared equally among its eligible recipients; with none it is lost;
the cost c*h_d is always paid):
  0 none     -- no gift (N0, with b = c = 0)
  1 patch    -- the other breeders of d's patch (T14, T3.5)
  2 nonoff   -- the other breeders of d's patch that are not d's own offspring (NO14)
  3 global   -- all other breeders in the population, equally (mean-field; X14)
  4 classpool -- control of STEP5_NONOFFSPRING.md: a donor with at least one eligible (`nonoff`) patch-mate puts its
                 gift into the pool of its patch class i (breeders in its patch); breeder j in class-i patch p receives
                 (D_i - D_p) / (i * (PC_i - 1)), with D_p the summed b*h of p's eligible donors, D_i the sum over
                 class-i patches and PC_i their number; with PC_i = 1 the class's gifts are lost.

Optional gift-route statistics (route=True, STEP5_NONOFFSPRING.md) use their own xorshift random stream, so
recording them never changes the main stream: a run is identical with and without them.
"""

from __future__ import annotations

import numpy as np
from numba import njit

NONE, PATCH, NONOFF, GLOBAL, CLASSPOOL = 0, 1, 2, 3, 4


@njit(cache=True)
def _seed(s):
    np.random.seed(s)


@njit(cache=True)
def _target(cnt_parent, stay_max, pj, P):
    """Destination patch of an offspring: home if the parent's patch holds at most stay_max breeders."""
    if cnt_parent <= stay_max:
        return pj
    return np.random.randint(0, P)


@njit(cache=True)
def _recompute_patch(p, n, occ, h, ident, parent, gift, b, mode):
    """Gift received by each breeder of patch p (modes PATCH and NONOFF)."""
    base = p * n
    for q in range(n):
        gift[base + q] = 0.0
    if mode == PATCH:
        i = 0
        H = 0.0
        for q in range(n):
            if occ[base + q]:
                i += 1
                H += h[base + q]
        if i > 1:
            for q in range(n):
                if occ[base + q]:
                    gift[base + q] = b * (H - h[base + q]) / (i - 1)
    elif mode == NONOFF:
        for qd in range(n):
            d = base + qd
            if not occ[d] or h[d] == 0.0:
                continue
            e = 0
            for qr in range(n):
                r = base + qr
                if r != d and occ[r] and parent[r] != ident[d]:
                    e += 1
            if e == 0:
                continue
            share = b * h[d] / e
            for qr in range(n):
                r = base + qr
                if r != d and occ[r] and parent[r] != ident[d]:
                    gift[r] += share


@njit(cache=True)
def _eligible_sum(p, n, occ, h, ident, parent, b):
    """Summed gift b*h of patch p's donors that have at least one eligible (non-offspring) patch-mate."""
    base = p * n
    D = 0.0
    for qd in range(n):
        d = base + qd
        if not occ[d] or h[d] == 0.0:
            continue
        for qr in range(n):
            r = base + qr
            if r != d and occ[r] and parent[r] != ident[d]:
                D += b * h[d]
                break
    return D


@njit(cache=True)
def _pool_gift(p, i, Dp, Dcls, PC):
    """Gift received by each breeder of patch p (class i) under CLASSPOOL."""
    if i < 1 or PC[i] < 2:
        return 0.0
    g = (Dcls[i] - Dp[p]) / (i * (PC[i] - 1))
    return g if g > 0.0 else 0.0


@njit(cache=True)
def _xs(state):
    """xorshift64* step on state[0]; returns a uniform integer in [0, 2**62)."""
    x = state[0]
    x ^= x >> np.uint64(12)
    x ^= x << np.uint64(25)
    x ^= x >> np.uint64(27)
    state[0] = x
    return np.int64((x * np.uint64(2685821657736338717)) >> np.uint64(2))


@njit(cache=True)
def _route(P, n, occ, h, ident, parent, marker, cnt, b, mode, olist, Nocc, PC, rstate, out_row, k0):
    """Gift-route statistics into out_row[k0:k0 + 7]: [sum of delivered gift g_d, sum g_d * q_d, sum g_d * q_ref_d,
    share of all gifts lost for want of an eligible patch-mate, share lost to a singleton class, share of donors'
    patch-mates that are their own offspring, (unused here)]. q_d: marker identity with the recipients (NONOFF: mean
    over eligible patch-mates; CLASSPOOL: mean over 10 breeders drawn from other patches of the donor's class);
    q_ref_d: identity with 10 breeders drawn uniformly from all patches other than the donor's."""
    for t in range(7):
        out_row[k0 + t] = np.nan
    if Nocc == 0 or (mode != NONOFF and mode != CLASSPOOL):
        return
    # patches by class, for CLASSPOOL recipient draws
    cls_start = np.zeros(n + 2, np.int64)
    for p in range(P):
        cls_start[cnt[p] + 1] += 1
    for i in range(1, n + 2):
        cls_start[i] += cls_start[i - 1]
    fill = cls_start.copy()
    by_cls = np.empty(P, np.int64)
    for p in range(P):
        by_cls[fill[cnt[p]]] = p
        fill[cnt[p]] += 1
    wsum = 0.0
    wq = 0.0
    wref = 0.0
    g_tot = 0.0
    lost_local = 0.0
    lost_single = 0.0
    own = 0.0
    mates = 0.0
    for p in range(P):
        i = cnt[p]
        if i == 0:
            continue
        base = p * n
        for qd in range(n):
            d = base + qd
            if not occ[d]:
                continue
            e = 0
            same_e = 0
            for qr in range(n):
                r = base + qr
                if r != d and occ[r]:
                    mates += 1.0
                    if parent[r] == ident[d]:
                        own += 1.0
                    else:
                        e += 1
                        if marker[r] == marker[d]:
                            same_e += 1
            give = b * h[d]
            if give <= 0.0:
                continue
            g_tot += give
            if e == 0:
                lost_local += give
                continue
            if mode == CLASSPOOL and PC[i] < 2:
                lost_single += give
                continue
            if mode == NONOFF:
                q = same_e / e
            else:
                hits = 0
                for _ in range(10):
                    while True:
                        pr = by_cls[cls_start[i] + _xs(rstate) % PC[i]]
                        if pr != p:
                            break
                    # every class-i patch holds exactly i breeders: draw one of them uniformly
                    kth = _xs(rstate) % i
                    for qr in range(n):
                        r = pr * n + qr
                        if occ[r]:
                            if kth == 0:
                                if marker[r] == marker[d]:
                                    hits += 1
                                break
                            kth -= 1
                q = hits / 10.0
            if Nocc - i == 0:          # no breeder outside the donor's patch: no reference, skip this donor
                continue
            hr = 0
            for _ in range(10):
                while True:
                    r = olist[_xs(rstate) % Nocc]
                    if r // n != p:
                        break
                if marker[r] == marker[d]:
                    hr += 1
            wsum += give
            wq += give * q
            wref += give * (hr / 10.0)
    out_row[k0] = wsum
    out_row[k0 + 1] = wq
    out_row[k0 + 2] = wref
    out_row[k0 + 3] = lost_local / g_tot if g_tot > 0 else np.nan
    out_row[k0 + 4] = lost_single / g_tot if g_tot > 0 else np.nan
    out_row[k0 + 5] = own / mates if mates > 0 else np.nan


@njit(cache=True)
def _sample(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, b, c, mode, Hglob, Nocc, nb_pairs, out_row, hist,
            Dp, Dcls, PC):
    """Fill out_row with [N, mean h, var h, occupancy, mean fecundity, Q_w, Q_b, own-offspring gift share,
    lost gift share, Q_w(i=6), Q_w(i=7), between-patch pairs drawn, ordered pairs in i=6 patches, in i=7
    patches, all ordered patch-mate pairs] and hist with the patch-type counts."""
    for i in range(n + 1):
        hist[i] = 0
    if Nocc == 0:
        for t in range(out_row.shape[0]):
            out_row[t] = np.nan
        out_row[0] = 0.0
        out_row[3] = 0.0
        hist[0] = P
        return
    s = 0.0
    s2 = 0.0
    fsum = 0.0
    same = 0.0
    pairs = 0.0
    same6 = 0.0
    pairs6 = 0.0
    same7 = 0.0
    pairs7 = 0.0
    g_tot = 0.0
    g_off = 0.0
    g_lost = 0.0
    for p in range(P):
        base = p * n
        i = cnt[p]
        hist[i] += 1
        for q in range(n):
            j = base + q
            if not occ[j]:
                continue
            s += h[j]
            s2 += h[j] * h[j]
            if mode == GLOBAL:
                g = b * (Hglob - h[j]) / (Nocc - 1) if Nocc > 1 else 0.0
            elif mode == PATCH:
                g = b * (Hp[p] - h[j]) / (i - 1) if i > 1 else 0.0
            elif mode == CLASSPOOL:
                g = _pool_gift(p, i, Dp, Dcls, PC)
            else:
                g = gift[j]
            fsum += 1.0 - c * h[j] + g
            for q2 in range(n):
                j2 = base + q2
                if q2 != q and occ[j2]:
                    sm = 1.0 if marker[j] == marker[j2] else 0.0
                    same += sm
                    pairs += 1.0
                    if i == 6:
                        same6 += sm
                        pairs6 += 1.0
                    elif i == 7:
                        same7 += sm
                        pairs7 += 1.0
            # gift accounting for donor j
            give = b * h[j]
            if give > 0.0:
                g_tot += give
                if mode == PATCH or mode == NONOFF or mode == CLASSPOOL:
                    e = 0
                    off = 0
                    for q2 in range(n):
                        j2 = base + q2
                        if q2 != q and occ[j2]:
                            if parent[j2] == ident[j]:
                                off += 1
                                if mode == PATCH:
                                    e += 1
                            else:
                                e += 1
                    if e == 0:
                        g_lost += give
                    elif mode == CLASSPOOL and PC[i] < 2:
                        g_lost += give
                    elif mode == PATCH:
                        g_off += give * off / e
                elif mode == GLOBAL and Nocc == 1:
                    g_lost += give
    # between-patch identity from random pairs of occupied sites in different patches
    sameb = 0.0
    nb = 0
    tries = 0
    while nb < nb_pairs and tries < 1000 * nb_pairs:
        tries += 1
        a = np.random.randint(0, P * n)
        z = np.random.randint(0, P * n)
        if not occ[a] or not occ[z] or a // n == z // n:
            continue
        nb += 1
        if marker[a] == marker[z]:
            sameb += 1.0
    N = float(Nocc)
    m = s / N
    out_row[0] = N
    out_row[1] = m
    out_row[2] = s2 / N - m * m
    out_row[3] = N / (P * n)
    out_row[4] = fsum / N
    out_row[5] = same / pairs if pairs > 0 else np.nan
    out_row[6] = sameb / nb if nb > 0 else np.nan
    out_row[7] = g_off / g_tot if g_tot > 0 else np.nan
    out_row[8] = g_lost / g_tot if g_tot > 0 else np.nan
    out_row[9] = same6 / pairs6 if pairs6 > 0 else np.nan
    out_row[10] = same7 / pairs7 if pairs7 > 0 else np.nan
    out_row[11] = nb
    out_row[12] = pairs6
    out_row[13] = pairs7
    out_row[14] = pairs


@njit(cache=True)
def _sample_all(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, b, c, mode, Hglob, Nocc, nb_pairs, row, hist,
                Dp, Dcls, PC, olist, route, rstate):
    """One sample: the step-5 statistics (columns 0-14, same random draws as before), then, for CLASSPOOL, the
    largest gap between the incrementally kept class sums and a full rebuild (column 22, after which the class
    sums are replaced by the rebuild), then the gift-route statistics (columns 15-21) if route is set."""
    _sample(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, b, c, mode, Hglob, Nocc, nb_pairs, row, hist,
            Dp, Dcls, PC)
    row[22] = np.nan
    if mode == CLASSPOOL:
        err = 0.0
        Dn = np.zeros(n + 1)
        PCn = np.zeros(n + 1, np.int64)
        for p in range(P):
            Dx = _eligible_sum(p, n, occ, h, ident, parent, b)
            err = max(err, abs(Dx - Dp[p]))
            Dp[p] = Dx
            Dn[cnt[p]] += Dx
            PCn[cnt[p]] += 1
        for i in range(n + 1):
            err = max(err, abs(Dn[i] - Dcls[i]))
            if PCn[i] != PC[i]:
                err = max(err, 1e9)
            Dcls[i] = Dn[i]
        row[22] = err
    if route:
        _route(P, n, occ, h, ident, parent, marker, cnt, b, mode, olist, Nocc, PC, rstate, row, 15)
    else:
        for t in range(15, 22):
            row[t] = np.nan


@njit(cache=True)
def simulate(P, n, k, b, c, mode, stay_max, mu, sd, u, T, sample_dt, occ, h, ident, parent, marker, nb_pairs,
             out, hists, counters, route, rstate):
    """Run from the given state to time T. out: (n_samples, len(COLS)); hists: (n_samples, n + 1).
    counters: [events, births settled, next id, next marker, final time]. route: record gift-route statistics
    (own random stream rstate, a uint64 array of length 1). Returns number of samples written."""
    S = P * n
    gift = np.zeros(S)
    cnt = np.zeros(P, np.int64)
    Hp = np.zeros(P)
    olist = np.empty(S, np.int64)
    pos = np.full(S, -1, np.int64)
    Nocc = 0
    Hglob = 0.0
    for j in range(S):
        if occ[j]:
            cnt[j // n] += 1
            Hp[j // n] += h[j]
            olist[Nocc] = j
            pos[j] = Nocc
            Nocc += 1
            Hglob += h[j]
    if mode == NONOFF:
        for p in range(P):
            _recompute_patch(p, n, occ, h, ident, parent, gift, b, mode)
    Dp = np.zeros(P)
    Dcls = np.zeros(n + 1)
    PC = np.zeros(n + 1, np.int64)
    for p in range(P):
        PC[cnt[p]] += 1
    if mode == CLASSPOOL:
        for p in range(P):
            Dp[p] = _eligible_sum(p, n, occ, h, ident, parent, b)
            Dcls[cnt[p]] += Dp[p]
    if mode == NONOFF:
        fmax = 1.0 + b * (n - 1)
    else:
        fmax = 1.0 + b
    next_id = int(counters[2])
    next_marker = int(counters[3])
    events = 0
    births = 0
    t = 0.0
    ns = out.shape[0]
    si = 0
    row = np.empty(out.shape[1])
    hist = np.empty(n + 1, np.int64)
    pdeath = k / (k + fmax)
    while si < ns:
        if Nocc == 0:
            while si < ns:
                _sample_all(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, b, c, mode, Hglob, Nocc, nb_pairs, row,
                            hist, Dp, Dcls, PC, olist, route, rstate)
                out[si, :] = row
                hists[si, :] = hist
                si += 1
            break
        dt = -np.log(1.0 - np.random.random()) / (Nocc * (k + fmax))
        # samples at times si * sample_dt that fall before the next event see the current state
        while si < ns and si * sample_dt <= t + dt:
            _sample_all(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, b, c, mode, Hglob, Nocc, nb_pairs, row,
                            hist, Dp, Dcls, PC, olist, route, rstate)
            out[si, :] = row
            hists[si, :] = hist
            si += 1
        if si >= ns:
            break
        t += dt
        events += 1
        j = olist[np.random.randint(0, Nocc)]
        if np.random.random() < pdeath:
            # death of j
            pj = j // n
            if mode == CLASSPOOL:
                Dcls[cnt[pj]] -= Dp[pj]
            PC[cnt[pj]] -= 1
            occ[j] = False
            Hglob -= h[j]
            cnt[pj] -= 1
            PC[cnt[pj]] += 1
            Hp[pj] -= h[j]
            last = olist[Nocc - 1]
            olist[pos[j]] = last
            pos[last] = pos[j]
            pos[j] = -1
            Nocc -= 1
            if mode == NONOFF:
                _recompute_patch(pj, n, occ, h, ident, parent, gift, b, mode)
            elif mode == CLASSPOOL:
                Dp[pj] = _eligible_sum(pj, n, occ, h, ident, parent, b)
                Dcls[cnt[pj]] += Dp[pj]
            continue
        # birth candidate j
        pj = j // n
        if mode == GLOBAL:
            g = b * (Hglob - h[j]) / (Nocc - 1) if Nocc > 1 else 0.0
        elif mode == PATCH:
            g = b * (Hp[pj] - h[j]) / (cnt[pj] - 1) if cnt[pj] > 1 else 0.0
        elif mode == CLASSPOOL:
            g = _pool_gift(pj, cnt[pj], Dp, Dcls, PC)
        else:
            g = gift[j]
        f = 1.0 - c * h[j] + g
        if np.random.random() * fmax >= f:
            continue
        target = _target(cnt[pj], stay_max, pj, P)
        site = target * n + np.random.randint(0, n)
        if occ[site]:
            continue
        hv = h[j]
        if np.random.random() < mu:
            hv = hv + sd * np.random.standard_normal()
            if hv < 0.0:
                hv = 0.0
            elif hv > 1.0:
                hv = 1.0
        mk = marker[j]
        if np.random.random() < u:
            mk = next_marker
            next_marker += 1
        if mode == CLASSPOOL:
            Dcls[cnt[target]] -= Dp[target]
        PC[cnt[target]] -= 1
        occ[site] = True
        h[site] = hv
        marker[site] = mk
        parent[site] = ident[j]
        ident[site] = next_id
        next_id += 1
        cnt[target] += 1
        PC[cnt[target]] += 1
        Hp[target] += hv
        olist[Nocc] = site
        pos[site] = Nocc
        Nocc += 1
        Hglob += hv
        births += 1
        if mode == NONOFF:
            _recompute_patch(target, n, occ, h, ident, parent, gift, b, mode)
        elif mode == CLASSPOOL:
            Dp[target] = _eligible_sum(target, n, occ, h, ident, parent, b)
            Dcls[cnt[target]] += Dp[target]
    counters[0] = events
    counters[1] = births
    counters[2] = next_id
    counters[3] = next_marker
    counters[4] = t
    return si


COLS = ("N", "mean_h", "var_h", "occupancy", "mean_f", "Qw", "Qb", "gift_own_offspring", "gift_lost", "Qw6", "Qw7",
        "Qb_pairs", "pairs6", "pairs7", "pairs",
        "route_w", "route_wq", "route_wqref", "lost_local", "lost_single", "own_mate_share", "unused", "cache_err")


def run(*, seed, b, c, mode, T, sample_dt, P=1000, n=10, k=0.5, stay_max=5, mu=0.02, sd=0.04, u=0.001,
        h0_mean=0.05, h0_sd=0.02, h_fixed=None, occ0=0.5, nb_pairs=100_000, chunk_T=10_000.0, progress=None,
        route=False):
    """One run. Returns dict(samples=(n_samples, len(COLS)) array, hists=(n_samples, n + 1), times, events,
    births). Simulated in chunks of chunk_T time units (the event clock restarts at each chunk boundary, which is
    exact because waiting times are exponential); progress(t_reached, N) is called after each chunk.
    h_fixed: set every founder's h to this value (pass mu = 0 to keep it)."""
    for x in (T, chunk_T):
        if abs(x / sample_dt - round(x / sample_dt)) > 1e-9:
            raise ValueError("T and chunk_T must be multiples of sample_dt")
    rng = np.random.default_rng(seed)
    S = P * n
    occ = rng.random(S) < occ0
    if h_fixed is None:
        h = np.clip(rng.normal(h0_mean, h0_sd, S), 0.0, 1.0)
    else:
        h = np.full(S, float(h_fixed))
    h[~occ] = 0.0
    ident = np.arange(S, dtype=np.int64)
    parent = np.full(S, -1, np.int64)
    marker = np.arange(S, dtype=np.int64)
    counters = np.array([0.0, 0.0, float(S), float(S), 0.0])
    _seed(seed + 7_000_001)
    rstate = np.array([((int(seed) * 0x9E3779B97F4A7C15 + 0x632BE59BD9B4E019) % 2 ** 64) or 1], np.uint64)
    samples, hists = [], []
    events = births = 0
    t_done = 0.0
    first = True
    while t_done < T - 1e-9:
        ct = min(chunk_T, T - t_done)
        ns = int(round(ct / sample_dt)) + 1
        out = np.empty((ns, len(COLS)))
        hs = np.empty((ns, n + 1), np.int64)
        simulate(int(P), int(n), float(k), float(b), float(c), int(mode), int(stay_max), float(mu), float(sd),
                 float(u), float(ct), float(sample_dt), occ, h, ident, parent, marker, int(nb_pairs), out, hs, counters,
                 bool(route), rstate)
        samples.append(out if first else out[1:])
        hists.append(hs if first else hs[1:])
        first = False
        events += int(counters[0])
        births += int(counters[1])
        t_done += ct
        if progress is not None:
            progress(t_done, int(occ.sum()))
    samples = np.concatenate(samples)
    hists = np.concatenate(hists)
    return dict(samples=samples, hists=hists, events=events, births=births,
                times=np.arange(len(samples)) * sample_dt)
