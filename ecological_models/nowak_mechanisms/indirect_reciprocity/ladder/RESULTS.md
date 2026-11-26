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

**Next:** rung 3a (below).

## Rung 3a: execution errors (2026-11-26)

**Verdict: MET (attempt 1).** With intended helps failing with probability e = 0.1 (on rung 2b: q = 0.6, o = 0.5,
start 90%), discriminators met the maintenance criterion in 19/20 seeds, and in 0/20 with shuffled records. The
registered two-way sanity check held: in every test-arm act of a discriminator, its record turned bad exactly when
an observed intended help to a good recipient failed (0 violations; qualifying failures occurred both with and
without consultation). As before, this shows maintenance over 500 generations from a 90% start at these settings,
not spread from rare or general stability.

- Pre-registration: `README.md`, "Rung 3a" (agreed 2026-11-26 before model code; draft revised after a Codex
  review). Code at 1155e60 (Codex code review gpt-6.1-sol: no mechanism bug; the unobserved-act monitor and counter
  checks were added before the run). Registered run 18:30 CET, 160 runs in 8.8 s.
- Command: `./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3a.run`.
  Raw output: `rung3a/data/rung3a_runs.csv`, `rung3a_traj.npz`, `rung3a_verdict.txt`.

| Condition | Arm | Seeds DISC ≥ 0.8 at gen 500 | Mean final DISC | Mean DISC, gen 100 | Screen, gen 100 | Gen 1: DISC records good (screen) | Gen 1: ALLD records good (screen) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Main: e = 0.1** | **test** | **19/20** | 0.950 | 0.979 | 0.982 | 0.927 (0.926) | 0.269 (0.265) |
| | **shuffled** | **0/20** | 0.000 | 0.016 | 0.011 | (0.861) | (0.301) |
| e = 0 (= rung 2b) | test | 20/20 | 1.000 | 0.994 | 0.998 | 1.000 (1.000) | 0.216 (0.214) |
| e = 0.05 | test | 20/20 | 1.000 | 0.991 | 0.993 | 0.960 (0.962) | 0.234 (0.240) |
| e = 0.2 | test | 12/20 | 0.596 | 0.840 | 0.908 | 0.860 (0.862) | 0.311 (0.309) |
| e = 0.3 | test | 5/20 | 0.250 | 0.734 | 0.756 | 0.804 (0.805) | 0.346 (0.349) |
| Image scoring, e = 0.1 | image | 20/20 | 1.000 | 0.984 | | 0.793 | 0.157 |
| Image scoring, e = 0 | image | 20/20 | 1.000 | 0.998 | | 0.930 | 0.148 |

All rows except the main test are reported conditions, not tests. Shuffled-arm record shares are in brackets
(not comparable with the screen's test-arm values). The e = 0 row's generation-100 mean equals rung 2b's main
test (0.994), as expected from the exact replay.

**Reading (descriptive).** The generation-1 record shares agree with the screen within 0.006 at every e. In the
reported conditions, maintenance became less frequent as e rose: 20/20 at e = 0.05, 12/20 at e = 0.2 (where the
screen puts the boundary at 89%, just below the 90% start) and 5/20 at e = 0.3, where the deterministic screen
indicated loss under its assumptions; finite-population runs near or beyond the boundary may vary because of
Wright-Fisher noise. In the reported image-scoring conditions, all 20 seeds met the same numerical endpoint with
and without errors. Their discriminators' records were good less often than under simple standing (0.79 against
0.93 at e = 0.1), consistent with the rule, under which justified refusals and failed helps are both recorded as
bad; their defectors' records were also good less often (0.16 against 0.27), since under this implementation every
observed refusal is recorded as bad. These arms contain no unconditional cooperators, so they do not test image
scoring in the mixed-strategy setting planned for rung 4a. None of these reported rows is a registered test.

**Next:** rung 3b (below).

## Rung 3b: assessment errors (2026-11-26)

