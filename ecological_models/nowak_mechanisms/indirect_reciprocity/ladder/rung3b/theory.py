"""Rung 3b theory screen (no simulation): rung 3a plus assessment errors.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3b.theory

Rules as rung 3a (execution errors e, observation o, consultation q, simple standing, public record), plus: when an
act is observed, the record assigned by the norm is flipped (good <-> bad) with probability a (drawn per observed
act). Round-wise mean field as rung 3a, with each strategy's probability of a good new record P replaced by
    P' = (1 - a) P + a (1 - P).
With a = 0 this is rung 3a's screen (checked in main()).
"""

import json

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3a import theory as t3

N, S, K, STEPS = t3.N, t3.S, t3.K, t3.STEPS
B_, C_ = t3.B_, t3.C_


def record_averages(x_disc, q, o, e, a, shuffled, k=K, steps=STEPS):
    xa, xd = 1 - x_disc, x_disc
    gd = ga = 1.0
    sum_d = sum_a = 0.0
    du = 1.0 / steps
    for _ in range(k):
        gd0, ga0 = gd, ga
        for _ in range(steps):
            b = xa * (1 - ga) + xd * (1 - gd)
            if shuffled:
                h_i = (1 - q) + q * (1 - b)
                pd = 1 - (1 - (1 - e) * h_i) * (1 - b)
            else:
                pd = 1 - e * (1 - b)
            pa = b
            pd = (1 - a) * pd + a * (1 - pd)
            pa = (1 - a) * pa + a * (1 - pa)
            gd += o * (pd - gd0) * du
            ga += o * (pa - ga0) * du
            sum_d += gd * du
            sum_a += ga * du
    return sum_d / k, sum_a / k


def payoffs(n_disc, q, o, e, a, shuffled):
    x = n_disc / N
    gd, ga = record_averages(x, q, o, e, a, shuffled)
    n_alld = N - n_disc
    if shuffled:
        h = (1 - e) * ((1 - q) + q * (x * gd + (1 - x) * ga))
        hd = ha = h
    else:
        hd = (1 - e) * ((1 - q) + q * gd)
        ha = (1 - e) * ((1 - q) + q * ga)
    pi_d = B_ * (n_disc - 1) * hd / (N - 1) - C_ * ((n_disc - 1) * hd + n_alld * ha) / (N - 1)
    pi_a = B_ * n_disc * ha / (N - 1)
    return pi_d, pi_a


def recursion(x0, q, o, e, a, shuffled, gens):
    x = x0
    for _ in range(gens):
        pd, pa = payoffs(x * N, q, o, e, a, shuffled)
        fd, fa = 1 + S * pd, 1 + S * pa
        x = x * fd / (x * fd + (1 - x) * fa)
    return x


def q_needed(x_disc, o, e, a):
    n = x_disc * N
    pd, pa = payoffs(n, 1.0, o, e, a, False)
    if pd <= pa:
        return None
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        pd, pa = payoffs(n, mid, o, e, a, False)
        lo, hi = (lo, mid) if pd > pa else (mid, hi)
    return hi


def boundary(q, o, e, a):
    lo, hi = 1, N - 1
    pd, pa = payoffs(hi, q, o, e, a, False)
    if pd <= pa:
        return None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        pd, pa = payoffs(mid, q, o, e, a, False)
        lo, hi = (lo, mid) if pd > pa else (mid, hi)
    return hi / N


def main():
    q, o, e = 0.6, 0.5, 0.1
    res = {"check_a0 (rung 3a e=0.1: DISC 0.926, ALLD 0.265, q 0.520, boundary 0.794)": {
        "records": record_averages(0.9, q, o, e, 0.0, False), "q_needed": q_needed(0.9, o, e, 0.0),
        "boundary": boundary(q, o, e, 0.0), "rung3a_records": t3.record_averages(0.9, q, o, e, False)}}
    for a in (0.0, 0.02, 0.05, 0.1, 0.15, 0.2):
        gd, ga = record_averages(0.9, q, o, e, a, False)
        res[f"a={a}"] = {"DISC_good": gd, "ALLD_good": ga, "q_needed_at_90pct": q_needed(0.9, o, e, a),
                         "boundary_q0.6": boundary(q, o, e, a),
                         "test_gen100": recursion(0.9, q, o, e, a, False, 100),
                         "test_gen500": recursion(0.9, q, o, e, a, False, 500),
                         "shuffled_gen100": recursion(0.9, q, o, e, a, True, 100)}
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
