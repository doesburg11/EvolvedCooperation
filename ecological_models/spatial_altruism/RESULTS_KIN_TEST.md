# Mitteldorf and Wilson (2000) as a kin-selection test: results (run 2026-11-25)

Pre-registration `PREREG_KIN_TEST.md` (agreed 2026-11-25, amendment A1 before the run); code `utils/run_kin_test.py`,
commit `ecad269`, tree clean (the runner's check); run with
`./.conda/bin/python -m ecological_models.spatial_altruism.utils.run_kin_test`, about one minute wall time on 8
workers (12:30-12:31 CET, from the console; not recorded in the JSON). Raw output in `data/kin_test/`
(`stage_s.json`, `stage_m_runs.json`, `verdict.json`). Code reviewed by Codex (gpt-6.2-sol, medium) before the run.

**Erratum (2026-11-25, after the run, from a reading of the full paper).** The pre-registration and the first version
of this file called harshness 0.96 (disease 0.213) "the paper's" setting. It is the repository's website-demo setting;
neither value appears in Mitteldorf and Wilson (2000). The paper's variable-density runs (its Table 2) use harshness
0.8, 0.9 and 0.95 with disease 0.2, 0.2 and 0.1, chosen with its eq. 4, `1 − m / (5(1 − g))`, so that all-selfish
populations persist alone (at density 0.6 to 0.8); at 0.96 and 0.213 that formula is below zero, consistent with the
screen failure here. The paper's Table 2 also bears on the test itself: at harshness 0.9, disease 0.2, a stalemate
(altruists and selfish coexisting for many generations, or each prevailing equally often across runs; 5-10 trials per
value) needs a benefit of 0.35 at cost
0.10 and 1.21 at cost 0.30, so roughly 0.59 at the cost used here (0.156, linear interpolation; disease here is 0.213,
not 0.2). The tested benefit, 0.468, is below that, so the result does not contradict the paper. This is not a
prediction of the rare-start result: the threshold depends on the absolute cost, and the test differs in disease and
start. The initial occupancy 0.78, also labelled "the paper's" in the pre-registration, is the demo config's (0.39 +
0.39); the paper's Figure 4 run starts with a randomized third each of altruists, selfish and empty sites. The verdict is unchanged; labels below are corrected.

**Verdict: not met, local failure.** At the screened setting (harshness 0.9), costly help starting rare reached the
endpoint in 0 of 50 runs.

## Stage S: demographic screen

All-altruist and all-selfish populations alone (b = 0.468, c = 0.156, disease 0.213, initial occupancy 0.78, seeds
500-509, 1000 steps).

| Harshness | Passes | Failures |
| --- | --- | --- |
| 0.96 (site demo setting; not the paper's, see erratum) | no | all 10 all-selfish populations went extinct (between steps 162 and 360); all-altruist populations persisted |
| 0.9 | **yes, chosen** | none |
| 0.8, 0.7, 0.6, 0.5 | yes | none |

## Stage M: the test at harshness 0.9

Seeds 100-149, 1000 steps, rare start (each site altruist with probability 0.05, selfish with probability 0.73). Measures over steps 901-1000.

| Arm | Viable | Successes | Mean altruist share | Mean occupied fraction |
| --- | --- | --- | --- | --- |
| **T: costly help (b/c 3)** | 50/50 | **0/50** | 0.004 | 0.28 |
| X: control (occupants shuffled before each help round) | 50/50 | 0/50 | 0.000 | 0.28 |
| D: dense reference (harshness 0, disease 0) | 50/50 | 0/50 | 0.000 | 1.00 |
| W: weak-altruism reference (b = 1.0, own share 0.2 > c) | 50/50 | 50/50 | 1.000 | 0.94 |
| P: site demo setting, harshness 0.96, rare start (descriptive) | 8/50 | 8/50 | 1.000 in the 8 survivors | 0.63 in the 8 survivors |

Classification, as registered: both arms valid (50/50 viable); T succeeded in 0 of 50, below 30, so **local failure**.

**Descriptive.**

- Initially, 20% of altruists had an altruist neighbour (79.7% were isolated; the same in every arm, which share
  seeds).
- Paired by seed, T and X tied in 49 of 50 runs on success; mean T − X in late altruist share was +0.4 percentage
  points. One T run (seed 102) averaged 20.0% altruists over steps 901-1000 and ended at 35.3%; in the other 49,
  altruists were essentially gone.
- Founder sharing at the final step (share of all occupied neighbour pairs descended from the same founder,
  measured immediately before the help round): T 0.86 against 0.39 under random mixing of the same occupants; X 0.61
  against 0.61, so the shuffle removed the clustering by descent where help acts. This covers all occupied pairs,
  not altruist pairs specifically, and in 49 of 50 T runs no altruists were left by then.
- Empty space was present throughout in T and X (late occupied fraction about 0.28); about 30,000 births per run went
  into previously empty sites over steps 901-1000.
- At the site's demo setting from a rare start (P), 42 of 50 populations went extinct; the 8 that survived were entirely
  altruist.

## What this shows (at these settings)

- **At harshness 0.9 (one of the paper's values, here with disease 0.213 rather than its 0.2), where all-selfish
  populations persist on their own, costly
  help (benefit-to-cost 3) did not spread from a rare, scattered start**: no run reached the endpoint, and altruists
  were essentially gone in 49 of 50 runs, although occupied neighbours were strongly clustered by descent and empty
  space was present throughout.
- **At the site's demo setting (harshness 0.96, outside the paper's tested range), all-selfish populations did not persist on their own** under the screen's
  criteria, and from a rare start the only populations that survived (8 of 50) were all-altruist. One possible
  explanation is that altruism acts there as a survival aid, keeping populations alive where selfish ones die out;
  this was not tested (there was no control arm at 0.96), and since the paper did not use this setting, it says nothing about the published
  results, which were obtained where all-selfish populations persist.
- **Help that pays for itself (weak altruism, b = 1.0) spread in every run** at the same setting.
- These results hold for this model (two discrete types, no mutation, non-overlapping generations), this benefit and
  cost, this starting pattern (randomly scattered altruists, 79.7% without an altruist neighbour) and 1000 steps.

**Predictions made before the data.** Demo setting 0.96 ("the paper's" in the pre-registration) fails the screen: 70% (yes). Some screened point passes: 60%
(yes). T met: 30% (no). X at most 10/50: 80% (yes, 0/50).

**Disposition (hard stop).** One attempt, used. No variants (other benefits, costs, starts) under this
pre-registration. As agreed, the site's reference row for this model is updated.
