# Self-routing diagnostic for the shared Moran engine (pre-registration DRAFT, 2026-11-25)

**Status: DRAFT, not agreed with the user, no Codex review. Code written
(`moran_models/interaction_kernel/utils/self_routing_diagnostic.py`); only its deterministic checks (`MODE = "check"`) have
been run, none of the registered runs.** Stage 0 result (2026-11-25, 13 s): all 17 checks passed; the `self` arm
reproduced the stored 2026-05-08 replicates exactly (difference 0.0) for all four mechanisms; 2.1-2.5 s CPU per
250-step run, so the registered run (832 runs) projects to about 32 minutes on one core. The checks run no `noself`
arm with `B` or `C` above 0.

## Why

In the shared Moran engine (`moran_models/interaction_kernel/core/`), `include_self_in_neighborhood` is `True` in
`DEFAULT_CONFIG` and every Nowak wrapper inherits it. The same neighbourhood mask is used for benefit routing and for
replacement, so a producer routes part of its own benefit to itself. The ladder's step 0 found this for kin
selection (weak altruism: the helper's marginal direct payoff is not negative). The same routing is used by the
network-reciprocity, group-selection and indirect-reciprocity wrappers.

**Exploratory observation that motivates this test (seen, not registered).** In the 2026-05-08 emergence comparison
(`compare_emergence_baselines_20260508_134242_summary.csv`), the sign of the helper's marginal direct payoff
`B/5 − C` (uniform routing over self + 4 von Neumann neighbours) matches the sign of the mean trait change in
**9/9 cells** for network reciprocity and **9/9** for group selection, and the size of the gain ranks with it
(network: +0.14 → +0.49, +0.10 → +0.36, +0.06 → +0.29, +0.04 → +0.17, 0.00 → +0.02). Kin selection's rare-helper
direct payoff (`B/2 − C`, no same-lineage neighbours) is positive in every cell, and every cell rose. In the
indirect-reciprocity wrapper, routing weights are `bias + reputation`, including the producer's own reputation, so
a rare helper among low-reputation neighbours keeps about 65% of its own benefit (`(0.1 + 1)/(0.1 + 1 + 4·0.15)` at
`h` = 1, neighbour reputation 0.05), a direct payoff of about +0.45 per unit `h` at `B` = 1, `C` = 0.2.

A sign match across a sweep is not a causal test. This diagnostic removes the self-route and leaves everything else
as it was.

**Not affected:** the engine's direct-reciprocity mechanism (`partner_memory` removes the diagonal unless
`direct_reciprocity_include_self_interaction` is set), the discrete direct-reciprocity models (pair games) and
`indirect_reciprocity/well_mixed_binary` (self-pairing excluded). They are not part of this test.

## Design

**The original comparison, unchanged:** mechanisms indirect reciprocity, network reciprocity, group selection, kin
selection, each with its wrapper config; `B` in {0.8, 1.0, 1.2} × `C` in {0.10, 0.20, 0.30}; seeds 0-7; 250
synchronous steps; success per run = final mean trait ≥ 0.50 and gain from the start ≥ 0.05.

**Two arms per run, paired by seed:**

| Arm | Routing neighbourhood | Replacement neighbourhood |
| --- | --- | --- |
| `self` | as in the original (self + 4 von Neumann neighbours) | unchanged |
| `noself` | the same with the producer's own site removed (diagonal of the routing mask set to False), before the kernel is normalised | unchanged (self included) |

The engine draws random numbers only for the initial state and in replacement; routing is deterministic. The two
arms of a seed therefore start from the same state and differ only through fitness.

**Descriptive high-benefit cells** (both arms, same seeds, no verdict): `C` = 0.2 and `B` in {1.6, 2.4, 3.2, 4.8}
(b/c 8, 12, 16, 24). Without self-routing, network reciprocity's per-edge benefit is `B/4`, so per-edge b/c is 2,
3, 4 and 6 against `k` = 4 (Ohtsuki et al. 2006, death-birth updating; this engine uses synchronous softmax
replacement, so no threshold is predicted).

