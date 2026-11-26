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

## Rung 2: reputation earned from actions, simple standing (2026-11-26)

**Verdict: MET (attempt 1).** With a public good/bad record updated by every act under simple standing,
discriminators were maintained from a 90% start at q = 0.6 in 20/20 seeds, and in 0/20 when the record a donor saw
was shuffled. The registered sanity check held (no discriminator was ever assessed bad in any test-arm run). This
is the ladder's first rung that meets its definition of indirect reciprocity: helping is costly, the record is
earned by acts, discriminators help according to the record, and cutting the link between record and recipient
removes the advantage. As on every rung, it shows maintenance over 500 generations from a 90% start at these
settings, not spread from rare or general stability.

- Pre-registration: `README.md`, "Rung 2" (agreed 2026-11-26 before model code; draft revised after a Codex review).
  Code at 022add7 (Codex code review gpt-6.1-sol: no bug in the mechanism; counter validation added before the
  run). Registered run 17:31 CET, 180 runs in 3.6 s.
- Command: `./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2.run`.
  Raw output: `rung2/data/rung2_runs.csv`, `rung2_traj.npz`, `rung2_verdict.txt`.

| Condition | Arm | Seeds with DISC ≥ 0.8 after generation 500 | Mean final DISC | Mean DISC, generation 100 | Screen, generation 100 |
| --- | --- | --- | --- | --- | --- |
| **Main: q = 0.6, start 90%** | **test** | **20/20** | 1.000 | 0.999 | 0.9996 |
| | **shuffled** | **0/20** | 0.000 | 0.009 | 0.0058 (Codex) |
| q = 0.45, start 90% (reported) | test | 18/20 | 0.900 | 0.946 | 0.971 |
| | shuffled | 0/20 | 0.000 | 0.003 | |
| q = 0.2, start 90% (reported) | test | 0/20 | 0.000 | 0.008 | 0.006 |
| | shuffled | 0/20 | 0.000 | 0.000 | |
| Rare start 5%, q = 0.6 (reported) | test | 0/20 | 0.000 | 0.000 | 0.00003 |
| | shuffled | 0/20 | 0.000 | 0.000 | |
| Image scoring, q = 0.6, start 90% (reported) | image | 20/20 | 1.000 | 1.000 | |

**Descriptive (not tests).** Among encounters of a consulting discriminator with a defector, the share in which the
defector's record was good, pooled over each run until fixation: 0.10 in the main test arm (the screen's
0.13-0.14 is for the starting population; the pooled value includes later generations with fewer defectors), 0.17
at q = 0.45, 0.05 under image scoring.

**Reading (descriptive).** The simulated values follow the theory screen's direction across the listed
conditions; apart from the main test, these comparisons are descriptive, not registered tests. At q = 0.45, near
the screen's threshold of about 0.41, 18/20 seeds met the maintenance criterion; in the image-scoring arm, 20/20
did. That pattern is consistent with the implemented error-free rules: under image scoring a defector's record,
once bad, cannot become good again (every refusal is bad), while a discriminator that refuses a bad defector gets
an occasional bad record. This result does not evaluate image scoring with errors or unconditional cooperators
(Leimar & Hammerstein 2001; Panchanathan & Boyd 2003); those settings are rungs 3-4.

**Next:** rung 2b (each act observed with probability < 1), which needs its own theory screen and
pre-registration, agreed with the user before code.
