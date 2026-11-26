# Partner choice with reputation: theory screen results (2026-11-26)

**Registered verdict: KILL; PPG module gate not met.** Within the registered grid, no choice-arm cell reached the
fairness criterion (≥ 16 of 20 seeds with mean offer ≥ 0.4) at any q, from any start, at any T, including T = 1
with q = 1. V1 (no-choice control ≤ 0.25) and V2 (q = 0 reproduces the earlier screen exactly) held. Under the
registered hard stop this model gets no tweak rounds.

Pre-registration: `PREREG_REPUTATION.md` (agreed 2026-11-26, revised after a Codex review before any code). Code at
commit 2b175e2 (Codex review gpt-6.1-sol; before it, the unit tests caught a variable-shadowing bug in which the
receiver index overwrote q after the first hunt; fixed before any registered run). Registered run 16:13-16:14 CET:
2,160 runs, 1.0 min (projection after 60 runs: 0.02 h). Data check passed.

**V2 detail:** all 360 q = 0 choice runs matched the earlier screen's per-generation mean s and mean a (float32,
exact) and five summary columns (to 1e-12).

## Registered results

Mean offer s (generations 1,801-2,000), 20 seeds per cell: fair seeds of 20 were **0 in every choice cell** (90
cells). Cell means:

| Start | h | T | q = 0 | 0.25 | 0.5 | 0.75 | 1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| exploiter | 0, 0.1 | 1, 5, 20 | ≤ 0.006 | ≤ 0.007 | ≤ 0.005 | ≤ 0.005 | ≤ 0.005 |
| fair | 0 | 1 | 0.004 | 0.133 | 0.094 | 0.047 | 0.083 |
| | 0 | 5 | 0.116 | 0.095 | 0.091 | 0.067 | 0.077 |
| | 0 | 20 | 0.102 | 0.093 | 0.090 | 0.087 | 0.068 |
| | 0.1 | 1 | 0.004 | 0.069 | 0.111 | 0.126 | 0.080 |
| | 0.1 | 5 | 0.075 | 0.134 | 0.100 | 0.092 | 0.088 |
| | 0.1 | 20 | 0.103 | 0.078 | 0.094 | 0.085 | 0.139 |
| random | 0, 0.1 | 1, 5, 20 | ≤ 0.045 | ≤ 0.023 | ≤ 0.020 | ≤ 0.047 | ≤ 0.029 |

q\* is none everywhere. No cell had a catch-weighted share ≥ 0.4 (no "fair exchanges among a subset"); the
catch-weighted share was within 0.002 of the mean offer in every cell. No-choice cells: 0.004-0.005.

## Descriptive (not tests)

| | mean a, fair start (q = 0 / 0.5 / 1) | refusals per generation (q = 0.25 → 1) |
| --- | --- | --- |
| T = 1 | 0.45 / 0.06 / 0.04 | about 55-100 |
| T = 5 | 0.06 / 0.06 / 0.04 | about 1-12 |
| T = 20 | 0.06 / 0.05 / 0.05 | about 0-1 |

Fair start, h = 0, q = 1, seed 0 (generation: mean s / mean a): T = 1: 200: 0.47/0.42, 500: 0.41/0.36, 1,000:
0.31/0.23, 2,000: 0.09/0.04. T = 5: 200: 0.50/0.42, 500: 0.44/0.35, 1,000: 0.31/0.26, 2,000: 0.03/0.00.

**A reading of these numbers (hypothesis, not tested here).** The step-1 expectation registered in advance was
that reputation acts on stingy agents but not directly on the decline of thresholds, and that a role, if any,
would show at T = 1 and high q. The first part is consistent with the data: in every cell, thresholds ended low
(about 0.04-0.06 from the fair start), and with low thresholds few candidate pairs were refused at T ≥ 5. The second part was not borne out: at T = 1, thresholds ended much lower with
reputation than at q = 0 (0.04-0.06 at q ≥ 0.5 against 0.45). This is compatible with refusals costing the refuser
a round as well, but that mechanism was not isolated or tested here. In the single trajectories shown, offers
stayed relatively high for several hundred generations before declining; thresholds had already begun to decline
by then.

Taken together, the two screens are compatible with a pattern in these implementations in which choosiness gives
no lasting measured advantage, and both choosiness and offers are low by the end of the runs. The screens do not
establish that choosiness declines because it is costly, or that its decline causes offers to fall. Some
partner-choice models that sustain fairness give choosiness a persistent benefit (for example continued variation
in partners, or mutation that keeps supplying stingy partners); neither was tested here.

## What this means for the goal

Two simple biological-market screens (leaving, then leaving plus refusal by exact reputation) did not support fair
sharing with inherited rules. That is about these minimal markets, not about partner choice or reputation in
general. Under the registered hard stops, this line does not continue with variants of the same market. A
different next question, if wanted, would be how choosiness itself is maintained, a separate question that has been discussed
for partner-choice models (under what conditions choosiness can be maintained); it would need its own theory
screen before any code.
