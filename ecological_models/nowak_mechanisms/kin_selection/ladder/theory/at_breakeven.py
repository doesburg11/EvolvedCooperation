"""Population break-even c/b for the step-5 port: resident helping h changes fecundity (F_1 = 1 - c h for a breeder
alone, F_i = 1 + (b - c) h otherwise); demography, reproductive values and consanguinity are solved at that resident;
the break-even is the ratio of breeder-weighted inclusive-fitness effects (eq. 2 summed, not ratios averaged), with
the lone breeder a cost-only class. Dispersal switch fixed at the paper's value (stay if i <= 5)."""
import numpy as np
from scipy.optimize import fsolve

def solve(n, k, m, F):
    x = np.arange(n + 1) / n; h = 1 - m
    p = np.ones(n + 1) / (n + 1)
    for _ in range(4000):
        S = np.sum(x * m * p * F)
        Q = np.zeros((n + 1, n + 1))
        for i in range(n + 1):
            if i < n: Q[i, i + 1] = (n - i) * (S + x[i] * h[i] * F[i])
            if i > 0: Q[i, i - 1] = i * k
        Q -= np.diag(Q.sum(1))
        pn = np.linalg.lstsq(np.vstack([Q.T, np.ones(n + 1)]), np.r_[np.zeros(n + 1), 1.0], rcond=None)[0]
        if np.max(abs(pn - p)) < 1e-15: break
        p = 0.5 * p + 0.5 * pn
    S = np.sum(x * m * p * F)
    def dv(vt):
        V = np.r_[0.0, 1.0, vt, 0.0]
        fo = sum((1 - x[j]) * p[j] * V[j + 1] for j in range(n))
        out = []
        for i in range(1, n + 1):
            e = 1 - x[i]
            out.append(-k * V[i] + (i - 1) * k * (V[i - 1] - V[i]) + F[i] * h[i] * e * (2 * V[i + 1] - V[i])
                       + (i - 1) * F[i] * h[i] * e * (V[i + 1] - V[i]) + F[i] * m[i] * fo + n * e * S * (V[i + 1] - V[i]))
        return np.array(out[1:])
    V = np.r_[0.0, 1.0, fsolve(dv, np.ones(n - 1), xtol=1e-13), 0.0]
    al = np.array([(n - i + 1) * F[i - 1] * h[i - 1] * x[i - 1] * p[i - 1] if i >= 1 else 0 for i in range(n + 1)])
    be = np.array([(n - i + 1) * S * p[i - 1] if i >= 1 else 0 for i in range(n + 1)])
    ga = np.array([(i + 1) * k * p[i + 1] if i < n else 0 for i in range(n + 1)])
    M = np.zeros((n + 1, n + 1)); r = np.zeros(n + 1)
    for i in range(2, n + 1):
        M[i, i] = al[i] + be[i] + ga[i]; r[i] = al[i] * 2 / (i * (i - 1))
        if i >= 3: M[i, i - 1] -= al[i] * (i * i - i - 2) / (i * (i - 1)) + be[i] * (i - 2) / i
        if i < n: M[i, i + 1] -= ga[i]
    G = np.zeros(n + 1); G[2:] = np.linalg.solve(M[2:, 2:], r[2:])
    fo = sum((1 - x[j]) * p[j] * V[j + 1] for j in range(n))
    alpha = beta = 0.0
    for i in range(1, n + 1):
        A = h[i] * (1 - x[i]) * V[i + 1] + m[i] * fo
        B = (1 + (i - 1) * (G[i] if i >= 2 else 0)) * h[i] * (1 - x[i]) * (V[i + 1] - V[i])
        w = x[i] * p[i]
        if i == 1:                      # gift lost: W = -c (A + B)
            beta += w * (A + B)
        else:                           # W = b (G A + B) - c (A + B)
            alpha += w * (G[i] * A + B); beta += w * (A + B)
    pairs = np.array([i * (i - 1) * p[i] for i in range(n + 1)])
    vbar = sum(x[i] * p[i] * V[i] for i in range(1, n + 1)) / sum(x[i] * p[i] for i in range(1, n + 1))
    wsum = sum(x[i] * p[i] for i in range(1, n + 1))
    return dict(cb=alpha / beta, alpha=alpha / wsum, beta=beta / wsum, vbar=vbar, occ=np.sum(x * p),
                G_pair=np.sum(pairs * G) / pairs.sum(), G=G, p=p)

n, k = 10, 0.5
m = np.array([0.0 if i <= 5 else 1.0 for i in range(n + 1)])
def at(b, c, hres):
    F = np.r_[0.0, 1 - c * hres, np.full(n - 1, 1 + (b - c) * hres)]
    return solve(n, k, m, F)
r0 = at(0, 0, 0)
print(f"neutral: occupancy {r0['occ']:.3f}, pair-weighted G {r0['G_pair']:.4f}; G_i 2..10 {np.round(r0['G'][2:], 3)}")
print("check vs Codex (b/c 14, c 0.01): h=0, 0.6, 1 ->", [round(at(0.14, 0.01, h)['cb'], 4) for h in (0, 0.6, 1.0)])
for c in (0.002, 0.005, 0.01):
    for bc in (3.5, 14, 20):
        b = bc * c
        cbs = [at(b, c, h)['cb'] for h in (0.0, 0.3, 0.6, 1.0)]
        print(f"c={c} b/c={bc}: actual c/b {1/bc:.3f}; break-even at h=0/0.3/0.6/1: {np.round(cbs, 4)}  "
              f"{'spreads to 1' if all(1/bc < q for q in cbs) else ('stalls' if 1/bc < cbs[0] else 'no invasion')}")


print("\nselection gradient g(h) = (b alpha - c beta) / mean RV per unit h per time unit (breeder-weighted):")
for b, c in ((0.07, 0.005), (0.14, 0.01), (0.0175, 0.005)):
    out = []
    for hres in (0.0, 0.3, 0.6, 1.0):
        F = np.r_[0.0, 1 - c * hres, np.full(n - 1, 1 + (b - c) * hres)]
        r = solve(n, k, m, F)
        out.append((b * r["alpha"] - c * r["beta"]) / r["vbar"])
    print(f"b={b} c={c} (b/c {b/c:.1f}): g at h=0/0.3/0.6/1 = {np.round(out, 5)}")