**Verdict: MET (attempt 1), narrowly.** With observed acts assessed wrongly (record flipped) with probability
a = 0.02, on rung 3a's base (q = 0.6, o = 0.5, e = 0.1, start 90%), discriminators met the maintenance criterion in
17/20 seeds (16 needed), and in 0/20 with shuffled records. The registered sanity check held (0 violations: for
every observed act of a discriminator its record ended bad exactly when a qualifying failure or a flip occurred,
not both; unobserved acts changed no record). As before, this shows maintenance over 500 generations from a 90%
start at these settings, not spread from rare or general stability.

- Pre-registration: `README.md`, "Rung 3b" (agreed 2026-11-26 before model code; draft revised after a Codex
  review). Code at 54464ed (Codex code review gpt-6.1-sol: no implementation bug). Registered run 18:38 CET, 120
  runs in 8.5 s.
- Command: `./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3b.run`.
  Raw output: `rung3b/data/rung3b_runs.csv`, `rung3b_traj.npz`, `rung3b_verdict.txt`.

| Condition | Arm | Seeds DISC ≥ 0.8 at gen 500 | Mean final DISC | Mean DISC, gen 100 | Screen, gen 100 | Gen 1: DISC records good (screen) | Gen 1: ALLD records good (screen) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Main: a = 0.02** | **test** | **17/20** | 0.850 | 0.938 | 0.969 | 0.915 (0.913) | 0.279 (0.285) |
| | **shuffled** | **0/20** | 0.000 | 0.014 | 0.011 | (0.849) | (0.326) |
| a = 0 (= rung 3a) | test | 19/20 | 0.950 | 0.979 | 0.982 | 0.927 (0.926) | 0.269 (0.265) |
| a = 0.05 | test | 13/20 | 0.650 | 0.887 | 0.932 | 0.895 (0.893) | 0.318 (0.314) |
| a = 0.1 | test | 5/20 | 0.253 | 0.713 | 0.766 | 0.857 (0.859) | 0.355 (0.360) |
| a = 0.2 | test | 0/20 | 0.000 | 0.331 | 0.199 | 0.792 (0.791) | 0.440 (0.440) |

All rows except the main test are reported conditions, not tests. Shuffled-arm record shares are in brackets. The
a = 0 row reproduces rung 3a's main test exactly (19/20, same means), as expected from the code making no flip
draw.

**Reading (descriptive).** The generation-1 record shares agree with the screen within 0.006. The seed counts fell
with a in the reported conditions (19, 17, 13, 5, 0 out of 20 at a = 0, 0.02, 0.05, 0.1, 0.2), For a = 0.02-0.1 the
deterministic screen's generation-100 values were above the simulated means; the reverse occurred at a = 0.2. None of these reported rows is a registered test.

**Margin across the ladder so far.** On fixed base settings (b = 3, c = 1, q = 0.6), the main-test seed counts have
been 20, 20, 20, 19 and 17 out of 20 for rungs 1, 2, 2b, 3a and 3b, across successive rungs that introduced partial
observation, execution errors and assessment errors. The next rungs (unconditional cooperators, mutation, private
assessment) may reduce the remaining margin; their effects are for their own theory screens to assess, and whether to keep the base settings fixed is a decision to take
before rung 4a's pre-registration.

**Next:** rung 4a (below).

## Rung 4a: unconditional cooperators (2026-11-26), attempt 1

**Verdict: NOT MET (attempt 1).** With unconditional cooperators added (start 10% ALLC, 80% DISC, 10% ALLD) on rung
3b's fixed base (b = 3, c = 1, q = 0.6, o = 0.5, e = 0.1, a = 0.02), cooperators (ALLC + DISC) stayed at 0.8 or above
in 14/20 seeds, short of the 16 required; the shuffled control held in 0/20. The registered sanity check held
(0 violations). Under the ladder's rules a second attempt needs its own pre-registration, agreed with the user; after
two failed attempts the rung gets a hard stop.

