"""Rung 5b-empathy theory screen (no simulation), 2026-11-27: empathetic judging (Radzvilavicius, Stewart and Plotkin
2019, eLife 8:e44269) on rung 5a′ (private views) with mutation mu = 0.001 switched back on.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5b_empathy.theory

Empathetic observer: judges a donor's act by simple standing using the DONOR's view of the recipient, not its own.
In rung 5a's independent-views mean field (rung5a/theory.py), with g_Y the share of views of a type-Y individual that
are good (the donor's view is one such view):
  DISC test: a refusal happens after a failed intended help (the donor did not consult, or consulted and saw good)
    or after an intentional refusal (consulted, saw bad). Judged by the donor's view, an intentional refusal is always
    good; a failed help is bad iff the donor saw the recipient as good. P(bad) = e * sum_Y x_Y g_Y, i.e.
    pd = 1 - e * sum_Y x_Y g_Y: the public-record formula (rung 4b). The disagreement term q g (1 - g) vanishes.
  DISC shuffled: the donor acts on its view of a random z but is judged by its view of the recipient (independent):
    P(bad) = sum_Y x_Y g_Y [q bbar + e (1 - q bbar)], identical to rung 5a's private shuffled formula.
  ALLC, ALLD: unchanged (their judged view is the donor's, independent, with the same mean).
So the screen runs rung 5a's code with the public formula for the test arm and the private formula for the shuffled
arm. check_algebra only confirms the identity (1 - q) g + q g = g (a sanity check, not an independent test). The
deterministic closure reproduces the public-record trajectory; it cannot establish equal stochastic behaviour, so rung
4b's simulated 96/100 does not transfer. Empathy removes the donor-vs-observer disagreement penalty only: disagreement
from independent assessment flips and missed observations remains.
"""

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import theory as t5


def pd_empathetic(x, g, q=t5.Q, e=t5.E):
    # direct evaluation from the act categories (see docstring)
    tot = 0.0
    for xy, gy in zip(x, g):
        p_intend_help_and_donor_good = (1 - q) * gy + q * gy      # non-consulter (view good w.p. gy) or consulted-good
        tot += xy * e * p_intend_help_and_donor_good             # failed help judged bad when donor's view is good
    return 1 - tot


def check_algebra():
    import itertools
    for x in ((0.1, 0.8, 0.1), (0.3, 0.6, 0.1), (0.0, 1.0, 0.0)):
        for g in itertools.product((0.2, 0.6, 0.95), repeat=3):
            good_mass = sum(a * b for a, b in zip(x, g))
            assert abs(pd_empathetic(x, g) - (1 - t5.E * good_mass)) < 1e-12


def main():
    check_algebra()
    print("algebra check: empathetic DISC term equals the public-record term")
    print("| Measure (b/c 3, q 0.8, o 0.5, e 0.1, a 0.02) | Rung 5a private (own view) | Empathetic private |")
    print("| --- | --- | --- |")
    for mu, start, label in ((0.001, (0.1, 0.8, 0.1), "mu 0.001, start 10/80/10"),
                             (0.002, (0.1, 0.8, 0.1), "mu 0.002, start 10/80/10"),
                             (0.001, (0.0, 1.0, 0.0), "mu 0.001, all-DISC start")):
        a5, w5, x5 = t5.run(start, mu, 2000, private=True)
        ae, we, xe = t5.run(start, mu, 2000, private=False)
        print(f"| {label}: cooperators gen 500 / gens 1,501-2,000 | {a5:.3f} / {w5:.3f} | {ae:.3f} / {we:.3f} |")
        print(f"| {label}: final ALLC / DISC / ALLD | {x5[0]:.3f} / {x5[1]:.3f} / {x5[2]:.3f} |"
              f" {xe[0]:.3f} / {xe[1]:.3f} / {xe[2]:.3f} |")
    _, ws, _ = t5.run((0.1, 0.8, 0.1), 0.001, 2000, private=True, shuffled=True)
    print(f"| Shuffled control, mu 0.001 (late window) | {ws:.3f} | {ws:.3f} (same formula) |")
    print(f"| Boundary DISC vs ALLD (no mutation) | {t5.boundary_two(True):.3f} | {t5.boundary_two(False):.3f} |")


if __name__ == "__main__":
    main()
