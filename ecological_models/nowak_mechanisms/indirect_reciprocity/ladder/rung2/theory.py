"""Rung 2 theory screen (no simulation): reputation earned from actions under the standing norm.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2.theory

Standing (public record, every act observed, assessed with the recipient's current public reputation):
  help anyone -> good; refuse a good recipient -> bad; refuse a bad recipient -> good (justified).
Everyone is good at birth. Without errors a DISC never refuses a good recipient, so DISC stay good. An ALLD
refuses everyone: after each own donor act it is good iff that recipient was bad.

Approximation (mean field, large N, one generation of k rounds, donors in random order each round):
  g = share of time an ALLD is good when met as a recipient.
  Steady state after its first act: g_ss = P(recipient bad) = x_A * (1 - g_ss)  ->  g_ss = x_A / (1 + x_A).
  Before its first act (on average half of round 1, i.e. a share 1/(2k) of its recipient events) it is good.
  So g = g_ss + (1 - g_ss) / (2k), and the DISC donor's effective information is q_eff = q * (1 - g):
  rung 0/1 payoffs apply with q replaced by q_eff.
Shuffled control: the donor's decision uses the reputation of a random other individual, so help does not depend
on the recipient; as in rung 1, ALLD should win. APPROXIMATION: the shuffled branch assumes DISC stay good, which
is false in that arm (a consulting DISC shown a bad proxy refuses a good recipient and becomes bad); Codex's review
integrated the correct dynamics (about 0.0058 at generation 100 instead of 0.0049). The assessment is simple
standing (L3), not Leimar-Hammerstein standing.
"""

import json

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung1 import theory as t1

N, K = t1.N, 10


def g_alld(x_alld, k=K):
    g_ss = x_alld / (1.0 + x_alld)
    return g_ss + (1.0 - g_ss) / (2.0 * k)


def q_eff(q, x_alld, k=K):
    return q * (1.0 - g_alld(x_alld, k))


def payoffs(n_disc, q, shuffled, k=K):
    x_alld = 1.0 - n_disc / N
    qq = q if shuffled else q_eff(q, x_alld, k)
    # shuffled: a knowing donor sees a random other's reputation; DISC are good, ALLD good with prob g
    if shuffled:
        g = g_alld(x_alld, k)
        n_alld = N - n_disc
        pd = []
        # help prob independent of recipient: (1-q) + q * P(random other is good)
        p_good = (n_disc + g * n_alld) / N
        h = (1 - q) + q * p_good
        ben_d = t1.B * (n_disc - 1) * h / (N - 1)
        ben_a = t1.B * n_disc * h / (N - 1)
        cost_d = t1.C * (N - 1) * h / (N - 1)
        return ben_d - cost_d, ben_a
    return t1.payoffs(n_disc, qq, False)


def step(x_disc, q, shuffled, k=K):
    n = round(x_disc * N)
    pd, pa = payoffs(n, q, shuffled, k)
    fd, fa = 1 + t1.S * pd, 1 + t1.S * pa
    return x_disc * fd / (x_disc * fd + (1 - x_disc) * fa)


def recursion(x0, q, shuffled, gens, k=K):
    x = x0
    for _ in range(gens):
        x = step(x, q, shuffled, k)
    return x


def boundary(q, k=K):
    for n in range(1, N):
        pd, pa = payoffs(n, q, False, k)
        if pd > pa:
            return n / N
    return None


def q_needed(x_disc, k=K):
    """Smallest q (to 1e-4) at which DISC does better at this DISC share."""
    n = round(x_disc * N)
    for i in range(1, 10001):
        q = i / 10000
        pd, pa = payoffs(n, q, False, k)
        if pd > pa:
            return q
    return None


def main():
    res = {
        "g_alld_at_10pct_alld": g_alld(0.1),
        "q_eff_q0.6_at_90pct": q_eff(0.6, 0.1),
        "q_needed_at_90pct": q_needed(0.9),
        "rung1_q_needed_at_90pct": t1.threshold_q(900),
        "unstable_boundary_q0.6": boundary(0.6),
        "rung1_boundary_q0.6": t1.boundary(0.6),
        "gen100": {
            "test_q0.6_start0.9": recursion(0.9, 0.6, False, 100),
            "shuffled_q0.6_start0.9": recursion(0.9, 0.6, True, 100),
            "test_q0.2_start0.9": recursion(0.9, 0.2, False, 100),
            "test_q0.6_start0.05": recursion(0.05, 0.6, False, 100),
            "test_q0.45_start0.9": recursion(0.9, 0.45, False, 100),
        },
        "gen500": {"test_q0.6_start0.9": recursion(0.9, 0.6, False, 500),
                   "shuffled_q0.6_start0.9": recursion(0.9, 0.6, True, 500)},
    }
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
