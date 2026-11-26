"""Rung 3a theory screen (no simulation): rung 2b plus execution errors.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3a.theory

Rules (as rung 2b, plus e): a donor that intends to help fails with probability e (no cost, no benefit); the act is
then a refusal. Each act observed with probability o; an observed act updates the donor's record by simple standing
with the recipient's true record (help -> good; refuse good -> bad; refuse bad -> good). Records good at birth.

Round-wise mean field (the refinement Codex used for rung 2b). Within round r, a fraction du of donors acts in
[u, u + du]; their records before acting are their start-of-round records, so for each strategy X
    dG_X/du = o [ P(new record good | X acts at u) - G_X(r, 0) ].
With B(u) = x_A (1 - G_A) + x_D (1 - G_D) the share of bad records (recipient drawn from the population):
    ALLD: new good iff recipient bad                      -> P = B
    DISC (test arm): bad iff an intended help to a good recipient fails -> P = 1 - e (1 - B)
    DISC (shuffled): intends help w.p. h_I = (1 - q) + q P(proxy good); bad iff it ends up refusing a good
        recipient -> P = 1 - (1 - (1 - e) h_I) (1 - B)
Generation averages Gbar_D, Gbar_A then give expected payoffs per encounter (finite-N counts as in rung 1):
    help to a DISC recipient: (1 - e)[(1 - q) + q Gbar_D];  to an ALLD: (1 - e)[(1 - q) + q Gbar_A]  (test arm)
    shuffled: (1 - e)[(1 - q) + q (x_D Gbar_D + x_A Gbar_A)] to anyone.
With e = 0 this reproduces Codex's refined rung-2b screen (checked in main()).
"""

import json

N, B_, C_, S, K = 1000, 3.0, 1.0, 0.1, 10
STEPS = 400  # Euler steps per round


def record_averages(x_disc, q, o, e, shuffled, k=K, steps=STEPS):
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
            gd += o * (pd - gd0) * du
            ga += o * (pa - ga0) * du
            sum_d += gd * du
            sum_a += ga * du
    return sum_d / k, sum_a / k


def payoffs(n_disc, q, o, e, shuffled):
    x = n_disc / N
    gd, ga = record_averages(x, q, o, e, shuffled)
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


def recursion(x0, q, o, e, shuffled, gens):
    x = x0
    for _ in range(gens):
        n = x * N  # continuous composition (no rounding, no stop at fixation; Codex review)
        pd, pa = payoffs(n, q, o, e, shuffled)
        fd, fa = 1 + S * pd, 1 + S * pa
        x = x * fd / (x * fd + (1 - x) * fa)
    return x


def q_needed(x_disc, o, e):
    n = round(x_disc * N)
    lo, hi = 0.0, 1.0
    pd, pa = payoffs(n, hi, o, e, False)
    if pd <= pa:
        return None
    for _ in range(30):
        mid = (lo + hi) / 2
        pd, pa = payoffs(n, mid, o, e, False)
        lo, hi = (lo, mid) if pd > pa else (mid, hi)
    return hi


def boundary(q, o, e):
    lo, hi = 1, N - 1
    pd, pa = payoffs(hi, q, o, e, False)
    if pd <= pa:
        return None
    # DISC advantage increases with DISC share here; bisection on the crossing
    while hi - lo > 1:
        mid = (lo + hi) // 2
        pd, pa = payoffs(mid, q, o, e, False)
        lo, hi = (lo, mid) if pd > pa else (mid, hi)
    return hi / N


def main():
    res = {"check_e0_o0.5 (Codex rung 2b: g 0.2145, q 0.4556, boundary 0.715)": {
        "g_alld": record_averages(0.9, 0.6, 0.5, 0.0, False)[1],
        "q_needed": q_needed(0.9, 0.5, 0.0), "boundary": boundary(0.6, 0.5, 0.0)}}
    for e in (0.0, 0.02, 0.05, 0.1, 0.2, 0.3):
        gd, ga = record_averages(0.9, 0.6, 0.5, e, False)
        res[f"e={e}"] = {
            "Gbar_DISC_good": gd, "Gbar_ALLD_good": ga,
            "q_needed_at_90pct": q_needed(0.9, 0.5, e),
            "boundary_q0.6": boundary(0.6, 0.5, e),
            "test_gen100": recursion(0.9, 0.6, 0.5, e, False, 100),
            "test_gen500": recursion(0.9, 0.6, 0.5, e, False, 500),
            "shuffled_gen100": recursion(0.9, 0.6, 0.5, e, True, 100),
        }
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