## Stage 0: checks (before any registered run)

1. `noself` routing mask: diagonal all False, every off-diagonal entry equal to the `self` mask; replacement
   neighbourhoods identical in both arms.
2. `noself` positive kernel at the start: diagonal all 0, every row sums to 1 (within 1e-12).
3. **Reproduction:** the `self` arm at `B` = 1.0, `C` = 0.2, seed 0 reproduces the stored 2026-05-08 replicate
   `final_mean_trait` within 1e-12, for each of the four mechanisms.
4. With `B` = `C` = 0, `self` and `noself` give identical mean-trait trajectories (50 steps, seed 0) for each
   mechanism.

**If any check fails, stop and report; no registered run.**

## Registered analysis

**Cells of interest** (fixed now from the stored data: cells where the original mean gain was ≥ +0.05):

| Mechanism | Cells (`B`, `C`) | n |
| --- | --- | --- |
| Indirect reciprocity | all nine | 9 |
| Network reciprocity | (0.8, 0.1), (1.0, 0.1), (1.2, 0.1), (1.2, 0.2) | 4 |
| Group selection | (0.8, 0.1), (1.0, 0.1), (1.2, 0.1), (1.2, 0.2) | 4 |
| Kin selection | all except (0.8, 0.3) | 8 |

Per cell of interest, from the `noself` arm:

- **dependent cell:** 0/8 successes and mean gain < +0.05;
- **surviving cell:** ≥ 4/8 successes and mean gain ≥ +0.05;
- otherwise **mixed cell**.

**Verdict per mechanism (mechanical):**

1. If Stage 0 failed: **not run**.
2. **Self-benefit-dependent** if at least 75% of its cells of interest are dependent cells: at these settings, the
   2026-05-08 spread from a low start needed the self-route, and it is weak altruism, not costly cooperation.
3. **Survives without self-routing** if at least 75% of its cells of interest are surviving cells.
4. Otherwise **mixed**.

**Reported for every cell (both arms):** mean initial and final trait, mean gain, successes, seed-paired difference
`noself − self` in final mean trait and the number of seeds with `noself` lower; mean self-share of the positive
kernel at the start and the end of the run (`self` arm; 0 in `noself` by check 2).

## Predictions (mine, before any registered run)

- Stage 0 passes: 90%.
- Kin selection self-benefit-dependent: 85% (the ladder's step 0b removed self from routing at `B` = 1: S-kin 0/20).
- Network reciprocity self-benefit-dependent: 85%.
- Group selection self-benefit-dependent: 70% (group copying is a second channel).
- Indirect reciprocity self-benefit-dependent: 40%. Without the self-route, neighbours still route help towards a
  high-reputation helper, which is the mechanism itself, so part of the spread may survive.
- In the high-benefit cells, `noself` network reciprocity spreads (≥ 4/8 successes) only at `B` = 4.8: 50%.

## Budget and hard stop

832 runs (4 mechanisms × 13 cells × 8 seeds × 2 arms) of 250 steps on a 24 × 24 grid; expected well under an hour
on one core (measured in Stage 0 and reported). Code gets a Codex review before the registered run. **Hard stop:**
one run; no other steps, cells, seeds or criteria under this pre-registration. A longer horizon, if wanted, is a
new pre-registration.

## What this would and would not show

- **Dependent** for a mechanism: its engine-wrapper result is weak altruism and should be relabelled on the site
  like kin selection's step 1. It does **not** show that the mechanism cannot support costly cooperation; it shows
  that this implementation did not test that.
- **Survives**: the wrapper's spread from a low start does not need the self-route at these settings; costly
  cooperation is still not established without a cost-only check of the remaining channels.
- 250 steps is short; a mechanism that is favoured but slow may be classed as dependent. The seed-paired
  differences and the high-benefit cells are reported to make that visible.
