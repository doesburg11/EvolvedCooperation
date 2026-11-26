# Partner choice and fair sharing: theory screen results (2026-11-26)

**Registered verdict: KILL.** In this market, the option to leave a partner did not produce fair splits from any
start, and did not keep them from a fair start. V1 (the no-choice control) held. Following the registered rule,
the PPG fairness module is not built on this mechanism, and the step-2 model gets no further tweak rounds
(hard stop).

Pre-registration: `PREREG_SCREEN.md` (agreed 2026-11-26, revised after a Codex review before any code). Code at
commit 59e155c (two Codex reviews, gpt-6.1-sol medium; one model bug fixed before the run: a break-up also paid
the hare payoff in the same round). Registered run 2026-11-26 15:26-15:27 CET: 1,800 runs, 0.6 min wall time
(kill-rule projection after 60 runs: 0.015 h). `analyze.py`: data check passed (exact grid, seeds 0-19 once,
2,000 generations, finite shares).

**Disclosure.** Before the registered run, two runs were made to time the model: choice arm, exploiter start,
h = 0.1, seed 0, at T = 1 and T = 100, under the code *before* the break-up fix. Both ended at a partner share
near 0 (0.005, 0.004). They are not part of the dataset. Smoke runs (30 generations) were used only to test the
pipeline.

## Step 2: registered results

Mean partner share (population mean offer s, generations 1,801-2,000), 20 seeds per cell.

**No-choice control (V1: every cell ≤ 0.25): holds.** Every cell is between 0.004 and 0.011.

**Choice arm:** fair seeds out of 20 (partner share ≥ 0.4) | mean partner share, by nominal T (H = 100).

| Start | h | T = 1 | 5 | 20 | 50 | 100 | x\* |
| --- | --- | --- | --- | --- | --- | --- | --- |
| exploiter | 0 | 0 \| 0.004 | 0 \| 0.005 | 0 \| 0.006 | 0 \| 0.005 | 0 \| 0.006 | none |
| | 0.1 | 0 \| 0.004 | 0 \| 0.004 | 0 \| 0.005 | 0 \| 0.007 | 0 \| 0.007 | none |
| | 0.3 | 0 \| 0.004 | 0 \| 0.006 | 0 \| 0.006 | 0 \| 0.009 | 0 \| 0.015 | none |
| **fair** | 0 | 0 \| 0.004 | 0 \| 0.116 | 0 \| 0.102 | 0 \| 0.133 | 0 \| 0.150 | none |
| | 0.1 | 0 \| 0.004 | 0 \| 0.075 | 0 \| 0.103 | 0 \| 0.105 | 1 \| 0.173 | none |
| | 0.3 | 0 \| 0.004 | 0 \| 0.112 | 0 \| 0.112 | 0 \| 0.121 | 0 \| 0.158 | none |
| **random** | 0 | 0 \| 0.005 | 0 \| 0.007 | 0 \| 0.011 | 0 \| 0.015 | 0 \| 0.050 | none |
| | 0.1 | 0 \| 0.005 | 0 \| 0.045 | 0 \| 0.007 | 0 \| 0.034 | 1 \| 0.043 | none |
| | 0.3 | 0 \| 0.005 | 0 \| 0.017 | 0 \| 0.022 | 0 \| 0.027 | 0 \| 0.051 | none |

x\* is none for every start and h, so PASS and MARGINAL both fail: **KILL**.

## Descriptive (not tests)

Choice arm, mean over 20 seeds and the three h values:

| Start | T | mean a | fraction paired | break-ups / generation | catch-weighted share |
| --- | --- | --- | --- | --- | --- |
| exploiter | 1 | 0.13 | 1.00 | 8,295 | 0.004 |
| exploiter | 5-100 | ≤ 0.001 | 0.94-0.28 | 17-2 | ≤ 0.009 |
| fair | 1 | 0.45 | 1.00 | 9,872 | 0.004 |
| fair | 5-100 | 0.06-0.09 | 0.94-0.28 | 26-2 | 0.10-0.16 |
| random | 1 | 0.50 | 1.00 | 9,436 | 0.005 |
| random | 5-100 | 0.01-0.03 | 0.94-0.27 | 19-3 | 0.01-0.05 |