- Pre-registration: `README.md`, "Rung 4a" (agreed 2026-11-26 before model code; base settings kept fixed by the
  user's decision; draft revised after a Codex review). Code at 519a4c4 (Codex code review gpt-6.1-sol: no mechanism
  bug; validation extended before the run). Registered run 18:50 CET, 120 runs in 13.1 s.
- Command: `./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a.run`.
  Raw output: `rung4a/data/rung4a_runs.csv`, `rung4a_traj.npz` (shares of ALLD, ALLC, DISC per generation),
  `rung4a_verdict.txt`.

| Condition | Arm | Seeds cooperators ≥ 0.8 at gen 500 | Mean final ALLC / DISC / ALLD | Mean cooperators, gen 100 | Mean peak ALLD | Help rate, gen 1 / pooled | Gen 1 good records: ALLC / DISC / ALLD (screen) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Main: 0.1 / 0.8 / 0.1** | **test** | **14/20** | 0.036 / 0.664 / 0.300 | 0.850 | 0.397 | 0.745 / 0.706 | 0.908 / 0.915 / 0.286 (0.913 / 0.913 / 0.285) |
| | **shuffled** | **0/20** | 0 / 0 / 1.000 | 0.017 | 1.000 | 0.724 / 0.222 | |
| No ALLC: 0 / 0.9 / 0.1 (= rung 3b) | test | 17/20 | 0 / 0.850 / 0.150 | 0.938 | 0.271 | 0.737 / 0.708 | — / 0.914 / 0.279 |
| 0.3 / 0.6 / 0.1 | test | 2/20 | 0.002 / 0.098 / 0.900 | 0.456 | 0.913 | 0.761 / 0.447 | 0.915 / 0.912 / 0.282 |
| No ALLD: 0.2 / 0.8 / 0 | test | 20/20 | 0.021 / 0.979 / 0 | 1.000 | 0 | 0.860 / 0.857 | 0.908 / 0.910 / — |
| Image scoring, main start | image | 15/20 | 0.034 / 0.716 / 0.250 | 0.919 | 0.346 | 0.698 / 0.696 | 0.905 / 0.793 / 0.176 |

All rows except the main test are reported conditions, not tests. The no-ALLC row reproduces rung 3b's main test
(17/20, same mean), as the exact-replay design requires. The screen's main-start help rate was 0.745, as observed in
generation 1.

**Per-seed outcomes (main test arm).** The outcome was all-or-nothing: in 14 seeds cooperators took over completely
(final cooperators 1.0; peak ALLD 0.10-0.27), and in the other 6 (seeds 4, 7, 10, 14, 18, 19) defectors did (final
ALLD 1.0).

**Reading (descriptive, not tested).** The diagnostics agree with the theory screen (generation-1 records within
0.006, the help rate exactly), and the sanity check and exact rung-3b replay held; these checks found no
implementation fault, though they cannot rule out every one. The screen indicated that defectors were briefly
favoured at the main start while unconditional cooperators were common; in a bistable finite-population system,
Wright-Fisher noise could contribute to divergence between runs, and 6 of 20 runs ended in the all-defector state.
In the reported comparisons, the maintenance count was 17/20 without ALLC (the same base, reproduced here), 14/20 at
10% ALLC and 2/20 at 30% ALLC; these are descriptive and do not establish a general monotonic effect of ALLC
frequency. In the reported no-ALLD condition, discriminators replaced unconditional cooperators in all 20 runs,
consistent with the screen's prediction for that condition. Image scoring reached 15/20. The deterministic screen
predicted near-complete cooperation by generation 500 but does not estimate the fraction of stochastic runs that
reach the all-defector state, because it omits Wright-Fisher sampling noise.

**Options for a second attempt (for the user to decide; none is registered).** (1) A smaller step towards the same
ingredient, as the ladder's rules prescribe: fewer unconditional cooperators at the start (for example 5%). (2) A
change of the fixed base (higher q or b/c), which the user decided against before this attempt. (3) A hard stop at
rung 4a.

## Rung 4a, attempt 2: 5% unconditional cooperators (2026-11-26)

