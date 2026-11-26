"""Theory screen for rung 1 of the kin-ladder close-out (2026-11-26): help to non-offspring patch-mates in the
empty-site islands (the NO arm of STEP5_EMPTY_SITES.md, gift mode `nonoff`).

The island theory (at_breakeven.py) has no genealogy, so it cannot split patch relatedness into own offspring and
others. This script measures, in fixed-trait runs of the step-5 model (h fixed, no h mutation, so nothing evolves
and no test arm is run), per patch class i = number of breeders:
  * L_i: share of donors with no eligible recipient (only own offspring, or alone): their gift is lost;
  * R_non_i: gift-weighted relatedness of a donor to its eligible (non-offspring) patch-mates,
    R = (Q - Q_b) / (1 - Q_b) from the neutral marker, as in Stage 0;
  * R_all_i: the same for all patch-mates (the T rule), to check the plug-in against the analytic G_i.
These are plugged into the analytic break-even: W_i = b (1 - L_i) (R_i A_i + B_i) - c (A_i + B_i), with demography
and reproductive values solved at the resident (fecundity F_i = 1 - c h + b h (1 - L_i)). The B term (the effect of
extra local births on the patch's reproductive value) does not depend on who receives the gift, only on whether it
is delivered.

Usage: python -m ecological_models.nowak_mechanisms.kin_selection.ladder.theory.no_offspring_screen
"""

from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.optimize import fsolve

N_SITES, K, STAY_MAX, C = 10, 0.5, 5, 0.005
BURN, MEASURE, DT = 10_000.0, 20_000.0, 200.0
SEEDS = (950, 951)
BC_LEVELS = (5, 14, 20, 28, 40)
H_LEVELS = (0.0, 0.05, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0)
NB_PAIRS = 20_000
OUT = Path(__file__).with_name("no_offspring_screen_output.json")


# ---------------------------------------------------------------- analytic parts (from at_breakeven.py)
def solve_parts(n, k, m, F):
    """Demography, reproductive values and consanguinity at fecundities F (index = patch class). Returns the
    per-class pieces of the inclusive-fitness effect: weight w_i, A_i, B_i and analytic G_i."""
    x = np.arange(n + 1) / n
    hh = 1 - m
    p = np.ones(n + 1) / (n + 1)
    for _ in range(4000):
        S = np.sum(x * m * p * F)
        Q = np.zeros((n + 1, n + 1))
        for i in range(n + 1):
            if i < n:
                Q[i, i + 1] = (n - i) * (S + x[i] * hh[i] * F[i])
            if i > 0:
                Q[i, i - 1] = i * k
        Q -= np.diag(Q.sum(1))
        pn = np.linalg.lstsq(np.vstack([Q.T, np.ones(n + 1)]), np.r_[np.zeros(n + 1), 1.0], rcond=None)[0]
        if np.max(abs(pn - p)) < 1e-15:
            break
        p = 0.5 * p + 0.5 * pn
    S = np.sum(x * m * p * F)

    def dv(vt):
        V = np.r_[0.0, 1.0, vt, 0.0]
        fo = sum((1 - x[j]) * p[j] * V[j + 1] for j in range(n))
        out = []
        for i in range(1, n + 1):
            e = 1 - x[i]
            out.append(-k * V[i] + (i - 1) * k * (V[i - 1] - V[i]) + F[i] * hh[i] * e * (2 * V[i + 1] - V[i])
                       + (i - 1) * F[i] * hh[i] * e * (V[i + 1] - V[i]) + F[i] * m[i] * fo
                       + n * e * S * (V[i + 1] - V[i]))
        return np.array(out[1:])

    V = np.r_[0.0, 1.0, fsolve(dv, np.ones(n - 1), xtol=1e-13), 0.0]
    al = np.array([(n - i + 1) * F[i - 1] * hh[i - 1] * x[i - 1] * p[i - 1] if i >= 1 else 0 for i in range(n + 1)])
    be = np.array([(n - i + 1) * S * p[i - 1] if i >= 1 else 0 for i in range(n + 1)])
    ga = np.array([(i + 1) * k * p[i + 1] if i < n else 0 for i in range(n + 1)])
    M = np.zeros((n + 1, n + 1))
    r = np.zeros(n + 1)
    for i in range(2, n + 1):
        M[i, i] = al[i] + be[i] + ga[i]
        r[i] = al[i] * 2 / (i * (i - 1))
        if i >= 3:
            M[i, i - 1] -= al[i] * (i * i - i - 2) / (i * (i - 1)) + be[i] * (i - 2) / i
        if i < n:
            M[i, i + 1] -= ga[i]
    G = np.zeros(n + 1)
    G[2:] = np.linalg.solve(M[2:, 2:], r[2:])
    fo = sum((1 - x[j]) * p[j] * V[j + 1] for j in range(n))
    w, A, B = np.zeros(n + 1), np.zeros(n + 1), np.zeros(n + 1)
    for i in range(1, n + 1):
        A[i] = hh[i] * (1 - x[i]) * V[i + 1] + m[i] * fo
        B[i] = (1 + (i - 1) * (G[i] if i >= 2 else 0)) * hh[i] * (1 - x[i]) * (V[i + 1] - V[i])
        w[i] = x[i] * p[i]
    vbar = np.sum(w[1:] * V[1:n + 1]) / w[1:].sum()
    return dict(w=w, A=A, B=B, G=G, p=p, vbar=vbar, occ=float(np.sum(x * p)))


