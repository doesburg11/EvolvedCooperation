# Step 5 via a ported empty-site model (Alizon and Taylor 2008): pre-registration (DRAFT, 2026-11-25)

**Status: DRAFT, not agreed; no code, no data.** Revised once after a Codex review (gpt-6.2-sol, medium,
2026-11-25: corrected thresholds, fixed dispersal switch instead of a co-evolving one, matched relatedness
estimand, own-offspring exclusion arm, neutral reference arm, power gate, validity rules). Follows the theory screen
`theory/THEORY_SCREEN_ALIZON_TAYLOR.md`; thresholds from `theory/at_breakeven.py`.

## Why

Step 5 of the site's stepwise table (births need free space, population size not fixed) failed in every attempt so
far: R5a-R8 on the R4 ecology, the 2026-11-24 restart on the K1 lattice (hard stop), Mitteldorf and Wilson's model
(not met), and the Taylor-Davies replication (not viable). The theory screen found a published model in which empty
sites remove most kin competition, and a condition the lattice attempts did not meet: births there were limited by
space at the family scale, not by fecundity. This does not reopen the closed lattice route; it ports the paper's
population rule as a new model ("port known mechanisms rather than tune").

The help is a fecundity gift to patch-mates. With overlapping generations, patch-mates can include the donor's own
offspring, so an arm that excludes them decides the sub-case. A positive result would be the first in the table's
second block (population size not fixed). There is no energy, limited food or movement.

## Model (individual-based version of the paper's model)

- **Space:** P = 1,000 patches of n = 10 sites; each site empty or holding one asexual breeder.
- **Events (continuous time, exact stochastic simulation):** each breeder dies at rate k = 0.5, independent of its
  traits. Each breeder j reproduces at rate f_j = 1 − c·h_j + (gifts received), where h_j in [0, 1] is its
  helping trait. **Gift rule:** each breeder d gives b·h_d in total, shared equally among its eligible recipients
  in its own patch (arm-specific, below); with no eligible recipient the gift is lost and the cost is still paid.
