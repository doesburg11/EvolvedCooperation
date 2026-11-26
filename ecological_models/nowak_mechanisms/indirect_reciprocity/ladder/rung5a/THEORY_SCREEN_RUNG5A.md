# Rung 5a theory screen: private assessment, on rung 4b's base (2026-11-26)

Rung 5a adds one ingredient to rung 4b (met 2026-11-26: q = 0.8, mutation μ = 0.001): **private assessment**. There
is no public record: every individual keeps its own view of every other, observes each act independently with
probability o = 0.5, and judges it by simple standing using its **own** view of the recipient. A discriminator
consults its own view. This screen (`theory.py`, output `theory_output.txt`; calculation only) uses an
independent-views mean field: the donor's and an observer's views of the same recipient are treated as independent.
Its only difference from rung 4b's screen is then one term: a discriminator that refuses a recipient it sees as bad
is judged bad by an observer who sees that recipient as good, with probability q·g·(1 − g) per recipient type
(g = share of observers seeing that type as good). With public records the term vanishes, and the screen reproduces
rung 4b's (0.988 / 0.988 at μ = 0.001).

| Measure (b/c 3, q 0.8, o 0.5, e 0.1, a 0.02) | Public records (rung 4b) | Private views (rung 5a) |
| --- | --- | --- |
| Boundary, DISC against ALLD (no mutation) | 0.606 | **0.729** |
| Good views of DISC / ALLD at 90% DISC | 0.913 / 0.285 | 0.840 / 0.332 |
| μ = 0.001, start 10/80/10: cooperators at gen 500 / gens 1,501-2,000 | 0.988 / 0.988 | **0.948 / 0.932** |
| Same, final ALLC / DISC / ALLD | 0.075 / 0.913 / 0.012 | 0.207 / 0.724 / 0.070 |
| μ = 0.002, start 10/80/10 (late window) | 0.970 | **0.029** (collapse) |
| Shuffled control, μ = 0.001 (late window) | 0.014 | 0.014 |
| Cooperative state lost (all-DISC start) | fold ≈ 0.0046 | finite-time threshold 0.00116-0.00119; fold ≈ 0.00128 |

- **Margin.** Disagreement makes discriminators look worse (good views 0.84 instead of 0.91), so they need a larger
  majority to resist defectors (0.729 instead of 0.606), unconditional cooperators do relatively better (about 21% of
  the population instead of 7.5%), and defectors persist at about 7%.
- **Cliff.** The cooperative state is lost at a mutation rate about four times lower than with public records: a
  finite-time threshold between μ = 0.00116 and 0.00119 (bisection in `theory.py`: all-DISC start, mean over
  generations 3,501-4,000), and an equilibrium fold near μ = 0.00128 (Codex's fixed-point calculation; at μ = 0.00119
  a stable cooperative state with 0.91 cooperators still exists, but it is slow to reach). The fixed base μ = 0.001
  is at 0.84-0.87 of the finite-time threshold and about 0.78 of the fold.
- **Stochastic risk (a warning, not a forecast).** In rung 4b, noise made runs escape well below the deterministic
  cliff: at μ = 0.004 (0.87 of its fold) only 10/100 runs met both endpoints although the screen predicted 0.90
  cooperators. Equal ratios need not mean equal escape probabilities (different basins and noise), but a rung-5a test
  at μ = 0.001 must be expected to be at substantial risk.

**Reading.** At the fixed base the deterministic screen passes (cooperators 0.948 / 0.932 against 0.014 shuffled), but
with a narrow margin: private views move the cliff close to the base's mutation rate, and rung 4b showed that
stochastic runs fail well before such a cliff. Under the line's rule (no change of parameters, and a valid failure
ends the line), a rung-5a test at μ = 0.001 is a fixed-base test with substantial uncertainty, not a predicted pass.
A Codex review (gpt-6.1-sol, medium) checked the derivation (including recovery of the public case), corrected the
claim that independence is conservative (it is so only if views are positively correlated, which is plausible but
not shown), and showed that the bisection gives a finite-time threshold, not the fold.

**What a pre-registration would have to fix:** whether the recipient observes and judges its own donor (it has no
self-view; the screen assumes it does not), independent flips per observer, how the shuffled control picks the random
individual (excluding donor and recipient), and the fixed-base failure rule.
