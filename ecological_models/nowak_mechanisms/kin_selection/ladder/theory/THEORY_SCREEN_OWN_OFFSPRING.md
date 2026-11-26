# Theory screen: help to own offspring in the empty-site islands (2026-11-26)

Rung 2 of the kin-ladder close-out agreed with the user on 2026-11-26 (two rungs in the empty-site islands, one
attempt each, then a hard stop): goal A's sub-case, kin selection through parental care, at step 5. It mirrors rung 1
(`THEORY_SCREEN_NO_OFFSPRING.md`, met 2026-11-26): one change, the recipient rule. No test arm was run for this
screen. Code: `own_offspring_screen.py`; output: `own_offspring_screen_output.txt` (and `.json`).

## Rule screened

Each donor d always pays c·h_d and gives b·h_d, shared equally among **its own offspring living in its patch**; with
none at home the gift is lost. What this is: help from a parent to its grown offspring that settled at home
(they stay home when the patch has at most 5 breeders), raising their fecundity. What it is not: care for dependent
young; the model has no juvenile stage.

## Method

Neutral runs of the step-5 model (h = 0, no gift, nothing evolves; 1,000 patches, four seeds, statistics over
20,000 time units after a 10,000 burn-in) measure per patch class i: L_i, the share of breeders with no own offspring
at home; R_i, the relatedness to the offspring at home (marker identity, between-patch reference); and the patch's
genetic mass relative to a donor that has offspring at home (1 + summed relatedness to all its patch-mates). These
enter the break-even of the island theory as in rung 1, W_i = b (1 − L_i)(R_i A_i + B_i^del) − c (A_i + B_i), where
the benefit's crowding term B_i^del uses the conditioned patch genetic mass and the cost keeps the unconditional
term. This conditioning was added after a Codex review (gpt-6.1-sol, medium). The review found the measurements
correct and the reverse direction (offspring giving to the parent) correctly excluded.

## Result

At the neutral state, 19% of breeders (breeder-weighted) have at least one own offspring at home (L_i from 0.92
at i = 2 to 0.79 at i = 6). Relatedness to them is about 0.999 (clonal inheritance; marker mutation 0.001 per birth).
Most gifts are lost, but the delivered ones go to near-clones.

| b/c | Actual c/b | Break-even c/b (every screened h) | Actual / break-even | Gradient per unit h per time unit (h = 0 to 1, ×10⁻³) |
| --- | --- | --- | --- | --- |
| 3.5 | 0.286 | 0.185 | 1.54 | −0.86 |
| 5 | 0.200 | 0.185 | 1.08 | −0.18 |
| 7 | 0.143 | 0.185 | 0.77 | +0.73 |
| 10 | 0.100 | 0.185 | 0.54 | +2.09 to +2.08 |
| **14** | 0.071 | 0.185 | **0.39** | **+3.90 to +3.87** |
| 28 | 0.036 | 0.185 | 0.19 | +10.3 to +10.1 |
| T14 for reference (all patch-mates) | 0.071 | 0.139 to 0.103 | 0.69 | +2.31 to +1.01 |
| NO28 for reference (non-offspring, met) | 0.036 | 0.095 to 0.047 | 0.76 | +4.10 to +0.68 |

The four seeds agree to within 0.02 in the ratio.

- **Passes the approximate screen at b/c 14** (b = 0.07, c = 0.005, the values of the step-5 test T14): the actual
  c/b is 0.39 of the break-even, and the gradient is above T14's at every screened level.
- **Below the threshold:** at b/c 3.5 (the values of T3.5) help to own offspring is disfavoured (ratio 1.54). The
  break-even sits near b/c 5.4.
- This fits rung 1: own offspring, although only a fifth of breeders have one at home, carry enough relatedness that
  help to them pays at a lower benefit than help to non-offspring patch-mates.

## Limits

Leading-order weak-selection screen: L_i, R_i and the patch genetic mass are measured at the neutral state and held
fixed at every resident h. Resident h enters only through class-average fecundity, so the flat break-even across h
mostly reflects that, and it is not evidence that care has no demographic feedback. Individual pedigree within a
patch class is ignored. The test arm itself is the check at positive h.

## Reading

The screen passes: a pre-registered test of help to own offspring at b/c 14, with b/c 3.5 below the threshold, is
worth running. A natural control, as in rung 1, pools the same gifts (from donors with offspring at home) to breeders
in other patches of the same size.