- **Offspring placement (the paper's rule, fixed switch):** if the parent's patch has at most 5 occupied sites
  (the paper's main-text and Fig. 2 ESS at n = 10, k = 0.5) the offspring stays home, otherwise it goes to a
  uniformly random patch (any patch, own included). It lands on a uniformly random site of that patch: if empty it
  settles, otherwise it dies. A patch with more fecund breeders thus fills its empty sites faster.
- **Inheritance:** clonal. With probability μ = 0.02 per birth, h mutates by N(0, 0.04), clipped to [0, 1]. Each
  breeder carries a neutral marker that mutates to a new unique value with probability u = 0.001 per birth (for
  relatedness only), a unique id and its parent's id.
- **Start:** each site occupied with probability 0.5; h ~ N(0.05, 0.02) clipped (a low-helping start with standing
  variation, as in the ladder's rungs); every founder has a unique marker and no parent.

**Theory (weak selection, infinite islands, fixed switch, the lone breeder a cost-only class; `at_breakeven.py`).**
With b = 0.07, c = 0.005 (b/c 14, actual c/b 0.071), the population break-even c/b is 0.139, 0.126, 0.115 and 0.103
at resident h = 0, 0.3, 0.6 and 1: helping is favoured at every level. With b = 0.0175 (b/c 3.5, c/b 0.286) it is
0.130-0.139: helping is disfavoured at every level. Selection gradient per unit h per time unit: +0.0023 to +0.0010
(b/c 14) and −0.0013 (b/c 3.5).

## Stage 0: port checks and power gate (before any test arm)

Neutral (b = c = 0), 4 seeds (900-903), 20,000 time units, statistics over the last 10,000, sampled every 100.

- **0a (demography and relatedness; h fixed at 0, no h mutation):** patch-type distribution p_i within total
  variation distance 0.03 of the theory's; mean occupancy within 0.02 of 0.535; patch relatedness
  R = (Q_w − Q_b)/(1 − Q_b) from the marker (Q_w: identity over all ordered pairs of patch-mates, pooled, so
  pairs are weighted as in the theory's pair-weighted G; Q_b: identity over 10^5 random pairs from different
  patches at each sample) within 0.02 of the theory's 0.1466; and R at i = 6 minus R at i = 7 at least 0.02
  (theory 0.054), pooled over seeds.
- **0c (power gate; h mutating, b = c = 0):** the population variance of h, V(t), averaged over seeds. Predicted
  time t* for T14 to raise mean h from 0.05 to 0.60, using the smallest gradient on that range (0.00145, at
  h = 0.6): the t at which 0.00145·∫V(s)ds reaches 0.55. **Passes if t* ≤ 25,000** (a quarter of the run).
- **Runtime:** events per second measured in Stage 0; Stage M must fit in 8 CPU-hours (about 15 minutes of wall
  time on 30 cores), otherwise stop and report before Stage M.

**Gate:** 0a in every seed, 0c and the runtime check. **If any fails:** stop and report; Stage M is not run.

## Stage M: the test

20 seeds per arm (0-19, shared), 100,000 time units (about 50,000 generations), c = 0.005 except N0.

| Arm | b | Eligible recipients of a breeder's gift | Role |
| --- | --- | --- | --- |
| **N0** | 0 (c = 0) | none | neutral reference (drift and mutation only) |
| **T14** | 0.07 | the other breeders of its patch | test |
| **NO14** | 0.07 | the other breeders of its patch that are not its own offspring | sub-case: excludes own offspring |
| **X14** | 0.07 | all other breeders in the population, equally (mean-field) | control: relatedness removed |
| **T3.5** | 0.0175 | the other breeders of its patch | below the theory's threshold |

X14 keeps the total gift and cost but changes who receives it, so recipients are unrelated on average. It also
removes the link between a patch's helping and its own fecundity, and it delivers the gifts of lone breeders that
T14 loses. Because it changes several things at once, a T14-X14 separation is reported as *consistent with* kin
selection (the site's convention for such controls).

**Measures:** mean h over breeders, averaged over the last 10,000 time units. **Endpoint:** mean h ≥ 0.60.
**Viable:** at least one breeder at 100,000. Recorded every 1,000 time units: mean h, variance of h, occupancy,
patch-type distribution, marker relatedness, mean fecundity, share of all gifts going to the donor's own offspring
(T14) and share of gifts lost (all arms).

**Validity:** every run must complete (a crash stops the stage; it is reported, not rerun). An extinct run counts as
not reaching the endpoint. An arm with fewer than 18 of 20 viable runs is not interpretable.

**Classification, in this order:**

1. N0, T14 or X14 not interpretable → **not interpretable**.
2. X14 at the endpoint in more than 2 of 20 → **not met: the control did not separate**.
3. T14 at the endpoint in at least 15 of 20 **and** final mean h of T14 above N0 in at least 16 of 20 seed pairs →
   **met** (otherwise **not met**).
4. If met, the sub-case: NO14 interpretable, at the endpoint in at least 15 of 20 and above N0 in at least 16 of 20
   pairs → **among non-offspring relatives** (help spreads with own offspring excluded); otherwise **help to
   patch-mates, own offspring not excluded** (sub-case not separated).

The endpoint counts of every arm are reported whatever the classification.

**H2 (the theory's threshold, reported separately):** T3.5 interpretable and its final mean h below N0's in at least
16 of 20 pairs → **supported**; T3.5 not interpretable → **not interpretable**; otherwise **not supported**.

**Site table:** met → a new second-block row "5 (empty-site islands, Alizon and Taylor 2008)" marked ✓, worded
*consistent with* kin selection and naming the sub-case; not met → the row marked ✗.

**Interim check (at 10,000 time units, a tenth of the way), from progress files only (time reached, breeders
alive), never h:** kill rule: stop and report if any run has crashed or stopped advancing, or the projected finish
exceeds the budget. Extinctions are not a kill reason (they enter validity at the end).

**Hard stop:** one attempt; no other b, c, n, k, switches or arms under this pre-registration.

**Predictions made before the data:** Stage 0 passes: 75%. T14 met: 70%. Sub-case non-offspring (NO14 met, given
T14 met): 65%. X14 at or below 2/20: 95%. H2 supported: 85%.

## What this would and would not show

A positive result is costly help to patch-mates spreading from a low-helping start against a control that removes
relatedness (and changes demography with it), in a population whose size is not fixed and whose births need free
space: step 5, in a ported published model. The islands are an abstraction of space, not a lattice; there is no
energy, limited food, starvation or movement; dispersal follows the paper's fixed ESS switch and does not evolve.
