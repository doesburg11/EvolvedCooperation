# Kin Selection Ladder: From the Moran Model to an Ecological Model (pre-registration 2026-11-19)

Status: **steps 0-1 and 0c run 2026-11-19. T0a not met (14/20), T0b not met (S-kin 0/20), T0c not met in both attempts (H-kin 0/20, H2-kin 0/20, while uniform routing spread 20/20 at 3000 steps). The user then chose a viscosity base: **step 0d met** (local replacement 20/20 against global-competitor replacement 1/20, p = 1.5e-10), so uniform routing with local replacement is the revised ladder's base. See `RESULTS.md`.** Pre-registration below (one neutral run was timed before it: h = 0, no helping data). Revised
after a Codex review, before any code.

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
