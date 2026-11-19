# Kin Selection Ladder: From the Moran Model to an Ecological Model (pre-registration 2026-11-19)

Status (2026-11-19): **original steps 0-0c run; none met** (T0a 14/20, T0b S-kin 0/20, T0c H-kin and H2-kin 0/20,
while uniform routing spread 20/20 at 3000 steps). The ladder was then rebuilt on a viscosity base: **step 0d met**
(local replacement 20/20 against global-competitor replacement 1/20, p = 1.5e-10) and **revised step 1, overlapping
generations, met** in attempt 1 (local 20/20 against global 0/20, p = 7e-12). **Step 1b (selection on survival via a
death lottery) not met** in either attempt (local 0/20 at λ = 1 and 0.5; helping finished below the drift baseline). **Step 1c (death lottery normalized
over the whole grid) met in attempt 2** (`λ` = 0.5: local 20/20 against global 0/20, p = 7e-12) but not attempt 1
(`λ` = 1: local 0/20, while the global-settlement arm spread in 14/20). The base for step 2 therefore has selection
half through births and half through deaths. **Step 2a (ages, adult-only helping) not met** in either attempt: helping spread
20/20 under both local and global settlement (comparison failed). That test did not show a dependence on local settlement (both arms at the ceiling). Diagnostic D2a followed. **Restart (user decision):** because every working step had weak altruism (no net
direct cost to the helper), the ladder steps back to establish a **costly-helping base, step K0**, which was **met in attempt 1**
(costly helping, b/c = 12: local 20/20 against global 0/20, p = 7e-12; no spread at b/c 3 or 6). **Step K1, parental care (help
only to own offspring), met in attempt 1**: at b/c = 6, 18/20 against 0/20 for neighbour help, and 20/20 even
without local settlement. **Rebuilt ladder (on K1): step R1 (care raises offspring survival) met in
attempt 2** (`λ` = 0.5, the care term weighted equally in the death exponent and in fecundity: at b/c = 6 under
local settlement, 20/20 against 0/20 for neighbour help; with care only on survival, `λ` = 1, 0/20). **Diagnostic DR1:** that
survival-only care settled at a modest level (about 0.07-0.24 at b/c 6-48) reached from below and from above,
and in the registered local comparison it was lower at b/c 48 than at 24, as saturation predicts in direction.
**Step R2 (care only for juvenile offspring, age < 2) met in attempt 1:** 20/20 against 0/20 for help to young
neighbours, and 20/20 without local settlement. **Step R3a (care and its cost carried over as condition, `ρ` = 0.8)
met in attempt 1:** 20/20 against 0/20, and 20/20 without local settlement. See the
last sections and `RESULTS.md`. The original step 1 (genomic kin
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

## Step 1c (revised ladder): survival selection with a globally normalized death lottery (pre-registration 2026-11-19; no 1c data; revised per Codex review)

**Why.** Step 1b moved selection from births to deaths through a death lottery normalized over self plus four
neighbours, and helping finished below drift in both attempts (`RESULTS.md`). One untested hypothesis is the local
normalization: a helper's death probability is normalized over the same sites it helps, so raising their payoffs
raises its own death probability. The user chose the smaller step that removes this: normalize over the whole
grid, so that a site's survival depends on its own payoff, and only the mean death rate is held fixed.

**Change from step 1b (one change).** Death: `d_i = min(1, 0.5 · w_i / mean(w over all 576 sites))`, with
`w_i = exp(−λ·x_i/T)`, `T` = 0.12. Everything else is as in step 1b: payoff `x_i = R_i − C·h_i`, births by a softmax
over `(1 − λ)·x_i/T` (equivalently over `(1 − λ)·W` at temperature `T`, since the constant in `W = 1 + x` cancels) among the start-of-step occupants of self plus four neighbours (or 5 random sites in the global
arms), mutation as before, survivors keep their site.

- With global normalization, a helper's own death probability depends on its own payoff relative to the whole
  population. Its own payoff does not change with its own `h` (it keeps 0.2·B·h, its cost). Raising its neighbours'
  payoffs still changes the shared denominator, but that effect is diluted by global averaging: each changed site
  contributes 1/576 of the change in the mean weight (nonlinear in payoff, and affected by the cap).
- The cap at 1 can lower the mean death rate below 0.5 when payoffs vary widely; the realized rate is reported.

**Checks (deterministic tests, before running).** `λ` = 0 reproduces step 1 exactly, and with B = C = 0 any `λ`
reproduces O-null exactly (full `h` and label trajectories).

**Arms, run length, outcomes, manipulation check, classification and alpha:** as in step 1b (6000 steps, seeds 0-19;
L-local, L-global, L-below, L-null; control invalid if L-global's mean neighbour `h` correlation over steps 1000-6000
is > 0.10 or undefined; local failure if L-local < 15/20 or L-below is maintained in > 2/20; comparison failed if
L-local leads L-global by fewer than 8 successes or one-sided Fisher p >= 0.025; otherwise met). Attempt 1: `λ` = 1.

**Attempt 2 (fixed now; runs only if attempt 1 is not met).** `λ` = 0.5 with the global normalization (arms L2-*).

**Decision.**

- **Met (either attempt):** that version is the base for step 2 (age structure). Since this differs from step 1b only
  in the normalization scope, a pass would be evidence for a normalization-scope effect at these parameters. It
  would not establish a general mechanism: samples are finite, and the normalization may interact with the cap or
  with the spatial payoff structure.
- **Not met in both attempts:** recorded; helping then failed to spread under both tested death-lottery
  normalizations at these parameters (other survival mappings, strengths, turnover rules and parent timing remain
  untested), and the next, smaller step is decided with the user.
- The two-attempt rule stays exploratory: "met" is a working base, not a confirmed effect.

**Expectation for attempt 1 (`λ` = 1; a prediction, not a theoretical result).** On a straight boundary between helpers (`h` = 1) and
non-helpers, a boundary helper with three helping neighbours has payoff 0.6, and a boundary non-helper with one
helping neighbour 0.2, so the helper is the less likely to die. Vacancies then fall mostly among non-helpers, and
a non-helper vacancy at the boundary is filled by a helper with probability 1/5 (births are uniform at `λ` = 1; at
`λ` = 0.5 that probability is a softmax). Helping clusters should therefore
grow slowly once formed. The obstacles are forming them from a rare start, where payoff differences are small, and
births among dying occupants diluting survival selection.

**Predictions (mine, before any data).**

- Attempt 1 met: about 50%.
- Attempt 2 met, given attempt 1 is not: about 45%.
- Realized mean death rate within 0.45-0.5: about 85%.

**Budget.** About 25 minutes on 8 cores for both attempts (as 1b). Code gets a Codex review before running; wording
before commit.

**Limits.** L-global controls offspring assortment under the new normalization; it is not a no-selection control.
Global normalization means a site's death probability depends on the population's mean payoff, a
global interaction kept only to fix turnover. Births among start-of-step occupants, including those dying this
step, remain as in 1b.

## Step 2a (revised ladder): ages, with only adults helping (pre-registration 2026-11-19; no step-2 data; rewritten per Codex review)

**Why split.** "Adults help, juveniles receive" bundles several ingredients: age state, adult-only production and
payment, juvenile-only receipt, benefit lost when no juvenile is near, and with them a net direct cost (strong
altruism). Following the one-ingredient rule, step 2a adds ages with adult-only helping, which keeps weak altruism;
step 2b (pre-registered after this verdict) then directs the help at juveniles only, the first costly-helping step.

**From the base (step 1c, attempt 2).** Uniform routing over self plus four neighbours, B = 1.0, C = 0.2; payoff
`x_i = R_i − C·h_i`; each step, deaths by the globally normalized death lottery with `λ` = 0.5
(`d_i = min(1, 0.5·w_i/mean(w))`, `w = exp(−0.5·x/0.12)`), and each dead site filled by a softmax over `0.5·x/0.12`
among the start-of-step occupants of self plus four neighbours; survivors keep their site. The mean death rate was
about 0.5 in the base.

**Ingredient: age-dependent helping (only adults produce and pay).**

- **Timing.** Each step: (1) payoffs from the start-of-step occupants and their ages; (2) deaths; (3) dead sites
  filled; (4) every surviving occupant's age increases by 1, and each newborn starts at age 0. So a newborn created
  at the end of step `t` is a juvenile (age 0) in the payoff computation of step `t + 1`, and an adult (age >= 1)
  from step `t + 2` if it survives.
- Only adults produce benefit `B·h` and pay `C·h`. Benefit is routed over self plus four neighbours as in the base,
  so adults and juveniles all receive, and an adult keeps `0.2·B·h`, its cost: helping stays weak altruism for
  adults (its own payoff does not change with its own `h`). A juvenile's own `h` has no effect on its current payoff.
- Initial ages: each site starts at age 0 with probability 0.5, otherwise age 1, from a separate stream
  (seed + 13,000,000); the age bookkeeping draws nothing from the engine's own stream.
- Everything else is as in the base. Every start-of-step occupant, juvenile or adult, can still parent a vacancy.

**Expected juvenile fraction.** If the realized death rate stays near 0.5, about half the sites hold juveniles at
each payoff computation. This is checked descriptively, not assumed.

**Check (deterministic test, before running).** With every occupant treated as an adult (juvenile period 0), the
model reproduces the base (L2-local, L2-global) exactly, comparing full `h` and label trajectories; this requires
the age bookkeeping to use no engine draws and to leave the order of operations unchanged.

**Arms (seeds 0-19, 6000 steps, rare start unless stated):** A-local (local settlement), A-global (5 random sites),
A-below (B = 0.05, common start), A-null (B = C = 0). Manipulation check (A-global mean neighbour `h` correlation
over steps 1000-6000 <= 0.10 and defined) and classification, in this order: **control invalid** if that check
fails; **local failure** if A-local succeeds in < 15/20 or A-below is maintained (final mean `h` >= 0.60) in > 2/20;
**comparison failed** if A-local leads A-global by fewer than 8 successes or one-sided Fisher p >= 0.025
(independent samples); otherwise **met**. Descriptive additionally: the realized juvenile
fraction.

**Attempt 2 (fixed now; runs only if attempt 1 is not met).** A smaller step: juveniles help at half strength
(produce `0.5·B·h`, pay `0.5·C·h`, still weak altruism), adults at full strength. Arms A2-*; same tests.

**Decision.**

- **Met (either attempt):** that age-dependent-helping version met the spread criterion and is the base for step 2b
  (help directed at juveniles only), pre-registered next.
- **Neither met:** recorded; the next, smaller step is decided with the user.
- The tested ingredient is age-dependent expression of helping (age bookkeeping alone has no effect). The two-attempt
  rule stays exploratory.

**Predictions (mine, before any data).**

- Attempt 1 met: about 70%. Adult-only helping roughly halves the helping expressed at any time (if age and `h` are
  uncorrelated, which selection need not keep), so spread may be slower.
- Attempt 2 met, given attempt 1 is not: about 60%.
- Realized juvenile fraction within 0.45-0.55: about 80%.

**Budget.** About 12 minutes per attempt on 8 cores. Code gets a Codex review before running; wording before commit.

**Limits.** A juvenile period of one step is the shortest possible; juveniles can still reproduce; selection is
still half through births and half through deaths (step 1c).

**Step 2b preview (pre-registered only after step 2a's verdict).** Adult benefit is shared only among the juveniles in
the adult's self-plus-four neighbourhood, and lost if there is none. An adult helper then pays `0.2·h` and gets
nothing back (strong altruism). Rough screen: with four neighbours each a juvenile with probability 0.5, the expected
delivered benefit is `15/16·B·h` (no juvenile with probability 1/16), and a given juvenile neighbour gets on average
`E[1/(1 + Binomial(3, 0.5))] ≈ 0.47` of it. A Hamilton heuristic `r·b > c` then needs `r` above about 0.21. Neighbour
`h` correlation (about 0.45 in the base) is only an assortment proxy, not relatedness, and local competition is
ignored, so this does not show the threshold is reachable.

## Diagnostic D2a: why does helping spread under global settlement once ages exist? (pre-registration 2026-11-19; exploratory, no D2a data; revised per Codex review)

**Question.** In step 2a, helping spread in 20/20 runs under global settlement (A-global), while the same arm without
ages (step 1c's L2-global) gave 0/20, and neighbour `h` correlation over all sites stayed near 0. This diagnostic
locates the selection, so that step 2b can get a valid control. It is not a ladder step and has no pass/fail; it has
pre-registered measurements and interpretation rules.

**Reasoning.** In the A-global model an occupant's own payoff does not depend on its own `h`: an adult keeps
`0.2·B·h`, its cost, and a juvenile neither produces nor pays. Both have `x_i = 0.2 × sum of the adult neighbours'
h` (the focal site excluded). So own `h` can affect fitness only through how it is associated with its payoff,
possibly nonlinearly (the death and birth lotteries are exponential and capped) or across steps. Positive linear
assortment between own `h` and adult neighbours' `h` is one candidate path, not the only one.

**Exact expected fitness.** For each start-of-step occupant `i`, the engine's own probabilities give its expected
number of sites after the step:

`w_i = (1 − d_i) + sum over the sites k whose candidate set C_k contains i of d_k · p_ik`,

with `d_k` the death probability of site `k`'s occupant and `p_ik` the birth-lottery probability that `i` parents
`k`. Since the `p_ik` sum to 1 over each candidate set, the `w_i` sum to 576, and the expected change in mean `h`
before mutation, given the state and the candidate sets, is exactly `cov(h, w)` (population covariance, 1/n). It
splits into a **survival part** `cov(h, 1 − d)` and a **birth part** `cov(h, expected offspring)`. There is no
death- or parent-lottery sampling drift in these; in the global arms, the random draw of candidate sets remains.

**Runs.** A-global and A-local (step 2a attempt 1) and L2-global (step 1c attempt 2, no ages, the failing control),
seeds 0-4, the first 2000 steps (the spread phase in step 2a). The models are unchanged; the measurements draw no
random numbers.

**Measurements (per run).**

1. **Expected selection:** survival and birth parts of `cov(h, w)`, summed over steps 1-2000, overall and by age class
   of the occupant. A class's contribution is `(1/n) · sum over i in the class of (h_i − mean h)·(w_i − 1)`, so the
   classes add up to the total.
2. **Association of own `h` with payoff:** Pearson and Spearman correlation of own `h` with own payoff `x`, over all
   sites, adults only and juveniles only, at steps 250, 500, ..., 2000, averaged over those samples.
3. **Realized accounting (descriptive):** `Δ = (1 − D)·(mean_survivors − H) + D·(mean_parents − H) +
   D·(mean_newborns − mean_parents)`. Here `mean_parents` is the parental `h` of the dead sites' realized offspring,
   with multiplicity, before mutation; parents are start-of-step occupants and may themselves have died.
   `mean_newborns` is after mutation and clipping to [0, 1]. Steps with `D = 0` contribute only the survivor term.
   These are realized terms, so they include drift.

**Code check (a test, before running).** The death probabilities recomputed from `x` and the formula
`min(1, 0.5·q/mean(q))`, `q = exp(−0.5·x/0.12)`, equal the engine's, and the birth probabilities equal the softmax used by the engine.

**Interpretation rules (fixed now; 5 runs per arm; "consistently" means in all 5 runs).**

- **Expected selection on `h`:** "positive" if the summed `cov(h, w)` is > 0 in all 5 runs; "absent" if its
  absolute value is below 10% of the absolute across-run mean of A-local's summed `cov(h, w)` in all 5 runs;
  otherwise "mixed".
- **Which part (only if expected selection is positive):** using signed contributions, survival or birth, whichever
  is positive and larger than the other in at least 4 of the 5 runs; otherwise "both".
- **Association with payoff:** "present" if the Spearman correlation of own `h` with `x` is > 0.02 in all 5 runs
  (overall or among adults); "absent" if it is within ±0.02 in all 5 runs, in every class; otherwise "mixed".
- **Readings for A-global:**
  - expected selection positive and association present: selection through an association of own helping with
    its payoff that the overall neighbour correlation misses (for example among adults);
  - expected selection positive and association absent: a path these measures do not capture (nonlinear or across
    steps); the code is audited before any interpretation;
  - expected selection absent or mixed: the step-2a spread may be drift-like or lagged; reported as such.
- **References:** L2-global is expected to show expected selection absent and association absent; A-local positive
  and present. If not, that is reported first.

**What follows.** The result is reported to the user with a proposed control for step 2b. No ladder step is run
until the user agrees.

**Predictions (mine, before any data).** A-global: expected selection positive about 85%; association present about
65%; survival part larger about 55%.

**Budget.** 15 runs of 2000 steps, a few minutes on 8 cores (the expected-fitness sums add some cost). Code gets a
Codex review before running; wording before commit.

## Restart: a costly-helping base (step K0; pre-registration 2026-11-19, after D2a; no K0 data; revised per Codex review)

**Why restart.** Every step that worked so far (0d, 1, 1c attempt 2) had **weak altruism**: routing includes self,
so a helper keeps `0.2·B·h` of its own benefit, which at B = 1.0 exactly cancels its cost `0.2·h`. Its own payoff
does not change with its own `h`. Every arm where helping had an unconditional net direct cost (0b: `−0.2·h`) was
0/20. Step 0c had a state-dependent self-return (neutral or positive with few same-label neighbours, costly with
many) and also failed. So the ladder has not yet shown that **costly** helping, the core of kin selection and of
parental care, spreads in this engine at all. The user decided (2026-11-19) to step back and establish that first.
Steps 2b-5 are paused; if K0 is met, the ladder is to be rebuilt on it.

**Theory screen (heuristic, not a prediction for this engine).** For lattices with `k` neighbours, Ohtsuki et al.
(2006) found that costly helping is favoured roughly when `b/c > k` under death-birth updating and `b/c > k + 2`
under imitation updating (weak selection, asynchronous updates, large populations). In their donation game a
helper pays `c` per neighbour and each neighbour gets `b`. Here a helper produces `B·h` split over four neighbours and
pays `C·h` once, so per edge `b = B/4` and `c = C/4`, and **`b/c = B/C`**. In 0b (B = 1.0, C = 0.2) that was 5:
above the death-birth screen (4) and below the imitation screen (6).

**Which screen is closer here.** In the step-1 engine a dead site is filled by a lottery among the start-of-step
occupants of the site itself and its four neighbours, so the dead occupant's own type also competes for its site.
That resembles imitation updating (screen 6) more than death-birth updating (screen 4). So 0b's 0/20 does not
contradict the screen, but it was close to it, not far below. The engine also differs from Ohtsuki's assumptions in
ways that can move a threshold either way: synchronous updating with half the sites dying each step, parents that
can reproduce in the step they die, strong selection (softmax at temperature 0.12), mutation, and a 24×24 torus. The
screen is used only to choose the sweep.

**Ingredient: helping with a net direct cost.** The base is step 1 attempt 1 (overlapping generations, `d` = 0.5,
6000 steps, deaths independent of `h`, dead sites filled by the base softmax lottery over `W = 1 + R − C·h`), with one
change: **self is removed from benefit routing** (the 0b routing mask; replacement keeps self plus four neighbours).
Routing is uniform over the four neighbours (no kin labels), so each neighbour gets `B·h/4` and the helper gets
nothing back: its own helping lowers its own payoff by `0.2·h` (marginal effect −0.2 per unit `h`) whatever its neighbours do. Any advantage of helping must come from spatial
assortment created by local settlement (helpers' neighbours tend to be their descendants). That can be read as kin
selection by viscosity or as network reciprocity; this step does not separate the two.

**Sweep.** C = 0.2 throughout; `b/c = B/C`.

| Arm | B | b/c | Replacement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| K3-local | 0.6 | 3 | local | rare | below both screens (descriptive) |
| K6-local | 1.2 | 6 | local | rare | at the imitation screen (descriptive) |
| K12-local | 2.4 | 12 | local | rare | twice the imitation screen (test) |
| K24-local | 4.8 | 24 | local | rare | four times the imitation screen (descriptive) |
| K12-global | 2.4 | 12 | 5 random sites, as in O-global (routing stays local) | rare | control: global-competitor replacement |
| K-below | 0.05 | 0.25 | local | common | below-rule control |
| K-null | 0 (and C = 0) | – | local | rare | descriptive drift baseline (equals O-null, since routing is irrelevant at B = 0) |

Seeds 0-19 per arm; rare start `h` ~ N(0.05, 0.02), common N(0.9, 0.05), as in step 0. Success: final mean `h` >= 0.60;
maintained: final mean `h` >= 0.60 from the common start.

**Tests and classification (mechanical, in this order).**

1. **Control invalid:** the global arm's mean neighbour `h` correlation over steps 1000-6000, averaged over runs, is
   > 0.10 or undefined. The comparison is not scored.
2. **Local failure:** the test arm succeeds in < 15/20, or K-below is maintained in > 2/20.
3. **Comparison failed:** the test arm leads the global arm by fewer than 8 successes, or one-sided Fisher p >= 0.025.
4. Otherwise **met**.

As in all earlier steps, the same seeds give the same initial state in every arm but the runs diverge from the first
step; seed pairing is ignored and arms are compared as independent samples (Fisher exact). p < 0.025 is Bonferroni
over the two attempts.

**Descriptive (not part of the verdict).** Success counts and mean final `h` for K3, K6 and K24, to see whether a
threshold-like pattern appears. Mean `h` every 50 steps; neighbour `h` correlation at steps 1000, 2000, ..., 6000;
sustained success (>= 0.60 at every sample from 5000 to 6000).

**Attempt 2 (fixed now; runs if attempt 1 is classified local failure or comparison failed; if attempt 1's control is invalid, the step stops and is discussed with the user instead).** A
step closer to death-birth updating, where the screen is lower (4): the dead site's own start-of-step occupant is
**excluded** from its lottery, so a vacancy is filled by one of its four neighbours only. The global control
matches the candidate count: **4** sites drawn at random from the whole grid, excluding the focal site. Everything
else unchanged, including synchronous updating and start-of-step parents (neighbours that die in the same step can
still parent), so this is death-birth-like, not standard asynchronous death-birth updating. Arms K3-DB, K6-DB,
K12-DB (test), K24-DB, K12-DB-global (control), K-below-DB, K-null-DB; same tests and classification.

**Checks (deterministic tests, before running).**

- With self in routing and B = 1.0, the K0 attempt-1 code reproduces step 1's O-local runs exactly (same seeds).
- With self out of routing, a site's own `R_i` does not depend on its own `h`.
- In attempt 2, a dead site's own occupant is never its parent, and the global control draws 4 distinct non-focal sites.

**Decision.**

- **Met (either attempt):** at these settings, costly helping (direct cost `0.2·h` to the helper, `b/c` = 12) spread under
  local settlement and was not shown to spread under global-competitor replacement: a costly-helping base consistent
  with selection through spatial assortment (kin selection by viscosity). Then the second level (parental care,
  below) is pre-registered, and after it the ladder is rebuilt on this base with costly helping at every step.
- **Neither attempt met:** the pre-registered local-versus-global costly-helping base was not established at
  `b/c` = 12 (the classification says whether the local arm failed or only the comparison did). The line stops tuning
  this engine, and the next base proposed to the user is the Mitteldorf & Wilson (2000) empty-sites model
  (`ecological_models/spatial_altruism`), where vacant sites ease competition among relatives.
- "Met" means a working base to build on; with two attempts and one test level, it is exploratory, not a confirmed
  threshold.

**Predictions (mine, before any data).**

- Attempt 1 met: about 55%. b/c = 12 is twice the imitation screen, but selection is strong and synchronous, and
  local competition among relatives (Taylor 1992) is not removed.
- K3-local succeeds in <= 2/20: about 85%.
- K24-local succeeds in >= 15/20: about 65%.
- Attempt 2 met, given attempt 1 is not: about 35%.

**Budget.** 140 runs of 6000 steps (about 45 s each): about 13 minutes on 8 cores per attempt. Code gets a Codex
review before running; wording before commit.

**Limits.**

- Raising B also raises selection strength at a fixed temperature (W up to 1 + B, 5.8 at B = 4.8), so the sweep
  changes selection strength together with b/c.
- Relatedness comes only from local settlement; no kin labels or genealogy.
- The global control bundles where offspring settle with who competes, as in 0d.

**Second level preview (pre-registered only after K0's verdict): parental care.** On the K0 base, a helper's benefit
goes only to its own living offspring among its four neighbours (individuals placed by its own lottery wins, tracked
by a parent id), and is lost if there are none; the cost `C·h` is always paid. Control: the same benefit routed to
random non-offspring neighbours. This separates care aimed by parentage from help spread by local assortment.

## Step K1: parental care on the costly-helping base (pre-registration 2026-11-19, after K0; no K1 data; revised per Codex review)

**Why this step.** K0 showed that costly help to neighbours spread under local settlement at b/c = 12 and 24, and
not at 3 or 6 (`RESULTS.md`). There, help reaches relatives only through viscosity. Parental care is the clearest
case of costly helping among kin: help aimed at one's own offspring through parentage. K1 asks whether routing
costly help to own offspring lets it spread at b/c = 6, where the same help spread evenly over neighbours did not.

**From the base (K0, attempt 1).** Overlapping generations (`d` = 0.5, deaths independent of `h`, 6000 steps);
dead sites filled by the softmax lottery (temperature 0.12) over `W = 1 + R − C·h` among the start-of-step
occupants of self plus four neighbours; C = 0.2; self out of routing; mutation as before (probability 0.02 per birth,
s.d. 0.04).

**Ingredient: benefit routed to own offspring only.**

- **Ids.** Each occupant has a unique id and the id of its parent (founders: none). A newborn gets a fresh id and
  the id of the start-of-step occupant that won its lottery. Survivors are restored with their own `h`, label, id
  and parent id together (the engine runs the full lottery on every site and then restores survivors, so the
  bookkeeping must be restored with them). Ids draw nothing from any random stream.
- **Timing.** Benefit is computed from the start-of-step occupants: helper `i` sends `B·h_i` in equal shares to its
  living offspring present at that moment (occupants whose parent id is `i`'s id). A newborn can therefore first
  receive care in the step after its birth. Founders have no parent and receive no care.
- **Loss.** If the helper has no living offspring, its benefit is lost. It always pays `C·h_i` and never receives
  its own benefit.
- **Where offspring are.** Under local settlement, a parent and its offspring both stay on their sites, and a
  retained offspring of a parent that is still alive can only have been born into one of the parent's four
  neighbouring sites (a newborn on the parent's own site exists only if the parent died). So at every payoff
  computation, all living offspring of a living parent are among its four neighbours. Under global settlement
  (5 random candidate sites, as in K12-global) offspring can be anywhere, and the benefit still reaches them: care
  is aimed by parentage, not by place.
- The benefit raises the offspring's `W`, so it increases the offspring's chance of winning vacancies (its own
  reproduction), not its survival.

**Rough screen (heuristic, not a prediction).** Under neutral turnover at `d` = 0.5, about half the occupants at
any payoff computation are newborns with no offspring yet, and a living occupant has on average about 1/3 of a
living offspring (an occupant of age `a` has about `1 − 2^{−a}`; ages are geometric). With a Poisson approximation,
only about a quarter of occupants have any living offspring, so roughly three quarters of produced benefit would be
lost if `h` is unrelated to age. Parents and offspring have similar `h` (mutation changes `h` in 2% of births), so a
Hamilton-style heuristic suggests care pays roughly when a quarter of B exceeds C, i.e. b/c above about 4, before
competition among relatives (Taylor 1992), which can raise it under local settlement. Strong selection and
synchronous updates are not covered. The test level b/c = 6 is above this rough screen but not far. Offspring counts
and benefit loss are measured, not assumed.

**Arms (seeds 0-19, 6000 steps; rare start unless stated; C = 0.2; b/c = B/C).**

| Arm | Routing | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| P6-local | own offspring | 6 (1.2) | local | rare | test |
| N6-local | uniform over 4 neighbours | 6 (1.2) | local | rare | known benchmark: reruns K6-local (0/20 in K0); a code check |
| P-below | own offspring | 0.25 (0.05) | local | common | below-rule control |
| P1.5-local, P3-local, P12-local | own offspring | 1.5, 3, 12 | local | rare | descriptive sweep |
| P3-global, P6-global, P12-global | own offspring | 3, 6, 12 | global (5 random sites) | rare | care without local settlement (P6-global: secondary test) |

Nine arms, 180 runs. N6-local must reproduce the K0 K6-local runs exactly (a mismatch stops the step as a code error).
No new drift arm: with B = C = 0 routing is irrelevant, so K-null serves.

**Primary test.** The comparison arm's outcome is already known (K6-local 0/20), so this is not a prospective
two-arm comparison. The prospective test is a fixed criterion against that benchmark, in this order:

1. **Local failure:** P6-local succeeds (final mean `h` >= 0.60) in < 15/20, or P-below is maintained in > 2/20.
2. Otherwise **met**. (With N6-local at 0/20, 15/20 also gives a lead of >= 8 runs and Fisher p < 0.025; Fisher is
   reported descriptively.)

**Secondary test (reported separately; does not change the primary verdict).** H2, pedigree-aimed care can spread
without local settlement: P6-global succeeds in >= 15/20. P6-global's mean neighbour `h` correlation over steps
1000-6000 is reported to confirm that spatial assortment is weak (<= 0.10, otherwise H2 is reported as not
interpretable). It does not mean recipients are unrelated: they are the helper's offspring by design.

**Descriptive (all arms, averaged over steps 1000-6000).**

- Mean number of living offspring per occupant, and the fraction of occupants with none.
- Benefit lost: `Σ_i h_i·1[n_i = 0] / Σ_i h_i` (weighted by produced benefit; undefined if all `h` = 0).
- Parent-offspring `h` correlation over living parent-offspring pairs.
- Success counts, mean final `h`, mean `h` every 50 steps, neighbour `h` correlation at steps 1000, ..., 6000.

**Attempt 2 (fixed now; runs only if attempt 1 is classified local failure).** A hybrid: a helper with living
offspring sends its benefit to them only, as in attempt 1; a helper with none sends it uniformly to its four
neighbours (as in K0) instead of losing it. This is not a half-strength version of parental care; since having no
offspring is tied to age, it is an age-conditioned mixture whose effect need not lie between K0 and K1. Arms (all
rerun, 160 runs): H6-local (test), H-below (control, its maintained criterion applied on its own), H1.5-local,
H3-local, H12-local, H3-global, H6-global (secondary test), H12-global. N6-local is not rerun. Its verdict, defined
on its own: **local failure** if H6-local succeeds in < 15/20 or H-below is maintained in > 2/20, otherwise **met**;
H2 is scored on H6-global as for P6-global. Descriptive measures as in attempt 1, except that the benefit-loss
measure is reported as the **fraction redirected** to neighbours (same formula), since nothing is lost.

**Checks (deterministic tests, before running).**

- Every newborn's parent id equals the id of the start-of-step occupant whose lottery it won; survivors keep their
  `h`, label, id and parent id together; founders have no parent; id bookkeeping draws nothing from any stream.
- Under local settlement, at every payoff computation, every living offspring of a living parent is one of its four
  neighbours.
- A helper's benefit reaches only its living offspring, in equal shares; with none it is lost (attempt 1) or routed
  uniformly to its four neighbours (attempt 2); no helper receives its own benefit.
- N6-local reproduces K6-local exactly; with B = C = 0, offspring routing gives the same trajectory as K-null.

**Decision.**

- **Attempt 1 met:** at these settings, the offspring-only routing package (recipients chosen by parentage, benefit
  concentrated on fewer recipients, benefit lost without offspring) let costly helping spread at b/c = 6, where
  even neighbour help did not. That gives a parental-care base. Which base (K0 neighbour help or K1 parental care)
  the ladder is rebuilt on is then decided with the user.
- **Attempt 2 met:** a hybrid parental-priority base, not full parental care; recorded as such, and the choice of
  base is discussed with the user.
- **Neither met:** recorded; the ladder is rebuilt on K0, and parental care is revisited later.
- "Met" means a working base to build on; with two attempts it is exploratory.

**Predictions (mine, before any data).**

- P6-local >= 15/20 (attempt 1 met): about 40% (lowered after the corrected screen).
- P12-local >= 15/20: about 75%.
- P6-global >= 15/20 (H2): about 45%.
- P1.5-local >= 15/20: about 10%.
- Attempt 2 met, given attempt 1 is not: about 45%.

**Budget.** 180 runs of 6000 steps (about 45-60 s each): about 17-23 minutes on 8 cores; attempt 2 (160 runs) about
15-20 minutes more. Code gets a Codex review before running; wording before commit.

**Limits.**

- Inheritance is clonal with rare mutation, so parent-offspring similarity is much higher than in sexual species.
- Care raises only the offspring's reproduction, not its survival, and parents cannot adjust care to need or to the
  number of offspring.
- The contrast with N6-local changes several things at once: who receives (offspring versus neighbours), how many
  receive (benefit concentration, which can act either way under softmax selection), and loss when there are no
  offspring. A positive result supports the whole offspring-routing package, not parentage alone.

## Rebuilt ladder on the parental-care base (user decision 2026-11-19, after K1)

The user chose K1 (costly care to own offspring) as the base. Each later step adds one ingredient to it, keeps the
help costly to the helper, and is tested against a control for that step; at most two pre-registered attempts per
step, and a failing step is replaced by a smaller one. Planned order (each pre-registered after the previous
verdict, and open to change with the user): R1 care raises offspring survival; R2 ages (care only from adults to
young); R3 energy; R4 empty sites; R5 groups or households.

## Step R1: care raises the offspring's survival (pre-registration 2026-11-19, after K1; no R1 data; revised per one Codex review; the second Codex pass could not run, usage limit)

**Why this step.** In K1, care adds to the offspring's fecundity `W` (its chance of winning vacancies). In nature,
parental care mainly keeps young alive. R1 moves the benefit of care to the offspring's survival; the parent's cost
stays on its own fecundity.

**From the base (K1, attempt 1).** Overlapping generations (death probability 0.5, 6000 steps); C = 0.2; helper `i`
sends `B·h_i` in equal shares to its living offspring present at the start of the step, lost if none; the parent pays
`C·h_i` on its own fecundity; dead sites filled by the softmax lottery (temperature `T` = 0.12) over fecundity among
the start-of-step occupants of the site and its four neighbours (local), or of 5 random sites (global).

**Ingredient: care lowers the recipient's death probability.** Each step, with `R_i >= 0` the care occupant `i`
receives:

- **Death:** `d_i = 0.5 · exp(−λ·R_i/T)`. An occupant receiving no care keeps `d_i` = 0.5, as in K1; care only lowers
  the recipient's own death probability. There is **no normalization and no cap** (`d_i` <= 0.5 since `R_i` >= 0), so
  care given to one occupant does not change anyone else's death probability directly. This differs from steps
  1b/1c, whose death lotteries were normalized (needed there because payoffs could be negative); the local
  normalization of 1b made relatives compete in the death lottery.
- **Birth:** each dead site's parent is drawn by the softmax over `W_i = 1 + (1 − λ)·R_i − C·h_i`, as in K1 with the
  care term scaled by `1 − λ`.
- **Attempt 1: `λ` = 1** (care acts only on survival; fecundity `W = 1 − C·h`).
- Death draws use the existing death stream (seed + 11,000,000): one uniform number per site, compared with `d_i`.

**What else changes (stated, not avoided).** Because care lowers deaths without raising others', the realized death
rate falls below 0.5 as care becomes common, so there are fewer vacancies; competition for them is how the effect
of care reaches everyone else, indirectly. The exponential form makes the effect nonlinear in `R`. Using the birth
lottery's temperature does not make survival selection equal in strength to fecundity selection; the two currencies
(offspring survival, parent fecundity) are not equivalent, so K1's b/c values do not carry over and no threshold is
predicted.

**Timing.** As in K1: care is computed from start-of-step occupants, so a newborn is first protected in the step after
its birth, which is also the first step in which it can die.

**Arms (seeds 0-19, 6000 steps, rare start unless stated; C = 0.2; b/c = B/C).**

| Arm | Care goes to | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| R6-local | own offspring | 6 (1.2) | local | rare | test |
| RN6-local | uniform over 4 neighbours (never self) | 6 (1.2) | local | rare | control: untargeted help, same B, also on survival |
| R-below | own offspring | 0.25 (0.05) | local | common | below-rule control |
| R3-local, R12-local, R24-local | own offspring | 3, 12, 24 | local | rare | descriptive sweep |
| R6-global | own offspring | 6 | global (5 random sites) | rare | secondary test |
| R12-global | own offspring | 12 | global | rare | descriptive |

Eight arms, 160 runs. RN6-local is new, so it is a prospective control. It is a control for the whole
offspring-care package against untargeted neighbour help (which differs in recipients, concentration on fewer
recipients, loss without offspring, and how widely deaths are lowered), not for parentage alone; local neighbours
are themselves assorted (K0 and K1 neighbour correlation about 0.4).

**Classification (mechanical, in this order).**

1. **Local failure:** R6-local succeeds (final mean `h` >= 0.60) in < 15/20, or R-below is maintained (final mean
   `h` >= 0.60 from the common start) in > 2/20.
2. **Comparison failed:** R6-local leads RN6-local by fewer than 8 successes, or one-sided Fisher p >= 0.025
   (independent samples, seed pairing ignored; Bonferroni over two attempts).
3. Otherwise **met**.

**Secondary (reported separately; does not change the verdict).** H2: R6-global succeeds in >= 15/20, read only if its
mean neighbour `h` correlation over steps 1000-6000 is <= 0.10. A low correlation does not make recipients unrelated:
they are still the helper's offspring.

**Descriptive (diagnostics averaged over payoff states after 1000-5999 updates, then over runs).**

- Realized death rate; mean death probability of occupants receiving care, of occupants receiving none, and of
  occupants that have living offspring (parents).
- Living offspring per occupant; fraction with none; benefit lost `Σ h_i·1[n_i = 0] / Σ h_i` (undefined if all
  `h` = 0); parent-offspring `h` correlation (as in K1).
- Success counts, mean final `h`, mean `h` every 50 steps, neighbour `h` correlation at steps 1000, ..., 6000.

**Attempt 2 (fixed now; runs only if attempt 1 is classified local failure or comparison failed).** `λ` = 0.5: the
care term enters the death exponent and the fecundity at half weight each; the cost stays fully on fecundity. This is
a half-step in the parameters, not necessarily in its effect (the death term is exponential). It differs from step
1c, which split the whole payoff, cost included. Arms with the prefix `R2-` and the same roles: R2-6-local (test),
R2-N6-local (control), R2-below, R2-3-local, R2-12-local, R2-24-local, R2-6-global (secondary), R2-12-global; same
classification with these names.

**Implementation.** A new engine combining K1's id bookkeeping (survivors restored with `h`, label, id and parent id;
newborn parent ids from the lottery's start-of-step parents) with this death rule; it cannot reuse the step-1b engine,
which bypasses the hook that records parents.

**Checks (deterministic tests, before running).**

- `λ` = 0 reproduces K1's P6-local and P6-global exactly (full `h`, label and id trajectories).
- With B = C = 0 and local settlement, any `λ` reproduces K-null exactly.
- `d_i` equals `0.5·exp(−λR_i/T)` and is 0.5 for every occupant without care; births use `W = 1 + (1 − λ)R − C·h`.
- RN6-local's care is uniform over the four neighbours, never self, and acts through the same death rule.

**Decision.**

- **Met (either attempt):** the survival-care package (care fully on survival, or half on survival in attempt 2)
  spread at b/c = 6 under local settlement and beat untargeted neighbour help on survival; this does not show that
  parentage by itself is the cause. That version is the base for R2 (ages), pre-registered next on the user's go.
- **Neither met:** recorded with its classification; the next, smaller step is decided with the user.
- Exploratory: two attempts, one test level.

**Predictions (mine, before any data).**

- Attempt 1 met: about 50%.
- RN6-local <= 3/20: about 70%.
- R6-global >= 15/20 (H2): about 55%.
- Attempt 2 met, given attempt 1 is not: about 50%.

**Budget.** 160 runs of 6000 steps (about 35 s each): about 12 minutes on 8 cores; attempt 2 about the same. Code gets
a Codex review before running; wording before commit. Timing checks use only the drift configuration (K1's run
disclosed a peek at a test arm).

**Limits.**

- Benefit and cost act in different currencies, with an exchange rate set by the shared temperature, not derived.
- Care lowers deaths without a fixed total, so turnover differs between arms (reported).
- The global-settlement arms change where offspring settle and who competes, as before.

## Diagnostic DR1: does survival care settle at a level approached from both sides? (pre-registration 2026-11-19, after R1; exploratory; no DR1 data; revised per Codex review)

**Question.** In R1 attempt 1 (care only on survival, `λ` = 1), helping neither spread nor collapsed: mean `h` rose
early and stayed nearly flat (about 0.10-0.12 locally at b/c 12-24, 0.23-0.24 globally at b/c 6-12; `RESULTS.md`).
The candidate explanation is saturation: under `d = 0.5·exp(−R/T)`, extra care adds less and less survival, while
the parent's fecundity cost rises linearly. DR1 asks two narrower questions: does mean `h` settle at the same level
when started from above, and does that level fall at higher benefit, as the saturation heuristic predicts?

**Why not a non-saturating rule (the option first proposed).** A rule with constant returns over the possible doses
exists (care received lies in [0, B]; for example `d = 0.5·(1 − R/B)`, the strongest such linear rule). But under the
heuristic below, even that rule predicts no helping at C = 0.2, T = 0.12: at every `h` the marginal survival gain
(0.5 per unit `h`, one offspring) is below the marginal fecundity loss (`(C/T)·survival`, at least
(0.2/0.12) × 0.5 ≈ 0.83). A failure
would not tell shape from strength, so DR1 does not run it.

**Rough optimum (heuristic, not a derivation for this engine).** Take one parent with one offspring, ignore
competition among relatives, dilution over several offspring and benefit loss, and treat the parent's fecundity
factor `exp(−C·h/T)` and the offspring's survival `1 − 0.5·exp(−B·h/T)` as multiplying (in the engine the first is a
relative lottery weight). The best `h` is `h* = (T/B)·ln((B + C)/(2C))`, with the cared offspring's death probability
`d* = C/(B + C)`. At C = 0.2, T = 0.12:

| B (b/c) | Predicted `h*` | Predicted `d*` | R1 attempt 1, local (rare start) |
| --- | --- | --- | --- |
| 0.6 (3) | 0.139 | 0.250 | `h` 0.014 |
| 1.2 (6) | 0.125 | 0.143 | `h` 0.037 |
| 2.4 (12) | 0.094 | 0.077 | `h` 0.119, cared death 0.112 |
| 4.8 (24) | 0.063 | 0.040 | `h` 0.100, cared death 0.049 |
| 9.6 (48) | 0.040 | 0.020 | not run |

`h*` falls with B over b/c 6-48, not in general (it is 0 for B <= C and first rises just above). The heuristic
misses badly at b/c 3 and 6 (predicted 0.13-0.14, observed 0.01-0.04) and below the global plateaus (0.23-0.24), and
the local fall from b/c 12 to 24 was seen before it was written down. So it is used only for direction.

**Arms (seeds 0-19, 6000 steps, `λ` = 1, offspring care, C = 0.2; R1 attempt-1 code: 56f1775, with the diagnostic
fix 333c42d that does not affect these arms).**

| Arm | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- |
| D12-local-high | 12 (2.4) | local | common, N(0.9, 0.05) | T1, against R12-local |
| D24-local-high | 24 (4.8) | local | common | T1, against R24-local; T2 |
| D48-local-high | 48 (9.6) | local | common | T2 |
| D6-global-high | 6 (1.2) | global | common | T1, against R6-global |
| D12-global-high | 12 (2.4) | global | common | T1, against R12-global |
| D48-local | 48 (9.6) | local | rare | descriptive |
| D-null-local-high | – (B = C = 0) | local | common | drift-with-mutation reference, local |
| D-null-global-high | – (B = C = 0) | global | common | drift-with-mutation reference, global |

160 runs. The rare-start counterparts are R1's archived runs (same seeds and code); their mean final `h` are frozen at
full precision: R12-local 0.11892638472644475, R24-local 0.10033534869417678, R6-global 0.2430629944190848,
R12-global 0.2259714860586167.

**T1, convergence from above (per pair, then overall).** A pair meets T1 if all of:

- the high-start arm's mean final `h` (over 20 runs) differs from its rare-start counterpart's by at most 0.03
  (absolute, full precision);
- the high-start arm's arm-mean `h` stays within a range of 0.02 (maximum minus minimum) over the 50-step samples
  from step 5000 to 6000 (settled);
- the drift reference with the same settlement has mean final `h` above 0.50.

T1 is **supported** if at least 3 of the 4 pairs meet it, **not supported** otherwise; each pair is reported, and
conclusions about convergence are limited to the pairs that meet it.

**T2, lower level at higher benefit (both arms new, both from above).** **Supported** if D48-local-high's mean final `h`
is below D24-local-high's, and D48-local-high's mean cared-offspring death probability is below D24-local-high's
(diagnostics averaged over payoff states after 1000-5999 updates within a run, then over runs). Both arms must also be settled
(arm-mean `h` range <= 0.02 over the samples from step 5000 to 6000); otherwise T2 is reported as **not
settled**. A lower cared death at higher B partly follows directly from the larger dose, so T2's specific content
is the lower `h`.

**Descriptive.** Per-seed paired differences (same seeds) for each T1 pair and for T2, with a Wilcoxon signed-rank
test; for each of the five high-start treatment arms, the first 50-step sample at which its arm-mean `h` falls below its counterpart's final
mean + 0.03 ("never" if it does not); all R1 diagnostics per arm; D48-local (rare start) against D48-local-high.

**What the results can and cannot show.**

- T1 supported: at these settings, mean `h` under survival-only care settled near the same level from below and
  from above. That is consistent with a level held by selection, but DR1 does not test selection immediately above
  and below it directly (for example by an exact selection gradient).
- T2 supported: the settled level was lower at higher benefit, as saturation predicts; other explanations are not
  excluded.
- DR1 does not change R1's verdict (attempt 1 not met, attempt 2 met at b/c 6) or the registered base for R2
  (`λ` = 0.5). If T1 and T2 are supported, whether to define a separate endpoint for survival care (a settled
  intermediate level against costly controls) is decided with the user before R2. In every other case (T1 not supported, or T1
  supported and T2 not), R2 is pre-registered next on the `λ` = 0.5 base, on the user's go.

**Predictions (mine, before any data).** T1 supported: about 65%. T2 supported: about 60%. Both drift references above
0.50: about 85%.

**Budget.** 160 runs (about 35 s each): about 12 minutes on 8 cores. The code (configuration and a scoring script) gets
a Codex review before running; wording before commit.

**Limits.** The heuristic ignores several offspring per parent, benefit loss, competition among relatives,
synchronous updates and mutation. Four pairs is a small check. The drift references have constant death 0.5, while
care changes turnover in the treatment arms, so the amount of mutation per step differs.

## Step R2: care only for young offspring (pre-registration 2026-11-19, after R1 and DR1; no R2 data; not yet reviewed by Codex, usage limit until 2026-11-20 03:00)

**Why this step.** So far a parent cares for all its living offspring, however old. In nature parental care is for
the young and stops at independence. R2 adds age and restricts care to juvenile offspring: one ingredient on the R1
base.

**From the base (R1, attempt 2; the user chose to continue on it after DR1).** Overlapping generations; helper `i`
sends `B·h_i` in equal shares to its living offspring present at the start of the step, lost if none; the parent pays
`C·h_i` (C = 0.2) on its own fecundity; care received `R` lowers the recipient's death probability,
`d = 0.5·exp(−0.5·R/T)`, and raises its fecundity by `0.5·R` (`λ` = 0.5); dead sites filled by the softmax lottery
(temperature `T` = 0.12) among the start-of-step occupants of the site and its four neighbours (local), or of 5
random sites (global); 6000 steps.

**Ingredient: care goes only to juvenile offspring.**

- **Ages.** Every occupant has an age. A newborn has age 0 at the first payoff computation after its birth; each
  survivor's age rises by 1 at the end of every step. Founders start at age 0 (they have no parent, so their age
  never affects care). Ages draw nothing from any random stream.
- **Juvenile:** age < `J` at the payoff computation. A helper sends `B·h_i` in equal shares to its living
  **juvenile** offspring, and the benefit is lost if it has none. It still pays `C·h_i` every step.
- **Who gives care.** A parent is always at least age 1 at a payoff computation (its offspring are born in a step
  in which it was already present), so only adults give care; that needs no rule.
- **Attempt 1: `J` = 2** (care in the first two steps after birth). `J` → infinity is the R1 base exactly.

**Arms (seeds 0-19, 6000 steps, rare start unless stated, `λ` = 0.5, C = 0.2, b/c = B/C).**

| Arm | Care goes to | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| Y6-local | own juvenile offspring | 6 (1.2) | local | rare | test |
| YN6-local | juvenile neighbours (equal shares among the juveniles in the four neighbouring sites, any parentage; lost if none; never self) | 6 (1.2) | local | rare | control: help to young neighbours, same B |
| Y-below | own juvenile offspring | 0.25 (0.05) | local | common | below-rule control |
| Y3-local, Y12-local, Y24-local | own juvenile offspring | 3, 12, 24 | local | rare | descriptive sweep |
| Y6-global | own juvenile offspring | 6 | global | rare | secondary test |
| Y12-global | own juvenile offspring | 12 | global | rare | descriptive |

Eight arms, 160 runs. YN6-local is new, so it is a prospective control. It differs from Y6-local in recipients
(juvenile neighbours of any parentage against own juveniles), in how many share the benefit, and in how often it is
lost, so the contrast is the own-young-care package against help to young neighbours, not parentage alone; under
local settlement juvenile neighbours are often the helper's own offspring or other relatives.

**Classification (mechanical, in this order).** Success: final mean `h` >= 0.60; maintained: final mean `h` >= 0.60
from the common start.

1. **Local failure:** Y6-local succeeds in < 15/20, or Y-below is maintained in > 2/20.
2. **Comparison failed:** Y6-local leads YN6-local by fewer than 8 successes, or one-sided Fisher p >= 0.025
   (independent samples, seed pairing ignored; Bonferroni over two attempts).
3. Otherwise **met**.

**Secondary (reported separately).** H2: Y6-global succeeds in >= 15/20, read only if its mean neighbour `h`
correlation over steps 1000-6000 is <= 0.10 (low correlation does not make recipients unrelated).

**Descriptive (diagnostics averaged over payoff states after 1000-5999 updates, then over runs).** As in R1 (death
probability of cared, uncared and parents; cared fraction; living offspring per occupant; benefit lost,
`Σ h_i·1[no recipient] / Σ h_i`, where "no recipient" means no living juvenile offspring in the offspring-care arms and
no juvenile in the four neighbouring sites in YN6-local); plus living juvenile offspring per occupant, the
juvenile fraction of occupants, and mean age. Success counts, mean final `h`, mean `h` every 50 steps, neighbour `h`
correlation at steps 1000, ..., 6000.

**Attempt 2 (fixed now; runs only if attempt 1 is classified local failure or comparison failed).** A smaller step
toward the R1 base: `J` = 5. Arms with the prefix `Y2-` and the same roles (Y2-6-local test, Y2-N6-local control,
Y2-below, Y2-3-local, Y2-12-local, Y2-24-local, Y2-6-global secondary, Y2-12-global); same classification with these
names.

**Checks (deterministic tests, before running).**

- With `J` larger than any age reached, Y6-local and Y6-global reproduce R1's R2-6-local and R2-6-global exactly
  (full `h`, label, id trajectories).
- Ages: newborns 0 at their first payoff computation, survivors +1 per step, no random draws.
- A helper's care reaches only its living juvenile offspring in equal shares, lost if none; YN6-local's care reaches
  only juvenile neighbours in equal shares, lost if none; never self.
- With B = C = 0 and local settlement, the model reproduces K-null exactly.

**Decision.**

- **Met (either attempt):** at these settings, care aimed at own young (for `J` steps after birth) spread at b/c = 6
  and beat help to young neighbours. That version is the base for R3 (energy), pre-registered next on the user's go.
- **Neither met:** recorded with its classification; the next, smaller step is decided with the user.
- Exploratory: two attempts, one test level.

**Predictions (mine, before any data).**

- Attempt 1 met: about 55%. With cared offspring surviving well, many living offspring are older than 2 and no
  longer cared for, so more benefit is lost; but the young are also where survival care was doing most.
- YN6-local <= 3/20: about 60% (juvenile neighbours under local settlement are often relatives).
- Y6-global >= 15/20 (H2): about 55%.
- Attempt 2 met, given attempt 1 is not: about 60%.

**Budget.** 160 runs (about 35 s each): about 12 minutes on 8 cores; attempt 2 about the same. Code gets a Codex
review before running; wording before commit.

**Limits.**

- `J` is a design choice (2, then 5), not derived; juveniles still reproduce and are still subject to the lottery
  like adults, so "juvenile" means only "still receives care".
- Benefit and cost act in different currencies, as in R1.
- The global arms change where offspring settle and who competes, as before.

## Step R3a: care and its cost carry over as body condition (pre-registration 2026-11-19, after R2; no R3a data; not yet reviewed by Codex, usage limit until 2026-11-20 03:00)

**Why this step, and why split.** The planned R3 (energy) bundles several ingredients: an energy store that persists
across steps, income, births that need an energy threshold, and death at zero energy. Following the one-ingredient
rule, R3 is split. R3a adds only the store: so far, care received and the cost paid act in the step they happen and
are then forgotten. In R3a they accumulate into a condition state that decays over time, so care received when young
can still help after the juvenile period, and a parent's caring depletes it over its whole life. Energy-limited
births (R3b) and starvation (R3c) are pre-registered later, one at a time.

**From the base (R2, attempt 1).** Overlapping generations; ages; helper `i` sends `B·h_i` in equal shares to its
living juvenile offspring (age < 2), lost if none, and pays `C·h_i` (C = 0.2); death `d = 0.5·exp(−0.5·R/T)`,
fecundity `W = 1 + 0.5·R − C·h` (`λ` = 0.5); births by the softmax lottery (temperature `T` = 0.12) among the
start-of-step occupants of the site and its four neighbours (local) or of 5 random sites (global); 6000 steps.

**Ingredient: two condition stores with carry-over `ρ`.** Each occupant has a care store `S` and a depletion store
`D`, both 0 at birth (founders included). Each step, before deaths and births:

- `S_i ← ρ·S_i + R_i` (care received this step is added; older care decays by `ρ` per step);
- `D_i ← ρ·D_i + C·h_i` (the cost paid this step is added; older cost decays likewise);
- death `d_i = 0.5·exp(−0.5·S_i/T)` and fecundity `W_i = 1 + 0.5·S_i − D_i`, i.e. R2's formulas with `R` replaced by
  `S` and `C·h` by `D`.

Survivors keep their stores; newborns start at 0. Stores draw nothing from any random stream. **`ρ` = 0 is R2
exactly** (a test checks this). The stores are not rescaled: at steady state a helper paying every step carries
`D = C·h/(1 − ρ)`, while an offspring receives care only for its first two steps, so its `S` peaks at about
`R·(1 + ρ)` and then decays. Carry-over therefore amplifies the cost of a lifetime of caring more than the benefit
of two steps of being cared for; that asymmetry is part of what R3a tests, not a side effect to remove.

- **Attempt 1: `ρ` = 0.8** (half-life about 3 steps; the mean death probability in R2's working arms was about 0.3,
  so a typical lifetime is a few steps).

**Arms (seeds 0-19, 6000 steps, rare start unless stated, `λ` = 0.5, juvenile age < 2, C = 0.2, b/c = B/C).**

| Arm | Care goes to | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| E6-local | own juvenile offspring | 6 (1.2) | local | rare | test |
| EN6-local | juvenile neighbours, any parentage (as YN6-local), same stores | 6 (1.2) | local | rare | control |
| E-below | own juvenile offspring | 0.25 (0.05) | local | common | below-rule control |
| E3-local, E12-local, E24-local | own juvenile offspring | 3, 12, 24 | local | rare | descriptive sweep |
| E6-global | own juvenile offspring | 6 | global | rare | secondary test |
| E12-global | own juvenile offspring | 12 | global | rare | descriptive |

Eight arms, 160 runs. EN6-local is a prospective control; as in R2, the contrast is the own-young-care package
against help to young neighbours, not parentage alone.

**Classification (mechanical, in this order).** Success: final mean `h` >= 0.60; maintained: final mean `h` >= 0.60
from the common start.

1. **Local failure:** E6-local succeeds in < 15/20, or E-below is maintained in > 2/20.
2. **Comparison failed:** E6-local leads EN6-local by fewer than 8 successes, or one-sided Fisher p >= 0.025
   (independent samples, seed pairing ignored; Bonferroni over two attempts).
3. Otherwise **met**.

**Secondary (reported separately).** H2: E6-global succeeds in >= 15/20, read only if its mean neighbour `h`
correlation over steps 1000-6000 is <= 0.10.

**Descriptive.** As in R2 (death of cared, uncared and parents; cared fraction; juvenile fraction; living (juvenile)
offspring per occupant; benefit lost; mean age), plus the mean `S` and `D` of all occupants, of juveniles, and of
occupants with living offspring, averaged over payoff states after 1000-5999 updates, then over runs. "Cared" means
`R > 0` this step.

**Attempt 2 (fixed now; runs only if attempt 1 is classified local failure or comparison failed).** A smaller step
toward R2: `ρ` = 0.4. Arms with the prefix `E2-` and the same roles (E2-6-local test, E2-N6-local control, E2-below,
E2-3-local, E2-12-local, E2-24-local, E2-6-global secondary, E2-12-global); same classification.

**Checks (deterministic tests, before running).**

- `ρ` = 0 reproduces R2's Y6-local, Y6-global and YN6-local exactly (full `h`, label, id and age trajectories).
- Stores follow the update rules; newborns start at 0; survivors keep their stores; no random draws.
- Death and fecundity use `S` and `D` as specified.
- With B = C = 0 and local settlement, the model reproduces K-null exactly.

**Decision.**

- **Met (either attempt):** at these settings, care for own young spread at b/c = 6 with care and its cost carried
  over as condition, and beat help to young neighbours. That version is the base for R3b (births need energy),
  pre-registered next on the user's go.
- **Neither met:** recorded with its classification; the next, smaller step is decided with the user.
- Exploratory: two attempts, one test level.

**Predictions (mine, before any data).**

- Attempt 1 met: about 35%. At `ρ` = 0.8 the steady cost of caring is five times the per-step cost, while a cared
  offspring's condition peaks at under twice one step's care.
- EN6-local <= 3/20: about 75%.
- E6-global >= 15/20 (H2): about 35%.
- Attempt 2 met, given attempt 1 is not: about 55%.

**Budget.** 160 runs (about 35-40 s each): about 13 minutes on 8 cores; attempt 2 about the same. Code gets a Codex
review before running; wording before commit.

**Limits.**

- `ρ` is a design choice (0.8, then 0.4); the two stores share it.
- The stores are condition indices with R2's units, not an energy budget: there is no income, no limit on paying
  the cost, and no starvation (those are R3b-R3c).
- Benefit and cost still act in different currencies (survival and fecundity for `S`, fecundity for `D`).
