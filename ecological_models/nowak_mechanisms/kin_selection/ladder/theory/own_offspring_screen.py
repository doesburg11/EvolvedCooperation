"""Theory screen for rung 2 of the kin-ladder close-out (2026-11-26): help to the donor's OWN offspring in its patch,
in the empty-site islands (goal A's sub-case, through parental care), the mirror of rung 1.

Rule screened: each donor d pays c*h_d always and gives b*h_d, shared equally among its own offspring living in its
patch; with none present the gift is lost. Measured in neutral runs of the step-5 model (h = 0, b = c = 0; nothing
evolves, no test arm), per patch class i:
  * L_i: share of breeders with no own offspring in their patch (gift lost);
  * R_off_i: relatedness of a donor to its own offspring in the patch (marker identity, between-patch reference).
Plugged into the analytic break-even of no_offspring_screen.py: W_i = b (1 - L_i)(R_i A_i + B_i) - c (A_i + B_i),
demography at the resident with F_i = 1 - c h + b h (1 - L_i). Limit: L_i and R_i are measured at the neutral
state only (at a resident h the gift itself changes demography, which this uses only through F_i).

Usage: python -m ecological_models.nowak_mechanisms.kin_selection.ladder.theory.own_offspring_screen
"""

from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from ecological_models.nowak_mechanisms.kin_selection.ladder.theory.no_offspring_screen import (
    C, K, N_SITES, STAY_MAX, breakeven, solve_parts)

BURN, MEASURE, DT = 10_000.0, 20_000.0, 200.0
SEEDS = (950, 951, 952, 953)
BC_LEVELS = (3.5, 5, 7, 10, 14, 20, 28)
H_LEVELS = (0.0, 0.05, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0)
NB_PAIRS = 20_000
OUT = Path(__file__).with_name("own_offspring_screen_output.json")


