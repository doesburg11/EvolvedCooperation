# Rung 5b′: empathetic judging with mutation, results (2026-11-27)

Pre-registration: `PREREGISTRATION.md` (agreed about 23:05 CET, before the model copy or any run). Code commit
5b28632. Rung 5a's setting (private views, μ = 0.001, b/c 3, q 0.8, o 0.5, e 0.1, a 0.02) with empathetic judging;
seeds 3400-3499, 100 test and 100 shuffled runs, 2,000 generations. All 200 runs passed validation, the stored-view
checks and the sanity rule: the runner returns MET only after `validate()` succeeds and with zero check mismatches and
sanity violations in every run (`run.py` `verdict`; per-run counters in `data/rung5b_runs.csv`). Benchmark projection 8.0 CPU-hours; actual 13.3 CPU-hours (limit 40).
Summary: `results.json`.

## Verdict: met

| | Test | Shuffled |
| --- | --- | --- |
| Cooperators ≥ 0.8 at generation 500 | 99/100 | 0/100 |
| Mean cooperators ≥ 0.8 over generations 1,501-2,000 | 95/100 | 0/100 |
| Both endpoints (bar: test ≥ 80, shuffled ≤ 20 on each) | **95/100** | 0/100 |

## Reported, not tested

| Test arm | Rung 5a (own view) | **Rung 5b (empathetic)** |
| --- | --- | --- |
| Runs meeting both endpoints | 45/100 | **95/100** |
| Mean cooperators, generations 1,501-2,000 | – | 0.949 |
| Mean ALLC / ALLD, generations 1,501-2,000 | – | 0.072 / 0.051 |
| Mean DISC at generation 500 / over the window | – | 0.90 / 0.88 |
| Runs with DISC ≥ 0.5 at generation 500 / over the window | – | 99 / 95 |
| Runs ever below 0.5 cooperators | – | 5 |
| Runs dropping below 0.8 after generation 500 (median first drop) | – | 9 (generation 1,512) |
| Pooled help rate | – | 0.81 |
| Residual disagreement (observer saw the recipient as good at an intentional refusal) | 0.581 | 0.594 |

Shuffled arm: ALLD 0.986 over the window in the mean; the shuffled-refusal disagreement ratio is 0.594.

**Reading (hedged).** With private views and recurrent mutation, the test-arm maintenance endpoints were met in
45/100 runs at rung 5a; with empathetic judging (and fresh seeds), they were met in 95/100, with discriminators the large majority
(about 0.88 over the late window) and unconditional cooperators about 0.07. Observers still disagreed with the donor
in about 59% of the observations of intentional refusals, so disagreement itself remained; under empathetic judging,
the observer's disagreement was not used in assessing these unhelped acts. The two runs are independent samples with different seeds, so the comparison is
between experiments, not a paired effect estimate. The result is consistent with the bridge diagnosis (discriminators
losing ground through judged-bad justified refusals), but this experiment does not test that mechanism directly.

**Limits.** Maintenance from a cooperative start over 2,000 generations at this setting; not recovery, spread from
rare or indefinite stability (9 runs dipped below 0.8 after generation 500). Observers are assumed to know the
donor's view of the recipient, an informational assumption that is neither costed nor evolved.

**What follows (pre-registration).** Empathetic judging with mutation sits on the reordered ladder as rung 5b′ (5b is the earlier gossip follow-up). The
next rung needs a new proposal and the user's agreement.
