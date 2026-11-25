# Step 5 via a ported empty-site model (Alizon and Taylor 2008): pre-registration (DRAFT, 2026-11-25)

**Status: DRAFT, not agreed; no code, no data.** Follows the theory screen `theory/THEORY_SCREEN_ALIZON_TAYLOR.md`.

## Why

Step 5 of the site's stepwise table (births need free space, population size not fixed) failed in every attempt so
far: R5a-R8 on the R4 ecology, the 2026-11-24 restart on the K1 lattice (hard stop), Mitteldorf and Wilson's model
(not met), and the Taylor-Davies replication (not viable). The theory screen found a published model in which empty
sites remove kin competition, and a condition the lattice attempts did not meet: births there were limited by
space at the family scale, not by fecundity. This pre-registration does not reopen the closed lattice route; it
ports the paper's population rule as a new model, following the rule "port known mechanisms rather than tune".

The help is a fecundity gift to a patch-mate, so a positive result is in the sub-case **among non-offspring
relatives**, the first result in the table's second block (population size not fixed). It has no energy, no
limited food and no movement; own-offspring care, energy and movement would be later rungs.

## Model (individual-based version of the paper's model)

- **Space:** P = 1,000 patches of n = 10 sites; each site empty or holding one asexual breeder.
- **Events (continuous time, exact stochastic simulation):** each breeder dies at rate k = 0.5, independent of its
  traits. Each breeder j reproduces at rate f_j = 1 − c·h_j + b·(H_p − h_j)/(i_p − 1), where h is its helping
  trait (0 to 1), H_p the sum of h over the i_p breeders of its patch (the gift is shared equally among the other
  breeders of the patch; a breeder alone in its patch pays the cost and its gift is lost). f_j ≥ 0 always holds at
  the registered values.
- **Offspring placement (the paper's rule):** if the parent's patch has i_p < θ_j occupied sites (θ_j: the parent's
  dispersal threshold) the offspring stays home, otherwise it goes to a uniformly random patch (any patch). It then
  lands on a uniformly random site of that patch: if the site is empty it settles there, otherwise it dies. This is
  the paper's "each competing offspring fills each empty site at rate 1/n": a patch with more fecund breeders
  fills its empty sites faster.
- **Inheritance:** clonal. With probability μ = 0.02 per birth, h mutates by N(0, 0.04) (clipped to [0, 1]) and,
  independently with probability 0.02, θ mutates by N(0, 0.3). Each offspring also inherits a neutral marker that
  mutates to a new unique value with probability u = 0.001 (for measuring relatedness only).
- **Dispersal threshold θ evolves.** The paper sets dispersal at its ESS (stay below about half full at k = 0.5).
  Letting θ evolve keeps dispersal near its ESS as fecundity changes with helping; with a fixed switch, the
  threshold c/b would fall from 0.139 to 0.079 as mean fecundity rises by 13% (screen), which would let helping
  limit itself.
- **Start:** each site occupied with probability 0.5; h ~ N(0.05, 0.02) clipped (low-helping start, as in the
  ladder's rungs); θ = 5.5.

**Theory (from the screen, weak selection, ESS dispersal):** help spreads when c/b < about 0.11-0.21 depending on the
death-to-fecundity ratio (0.139 at k/f = 0.5; 0.12-0.13 at the about 13% higher mean fecundity of a fully helping
population at the registered b and c), that is when b/c exceeds about 7-9.

## Stage 0: does the port reproduce the theory? (gate)

b = c = 0, h = 0, no h mutation; 4 seeds, 20,000 time units each, statistics over the last 10,000.

- **0a (fixed dispersal, θ = 5.5 for all, no θ mutation):** patch-type distribution p_i within total variation
  distance 0.03 of the theory's; mean occupancy within 0.02 of 0.535; patch relatedness from the neutral marker
  (identity within patches against identity between patches, R = (Q_w − Q_b)/(1 − Q_b), breeder-pair weighted)
  within 0.03 of the theory's mean G = 0.154.
- **0b (θ evolving from 5.5):** mean θ over the last 10,000 time units in [5.0, 6.5] (the ESS switch is between 5
  and 6 occupied sites).

**Passes if** all criteria hold in every seed. **If it fails:** stop and report; Stage M is not run.

## Stage M: the test

20 seeds per arm (seeds 0-19, shared), 200,000 time units (about 100,000 generations), c = 0.01.

| Arm | b | b/c | Gift goes to | Prediction |
| --- | --- | --- | --- | --- |
| **T14 (test)** | 0.14 | 14 | other breeders of own patch | spreads (c/b 0.071 < 0.12-0.14) |
| **T3.5 (below threshold)** | 0.035 | 3.5 | other breeders of own patch | does not spread (c/b 0.29 > 0.21) |
| **X14 (control, relatedness removed)** | 0.14 | 14 | all other breeders in the population, equally (mean-field) | does not spread |

X14 keeps the total gift and the cost; only who receives it changes, so the recipients are unrelated on average.
It also removes the local fecundity boost of a helping patch (that boost exists only because the recipients are
local); this is stated, not avoided.

**Measures:** mean h over occupied sites, averaged over the last 20,000 time units. **Endpoint:** mean h ≥ 0.60.
Also recorded every 1,000 time units: mean h, mean θ, occupancy, patch-type distribution, neutral-marker
relatedness, mean fecundity.

**Hypotheses and classification:**

- **H1 (definition):** T14 reaches the endpoint in at least 15 of 20 runs and X14 in at most 2 of 20.
- **H2 (theory, both directions):** T3.5 reaches it in at most 2 of 20.
- **Per-arm validity:** at least 18 of 20 runs viable (population not extinct at the end).

Classification, in this order: fewer than 18/20 viable in T14 or X14 → **not interpretable**; X14 above 2/20 →
**not met: the control did not separate**; T14 at least 15/20 → **met**; otherwise **not met**. H2 is reported
separately: if H1 is met but H2 fails, the result is reported as "met, but the theory's threshold was not
supported" (help spread below the predicted threshold too).

**If met:** a new row in the table's second block, "5 (empty-site islands, Alizon and Taylor 2008)", ✓, sub-case
among non-offspring relatives, with the limits above. **If not met:** row ✗.

**Interim check (at 20,000 time units, a tenth of the way):** all runs alive and advancing and the projected
finish within the budget; kill rule: stop and report otherwise. No look at h until all runs are complete.

**Budget:** Stage 0 and Stage M together under 2 CPU-hours (exact simulation in numba; about 10^9 events per Stage
M run). **Hard stop:** one attempt; no other b, c, n, k or arms under this pre-registration.

**Predictions made before the data:** Stage 0 passes: 75% (the relatedness check is the least certain, because
mutation and finite size bias the marker estimate). H1 met: 65% (risk: the rise may be slow at this weak selection,
s ≈ b·G − c ≈ 0.008 per unit h). X14 at or below 2/20: 95%. H2: 85%.

## What this would and would not show

A positive result shows costly help to patch-mates spreading from a low-helping start, against a
relatedness-removed control, in a population whose size is not fixed and whose births need free space: step 5 for
the sub-case among non-offspring relatives, in a ported published model. It does not include energy, limited food,
starvation, movement or care for own offspring, and the islands are an abstraction of space, not a lattice. The
dispersal threshold co-evolves; its contribution is not isolated (a fixed-switch arm is not run).
