# Bridge to rung 5a: theory screen (2026-11-27, calculation only)

**Why.** The ladder ended at rung 5a: with private views under simple standing, 45/100 runs met both registered
maintenance endpoints (bar 80). In the external check of the authors' model (Kawakatsu, Kessinger and Plotkin 2024,
`../../kawakatsu2024_gossip/RESULTS.md`), simple standing with private views and no gossip lost ALLD in 175/200 runs
from the four mixture-basin starts. This screen asks which parameter differences between the two models move rung
5a's mutation cliff most. It is a step before any proposal to reopen the ladder, which is the user's decision.

**Method.** `theory.py` reuses rung 5a's mean-field screen (`../rung5a/theory.py`) unchanged. It sets one of its
constants at a time to the authors' value, then all four together. A Codex review (gpt-6.1-sol, medium) checked that
every override reaches every use and that the bisection brackets are valid; asserts now check the brackets. Output:
`theory_output.txt` (about 3 minutes on 6 processes).

| Change from rung 5a | DISC-vs-ALLD boundary | Cooperators at μ = 0.001 (late) | Shuffled | Final ALLC / DISC / ALLD | Finite-time cliff μ | Cliff / base cliff |
| --- | --- | --- | --- | --- | --- | --- |
| None (rung 5a base) | 0.729 | 0.932 | 0.014 | 0.206 / 0.724 / 0.070 | 0.00116-0.00117 | 1.0 |
| b/c 3 → 5 | 0.487 | 0.966 | 0.014 | 0.494 / 0.472 / 0.034 | 0.00668-0.00677 | **5.8** |
| Execution error 0.1 → 0.02 | 0.656 | 0.968 | 0.013 | 0.310 / 0.658 / 0.032 | 0.00278-0.00281 | 2.4 |
| Consultation q 0.8 → 1 | 0.613 | 0.960 | 0.016 | 0.347 / 0.614 / 0.040 | 0.00322-0.00327 | 2.8 |
| Observation o 0.5 → 1 | 0.696 | 0.941 | 0.015 | 0.264 / 0.677 / 0.059 | 0.00158-0.00160 | 1.4 |
| All four | 0.353 | 0.984 | 0.015 | 0.641 / 0.344 / 0.016 | 0.0294-0.0298 | 25.5 |

"Cooperators" is ALLC + DISC. Late = mean over generations 1,501-2,000 from 10/80/10 (ALLC/DISC/ALLD). The cliff
uses an all-DISC start and generations 3,501-4,000 (bar 0.8); it is neither an equilibrium fold nor a survival
probability.

**Reading.**
- Rung 5a's base mutation rate (0.001) sits just below its finite-time cliff (0.00116). Of the tested single
  changes, raising b/c from 3 to 5 moves the cliff furthest (5.8× the base cliff) and lowers the DISC-vs-ALLD boundary
  most (0.729 → 0.487). It does not give the highest late cooperation: lowering execution error gives 0.968 against
  0.966. Raising b at fixed c and selection strength also strengthens selection.
- Every change keeps cooperation by raising the ALLC share: at b/c 5, DISC falls below a majority (0.472), and with
  all four changes ALLC is 0.641. This is cooperation in an ALLC-DISC mixture, as in the authors' simple-standing
  analysis, not a stronger hold by discriminators.
- **Main limit:** the unchanged base already predicts 0.932 cooperators, yet the simulation met the endpoints in only
  45/100 runs. The mean field misses the failure that random fluctuations cause in a finite population near the
  cliff, as rung 4b already showed. So this screen ranks margins and does not predict pass rates. Structural
  differences (Fermi pairwise vs Wright-Fisher updating, N = 100 vs 1,000, no mutation, every-generation re-judging)
  are not in the mean field at all.

**Implication for a bridge line (proposal, not agreed).** Because the mean field cannot predict the stochastic pass
rate, the bridge has to be simulated in rung 5a's own model: one benefit change in B1 (b/c 5), followed, only if B1
is not met, by the bundled execution-error and consultation change in B2 (e 0.02, q 1; screen row "B2" in
`theory_output.txt`). If a step meets rung 5a's registered criteria,
that setting meets the criterion, and the ladder would need a rebase at that setting (rungs 2-4b re-run, as for
q = 0.8). Open question for a pre-registration: whether an ALLC-DISC mixture with DISC below a majority still
counts as indirect reciprocity under the site's definition.
