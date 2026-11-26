"""Numba port of Kanwal and Gardner's (2022) individual-based simulation.

Source: github.com/jkanwal/viscosity-promotes-altruism, `run_simulation.py`, commit
0a2bc74f9eae496a71f81ad58d25dde26bc026ad. The life cycle is translated step by step; only the random-number
source differs (numpy's generator inside numba instead of Python's `random`), so runs are equivalent in
distribution, not bit-identical.

Per generation (authors' order):
  1. Reproduce: each of the n breeders on each of the N patches makes k clones. Each clone mutates gene b1
     by -0.05 with probability m/2 and +0.05 with probability m/2 (same for b2), and gets a new altruism value
     z ~ U(0, 1) with probability m.
  2. Survival, per patch: zbar = mean z over the patch's n*k juveniles (self included). SE ~ U(0.5, 1) per
     patch. A juvenile survives if U <= 0.5 + 0.5 * (1 - z) * zbar and then U' <= SE.
  3. Dispersal, per patch: P = survivors / n. Each survivor attempts dispersal with probability
     D = (P - 0.5k) * (b2 - b1) / (0.5k) + b1 (linear in P, b1 at P = k/2, b2 at P = k). With the same draw r,
     r <= D * (1 - c) is a surviving disperser, r <= D a disperser that dies, otherwise it stays.
     Surviving dispersers each go to a uniformly random patch (their own included).
  4. Breeders: an empty patch gets n new individuals [b_init, b_init, U(0, 1)]; a patch with fewer than n
     candidates draws n with replacement; otherwise n are drawn without replacement.

Switches for the kin-selection test (both off = the authors' model):
  * `dd = False` (fixed dispersal): D = b1 regardless of P (density-independent dispersal; Taylor 1992).
  * `shuffle = True` (relatedness removed): after reproduction, all N*n*k juveniles are randomly permuted
    across patches before step 2, so patch-mates at the time of helping (and afterwards) are a random sample
    of the population; everything else is unchanged.
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _seed(s):
    np.random.seed(s)


@njit(cache=True)
def step(B, n, k, m, c, dd, shuffle, b_init, J, R, Dsp, dest, imm_cnt, imm_off, imm_idx, B_new, rec):
    """One generation. B: (N, n, 3) breeders [b1, b2, z]. Returns B_new filled and stats in rec:
    rec[0] = sum over patches with survivors of (dispersal attempts / survivors), rec[1] = number of such
    patches, rec[2] = number of empty patches at breeder selection (refilled), rec[3] = total survivors,
    rec[4] = total surviving dispersers, rec[5] = sum of z over juveniles whose own z lowers their own survival
    probability (patch mean zbar > (1 - z) / (n k): net direct cost after their own share of the patch mean),
    rec[6] = sum of z over all juveniles."""
    N = B.shape[0]
    nk = n * k
    half = m / 2.0
    # 1. reproduction into J (patch-major, nk rows per patch)
    row = 0
    for i in range(N):
        for j in range(n):
            b1 = B[i, j, 0]
            b2 = B[i, j, 1]
            z = B[i, j, 2]
            for _ in range(k):
                o1 = b1
                r0 = np.random.random()
                if r0 <= half:
                    o1 = b1 - 0.05
                elif r0 <= m:
                    o1 = b1 + 0.05
                o2 = b2
                r1 = np.random.random()
                if r1 <= half:
                    o2 = b2 - 0.05
                elif r1 <= m:
                    o2 = b2 + 0.05
                oz = z
                if np.random.random() <= m:
                    oz = np.random.random()
                J[row, 0] = o1
                J[row, 1] = o2
                J[row, 2] = oz
                row += 1
    if shuffle:  # Fisher-Yates over all juveniles
        total = N * nk
        for a in range(total - 1, 0, -1):
            b = np.random.randint(0, a + 1)
            for g in range(3):
                t = J[a, g]
                J[a, g] = J[b, g]
                J[b, g] = t
    # 2-3. survival and dispersal, per patch
    nR = 0
    nD = 0
    rec[0] = 0.0
    rec[1] = 0.0
    rec[2] = 0.0
    rec[3] = 0.0
    rec[4] = 0.0
    rec[5] = 0.0
    rec[6] = 0.0
    R_start = np.empty(N, np.int64)
    R_cnt = np.empty(N, np.int64)
    halfk = 0.5 * k
    for i in range(N):
        base = i * nk
        s = 0.0
        for q in range(nk):
            s += J[base + q, 2]
        zbar = s / nk
        rec[6] += s
        SE = 0.5 + 0.5 * np.random.random()          # random.uniform(0.5, 1)
        # survivors: mark by compacting into the front of this patch's block of J
        L = 0
        for q in range(nk):
            zq = J[base + q, 2]
            if zbar * nk > 1.0 - zq:
                rec[5] += zq
            S = 0.5 + 0.5 * (1.0 - zq) * zbar
            if np.random.random() <= S:
                if np.random.random() <= SE:
                    if L != q:
                        for g in range(3):
                            J[base + L, g] = J[base + q, g]
                    L += 1
        rec[3] += L
        P = L / n
        R_start[i] = nR
        dcount = 0
        for q in range(L):
            b1 = J[base + q, 0]
            b2 = J[base + q, 1]
            if dd:
                D = (P - halfk) * (b2 - b1) / halfk + b1
            else:
                D = b1
            r = np.random.random()
            if r <= D:
                dcount += 1
                if r <= D * (1.0 - c):
                    for g in range(3):
                        Dsp[nD, g] = J[base + q, g]
                    nD += 1
            else:
                for g in range(3):
                    R[nR, g] = J[base + q, g]
                nR += 1
        R_cnt[i] = nR - R_start[i]
        if L > 0:
            rec[0] += dcount / L
            rec[1] += 1.0
    rec[4] = nD
    # dispersers to random patches; build CSR of immigrants
    for i in range(N):
        imm_cnt[i] = 0
    for d in range(nD):
        p = np.random.randint(0, N)
        dest[d] = p
        imm_cnt[p] += 1
    acc = 0
    for i in range(N):
        imm_off[i] = acc
        acc += imm_cnt[i]
    for i in range(N):
        imm_cnt[i] = 0
    for d in range(nD):
        p = dest[d]
        imm_idx[imm_off[p] + imm_cnt[p]] = d
        imm_cnt[p] += 1
    # 4. breeder selection
    chosen = np.empty(n, np.int64)
    for i in range(N):
        Rc = R_cnt[i]
        Ic = imm_cnt[i]
        Lp = Rc + Ic
        if Lp == 0:
            rec[2] += 1.0
            for j in range(n):
                B_new[i, j, 0] = b_init
                B_new[i, j, 1] = b_init
                B_new[i, j, 2] = np.random.random()
            continue
        if Lp < n:
            for j in range(n):
                chosen[j] = np.random.randint(0, Lp)
        else:  # n distinct indices, uniform n-subset (rejection; n <= 10)
            got = 0
            while got < n:
                p = np.random.randint(0, Lp)
                dup = False
                for t in range(got):
                    if chosen[t] == p:
                        dup = True
                        break
                if not dup:
                    chosen[got] = p
                    got += 1
        for j in range(n):
            p = chosen[j]
            if p < Rc:
                src = R_start[i] + p
                for g in range(3):
                    B_new[i, j, g] = R[src, g]
            else:
                src = imm_idx[imm_off[i] + p - Rc]
                for g in range(3):
                    B_new[i, j, g] = Dsp[src, g]


def run(n, c, G=20000, seed=0, dd=True, shuffle=False, init_z="random", k=100, m=0.01, total_breeders=50000,
        record_last=1000, progress=None):
    """Run one simulation. Returns a dict of per-generation arrays (length G + 1, generation 0 = initial):
    mean b1, mean b2, mean z, median z of breeders; dispersal stats (d_sum / d_rows pooled over a window gives
    the authors' notebook measure: mean over patch-generation rows with survivors of attempts / survivors);
    empty-patch refills; survivors; surviving dispersers; cost_z / total_z = share of all helping (sum of z over
    juveniles) given at a net direct cost to the helper's own survival."""
    N = int(total_breeders / n)
    z_star = 2 / (1 + 2 * c * n + np.sqrt(1 + 4 * n * (n - 1) * (c ** 2)))
    _seed(seed)
    rng = np.random.default_rng(seed + 1_000_003)   # only for the initial z values
    B = np.empty((N, n, 3))
    B[:, :, 0] = z_star
    B[:, :, 1] = z_star
    if init_z == "random":
        B[:, :, 2] = rng.random((N, n))
    elif init_z == "zero":
        B[:, :, 2] = 0.0
    else:
        raise ValueError(init_z)
    nk = n * k
    J = np.empty((N * nk, 3))
    R = np.empty((N * nk, 3))
    Dsp = np.empty((N * nk, 3))
    dest = np.empty(N * nk, np.int64)
    imm_cnt = np.empty(N, np.int64)
    imm_off = np.empty(N, np.int64)
    imm_idx = np.empty(N * nk, np.int64)
    B_new = np.empty_like(B)
    rec = np.zeros(7)
    out = {k_: np.empty(G + 1) for k_ in ("b1", "b2", "z", "z_median", "d_mean", "d_sum", "d_rows", "empty",
                                           "survivors", "dispersers", "cost_z", "total_z")}

    def write(g, Bx):
        out["b1"][g] = Bx[:, :, 0].mean()
        out["b2"][g] = Bx[:, :, 1].mean()
        out["z"][g] = Bx[:, :, 2].mean()
        out["z_median"][g] = np.median(Bx[:, :, 2])

    write(0, B)
    for name in ("d_mean", "d_sum", "d_rows", "empty", "survivors", "dispersers", "cost_z", "total_z"):
        out[name][0] = np.nan
    for g in range(1, G + 1):
        step(B, n, k, m, c, dd, shuffle, z_star, J, R, Dsp, dest, imm_cnt, imm_off, imm_idx, B_new, rec)
        B, B_new = B_new, B
        write(g, B)
        out["d_mean"][g] = rec[0] / rec[1] if rec[1] > 0 else np.nan
        out["d_sum"][g] = rec[0]
        out["d_rows"][g] = rec[1]
        out["cost_z"][g] = rec[5]
        out["total_z"][g] = rec[6]
        out["empty"][g] = rec[2]
        out["survivors"][g] = rec[3]
        out["dispersers"][g] = rec[4]
        if progress is not None:
            progress(g)
    out["final_breeders"] = B.copy()
    return out
