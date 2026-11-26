"""Outcome-free theory screen for the rung-5b gossip draft.

For a fixed target let A and B be two receivers' pre-gossip views and S the
source's view.  Each receiver independently copies S with probability q.  The
calculation below enumerates all eight binary (A, B, S) configurations and four
copy outcomes.  It is exact for every population size when source and the two
receivers are distinct; no simulation outcome is inspected.
"""

from fractions import Fraction
from itertools import product


def disagreement_multiplier(q: Fraction) -> Fraction:
    """Expected multiplier under independently exchangeable binary source/receiver views."""
    before = Fraction(0)
    after = Fraction(0)
    for a, b, source in product((0, 1), repeat=3):
        for copy_a, copy_b in product((0, 1), repeat=2):
            p = Fraction(1, 8) * (q if copy_a else (1 - q))
            p *= q if copy_b else (1 - q)
            before += p * (a != b)
            new_a = source if copy_a else a
            new_b = source if copy_b else b
            after += p * (new_a != new_b)
    return after / before


def main() -> None:
    q = Fraction(4, 5)
    actual = disagreement_multiplier(q)
    expected = 1 - q * q
    if actual != expected:
        raise SystemExit(f"theory screen failed: {actual} != {expected}")
    print(f"PASS: exchangeable-view E[D']/E[D] = {actual} = {float(actual):.2f} for Q = {q}")


if __name__ == "__main__":
    main()
