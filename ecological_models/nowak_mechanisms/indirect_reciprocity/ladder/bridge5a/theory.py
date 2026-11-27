"""Bridge-5a theory screen (no simulation), 2026-11-27.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.bridge5a.theory

Question: rung 5a (private views, simple standing) failed at 45/100, while the authors' model of Kawakatsu,
Kessinger and Plotkin (2024) kept cooperation under simple standing with private views and no gossip. Which of the
parameter differences between the two moves rung 5a's mutation cliff most? Uses rung 5a's own mean-field screen
unchanged, setting one module constant at a time to the authors' value (b/c 3 -> 5, execution error 0.1 -> 0.02,
consultation q 0.8 -> 1, observation o 0.5 -> 1), then all four together. For each: the DISC-vs-ALLD boundary, mean
cooperators over generations 1,501-2,000 at the base mu = 0.001 (start 10/80/10), and a finite-time cliff in mu
(bisection, all-DISC start, mean cooperators over generations 3,501-4,000 >= 0.8). Structural differences
(Fermi pairwise vs Wright-Fisher updating, N, no mutation at all, every-generation re-judging) are not in this
mean field and are listed, not screened.
"""

import sys
from concurrent.futures import ProcessPoolExecutor

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import theory as t5  # noqa: E402

BASE = dict(B=3.0, E=0.1, Q=0.8, O=0.5)
CHANGES = [("rung 5a base", {}), ("b/c 5", {"B": 5.0}), ("execution error 0.02", {"E": 0.02}),
           ("q = 1", {"Q": 1.0}), ("o = 1", {"O": 1.0}),
           ("all four", {"B": 5.0, "E": 0.02, "Q": 1.0, "O": 1.0}),
           ("B2: b/c 5, e 0.02, q 1", {"B": 5.0, "E": 0.02, "Q": 1.0})]


def setp(p):
    for k, v in {**BASE, **p}.items():
        setattr(t5, k, v)
    # records() takes q, o, e as defaults bound at definition: rebind
    t5.records.__defaults__ = (True, False, t5.Q, t5.O, t5.E, t5.A, t5.K, t5.STEPS)


def cliff(lo, hi, steps=9, gens=4000, bar=0.8):
    assert t5.run((0.0, 1.0, 0.0), lo, gens)[1] >= bar, "lower bracket does not pass"
    assert t5.run((0.0, 1.0, 0.0), hi, gens)[1] < bar, "upper bracket does not fail"
    for _ in range(steps):
        mid = (lo * hi) ** 0.5                               # geometric bisection
        _, win, _ = t5.run((0.0, 1.0, 0.0), mid, gens)
        lo, hi = (mid, hi) if win >= bar else (lo, mid)
    return lo, hi


def screen(item):
    name, p = item
    setp(p)
    bnd = t5.boundary_two(True)
    _, late, xf = t5.run((0.1, 0.8, 0.1), 0.001, 2000)
    _, late_sh, _ = t5.run((0.1, 0.8, 0.1), 0.001, 2000, shuffled=True)
    lo, hi = cliff(0.0002, 0.2)
    return name, bnd, late, late_sh, xf, lo, hi


def main():
    with ProcessPoolExecutor(len(CHANGES)) as ex:
        rows = list(ex.map(screen, CHANGES))
    print("| Change from rung 5a | DISC-vs-ALLD boundary | Cooperators, mu 0.001 (late) | Shuffled | Final ALLC/DISC/ALLD"
          " | Cliff mu (finite-time) | Cliff / base cliff |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    base = rows[0][5]
    for name, bnd, late, sh, xf, lo, hi in rows:
        b = "none" if bnd is None else f"{bnd:.3f}"
        print(f"| {name} | {b} | {late:.3f} | {sh:.3f} | {xf[0]:.3f}/{xf[1]:.3f}/{xf[2]:.3f} | {lo:.5f}-{hi:.5f} |"
              f" {lo / base:.1f} |")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
