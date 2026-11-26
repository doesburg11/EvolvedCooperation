# Indirect Reciprocity Ladder: Results

## Rung 1: sampled encounters, oracle-label baseline (2026-11-26)

**Verdict: MET (attempt 1).** With sampled encounters (k = 10 donor turns per generation, random recipients) and
the strategy label as reputation, discriminators were maintained from a 90% start at q = 0.6 in 20/20 seeds, and in
0/20 when reputations were shuffled. As registered, this is an **oracle-label baseline**, a plumbing check: it is
**not** indirect reciprocity by the ladder's definition, because reputation is not yet earned by actions.

- Pre-registration: `README.md`, "Rung 1" (agreed 2026-11-26 before model code; plan and draft revised after a
  Codex review). Code at d0cf869 (Codex code review gpt-6.1-sol: no bug in the simulation; data validation
  tightened before the run). Registered run 16:34 CET, 120 runs in 1.0 s.
- Command: `./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung1.run`.
  Raw output: `rung1/data/rung1_runs.csv`, `rung1_traj.npz`, `rung1_verdict.txt`.

| Condition | Arm | Seeds with DISC ≥ 0.8 after generation 500 | Mean final DISC | Mean DISC, generation 100 | Theory, generation 100 |
| --- | --- | --- | --- | --- | --- |
| **Main: q = 0.6, start 90%** | **test** | **20/20** | 1.000 | 1.000 | 0.99987 |
| | **shuffled** | **0/20** | 0.000 | 0.034 | 0.0287 |
| q = 0.2, start 90% (reported) | test | 0/20 | 0.000 | 0.046 | 0.0283 |
| | shuffled | 0/20 | 0.000 | 0.001 | |
| Rare start 5%, q = 0.6 (reported) | test | 0/20 | 0.000 | 0.000 | 0.00103 |
| | shuffled | 0/20 | 0.000 | 0.002 | |

Theory column: deterministic recursion with expected payoffs (`rung1/theory.py`). The simulated values follow it in
every condition, within what Wright-Fisher sampling allows (the generation-100 means are seed means of stochastic
runs, not tests).

**What this establishes.** The sampled-encounter machinery reproduces rung 0's behaviour: discriminators resist
defectors above the threshold (q\* ≈ 0.36 at a 90% start), lose below it, and do not spread from rare, and the gain
depends on reputations being linked to the recipient (the shuffled arm collapses). It does not test whether helping
earns a reputation that brings help back; that starts at rung 2.

**Next:** rung 2 (reputation earned from actions, standing norm), which needs its own theory screen and
pre-registration, agreed with the user before code.