**Verdict: NOT MET (attempt 2, the last).** With the start changed to 5% ALLC, 85% DISC, 10% ALLD (everything else
as attempt 1), cooperators stayed at 0.8 or above in **11/20** seeds, short of the 16 required; the shuffled control
held in 0/20. The registered sanity check held (0 violations). As registered, **rung 4a now has a hard stop**: no
further change of composition, parameters, seeds, horizon or threshold; the user decides how the ladder continues.

- Pre-registration: `README.md`, "Rung 4a, attempt 2" (chosen by the user after attempt 1, agreed 2026-11-26 before
  the runner was written; draft revised after a Codex review). Runner `rung4a/run_attempt2.py` at b0c4718 (Codex
  review gpt-6.1-sol: no bug), model unchanged from attempt 1. Registered run 19:09 CET, 40 runs in 3.1 s.
- Command: `./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a.run_attempt2`.
  Raw output: `rung4a/data/rung4a_attempt2_runs.csv`, `_traj.npz`, `_verdict.txt`.

| Arm | Seeds cooperators ≥ 0.8 at gen 500 | Mean final ALLC / DISC / ALLD | Mean cooperators, gen 100 | Mean peak ALLD | Help rate, gen 1 / pooled | Gen 1 good records: ALLC / DISC / ALLD |
| --- | --- | --- | --- | --- | --- | --- |
| **test** | **11/20** | 0.000 / 0.550 / 0.450 | 0.830 | 0.527 | 0.742 / 0.625 | 0.915 / 0.916 / 0.291 |
| **shuffled** | **0/20** | 0 / 0 / 1.000 | 0.014 | 1.000 | 0.718 / 0.244 | |

Per seed (test arm), the outcome was again all-or-nothing: cooperators took over in seeds 0, 3, 4, 8, 9, 13, 14, 16,
17, 18, 19 and defectors in seeds 1, 2, 5, 6, 7, 10, 11, 12, 15. The screen (no defector-favoured phase at this
start; cooperators ≈ 0.995 by generation 500) does not estimate the share of stochastic runs that are lost.

**Reading (descriptive, post hoc, not tested).** In this fixed-seed sample the observed counts were 17/20 without
ALLC (rung 3b), 14/20 with 10% ALLC (attempt 1) and 11/20 with 5% ALLC (attempt 2), so the 5% condition gave a lower
count than the 10% condition here; this ordering does not establish a monotonic or causal effect of ALLC frequency.
As an illustration only: for runs that each end in one of two absorbing states, a count out of 20 spreads widely.
If the underlying chance of keeping cooperation were 0.7, a count of 11 or fewer would occur about 11% of the time
and 16 or more about 24%; the registered threshold of 16/20 would be met about 63% of the time at a chance of 0.8
and about 83% at 0.85. With 20 seeds per condition, differences of the size seen between these three conditions are
hard to resolve. This calculation was made after the result and is not part of any test.

**Where the ladder stands.** The registered criteria were met for rungs 1 (oracle-label baseline, not yet indirect
reciprocity by the ladder's definition), 2 (the first rung meeting that definition: reputation earned by actions,
simple standing), 2b (partial observation), 3a (execution errors) and 3b (assessment errors, narrowly). Rung 4a
(unconditional cooperators) was not met in either of its two permitted attempts and is hard-stopped. These results
are conditional on the fixed base (b = 3, c = 1, q = 0.6), kept fixed by the user's decision before rung 4a, and do
not establish performance under other base settings.

## Rebase to q = 0.8, Stage R and rung 4a attempt 3 (2026-11-26)

**Verdict: Stage R met (all four rungs); rung 4a attempt 3 MET.** Pre-registration: `README.md`, "Rebase to q = 0.8
and rung 4a, attempt 3" (agreed with the user 2026-11-26, after the rung-4a hard stop and before any rebase code or
run; an outcome-informed new branch). Theory screen: `rebase/THEORY_SCREEN_REBASE.md`. Runner `rebase/run.py` (commit
dd64e61; two Codex code reviews), reusing the registered rung runners unchanged at q = 0.8, seeds 1000-1099 paired
across arms; thresholds test ≥ 80/100, shuffled ≤ 20/100. Raw output and summaries: `rebase/data/`.

