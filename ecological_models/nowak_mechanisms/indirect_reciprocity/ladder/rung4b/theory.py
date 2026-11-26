"""Rung 4b theory screen (no simulation), 2026-11-26: rung 4a on the rebased setting (q = 0.8) plus mutation.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b.theory

Mutation: each offspring takes a uniformly random strategy other than its parent's with probability mu (so each of
the two other strategies with mu / 2). Deterministic Wright-Fisher recursion of rung 4a's screen (records and payoffs
from rebase/theory.py, q = 0.8, o = 0.5, e = 0.1, a = 0.02, b = 3, c = 1, s = 0.1), selection then mutation:
x' = M (x * f / mean f), with M the mutation matrix. Reported for each mu: shares at generation 500 from rung 4a's
main start (0.1 / 0.8 / 0.1) and from an all-DISC start, the long-run state (generation 5,000), whether defectors
take over, the shuffled control, and the mutation-selection floor of ALLD near the cooperative state.
"""

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rebase import theory as rb

Q, B = 0.8, 3.0
MU_GRID = (0.0, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05)
S = rb.S


def step(x, mu, shuffled=False):
    pis = rb.payoffs_3(x, B, Q, shuffled)
    f = [1 + S * p for p in pis]
    tot = sum(xi * fi for xi, fi in zip(x, f))
    y = [xi * fi / tot for xi, fi in zip(x, f)]
    return tuple((1 - mu) * y[i] + mu / 2 * (sum(y) - y[i]) for i in range(3))


def run(x0, mu, gens, shuffled=False, marks=(100, 500, 5000)):
    x = tuple(x0)
    out, peak_alld, min_coop = {}, x[2], x[0] + x[1]
    for g in range(1, gens + 1):
        x = step(x, mu, shuffled)
        peak_alld = max(peak_alld, x[2])
        min_coop = min(min_coop, x[0] + x[1])
        if g in marks:
            out[g] = x
    return out, peak_alld, min_coop


def finite_time_cliff(lo=0.002, hi=0.005, steps=6, horizon=3000, bar=0.8):
    """Bisection on mu for cooperators >= bar at generation `horizon` from an all-DISC start (a finite-time
    threshold, not the equilibrium fold: just above the fold the collapse is slow)."""
    rows = []
    for _ in range(steps):
        mid = (lo + hi) / 2
        o, _, _ = run((0.0, 1.0, 0.0), mid, horizon, marks=(horizon,))
        coop = o[horizon][0] + o[horizon][1]
        rows.append((mid, coop))
        lo, hi = (mid, hi) if coop >= bar else (lo, mid)
    return lo, hi, rows


def main():
    res = {}
    for mu in MU_GRID:
        m, peak, mn = run((0.1, 0.8, 0.1), mu, 5000)
        d, _, _ = run((0.0, 1.0, 0.0), mu, 5000)
        sh, _, _ = run((0.1, 0.8, 0.1), mu, 500, shuffled=True)
        res[mu] = dict(main_gen500=m[500], main_gen5000=m[5000], main_peak_alld=peak, main_min_coop=mn,
                       allDISC_gen500=d[500], allDISC_gen5000=d[5000], shuffled_gen500=sh[500])
        print(f"mu {mu:<6}: main gen500 C/D/A {tuple(round(v, 4) for v in m[500])}, gen5000 "
              f"{tuple(round(v, 4) for v in m[5000])}, peak ALLD {peak:.4f}, min coop {mn:.4f}; all-DISC start gen5000 "
              f"{tuple(round(v, 4) for v in d[5000])}; shuffled gen500 ALLD {sh[500][2]:.4f}")
    lo, hi, rows = finite_time_cliff()
    for mid, coop in rows:
        print(f"finite-time bisection mu {mid:.5f}: all-DISC start, gen 3000 cooperators {coop:.4f}")
    print(f"finite-time threshold (gen 3000, cooperators >= 0.8): between mu {lo:.5f} and {hi:.5f}")
    res["finite_time_cliff"] = (lo, hi)
    return res


if __name__ == "__main__":
    main()