def measure(seed):
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
    P, n = 1000, N_SITES
    S = P * n
    rng = np.random.default_rng(seed)
    occ = rng.random(S) < 0.5
    h = np.zeros(S)
    ident = np.arange(S, dtype=np.int64)
    parent = np.full(S, -1, np.int64)
    marker = np.arange(S, dtype=np.int64)
    counters = np.array([0.0, 0.0, float(S), float(S), 0.0])
    E._seed(seed + 7_000_001)
    out = np.empty((2, len(E.COLS)))
    hs = np.empty((2, n + 1), np.int64)
    acc = {key: np.zeros(n + 1) for key in ("donors", "lost", "Rq_off", "n_off", "same_all_del")}
    qb_hits = qb_pairs = 0
    t = 0.0
    while t < BURN + MEASURE - 1e-9:
        E.simulate(P, n, K, 0.0, 0.0, E.NONE, STAY_MAX, 0.0, 0.04, 0.001, DT, DT, occ, h, ident, parent, marker,
                   1000, out, hs, counters, False, np.array([1], np.uint64))
        t += DT
        if t <= BURN + 1e-9:
            continue
        o = occ.reshape(P, n)
        mk = marker.reshape(P, n)
        idn = ident.reshape(P, n)
        par = parent.reshape(P, n)
        cnt = o.sum(1)
        both = o[:, :, None] & o[:, None, :]
        np.einsum("pii->pi", both)[:] = False
        off = both & (par[:, None, :] == idn[:, :, None])           # recipient j is donor i's own offspring
        same = mk[:, :, None] == mk[:, None, :]
        no = off.sum(2)
        q = np.where(no > 0, (same & off).sum(2) / np.maximum(no, 1), 0.0)
        cls = np.broadcast_to(cnt[:, None], o.shape)
        for i in range(1, n + 1):
            sel = o & (cls == i)
            acc["donors"][i] += sel.sum()
            acc["lost"][i] += (sel & (no == 0)).sum()
            acc["Rq_off"][i] += q[sel & (no > 0)].sum()
            acc["n_off"][i] += no[sel].sum()
            # identity with all other patch-mates, summed over delivering donors (for the conditioned B term)
            acc["same_all_del"][i] += (same & both).sum(2)[sel & (no > 0)].sum()
        live = np.flatnonzero(occ)
        a = live[rng.integers(0, len(live), NB_PAIRS)]
        z = live[rng.integers(0, len(live), NB_PAIRS)]
        keep = (a // n) != (z // n)
        qb_hits += int((marker[a[keep]] == marker[z[keep]]).sum())
        qb_pairs += int(keep.sum())
    return dict(seed=seed, qb_hits=qb_hits, qb_pairs=qb_pairs, **{k_: v.tolist() for k_, v in acc.items()})


def pooled(rows):
    tot = {k_: np.sum([r[k_] for r in rows], 0) for k_ in ("donors", "lost", "Rq_off", "n_off", "same_all_del")}
    qb = sum(r["qb_hits"] for r in rows) / sum(r["qb_pairs"] for r in rows)
    L = tot["lost"] / np.maximum(tot["donors"], 1)
    L[1] = 1.0
    Q = tot["Rq_off"] / np.maximum(tot["donors"] - tot["lost"], 1)
    R = (Q - qb) / (1 - qb)
    R[:2] = 0.0
    mean_off = tot["n_off"] / np.maximum(tot["donors"], 1)
    # patch genetic mass relative to a delivering donor: 1 + sum over its i - 1 patch-mates of their relatedness
    deliv = np.maximum(tot["donors"] - tot["lost"], 1)
    i_arr = np.arange(N_SITES + 1)
    mass = 1 + (tot["same_all_del"] / deliv - qb * (i_arr - 1)) / (1 - qb)
    mass[:2] = 1.0
    return L, R, mean_off, mass


def breakeven_cond(parts, R, L, mass):
    """As no_offspring_screen.breakeven, but the benefit's crowding term uses the patch genetic mass of delivering
    donors (mass_i) instead of the unconditional 1 + (i - 1) G_i; the cost keeps the unconditional term."""
    w, A, B, G = parts["w"], parts["A"], parts["B"], parts["G"]
    Bd = np.zeros_like(B)
    for i in range(2, N_SITES + 1):
        Bd[i] = B[i] * mass[i] / (1 + (i - 1) * G[i])
    alpha = sum(w[i] * (1 - L[i]) * (R[i] * A[i] + Bd[i]) for i in range(2, N_SITES + 1))
    beta = sum(w[i] * (A[i] + B[i]) for i in range(1, N_SITES + 1))
    return alpha / beta, alpha / w[1:].sum(), beta / w[1:].sum()


def main():
    with Pool(len(SEEDS)) as pool:
        rows = pool.map(measure, SEEDS)
    OUT.write_text(json.dumps(rows))
    L, R, mean_off, mass = pooled(rows)
    m = np.array([0.0 if i <= STAY_MAX else 1.0 for i in range(N_SITES + 1)])
    print("neutral state, per patch class i = 1..10:")
    print("  share of breeders with no own offspring at home (L_i):", np.round(L[1:], 3))
    print("  mean number of own offspring at home:", np.round(mean_off[1:], 3))
    print("  relatedness to own offspring at home (R_i, i >= 2):", np.round(R[2:], 3))
    print("  patch genetic mass of delivering donors (i >= 2):", np.round(mass[2:], 3))
    parts0 = solve_parts(N_SITES, K, m, np.r_[0.0, np.ones(N_SITES)])
    w = parts0["w"]
    print(f"  breeder-weighted share with an own offspring at home: {np.sum(w[1:] * (1 - L[1:])) / w[1:].sum():.3f}")
    per_seed = {r["seed"]: pooled([r]) for r in rows}
    print("\nbreak-even c/b and gradient per unit h per time unit, by b/c (c = 0.005):")
    print("h grid:", H_LEVELS)
    for bc in BC_LEVELS:
        b = bc * C
        cbs, grads = [], []
        for hres in H_LEVELS:
            F = np.r_[0.0, 1 - C * hres, 1 - C * hres + b * hres * (1 - L[2:])]
            parts = solve_parts(N_SITES, K, m, F)
            cb, al, be = breakeven_cond(parts, R, L, mass)
            if hres == 0.0 and bc == BC_LEVELS[0]:
                print("  unconditioned break-even (for comparison):", round(breakeven(parts, R, L)[0], 4))
            cbs.append(cb)
            grads.append((b * al - C * be) / parts["vbar"])
        cbs = np.array(cbs)
        seed_ratio = []
        for s, (Ls, Rs, _, Ms) in per_seed.items():
            cs = []
            for hres in H_LEVELS:
                F = np.r_[0.0, 1 - C * hres, 1 - C * hres + b * hres * (1 - Ls[2:])]
                cs.append(breakeven_cond(solve_parts(N_SITES, K, m, F), Rs, Ls, Ms)[0])
            seed_ratio.append((1 / bc) / min(cs))
        print(f"b/c {bc}: actual c/b {1 / bc:.4f}; break-even {np.round(cbs, 4)}; actual / min break-even "
              f"{(1 / bc) / cbs.min():.2f} (per seed {np.round(seed_ratio, 2)}); gradient {np.round(grads, 5)}")
    print("\nReference: T14 (all patch-mates) actual / min break-even 0.69, gradient 0.0023 to 0.0010; "
          "NO28 (non-offspring) 0.76, gradient 0.0041 to 0.0007")


if __name__ == "__main__":
    main()
