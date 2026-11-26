# Theory screen: help to non-offspring patch-mates in the empty-site islands (2026-11-26)

Rung 1 of the kin-ladder close-out agreed with the user on 2026-11-26 (at most two rungs, then a hard stop): can the
sub-case **among non-offspring relatives** be separated at step 5, where `STEP5_EMPTY_SITES.md` left it open (NO14
at the endpoint in 14 of 20 runs against a bar of 15; above neutral in 11 of 20 pairs)? No test arm was run for this
screen. Code: `no_offspring_screen.py`; output: `no_offspring_screen_output.txt` (and `.json`).

## Method

The island theory (`at_breakeven.py`) has no genealogy, so it cannot split patch relatedness into own offspring and
others. Fixed-trait runs of the step-5 model (h fixed for everyone, no h mutation, so nothing evolves; 1,000
patches, two seeds, statistics over 20,000 time units after a 10,000 burn-in) measure per patch class i:

- L_i, the share of donors with no eligible recipient (their gift is lost);
- R_non_i, the gift-weighted relatedness of a donor to its non-offspring patch-mates (from the neutral marker, with
  the between-patch identity as reference, as in Stage 0).

These are plugged into the analytic break-even: W_i = b (1 − L_i)(R_i A_i + B_i) − c (A_i + B_i), with demography and
reproductive values solved at the resident. **Check:** the same plug-in with all patch-mates as recipients (the T
rule) reproduces the analytic break-even (0.1385 vs 0.1387 at h = 0, 0.1149 vs 0.1154 at 0.6, 0.1027 vs 0.1028 at
1). A Codex review (gpt-6.2-sol, medium) found the masks, pooling and solver correct. Its one derivation correction
(the crowding term should be averaged over delivering donors only) changes the gradients by less than 0.00001.

## Result

At h = 0, own offspring are 2-7% of a donor's patch-mates but carry about a third of the relatedness: R_non is 0.135
against 0.198 for all patch-mates at i = 2, and 0.119 against 0.161 at i = 6. Gifts are lost mainly in two-breeder
patches (7.4%).

| b/c | Break-even c/b at h = 0 / 0.3 / 0.6 / 1 | Actual / lowest break-even | Gradient at h = 0 / 0.3 / 0.6 / 1 (×10⁻³) |
| --- | --- | --- | --- |
| 14 (the NO14 arm) | 0.095 / 0.085 / 0.077 / 0.066 | 1.08 | 0.82 / 0.46 / 0.18 / −0.16 |
| 20 | 0.095 / 0.081 / 0.070 / 0.057 | 0.88 | 2.23 / 1.48 / 0.92 / 0.31 |
| 28 | 0.095 / 0.075 / 0.062 / 0.047 | 0.76 | 4.10 / 2.58 / 1.64 / 0.68 |
| 40 | 0.095 / 0.068 / 0.050 / 0.035 | 0.71 | 6.90 / 4.00 / 2.24 / 0.86 |
| T14, for reference (all patch-mates) | 0.139 / 0.126 / 0.115 / 0.103 | 0.69 | 2.31 / 1.85 / 1.45 / 1.01 |

- **NO14** is favoured from rare, but its gradient falls to zero near h = 0.8. On the way to the endpoint (h 0.05
  to 0.6) it is 0.12 to 0.36 times T14's. This is consistent with its slower spread in Stage M, but it does not
  explain the 14-of-20 count (the neutral arm also reached the endpoint in 8 of 20).
- **NO28** is favoured at every h (actual c/b 24% below the lowest break-even; per seed 0.76 and 0.77), and its
  gradient is at least T14's at every sampled h from 0 to 0.6 (1.64 vs 1.45 at 0.6). **NO40** has T14's margin
  (0.71) but needs b = 0.2, further from the weak-selection regime the theory assumes.
- **Below the threshold:** the break-even is highest at h = 0 (0.095), so for b/c below about 10.5 non-offspring help
  is disfavoured at every h (for example b/c 5: c/b 0.2, about twice the break-even, as T3.5 was).

## The dispersal option

The paper's switch (stay if the patch has at most 5 breeders, otherwise disperse) already is density-dependent
dispersal at its ESS for these settings. Letting it evolve would add a co-evolving trait with little expected
margin, so the screen does not take it further.

## Reading

The screen passes for a test at **b/c 28** (b = 0.14, c = 0.005): help to non-offspring patch-mates should spread
from a low start with a margin and a gradient comparable to T14's. Limits: weak-selection theory, class-level
reproductive values (individual pedigree within a patch class ignored), relatedness measured at fixed resident h,
two seeds, and a grid of eight h values.
