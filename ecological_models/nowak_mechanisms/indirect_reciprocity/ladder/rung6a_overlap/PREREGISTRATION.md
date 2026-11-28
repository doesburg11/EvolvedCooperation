# Rung 6a: overlapping generations, pre-registration (2026-11-28)

**Status: agreed with the user 2026-11-28, before the model copy or any run.** First ecological rung, after rung 5c (C2, p = 0.75, met 92/100). The user asked for
small steps, especially at the beginning. If agreed, an explicit, dated exception to the earlier stops for this one
step; all earlier results stand.

## Change from rung 5c C2: one ingredient

Setting: rung 5c C2 exactly (N = 1,000, k = 10, b/c 3, s = 0.1, q = 0.8, o = 0.5, e = 0.1, a = 0.02, μ = 0.001 per
offspring, private views reset to good at the start of every generation, empathy p = 0.75 per observation, start
10% ALLC / 80% DISC / 10% ALLD, test and shuffled arms, main condition only). **The only change:** each generation,
after play, **r = 0.5** of the population (500 slots) is replaced and the rest survive:

1. **Survivors:** 500 individuals chosen uniformly at random without replacement, independent of payoff and
   strategy, keep their strategy. Counts by strategy are drawn as a multivariate hypergeometric (sequential
   hypergeometric draws ALLD, then ALLC among the rest), from the model's seeded stream, **before** any offspring
   draw; a category with zero members gives zero survivors without a draw. With r = 1 the survivor step is skipped
   entirely (no random draws), so the r = 1 path is identical to rung 5c's on the same seed.
2. **Offspring:** the other 500 slots are filled by rung 5a's fitness-weighted reproduction over **all** 1,000
   parents (fitness 1 + s × net payoff / k), drawn as rung 5a's sequential binomials with n = 500; mutation μ applies
   to offspring only, by rung 4b's `mutate_detail` on the offspring counts.
3. Next generation = survivors + mutated offspring. Payoffs are earned anew each generation (no accumulation);
   survivors carry no views or payoffs (views reset as before).

**Horizon rescaled to equal births** (`THEORY_SCREEN_OVERLAP.md`): **4,000 generations**; endpoints: cooperators
(ALLC + DISC) ≥ 0.8 at **generation 1,000**, and mean cooperators ≥ 0.8 over **generations 3,001-4,000** (the same
number of births as rung 5c's generation 500 and window 1,501-2,000).

**Code.** A copy of rung 5c's model (`rung6a_overlap/model.py`) with a new `generation` step as above; play,
assessment, empathy, checks and sanity rule unchanged. The audit row keeps its ten columns (offspring before
mutation, mutants, transfers, encounters) and **appends three survivor columns** (ALLC, DISC, ALLD). The validator
checks: offspring sum to 500 (replacing rung 5c's N); survivors sum to 500 and do not exceed each strategy's count
in the previous generation (`counts[:-1]`, DISC derived); rung 5c's mutation-source and transfer bounds; next counts
= survivors + mutated offspring for ALLD and ALLC. Every row records r and the replacement count, validated against
the frozen values. The mutant diagnostic range uses Binomial(500 × GENS, μ). A copy of rung 5c's runner with GENS =
4,000, the endpoints above, seeds and data folder, empathy **fixed at 0.75** (rung 5c's C1/C2 step selection
removed); the benchmark projects 200 runs of 4,000 generations. Equal births means doubled encounters and view resets
per birth: this is part of the ingredient.

**Tests before the run.** r = 1 path (all replaced, no survivors) reproduces rung 5c's `generation` exactly on the
same seed; survivor draws are uniform and strategy-blind (sampling test, frozen: 20,000 draws of 500 from a 300/500/200 mix:
mean counts within 1 of 150/250/100 and per-strategy variances within 10% of the multivariate hypergeometric values,
plus an exact distribution check on a population of 6); offspring mutation only on offspring; accounting corruption tests (survivors > count, transfer
imbalance, wrong offspring total) are rejected by the validator; rung 5c's other tests retargeted.

## Test and criteria

Test and shuffled arms, 100 runs each, **seeds 3700-3799** (fresh). **Met** if at least 80/100 test runs meet both
endpoints and the shuffled arm meets each endpoint in at most 20/100. Rung 5a's validity rules, in-model checks,
benchmark gate (40 CPU-hours), heartbeat watcher and one-repair rule.

**Theory screen (mean field, birth-scaled endpoints):** at r = 0.5 cooperators 0.986 at the endpoint and over the window;
final ALLC / DISC / ALLD 0.095 / 0.891 / 0.014; shuffled 0.014; finite-time cliff 0.0039 (identical to r = 1 within
the bisection's resolution; `theory_output.txt`). The
fixed points coincide with rung 5c's for any r > 0; trajectories and finite-time thresholds can differ. Not a
pass-rate forecast.

**Reported, not tested:** rung 5c's reported summaries (DISC shares and counts, ALLC and ALLD, first drop below 0.8
after generation 1,000, per-run values, residual disagreement, realised empathetic share, help rate), and the survivor
and offspring totals.

## Hard stop

This one step. A valid **not met** ends it; no other r, horizons, seeds or conditions. A pass allows a proposal for
the next small ecological step (for example, views kept across generations by survivors), which needs the user's
agreement.

## Interpretation limits

Maintenance from a cooperative start over a horizon of equal births, at this setting. Survival is random and
payoff-blind; age, ageing and survivor memory are not modelled. Not recovery, spread from rare or indefinite
stability.

## Forecast (mine, before any data)

Met: 75%.

## Amendment A1 and technical repair (2026-11-28, before any result)

Attempt 1 was launched at 13:32 CET (commit d410a5e). Its benchmark projected 32.3 CPU-hours against the 40-hour
limit, but rungs 5b′ and 5c had used about 1.65 times their projections (8.0 → 13.3; 15.9 → 26.7 and 25.1), because
the benchmark times one process on an idle machine while 28 run in parallel. That predicted about 53 CPU-hours: the
watcher would have stopped the stage at 40 with no verdict. I stopped attempt 1 about 15 seconds after launch; **0 of
200 runs had finished and no outcome was read**. Its files are kept in `data/attempt1_aborted/`.

**Amendment A1 (agreed with the user 2026-11-28):** the CPU limit for this step is raised from 40 to **80
CPU-hours**. This is the step's one documented technical repair: attempt 2 reruns the frozen design exactly (same
seeds, settings, endpoints and criteria). No further technical repair is available for this step.
