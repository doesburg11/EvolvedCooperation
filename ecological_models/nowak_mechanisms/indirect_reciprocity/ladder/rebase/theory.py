"""Rebase theory screen (no simulation), 2026-11-26: which base gives the ladder more margin before rung 4a is retried?

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rebase.theory

The user chose (2026-11-26) to rebase the ladder with more margin and retry rung 4a. This screen scans the base
parameters the ladder has held fixed: the probability q that a discriminator consults a reputation, and the benefit
b (c = 1), with the full rung-3b stack (observation o = 0.5, execution errors e = 0.1, assessment flips a = 0.02,
simple standing, public records). It reuses the round-wise mean-field records of rungs 3b and 4a, which do not depend
on b, and recomputes payoffs for each b. Measures:

  * boundary_3b: unstable DISC share between ALLD and DISC (two strategies, rung 3b's model; finite-N payoffs as in
    rung3b/theory.py). Reference values on the current base (q = 0.6, b = 3): rung 2 (o = 1, e = a = 0) 0.67 (test
    20/20), rung 3b 0.824 (test 17/20).
  * At rung 4a's main start (ALLC 0.1 / DISC 0.8 / ALLD 0.1, large-N payoffs as in rung4a/theory.py): ALLD's payoff
    minus DISC's at the start, the number of generations in which ALLD out-earns DISC, the peak ALLD share, and the
    shares at generation 500 (deterministic Wright-Fisher recursion, s = 0.1).
  * At 30% ALLC (0.3 / 0.6 / 0.1): ALLD share at generation 500 (on the current base ALLD takes over).
  * Shuffled control at the main start: ALLD share at generation 100 (must stay high: the control must still fail).
"""

import json

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3b import theory as t3b
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a import theory as t4a

O, E, A = 0.5, 0.1, 0.02
C_, S, N = 1.0, 0.1, 1000
Q_GRID = (0.6, 0.7, 0.8, 0.9, 1.0)
B_GRID = (3.0, 3.5, 4.0, 5.0)


def payoffs_2(n_disc, b, q, shuffled=False):
    x = n_disc / N
    gd, ga = t3b.record_averages(x, q, O, E, A, shuffled)
    n_alld = N - n_disc
    if shuffled:
        h = (1 - E) * ((1 - q) + q * (x * gd + (1 - x) * ga))
        hd = ha = h
    else:
        hd = (1 - E) * ((1 - q) + q * gd)
        ha = (1 - E) * ((1 - q) + q * ga)
    pi_d = b * (n_disc - 1) * hd / (N - 1) - C_ * ((n_disc - 1) * hd + n_alld * ha) / (N - 1)
    pi_a = b * n_disc * ha / (N - 1)
    return pi_d, pi_a


def boundary_3b(b, q):
    lo, hi = 1, N - 1
    pd, pa = payoffs_2(hi, b, q)
    if pd <= pa:
        return None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        pd, pa = payoffs_2(mid, b, q)
        lo, hi = (lo, mid) if pd > pa else (mid, hi)
    return hi / N


def payoffs_3(x, b, q, shuffled=False):
    gs = t4a.records(x, q, O, E, A, shuffled)
    bbar = sum(xi * (1 - gi) for xi, gi in zip(x, gs))
    hc = [(1 - E)] * 3
    if shuffled:
        hd = [(1 - E) * ((1 - q) + q * (1 - bbar))] * 3
    else:
        hd = [(1 - E) * ((1 - q) + q * gy) for gy in gs]
    h = (hc, hd, [0.0] * 3)
    return [b * sum(x[d] * h[d][me] for d in range(3)) - C_ * sum(x[r] * h[me][r] for r in range(3))
            for me in range(3)]


def run_3(x0, b, q, gens, shuffled=False):
    x = tuple(x0)
    peak, favoured, grows = x[2], 0, 0
    first = None
    for g in range(1, gens + 1):
        pis = payoffs_3(x, b, q, shuffled)
        if first is None:
            first = pis
        if pis[2] > pis[1]:
            favoured += 1
        f = [1 + S * p for p in pis]
        tot = sum(xi * fi for xi, fi in zip(x, f))
        if x[2] > 0 and f[2] > tot:              # ALLD above the population mean: its share grows
            grows += 1
        x = tuple(xi * fi / tot for xi, fi in zip(x, f))
        peak = max(peak, x[2])
    return x, peak, favoured, first, grows


def main():
    res = {"check_current_base_boundary_3b (0.824)": boundary_3b(3.0, 0.6)}
    rows = []
    for q in Q_GRID:
        for b in B_GRID:
            x500, peak, fav, first, grows = run_3((0.1, 0.8, 0.1), b, q, 500)
            x500_30, peak30, fav30, _, grows30 = run_3((0.3, 0.6, 0.1), b, q, 500)
            xs100, _, _, _, _ = run_3((0.1, 0.8, 0.1), b, q, 100, shuffled=True)
            row = dict(q=q, b=b, boundary_3b=boundary_3b(b, q),
                       alld_minus_disc_payoff_at_start=first[2] - first[1],
                       gens_alld_outearns_disc=fav, gens_alld_grows=grows, peak_alld=peak, gen500_C_D_A=x500,
                       allc30_gens_alld_outearns_disc=fav30, allc30_gens_alld_grows=grows30, allc30_peak_alld=peak30,
                       allc30_gen500_alld=x500_30[2], shuffled_gen100_alld=xs100[2])
            rows.append(row)
            print(f"q {q:.1f} b {b:.1f}: boundary_3b {row['boundary_3b']}; ALLD-DISC at start "
                  f"{row['alld_minus_disc_payoff_at_start']:+.3f}; ALLD > DISC {fav} / grows {grows} gens; peak ALLD "
                  f"{peak:.4f}; gen500 C/D/A {tuple(round(v, 3) for v in x500)}; 30% ALLC: ALLD > DISC {fav30} / "
                  f"grows {grows30} gens, peak {peak30:.4f}, gen500 ALLD {x500_30[2]:.3f}; shuffled gen100 ALLD "
                  f"{xs100[2]:.3f}")
    res["rows"] = rows
    print(json.dumps({"check": res["check_current_base_boundary_3b (0.824)"]}))
    return res


if __name__ == "__main__":
    main()
