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

**Next:** rung 2b (below).

## Rung 2b: partial observation (2026-11-26)

**Verdict: MET (attempt 1).** With each act observed with probability o = 0.5 (q = 0.6, start 90%),
discriminators were maintained in 20/20 seeds, and in 0/20 with shuffled records. The registered sanity check held
(no discriminator assessed bad in any test-arm run). As before, this shows maintenance over 500 generations from a
90% start at these settings, not spread from rare or general stability.

- Pre-registration: `README.md`, "Rung 2b" (agreed 2026-11-26 before model code; draft revised after a Codex
  review, whose refined mean field is the comparison column below). Code at 3e72da8 (Codex code review
  gpt-6.1-sol: no mechanism bug; counter validation extended before the run). Registered run 18:01 CET, 140 runs
  in 5.9 s. One note was added to the pre-registration before the run: at o = 1 the code makes no observation draw,
  so those runs reproduce rung 2's runs exactly (unit-tested), not only its distribution.
- Command: `./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2b.run`.
  Raw output: `rung2b/data/rung2b_runs.csv`, `rung2b_traj.npz`, `rung2b_verdict.txt`.

| Condition | Arm | Seeds DISC ≥ 0.8 at gen 500 | Mean DISC, gen 100 | Refined screen, gen 100 | Gen 1: consulted ALLD with good record | Refined screen g |
| --- | --- | --- | --- | --- | --- | --- |
| **Main: q = 0.6, o = 0.5** | **test** | **20/20** | 0.994 | 0.998 | 0.216 | 0.214 |
| | **shuffled** | **0/20** | 0.006 | 0.005 | (0.259) | |
| q = 0.6, o = 1 (= rung 2) | test | 20/20 | 0.999 | 0.9996 | 0.132 | 0.132 |
| q = 0.6, o = 0.25 | test | 16/20 | 0.940 | 0.953 | 0.365 | 0.368 |
| q = 0.6, o = 0.1 | test | 0/20 | 0.044 | 0.035 | 0.631 | 0.630 |
| q = 1.0, o = 0.1 | test | 16/20 | 0.884 | 0.933 | 0.628 | 0.630 |
| q = 0.45, o = 0.5 | test | 7/20 | 0.781 | 0.881 | 0.216 | 0.214 |

All rows except the main test are reported conditions, not tests. In the shuffled arm the generation-1 share is in
brackets: there the good-record share also changes because discriminators can turn bad, so it is not comparable
with the screen's g. Share of defectors with no observed act during generation 1: 0.000 (o = 0.5), 0.055
(o = 0.25), 0.346 (o = 0.1), against (1 − o)^10 = 0.001, 0.056, 0.349.

**Reading (descriptive).** The generation-1 diagnostics agree closely with the refined mean field at every o
(within 0.004 for the good-record share), which is consistent with the screen's account that partial observation
helps defectors by letting them keep their good birth record until their first observed refusal; these diagnostics
do not isolate that mechanism. In the reported conditions, maintenance was lower at smaller o: 16/20 seeds met the
criterion at o = 0.25, none at o = 0.1 with q = 0.6. With full consultation (q = 1), 16/20 met it at o = 0.1,
directionally consistent with the refined screen (the original script had predicted failure). At q = 0.45,
o = 0.5, near the refined threshold of about 0.456, 7/20 seeds met the criterion and the generation-100 mean was
below the screen's value; because this condition is near the threshold, its outcome may be sensitive to
Wright-Fisher noise and finite-population effects. None of these reported rows is a registered test.

**Next:** rung 3a (execution errors: an intended help fails), which needs its own theory screen and
pre-registration, agreed with the user before code.
