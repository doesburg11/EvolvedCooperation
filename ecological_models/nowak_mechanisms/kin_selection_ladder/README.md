# Kin Selection Ladder: From the Moran Model to an Ecological Model (pre-registration 2026-11-19)

Status (2026-11-19): **original steps 0-0c run; none met** (T0a 14/20, T0b S-kin 0/20, T0c H-kin and H2-kin 0/20,
while uniform routing spread 20/20 at 3000 steps). The ladder was then rebuilt on a viscosity base: **step 0d met**
(local replacement 20/20 against global-competitor replacement 1/20, p = 1.5e-10) and **revised step 1, overlapping
generations, met** in attempt 1 (local 20/20 against global 0/20, p = 7e-12). The original step 1 (genomic kin
weights) was not run. See `RESULTS.md`. Each pre-registration below was revised after a Codex review, before any
code or data for that step.

## Why a ladder

The ecological kin-selection model (`../kin_selection/`) never showed kin selection cleanly. Each test exposed a
new problem: care is a lifeline, not a bonus (`../kin_selection_floor_control/`); learning adds nothing beyond a
small constant care effort (`../kin_selection_learning/`); long runs die because mates run out
(`../kin_selection_bonus_care/`, Amendment 1). Patching that model down has not converged.

This line builds up instead. It starts from the working Moran kin-selection model
(`moran_models/nowak_mechanisms/kin_selection/`) and adds one ecological ingredient per step. Each step must
reproduce the effect against its own control before the next.