**Stage R** (20:18 CET, 800 runs in 23 s; commit 60dcbec): rungs 2, 2b, 3a and 3b each **100/100** in the test arm
(DISC ≥ 0.8 after generation 500) and **0/100** in the shuffled control; the registered sanity rules found no
violation (the runners' verdicts check them; the violation counters are 0 in the run files).

**Stage 4a, rung 4a attempt 3** (20:19 CET, 700 runs in 76 s): start 10% ALLC / 80% DISC / 10% ALLD, endpoint
cooperators (ALLC + DISC) ≥ 0.8 after generation 500.

| Condition (test arm unless stated) | Runs at endpoint | Final ALLC / DISC / ALLD (mean) | Mean peak ALLD | Help rate, gen 1 / pooled | Gen-1 good records, consulted ALLC / DISC / ALLD |
| --- | --- | --- | --- | --- | --- |
| **main** | **100/100** | 0.015 / 0.985 / 0.000 | 0.113 | 0.724 / 0.822 | 0.912 / 0.913 / 0.285 |
| **main, shuffled** | **0/100** | 0 / 0 / 1.000 | 1.000 | 0.687 / 0.214 | |
| 5% ALLC (85/10) | 100/100 | 0.003 / 0.997 / 0.000 | 0.111 | 0.718 / 0.815 | 0.918 / 0.912 / 0.283 |
| no ALLC (0/90/10) | 100/100 | 0 / 1.000 / 0 | 0.108 | 0.713 / 0.784 | – / 0.912 / 0.287 |
| 30% ALLC (30/60/10) | 89/100 | 0.009 / 0.881 / 0.110 | 0.246 | 0.745 / 0.768 | 0.911 / 0.913 / 0.283 |
| no ALLD (20/80/0) | 100/100 | 0.018 / 0.982 / 0 | 0 | 0.848 / 0.842 | 0.907 / 0.909 / – |
| image scoring, main start | 100/100 | 0.243 / 0.757 / 0.000 | 0.112 | 0.633 / 0.786 | 0.899 / 0.733 / 0.167 |

- **Classification:** test 100/100 (bar 80), shuffled 0/100 (bar 20) → **met**. Sanity: no violation in any test-arm
  run. The no-ALLC runs replayed Stage R's rung-3b test runs exactly (integer strategy counts in every generation and
  all 12 shared counters) for all 100 seeds.
- **Descriptive.** Unconditional cooperators declined towards zero in every condition with defectors, as the screen
  predicted. Defectors rose a little above their 10% start (mean peak 0.108-0.113), which the noise-free screen did
  not show; mean final ALLD was 0 in every condition with defectors except 30% ALLC. From a 30% ALLC start the
  endpoint was met in 89/100 runs; in the other 11, defectors took over (final ALLD 1.0 in all 11).

**Reading.** On the rebased setting (reputation consulted with probability 0.8 instead of 0.6), the registered
maintenance endpoint of indirect reciprocity under simple standing was met in every test run of every rung from 2
to 3b, and with unconditional cooperators present from the start (rung 4a), while the shuffled-reputation control
missed it in every run. This is finite-horizon maintenance from a 90% cooperative start, not invasion from rare or a stable
mixture against reintroduced defectors (that is rung 4b, mutation). The branch was chosen after rung 4a failed twice
on q = 0.6; those failures stand, and this result applies to the new base only. The screen chose the base without
simulation, but the choice was made knowing that q = 0.6 had failed.

**Next, under the agreed line hard stop:** the ladder may continue on q = 0.8 up to rung 5b at most (rung 4b mutation,
5a private assessment, 5b gossip), each with a theory screen, its own agreement and at most two attempts, with no
further rebase; two valid failures at any rung end the line.

## Rung 4b: mutation, on the rebased setting q = 0.8 (2026-11-26)

