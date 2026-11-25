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
