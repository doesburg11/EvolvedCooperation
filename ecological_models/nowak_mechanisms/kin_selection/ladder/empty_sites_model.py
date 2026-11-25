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
"""

from __future__ import annotations

import numpy as np
from numba import njit

NONE, PATCH, NONOFF, GLOBAL = 0, 1, 2, 3


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
def _sample(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, b, c, mode, Hglob, Nocc, nb_pairs, out_row, hist):
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
                if mode == PATCH or mode == NONOFF:
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
def simulate(P, n, k, b, c, mode, stay_max, mu, sd, u, T, sample_dt, occ, h, ident, parent, marker, nb_pairs,
             out, hists, counters):
    """Run from the given state to time T. out: (n_samples, 11); hists: (n_samples, n + 1).
    counters: [events, births settled, next id, next marker, final time]. Returns number of samples written."""
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
                _sample(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, b, c, mode, Hglob, Nocc, nb_pairs, row, hist)
                out[si, :] = row
                hists[si, :] = hist
                si += 1
            break
        dt = -np.log(1.0 - np.random.random()) / (Nocc * (k + fmax))
        # samples at times si * sample_dt that fall before the next event see the current state
        while si < ns and si * sample_dt <= t + dt:
            _sample(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, b, c, mode, Hglob, Nocc, nb_pairs, row, hist)
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
            occ[j] = False
            Hglob -= h[j]
            pj = j // n
            cnt[pj] -= 1
            Hp[pj] -= h[j]
            last = olist[Nocc - 1]
            olist[pos[j]] = last
            pos[last] = pos[j]
            pos[j] = -1
            Nocc -= 1
            if mode == NONOFF:
                _recompute_patch(pj, n, occ, h, ident, parent, gift, b, mode)
            continue
        # birth candidate j
        pj = j // n
        if mode == GLOBAL:
            g = b * (Hglob - h[j]) / (Nocc - 1) if Nocc > 1 else 0.0
        elif mode == PATCH:
            g = b * (Hp[pj] - h[j]) / (cnt[pj] - 1) if cnt[pj] > 1 else 0.0
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
        occ[site] = True
        h[site] = hv
        marker[site] = mk
        parent[site] = ident[j]
        ident[site] = next_id
        next_id += 1
        cnt[target] += 1
        Hp[target] += hv
        olist[Nocc] = site
        pos[site] = Nocc
        Nocc += 1
        Hglob += hv
        births += 1
        if mode == NONOFF:
            _recompute_patch(target, n, occ, h, ident, parent, gift, b, mode)
    counters[0] = events
    counters[1] = births
    counters[2] = next_id
    counters[3] = next_marker
    counters[4] = t
    return si


COLS = ("N", "mean_h", "var_h", "occupancy", "mean_f", "Qw", "Qb", "gift_own_offspring", "gift_lost", "Qw6", "Qw7",
        "Qb_pairs", "pairs6", "pairs7", "pairs")


def run(*, seed, b, c, mode, T, sample_dt, P=1000, n=10, k=0.5, stay_max=5, mu=0.02, sd=0.04, u=0.001,
        h0_mean=0.05, h0_sd=0.02, h_fixed=None, occ0=0.5, nb_pairs=100_000, chunk_T=10_000.0, progress=None):
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
                 float(u), float(ct), float(sample_dt), occ, h, ident, parent, marker, int(nb_pairs), out, hs, counters)
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
