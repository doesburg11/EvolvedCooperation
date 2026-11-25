"""Numerical re-derivation of Alizon & Taylor (2008), Fig. 2 (n = 10, k = 0.5), from their appendix."""
import numpy as np
from scipy.optimize import fsolve

def solve(n=10, k=0.5, m=None):
    x = np.arange(n + 1) / n
    if m is None:
        m = np.array([0.0 if i <= n // 2 else 1.0 for i in range(n + 1)])   # main text: m_i = 0 for i <= 5 (n = 10)
    h = 1 - m
    # stationary p_i (A3), with S = sum_j x_j m_j p_j depending on p: iterate
    p = np.ones(n + 1) / (n + 1)
    for _ in range(2000):
        S = np.sum(x * m * p)
        Q = np.zeros((n + 1, n + 1))   # generator, Q[a, b] rate a -> b
        for i in range(n + 1):
            if i < n: Q[i, i + 1] = (n - i) * (S + x[i] * h[i])
            if i > 0: Q[i, i - 1] = i * k
        Q -= np.diag(Q.sum(1))
        A = np.vstack([Q.T, np.ones(n + 1)])
        p_new = np.linalg.lstsq(A, np.r_[np.zeros(n + 1), 1.0], rcond=None)[0]
        if np.max(abs(p_new - p)) < 1e-14: break
        p = 0.5 * p + 0.5 * p_new
    S = np.sum(x * m * p)
    # reproductive values from Table A1 (v_1 = 1), i = 1..n
    def dv(v):
        V = np.r_[0.0, v, 0.0]            # V[i], i = 0..n+1
        foreign = sum((1 - x[j]) * p[j] * V[j + 1] for j in range(n))
        out = []
        for i in range(1, n + 1):
            e = 1 - x[i]
            r = -k * V[i] + (i - 1) * k * (V[i - 1] - V[i]) + h[i] * e * (2 * V[i + 1] - V[i]) \
                + (i - 1) * h[i] * e * (V[i + 1] - V[i]) + m[i] * foreign + n * e * S * (V[i + 1] - V[i])
            out.append(r)
        return np.array(out)
    def eqs(vt):
        v = np.r_[1.0, vt]
        return dv(v)[1:]
    v = np.r_[1.0, fsolve(eqs, np.ones(n - 1))]
    V = np.r_[0.0, v, 0.0]
    # consanguinity G_i (A5), i = 2..n, linear system
    alpha = np.array([(n - i + 1) * h[i - 1] * x[i - 1] * p[i - 1] if i >= 1 else 0 for i in range(n + 1)])
    beta = np.array([(n - i + 1) * S * p[i - 1] if i >= 1 else 0 for i in range(n + 1)])
    gamma = np.array([(i + 1) * k * p[i + 1] if i < n else 0 for i in range(n + 1)])
    M = np.zeros((n + 1, n + 1)); rhs = np.zeros(n + 1)
    for i in range(2, n + 1):
        tot = alpha[i] + beta[i] + gamma[i]
        M[i, i] = tot
        rhs[i] = alpha[i] * 2 / (i * (i - 1))
        if i - 1 >= 2:
            M[i, i - 1] -= alpha[i] * (i * i - i - 2) / (i * (i - 1)) + beta[i] * (i - 2) / i
        if i < n:
            M[i, i + 1] -= gamma[i]
    G = np.zeros(n + 1)
    G[2:] = np.linalg.solve(M[2:, 2:], rhs[2:])
    # threshold c/b per patch type from eq. (2)
    foreign = sum((1 - x[j]) * p[j] * V[j + 1] for j in range(n))
    cb = np.full(n + 1, np.nan)
    for i in range(2, n + 1):
        A = h[i] * (1 - x[i]) * V[i + 1] + m[i] * foreign
        B = (1 + (i - 1) * G[i]) * h[i] * (1 - x[i]) * (V[i + 1] - V[i])
        cb[i] = (G[i] * A + B) / (A + B)
    w = x * p
    return dict(x=x, p=p, S=S, v=v, G=G, cb=cb, occ=np.sum(x * p),
                G_avg=np.nansum((w * G)[2:]) / w[2:].sum(), cb_avg=np.nansum((w * cb)[2:]) / w[2:].sum())

r = solve()
np.set_printoptions(precision=3, suppress=True)
print("p_i  ", r["p"]); print("v_i  ", r["v"], " v_n/v_1 =", round(r["v"][-1] / r["v"][0], 3))
print("G_i  ", r["G"][2:]); print("c/b_i", r["cb"][2:])
print("mean occupancy", round(r["occ"], 3), " mean G", round(r["G_avg"], 3), " mean c/b", round(r["cb_avg"], 3),
      " argmax c/b at i =", int(np.nanargmax(r["cb"])))
for k in (0.1, 0.25, 0.5):   # m fixed at the n = 10 switch (not re-optimised); k = 1 is extinct
    q = solve(k=k)
    print(f"k={k}: occupancy {q['occ']:.2f}, mean c/b threshold {q['cb_avg']:.3f}")

def ess(n=10, k=0.5):
    m = np.array([0.0 if i <= n // 2 else 1.0 for i in range(n + 1)])
    for it in range(60):
        r = solve(n, k, m)
        V = np.r_[0.0, r["v"], 0.0]; x = r["x"]; p = r["p"]; G = r["G"]
        foreign = sum((1 - x[j]) * p[j] * V[j + 1] for j in range(n))
        dm = np.array([foreign - (1 - x[i]) * (2 * V[i + 1] - V[i] + (i - 1) * (V[i + 1] - V[i]) * G[i])
                       if i >= 1 else 0 for i in range(n + 1)])
        new = np.where(dm > 0, 1.0, 0.0); new[0] = 0.0
        if np.array_equal(new, m): break
        m = new
    return r, m

print("\nESS dispersal re-optimised (eq. A6) per death rate k (birth rate 1, n = 10):")
for k in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
    r, m = ess(k=k)
    if r["occ"] < 0.02:
        print(f"k={k}: extinct"); continue
    i0 = int(np.argmax(m > 0)) if m.any() else None
    print(f"k={k}: occupancy {r['occ']:.2f}, stay-home below i = {i0}, mean G {r['G_avg']:.3f}, "
          f"mean c/b threshold {r['cb_avg']:.3f} (needed b/c > {1/max(r['cb_avg'],1e-9):.1f})")


print("\ndensity-INDEPENDENT dispersal (same m in every patch type), n = 10:")
for k in (0.2, 0.5):
    for mc in (0.05, 0.2, 0.5, 0.9):
        m = np.full(11, mc); m[0] = 0
        r = solve(10, k, m)
        print(f"k={k} m={mc}: occupancy {r['occ']:.2f}, mean G {r['G_avg']:.3f}, mean c/b threshold {r['cb_avg']:.3f}")
