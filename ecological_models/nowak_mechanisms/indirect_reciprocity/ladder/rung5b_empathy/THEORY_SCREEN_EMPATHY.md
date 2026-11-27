# Rung 5b-empathy theory screen (2026-11-27, calculation only)

**Candidate rung (not agreed):** rung 5a′ (private views, rung 4a's base) plus **empathetic judging** (Radzvilavicius,
Stewart and Plotkin 2019, *eLife* 8:e44269: an observer judges a donor by simple standing using the donor's view of
the recipient), with mutation μ = 0.001 switched back on. Motivation: the bridge diagnosis (`../bridge5a/RESULTS.md`)
showed unconditional cooperators displacing discriminators before defectors invaded; under private views, a
discriminator's justified refusal is often judged bad by observers who see the recipient differently. Empathetic
judging removes exactly that penalty. No earlier implementation of this paper exists in EvolvedCooperation or on the
site.

**Derivation** (`theory.py` docstring; reviewed by Codex, gpt-6.1-sol, medium): in rung 5a's independent-views mean
field, the empathetic DISC term equals the public-record term (rung 4b); the shuffled arm, ALLC and ALLD keep rung
5a's formulas; payoffs are unchanged. Output `theory_output.txt`:

| Measure (b/c 3, q 0.8, o 0.5, e 0.1, a 0.02) | Rung 5a (own view) | Empathetic |
| --- | --- | --- |
| μ 0.001, start 10/80/10: cooperators at gen 500 / gens 1,501-2,000 | 0.948 / 0.932 | **0.988 / 0.988** |
| Same, final ALLC / DISC / ALLD | 0.206 / 0.724 / 0.070 | 0.075 / 0.913 / 0.012 |
| μ 0.002, same start | 0.052 / 0.029 (collapse) | 0.970 / 0.970 |
| Shuffled control, μ 0.001 (late) | 0.014 | 0.014 |
| DISC-vs-ALLD boundary (no mutation) | 0.729 | 0.606 |

**Limits.** The closure reproduces the public-record trajectory and cannot establish equal stochastic behaviour, so
rung 4b's simulated 96/100 does not transfer. Rung 5a's own screen also predicted a pass (0.932) and the simulation
gave 45/100. Empathy removes only the donor-vs-observer disagreement; disagreement from independent assessment flips
and missed observations remains. Realism: observers must know the donor's view of the recipient.

**A pre-registration would need to fix (Codex):** every observer reads the donor's stored view of the recipient as
it was before the act, including for non-consulting DISC, ALLC and ALLD; in the shuffled arm the donor decides from
its view of a random other but is judged by its view of the actual recipient; snapshot timing and update order;
observer eligibility; independent flips; resets at birth; missed observations leave views stale; and an independent
truth-table test of the assessment rule, including shuffled and stale-view cases.