**Rules (the user's, 2026-11-19).**

- One ingredient per step.
- At most 2 pre-registered attempts per step, with no parameter tuning between them.
- If a step fails, it is replaced by a smaller step from the last step that worked, for example one half of the
  ingredient. The line does not patch a failing step.

**Planned steps (later steps are pre-registered one at a time, after the previous verdict).**

| Step | Ingredient |
| --- | --- |
| 0 | The Moran model itself, at n = 20, plus a check of self-benefit (below) |
| 1 | Kin bias by genomic relatedness instead of founder labels |
| 2 | Help raises the recipient's survival instead of adding to a fitness score |
| 3 | Age structure: adults help, juveniles receive |
| 4 | Energy: help costs energy, births need energy |
| 5 | Variable population size: empty sites, regulation by space |
| 6 | Groups and households instead of grid neighbours |

## The Moran model, as it is

24 × 24 torus, von Neumann neighbourhood plus self, 1000 synchronous steps. Each site has a helping trait `h` and a
lineage label (18 founder labels, inherited clonally).

- Each site produces benefit `B·h` (B = 1.0) and pays cost `C·h` (C = 0.2).
- The benefit is shared over the routing neighbourhood. Weights: 0.8 to sites with the producer's label, 0.2
  otherwise, normalized.
- Fitness `W = 1 + received − C·h`.
- Each site is replaced by a parent from its neighbourhood (self included), chosen by softmax over `W` with
  temperature 0.12. The child gets the parent's `h` (mutation probability 0.02, s.d. 0.04) and label.
- Old proof (5 seeds): spread from rare (`h` ≈ 0.05) 5/5, uniform local routing (weights 0.5/0.5, called
  "well-mixed" in the old proof, though replacement stays local) 1/5 (mean final `h` 0.49), below Hamilton's rule (B = 0.05, common start) 0/5 maintained. Success means final mean `h` >= 0.60.

**Theory screen: helpers keep part of their own benefit.** The routing neighbourhood includes the producer itself
(`space.py`, `include_self_in_neighborhood`), and a producer always has its own label (`kernels.py`). So a producer
sends itself the highest weight. With `m` same-label neighbours, its self-share is `0.8 / (0.8(1 + m) + 0.2(4 − m))`,
and its marginal direct payoff from its own helping is `B × share − C` per unit `h`:

- No same-label neighbours: it keeps 0.8 / (0.8 + 4 × 0.2) = 0.5 of its benefit, 0.5·h against a cost of 0.2·h.
  Net **+0.3·h**: helping pays the helper directly.
- All four neighbours same-label: it keeps 0.2·h, exactly the cost. Net 0.
- No kin bias (0.5/0.5): it keeps 1/5, 0.2·h. Net 0.

So in the working model, a helper's marginal direct payoff from its own helping is never negative, and kin bias
raises it for a rare helper. This is the marginal payoff only; neighbours' help and local competition also affect
reproduction. The old spread result may therefore owe much to self-benefit rather than to benefits falling on
relatives. Step 0 tests this before anything is built on it.

## Step 0: is the Moran result kin selection?

Seeds 0-19 per arm, 1000 steps, everything else as above. Success per run: final mean `h` >= 0.60 (the Moran
proof rule). Rare start: `h` ~ N(0.05, 0.02); common start: N(0.9, 0.05).

**0a, replication as is (self in routing).**

| Arm | Change | Start |
| --- | --- | --- |
| A-kin | none | rare |
| A-nobias | kin weights 0.5/0.5 | rare |
| A-below | B = 0.05 | common |

**0b, altruism version (self removed from routing only).** The engine uses one neighbourhood for both routing
and replacement, and `include_self_in_neighborhood` = False would remove self from both. So 0b uses a separate
routing mask: the original neighbourhood with the diagonal removed, before the kin weights are normalized.
Replacement keeps the original neighbourhood, self included. The producer's benefit then goes to its four
neighbours only. Its marginal direct payoff is −0.2·h, so spread needs benefits to fall on relatives.

| Arm | Change | Start |
| --- | --- | --- |
| S-kin | self out of routing | rare |
| S-nobias | self out, uniform routing (0.5/0.5) | rare |
| S-below | self out, B = 0.05 | common |

Spatial structure alone can favour altruism in lattice models (Ohtsuki et al. 2006), so S-nobias may also spread.
Their rule does not map directly onto this model: here a total benefit `B·h` is split over four recipients
(per-edge benefit B/4, so B/(4C) = 1.25 at B = 1), and replacement is a synchronous softmax, not death-birth
updating. So no threshold is predicted. If S-nobias spreads in >= 8/20, kin bias cannot show a difference at
B = 1.0, and a lower-benefit diagnostic runs: **B = 0.6**, arms S-kin-0.6 and S-nobias-0.6, same seeds. This
condition is fixed now, before any data.

**Tests (all thresholds whole numbers of runs; one-sided Fisher exact on success counts).**

- **T0a, replication.** A-kin succeeds in >= 15/20, more than A-nobias with Fisher p < 0.05, and A-below is
  maintained in <= 2/20.
- **T0b, kin bias without self-benefit.** At B = 1.0: S-kin succeeds in >= 15/20, exceeds S-nobias by >= 8
  runs with Fisher p < 0.05, and S-below is maintained in <= 2/20.
  - If S-nobias succeeds in >= 8/20 (uniform routing alone spreads), T0b is scored at B = 0.6 instead, and that
    verdict replaces the B = 1.0 one: S-kin-0.6 >= 12/20, exceeding S-nobias-0.6 by >= 8 runs with Fisher
    p < 0.05. S-below (maintained in <= 2/20) stays required in both cases.
- **Descriptive:** mean final `h` per arm (Mann-Whitney S-kin versus S-nobias), lineage count at the end, and the
  mean `h` trajectory every 50 steps.

**Decision.**

- **T0b met:** without self-benefit, label-biased routing makes helping spread detectably more often than uniform
  routing, at these settings. That is the ladder's base: every later step keeps self out of routing.
- **T0a met, T0b not:** no detectable effect of label-biased routing once self-benefit is removed, at these
  settings. That does not prove there is none, but the ladder has no working base. Recorded, the Moran README
  gets a caveat about self-benefit, and the next step is discussed with the user (for example a textbook kin
  model as a new step 0).
- **T0a not met:** the old proof does not replicate at n = 20; recorded and discussed.

## Step 1: kin bias by genomic relatedness (pre-registered now, runs only if T0b is met)

Built on 0b (self out of routing), at the B at which T0b was met.

**Ingredient.** The ecological model recognises kin by genomic relatedness, not by inherited labels. This is a
stricter, genealogy-based kin definition, not an equivalent of labels: with all-unique founder alleles, founders
that share one of the 18 random labels have `r` = 0, so `r` measures identity by descent since the start only. Each site gets
a neutral genome of 64 loci, inherited clonally with the site's parent. Each locus mutates to a new, unique allele
with probability `mu` per birth. Founders have all-unique alleles. Relatedness `r_ij` is the fraction of loci
with the same allele. Routing weight from i to neighbour j: `0.2 + (0.8 − 0.2) × r_ij`, normalized over the four
neighbours. The labels are no longer used.

**Step 1-cal: choose `mu` (no helping: `h` = 0 everywhere, so all fitnesses are equal and parents are random).**

- Genome mutation draws come from a separate random stream, so for a given seed the genealogy (who descends from
  whom) is identical across `mu` values and identical to a label-only run. The label contrast is therefore one
  fixed reference per seed, the same for every `mu`.
- Grid `mu` in {0.001, 0.003, 0.01, 0.03}, seeds 0-4, 1000 steps.
- Pairs: each neighbour edge once (unordered), and 2,000 unordered random pairs of distinct, non-adjacent sites,
  drawn once from a fixed stream (seed 12345) and reused at every sample.
- Every 50 steps, from 100 to 1000: genomic contrast = mean `r` of neighbour pairs − mean `r` of random pairs.
  Label contrast = fraction of neighbour pairs sharing a label − fraction of random pairs sharing a label.
- Rule: `mu*` is the `mu` whose genomic contrast, averaged over samples and seeds, is closest to the label
  contrast averaged the same way; a tie goes to the lower `mu`. Both trajectories are reported, since the
  contrasts change over time and the averages can hide that. This matches one summary of kin information, not
  the kin definitions themselves.

**Arms (seeds 0-19, rare start).** G-kin (genomic kin weights) and G-nobias (weights 0.5/0.5, genome unused), plus
G-below (B = 0.05, common start).

**T1.** G-kin succeeds in >= 15/20 (>= 12/20 if step 0 was scored at B = 0.6), exceeds G-nobias by >= 8 runs with
Fisher p < 0.05, and G-below is maintained in <= 2/20.

**Decision.**

- **T1 met:** step 2 is pre-registered next.
- **T1 not met:** attempt 2 is fixed now, with the same arms and tests. It uses genomic weights with `mu*` divided
  by 10, which keeps the memory of shared descent longer, closer to founder labels.
- **Attempt 2 also fails:** the step is split into a half-step from 0b, pre-registered with the user. One candidate:
  labels kept, with weights scaled by genomic `r` only among same-label neighbours.

## Predictions (mine, before any data)

- T0a about 85%.
- S-nobias succeeds in >= 8/20 at B = 1.0 (uniform routing alone): about 35%.
- T0b about 40% overall. Without self-benefit, a rare helper's relatives are rare too, and this update rule is
  strongly selective (temperature 0.12), which hurts rare altruists.
- T1, given T0b: about 60%.

## Budget and hard stop

- Step 0: 120 runs, plus 40 if B = 0.6 is triggered. Step 1-cal: 20 runs. Step 1: 60 runs (attempt 2: 60 more).
  About 7.5 s per run on one core; a few minutes on 8 cores.
- Code gets a Codex review before running; results wording a Codex review before commit.
- No arm, threshold or parameter changes after seeing results; a failure is recorded, not tuned.

## Limits

- Strong selection (temperature 0.12) and synchronous updating, as in the Moran model; weak-selection lattice
  theory does not apply directly.
- The label model's kin bias is perfect within lineages and blind across them; genomic relatedness is graded.
- n = 20 per arm detects large differences only (>= 8 runs of 20).

## Step 0c: the half-step (pre-registration 2026-11-19, after the steps 0-1 verdict; no 0c data; revised per Codex review)

This is a *data-informed follow-up* pre-registration: its design (the half-step, the run length) was chosen after
seeing the step-0 results, so it is not an independent confirmation of the original ladder.

**Why.** Steps 0a and 0b differ in two things at once: whether the helper is in its own routing neighbourhood, and
whether kin bias raises the helper's share of its own benefit. 0a spread (14/20, one short of the bar); 0b never did
(0/20). Following the ladder rule, the next attempt is a smaller step from 0a: the helper stays in its routing
neighbourhood, but at the non-kin weight, so kin bias no longer sends help back to the helper.

**Ingredient.** Routing weights: self `w_self`, same-label neighbour 0.8, other-label neighbour 0.2, normalized
over self plus the four neighbours. Attempt 1: `w_self` = 0.2. Replacement is unchanged (self included). The
current code gives self the same-label weight; a separate `w_self` setting is added and tested before running.

**Theory screen (attempt 1).** With `m` same-label neighbours, the self-share is `0.2 / (1.0 + 0.6m)`, so the
marginal direct payoff per unit `h` is `B × share − C`:

| `m` | Self-share | Direct payoff (B = 1, C = 0.2) | Share sent to the `m` kin neighbours |
| --- | --- | --- | --- |
| 0 | 0.20 | 0 | 0 |
| 1 | 0.125 | −0.075 | 0.50 |
| 2 | 0.091 | −0.109 | 0.73 |
| 4 | 0.059 | −0.141 | 0.94 |

So a rare helper with no kin nearby is directly neutral, and helping is directly costly once kin are nearby, while
most of its benefit then goes to kin. In 0a the same helper had a direct payoff of +0.3 (m = 0) to 0 (m = 4).

**Run length.** In 0a, mean `h` in A-kin was still rising at step 850 (0.70). A weaker self-return will spread
more slowly, so all 0c arms run **3000 steps**, and A-kin is rerun at 3000 steps as a reference. This choice was made
after seeing 0a's trajectory (hence a data-informed follow-up), but before any 0c data. Success per run stays final mean `h` >= 0.60.

**Arms (seeds 0-19, B = 1.0, C = 0.2, everything else as in step 0).**

| Arm | Routing | Start | Role |
| --- | --- | --- | --- |
| H-kin | `w_self` 0.2, label weights 0.8/0.2 | rare | test |
| H-nobias | all weights 0.5 (self included) | rare | control; the A-nobias model arm, rerun at 3000 steps |
| H-below | `w_self` 0.2, label weights, B = 0.05 | common | below-rule control |
| A-kin-3k | 0a routing (self at the same-label weight) | rare | descriptive reference only |

H-nobias is uniform routing over self plus four neighbours, so the helper's self-share is 1/5 = 0.2 there too:
the control differs from H-kin only in how the neighbours' shares are weighted.

**T0c.** H-kin succeeds in >= 15/20, exceeds H-nobias by >= 8 runs with one-sided Fisher p < 0.05, and H-below is
maintained in <= 2/20. Descriptive: final `h` Mann-Whitney H-kin versus H-nobias, mean `h` every 50 steps, final
label counts, and A-kin-3k's successes.

**Attempt 2 (fixed now; runs only if T0c fails).** A smaller step still, between 0a and attempt 1: `w_self` = 0.5.
The self-share is then `0.5 / (1.3 + 0.6m)`: direct payoff +0.185 at m = 0 and −0.065 at m = 4. Arms H2-kin and
H2-below as above with `w_self` 0.5; the H-nobias runs are reused as the control (uniform 0.5 weights are the same
model). Attempt 2 meets T0c only if every T0c criterion holds with H2-kin, H-nobias and H2-below in place of H-kin,
H-nobias and H-below, with one change: because the control is reused and a second test is run, its Fisher threshold
is p < 0.025 (Bonferroni over the two attempts). Same run length.

**Decision.**

- **T0c met (attempt 1 or 2):** that half-step is the ladder's base. Step 1 (genomic kin weights) is re-registered
  on that base before it runs, keeping step 1's design and adapting only the base and run length.
- **Both attempts fail:** under the tested arms, the only one that met (or nearly met) the spread bar was 0a, which
  had the largest rare-helper self-return. These tests change self-return, routing and dynamics together, so they do
  not show that self-return caused the difference. The ladder stops at the Moran level, recorded, and the next move
  is decided with the user (for example the higher-benefit altruism base).
- The ladder's two-attempt rule is exploratory: a pass is a working base to build on, not a confirmed effect.
- No re-scoring of 0a at 3000 steps: A-kin-3k is descriptive only.

**Predictions (mine, before any 0c data).**

- H-kin attempt 1 meets T0c: about 30%. Kin competition still applies, and the rare helper gains nothing directly.
- H-nobias at 3000 steps succeeds in >= 8/20: about 40% (A-nobias was rising: 0.35 at step 850). If it does, the
  >= 8-run difference becomes hard to reach.
- Attempt 2 meets T0c, given attempt 1 fails: about 45%.
- A-kin-3k succeeds in >= 15/20: about 80%.

**Budget.** 80 runs of 3000 steps (about 22 s each), plus 40 for attempt 2: about 5 minutes on 8 cores. Codex
reviews the code before running and the wording before commit.

## Revised ladder: viscosity base (user decision 2026-11-19, after step 0c)

Steps 0-0c showed, at these settings, that helping spread only where it had no net direct cost to the helper, and
that label kin discrimination gave no lasting advantage (`RESULTS.md`). The spreading arms are consistent with weak
altruism in a viscous population, but viscosity was never varied. The user chose to rebuild the ladder on that base.

**Revised plan (each step pre-registered after the previous verdict; each tested against a global-competitor
replacement control, which strongly reduces viscosity. The control and the endpoint are re-checked at every step,
since each ingredient can change what fitness and competition mean).**

| Step | Ingredient |
| --- | --- |
| 0d | Base: uniform routing (helper keeps 0.2·h, its cost), local replacement; control: global replacement |
| 1 | Help raises the recipient's survival instead of adding to a fitness score |
| 2 | Age structure: adults help, juveniles receive |
| 3 | Energy: help costs energy, births need energy |
| 4 | Variable population size (empty sites, as in Mitteldorf & Wilson 2000); costly helping (self out of routing) is tested again here, since their model suggests empty sites may let it spread by easing competition among relatives |
| 5 | Groups and households instead of grid neighbours |

The genomic kin-recognition step is dropped for now: kin discrimination showed no lasting advantage, and the
ecological model's helping must first work by viscosity alone. It can return as a later step.

## Step 0d: does the spread depend on local replacement? (pre-registration 2026-11-19; no 0d data; revised per Codex review)

This is a data-informed follow-up: the base arm (V-local) is the H-nobias configuration, which already spread in
20/20 runs at 3000 steps. Its new content is the control.

**Arms (seeds 0-19, 3000 steps, B = 1.0, C = 0.2, uniform routing over self plus four neighbours, everything else
as in step 0).**

| Arm | Replacement | Start | Role |
| --- | --- | --- | --- |
| V-local | parent chosen from the site's own neighbourhood (self + 4 neighbours), as before | rare | base; the H-nobias configuration, rerun |
| V-global | parent chosen from 5 sites drawn uniformly at random from the whole grid (without replacement; the focal site is included only by chance), fresh each step and site | rare | control: global-competitor replacement |
| V-below | local, B = 0.05 | common | below-rule control |
| V-null | global replacement, B = 0, C = 0 | rare | descriptive drift baseline: `h` has no effect at all |

- In V-global, benefit routing stays local (the self plus four grid neighbours, uniform weights), and the lottery
  keeps 5 candidates with the same softmax temperature 0.12. What changes is the replacement package: a site's new
  occupant comes from anywhere, so neighbours are no more related than random pairs. This also changes who competes
  with whom, ends parent-offspring continuity on a site, and changes how lotteries overlap. A difference between
  V-local and V-global therefore shows dependence on this local-replacement package, not on viscosity alone.
- The candidate draws in V-global and V-null use a separate random stream (seed + 9,000,000).
- Same seeds give the same initial `h` and labels in every arm, but the runs diverge from the first step. Arms are
  compared as independent samples (Fisher exact), not as matched pairs.
- V-local reruns the exact H-nobias configuration and seeds; its results must equal the step-0c H-nobias runs
  (checked, a mismatch stops the step as a code error).

**Null expectation (not a derivation).** In V-global the helper keeps 0.2·h, exactly its cost, and its neighbours
are on average unrelated, so the expectation is that helping has little net effect on its lineage, leaving `h` to
drift and mutation. No quantitative drift prediction is made: the engine replaces all 576 sites each step,
mutates every offspring, and clips `h` at 0 (an upward bias near 0). V-null measures that drift directly.

**Outcomes per run.** Success: final mean `h` >= 0.60. Descriptive: sustained success (mean `h` >= 0.60 at every
50-step sample from 2500 to 3000); mean `h` every 50 steps; neighbour assortment
of `h` at steps 500, 1000, ..., 3000 (correlation of `h` between grid neighbours, each edge once); label-sharing
fraction of neighbour pairs minus random pairs at the same steps (a relatedness proxy, the same pairs as step 1-cal).

**T0d.** All of:

- V-local succeeds in >= 15/20.
- V-local exceeds V-global by >= 8 runs, one-sided Fisher p < 0.05.
- V-below is maintained in <= 2/20.

**Decision.**

- **T0d met:** at these settings, spread differs between the local and the global-competitor replacement rules,
  consistent with weak altruism favoured by viscosity. That is the base. Step 1 (help raises survival) is
  pre-registered next, with its control re-checked.
- **V-local and V-below pass, but the comparison fails for any reason** (fewer than 8 runs apart, or Fisher
  p >= 0.05): the spread was not shown to depend on local replacement; the base is not established as kin selection
  by viscosity. Recorded, and the next move is decided with the user. No second attempt: this step is a control on
  a working arm, not an ingredient.
- **V-local fails (< 15/20) or V-below is maintained in > 2/20:** a replication failure of the base; recorded and
  discussed.

**Predictions (mine, before any 0d data).**

- V-local >= 15/20: about 95% (it is a rerun of a 20/20 arm; the equality check makes it near certain).
- V-global <= 3/20: about 70%.
- T0d met: about 75%.

**Budget.** 80 runs of 3000 steps, about 4 minutes on 8 cores. Code gets a Codex review before running; wording
before commit.

**Limits.**

- V-global bundles several changes (where offspring settle, who competes, lottery overlap, reproductive variance),
  so it is a strong reduction of viscosity, not a clean removal of recipient relatedness alone.
- One benefit level and one selection strength. Weak altruism only (no net direct cost); costly helping returns at
  step 4.

## Step 1 (revised ladder): overlapping generations (pre-registration 2026-11-19; no step-1 data; rewritten per two Codex reviews)

**Why this step.** "Help raises survival" bundles several changes: overlapping generations, benefit and cost
moving from fecundity to survival, equal fecundity, and only survivors reproducing. Following the one-ingredient
rule, it is split. Step 1 adds only overlapping generations; step 1b (pre-registered after this verdict) then moves
the benefit and cost to survival.

**From the base (0d).** Uniform routing over self plus four neighbours, B = 1.0, C = 0.2: each site receives `R_i`
and pays `C·h_i`, with fecundity `W_i = 1 + R_i − C·h_i`. In the base, every site is replaced every step by a softmax
lottery (temperature 0.12) over `W` among self plus four neighbours.

**Ingredient: overlapping generations.** Each step:

1. Routing and `W` as in the base.
2. Each occupant dies with probability `d`, independent of `h` and of help (a separate stream, seed + 11,000,000).
   Attempt 1: `d` = 0.5.
3. Each dead site gets a new occupant by **exactly the base lottery**: softmax over `W` (temperature 0.12) among the
   start-of-step occupants of the site itself and its four neighbours, as in the base. Survivors keep their site and
   their `h`.
4. Inheritance as in the base (mutation probability 0.02, s.d. 0.04, clipped to [0, 1]).

So the only change from the base is that a fraction `1 − d` of sites is not replaced each step. At `d` = 1 the step
is the base exactly (a test checks this). All occupants present at the start of the step can parent, as in the base,
where every occupant parents and then is replaced; since death does not depend on `h`, this does not undo any
selection. Lotteries keep 5 candidates, and no fallback is needed.

**Run length.** Runs last **6000 steps**: `d × steps` = 3000 expected replacements per site, as in the base's
3000 steps. (With overlapping generations this is turnover, not a count of generations.) Success: final mean
`h` >= 0.60. Descriptive: sustained success (>= 0.60 at every 50-step sample from 5000 to 6000), mean `h` every 50
steps, neighbour `h` correlation at steps 1000, 2000, ..., 6000.

**Arms (seeds 0-19, rare start unless stated).**

| Arm | Lottery candidates for a dead site | Other | Role |
| --- | --- | --- | --- |
| O-local | start-of-step occupants of self + 4 grid neighbours (the base lottery) | | test |
| O-global | start-of-step occupants of 5 sites drawn uniformly from the whole grid, as in V-global (stream seed + 9,000,000) | routing stays local | control: global-competitor replacement |
| O-below | local | B = 0.05, common start | below-rule control |
| O-null | local | B = 0, C = 0 | descriptive drift baseline |

**Manipulation check (control).** O-global is valid only if its mean neighbour `h` correlation over the samples at
steps 1000-6000, averaged over runs, is <= 0.10. In 0d it was about 0; survivors staying in place could in
principle keep some assortment, so it is checked, not assumed.

**Tests and classification (mechanical, in this order).** "Maintained" means final mean `h` >= 0.60 from the
common start.

1. **Control invalid:** O-global's correlation > 0.10. The comparison is not scored.
2. **Local failure:** O-local succeeds in < 15/20, or O-below is maintained in > 2/20.
3. **Comparison failed:** O-local succeeds by fewer than 8 more runs than O-global, or one-sided Fisher p >= 0.025
   (independent samples).
4. Otherwise **met**.

Both attempts use p < 0.025 (Bonferroni over the two Fisher tests). The ladder's two-attempt rule is exploratory
overall: "met" means a working base to build on, not a confirmed effect, since the composite endpoint gets two
chances.

**Attempt 2 (fixed now; runs only if attempt 1 is not met).** A smaller step, closer to the base: `d` = 0.8 (the base
is `d` = 1). Runs last 3750 steps (3000 expected replacements per site). Arms O2-local, O2-global, O2-below, O2-null;
same tests.

**Decision.**

- **Met (either attempt):** that version is the base for step 1b (benefit and cost act on survival), pre-registered
  next.
- **Not met in both attempts:** recorded with its classification; the next, smaller step is decided with the user.

**Expectation (a prediction, not a theoretical result).** With death independent of `h`, the change is mainly to
the life cycle; the base's local assortment should persist, so I expect spread under local replacement. Local
competition among relatives (Taylor 1992) could weaken it, since survivors now hold sites near their kin. Lattice
results such as Ohtsuki et al. (2006) assume asynchronous updating and weak selection, so they are not used
quantitatively here.

**Predictions (mine, before any data).**

- Attempt 1 met: about 75%.
- O-null reaches 0.60 in <= 2/20: about 80%.
- Attempt 2 met, given attempt 1 is not: about 50%.

**Budget.** 80 runs of 6000 steps (about 45 s each): about 8 minutes on 8 cores; attempt 2 about 5 minutes more.
Code gets a Codex review before running; wording before commit.

**Limits.** `d` is a design choice (0.5, then 0.8 closer to the base), not derived. Parents dying in the same step
can still reproduce, as in the base; that is a modelling choice that keeps `d` = 1 equal to the base. The global
control bundles where offspring settle with who competes, as in 0d.

**Step 1b preview (pre-registered only after step 1's verdict).** On the step-1 base, `W` is set equal for all and
benefit and cost move to survival, `s_i = clip(s0 + k·(R_i − C·h_i), 0, 1)`. A helper's marginal effect on its own
survival is then 0 before clipping (its self-share 0.2·B·h equals its cost at B = 1, C = 0.2), though helping still
changes nearby vacancies.

## Step 1b (revised ladder): selection acts on survival (pre-registration 2026-11-19; no 1b data; revised per Codex review)

**From the step-1 base.** Uniform routing over self plus four neighbours, B = 1.0, C = 0.2. Each site has a payoff
`x_i = R_i − C·h_i` (received help minus own cost; fecundity `W_i = 1 + x_i`). Each step, each occupant dies with
probability 0.5, independent of `x`, and each dead site is filled by a softmax lottery over `W` (temperature
`T` = 0.12) among the start-of-step occupants of the site and its four neighbours.

**Ingredient: the payoff acts on survival instead of fecundity.** The primary intended change is the life stage at
which selection acts. It is implemented as a strength-matched survival analogue of the base's birth lottery, not a
strict one-for-one mapping: the birth lottery normalizes over each vacancy's candidates, the death lottery once over
each occupant's own neighbourhood, scaled by 0.5 and capped at 1, and lifespan and reproductive variance change too.

- **Death:** each occupant dies with probability `d_i = min(1, 0.5 · w_i / mean(w_j for j in self + 4 neighbours))`,
  with `w_i = exp(−x_i / T)`. Same payoff, same temperature, same neighbourhood as the birth lottery. The mean
  death rate stays near 0.5, as in step 1 (the realized rate is reported, since the cap at 1 and the local
  normalization can shift it).
- **Birth:** each dead site's parent is drawn uniformly among the start-of-step occupants of the site and its four
  neighbours, as in step 1 but with equal fecundity.
- **Interpolation (used by attempt 2):** with weight `λ`, the death exponent is `−λ·x_i/T` and the birth lottery is a
  softmax over `(1 − λ)·x_i/T`. `λ` = 0 is step 1 exactly; `λ` = 1 is full survival selection.

Why this form rather than a survival function such as `s = 0.5 + 0.5·x`: a linear survival function with a slope
that keeps survival below 1 gives selection about 8 times weaker than the base's birth lottery at small payoff
differences (a 1% change in survival against about 9% in lottery weight), and a slope strong enough to match it pushes
survival to 1 for strong helpers, stopping turnover. (First order at survival 0.5: a payoff advantage of 0.01 raises
survival from 0.500 to 0.505, 1%, while the birth-lottery weight rises by exp(0.01/0.12) − 1, 8.7%.) The death
lottery is built to match the base's strength, locality and turnover at first order; equal realized selection in
the spatial process is not established.

**Direct effect.** Holding the neighbours fixed, the helper keeps 0.2·B·h of its benefit, which equals its cost at
B = 1, C = 0.2, so its own payoff `x_i` does not change with its own `h` (weak altruism, as in the base). It is
payoff-neutral to itself, but not neutral in survival: its helping raises its neighbours' payoffs, which lowers their
death weights and so raises its own death probability through the local normalization.

**Checks (deterministic tests, before running).** `λ` = 0 reproduces step 1 (O-local, O-global) exactly, and with
B = C = 0 any `λ` reproduces O-null exactly, comparing full `h` and label trajectories over many steps. This needs the
same random streams and draw order as `OverlappingEngine`, so the death draws stay on their own stream.

**Run length and outcomes.** 6000 steps (mean turnover about 0.5 per step, as in step 1). Success: final mean `h`
>= 0.60. Descriptive: sustained success (every 50-step sample from 5000 to 6000), mean `h` every 50 steps, realized
death rate, neighbour `h` correlation at steps 1000, ..., 6000.

**Arms (seeds 0-19, rare start unless stated; attempt 1, `λ` = 1).**

| Arm | Birth candidates | Other | Role |
| --- | --- | --- | --- |
| S-local | start-of-step occupants of self + 4 neighbours | | test |
| S-global | start-of-step occupants of 5 random sites (stream seed + 9,000,000) | death lottery and routing stay local | control for offspring settlement (assortment), not for survival selection itself |
| S-below | local | B = 0.05, common start | below-rule control |
| S-null | local | B = C = 0 | descriptive drift baseline (equals O-null) |

**Manipulation check and classification:** as in step 1, in the same order. Control invalid if S-global's mean
neighbour `h` correlation over steps 1000-6000 is > 0.10 or undefined; local failure if S-local < 15/20 or S-below is
maintained in > 2/20; comparison failed if S-local leads S-global by fewer than 8 successes or one-sided Fisher
p >= 0.025; otherwise met.

**Attempt 2 (fixed now; runs only if attempt 1 is not met).** A smaller step from step 1: `λ` = 0.5, so selection
acts half through births and half through deaths. Arms S2-local, S2-global, S2-below, S2-null; same run length,
tests and alpha.

**Decision.**

- **Met (either attempt):** that version is the base for step 2 (age structure), pre-registered next. If only
  attempt 2 is met, the full move to survival selection is noted as not achieved.
- **Not met in both attempts:** recorded with its classification; the next, smaller step is decided with the user.
- As before, the two-attempt rule is exploratory: "met" is a working base, not a confirmed effect. Fisher's test
  treats arms as independent samples, although they share seed numbers; that is conservative, and consistent with
  the earlier steps.

**Expectation (a prediction, not a theoretical result).** Selection through deaths at first-order matched strength
may favour helping as selection through births did. One difference: births are uniform among start-of-step
occupants, including ones that die in the same step, so a selected-against occupant can die and still parent the
vacancy, its own included. Survival selection then works only through how long a site is held, which dilutes it. A
pass would show that spread is robust under this mortality rule; it would not show that survival selection
substitutes for fecundity selection at equal strength.

**Predictions (mine, before any data).**

- Attempt 1 met: about 60%.
- Attempt 2 met, given attempt 1 is not: about 60%.
- Realized mean death rate within 0.45-0.55: about 85%.

**Budget.** 80 runs of 6000 steps: about 10 minutes on 8 cores, plus about 10 for attempt 2. Code gets a Codex review
before running; wording before commit.

**Limits.** The death lottery is one way to move selection to survival; it is chosen to match the base's strength
and turnover, not from biology. Births among start-of-step occupants (including those dying this step) keep the step
comparable to step 1, but are a modelling choice that dilutes viability selection. The global control changes only
where offspring settle; the death lottery and routing stay local.
