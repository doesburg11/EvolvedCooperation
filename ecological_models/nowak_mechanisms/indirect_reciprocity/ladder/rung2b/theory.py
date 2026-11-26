"""Rung 2b theory screen (no simulation): rung 2 with each act observed only with probability o.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2b.theory

An unobserved act leaves the donor's record unchanged. Without errors a DISC still never becomes bad. An ALLD is
good from birth until its first observed act; after that its record reflects the recipient of its last observed
act, good iff that recipient was bad: steady state g_ss = x_A / (1 + x_A) (as rung 2).

Pre-observation share. An ALLD's first act falls at u ~ U(0, 1) into round 1; its m-th act at u + m - 1. The first
observed act is the M-th, M ~ Geometric(o). Over a generation of k rounds the share of time before it is
  P_pre = [sum_{m=1..k} o (1-o)^(m-1) (m - 1/2) + (1-o)^k k] / k      (o = 1 gives rung 2's 1/(2k)).
Mean field: g = P_pre + (1 - P_pre) g_ss (ignores the relaxation of g after the first observed act), and rung 2's
payoffs apply with q_eff = q (1 - g). The shuffled branch is rung 2's approximation (assumes DISC stay good).

KNOWN LIMITS (Codex review 2026-11-26): giving an ALLD the steady-state share right after its first observed act
overstates g (early recipients are mostly good), so q needed and the boundary are overstated; the refined values
are in README.md, Rung 2b. The shuffled branch ignores o.
"""

import json

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung1 import theory as t1
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2 import theory as t2

N, K = t1.N, 10


def p_pre(o, k=K):
    s = sum(o * (1 - o) ** (m - 1) * (m - 0.5) for m in range(1, k + 1))
    return (s + (1 - o) ** k * k) / k


def g_alld(x_alld, o, k=K):
    g_ss = x_alld / (1.0 + x_alld)
    p = p_pre(o, k)
    return p + (1 - p) * g_ss


def payoffs(n_disc, q, o, shuffled, k=K):
    if shuffled:
        return t2.payoffs(n_disc, q, True, k)  # rung 2's shuffled approximation (o barely matters there)
    x_alld = 1.0 - n_disc / N
    return t1.payoffs(n_disc, q * (1.0 - g_alld(x_alld, o, k)), False)


def recursion(x0, q, o, shuffled, gens, k=K):
    x = x0
    for _ in range(gens):
        n = round(x * N)
        pd, pa = payoffs(n, q, o, shuffled, k)
        fd, fa = 1 + t1.S * pd, 1 + t1.S * pa
        x = x * fd / (x * fd + (1 - x) * fa)
    return x


def q_needed(x_disc, o, k=K):
    n = round(x_disc * N)
    for i in range(1, 10001):
        q = i / 10000
        pd, pa = payoffs(n, q, o, False, k)
        if pd > pa:
            return q
    return None


def boundary(q, o, k=K):
    for n in range(1, N):
        pd, pa = payoffs(n, q, o, False, k)
        if pd > pa:
            return n / N
    return None


def main():
    res = {}
    for o in (1.0, 0.5, 0.25, 0.1):
        res[f"o={o}"] = {
            "P_pre": p_pre(o),
            "g_at_90pct": g_alld(0.1, o),
            "q_eff_q0.6_at_90pct": 0.6 * (1 - g_alld(0.1, o)),
            "q_needed_at_90pct": q_needed(0.9, o),
            "boundary_q0.6": boundary(0.6, o),
            "gen100_test_q0.6": recursion(0.9, 0.6, o, False, 100),
            "gen500_test_q0.6": recursion(0.9, 0.6, o, False, 500),
            "gen100_test_q0.45": recursion(0.9, 0.45, o, False, 100),
        }
    res["gen100_shuffled_q0.6"] = recursion(0.9, 0.6, 0.5, True, 100)
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
