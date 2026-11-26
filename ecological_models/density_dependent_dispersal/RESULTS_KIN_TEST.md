# Kanwal and Gardner (2022) as a kin-selection test: results

## Stage V: port validation (run 2026-11-25 21:53 to 2026-11-26 00:05 CET, commit f96375d): passed

25 cells, authors' random start, compared with the authors'-code runs of 2026-11-21 to 25
(`data/stage_v_summary.json`): A above 1/n in 20/20 cells with n > 1; mixed-model slope of A on d −0.173 (authors'
code −0.177), converged; |A_port − A_orig| ≤ 0.03 in 25/25 cells (largest 0.018); |d_port − d_orig| ≤ 0.03 in 24/25.
The one dispersal difference: at n = 2, c = 0.2 the port's population ended with every survivor attempting
dispersal (d 1.00) against 0.66 in the authors' run, with A close (0.508 vs 0.526); descriptive.

## Stage M: stopped by the registered kill rule (2026-11-26 00:38 CET)

Launched 00:07 at commit 532611c, 60 runs on 30 workers (first wave: the n = 2 cell, all arms). The interim check
(`interim_check.py`, progress files only) at 00:37, when every running run had passed generation 2,000, projected
the stage at 10.1 h after launch, above the registered 6 h, so the runner was stopped as registered. No run had
finished and no trait value was read (only generation counts and elapsed times).

Speeds in the first wave (mean over the 10 runs per arm): T 0.35 s per generation, F 0.35, **X 0.89** (the X arm
permutes all 5 million juveniles every generation). The budget in the pre-registration (about 3 h) was based on a
single run's speed (0.2 s per generation) and did not account for the slowdown with 30 concurrent runs (Stage V
already showed 0.31 s at 25) or for the cost of X's shuffle.

**Status:** no verdict; the test has not been run to completion. Any rerun needs a decision by the user (amendment).

**Rerun (amendment A1, agreed 2026-11-26):** Stage M relaunched at 09:31 CET at commit 0ec0c0f with a faster X
shuffle (same model in distribution), T and F byte-identical to the Stage V code, X runs first and an 8 h kill
rule. Trait values seen before the rerun (benchmarks, early generations) are disclosed in the amendment.

## Stage M rerun (amendment A1): met in both cells (2026-11-26, 09:31 to 15:18 CET, commit 0ec0c0f)

All 60 runs completed (5.8 h; the 8 h interim rule was never breached). Registered analysis
`analyze_test.py M` → `data/stage_m_summary.json`. A = zbar / (1 − zbar) over the last 1,000 of 20,000
generations, from the no-helping start (z = 0 everywhere).

| Cell | Arm | Runs at endpoint (A ≥ 1/n) | A, range over 10 runs | mean A | d (dispersal attempts / survivors) |
| --- | --- | --- | --- | --- | --- |
| n = 2, c = 0.8 (endpoint 0.5) | T (authors' model) | **10/10** | 0.621-0.629 | 0.624 | 0.258-0.263 |
| | X (relatedness removed) | **0/10** | 0.111-0.113 | 0.112 | 0.000 |
| | F (fixed dispersal) | 10/10 | 0.525-0.531 | 0.528 | 0.298-0.300 |
| n = 5, c = 0.8 (endpoint 0.2) | T | **10/10** | 0.438-0.449 | 0.442 | 0.100-0.103 |
| | X | **0/10** | 0.111-0.114 | 0.112 | 0.000 |
| | F | 10/10 | 0.296-0.302 | 0.300 | 0.122-0.124 |

- **H1 (definition):** T at the endpoint in 10/10 runs and X in 0/10, in both cells.
- **Net-cost check:** passed. In every T run the share of helping given at a net direct cost to the helper's own
  survival was 1.00 over the whole run and over the last 1,000 generations, against the registered ≥ 0.95.
- **Classification:** both cells "met" → **verdict: met**.
- **H2 (paper's mechanism, secondary):** T's A above F's in 10/10 seed pairs in both cells → criterion met
  (an endpoint comparison; it does not identify the mechanism causally).
- **Validity:** 60/60 runs complete. One empty-patch refill in the whole stage (T, n = 2, seed 101; expected
  none).

**Reading.** From an all-zero start, where helping enters only by mutation, costly help to patch-mates (the
sub-case among non-offspring relatives) rose in the authors' model to late-run levels (A 0.624 and 0.442)
comparable to those the authors' random-start runs settle at (A 0.62 and 0.45 at these cells, Stage V and the
authors' code). This is establishment under the registered criterion, not a test of invasion by a single rare
lineage. In X, the shuffle broke up patch-level kin clustering and A stayed at about 0.112 in both cells, close to
the mutation-only floor the theory screen predicted (A about 0.11). By the registered rule this is **met**. The
shuffle also changes other things: local genotype mix, patch productivity and competition, and dispersal
evolution (X's dispersal rate at the end was about zero). So, by the site's convention for controls that change
several things, the result is read as **consistent with** kin selection, not as an isolation of relatedness alone.

The H2 comparison is consistent with the paper's density-dependence mechanism but does not identify it causally.
F is not a single-change comparison: its evolved dispersal rate also differed from T's (mean d 0.299 vs 0.261 at
n = 2; 0.123 vs 0.101 at n = 5). F also ended above Taylor's value 1/n in every run (A 0.53 vs 0.5; 0.30 vs 0.2),
so in these runs fixed dispersal did not bring helping down to the cancellation value; why was not tested
(mutation may contribute, as it holds X at about 0.11).

**Seen before the rerun (amendment A1):** trait values were read before the rerun only for n = 2: T and F slightly
above the endpoint at 3.5-6.5% of the run, X near the floor. None were read for n = 5; the completed rerun gave the
same classification there. The fixed-population setting keeps this result in the first block of the site's table
(a reference row, not a step).