def breakeven(parts, R, L):
    """Population break-even c/b and the per-unit-h gradient pieces with relatedness R_i and loss L_i (L_1 = 1)."""
    w, A, B = parts["w"], parts["A"], parts["B"]
    alpha = sum(w[i] * (1 - L[i]) * (R[i] * A[i] + B[i]) for i in range(2, N_SITES + 1))
    beta = sum(w[i] * (A[i] + B[i]) for i in range(1, N_SITES + 1))
    return alpha / beta, alpha / w[1:].sum(), beta / w[1:].sum()


# ---------------------------------------------------------------- measurement in the step-5 model
def measure(args):
    mode_name, bc, hres, seed = args
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
    mode = {"patch": E.PATCH, "nonoff": E.NONOFF}[mode_name]
    b = bc * C
    P, n = 1000, N_SITES
    S = P * n
    rng = np.random.default_rng(seed)
    occ = rng.random(S) < 0.5
    h = np.where(occ, hres, 0.0)
    ident = np.arange(S, dtype=np.int64)
    parent = np.full(S, -1, np.int64)
    marker = np.arange(S, dtype=np.int64)
    counters = np.array([0.0, 0.0, float(S), float(S), 0.0])
    E._seed(seed + 7_000_001)
    out = np.empty((2, len(E.COLS)))
    hs = np.empty((2, n + 1), np.int64)
    acc = {key: np.zeros(n + 1) for key in ("donors", "lost", "Rq_non", "Rq_all", "own_pairs", "pairs")}
    qb_hits = qb_pairs = 0
    nsnap = 0
    occ_sum = 0.0
    t, t_end = 0.0, BURN + MEASURE
    while t < t_end - 1e-9:
        E.simulate(P, n, K, b, C, mode, STAY_MAX, 0.0, 0.04, 0.001, DT, DT, occ, h, ident, parent, marker,
                   1000, out, hs, counters, False, np.array([1], np.uint64))
        t += DT
        if t <= BURN + 1e-9:
            continue
        nsnap += 1
        occ_sum += float(occ.mean())
        o = occ.reshape(P, n)
        mk = marker.reshape(P, n)
        idn = ident.reshape(P, n)
        par = parent.reshape(P, n)
        cnt = o.sum(1)
        both = o[:, :, None] & o[:, None, :]
        np.einsum("pii->pi", both)[:] = False                     # no self pairs
        same = mk[:, :, None] == mk[:, None, :]
        offspring = par[:, None, :] == idn[:, :, None]            # recipient j is donor i's own offspring
        elig = both & ~offspring
        ne = elig.sum(2)
        na = both.sum(2)
        r_non = np.where(ne > 0, (same & elig).sum(2) / np.maximum(ne, 1), 0.0)
        r_all = np.where(na > 0, (same & both).sum(2) / np.maximum(na, 1), 0.0)
        own = (both & offspring).sum(2)
        cls = np.broadcast_to(cnt[:, None], o.shape)
        for i in range(1, n + 1):
            sel = o & (cls == i)
            acc["donors"][i] += sel.sum()
            acc["lost"][i] += (sel & (ne == 0)).sum()
            acc["Rq_non"][i] += r_non[sel & (ne > 0)].sum()
            acc["Rq_all"][i] += r_all[sel & (na > 0)].sum()
            acc["own_pairs"][i] += own[sel].sum()
            acc["pairs"][i] += na[sel].sum()
        # between-patch identity from random pairs of breeders in different patches
        live = np.flatnonzero(occ)
        a = live[rng.integers(0, len(live), NB_PAIRS)]
        c2 = live[rng.integers(0, len(live), NB_PAIRS)]
        keep = (a // n) != (c2 // n)
        qb_hits += int((marker[a[keep]] == marker[c2[keep]]).sum())
        qb_pairs += int(keep.sum())
    return dict(mode=mode_name, bc=bc, h=hres, seed=seed, snapshots=nsnap, qb_hits=qb_hits, qb_pairs=qb_pairs,
                occupancy=occ_sum / nsnap, **{key: v.tolist() for key, v in acc.items()})


def pooled(rows):
    """Pool seeds: per class L_i, R_non_i, R_all_i (relatedness from identity with pooled Q_b), own-offspring share."""
    tot = {key: np.sum([r[key] for r in rows], 0) for key in ("donors", "lost", "Rq_non", "Rq_all", "own_pairs", "pairs")}
    qb = sum(r["qb_hits"] for r in rows) / sum(r["qb_pairs"] for r in rows)
    d = np.maximum(tot["donors"], 1)
    delivered = np.maximum(tot["donors"] - tot["lost"], 1)
    L = tot["lost"] / d
    L[1] = 1.0
    Qn = tot["Rq_non"] / delivered
    Qa = tot["Rq_all"] / np.maximum(tot["donors"] - (np.arange(N_SITES + 1) == 1) * tot["donors"], 1)
    Rn = (Qn - qb) / (1 - qb)
    Ra = (Qa - qb) / (1 - qb)
    Rn[:2] = Ra[:2] = 0.0
    own_share = tot["own_pairs"] / np.maximum(tot["pairs"], 1)
    return L, Rn, Ra, own_share, qb, float(np.mean([r["occupancy"] for r in rows]))


def main():
    jobs = [("nonoff", 14, 0.0, s) for s in SEEDS]
    jobs += [("nonoff", bc, hres, s) for bc in BC_LEVELS for hres in H_LEVELS[1:] for s in SEEDS]
    jobs += [("patch", 14, hres, s) for hres in (0.0, 0.6, 1.0) for s in SEEDS]
    with Pool(min(16, len(jobs))) as pool:
        rows = pool.map(measure, jobs)
    OUT.write_text(json.dumps(rows))
    m = np.array([0.0 if i <= STAY_MAX else 1.0 for i in range(N_SITES + 1)])

    def group(mode, bc, hres):
        sel = [r for r in rows if r["mode"] == mode and r["h"] == hres and (hres == 0.0 or r["bc"] == bc)]
        return pooled(sel)

    print("== Check: T rule, measured R_all_i against the analytic G_i, and the plug-in break-even (b/c 14)")
    for hres in (0.0, 0.6, 1.0):
        L0, _, Ra, own, qb, occ = group("patch", 14, hres)
        b = 14 * C
        F = np.r_[0.0, 1 - C * hres, np.full(N_SITES - 1, 1 + (b - C) * hres)]
        parts = solve_parts(N_SITES, K, m, F)
        zero = np.zeros(N_SITES + 1)
        zero[1] = 1.0
        cb_an, _, _ = breakeven(parts, parts["G"], zero)
        cb_pl, _, _ = breakeven(parts, Ra, zero)
        print(f"h={hres}: occupancy sim {occ:.3f} theory {parts['occ']:.3f}; R_all 2..10 {np.round(Ra[2:], 3)}; "
              f"analytic G {np.round(parts['G'][2:], 3)}; break-even analytic {cb_an:.4f}, plug-in {cb_pl:.4f}")

    print("\n== NO rule (own offspring excluded): break-even c/b and selection gradient per unit h per time unit")
    L0, Rn0, Ra0, own0, qb0, occ0 = group("nonoff", 14, 0.0)
    print(f"neutral (h = 0): loss L_i 1..10 {np.round(L0[1:], 3)}; own-offspring share of patch-mate pairs "
          f"{np.round(own0[2:], 3)}; R_non 2..10 {np.round(Rn0[2:], 3)}; R_all {np.round(Ra0[2:], 3)}")
    def no_curve(bc, seed=None):
        b = bc * C
        cbs, grads = [], []
        for hres in H_LEVELS:
            sel = [r for r in rows if r["mode"] == "nonoff" and r["h"] == hres and (hres == 0.0 or r["bc"] == bc)
                   and (seed is None or r["seed"] == seed)]
            L, Rn, _, _, _, _ = pooled(sel)
            F = np.r_[0.0, 1 - C * hres, 1 - C * hres + b * hres * (1 - L[2:])]
            parts = solve_parts(N_SITES, K, m, F)
            cb, al, be = breakeven(parts, Rn, L)
            cbs.append(cb)
            grads.append((b * al - C * be) / parts["vbar"])
        return np.array(cbs), np.array(grads)

    print("h grid:", H_LEVELS)
    summary = {}
    for bc in BC_LEVELS:
        cbs, grads = no_curve(bc)
        per_seed = [(1 / bc) / no_curve(bc, s)[0].min() for s in SEEDS]
        ratio = (1 / bc) / cbs.min()
        summary[bc] = dict(breakeven=cbs.tolist(), gradient=grads.tolist(), ratio=ratio, ratio_per_seed=per_seed)
        print(f"b/c {bc}: actual c/b {1 / bc:.4f}; break-even {np.round(cbs, 4)}; actual / min break-even "
              f"{ratio:.2f} (per seed {np.round(per_seed, 2)}); gradient {np.round(grads, 5)}")
    tg = []
    for hres in H_LEVELS:                                   # T14 reference gradient, analytic, same grid
        b = 14 * C
        F = np.r_[0.0, 1 - C * hres, np.full(N_SITES - 1, 1 + (b - C) * hres)]
        parts = solve_parts(N_SITES, K, m, F)
        zero = np.zeros(N_SITES + 1)
        zero[1] = 1.0
        _, al, be = breakeven(parts, parts["G"], zero)
        tg.append((b * al - C * be) / parts["vbar"])
    print(f"T14 reference (analytic): gradient {np.round(tg, 5)}; actual / min break-even 0.071/0.103 = 0.69")
    return summary


if __name__ == "__main__":
    sys.exit(0 if main() is not None else 1)