Trajectories, fair start, h = 0, seed 0 (generation: mean s / mean a): T = 5: 0: 0.50/0.45, 200: 0.48/0.41,
500: 0.45/0.36, 2,000: 0.17/0.07. T = 100: 200: 0.50/0.45, 500: 0.48/0.35, 2,000: 0.09/0.08. T = 1: 100:
0.35/0.38, 500: 0.01/0.51, 2,000: 0.00/0.96.

**A reading of these numbers (hypothesis, not tested here).** Two different failures:

- **T ≥ 5: choosiness erodes first.** A lower acceptance threshold never costs its carrier anything, while a
  threshold that triggers a break-up costs search rounds. Once all offers are similar there is nothing better
  to find by leaving, so thresholds drift and are selected down (0.45 to about 0.07 from the fair start), and
  offers then fall with nothing holding them up.
- **T = 1: leaving is no punishment.** Thresholds stay high and pairs break thousands of times per generation,
  but rematching is instant for the stingy catcher as well, so being left costs it nothing, and offers fall to
  about 0.

Both point at the same gap. In step 1 a partner's outside option is a *fair* market. In step 2 the outside
option is whatever the market currently offers, and nothing in this model makes a fair partner easier to find
than a stingy one. Partner-choice accounts in the literature add ingredients this model left out (for example
variation in partner quality that persists, information about partners before pairing, or costs to the left
catcher). Which of these is needed was not tested and, under the hard stop, is not tested in this line.

## Step 3: PPG measurements (descriptive)

PredPreyGrass `deer_stag_hunt`, section 2 touch-rule runs, final checkpoints, 50 episodes each (section 2.2
settings), eval-only logger `launchers/partner_market.py` (Codex review gpt-6.1-sol: no change to dynamics, metrics
as registered); output `results/partner_market.json`. Run 2026-11-26 15:27-15:30 CET. The Kaplan-Meier median was
computed before a review fix for a floating-point tie at exactly 50% survival (fixed afterwards); with thousands
of intervals per run this can shift a median by at most one interval value.

| | touch_1 | touch_2 | touch_3 |
| --- | --- | --- | --- |
| Joint catches: adult / middle / fawn | 721 / 884 / 32 | 1,060 / 1,011 / 38 | 399 / 463 / 18 |
| Repeat-partner rate (joint catches with a pair that co-caught before, same episode) | 0.30 | 0.32 | 0.24 |
| Predator pairs that ever co-catch | 1,140 | 1,433 | 670 |
| Co-catches per pair: mean; share of pairs with ≥ 2 | 1.44; 0.29 | 1.47; 0.32 | 1.32; 0.22 |
| Co-catch cadence, Kaplan-Meier median (physics steps; observed / censored intervals) | 631 (2,422 / 853) | 513 (3,284 / 935) | 1,050 (1,129 / 632) |
| Solo-catch energy per predator-alive step | 0.0106 | 0.0102 | 0.0113 |
| Realized energy per participant, joint adult catch | 1.43 | 1.43 | 1.43 |

**Reading (descriptive).** Partners do meet again, but not often: about a quarter to a third of joint catches
repeat an earlier pair, and about 70% of pairs that hunt together do so only once per episode. A predator's joint
catches are hundreds of physics steps apart. Over one such interval its solo-catch income (about 0.0105 × 500-1,000
≈ 5-11 energy) is several times one share of an adult (1.43). So the outside option without a partner is not small
in PPG. In step-2 terms that is a high h, which made no difference in step 2. A PPG partner-choice module would
first need hunters that can recognise each other and meet again much more often. Under the KILL verdict no such
module is planned. These numbers are recorded as a design note for any later reputation module.

## What this means for the goal

Partner choice by leaving, in its simplest form (inherited offers and thresholds, memory of one offer, anonymous
random rematching), does not support fair sharing here. That is a statement about this minimal market, not about
partner choice in general. The reading above suggests that what is missing is information: knowing who is fair
before pairing. That is reputation (indirect reciprocity), the candidate mechanism already named as next in
`PREREG_SCREEN.md`.