**Verdict: MET.** With mutation at μ = 0.001 (each offspring switches to one of the other two strategies with
probability 0.001), from the start 10% ALLC / 80% DISC / 10% ALLD, **96/100** test runs met both endpoints
(cooperators ≥ 0.8 at generation 500, and a mean cooperator share ≥ 0.8 over generations 1,501-2,000); the shuffled
control met the generation-500 endpoint in **0/100** and the late-window endpoint in **0/100**. Pre-registration:
`README.md`, "Rung 4b" (agreed 2026-11-26 before any rung-4b code). Model and runner at 6d8a74d (two Codex code
reviews). Registered run 20:55 CET, 800 runs in 47 s; all 800 passed validation (mutation audit, encounters per
generation, counters, recomputed endpoints) and the test-arm sanity rule found no violation. Raw output:
`rung4b/data/` (runs CSV, counts and audit NPZ, summary JSON).

| Condition (test arm unless stated) | Gen 500 / late window / both | Mean cooperators, gen 500 / window | Window ALLC / ALLD | Runs ever below 0.5 | Screen (gen 500 / window) |
| --- | --- | --- | --- | --- | --- |
| **main, μ = 0.001** | 98 / 96 / **96** | 0.962 / 0.946 | 0.079 / 0.054 | 4 | 0.988 / 0.988 |
| **main, shuffled** | 0 / 0 / **0** | 0.015 / 0.014 | 0.005 / 0.986 | 100 | 0.014 / 0.014 |
| μ = 0.002 | 92 / 77 / 76 | 0.900 / 0.761 | 0.097 / 0.239 | 24 | 0.970 / 0.970 |
| μ = 0.004 | 45 / 10 / 10 | 0.569 / 0.157 | 0.038 / 0.843 | 91 | 0.903 / 0.903 |
| μ = 0.005 | 19 / 1 / 1 | 0.315 / 0.082 | 0.030 / 0.918 | 99 | 0.734 / 0.074 |
| all-DISC start, μ = 0.001 | 100 / 96 / 96 | 0.986 / 0.954 | 0.073 / 0.046 | 5 | 0.988 / 0.988 |
| all-ALLD start, μ = 0.001 | 0 / 0 / 0 | 0.015 / 0.015 | 0.006 / 0.985 | 100 | 0.014 / 0.014 |
| image scoring, main start | 71 / 14 / 13 | 0.761 / 0.191 | 0.055 / 0.809 | 88 | – |

- **The four failed test runs** (seeds 2022, 2042, 2048, 2075) each fell below half cooperators once (at generations
  278, 294, 963 and 619) and ended with ALLD at 0.98-0.99: escapes from the cooperative state to the
  defector-dominated one, which did not reverse within the run.
- **Mutation counts** matched their binomial expectation (about 2,000 per run at μ = 0.001; no run outside its
  99.9% range).

**Reading.** At μ = 0.001, on the rebased setting, the registered maintenance endpoints were met: cooperative
strategies (mostly discriminators, with about 8% unconditional cooperators kept in by mutation) held from a cooperative start for 2,000 generations with mutation active throughout (late-window mean ALLC 0.079), and the shuffled-reputation control
lost every run. Starting from all-ALLD, no run reached either registered cooperation endpoint (0/100; mutation kept cooperators near 1.5%), as the screen's second basin predicted:
this is maintenance, not recovery or spread from rare. The stochastic outcomes were less favourable than the noise-free screen suggested: the screen put the cliff near μ = 0.0046 and predicted cooperators near 0.97 at
μ = 0.002 and 0.90 at 0.004, but in the stochastic runs both endpoints were met in 76/100 runs at μ = 0.002 and
10/100 at 0.004; stochastic runs escaped to the defector-dominated basin even at mutation rates below the deterministic fold. Image scoring, which held without
mutation (rung 4a: 100/100), mostly did not hold under mutation (13/100). These are descriptive comparisons at one
setting, not tests.

**Next, under the agreed line hard stop:** rung 5a (private assessment), then 5b (gossip), each with a theory screen,
its own agreement and at most two attempts; two valid failures end the line.
