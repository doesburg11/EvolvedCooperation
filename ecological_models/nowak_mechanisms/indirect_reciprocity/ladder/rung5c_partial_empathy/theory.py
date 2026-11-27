"""Rung 5c theory screen (no simulation), 2026-11-28: PARTIAL empathy on rung 5b′.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5c_partial_empathy.theory

Each observation independently: with probability p the observer judges by the donor's view of the recipient (rung
5b′), otherwise by its own view (rung 5a). In rung 5a's independent-views mean field, the probability that a DISC
test-arm act earns a good view (before flips) is then p * pd_empathetic + (1 - p) * pd_own, where pd_empathetic is
the public-record formula (rung 5b′ screen) and pd_own rung 5a's private formula. The shuffled arm, ALLC and ALLD
formulas are the same under both rules (rung 5b′ screen), so they do not depend on p. p = 0 is rung 5a, p = 1 rung 5b′.
The mix is of assessment probabilities at the current state; trajectories need not interpolate linearly. install()
patches rung5a.theory.records globally, so check_endpoints() must run first in a fresh process (as main does).
Same limits as the earlier screens: the mean field predicted 0.932 for rung 5a (simulated 45/100) and 0.988 for rung
5b′ (simulated 95/100); it ranks settings within this deterministic screen only. The base-mu / cliff ratio is a
descriptive margin, not a forecast: bridge B1 had 0.15 and passed 59/100, rung 5b′ had 0.22 and passed 95/100.
"""

from concurrent.futures import ProcessPoolExecutor

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import theory as t5

PS = (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)


def records_mix(x, p, shuffled=False, q=t5.Q, o=t5.O, e=t5.E, a=t5.A, k=t5.K, steps=t5.STEPS):
    """rung5a.theory.records with the DISC test-arm term mixed between own-view and empathetic judging."""
    xc, xd, xa = x
    g = [1.0, 1.0, 1.0]
    acc = [0.0, 0.0, 0.0]
    du = 1.0 / steps
    for _ in range(k):
        g0 = list(g)
        for _ in range(steps):
            good_mass = xc * g[0] + xd * g[1] + xa * g[2]
            bbar = 1.0 - good_mass
            pc = 1 - e * good_mass
            pa = 1 - good_mass
            if shuffled:
                h_i = (1 - q) + q * (1 - bbar)
                pd = 1 - good_mass * (e * h_i + q * bbar)
            else:
                pd_own = 1 - sum(xy * gy * (e * ((1 - q) + q * gy) + q * (1 - gy)) for xy, gy in zip(x, g))
                pd_emp = 1 - e * good_mass
                pd = p * pd_emp + (1 - p) * pd_own
            ps = [(1 - a) * v + a * (1 - v) for v in (pc, pd, pa)]
            for i in range(3):
                g[i] += o * (ps[i] - g0[i]) * du
                acc[i] += g[i] * du
    return [v / k for v in acc]


def install(p):
    """Route rung 5a's payoffs through the mixed records (test arm); private=True keeps its payoff path."""
    orig = t5.records

    def rec(x, private=True, shuffled=False, *args, **kw):
        return records_mix(x, p, shuffled)
    t5.records = rec
    return orig


def cliff(lo, hi, steps=9, gens=4000, bar=0.8):
    assert t5.run((0.0, 1.0, 0.0), lo, gens)[1] >= bar and t5.run((0.0, 1.0, 0.0), hi, gens)[1] < bar
    for _ in range(steps):
        mid = (lo * hi) ** 0.5
        lo, hi = (mid, hi) if t5.run((0.0, 1.0, 0.0), mid, gens)[1] >= bar else (lo, mid)
    return lo, hi


def screen(p):
    install(p)
    g5, w, x = t5.run((0.1, 0.8, 0.1), 0.001, 2000)
    _, ws, _ = t5.run((0.1, 0.8, 0.1), 0.001, 2000, shuffled=True)
    lo, hi = cliff(0.0002, 0.2)
    return p, g5, w, x, ws, lo, hi


def check_endpoints():
    # p = 0 must reproduce rung 5a's screen and p = 1 the public-record (rung 5b′) screen
    orig = t5.records
    x = (0.1, 0.8, 0.1)
    a0 = orig(x, True, False)
    a1 = orig(x, False, False)
    b0, b1 = records_mix(x, 0.0), records_mix(x, 1.0)
    assert max(abs(u - v) for u, v in zip(a0, b0)) < 1e-12 and max(abs(u - v) for u, v in zip(a1, b1)) < 1e-12
    s0 = orig(x, True, True)
    assert max(abs(u - v) for u, v in zip(s0, records_mix(x, 0.5, True))) < 1e-12


def main():
    check_endpoints()
    print("endpoint check: p = 0 equals rung 5a's records, p = 1 the public record; shuffled independent of p")
    with ProcessPoolExecutor(len(PS)) as ex:
        rows = list(ex.map(screen, PS))
    print("| p (share of observations judged empathetically) | Cooperators gen 500 / gens 1,501-2,000 (mu 0.001)"
          " | Final ALLC / DISC / ALLD | Shuffled | Finite-time cliff mu | Base mu / cliff |")
    print("| --- | --- | --- | --- | --- | --- |")
    for p, g5, w, x, ws, lo, hi in rows:
        print(f"| {p:.2f} | {g5:.3f} / {w:.3f} | {x[0]:.3f} / {x[1]:.3f} / {x[2]:.3f} | {ws:.3f} |"
              f" {lo:.5f}-{hi:.5f} | {0.001 / lo:.2f} |")


if __name__ == "__main__":
    main()
