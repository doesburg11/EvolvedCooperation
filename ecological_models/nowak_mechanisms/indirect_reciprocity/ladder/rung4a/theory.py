"""Rung 4a theory screen (no simulation): rung 3b with three strategies, ALLC, DISC and ALLD (no mutation).

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a.theory

ALLC always intends to help (never consults); its intended helps fail with probability e like anyone's. Records,
observation (o), execution errors (e), assessment flips (a), simple standing: as rung 3b.

Round-wise mean field (as rungs 3a-3b), three record shares G_C, G_D, G_A, with B = sum_X x_X (1 - G_X):
  new-record good probability before flips:
    ALLC: 1 - e (1 - B)      DISC (test): 1 - e (1 - B)      ALLD: B
    DISC (shuffled): 1 - (1 - (1 - e) h_I)(1 - B), h_I = (1 - q) + q (1 - B)
  then P' = (1 - a) P + a (1 - P).
Payoff per encounter (large-N: recipients and donors drawn from the whole population):
  help by DISC to a type-Y recipient: (1 - e)[(1 - q) + q Gbar_Y] (test) or (1 - e)[(1 - q) + q (1 - Bbar)] (shuffled)
  help by ALLC: (1 - e); by ALLD: 0.
  pi_X = b * sum_Y x_Y help_Y->X  -  c * sum_Y x_Y help_X->Y.
Wright-Fisher (deterministic): x_X' = x_X f_X / sum_Y x_Y f_Y, f = 1 + s pi.
"""

import json

B_, C_, S, K, STEPS = 3.0, 1.0, 0.1, 10, 400
Q, O, E, A = 0.6, 0.5, 0.1, 0.02


def records(x, q=Q, o=O, e=E, a=A, shuffled=False, k=K, steps=STEPS):
    xc, xd, xa = x
    g = [1.0, 1.0, 1.0]
    acc = [0.0, 0.0, 0.0]
    du = 1.0 / steps
    for _ in range(k):
        g0 = list(g)
        for _ in range(steps):
            bad = xc * (1 - g[0]) + xd * (1 - g[1]) + xa * (1 - g[2])
            pc = 1 - e * (1 - bad)
            if shuffled:
                h_i = (1 - q) + q * (1 - bad)
                pd = 1 - (1 - (1 - e) * h_i) * (1 - bad)
            else:
                pd = 1 - e * (1 - bad)
            pa = bad
            ps = [(1 - a) * p + a * (1 - p) for p in (pc, pd, pa)]
            for i in range(3):
                g[i] += o * (ps[i] - g0[i]) * du
                acc[i] += g[i] * du
    return [v / k for v in acc]


def payoffs(x, q=Q, o=O, e=E, a=A, shuffled=False):
    gc, gd, ga = records(x, q, o, e, a, shuffled)
    xc, xd, xa = x
    gs = (gc, gd, ga)
    bbar = sum(xi * (1 - gi) for xi, gi in zip(x, gs))
    # help[donor][recipient]
    hc = [(1 - e)] * 3
    if shuffled:
        hd = [(1 - e) * ((1 - q) + q * (1 - bbar))] * 3
    else:
        hd = [(1 - e) * ((1 - q) + q * gy) for gy in gs]
    ha = [0.0] * 3
    h = (hc, hd, ha)
    pis = []
    for me in range(3):
        ben = B_ * sum(x[d] * h[d][me] for d in range(3))
        cost = C_ * sum(x[r] * h[me][r] for r in range(3))
        pis.append(ben - cost)
    return pis, gs


def step(x, **kw):
    pis, _ = payoffs(x, **kw)
    f = [1 + S * p for p in pis]
    tot = sum(xi * fi for xi, fi in zip(x, f))
    return tuple(xi * fi / tot for xi, fi in zip(x, f))


def recursion(x0, gens, **kw):
    x = tuple(x0)
    traj = {0: x}
    for g in range(1, gens + 1):
        x = step(x, **kw)
        if g in (100, 500):
            traj[g] = x
    return traj


def main():
    res = {}
    starts = {"main_C0.1_D0.8_A0.1": (0.1, 0.8, 0.1), "noALLC_D0.9_A0.1 (= rung 3b)": (0.0, 0.9, 0.1),
              "moreALLC_C0.3_D0.6_A0.1": (0.3, 0.6, 0.1), "noALLD_C0.2_D0.8": (0.2, 0.8, 0.0)}
    for name, x0 in starts.items():
        pis, gs = payoffs(x0)
        tr = recursion(x0, 500)
        res[name] = {"payoffs_C_D_A_at_start": pis, "records_C_D_A_at_start": gs,
                     "gen100_C_D_A": tr[100], "gen500_C_D_A": tr[500],
                     "shuffled_gen100_C_D_A": recursion(x0, 100, shuffled=True)[100]}
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
