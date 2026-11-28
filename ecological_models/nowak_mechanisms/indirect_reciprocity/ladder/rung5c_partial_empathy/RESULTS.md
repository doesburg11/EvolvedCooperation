# Rung 5c: partial empathy, results (2026-11-28)

Pre-registration: `PREREGISTRATION.md` (agreed 2026-11-28 before the model copy or any run). Code commit 9c734e1 (C1)
and 35641e9 (switch to C2 under the registered rule: C1 valid NOT MET → p = 0.75). Rung 5b′'s setting (rung 5a's,
with mutation 0.001) with each observation empathetic independently with probability p. 100 test and 100 shuffled
runs per step, 2,000 generations. Both steps returned MET or NOT MET from the runner, which happens only after
`validate()` succeeds with zero check mismatches and sanity violations. CPU measured 26.7 and 25.1 hours (run logs; projected 15.9 and 15.4; limit 40 each).
Summaries: `results_c1.json`, `results_c2.json`.

| | Rung 5a (p = 0) | **C1 (p = 0.5)** | **C2 (p = 0.75)** | Rung 5b′ (p = 1) |
| --- | --- | --- | --- | --- |
| Test runs meeting both endpoints (bar 80) | 45 | **71** | **92** | 95 |
| Shuffled runs meeting either endpoint (bar ≤ 20) | 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Verdict | not met | **not met** | **met** | met |
| Test, cooperators ≥ 0.8 at generation 500 | – | 93 | 100 | 99 |
| Test, mean cooperators over generations 1,501-2,000 | – | 0.714 | 0.910 | 0.949 |
| Test, mean ALLC / ALLD over the window | – | 0.075 / 0.286 | 0.081 / 0.090 | 0.072 / 0.051 |
| Test, mean DISC over the window; runs with DISC ≥ 0.5 | – | 0.64; 72 | 0.83; 92 | 0.88; 95 |
| Runs dropping below 0.8 after generation 500 (median first drop) | – | 35 (946) | 15 (1,358) | 9 (1,512) |
| Realised empathetic share of observations | 0 | 0.50 | 0.75 | 1 |

Each step used fresh, non-overlapping seeds (C1 3500-3599, C2 3600-3699). The random streams were separate, but C2's
setting was selected by the pre-registered rule from C1's final verdict.

**Outcome.** C1 did not meet and C2 met. Under the pre-registered decision rule, p = 0.5 did not meet and p = 0.75
met. These are results at two tested settings, with C2 selected adaptively from C1's verdict, not an estimated
threshold. The lowest tested p that met (0.75) is carried into the next proposal.

**Post-hoc diagnosis (not registered, `diagnose_erosion.py`).** Mean composition (ALLC / DISC / ALLD) before the first
drop below 0.8, in the test runs whose late-window mean was below 0.8:

| Generations before the drop | 400 | 200 | 100 | 50 | 0 |
| --- | --- | --- | --- | --- | --- |
| C1 (29 runs) | 0.13 / 0.83 / 0.04 | 0.17 / 0.75 / 0.08 | 0.27 / 0.58 / 0.16 | 0.29 / 0.51 / 0.20 | 0.25 / 0.42 / 0.33 |
| C2 (8 runs) | 0.16 / 0.82 / 0.03 | 0.18 / 0.80 / 0.03 | 0.27 / 0.71 / 0.02 | 0.39 / 0.55 / 0.07 | 0.33 / 0.46 / 0.21 |

In C2 the eroded runs followed the bridge's two-phase pattern (ALLC rising while ALLD stayed rare, then ALLD). In C1,
ALLD rose alongside ALLC from about 200 generations before the drop. Descriptive only; the mechanism is not tested.

**Limits.** As rung 5b′: maintenance from a cooperative start over 2,000 generations at this setting; empathy is a
fixed probability per observation, not a cost, trait or learned inference.
