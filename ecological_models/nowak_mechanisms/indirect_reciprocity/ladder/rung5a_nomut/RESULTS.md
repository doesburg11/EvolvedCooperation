# Rung 5a′: private views before mutation, results (2026-11-27)

Pre-registration: `PREREGISTRATION.md` (agreed about 21:50 CET, before the adapter or any run). Adapter commit b97b234;
rung 5a's model and runner unchanged, μ = 0, seeds 3300-3399, 100 test and 100 shuffled runs, 2,000 generations.
All 200 runs passed rung 5a's validation and in-model checks and the registered mutation-free check (no mutant or
transfer in any generation). Benchmark projection 7.2 CPU-hours (limit 40). Rung 5a's own summary file carries the
runner's verdict before the mutation-free check; the registered verdict is the adapter's (`results.json`).

## Verdict: met

| | Test | Shuffled |
| --- | --- | --- |
| Cooperators ≥ 0.8 at generation 500 | 94/100 | 0/100 |
| Mean cooperators ≥ 0.8 over generations 1,501-2,000 | 94/100 | 0/100 |
| Both endpoints (bar: test ≥ 80, shuffled ≤ 20 on each) | **94/100** | 0/100 |

## Reported, not tested

| Test arm | Value |
| --- | --- |
| Runs in which ALLD went extinct | 94/100, all by generation 500 (median generation 87.5); no reappearance |
| Mean ALLC / ALLD over generations 1,501-2,000 | 0.02 / 0.06 |
| Mean DISC share at generation 500 / over generations 1,501-2,000 | 0.84 / 0.92 |
| Runs with DISC ≥ 0.5 at generation 500 / over the window | 90 / 93 |
| Test runs ever below 0.5 cooperators | 6 |
| Pooled help rate; disagreement penalty | 0.76; 0.64 |

In the shuffled arm, ALLD never went extinct and took over every run (mean ALLD 1.00 over the window).

**Reading (hedged).** The six endpoint failures were exactly the six test runs in which ALLD did not go extinct
(seeds 3304, 3315, 3325, 3326, 3377 and 3384; from `data/per_run.csv` and the saved trajectories). In the other 94, ALLD was
lost early (by generation 500, median 87.5), and cooperation then held with discriminators as the large majority
(about 0.92). This late-window mean (ALLC about 0.02, DISC 0.92, ALLD 0.06) differs from the pre-registered
mean-field final composition (ALLC 0.30, DISC 0.70, ALLD 0); that compares a window mean with a final state. The
bridge runs with mutation had higher late-window ALLC means (0.217 in B1, 0.320 in B2). At this setting, the
pass/fail split coincided exactly with early ALLD extinction: all 94 runs with extinction passed, and the six without
it failed. Without mutation, nothing tested whether the cooperative state resists defectors
that return. Within 2,000 generations from this cooperative start, the pass shows maintenance of cooperative
strategies under private, disagreeing views with a shuffled control that failed in every run. It does not show
recovery, spread from rare, resistance to re-invading defectors or indefinite stability.

**What follows (pre-registration).** Private views now sit on the reordered ladder as rung 5a′. The next step is not
authorised by this result. Mutation on top of private views has already failed (rung 5a, 45/100), so any next rung
needs a new proposal and the user's agreement.
