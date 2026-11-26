"""Rung 1 theory screen (no simulation): expected payoffs and the deterministic recursion.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung1.theory

Expected payoff per encounter in rung 1 (k donor turns, uniform random recipients, fitness 1 + s * net / k) equals
rung 0's (payoff / (N - 1)), so rung 0's expected payoffs apply. Shuffled control: a "knowing" donor sees the label
of a uniform random individual other than donor and recipient, so its help no longer depends on the recipient.
"""

import json

N, B, C, S = 1000, 3.0, 1.0, 0.1


def help_prob(donor_disc, recip_disc, n_disc, q, shuffled):
    """Probability that a donor helps a recipient (ALLD never helps)."""
    if not donor_disc:
        return 0.0
    if not shuffled:
        return 1.0 if recip_disc else 1.0 - q
    others_disc = n_disc - 1 - (1 if recip_disc else 0)  # excluding donor and recipient
    return (1.0 - q) + q * others_disc / (N - 2)


def payoffs(n_disc, q, shuffled):
    """Expected net payoff per encounter (benefit received minus cost paid), (DISC, ALLD)."""
    n_alld = N - n_disc
    out = []
    for me_disc in (True, False):
        # benefit: from each DISC donor j != me, chosen with prob 1/(N-1) per turn
        d_donors = n_disc - (1 if me_disc else 0)
        ben = B * d_donors * help_prob(True, me_disc, n_disc, q, shuffled) / (N - 1)
        if me_disc:
            d_recips = n_disc - 1
            cost = C * (d_recips * help_prob(True, True, n_disc, q, shuffled)
                        + n_alld * help_prob(True, False, n_disc, q, shuffled)) / (N - 1)
        else:
            cost = 0.0
        out.append(ben - cost)
    return out


def step(x_disc, q, shuffled):
    n = round(x_disc * N)
    pd, pa = payoffs(n, q, shuffled)
    fd, fa = 1 + S * pd, 1 + S * pa
    return x_disc * fd / (x_disc * fd + (1 - x_disc) * fa)


def recursion(x0, q, shuffled, gens):
    x = x0
    traj = [x]
    for _ in range(gens):
        x = step(x, q, shuffled)
        traj.append(x)
    return traj


def threshold_q(n_disc):
    """q at which DISC and ALLD payoffs are equal (test arm)."""
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        pd, pa = payoffs(n_disc, mid, False)
        lo, hi = (mid, hi) if pd < pa else (lo, mid)
    return (lo + hi) / 2


def boundary(q):
    """Smallest DISC count at which DISC does better (test arm)."""
    for n in range(1, N):
        pd, pa = payoffs(n, q, False)
        if pd > pa:
            return n / N
    return None


def main():
    res = {
        "q_threshold_at_90pct": threshold_q(900),
        "unstable_boundary_q0.6": boundary(0.6),
        "payoffs_90pct_q0.6_test": payoffs(900, 0.6, False),
        "gen100": {
            "test_q0.6_start0.9": recursion(0.9, 0.6, False, 100)[-1],
            "shuffled_q0.6_start0.9": recursion(0.9, 0.6, True, 100)[-1],
            "test_q0.2_start0.9": recursion(0.9, 0.2, False, 100)[-1],
            "test_q0.6_start0.05": recursion(0.05, 0.6, False, 100)[-1],
        },
        "gen500": {
            "test_q0.6_start0.9": recursion(0.9, 0.6, False, 500)[-1],
            "shuffled_q0.6_start0.9": recursion(0.9, 0.6, True, 500)[-1],
        },
    }
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
