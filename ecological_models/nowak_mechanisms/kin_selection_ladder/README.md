# Kin Selection Ladder: From the Moran Model to an Ecological Model (pre-registration 2026-11-19)

Status: **pre-registered, nothing built or run** (one neutral run was timed: h = 0, no helping data). Revised
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
