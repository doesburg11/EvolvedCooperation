# Bridge to rung 5a: results (2026-11-27)

Pre-registration: `PREREGISTRATION.md` (agreed about 20:20 CET, before the adapter or any run). Adapter commit
172f59a (B1) and cdf8ff5 (switch to B2 under the registered transition rule). Rung 5a's model and runner unchanged;
main condition only, 100 test and 100 shuffled runs per step, 2,000 generations, μ = 0.001. All 400 runs passed
rung 5a's validation and in-model checks. Benchmark projections 7.3 and 7.2 CPU-hours (limit 40).

| | Rung 5a (b/c 3, e 0.1, q 0.8) | **B1** (b/c 5) | **B2** (b/c 5, e 0.02, q 1) |
| --- | --- | --- | --- |
| Test runs meeting both endpoints (bar 80) | 45 | **59** | **60** |
| Test runs, cooperators ≥ 0.8 at generation 500 | – | 97 | 98 |
| Test runs, mean cooperators ≥ 0.8 over generations 1,501-2,000 | – | 59 | 60 |
| Shuffled runs meeting either endpoint (bar ≤ 20) | 0 | 0 / 0 | 0 / 0 |
| Verdict | not met | **not met** | **not met** |
| Test arm, mean cooperators over generations 1,501-2,000 | – | 0.624 | 0.649 |
| Test arm, mean ALLC / ALLD over generations 1,501-2,000 | – | 0.217 / 0.376 | 0.320 / 0.351 |
| Test runs ever below 0.5 cooperators | – | 43 | 43 |
| Theory screen, mean cooperators late (mean field) | 0.932 | 0.966 | 0.984 |

Reported, not tested (option A), test arm: mean DISC share 0.662 (B1) and 0.573 (B2) at generation 500, 0.407 and
0.329 over generations 1,501-2,000; runs with DISC ≥ 0.5 over that window: 56 (B1) and 29 (B2). Disagreement penalty
(share of observed intentional refusals in which the observer saw the recipient as good): 0.612 (B1), 0.659 (B2).
Per-run DISC values: `data/b1|b2/disc_per_run.csv` (not committed); summaries `results_b1.json`, `results_b2.json`.

**Outcome.** Both steps are valid **not met** results, so the bridge line ends at its agreed hard stop. Neither
tested setting met the registered maintenance-and-control criterion. Almost every test run was still cooperative at
generation 500 (97 and 98/100), but about 40 runs per step fell below the bar by the late window. The shuffled control
had zero runs meeting either registered endpoint.

**Interpretation (hedged).** Across these independent samples, the settings with higher benefit (and, for B2,
lower execution error and full consultation) coincided with joint pass counts of 59/60 against rung 5a's 45, but not 80, whereas the mean-field screen predicted
0.97-0.98 cooperators in the same settings. The gap between high generation-500
cooperation and the lower late-window pass counts is consistent with late stochastic erosion that the mean-field
screen does not represent; it is not evidence of a deterministic cliff. This experiment does not identify the cause. Differences from the
authors' model that were not tested here include observation rate (o), population size, mutation (the authors' runs
have none), the Wright-Fisher versus pairwise-imitation updating, and the re-judging schedule. The seeds differ from
rung 5a's, so the change from 45 to 59/60 is a comparison between independent samples.

## Post-hoc diagnosis: how the eroded runs collapsed (not registered, no new runs)

`diagnose_erosion.py` reads the saved test-arm trajectories. In the 41 (B1) and 40 (B2) runs that fell below 0.8
cooperators after generation 500 (median first drop at generation 1,034 and 1,133), the mean composition before the
drop was:

| Generations before the drop | 400 | 200 | 100 | 50 | 0 |
| --- | --- | --- | --- | --- | --- |
| B1 ALLC / DISC / ALLD | 0.32 / 0.67 / 0.01 | 0.44 / 0.53 / 0.02 | 0.57 / 0.40 / 0.04 | 0.62 / 0.31 / 0.07 | 0.52 / 0.24 / 0.24 |
| B2 ALLC / DISC / ALLD | 0.43 / 0.56 / 0.01 | 0.55 / 0.44 / 0.01 | 0.65 / 0.32 / 0.03 | 0.72 / 0.22 / 0.06 | 0.60 / 0.16 / 0.24 |

The runs that held kept a roughly stable composition (B1 about 0.31 / 0.66 / 0.02 from generation 1,000 on; B2
about 0.45 / 0.52 / 0.02). No eroded run recovered by generation 2,000.

**Reading (descriptive, hedged).** Collapse followed a two-phase sequence: unconditional cooperators first displaced
discriminators over a few hundred generations, while defectors stayed rare; once discriminators fell to about a
quarter or less, defectors rose within roughly 50 generations. This is consistent with the private-view penalty on
discriminators (a discriminator's justified refusal is often judged bad by observers who disagree) letting ALLC
spread at their expense, after which too few discriminators remain to contain defectors, which mutation keeps
re-introducing. Whether ALLC's spread is mainly selection or drift, and how much mutation matters, is not tested here.
