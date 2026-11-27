# Rung 5c theory screen: partial empathy (2026-11-28, calculation only)

**Question.** Rung 5b′ assumed onlookers always know the donor's view of the recipient (full empathy), and met
95/100 with mutation; rung 5a, with no empathy, met 45/100. How much empathy is needed? Here each observation is
judged by the donor's view with probability p, otherwise by the observer's own view.

**Method.** `theory.py`: in rung 5a's independent-views mean field, the DISC test-arm assessment is the p-weighted
mix of the own-view and empathetic formulas; the shuffled arm, ALLC and ALLD do not depend on p. Checks: p = 0
reproduces rung 5a's records, p = 1 the public record (rung 5b′). Reviewed by Codex (gpt-6.1-sol, medium): the mix is
correct within the closure and reaches both arms. Output `theory_output.txt`.

| p | Cooperators at gen 500 / gens 1,501-2,000 (μ 0.001) | Final ALLC / DISC / ALLD | Shuffled | Finite-time cliff μ | Base μ / cliff |
| --- | --- | --- | --- | --- | --- |
| 0 (rung 5a) | 0.948 / 0.932 | 0.206 / 0.724 / 0.070 | 0.014 | 0.00116 | 0.87 |
| 0.25 | 0.975 / 0.972 | 0.187 / 0.785 / 0.028 | 0.014 | 0.00221 | 0.45 |
| 0.5 | 0.983 / 0.983 | 0.132 / 0.851 / 0.017 | 0.014 | 0.00309 | 0.32 |
| 0.75 | 0.986 / 0.986 | 0.095 / 0.891 / 0.014 | 0.014 | 0.00389 | 0.26 |
| 0.9 | 0.987 / 0.987 | 0.082 / 0.906 / 0.013 | 0.014 | 0.00433 | 0.23 |
| 1 (rung 5b′) | 0.988 / 0.988 | 0.075 / 0.913 / 0.012 | 0.014 | 0.00458 | 0.22 |

**Reading.** Most of the gain in the deterministic margin comes early: a quarter of the observations judged
empathetically already doubles the cliff (0.00116 to 0.00221), and half gives about two thirds of the full-empathy
cliff. The screen does **not** predict pass rates: its margins have not tracked the simulations (bridge B1: ratio
0.15, 59/100; rung 5b′: 0.22, 95/100; rung 5a: 0.87, 45/100). Only simulation can say where between 45 and 95 a given
p lands.

**Proposed use (not agreed):** a first simulated rung at p = 0.5 on rung 5b′'s code (one new parameter), then, within
the user's hard stop of two rungs, p = 0.25 if 0.5 passes, or p = 0.75 if it fails.
