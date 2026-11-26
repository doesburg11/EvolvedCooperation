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
met in attempt 1:** 20/20 against 0/20, and 20/20 without local settlement. **Step R3b (a birth costs the surviving parent
condition, `c_b` = 0.5) met in attempt 1:** 19/20 against 0/20, and 20/20 without local settlement. **Step R3c (births need a minimum
condition, `θ` = 0.25) met in attempt 1:** 20/20 against 0/20, and 20/20 without local settlement; ineligibility was
concentrated among helpers, but sites almost never stayed empty (occupancy 1.00), so vacant space is still untested. **Step R3d (starvation, death when the
condition score falls below `σ` = 0) met in attempt 1:** 19/20 against 0/20, and 20/20 without local settlement;
starvation was active but weak (1.3% of deaths in the test arm, just above the 1% bar). The energy steps R3a-R3d are
complete; substantial vacant space remains untested. **Step R4 (income from a limited, renewable site resource,
`γ` = 0.15) met in attempt 1:** 19/20 against 0/20, and 20/20 without local settlement; added starvation deaths were 26% of deaths
in the test arm, but vacant space stayed rare (at most 1.4% of fills emptied, also at `γ` = 0.08). Helping
ended higher in R4 than in R3d (0.90 against 0.65; descriptive, separate unpaired batches). **Diagnostic DR4
(valid, same-batch references reproduced exactly):** a uniform baseline of 0.75 met the registered rise criterion
(final `h` 0.94), while a baseline of 0.85, approximately R4's mean income store, did not (0.63); with founder and
newborn stores at 0.75, R4 still ended at 0.90; the birth-cost reading is unclear. So at these settings a
sufficiently low condition baseline can be sufficient; the mechanism favouring care was not identified. **Step R5a (foraging over the neighbourhood): the exposure pilot was below its
threshold** (harvest changed by more than 0.01 in 0.78% and 0.06% of occupant-steps, bar 2%), so its main run was
not done; window occupancy remained at least 0.998. **Step R5b (movement into empty sites) was not run** (user decision: with the
lattice this full, moves are bounded below its pilot bar). **Step R6 (the newborn's endowment paid by its parent):
the pilot found vacant space rare at both levels** (fills left empty 0.28% at `q` = 1, where the recorded
starvation rate of recent parents was 100%, and 1.97% at `q` = 0.5; bar 5%), so its main run was not done. **Step
R7 (juveniles cannot breed): the pilot chose no level** (`a_b` = 2 not viable: one of two seeds went extinct during an
early low-occupancy phase observed when all founders started at age 0; `a_b` = 1 viable but fill failure 3.65%, bar 5%), so its main
run was not done; the surviving `a_b` = 2 seed had 19% fill failure (exploratory, looked at after the selection). **Step R7b (R7 at `a_b` = 2 with founders starting at adult age, data-suggested): not viable** (both fresh pilot
seeds extinct, at updates 376 and 193, with occupancy declining across the sampled checkpoints), so its main run was
not done. **Step R8 (parent-driven births into empty neighbouring sites, with an energy gate and an energy-split attempt; the
last attempt at the empty-site rung): Stage S (demographic screen) chose `d0` = 0.2, `g_rep` = 0.5** (occupancy
0.77 at fixed `h` = 0 and 0.95 at `h` = 0.6; without care, both tested points one grid step higher in either parameter
ended in extinction);
**Stage M: neither primary test met the criterion** (both classified as local failure; test arm 0/20).
Own-young care settled near `h` = 0.35 with local births; in attempt 2, the global-dispersal arms reached about 0.99,
with 20/20 successes. Per the hard stop agreed in advance, the
empty-site rung is closed; next is a write-up of R1-R4 and the empty-site attempts. See the
last sections and `RESULTS.md`. The original step 1 (genomic kin
weights) was not run. See `RESULTS.md`. Each pre-registration below was revised after a Codex review, before any
code or data for that step, except R2 and R3a: Codex hit a usage limit, so they were reviewed only after their runs
(2026-11-20; no verdict-changing finding, see `RESULTS.md`).

## Close-out (2026-11-26): step 5 in empty-site islands

After the lattice route reached its hard stop, step 5 (births need free space, population size not fixed) was taken
in a port of Alizon and Taylor's (2008) empty-site island model, each test with a theory screen first, one
pre-registered attempt and a control that pools the gift away from the donor's patch (or shares it with everyone):

| Test | Recipients | b/c | Test arm at endpoint | Control at endpoint | Verdict |
| --- | --- | --- | --- | --- | --- |
| `STEP5_EMPTY_SITES.md` (2026-11-25) | patch-mates | 14 | 20/20 | 0/20 | met, own offspring not excluded |
| `STEP5_NONOFFSPRING.md` (2026-11-26) | patch-mates except own offspring | 28 | 20/20 | 0/20 | met: among non-offspring relatives |
| `STEP5_OWNOFFSPRING.md` (2026-11-26) | own offspring at home | 14 | 20/20 | 0/20 | met: through parental care (help after they settle) |

All three are read as *consistent with* kin selection: the controls also change what a patch's gifts do for itself.
Limits: islands rather than a grid; no energy, limited food, starvation or movement; clonal inheritance; help to own
offspring is help after they settle, not care of dependent young. Theory screens: `theory/THEORY_SCREEN_ALIZON_TAYLOR.md`,
`theory/THEORY_SCREEN_NO_OFFSPRING.md`, `theory/THEORY_SCREEN_OWN_OFFSPRING.md`; results: `RESULTS.md`. As agreed with
the user before the last two rungs (at most two, one attempt each, then a stop), the kin line paused here; the next
ingredients would be energy, limited food and starvation, then movement, one at a time. The draft `STEP5K_SIBLINGS.md` (below)
was not taken up.

## Summary of the ladder (2026-11-20, after R8; the line is closed for now)

**2026-11-24:** the empty-space step (step 5 of the site's table) was reopened with the user's agreement as a smaller
step on the K1 base, with its own pre-registration, budget and hard stop: [`STEP5_RESTART.md`](STEP5_RESTART.md).
The rest of the ladder stays closed. Result (same day): not met, hard stop reached (`RESULTS.md`, "Step 5 restart").

**2026-11-25 (draft only):** [`STEP5K_SIBLINGS.md`](STEP5K_SIBLINGS.md) drafts a side step, not agreed and not
reviewed: costly help to siblings with global births (kin association without viscosity), a shuffled-group
control that removes only relatedness, and a direction-based criterion. Queued behind `STEP5_EMPTY_SITES.md`.

This section summarizes the whole ladder; the detailed pre-registrations follow below, and every result is in
`RESULTS.md`. The main comparisons use a 24 × 24 torus, 20 seeds per arm and a 0.60 endpoint on final mean helping
`h`, each against the control registered for its step; pilots and diagnostics used their own sample sizes and
criteria. All results hold at these settings only.

**What the ladder set out to do.** Start from the working Moran kin-selection model and add one ecological
ingredient per step, so that each step shows helping spreading against a control before the next, until the model
resembles a PredPreyGrass-style ecology (energy, limited food, empty space, movement).

| Phase | Steps | Outcome |
| --- | --- | --- |
| Moran level | 0-0c | Kin-biased routing spread faster at 1000 steps (14/20 against 3/20 without it), but the difference disappeared by 3000 steps (20/20 in both); helping spread only where it had no net direct cost to the helper (weak altruism), and every costly-helping arm failed (0/20). |
| Viscosity base | 0d, 1, 1b, 1c, 2a | Spread needed local replacement (0d: 20/20 against 1/20 with global competitors); it survived overlapping generations (1) and selection half through survival (1c, `λ` = 0.5); with selection fully through survival the local arm failed (1b; 1c at `λ` = 1, where the global arm reached 14/20); with ages, local and global settlement both reached 20/20 (2a, comparison failed). |
| Costly-helping base | K0 | **Costly help to neighbours spread only with local replacement**: at b/c 12, 20/20 against 0/20 with global competitors (none at b/c 3 or 6). This is the ladder's kin-selection-by-viscosity result. |
| Parental-care base | K1 | Care for own offspring spread at b/c 6 (18/20 against 0/20 for neighbour help), and also without local settlement (20/20). |
| Rebuilt ladder | R1-R4 | Care for own young kept spreading as ingredients were added: survival effect (R1), ages (R2), carried-over condition (R3a), birth costs (R3b), a breeding threshold (R3c), starvation (R3d), and income from a limited renewable resource (R4): 19-20/20 against 0/20 for help to young neighbours at every step, and 20/20 without local settlement. |
| Empty-site rung | R5a, R5b, R6, R7, R7b, R8 | **Not reached.** Foraging over the neighbourhood (R5a), a parent-paid endowment (R6) and a breeding age of 1 (R7) left the lattice almost full; a breeding age of 2 was not viable (one of two R7 pilot seeds and both R7b pilot seeds went extinct); movement (R5b) was skipped. Parent-driven births into vacant sites (R8) produced substantial vacancies with the energy split (attempt 1) but rare ones with the free endowment (attempt 2); in both, care for own young settled near `h` 0.35 with local births and the test arm missed the endpoint (0/20). |

**What it shows.**

- **Kin selection by viscosity, with a real cost to the helper, was shown once:** at the K0 level (overlapping
  generations, costly help to neighbours, b/c 12), helping spread only with local replacement.
- **Care for own young is robust to ecological detail:** survival effects, ages, energy stores, birth costs,
  breeding and starvation cutoffs, and limited income did not stop it (R1-R4). But it spread equally well without
  local settlement (K1, R2-R4: 20/20), so under the broad definition used in this repo (see `../README.md`) these steps show **kin
  selection through parental care**, a benefit to the helper's own offspring, not kin selection among non-offspring
  relatives. The comparison changes who receives the help as a whole, not parentage alone. Many treatments count
  parental care as direct fitness and keep "kin selection" for help to other relatives.
- **The replacement rule fixes the population size in practice.** As long as every death is refilled by a lottery
  among neighbours, sites stay full (occupancy at least 0.996 in every viable run through R7); changing the parents'
  condition or the endowment did not change that (R4-R6, DR4).
- **With parent-driven births, care was lower with local than with global births** (R8, attempt 2: 0.99 and 20/20
  under global dispersal against 0.35 locally). This is the reverse of the earlier pattern and is consistent with, but
  does not establish, kin competition (relatives competing for the same nearby vacancies, Taylor 1992). Diagnostic DR8 found that locally about two thirds of breeding opportunities had no vacant neighbour,
  for high and low helpers alike (high helpers only 0.6 percentage points more often), and own offspring were 12% of
  neighbours in both classes: space was short for everyone, rather than specifically around helpers.
- **Diagnostics:** survival-only care settles at a low level reached from both sides (DR1); the higher helping under
  limited income in R4 was reproduced by a uniform cut in condition to 0.75, not 0.85, so helping levels depend on
  where the condition cutoffs sit (DR4).

**What it does not show.** Kin selection among non-descendant relatives in an ecological model; any result with
vacant space and local care reaching the endpoint; movement, sexual reproduction, predators, or a PredPreyGrass port.

**Open threads (none scheduled).** A direct test of kin competition with parent-driven births (for example
dispersal distance as the varied factor); costly help to non-offspring relatives once a model with vacant space
supports local care; a model family in which population size follows the resource from the start, instead of a
replacement lottery.

## Why a ladder

The ecological kin-selection model (`../`, the base `kin_selection` package) never showed kin selection cleanly. Each test exposed a
new problem: care is a lifeline, not a bonus (`../floor_control/`); learning adds nothing beyond a
small constant care effort (`../learning/`); long runs die because mates run out
(`../bonus_care/`, Amendment 1). Patching that model down has not converged.

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
  *Clarification 2026-11-20 (Codex post-run review; text above kept as registered): this is wrong for `J` = 2. An
  age-1 parent is itself juvenile, so juveniles can give care, and founders count as juvenile neighbours in the
  control. R2 restricts recipients, not donors.*
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

## Step R3b: a birth costs the parent condition (pre-registration 2026-11-20, after R3a; no R3b data; revised per Codex review)

**Why this step, and a change to the R3 split.** R3a planned "births need energy" as R3b. Done literally, that
bundles two ingredients: a birth threshold, and the empty sites that appear when no candidate meets it (the
lattice has never had vacancies). Following the one-ingredient rule, R3b adds only the cost side: **each realized birth by a parent that survives the step
draws on the parent's condition.** The threshold with vacancies becomes R3c, and starvation R3d. Each is
pre-registered later, one at a time.

**From the base (R3a, attempt 1).** Overlapping generations; ages; helper `i` sends `B·h_i` in equal shares to its
living juvenile offspring (age < 2), lost if none, and pays `C·h_i` (C = 0.2). Condition stores `S ← ρS + R` and
`D ← ρD + C·h` with `ρ` = 0.8; death `d = 0.5·exp(−0.5·S/T)`; birth-lottery fecundity `W = 1 + 0.5·S − D`; births by
the softmax lottery (temperature `T` = 0.12) among the start-of-step occupants of the site and its four neighbours
(local) or of 5 random sites (global); newborns start with `S = D = 0`; 6000 steps.

**Ingredient: a birth cost `c_b` added to the parent's depletion store.** A **realized birth** is a newborn at a
site whose occupant died this step; its parent is the lottery winner recorded for that site (`last_parents` at the
dead sites). Lottery draws at surviving sites are discarded and are not births. After the step, each parent that
**survived** the step adds `k·c_b` to its `D`, where `k` is its number of realized births that step (counted over the
newborns' sites). A parent that died in the same step is still recorded as the newborn's parent but pays nothing,
since its own site's stores are reset; a newborn always starts at `S = D = 0`, also when its parent came from the
same site. The charge does not change this step's lottery (already drawn); it enters the next step's lottery as
extra depletion `ρ·k·c_b` and keeps decaying by `ρ`. It does not change death (death depends on `S` only, as in R3a).
No random draws are added. **`c_b` = 0 is R3a exactly** (a test checks this).

- **Attempt 1: `c_b` = 0.5** (one birth costs as much as 2.5 steps of full helping, `C·h` = 0.2 at `h` = 1).
  Strength: depletion enters the lottery as `W/T` with `T` = 0.12, so one charge multiplies the parent's odds in the
  next lottery, against an otherwise identical candidate, by about `exp(−ρ·c_b/T)` ≈ 0.036, and the factor recovers
  to 0.5 only after about 8 steps. Repeat breeding is strongly damped. Scale of the average: births equal deaths,
  about 0.06-0.11 per occupant per step in R3a's working arms, and only births to surviving parents are charged, so
  `c_b · 0.1 / (1 − ρ)` = 0.25 is an upper bound on the mean added depletion (deaths also erase stores). A larger
  `c_b` = 1 (odds factor about 0.0013) would make breeding nearly once per life; that is not this step.

**What could go either way.** The cost falls on lottery winners, so it can even out fecundity and could weaken
selection on everything, `h` included; E6-local in R3a ended at 0.64-0.82, near the 0.60 bar. It can also dampen
repeat breeding by cared-for offspring (high `S`, so higher `W`), partly taxing the benefit of care (R3a did not
measure breeding by care status). The charge per birth is the same for helpers and non-helpers, but it can still
affect them differently through how often each breeds and survives.

**Arms (seeds 0-19, 6000 steps, rare start unless stated, `λ` = 0.5, juvenile age < 2, `ρ` = 0.8, C = 0.2,
b/c = B/C).**

| Arm | Care goes to | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| Q6-local | own juvenile offspring | 6 (1.2) | local | rare | test |
| QN6-local | juvenile neighbours, any parentage (as EN6-local), same stores and birth cost | 6 (1.2) | local | rare | control |
| Q-below | own juvenile offspring | 0.25 (0.05) | local | common | below-rule control |
| Q3-local, Q12-local, Q24-local | own juvenile offspring | 3, 12, 24 | local | rare | descriptive sweep |
| Q6-global | own juvenile offspring | 6 | global | rare | secondary test |
| Q12-global | own juvenile offspring | 12 | global | rare | descriptive |

Eight arms, 160 runs. As before, the contrast is the own-young-care package against help to young neighbours, not
parentage alone.

**Classification (mechanical, in this order; unchanged from R2 and R3a).** Success: final mean `h` >= 0.60;
maintained: final mean `h` >= 0.60 from the common start.

1. **Local failure:** Q6-local succeeds in < 15/20, or Q-below is maintained in > 2/20.
2. **Comparison failed:** Q6-local leads QN6-local by fewer than 8 successes, or one-sided Fisher p >= 0.025
   (independent samples, seed pairing ignored; Bonferroni over two attempts). Kept for comparability with K0-R3a.
   As Codex noted, once the >= 15/20 and >= 8 lead gates hold, Fisher always passes (largest p 0.012), so the count
   gates are the effective rule and no calibrated error rate is claimed. A one-sided exact McNemar test on the
   matched seeds is reported, descriptive only.
3. Otherwise **met**.

**Secondary (reported separately).** H2: Q6-global succeeds in >= 15/20, read only if its mean neighbour `h`
correlation over the six samples at steps 1000, 2000, ..., 6000 is <= 0.10; if the correlation is undefined, H2 is
uninterpretable.

**Descriptive.** As in R3a, plus: realized births per occupant per step; the fraction of births charged (parent
survived); the part of `D` added by births (tracked in a diagnostic-only copy with the same decay, never used by the
model); and the mean `D`, at the next payoff computation, of surviving parents of realized births in the last
step. Averaged over payoff states after 1000-5999 updates, then over runs. "Uncared" is everyone with `R = 0`
this step, juveniles included.

**Attempt 2 (fixed now; runs only if attempt 1 is classified local failure or comparison failed).** A smaller step
toward R3a: `c_b` = 0.2 (one step of full helping; next-lottery odds factor about 0.26). Arms with the prefix `Q2-` and the same roles; same classification.

**Checks (deterministic tests, before running).**

- `c_b` = 0 reproduces R3a's E6-local, E6-global and EN6-local exactly (full `h`, label, id, parent-id, age, `S`
  and `D` trajectories).
- Birth cost, with forced lottery outcomes: a surviving parent with two realized births gains exactly `2·c_b`; a
  win at a surviving site is discarded and charges nothing; a parent that died wins its own site and another site,
  pays nothing, and both newborns start at 0; non-parents gain nothing; this step's lottery fecundity is unchanged;
  the next lottery sees exactly `ρ·k·c_b` extra depletion.
- Site-by-site death: the death draw uses each site's own `S` (a test with unequal `S` per site, not only the mean).
- From the R2 review: a finite-`J` test calling `step()` with an age-1 donor, an age-2 offspring that receives no
  care, and a founder counted as a juvenile neighbour in the control.
- With B = C = 0, `c_b` = 0 and local settlement, the model reproduces K-null exactly.
- Archive: the verdict file records `care_rho` and `c_b`; per-seed H2 correlation samples are saved.

**Decision.**

- **Met (either attempt):** at these settings, care for own young (b/c = B/C, the care benefit-to-cost ratio, = 6)
  crossed the endpoint threshold with a delayed fecundity cost per birth added to R3a's condition stores, and beat
  help to young neighbours. That version is the base for R3c (births need a
  minimum condition, with empty sites), pre-registered next on the user's go.
- **Neither met:** recorded with its classification; the next, smaller step is decided with the user.
- Exploratory: two attempts, one test level.

**Predictions (mine, before any data).**

- Attempt 1 met: about 45%. The charge is the same for helpers and non-helpers, but it strongly damps repeat
  breeding, and Q6-local starts from R3a's narrow margin.
- QN6-local <= 3/20: about 80%.
- Q6-global >= 15/20 (H2): about 55%.
- Attempt 2 met, given attempt 1 is not: about 60%.

**Budget.** 160 runs, about 15 minutes on 8 cores; attempt 2 about the same. The pre-registration and code get a
Codex review (gpt-6.2-sol, medium) before running; wording (gpt-reserve, medium) before commit.

**Limits.**

- `c_b` is a design choice (0.5, then 0.2), in the units of the condition stores, not an energy budget.
- Births still never fail: there is no threshold and no empty site (R3c), and no starvation (R3d).
- The birth cost lowers only fecundity, not survival, because `D` enters only the lottery.

## Step R3c: births need a minimum condition, so sites can stay empty (pre-registration 2026-11-20, after R3b; no R3c data; revised per Codex review)

**Why this step.** So far every death is refilled at once: the lottery always finds a parent. In real populations,
an individual in poor condition cannot breed, and space can go unused. R3c adds that single change: **a candidate
can win a birth only if its condition is high enough; a site whose candidates are all below the bar stays empty.**
This is one mechanistic ingredient: the eligibility filter changes the lottery odds even when a site fills, and
vacancies, with their feedback on care and competition, follow from the same rule when no candidate qualifies. Starvation (R3d) is not part of this step.

**From the base (R3b, attempt 1).** Overlapping generations; ages; helper `i` sends `B·h_i` in equal shares to its
living juvenile offspring (age < 2), lost if none, and pays `C·h_i` (C = 0.2). Condition stores `S ← ρS + R`,
`D ← ρD + C·h` (`ρ` = 0.8); each realized birth by a surviving parent adds `c_b` = 0.5 to its `D`; death
`d = 0.5·exp(−0.5·S/T)`; lottery fecundity `W = 1 + 0.5·S − D`; softmax lottery (temperature `T` = 0.12) among the
start-of-step occupants of the site and its four neighbours (local) or of 5 random sites (global); 6000 steps.

**Ingredient: a breeding threshold `θ` on `W`, with empty sites.**

- **Eligibility.** A start-of-step occupant is eligible to win a birth only if `W_i >= θ`, with `W` computed as in
  R3b at that step's payoff computation. Ineligible occupants keep living, helping and paying as before.
- **Lottery.** For each site that needs filling (its occupant died this step, or it was empty), the softmax lottery
  runs over the eligible candidates only. If none is eligible, the site stays empty this step. To keep random
  streams independent of eligibility, every site still consumes the same lottery and mutation draws as in R3b
  (a site with no eligible candidate draws from its unfiltered lottery and the result is discarded).
- **Synchronous update and random streams.** Occupancy, candidate traits and ids, `W` and eligibility are frozen
  at the payoff computation. A candidate that dies this step can still be a parent, including at its own site (its
  site is in its own pool, as before). Newborns are not candidates until the next step. All births are committed
  together; then surviving parents are charged `c_b` per realized birth. In the global arms each destination draws
  5 distinct lattice sites in the existing order, then filters out empty and ineligible ones, without redraws.
  Every lattice site keeps exactly one lottery draw (a site with no eligible candidate draws over its unfiltered
  pool and the result is discarded), and the mutation mask, its normal draws, the death draws and the global
  candidate draws are made for all sites on their existing streams. At `θ` = −infinity the existing lottery is
  used, so outcomes and streams are identical to R3b.
- **Empty sites.** An empty site has no occupant: it neither helps nor pays, receives no care, is never a candidate
  and never dies; its stores and age are 0. It can be filled at a later step if an eligible candidate is among
  its pool. In the global arms, an empty site drawn among the 5 random candidates is simply not a candidate.
- **Everything else unchanged.** Care is shared among living (occupied) juvenile offspring, or occupied juvenile
  neighbours in the control; benefit is lost if there are none. Births still charge surviving parents `c_b`.
- **`θ` = −infinity is R3b exactly** (a test checks this, with the same random streams).

**Choice of `θ`, and a rough benchmark.** A newborn starts at `W` = 1. A long-lived helper carries
`D ≈ C·h/(1 − ρ) = h` from care costs plus about 0.15 from births, and adults' `S` was about 0.48 in R3b's
Q6-local, so an old helper has `W ≈ 1 + 0.24 − h − 0.15`. At those assumed stores, `W >= θ` holds only for
`h ≲ 1.09 − θ`. This benchmark describes the eligibility of long-lived breeders, not the outcome: the 0.60 endpoint
averages over all occupants, including ineligible ones, and younger adults (less `D`) and recently cared-for
offspring (higher `S`) sit above it.

- **Attempt 1: `θ` = 0.25** (benchmark about 0.84). It also binds for non-helpers after repeated breeding: with
  `S` = 0, three consecutive single-birth charges add about 0.98 to `D` at payoff, enough to exclude at 0.25.
- A larger `θ` = 0.5 would put the benchmark near the 0.60 bar; it was not chosen as the first step.

**Arms (seeds 0-19, 6000 steps, rare start unless stated, `λ` = 0.5, juvenile age < 2, `ρ` = 0.8, `c_b` = 0.5,
C = 0.2, b/c = B/C).**

| Arm | Care goes to | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| V6-local | own juvenile offspring | 6 (1.2) | local | rare | test |
| VN6-local | juvenile neighbours, any parentage (as QN6-local) | 6 (1.2) | local | rare | control |
| V-below | own juvenile offspring | 0.25 (0.05) | local | common | below-rule control |
| V3-local, V12-local, V24-local | own juvenile offspring | 3, 12, 24 | local | rare | descriptive sweep |
| V6-global | own juvenile offspring | 6 | global | rare | secondary test |
| V12-global | own juvenile offspring | 12 | global | rare | descriptive |

Eight arms, 160 runs. As before, the contrast is the own-young-care package against help to young neighbours, not
parentage alone.

**Classification (mechanical, in this order).** Mean `h` is now taken over occupied sites. "Met" refers to this
joint endpoint and to the lead in joint successes. **Success:** final mean
`h` >= 0.60 **and** final occupancy >= 0.5 (a run whose population has collapsed below half the lattice does not
count, whatever its mean `h`); an extinct run is a failure. **Maintained:** the same, from the common start.

1. **Local failure:** V6-local succeeds in < 15/20, or V-below is maintained in > 2/20.
2. **Comparison failed:** V6-local leads VN6-local by fewer than 8 successes, or one-sided Fisher p >= 0.025
   (a calculation that ignores seed pairing; Bonferroni over two attempts). As in R3b, once the count gates hold
   Fisher always passes (largest p 0.012), so the count gates are the effective rule; a paired McNemar test is
   reported, descriptive only.
3. Otherwise **met**.

**Secondary (reported separately).** H2: V6-global succeeds in >= 15/20, read only if its mean neighbour `h`
correlation (over edges with both ends occupied) across the six samples at steps 1000, 2000, ..., 6000 is <= 0.10;
the gate is the mean over all six samples of all 20 seeds, and any undefined sample (for example a uniform trait
field on the occupied edges) makes H2 uninterpretable.

**Descriptive.** As in R3b, plus: both endpoint components per run (final mean `h`, final occupancy), archived;
occupancy (mean over the diagnostic window, over the last 1000 steps, and final), to show whether a passing
population was stable or declining; the fraction of fill attempts whose pool the threshold trimmed (some candidate
excluded) or emptied (site left empty); the fraction of occupants ineligible, overall and by helping level (`h`
below and above 0.5); extinctions per arm. A run can pass with no failed births, and a control can miss the joint
endpoint through low occupancy alone, so these are reported for every arm. Averaged over payoff states after 1000-5999 updates, then over runs.

**Attempt 2 (fixed now; runs only if attempt 1 is classified local failure or comparison failed).** A smaller step
toward R3b: `θ` = 0 (excludes an occupant only when `D > 1 + 0.5·S`; it may be nearly inert). Arms with the prefix `V2-`
and the same roles; same classification.

**Checks (deterministic tests, before running).**

- `θ` = −infinity reproduces R3b's Q6-local, Q6-global and QN6-local exactly (full `h`, label, id, parent-id, age,
  `S` and `D` trajectories), and occupancy stays 1.
- Forced cases: a site whose candidates are all ineligible stays empty, with stores and age 0; an ineligible
  occupant still helps, pays and can die; an empty site never helps, receives, breeds or dies; a candidate with
  `W` exactly `θ` is eligible; a dying parent wins its own site and another, pays nothing, and both newborns start
  at 0; a survivor fills an old vacancy and pays only for realized births; a newborn cannot fill a second site in
  the step it is born; the lottery probabilities over eligible candidates equal the softmax restricted to them.
- Random streams: the lottery, mutation and death generator states after a step with an all-masked pool and with
  a single eligible candidate equal those of the same step at `θ` = −infinity.
- Global arms: empty sites among the 5 random candidates are excluded.
- Care: shares go only to occupied juvenile offspring (or occupied juvenile neighbours in the control).
- Statistics: mean `h` and neighbour correlation use occupied sites only; success needs occupancy >= 0.5;
  extinction gives failure, not an error.
- With B = C = 0, `c_b` = 0, `θ` = −infinity and local settlement, the model reproduces K-null exactly.

**Decision.**

- **Met (either attempt):** at these settings, care for own young met the joint endpoint (mean `h` and occupancy)
  with births that need a minimum condition (and can therefore fail), on top of R3b, and beat help to young
  neighbours in joint successes. That version
  is the base for R3d (starvation: death when condition falls too low), pre-registered next on the user's go.
- **Neither met:** recorded with its classification; the next, smaller step is decided with the user.
- Exploratory: two attempts, one test level.

**Predictions (mine, before any data).**

- Attempt 1 met: about 40%. This is the first hard eligibility cutoff, and it ties the cost of helping directly to
  the ability to breed (through `D`); R3b's Q6-local ended at 0.68, close to the bar.
- VN6-local <= 3/20: about 80%.
- V6-global >= 15/20 (H2): about 50%.
- Attempt 2 met, given attempt 1 is not: about 55%.
- Occupancy in the successful arms: above 0.9 (about 65%).

**Budget.** 160 runs, about 20-30 minutes on 8 cores (the masked lottery is slower); attempt 2 about the same. The
pre-registration and code get a Codex review (gpt-6.2-sol, medium) before running; wording (gpt-reserve, medium)
before commit.

**Limits.**

- `θ` is a design choice (0.25, then 0), on the same condition scale as the lottery, not an energy budget.
- Empty sites change the meaning of "local competition": fewer neighbours compete, and care can no longer reach a
  vacant neighbour site.
- No starvation: an ineligible occupant still dies only at the base rate set by `S` (R3d).
- The benchmark uses R3b means, so it is approximate.

## Step R3d: starvation, death when condition falls too low (pre-registration 2026-11-20, after R3c; no R3d data; revised per Codex review)

**Why this step.** So far condition affects death only through care received (`S` lowers the death probability);
depletion `D`, from caring and from births, lowers only breeding. In real populations, an individual whose reserves
run out dies. R3d adds that single change: **an occupant whose condition score `W` is below a starvation level `σ` dies
this step.** Nothing else changes.

**From the base (R3c, attempt 1).** Overlapping generations; ages; helper `i` sends `B·h_i` in equal shares to its
living juvenile offspring (age < 2), lost if none, and pays `C·h_i` (C = 0.2). Condition stores `S ← ρS + R`,
`D ← ρD + C·h` (`ρ` = 0.8); each realized birth by a surviving parent adds `c_b` = 0.5 to its `D`; condition
`W = 1 + 0.5·S − D`; base death `d = 0.5·exp(−0.5·S/T)`; only occupants with `W >= θ` (`θ` = 0.25) can win a birth,
and a site with no eligible candidate stays empty; softmax lottery (temperature `T` = 0.12) among the start-of-step
occupants of the site and its four neighbours (local) or of 5 random sites (global); 6000 steps; success needs final
mean `h` over occupied sites >= 0.60 and final occupancy >= 0.5.

**Ingredient: starvation below `σ`.**

- At the payoff computation, after the stores are updated, an occupant with `W_i < σ` dies this step with
  certainty; every other occupant dies with the base probability `d_i`. `W` is the same quantity that decides
  eligibility, and `σ <= θ` (also for the joint null `θ = σ` = −infinity), so a starving occupant is always also
  ineligible. `W` is computed once, after care and the stores are updated, before survival.
- The death draw is still made once for every site (the stream is unchanged); survival is then overridden for
  occupied sites with `W < σ`. Starvation uses no random draws. Pools and eligibility stay frozen at the payoff
  computation: a starving occupant still helped and paid this step and can appear in a pool, but it is ineligible,
  so it cannot be the parent of a realized birth; an eligible occupant that dies by the base draw can still breed.
  Only surviving parents are charged, after the fills, as before.
- Its site then needs a birth like any other death, and stays empty if no eligible candidate is in its pool.
- **`σ` = −infinity is R3c exactly** (a test checks this, with the same random streams).

**Who can starve (a screen; corrected per Codex).** From the store updates, a survivor charged for `k` births has,
at the next payoff computation,
`W_next = 0.2 + 0.8·W + 0.5·R_next − 0.2·h − 0.4·k` (with `ρ` = 0.8, `c_b` = 0.5, C = 0.2). Without a birth
(`k` = 0), `W` relaxes toward about `1 − h + 2.5·R`, which is never negative; an occupant at `W >= 0` cannot fall
below 0 in one step. So, for occupants at `W >= 0` in the previous step, **at `σ` = 0 starvation needs a birth**: a parent (necessarily eligible, `W >= θ` = 0.25)
starves after one birth if `W < 0.25 + 0.25·h` (with no care received), so only helpers (`h > 0`) can starve after a
single birth, and higher helpers over a wider band; a non-helper needs two or more births in one step, or births
in quick succession (three consecutive single charges add about 0.98 to `D` at the payoff computation after the third, since the
charges have already decayed: 0.5·(0.8 + 0.64 + 0.512)). Juveniles carry high `S` and low `D`
and should rarely starve. That starvation concentrates among high helpers that breed is a prediction, not a given.

- **Attempt 1: `σ` = 0** (a cutoff at zero on the model's condition score).

**What R3d does not test.** In R3c vacancies were rare (at most 0.3% of fills emptied). Starvation adds deaths but
does not make pools ineligible: a starved site is refilled as long as there is an eligible candidate in its pool.
So vacancies are expected to stay rare here as well. Whether care survives in a population with real vacant space
remains an open step after R3d (for example a higher `θ`, or an income-limited energy budget), to be decided with
the user.

**Arms (seeds 0-19, 6000 steps, rare start unless stated, `λ` = 0.5, juvenile age < 2, `ρ` = 0.8, `c_b` = 0.5,
`θ` = 0.25, C = 0.2, b/c = B/C).**

| Arm | Care goes to | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| F6-local | own juvenile offspring | 6 (1.2) | local | rare | test |
| FN6-local | juvenile neighbours, any parentage (as VN6-local) | 6 (1.2) | local | rare | control |
| F-below | own juvenile offspring | 0.25 (0.05) | local | common | below-rule control |
| F3-local, F12-local, F24-local | own juvenile offspring | 3, 12, 24 | local | rare | descriptive sweep |
| F6-global | own juvenile offspring | 6 | global | rare | secondary test |
| F12-global | own juvenile offspring | 12 | global | rare | descriptive |

Eight arms, 160 runs. As before, the contrast is the own-young-care package against help to young neighbours, not
parentage alone.

**Classification (mechanical, in this order; unchanged from R3c).** Success: final mean `h` over occupied sites
>= 0.60 and final occupancy >= 0.5 (extinct: failure). Maintained: the same, from the common start.

1. **Local failure:** F6-local succeeds in < 15/20, or F-below is maintained in > 2/20.
2. **Comparison failed:** F6-local leads FN6-local by fewer than 8 successes, or one-sided Fisher p >= 0.025 (a
   calculation that ignores seed pairing; Bonferroni over two attempts). Once the count gates hold, Fisher always
   passes (largest p 0.012), so the count gates are the effective rule; a paired McNemar test is reported,
   descriptive only.
3. Otherwise **met**.

**Secondary (reported separately).** H2: F6-global succeeds in >= 15/20, read only if its mean neighbour `h`
correlation (over edges with both ends occupied), the mean over all six samples (steps 1000, ..., 6000) of all 20
seeds, is <= 0.10; any undefined sample makes H2 uninterpretable.

**Activation (reported with the verdict).** Starvation deaths are split into **added deaths** (`W < σ` and the base
draw would have survived) and all below-cutoff deaths. Added deaths are reported per seed for every arm. If added
deaths are fewer than 1% of all deaths in F6-local over the diagnostic window, the verdict is reported as "met (or
not met), starvation inactive": the rule then barely acted and the step does not test starvation. Both endpoint
components (final mean `h`, final occupancy) are kept per run, since a control can fail on occupancy alone.

**Descriptive.** As in R3c, plus: added and all starvation deaths per occupant per step; the share of all deaths
that were added starvation deaths (denominator: all deaths of start-of-step occupants in the step; undefined when
there are none, averaged over steps where defined); the starvation rate by helping level (`h` < 0.5 and `h` >= 0.5),
among occupants charged for a birth in the previous step, and among juveniles. Averaged over payoff states after 1000-5999 updates,
then over runs, over occupied sites.

**Attempt 2 (fixed now; runs only if attempt 1 is classified local failure or comparison failed).** A smaller step
toward R3c: `σ` = −0.1. After one birth an eligible parent starves only if `W < 0.125 + 0.25·h` with no care, which
needs `h` > 0.5; a weaker rule that still acts on high helpers. (`σ` = −0.25 was considered and rejected: an eligible
parent reaches at least −0.2 after one birth, so it would act only after two births in one step and be close to
inert.) Arms with the prefix `F2-` and the same roles; same classification.

**Checks (deterministic tests, before running).**

- `σ` = −infinity reproduces R3c's V6-local, V6-global and VN6-local exactly (full `h`, label, id, parent-id, age,
  `S`, `D`, occupancy trajectories, and the lottery, mutation, death and global generator states).
- Forced cases: an occupant with `W < σ` dies even when its draw says survive; one with `W` exactly `σ` does not
  starve; a starving occupant is never the parent of a realized birth; an eligible occupant that dies by the base
  draw can still breed (committed parent ids checked) in a pool that also holds a starving occupant; a starved site
  is refilled by an eligible candidate, or stays empty if none is eligible; two steps: a surviving winner is
  charged, then crosses `σ` at the next payoff computation and starves; starvation consumes no random draws (the
  `rng` lottery and mutation stream, `death_rng` and `global_rng` states equal those of the same step at `σ` =
  −infinity).
- Diagnostics: added and all starvation counts match the forced cases; shares are over occupied sites; the `h`
  bins are `h` < 0.5 and `h` >= 0.5.
- With B = C = 0, `c_b` = 0, `θ` = `σ` = −infinity and local settlement, the model reproduces K-null exactly.

**Decision.**

- **Met (either attempt):** at these settings, care for own young met the joint endpoint with starvation added to
  R3c's condition rules, and beat help to young neighbours in joint successes (with the activation label above).
  The conclusion is limited to the endpoint at the tested settings. The energy steps R3a-R3d are then
  complete; what comes next (vacant space, income, or a first PPG-style port) is decided with the user.
- **Neither met:** recorded with its classification; the next, smaller step is decided with the user.
- Exploratory: two attempts, one test level.

**Predictions (mine, before any data).**

- Attempt 1 met: about 40%. Starvation adds a survival cost to helpers that breed, on top of the breeding
  threshold, and R3c's V6-local ended at 0.67, close to the bar.
- Starvation active in F6-local (added deaths >= 1% of deaths): about 70%.
- FN6-local <= 3/20: about 80%.
- F6-global >= 15/20 (H2): about 50%.
- Attempt 2 met, given attempt 1 is not: about 50%.
- Fills left empty: below 1% in every arm (about 75%).

**Budget.** 160 runs, about 20 minutes on 8 cores (R3c took 18); attempt 2 about the same. The pre-registration and
code get a Codex review (gpt-6.2-sol, medium) before running; wording (gpt-reserve, medium) before commit.

**Limits.**

- `σ` is a design choice (0, then −0.1), on the same condition scale as the lottery and the threshold.
- Starvation is deterministic and immediate; a real reserve would run down gradually with income, which this model
  does not have.
- The screen is a one-step bound from the store updates; who actually starves depends on the joint distribution of `W`,
  `h` and births, which only the run shows.

## Step R4: income from a limited, renewable site resource (pre-registration 2026-11-20, after R3d; no R4 data; revised per Codex review)

**Why this step.** In R3a-R3d every occupant's condition score starts from a free baseline of 1 each step
(`W = 1 + 0.5·S − D`). The baseline of 1 is free rather than earned, so populations never run short and space almost never empties (occupancy
stayed at 1.00; R3d did have starvation, and rare vacancies). In PredPreyGrass-like ecologies, energy comes from eating a resource that regrows. R4 replaces the
free baseline by **income harvested from a renewable resource on the occupant's own site**. Only the resource's
limitation is new: with an unlimited resource the model is R3d exactly.

**From the base (R3d, attempt 1).** Overlapping generations; ages; helper `i` sends `B·h_i` in equal shares to its
living juvenile offspring (age < 2), lost if none, and pays `C·h_i` (C = 0.2). Stores `S ← ρS + R`, `D ← ρD + C·h`
(`ρ` = 0.8); each realized birth by a surviving parent adds `c_b` = 0.5 to its `D`; condition `W = 1 + 0.5·S − D`;
base death `d = 0.5·exp(−0.5·S/T)`; only occupants with `W >= θ` (`θ` = 0.25) can win a birth, and a site with no
eligible candidate stays empty; an occupant with `W < σ` (`σ` = 0) starves; softmax lottery (temperature
`T` = 0.12) among the start-of-step occupants of the site and its four neighbours (local) or of 5 random sites
(global); 6000 steps; success needs final mean `h` over occupied sites >= 0.60 and final occupancy >= 0.5.

**Ingredient: an income store `G` fed by a site resource `r` that is harvested and regrows.**

- Each site has a resource `r` in [0, 1], 1 at the start.
- At the payoff computation, each occupant harvests `g_i = min(r_i, 0.2)` from its own site (`r_i ← r_i − g_i`)
  and adds it to an income store: `G_i ← ρ·G_i + g_i`. The cap 0.2 = `1 − ρ` makes the steady store of a fully fed
  occupant exactly 1, the old baseline.
- The condition score becomes `W = G + 0.5·S − D` (the 1 is replaced by `G`); eligibility (`W >= θ`) and starvation
  (`W < σ`) use this `W`, as does the lottery.
- At the end of every step, every site's resource regrows: `r ← r + γ·(1 − r)` (empty sites too; an empty site
  harvests nothing).
- A founder or newborn starts with `G = 1` (an endowment, as in R3d where everyone had 1) and `S = D = 0`. A site's
  resource is not reset when its occupant changes. No random draws are added.
- **Timing within a step.** (1) Every start-of-step occupant, including those about to die, harvests from its
  site; (2) `G`, `S` and `D` are updated; (3) `W` is computed once and used for starvation, eligibility and the
  lottery; (4) deaths and births are settled as in R3d; (5) every site regrows from its post-harvest stock. A
  newborn harvests for the first time in the next step. The cap is the literal 0.2. Empty sites carry `G = 1`
  (never used: they are never eligible), so their `W` is as in R3d. At `γ` = 1 the regrowth sets `r` to exactly 1.
- **An unlimited resource is R3d exactly.** At `γ = 1` the resource is refilled to 1 every step, every occupant
  harvests 0.2 and keeps `G = 1` (a test checks exact equality with R3d, random streams included). More generally
  the harvest is never limited while `γ >= 0.2`.

**What limitation does (a screen).** With `γ < 0.2` and a continuously occupied site, the resource is harvested to
0 each step and regrows to `γ`, so the occupant's income settles at `γ` per step and its store at
`G* = γ/(1 − ρ) = 5γ`. `G*` describes a long-lived occupant: turnover restores `G` = 1 for the newborn, and its
store then decays toward `G*`. For such an occupant the condition score is lowered by `1 − 5γ`, helpers and
non-helpers alike. With no care received and no birth charges, a helper's score relaxes toward `G* − h`, so it
starves (`W < 0`) for `h > 5γ` and is ineligible (`W < 0.25`) for `h > 5γ − 0.25`: these individual steady-state
cutoffs are 0.75 / 0.50 at `γ` = 0.15, 0.90 / 0.65 at 0.18, and 0.40 / 0.15 at 0.08. A site needing a fill stays
empty when its pool has no eligible occupant; helping costs and birth charges can cause that even when `G*` is well
above `θ`. This is a screen from steady states, not a prediction of the outcome.

- **Attempt 1: `γ` = 0.15** (`G*` = 0.75, a 25% cut in steady income).
- **Lean descriptive arms (not part of the classification): `γ` = 0.08** (`G*` = 0.4), included only to see whether
  strong limitation produces vacant space.

**Arms (seeds 0-19, 6000 steps, rare start unless stated, `λ` = 0.5, juvenile age < 2, `ρ` = 0.8, `c_b` = 0.5,
`θ` = 0.25, `σ` = 0, C = 0.2, b/c = B/C; `γ` = 0.15 unless stated).**

| Arm | Care goes to | b/c (B) | Settlement | Start | Role |
| --- | --- | --- | --- | --- | --- |
| G6-local | own juvenile offspring | 6 (1.2) | local | rare | test |
| GN6-local | juvenile neighbours, any parentage (as FN6-local) | 6 (1.2) | local | rare | control |
| G-below | own juvenile offspring | 0.25 (0.05) | local | common | below-rule control |
| G3-local, G12-local, G24-local | own juvenile offspring | 3, 12, 24 | local | rare | descriptive sweep |
| G6-global | own juvenile offspring | 6 | global | rare | secondary test |
| G12-global | own juvenile offspring | 12 | global | rare | descriptive |
| G6-local-lean, G6-global-lean | own juvenile offspring, `γ` = 0.08 | 6 | local / global | rare | descriptive only |

Ten arms, 200 runs. As before, the contrast is the own-young-care package against help to young neighbours, not
parentage alone.

**Classification (mechanical, in this order; unchanged from R3c-R3d).** Success: final mean `h` over occupied sites
>= 0.60 and final occupancy >= 0.5 (extinct: failure). Maintained: the same, from the common start.

1. **Local failure:** G6-local succeeds in < 15/20, or G-below is maintained in > 2/20.
2. **Comparison failed:** G6-local leads GN6-local by fewer than 8 successes, or one-sided Fisher p >= 0.025 (a
   calculation that ignores seed pairing; Bonferroni over two attempts). Once the count gates hold, Fisher always
   passes (largest p 0.012), so the count gates are the effective rule; a paired McNemar test is reported,
   descriptive only.
3. Otherwise **met**.

**Secondary (reported separately).** H2: G6-global succeeds in >= 15/20, read only if its mean neighbour `h`
correlation (over edges with both ends occupied), the mean over all six samples (steps 1000, ..., 6000) of all 20
seeds, is <= 0.10; any undefined sample makes H2 uninterpretable.

**Activation (reported with the verdict).** Exposure to limitation is "active" in the attempt's own test arm
(G6-local, or G2-6-local in attempt 2) if its pooled harvest (total harvest over total occupant-steps in the
diagnostic window, summed over seeds; windows without occupants contribute nothing) is at most 0.19, at least 5%
below the unlimited 0.2; otherwise the verdict is labelled "income limitation inactive", and a "met" is then
reported without any claim about limited income. Under continuous occupancy this bar is almost automatic at both
`γ` values: it measures exposure to limitation, not an effect of it. Both endpoint components (final mean `h`,
final occupancy) are kept per seed, since the comparison can also clear through a control's loss of occupancy.

**Descriptive.** As in R3d, plus: mean harvest per occupant per step; mean `G` (all, juveniles, parents); mean site
resource on occupied and on empty sites (pre-harvest, at the payoff computation); the fraction of occupants whose harvest was capped by the resource
(`r < 0.2`); occupancy, fills emptied and extinctions, as before. Averaged over payoff states after 1000-5999
updates, then over runs, over occupied sites (resource means over the relevant sites).

**Attempt 2 (fixed now; runs only if attempt 1 is classified local failure or comparison failed).** A smaller step
toward R3d: `γ` = 0.18 (`G*` = 0.9, a 10% cut). Arms with the prefix `G2-` and the same roles, without lean arms;
same classification.

**Checks (deterministic tests, before running).**

- `γ` = 1 reproduces R3d's F6-local, F6-global and FN6-local exactly (full `h`, label, id, parent-id, age, `S`, `D`,
  occupancy trajectories, and all random generator states); `G` stays exactly 1 and the harvest exactly 0.2.
- Resource and income: harvest is `min(r, 0.2)` on start-of-step occupied sites only (dying occupants
  included), taken before the stores are updated; regrowth `r ← r + γ(1 − r)` on every site at the end of the step,
  from the post-harvest stock; `G` follows its update; a newborn starts at `G` = 1, its site keeps its resource, and
  it first harvests in the next step; an empty site does not harvest and regrows.
- Two-step forced vacancy and refill: a site emptied in one step regrows, and its next occupant harvests from the
  regrown stock; `W` (`last_W`) equals R3d's exactly at `γ` = 1 also on a lattice with vacancies.
- Runner: activation pooled over occupant-steps, at exactly 0.19 counted active, an empty window ignored, and the
  attempt-2 test arm used in attempt 2.
- Steady state: a single site kept occupied with `γ` < 0.2 settles at harvest `γ` and `G` = `5γ`.
- `W = G + 0.5·S − D` is used for eligibility, starvation and the lottery (forced cases with unequal `G`).
- With B = C = 0, `c_b` = 0, `θ` = `σ` = −infinity, `γ` = 1 and local settlement, the model reproduces K-null
  exactly.

**Decision.**

- **Met (either attempt):** at these settings, care for own young met the joint endpoint with income from a
  renewable site resource, on top of R3d, and beat help to young neighbours in joint successes (with the activation
  label above, which measures exposure to limitation, not its effect). Whether vacant space arose is reported separately (lean arms included). What comes next (care that
  transfers income, foraging movement, or a PPG port) is decided with the user.
- **Neither met:** recorded with its classification; the next, smaller step is decided with the user.
- Exploratory: two attempts, one test level.

**Predictions (mine, before any data).**

- Attempt 1 met: about 30%. Limited income lowers long-lived occupants' condition, and by the screen it penalizes
  high helping (starvation above about `h` = 0.75 without care received, ineligibility above about 0.5), while
  R3d's F6-local ended at 0.65.
- Income limitation active in G6-local: about 90%.
- GN6-local <= 3/20: about 85%.
- G6-global >= 15/20 (H2): about 40%.
- Attempt 2 met, given attempt 1 is not: about 50%.
- Fills left empty below 1% in the `γ` = 0.15 arms: about 70%; above 5% in at least one lean arm: about 50%.

**Budget.** 200 runs, about 25 minutes on 8 cores; attempt 2 (160 runs) about 20. The pre-registration and code get a
Codex review (gpt-6.2-sol, medium) before running; wording (gpt-reserve, medium) before commit.

**Limits.**

- `γ` is a design choice (0.15, then 0.18; lean 0.08); the harvest cap 0.2 is fixed by the old baseline.
- Newborns get a free endowment `G` = 1, not taken from the parent; care is still a free benefit, not a transfer of
  income. Both are candidate later steps.
- Occupants harvest only their own site and cannot move; there is no foraging.
- The screen uses steady states, so it is approximate.

## Diagnostic DR4: why did helping rise under limited income? (pre-registration 2026-11-20, after R4; no DR4 data; revised per Codex review)

**Why.** In R4 (`γ` = 0.15), care for own young ended higher than in R3d (descriptive, separate unpaired batches):
final mean `h` 0.90 in G6-local against 0.65 in R3d's F6-local, and 0.96 against 0.86 without local settlement. My
screen predicted the opposite direction. Before adding more ingredients, this diagnostic asks which part of R4
could account for the rise. It adds no new model ingredient and makes no claim about kin selection.

**What R4 changed (three candidate parts).** R4 replaced the free baseline 1 in `W` by an earned store `G`. Relative
to R3d, this introduced three candidate pathways that could contribute to the difference:

1. **A uniform cut in condition.** Occupied sites were harvested to the regrowth level (resource 0.150 before the
   harvest on occupied sites, capped in more than 99% of occupant-steps), so income was nearly the same on every
   site, so a largely uniform cut is plausible. The lottery is a softmax, which ignores a shift that is the same for
   everyone in a pool, so a uniform cut acts only through the absolute cutoffs: lowering everyone's `W` by `x` is the
   same as raising `θ` and `σ` by `x`. Ineligibility and starvation were much higher (G6-local 31% ineligible and
   recent parents starving at 9.6% per step, against 4% and 2.1% in the separate F6-local batch).
2. **A free endowment and an age gradient in condition.** Newborns start with `G` = 1, and long-lived occupants'
   stores decay toward `G*` = 0.75; in G6-local, `G` at payoff was 0.93 for juveniles and 0.82 for parents with
   living offspring, an age-related condition difference that R3d did not have; `G` differences
   (by age, and by site history) also change the softmax odds, not only the cutoffs.
3. **Site differences in resource.** Unresolved: the mean stock on occupied sites was 0.150, at the regrowth level,
   but a mean does not measure site-to-site variation, and the capped fraction (`r` < 0.2) cannot rule out variation among capped sites, so this is not excluded; no
   arm of its own (D-E against D-U75 bears on it, below).

A fourth possibility is an interaction with the birth cost (`c_b` = 0.5): with a lower margin, a birth pushes the
parent below the cutoffs more often, which could fall hardest on occupants that breed often and care little. The
birth-cost arms test only whether the rise needs birth costs; they cannot show who was penalized.

**Arms (seeds 0-19, 6000 steps, b/c 6 (B = 1.2), local settlement, rare start, otherwise R3d / R4 attempt 1).**

| Arm | Model | Change | Isolates |
| --- | --- | --- | --- |
| D-F | R3d (F6-local) | none | reference, same batch |
| D-G | R4 (G6-local, `γ` = 0.15) | none | reference, same batch |
| D-U85 | R3d | constant baseline 0.85 instead of 1 (G6-local's mean `G` at payoff, 0.845, chosen after seeing R4) | uniform cut, matched to the observed mean |
| D-U75 | R3d | constant baseline 0.75 (= `G*` = 5`γ`) | uniform cut, steady-state level |
| D-E | R4 | founders and newborns start with `G` = 0.75 instead of 1 | lower endowment (removes most of the age gradient) |
| D-Fcb0 | R3d | `c_b` = 0 | pair with D-Gcb0 |
| D-Gcb0 | R4 | `c_b` = 0 | rise without birth costs |

Seven arms, 140 runs. The constant baseline is the existing `base_fitness` entry, which in these engines enters the
dynamics only through `W` (it also changes the recorded mean fitness). D-E needs one new engine option (initial and
newborn `G`), with default 1 (R4 unchanged). D-E lowers the endowment, which also lowers mean condition; and since
founders start on full stock (first store 0.8·0.75 + 0.2 = 0.80) and refilled sites can give extra harvest, it does
not remove every age difference. `s_E` is therefore read as "the rise kept with a lower endowment"; D-E against D-U75
(descriptive) compares R4's resource dynamics with a constant baseline at a similar level.

**Measures.** `h̄(X)`: mean over the 20 seeds of final mean `h` over occupied sites in arm X. The rise is
`Δ = h̄(D-G) − h̄(D-F)`. Shares of the rise:

- uniform cut: `s_U85 = (h̄(D-U85) − h̄(D-F)) / Δ`, `s_U75` likewise;
- age gradient: `s_E = (h̄(D-E) − h̄(D-F)) / Δ` (the rise kept without the gradient);
- birth cost: `s_cb0 = (h̄(D-Gcb0) − h̄(D-Fcb0)) / Δ` (the rise kept without birth costs).

An extinct run (no occupied site) counts as final `h` = 0. The shares are reported as point estimates. **The
decisions use the difference `d_X = (numerator of s_X) − 0.5·Δ`** (for example `d_U85 = h̄(D-U85) − h̄(D-F) − 0.5·Δ`),
with a 95% percentile bootstrap interval: 10,000 resamples of the 20 seeds as whole blocks (the same resampled seeds
in every arm, since the arms share seed ids and random streams; the stored F6/G6 endpoints have a seed-matched
correlation of 0.42), the same draw used for numerator and `Δ`, generator seed 0.

**Reading (mechanical).**

- **Validity:** the reference arms D-F and D-G must reproduce `final_mean_trait`, `final_occupancy` and
  `traj_every_50` of F6-local in `r3d_runs.csv` and G6-local in `r4_runs.csv` exactly, per seed; and `Δ` >= 0.10
  (stored: 0.247). Otherwise the diagnostic is void.
- For each `d_X`: interval entirely above 0: **"accounts for most of the rise"** (`s_X` > 0.5); entirely below 0:
  **"accounts for less than half"**; otherwise **"unclear"**. For D-E and the birth-cost pair the reading is about what is
  kept: "accounts for most" means the removed part is not needed for most of the rise ("not needed"); "accounts for less than
  half" means it is ("needed").
- Shares need not add up: the parts can interact.
- **Overall:** if every `d_X` is "unclear", the diagnostic is **inconclusive**. If none is unclear and neither
  uniform cut accounts for most, and neither a lower endowment nor the absence of birth costs removes most of the rise,
  the rise is recorded as **unexplained by these parts**. Otherwise the parts with clear readings are listed.

**Descriptive.** Mean `h` at steps 2000, 4000 and 6000 (R4's test arm was still rising at 6000); births per occupant
per step for `h` < 0.5 and `h` >= 0.5 (new diagnostic: realized births by parent, counted from the lottery's parents
of filled sites before the survivor filter, so births by parents that died in the same step count; over start-of-step
occupants of each class); ineligibility and starvation rates by `h` class and for recent parents; mean `G`, `S`, `D`; final `h`
spread (sd) per arm.

**Checks (deterministic tests, before running).** The constant baseline enters the dynamics through `W` only (a
shift test on a fixed state: with `θ` and `σ` raised by the same amount, the lottery probabilities agree within
1e-12, and eligibility and starvation agree on states kept away from the cutoffs; exactly at a cutoff, floating
point can flip a decision, which is allowed); D-E with `G` start 1 is R4 exactly; the births-by-class diagnostic on a forced case; the reference reruns reproduce
`r3d_runs.csv` and `r4_runs.csv` (final `h`, final occupancy) for F6-local and G6-local.

**Predictions (mine, before any data).**

- `s_U85` "accounts for most": about 35%; `s_U75`: about 45%.
- D-E "accounts for less than half" (the free endowment needed): about 30%.
- Birth-cost pair "accounts for less than half" (birth costs needed): about 40%.
- Unexplained by these parts: about 20%; inconclusive: about 15%.

**Decision.** Recorded either way; no follow-up diagnostic without agreement with the user. It does not change R4's
verdict. Its result informs how R5 is read (below), but does not block R5.

**Budget.** 140 runs, about 20 minutes on 8 cores. Code gets a Codex review (gpt-6.2-sol, medium) before running.

**Limits.** One b/c level, local settlement only (the rise also appeared without local settlement); final `h` at
6000 steps may not be an equilibrium; the 0.85 baseline was chosen after seeing R4. The arms remove parts; they do
not separate the eligibility pathway from the starvation pathway, or cutoff effects from changed softmax odds.

**Amendment before running (2026-11-20, after the Codex code review, no DR4 data).** (1) Per-seed `traj_every_50`
was never stored for R3d or R4 (the CSVs keep only scalars; the verdicts keep the across-seed mean). The validity
check therefore compares per seed `final_mean_trait` and `final_occupancy` exactly, and the across-seed mean
trajectory exactly against the stored `mean_h_every_50`; DR4 stores per-seed trajectories
(`dr4_trajectories.json`). (2) The rise check is inclusive with a float tolerance (`Δ` >= 0.10 − 1e-12), and two
undefined values (a reproduced extinct run) count as a match. (3) Descriptive conventions: births by `h` class are
pooled counts over the diagnostic window (payoff steps 1000-5999, as all other rates), divided by start-of-step
occupant-steps of the class; extinct runs count as `h` = 0 in the step-2000 and step-4000 means too. None of these
changes the arms, the decision measures or the readings.

## Step R5: foraging over the neighbourhood (R5a), then movement into empty sites (R5b) (pre-registration 2026-11-20, after R4; no R5 data; revised per Codex review)

**Why this step.** In R4 each occupant eats only from its own site, so food per occupant does not depend on how
many neighbours there are, and occupants cannot move. In PredPreyGrass-like ecologies, animals forage over an area
shared with their neighbours and move toward food. R5 adds these two ingredients, one per rung: **R5a** shares
food among neighbours; **R5b** adds movement into empty sites. Base: R4 attempt 1 (`γ` = 0.15).

**R5a ingredient: foraging over the von Neumann neighbourhood.**

- Each start-of-step occupant `i` forages the five sites of its neighbourhood `N(i)` (its own site and its four
  grid neighbours; foraging is spatial in every arm, also those with global settlement). Its demand per step is
  still 0.2 in total, spread as 0.2·`w_is` over the sites (attempt 1: `w` = 1/5 for each site).
- Each site `s` splits its stock proportionally among the occupants foraging it: with total demand
  `Q_s = Σ_j 0.2·w_js` over its foragers, each forager gets the fraction `a_s = min(1, r_s / Q_s)` of its demand,
  so `g_i = 0.2 · Σ_{s ∈ N(i)} w_is · a_s`, and the site loses `min(r_s, Q_s)`. A site with no foragers
  (`Q_s` = 0) is skipped. If every `a_s` in `N(i)` is 1, `g_i` is set to the literal 0.2 (a sum of five 0.04 terms
  is not exactly 0.2 in floating point). An empty site is foraged by its occupied neighbours.
- Everything else as R4: `G ← ρG + g`, timing, `G` = 1 for newborns, regrowth `r ← r + γ(1 − r)` from the
  post-harvest stock on every site, no random draws added.
- **Reductions (to be checked by tests).** At `γ` = 1 every stock is 1 at the start of each step, so `a_s` = 1 and
  `g_i` = 0.2 for every forager, vacancies included: R5a is meant to be R3d exactly (a test checks it, random streams
  included). On a fully occupied lattice with the same stock on every site, `g_i` equals R4's `min(r, 0.2)`. Foraging
  is therefore expected to differ from R4 mainly near empty sites, and where stocks differ between neighbouring
  sites.

**R5b ingredient: movement into an empty neighbouring site (on top of R5a).** A movement phase after deaths, births,
birth charges and newborn `G` initialization, and before regrowth, simultaneous for all occupants:

- The empty sites (after this step's fills) and the post-harvest stocks are frozen at the start of the phase.
- Every surviving occupant (not this step's newborns) with an empty site among its four grid neighbours targets the
  one with the most resource (ties: lowest site index), and claims it if that resource exceeds its own site's by more
  than `m` (attempt 1: `m` = 0; an equal resource is no move).
- A site claimed by several occupants goes to the claimant with the higher `W` at payoff time (at its source site);
  ties: lowest source index. Losers stay. All moves are then made together; a site vacated in this phase cannot be
  entered before the next step.
- A mover carries everything (`h`, lineage, id, parent id, age, `S`, `D`, `Db`, `G`, the birth-charge flag). Its
  source site gets the empty-site convention of R3c (and `G` = 1); the resource stays with the site.
- Movement always uses the fixed grid adjacency, also in the global-settlement arms (where the lottery's random
  candidate pools are separate). Own-young care is routed by id (`parent_sites()` is rebuilt every step), so it
  follows a mover; young-neighbour care (control) follows the updated grid.
- The completed step's diagnostics (`last_survivors`, `last_W`, `last_harvest`, starvation and death counts) stay
  indexed by the sites before the movement phase. No random draws added. With no empty sites the phase does nothing,
  so R5b is R5a exactly; at `γ` = 1 moves are still possible when vacancies and unequal stocks exist, so R5b is not
  R3d there.

**Screen (before any data; arithmetic checked by Codex).** R4 left almost no empty sites: window occupancy 0.9989 in
the test arm and 0.9980 in the lean arm, and fills left empty at most 1.4%. A site has fewer than five foragers only
next to a vacancy, so only occupants within two grid steps of a vacancy (12 occupied sites around each vacant centre)
can get a different harvest from R4's: an upper bound of about 1.3% (test arm) and 2.4% (lean arm) of occupant-steps,
before overlaps and before the 0.01 materiality cutoff. With one isolated vacancy on otherwise uniform stock, 8
occupants clear that cutoff at `γ` = 0.15 and none at `γ` = 0.08 (stock differences left by earlier vacancies can add
more). Movement can only go into empty sites: at most the post-fill vacancies per start-of-step occupant, about 0.1-0.2%
of occupant-steps. **At R4's occupancy, both ingredients are expected to be nearly inert.** Because this screen suggests both may have little
exposure, each rung starts with a cheap exposure pilot with a pre-set kill rule.

**Exposure pilots (before each rung's main run).** Seeds 0 and 1 of the rung's test arm (b/c 6 local, `γ` = 0.15)
and lean arm (b/c 6 local, `γ` = 0.08), 6000 steps, payoff states after 1000-5999 updates, pooled over both seeds.

- **R5a exposure:** the fraction of occupant-steps in which `g_i` differs by more than 0.01 (5% of the full
  harvest) from R4's own-site rule `min(r_i, 0.2)` evaluated in the same state.
- **R5b exposure:** moves per occupant-step (move opportunities, occupants with an empty neighbour, also reported).
- **Kill rule:** if exposure is strictly below 2% (R5a) or strictly below 0.5% (R5b) in both pilot arms, the rung's
  main run is not done; exposure exactly at the bar passes. The rung is recorded as "below the pilot exposure
  threshold", with the pilot numbers. A pilot arm with no occupant-steps in the window is void (not zero exposure),
  and a pilot with a void arm is decided with the user. The pilot measures a one-step difference on the same state;
  cumulative effects and their concentration in juveniles or breeders are not covered by it.
- The R5b pilot runs even if R5a is below its threshold (exposure there is a different quantity), built on R5a's
  attempt-1 weights.

**Main run (each rung, only if its pilot passes).** Arms as in R4, with prefix `A` (R5a) or `M` (R5b): A6-local
(test), AN6-local (control), A-below, A3/A12/A24-local, A6-global (H2), A12-global, A6-local-lean and A6-global-lean
(`γ` = 0.08, descriptive); 10 arms, 200 runs per rung. **Classification, H2 and activation as in R4** (joint
endpoint: final mean `h` >= 0.60 and final occupancy >= 0.5; local failure if the test arm < 15/20 or below-control
maintained in > 2/20; comparison failed if the lead < 8 or Fisher p >= 0.025; H2 >= 15/20 with neighbour
correlation <= 0.10). The rung's exposure (as in the pilot, over all 20 seeds of the test arm) is reported with the
verdict, as a label like R4's activation, not a gate.

**Attempt 2 (fixed now; only if attempt 1 is local failure or comparison failed).** A smaller step toward R4. R5a:
half of the demand on the own site (`w` = 1/2 own, 1/8 each neighbour). R5b: only `m` changes, to 0.05 (move only for
a gain of more than 0.05). Prefixes `A2-` / `M2-`, no lean arms, same classification. Attempt 2 runs without a pilot
of its own (the rung's pilot already passed).

**What R5b builds on.** R5b uses the R5a weights of the attempt that met (attempt 1: `w` = 1/5; attempt 2: 1/2 own,
1/8 each neighbour). If R5a's pilot was below threshold, R5b uses attempt-1 weights. If R5a's main run met in neither
attempt, R5b is not run, and the next step is decided with the user.

**Descriptive (both rungs).** As in R4, plus: occupancy and fills emptied (are there more empty sites?), mean
harvest near and away from empty sites, the R5a exposure; for R5b: moves per occupant-step, mean distance moved
from the birth site, the fraction of moves made by juveniles, and neighbour `h` correlation (does movement weaken
the local kin structure?).

**Checks (deterministic tests, before running).**

- R5a at `γ` = 1 is R3d exactly (`h`, label, ids, parent ids, age, `S`, `D`, `G`, occupancy, `last_W`, all generator
  states), also with forced vacancies and refills; R5b with no empty sites is R5a exactly.
- R5a harvest on forced states: a uniform full lattice gives `min(r, 0.2)`; a site with an empty neighbour; two
  foragers on a short stock split it proportionally; stocks never go below 0; attempt-2 weights.
- R5b on forced states: a move into the richer empty neighbour; no move at equal resource (`m` = 0) or below the
  margin; a conflict won by the higher `W`, a tie by the lower index; losers stay; everything carried (including a
  moved recent parent's birth-charge flag and its `G`, not reset at the destination), the vacated site empty and not
  entered in the same phase; a same-step fill next to a vacancy and a move; care received by a moved juvenile from
  its parent; newborns do not move; a global-settlement arm (movement on the grid, lottery pools random); the
  completed step's diagnostics indexed by the original sites.
- Pilot and runner: exposure pooled over occupant-steps; the kill rule on forced numbers (both arms below, one
  above).

**Decision.**

- **Pilot inert:** recorded; the next step is decided with the user. Possible candidates are ingredients that could
  produce empty space first, such as a newborn endowment paid by the parent.
- **Met (either attempt):** at these settings, care for own young met the joint endpoint with neighbourhood foraging
  (and, for R5b, movement), on top of R4, and beat help to young neighbours.
- **Neither met:** recorded with its classification; the next, smaller step is decided with the user.
- Order: DR4 first, then R5a's pilot, then (if it passes) R5a's main run, then R5b's pilot and main run. Two
  attempts per rung, one test level.

**Predictions (mine, before any data).**

- R5a pilot inert: about 75%. R5b pilot inert: about 80%.
- If a main run is done: met in attempt 1, about 65% (R5a) and 60% (R5b).
- If R5b runs: neighbour `h` correlation in the test arm lower than in R4's (0.53): about 60%.

**Budget.** Pilots: 4 runs per rung, a few minutes. Main runs: 200 runs per rung, about 25 minutes each; attempt 2
about 20 minutes each. The pre-registration and code get a Codex review (gpt-6.2-sol, medium); wording (gpt-reserve,
medium) before commit.

**Limits.**

- Foraging range and movement range are both one grid step; demand stays at the R4 cap of 0.2.
- Movement is only into empty sites, which are rare in R4; no swapping or crowding.
- Newborns still get a free endowment `G` = 1, which likely keeps the lattice full; this is why the pilots exist.

**R5a pre-pilot note (2026-11-20, after the Codex code review, no R5 data).** The exposure cutoff "more than 0.01"
is computed with a float tolerance (difference > 0.01 + 1e-12), so a difference of exactly 0.01 that rounds to
0.0100...09 does not count. The pilot's exposure is pooled counts over occupant-steps (per seed and per arm);
the per-step mean `frac_exposed` is a diagnostic only. R5b is not built yet; it is built after the R5a pilot.

**R5b not run (user decision 2026-11-20, after the R5a pilot).** The pre-registration said R5b's pilot runs even if
R5a's is below its threshold. It was skipped: a move needs an empty grid neighbour, and in the R5a pilot window
occupancy stayed at least 0.998 (fills emptied 0.8-1.1%). Each empty site can receive at most one mover per step
(a conflict has one winner), so moves per occupant-step are bounded by the empty sites,
about 0.10-0.20% (at most 0.12-0.22% allowing for the one-step shift between pre-fill and post-fill vacancies),
below R5b's 0.5% bar. That bound holds for the observed R5a states; movement could change later vacancies, so it is
not established for an R5b trajectory. R5b is recorded as "not run: user decision, low expected exposure". It can be
revisited once a preceding step produces enough vacant space to make the 0.5% movement bar plausible.

## Step R6: the newborn's endowment is paid by its parent (pre-registration 2026-11-20, after DR4 and R5a; no R6 data)

**Why this step.** From R4 on, a newborn starts with an income store `G` that comes from nowhere (1 in R4). Energy
is therefore created at every birth, which plausibly helps keep the lattice full (R4, DR4 and R5a: occupancy at
least 0.996, fills left empty at most 1.4%), and vacant space is still untested. In PredPreyGrass-like ecologies, a
newborn's energy comes from its parent. R6 makes the parent pay for the endowment.

**Base: DR4's D-E configuration** (R4 attempt 1, `γ` = 0.15, with founders and newborns starting at `G` = 0.75
instead of 1). It was run as a DR4 arm (18/20, final `h` 0.90), not as a pre-registered rung; the level 0.75 (=
`G*` = 5`γ`) was chosen after seeing R4 and DR4. It is used so that the endowment the parent pays is the long-run
store level, not the larger free 1. Everything else as R4: stores `S`, `D`, `G` (`ρ` = 0.8), harvest `min(r, 0.2)`
from the own site, regrowth `r ← r + γ(1 − r)`, `W = G + 0.5·S − D`, birth cost `c_b` = 0.5 to `D`, eligibility `W >=
θ` (0.25), starvation `W < σ` (0), softmax lottery (`T` = 0.12), care `B·h` to living juvenile offspring (age < 2) at
cost `C·h` (`C` = 0.2), base death `0.5·exp(−0.5·S/T)`; 6000 steps; success needs final mean `h` over occupied
sites >= 0.60 and final occupancy >= 0.5.

**Ingredient: the parent pays a fraction `q` of the newborn's endowment `E` = 0.75 from its own store.**

- The newborn still starts with `G = E = 0.75`.
- Each parent that survives the step pays `q·E` per realized birth from its `G`, at the same point as the birth cost
  (after births are settled; `G_p ← G_p − k·q·E` for `k` births). It enters the next step's `W` through
  `G ← ρG + g`. `G` may become negative (an overdraft; recorded).
- As with the birth cost, a parent that died in the same step pays nothing (its stores are discarded), so a birth by
  a dying parent is still partly free; the share of such births is recorded (R4 test arm: 10%).
- **In this model the payment is dynamically the same as a higher birth cost.** Since `G` and `D` both decay at `ρ`
  and enter `W` linearly, paying `q·E` from `G` gives the same `W`, and so the same dynamics, as `c_b` = 0.5 + `q·E`
  in `D` (in exact arithmetic; a test checks this; a dying parent pays neither). What is new is the bookkeeping: the
  paid part `q·E` is transferred from parent to newborn; the unpaid part `(1 − q)·E` (all of `E` for a dying parent)
  is still newly created, and overdrafts let a parent pay more than it holds. No random draws are added; `q` = 0 is D-E exactly.
- Levels: `q` = 1 (the parent pays the whole endowment; effective birth cost 1.25) and `q` = 0.5 (half; 0.875).

**Screen (before any data).** Recent parents in R4's test arm had `W` of roughly 0.82 + 0.5·0.63 − 0.875 ≈ 0.27 at
payoff (means of `G` and `S` over occupants with living offspring and of `D` over recent parents; the means of
different groups do not combine exactly). D-E's parent stores were 0.75, so somewhat lower. The extra payment lowers
the next payoff's `W` by `ρ·k·q·E`: 0.6 at `q` = 1 and 0.3 at `q` = 0.5 per birth. A charged survivor starves at its
next payoff if its otherwise identical `W` there is below `ρ·k·q·E`; on these averages that would often be the case
at both levels, but no matched distribution of recent parents' `W` is available, so this is a one-step sensitivity,
not a starvation frequency. Two consequences are plausible, and their sizes are not predictable from this screen:

1. **Care could collapse.** Care goes from a living parent to its young (age < 2). A parent that starves the step
   after a birth still gives care in that step (it is a start-of-step occupant), but not afterwards.
2. **Vacancies may still stay rare.** A site stays empty only if no occupant of its pool is eligible (`W >= θ`).
   Juveniles start at `G` = 0.75 and cared juveniles have high `W` (R4: `S` 0.96 for juveniles), so pools that
   contain juveniles will usually fill. The ingredient lowers the parents' condition, not the newborns'.

Because of this, R6 starts with a pilot that checks for vacant space and viability before the main run.

**Pilot (before the main run).** Seeds 0 and 1 of the test arm (b/c 6, local settlement), at `q` = 1 and
`q` = 0.5 (4 runs), 6000 steps; measures over payoff states after 1000-5999 updates, pooled over both seeds.

- **Counts.** Window occupancy = occupied site-steps / all site-steps; fill failure = sites left empty / sites that
  needed a fill (an occupant died, or the site was already empty), both pooled over the window and both seeds.
- **Viable:** no extinction and final occupancy >= 0.5 in both seeds (an extinct run is not viable).
- **Vacant space:** fill failure >= 5%, or window occupancy <= 0.97 (inclusive). With no fills needed, fill failure
  is undefined and occupancy decides.
- **Choice of the main-run level:** `q` = 1 if it is viable with vacant space; else `q` = 0.5 if that is; else the
  main run is not done. Each level's outcome is recorded with its reason ("not viable", "vacant space rare", or
  "passed"), and the next step is decided with the user. A missing, duplicated or failed pilot run makes the pilot
  incomplete: no level is chosen, and it is rerun or decided with the user.
- **No peeking at `h`:** the runner computes and writes the chosen level before any `h` is reported; final `h` is
  written afterwards, for the record only. Seeds 0 and 1 recur in the main run, and viability and vacancies can
  depend on care, so the main run is a pilot-selected result; this is reported with it.
- The pilot does not test whether care spreads; the main run does.

**Main run (only if the pilot passes).** Arms as in R4 with prefix `T`, at the chosen `q`: T6-local (test),
TN6-local (control: help to young neighbours), T-below (b/c 0.25, common start), T3/T12/T24-local, T6-global (H2),
T12-global, T6-local-lean and T6-global-lean (`γ` = 0.08, with `E` = 0.75, as above; descriptive); 10 arms, 200
runs, seeds 0-19 (the full seed roster of every arm is checked before classifying). **Classification, H2 and
activation as in R4**, in this order: local failure if the test arm is below 15/20 or T-below maintained in more
than 2/20; else comparison failed if the lead over TN6-local is below 8 or the one-sided Fisher p >= 0.025; else met.
H2: >= 15/20 with mean neighbour correlation <= 0.10; an undefined correlation makes H2 "not interpretable".
**Vacancy label (not a gate):** both vacancy measures of the test arm are reported (counts as in the pilot); fill
failure >= 5% or window occupancy <= 0.97 gives "vacant space present", otherwise "vacant space rare". "Met" refers
to the care comparison only. The number of test-arm seeds that are both successes and individually show vacant space
is reported, so a claim of care spreading *with* vacancies can be read per seed. H2, income activation and the
vacancy label are reported separately and never trigger attempt 2.

**Attempt 2 (fixed now; only if attempt 1 is local failure or comparison failed).** A smaller step toward D-E:
half of attempt 1's `q` (0.5 if attempt 1 used 1; 0.25 if it used 0.5). Everything else as attempt 1: `γ` = 0.15
(not R4's attempt-2 0.18), `E` = 0.75, seeds 0-19, the eight non-lean arms with prefix `T2-`, no pilot of its own,
same classification.

**Descriptive.** As in R4, plus: occupancy and fills left empty; the fraction of recent parents in overdraft
(`G` < 0) and starving; births by parents that died in the same step (and the net `G` added per birth); births by `h` class (as in DR4); mean age;
`G`, `S`, `D` for juveniles and parents.

**Checks (deterministic tests, before running).** `q` = 0 is D-E exactly (all state and random streams); a `q` arm
gives the same `h`, occupancy, `last_W` (within 1e-12) and random streams as D-E with `c_b` = 0.5 + `q·E` on a seed
where no decision lies at a cutoff or a lottery boundary (rounding can flip a starvation or eligibility decision at
its cutoff, or a lottery winner at a cumulative-probability boundary; such a flip is allowed, not a failure); on a forced case, a surviving parent with `k` births pays `k·q·E` from `G`,
a dying parent pays nothing, the newborn starts at 0.75, and `G` can go negative; the pilot decision rule on forced
numbers (viable with vacancies, viable without, not viable, both levels).

**Decision.**

- **Pilot fails:** recorded; the next step is decided with the user (for example a lower endowment, or juveniles
  that cannot breed).
- **Met (either attempt):** at these settings, care for own young met the joint endpoint with a parent-paid
  endowment, on top of D-E, and beat help to young neighbours; whether space was vacant is reported with it.
- **Neither met:** recorded with its classification; the next step is decided with the user.

**Predictions (mine, before any data).**

- `q` = 1 viable: about 70%. Vacant space at `q` = 1: about 35%; at `q` = 0.5: about 20%.
- Pilot passes at some level: about 40%.
- If the main run is done: met in attempt 1, about 40% (care may collapse because parents starve after a birth).

**Budget.** Pilot: 4 runs, a few minutes. Main run: 200 runs, about 25 minutes; attempt 2 about 20 minutes. The
pre-registration and the code get a Codex review (gpt-6.2-sol, medium), wording (gpt-reserve, medium) before commit.

**Limits.** One endowment level (`E` = 0.75, chosen after DR4); dynamically this step is a higher birth cost; juveniles
can still breed, which may keep pools eligible; the pilot looks at two seeds only.

## Step R7: juveniles cannot breed (pre-registration 2026-11-20, after the R6 pilot; no R7 data; revised per Codex review)

**Why this step.** R4, R5a and R6 all left the lattice almost full (fills left empty at most about 2%), so vacant
space has not yet occurred at the levels needed to assess neighbourhood foraging and movement (R5). One candidate
reason: juveniles (age < 2) start with a sizeable store, receive care, and can win a birth from their first payoff
on, which could help explain why replacement pools usually contain an eligible candidate. In D-E, juveniles were 26% of occupants with `W` of
roughly 0.75 + 0.5·0.98 − 0.28 ≈ 0.96 at payoff (means over juveniles; `θ` = 0.25), so most of them were plausibly
eligible (juvenile ineligibility was not measured; starving juveniles, 0.4% per step, are ineligible, so this gives
only a lower bound), while about 35% of all occupants were ineligible. R7 adds the usual age-structure assumption that
young animals mature before they reproduce, as in PredPreyGrass-like ecologies.

**Base: DR4's D-E configuration**, as in R6 (R4 attempt 1, `γ` = 0.15, founders and newborns at `G` = 0.75; DR4
arm, 18/20, final `h` 0.90). R6 did not reach its main run, so its payment is not part of the base. Everything else
as R4 (see R6's base paragraph).

**Ingredient: an occupant can win a birth only from age `a_b` on.** The eligibility mask becomes
`occupied & (W >= θ) & (start-of-step age >= a_b)`; payoff ages are the start-of-step ages (survivors age by 1 and
filled sites reset to 0 only after the lottery). Founders and newborns start at age 0, so founders cannot breed in
the first `a_b` updates. As before, an eligible occupant that dies by its ordinary death draw can still parent that
step, and a starving one fails `W >= θ`. A site that needs a fill and whose pool holds no eligible candidate stays
empty, as in R3c. Juveniles still receive care, harvest, pay costs, can starve and die as before. No random draws
are added: the per-site lottery draw (discarded for an all-ineligible pool, as in R3c), inheritance and mutation,
death and, under global settlement, candidate draws are all kept; `a_b` = 0 reproduces each matched income arm (with
`G` start 0.75) exactly, D-E being the local test-arm reference. Levels: `a_b` = 2 (the care-juvenile period: juveniles cannot breed) and `a_b` = 1 (only age-0 occupants
cannot breed).

**Screen (before any data; a frozen-state toy calculation).** Assume (not measured) that almost no juvenile was
ineligible in D-E. Under that assumption the 35% ineligible would be adults, about 47% of adults (0.35 / 0.74), and
barring juveniles
leaves about 0.74 × 0.53 ≈ 0.39 of occupants eligible, against about 0.65 in D-E. If the five candidates of a pool
were independent draws at these rates, a pool would have no eligible candidate with probability about 0.35^5 ≈ 0.5%
in D-E and about 0.61^5 ≈ 8% after the `a_b` = 2 bar. The observed D-E fill failure (1.4%) is not comparable with the
0.5%: it is conditional on a site needing a fill, the pool includes the focal site (a starving occupant is both
ineligible and in need of a fill), and existing vacancies and variation across steps and seeds also enter. For
`a_b` = 1: newborns are the next step's age-0 occupants, and births were about 13% of occupant-steps in D-E, about
half the juvenile share; the same toy calculation gives about 2.7% (about a quarter of the age-2 increase). Feedbacks
can move the real rates either way: fewer early births make the population older (more adults), and already-empty
sites need a fill again every step. On this toy calculation, vacancies above the 5% bar are plausible at `a_b` = 2 but
not certain, and less likely at `a_b` = 1. The rule does not remove care from existing juveniles, but it may change
care indirectly by altering births and the age composition; young occupants lose their first `a_b` steps of
breeding, which could lower the fitness of all strategies alike.

**Pilot (before the main run).** As in R6, with `a_b` in place of `q`: seeds 0 and 1 of the test arm (b/c 6, local
settlement) at `a_b` = 2 and `a_b` = 1 (4 runs), 6000 steps, payoff states after 1000-5999 updates, pooled over both
seeds.

- **Counts:** window occupancy = occupied site-steps / all site-steps (start of step); fill failure = sites left
  empty / sites that needed a fill (an occupant died, or the site was already empty).
- **Viable:** no extinction and final occupancy >= 0.5 in both seeds.
- **Vacant space:** fill failure >= 5%, or window occupancy <= 0.97 (inclusive); with no fills needed, occupancy
  decides.
- **Level choice:** `a_b` = 2 if viable with vacant space; otherwise `a_b` = 1 if that level is viable with vacant
  space; otherwise the main run is not done.
  Each level's outcome is recorded with its reason ("not viable", "vacant space rare", "passed"); the next step is
  then decided with the user. A missing, duplicated or failed run (or a wrong level set) makes the pilot incomplete:
  no level is chosen. "Complete" means exactly one finished result for each of the four (level, seed) jobs and no
  other rows; a finished run that went extinct is a valid result ("not viable"), an execution failure is not. The
  runner reads only these pilot counts before it writes the choice, writes the choice before any `h` is reported,
  and a failed run leaves an "incomplete" selection, never an earlier one. Final `h` is recorded afterwards, for the record only. Seeds 0 and 1
  recur in the main run, so the main run is a pilot-selected result; this is reported with it.

**Main run (only if the pilot passes).** Arms as in R4 with prefix `J`, at the chosen `a_b`: J6-local (test),
JN6-local (control: help to young neighbours), J-below (b/c 0.25, common start), J3/J12/J24-local, J6-global (H2),
J12-global, J6-local-lean and J6-global-lean (`γ` = 0.08, `G` start 0.75; descriptive); 10 arms, 200 runs, seeds
0-19. The attempt is classified only if every arm has exactly one finished run for each seed; an incomplete attempt
gets no classification and cannot trigger attempt 2 (it is rerun or decided with the user). **Joint endpoint (per
run):** final mean `h` over occupied sites >= 0.60 and final occupancy >= 0.50; both components are recorded per seed,
so high `h` among few remaining occupants cannot hide an occupancy loss. **Classification as in R4, in this order:** local
failure if the test arm is below 15/20 or J-below (rare-helping start reversed: common start at b/c 0.25) still
meets the joint endpoint in more than 2/20; else comparison failed if the lead
over JN6-local is below 8 or the one-sided Fisher p >= 0.025; else met. **H2:** J6-global; if any neighbour
correlation sample is undefined or the mean correlation is above 0.10, H2 is "not interpretable"; otherwise met if
>= 15/20. **Income activation (label):** pooled test-arm harvest per occupant-step <= 0.19 (with the 1e-12
tolerance). **Vacancy label (not a gate):** pooled counts (as in the pilot) over the window of the test arm's
non-extinct seeds; fill failure >= 5% or occupancy <= 0.97 gives "vacant space present", otherwise "vacant space
rare"; extinct seeds are reported separately. Per seed, both vacancy measures are reported, and the number of test
seeds that are successes and individually show vacant space. "Met" refers to the care comparison only. H2, income
activation and the vacancy label never trigger attempt 2.

**Attempt 2 (fixed now; only if attempt 1 is local failure or comparison failed, and only if attempt 1 used `a_b` =
2).** A smaller step toward D-E: `a_b` = 1, run even if `a_b` = 1 failed its pilot (the pilot chooses the attempt-1
level only; it is not a veto on attempt 2). Everything else as attempt 1 (`γ` = 0.15, `G` start 0.75, seeds 0-19),
the eight non-lean arms with prefix `J2-`, no pilot of its own, same classification. If attempt 1 used `a_b` = 1,
there is no attempt 2.

**Descriptive.** As in R4 and DR4, plus: occupancy and fill failure; the share of failed fills whose pool held a
candidate with `W >= θ` that was too young ("age-blocked"); births per occupant-step by age class and by `h` class;
mean parent age at birth; juvenile fraction and mean age; and, if vacancies appear, the mean number of empty sites
among each empty site's four neighbours (are vacancies clustered?).

**Checks (deterministic tests, before running).** `a_b` = 0 reproduces D-E and the matched global and control arms
exactly (all state and random streams); over a run, no realized birth has a parent with start-of-step age below
`a_b`; age boundary: at `a_b` = 1 an age-1 occupant can win, an age-0 one cannot; on a forced case, a pool whose only
candidate with `W >= θ` has age below `a_b` stays empty and is counted as age-blocked, while the same pool with
`a_b` = 0 fills from it; an eligible adult that dies by its death draw in the same step can still parent; an
all-ineligible pool still makes its draw (random streams match a run where the fill is forced to fail by `W`), under
local and global settlement; the runner exports the raw vacancy counts for R7 arms; the pilot rule on forced numbers
(as R6's tests: both levels, viability, the occupancy-only path, incomplete pilots, fail-closed selection, selection
written before `h`); the main-run vacancy label with an extinct seed (excluded from the pooled label, reported
separately).

**Decision.**

- **Pilot fails:** recorded; the next step is decided with the user.
- **Met (either attempt):** at these settings, care for own young met the joint endpoint with the breeding-age rule
  added to the D-E base, and beat help to young neighbours; whether space was vacant is reported with it.
- **Reopening R5:** proposed to the user only if at least 10 of the 20 test seeds are non-extinct and individually
  show vacant space; R5a and R5b then get new pre-registrations with their own exposure pilots (for movement: surviving
  occupants with an empty grid neighbour after fills). The pooled label alone is not enough.
- **Neither met:** recorded with its classification; the next step is decided with the user.

**Predictions (mine, before any data).**

- `a_b` = 2 viable: about 85%. Vacant space at `a_b` = 2: about 50%; at `a_b` = 1: about 15%.
- Pilot passes at some level: about 52%.
- If the main run is done: met in attempt 1, about 55%.

**Budget.** Pilot: 4 runs, a few minutes. Main run: 200 runs, about 25 minutes; attempt 2 about 20 minutes. The
pre-registration and code get a Codex review (gpt-6.2-sol, medium), wording (gpt-reserve, medium) before commit.

**Limits.** One base (D-E, with `G` start 0.75 chosen after DR4); the breeding age equals the care-juvenile period by
choice; the screen is a frozen-state toy calculation that assumes nearly all juveniles were eligible in D-E (not
measured by age) and independence within pools; the pilot looks at two seeds only.

## Step R7b: juveniles cannot breed, with adult founders (pre-registration 2026-11-20, after the R7 pilot; no R7b data; revised per Codex review)

**Why this step, and its status.** In the R7 pilot, `a_b` = 2 was not viable: one of two seeds went extinct. After
the level choice, the trajectories showed an early low-occupancy phase (occupancy about 0.06-0.10 by step 100 in both
seeds): every founder starts at age 0, so no founder is eligible to breed in the first two updates, while uncared occupants die
with probability 0.5 per update. The seed that got through this phase kept occupancy about 0.96 with 19% of fills
left empty, almost all age-blocked (blocked by breeding-age eligibility): the first substantial vacant space
observed on this ladder, in one seed. **This step is data-suggested**
(it was proposed after looking at R7's pilot runs, seeds 0 and 1); it changes only the start condition. Both its
pilot (seeds 20-21) and its main run (seeds 22-41) use seeds that were not looked at, so neither reuses the R7 pilot
seeds that motivated this step, and they are disjoint from each other. Comparisons with earlier rungs (seeds 0-19) are
therefore unpaired.

**Base and ingredient.** Exactly R7 at `a_b` = 2 (D-E base: R4 attempt 1, `γ` = 0.15, `G` start 0.75; eligibility
`occupied & (W >= θ) & (start-of-step age >= a_b)`), except that **all founders' ages are set to 2** (instead of 0)
before the first payoff: they are adults and can breed from the first update. Founders keep `G` = 0.75, `S = D = 0`,
unique ids and parent id −1. Effect on care: own-young care has no recipients among founders at either founder age
(they have no living parent); in the young-neighbour control, age-0 founders were care recipients at the first
payoffs, age-2 founders are not (a start difference between the two founder ages, in the control only). Founders
pay `C·h` and can give care once they have young. Newborns start at age 0 with their breeder's id and receive
own-young care from the next payoff if that breeder survives; the id lookup is the same under local and global
settlement. The initial ages are set without random draws, so the random-draw sequence is unchanged from R7. With founder age 0
this step is R7 exactly.

**Screen (before any data).** The resource starts at 1 everywhere (also in the lean arms), so a founder's first
payoff has `G` = 0.8·0.75 + 0.2 = 0.8 and `W = 0.8 − 0.2·h` (cost `C·h`, no care, no debt), between 0.6 and 0.8,
above `θ` = 0.25: all founders are eligible at the first update, including those drawn to die, so every first-update
fill succeeds and R7's forced two-update breeding pause does not occur. Later low occupancy remains possible as debt
accrues and newborns (barred until age 2) enter the pools (R7's runs were at about 0.06 by step 100). Later occupancy may resemble that of R7's surviving `a_b` = 2 seed (occupancy about
0.96, fill failure about 19%), but that is one seed and a different start; later extinctions are possible. That
seed's final `h` was 0.59, just below the 0.60 endpoint, so the main run's test arm may fail to reach the 15-of-20
success criterion even if space opens; this is a real risk to the verdict, not a reason to change the endpoint.

**Pilot (before the main run).** Seeds **20 and 21**, test arm (b/c 6, local settlement), `a_b` = 2 with adult founders, 2 runs, 6000 steps, payoff
states after 1000-5999 updates, pooled over both seeds. Counts, viability (no extinction and final occupancy >= 0.5
in both seeds) and vacant space (fill failure >= 5% or window occupancy <= 0.97, inclusive; with no fills needed,
occupancy decides) exactly as in R7. **Pass:** viable and vacant space. **Fail:** recorded with its reason ("not
viable" or "vacant space rare"); the main run is not done and the next step is decided with the user. Completeness,
fail-closed selection and writing the decision before any `h` is reported, as in R7 (exactly one finished run per
seed, no other rows). An incomplete pilot gets no biological verdict and triggers no main attempt.

**Main run (only if the pilot passes).** Arms as R7's, with prefix `B` and adult founders in every arm: B6-local
(test), BN6-local (control: help to young neighbours), B-below (b/c 0.25, common start), B3/B12/B24-local, B6-global
(H2), B12-global, B6-local-lean and B6-global-lean (`γ` = 0.08, descriptive); 10 arms, 200 runs, **seeds 22-41**.
Completeness, joint endpoint, classification order, H2, income activation, the vacancy label (pooled over
non-extinct test seeds, extinct seeds reported separately, per-seed measures and the count of test seeds that are
successes with vacant space), and the rule for proposing to reopen R5 (at least 10 of 20 test seeds non-extinct with
vacant space) as in R7. If every test seed goes extinct, the vacancy label is "undefined" and no seed counts toward
reopening R5. The reopening rule is applied to the last completed attempt (attempt 1, or attempt 2 if it ran); it
does not require "met", and R5 would inherit that attempt's settings. "Met" refers to the care comparison only.

**Attempt 2 (fixed now; only if attempt 1 is local failure or comparison failed).** `a_b` = 1 with the same adult
founders (age 2), the eight non-lean arms with prefix `B2-`, `γ` = 0.15, `G` start 0.75, seeds 22-41, no pilot,
same classification. The care-juvenile cutoff stays at 2, so age-1 occupants can then both receive care and breed.
Only a complete attempt 1 classified "local failure" or "comparison failed" triggers it; a pilot failure, an
incomplete attempt or a secondary label does not.

**Descriptive.** As R7, plus occupancy after updates 10, 50, 100 and 500 (does the start-up phase disappear?) and
the number of runs per arm that go extinct, with the first update at which the lattice is empty (both recorded by
the runner).

**Checks (deterministic tests, before running).** Founder age 0 reproduces R7's J arms exactly (all state and random
streams), local, global and the young-neighbour control; with adult founders, every founder is eligible at the first
update and every first-update fill succeeds; in the control, age-2 founders receive no first-payoff care, age-0
founders do; newborns start at age 0, at `a_b` = 2 cannot breed before age 2, and at `a_b` = 1 (attempt 2) can breed
at age 1 while still receiving care; the startup occupancy and first-empty-update records; the pilot rule on
forced numbers (pass, not viable, vacant space rare, incomplete or wrong seed roster, fail-closed, decision before
`h`).

**Decision.**

- **Pilot fails:** recorded; next step decided with the user. If it fails as "vacant space rare", the pooled pilot
  did not clear either vacancy threshold (one seed may still show vacant space; two seeds cannot separate founder age from the
  change of seeds).
- **Met (either attempt):** at these settings, under the tested breeding age and adult-founder start on the D-E base,
  care for own young met the joint endpoint and outperformed help to young neighbours; the vacancy label is reported
  with it.
- **Neither met:** recorded with its classification; next step decided with the user.

**Predictions (mine, before any data).** Pilot viable: about 80%. Vacant space in the pilot: about 75%. Pilot passes:
about 65%. If the main run is done: met in attempt 1, about 35% (R7's surviving seed ended at `h` 0.59).

**Budget.** Pilot: 2 runs, a few minutes. Main run: 200 runs, about 25 minutes; attempt 2 about 20 minutes. Codex
review of the pre-registration and code (gpt-6.2-sol, medium), wording (gpt-reserve, medium).

**Limits.** Data-suggested step; the founder age is a start condition, not an ecological ingredient; two
pre-specified breeding ages (2, then 1 in attempt 2); one base; main-run seeds differ from earlier rungs.

## Step R8: births into empty neighbouring sites, limited by the parent's energy (pre-registration 2026-11-20, after R7b; no R8 data; revised per Codex review)

**Why this step.** The empty-site rung has been attempted five times: R5a and R6 left the lattice almost full, R5b
was skipped, R7 at `a_b` = 1 was viable but missed the vacancy bar, and `a_b` = 2 was not viable in R7 and R7b. In
this model every site that needs a fill draws a parent from its pool of five, and any one eligible candidate fills
it; births are primarily constrained by available space, not by the parents' energy, so occupancy is close to fixed by
construction. In PredPreyGrass-like ecologies (and in Mitteldorf & Wilson 2000), a parent reproduces when it has
gathered enough energy and places its offspring in nearby free space, which lets the population size respond to the
resource. R8 replaces the replacement lottery with an analogous parent-driven birth rule. **This is a structural change, a package of rules
rather than one ingredient**, so it gets a demographic screen before any test of care, and it is the last attempt at
this rung (hard stop, below).

**Base: D-E** (R4 attempt 1, `γ` = 0.15; stores `G`, `S`, `D` with `ρ` = 0.8; own-site harvest `min(r, 0.2)`;
`W = G + 0.5·S − D`; care `B·h` from each occupant, split equally among its own living offspring of age < 2, found by
individual id at any distance (control: among occupied juvenile grid neighbours), at cost `C·h` (`C` = 0.2) paid even
with no recipient; starvation `W < σ` (0); death probability `d0·exp(−0.5·S/T)` with `T` = 0.12; mutation rate 0.02,
SD 0.04, clipped to [0, 1]; founders on a full lattice with `G` = 0.75, age 0). No breeding age.

**One update (all quantities from one payoff snapshot).**

1. **Payoff, as in R4:** every start-of-update occupant (including those that will die) harvests from its own site
   and updates `G ← 0.8·G + g`; care is routed among start-of-update occupants (`S ← 0.8·S + R`, `D ← 0.8·D + C·h`);
   `W` is computed once. A donor that dies later in the update still delivers its care.
2. **Deaths:** an occupant survives if its death draw is at least its death probability and `W >= σ`; deaths are
   counted as draw deaths and added starvation deaths, as in R3d. A dead occupant's site becomes vacant (R3c's empty-
   site convention; `G` = 0 there, never read); the site keeps its post-harvest resource.
3. **Claims (all collected before any site is filled):** a **surviving** occupant is a claimant if `W >= θ` (0.25),
   its updated (pre-split) `G >= g_rep`, and at least one of its four grid neighbours is vacant after step 2
   (vacancies from this update or earlier). Claimants are visited in increasing site index; each draws one target
   uniformly among its vacant grid neighbours, listed in increasing site index (global: all vacancies in increasing
site index), from a new birth stream seeded with 15,000,000 + seed (one `integers` draw per claimant).
   This deliberately differs from earlier rungs, where an occupant that died by its draw could still parent.
4. **Resolution:** targeted sites are visited in increasing site index; a site with one claimant goes to it without a
   draw; a site with several claimants goes to one of them by the softmax of their `W` (`T` = 0.12), one draw from the
   lottery stream; losers make no second claim and pay nothing. Then mutation for all realized births at once, in
   increasing target index, by one call of `inherit_trait_and_lineage` on the lottery stream (all uniforms first,
   then the normals for the mutating births).
5. **Birth:** the newborn gets the parent's `h` (with mutation), a copy of the parent's lineage label, a fresh
   individual id, `parent_id` = the parent's id, age 0, `S = D = 0`. **Attempt 1 (energy split):** the parent's `G` is
   halved and the newborn starts with the other half (`G` is conserved), and **there is no separate birth cost
   (`c_b` = 0)**: the energy given to the offspring is the cost of the birth. (Keeping `c_b` = 0.5 as well would make a
   founder with `h` = 0.6 that breeds at update 1 starve at update 2: `G` 0.52, `D` 0.616, `W` = −0.096.) The split
   first affects condition at the next payoff. The newborn first harvests at the next update.
6. **Ageing and regrowth:** survivors age by 1, newborns stay at 0; every site regrows once, `r ← r + γ(1 − r)`.

At most one birth per parent per update; nobody gives birth on an occupied site; a lattice with no vacancy after the
deaths has no births. R8 does not reduce to an earlier step, so it is checked by invariant tests, not by a reduction.

- **Global dispersal (the H2 control for this rung):** a claimant needs at least one vacancy anywhere and draws its
  target uniformly from all vacancies on the lattice (it can still land next to its parent by chance); everything else
  is the same, including care to own young by id at any distance. Global targeting also changes access to vacancies
  and competition for them, so the local/global contrast does not isolate relatedness alone.

**Two parameters, selected by the screen:** the base death `d0` (0.5 in every earlier rung) and the reproduction
threshold `g_rep`. With `d0` = 0.5 and energy-limited births, a population without care would need a birth about every
two updates, more than the store can supply after a split, so non-helpers would likely die out and care could act mainly as
a survival aid rather than as a trait under selection (the problem that stopped `../floor_control/`). The screen looks
for settings at which a population of non-helpers **and** a population of helpers both persist with vacant space.

**Stage S: demographic screen (no evolution, before any care test).** Fixed traits, no mutation: `h` = 0 everywhere,
and separately `h` = 0.6 everywhere (own-young care, b/c 6, `B` = 1.2), local births, attempt-1 rules. Grid: `d0` in
{0.1, 0.2, 0.3} × `g_rep` in {0.5, 0.7}; seeds 50 and 51; 3000 updates; window = the start-of-update states after
1000, ..., 2999 completed updates (2000 states; occupied site-updates over all site-updates). 24 jobs. **Complete:** exactly one finished result per
(point, `h`, seed) with the full window and no other rows; an extinct run is a valid result; a missing, duplicated,
failed or truncated job makes the screen incomplete (no point chosen; the same jobs are rerun). **A point passes** if,
for both `h` levels and both seeds, the run does not go extinct, its final occupancy is >= 0.50, and its own window
occupancy is between 0.50 and 0.95 inclusive (per seed, so one seed cannot be averaged away). **Choice:** among passing
points, the highest `d0` (closest to the earlier rungs), then the lower `g_rep`. **If no point passes, R8 stops** (see
the hard stop). The choice and per-point outcomes are written before Stage M is run. Also recorded: occupancy after
updates 10, 50, 100 and 500, births, draw and starvation deaths. Scope: the screen tests whether two homogeneous
populations can persist with vacant space under local, split-energy births; it does not test that rare helpers can
invade, nor that the control, global or attempt-2 arms are viable.

**Stage M: care test (only if Stage S chose a point).** At the chosen `d0` and `g_rep`, prefix `U`: U6-local (test:
own-young care, b/c 6, local births), UN6-local (control: help to young neighbours, b/c 6), U-below (own-young care,
`B` = 0.05, b/c 0.25, common start: initial `h` 0.9, SD 0.05), U3/U12/U24-local, U6-global (H2: global dispersal),
U12-global; all but U-below start rare (initial `h` 0.05, SD 0.02); 8 arms, 160 runs, seeds 0-19, 6000 updates.
Completeness as in Stage S (exactly one finished run per arm and seed; window = the start-of-update states after
1000, ..., 5999 completed updates, 5000 states, as in earlier rungs); an incomplete attempt gets no
classification, is rerun as the same jobs, and triggers nothing. **Joint endpoint per run:** final mean `h` over
occupied sites >= 0.60 and final occupancy >= 0.50; both components are reported per seed (the test-control contrast
can also pass because the control loses occupancy, and U-below can stay below its gate by collapsing, so "met"
supports the joint endpoint for the own-young care package, not a trait effect alone). **Classification, in order:**
local failure if U6-local succeeds in fewer than 15/20 or U-below in more than 2/20; else comparison failed if U6-local
leads UN6-local by fewer than 8 successes or the one-sided Fisher p >= 0.025; else met. **H2 (each attempt that runs):**
U6-global; neighbour `h` correlation over occupied grid edges, sampled after updates 1000, 2000, ..., 6000 in all 20
seeds, equal weight per sample; if any sample is undefined or the mean is above 0.10, H2 is "not interpretable";
otherwise met if >= 15/20, else not met. **Labels (reported, never gates):** income activation as in R4 (pooled harvest
<= 0.19); vacancy: fills needed = sites vacant after the deaths, fills failed = those not filled by a birth, pooled
over non-extinct test seeds' windows; fill failure >= 5% or window occupancy <= 0.97 gives "vacant space present",
otherwise "vacant space rare"; if every test seed goes extinct, "undefined". "Met" refers to the care comparison only.

**Attempt 2 (fixed now; only if a complete attempt 1 is local failure or comparison failed).** A smaller step back
toward D-E's birth economics: the same parent-driven claims (survivors, `W >= θ`, `G >= g_rep`, chosen `d0`), but
**without the energy split**: the newborn gets the free `G` = 0.75 and the parent keeps its `G` and pays `c_b` = 0.5
to `D`, as in D-E. Prefix `U2-`, the same 8 arms, seeds 0-19, no screen of its own (Stage S applies to attempt 1),
same classification and labels. A success there supports parent-driven births with the `G` gate and a free newborn
endowment, not energy-conserving births.

**Descriptive.** Births per occupant-update; claimants per targeted site; targeted sites per vacancy; births by `h`
class; deaths by cause; mean `G`, `S`, `D` for juveniles and parents; occupancy after updates 10, 50, 100, 500 and the
first empty update per run; neighbour `h` correlation, local against global.

**Checks (deterministic tests, before running).** Births only into sites vacant after this update's deaths; at most
one birth per parent per update; a dying or starving occupant never parents; a claimant needs `W >= θ`, pre-split
`G >= g_rep` and a vacant grid neighbour (global: a vacancy anywhere, including adjacent ones); claim order and draw
order as specified (birth stream for targets, lottery stream for conflicts then mutations; no draw for single
claimants); with several claimants the softmax over `W` decides and losers keep their `G` and pay nothing; attempt 1:
the split conserves `G` exactly and no `c_b` is charged; attempt 2: newborn `G` 0.75, parent `G` unchanged, `c_b` 0.5
charged; the newborn's id, parent id, lineage and age; care to a newborn starts at the next payoff (own young by id,
also after global dispersal); the target keeps its resource and regrows once; a site nobody targets stays vacant;
no births when no site is vacant after the deaths; the hand-computed founder case above (with and without `c_b`); the
screen's predicates on forced numbers (per-seed bounds, inclusive, extinction and final-occupancy failures, both `h`
levels required, tie order, no passing point, incomplete screens); completeness and fail-closed outputs as in R7.

**Decision and hard stop.**

- **Stage S complete, no passing point:** "no setting passed the registered R8 screen"; the empty-site rung is closed.
- **Met (either attempt):** at these settings, with parent-driven births into vacant sites, care for own young met the
  joint endpoint and had the registered advantage over help to young neighbours; the vacancy label and H2 are
  reported with it. If the
  vacancy label is "vacant space rare", the empty-site question itself is recorded as still not reached.
- **Neither attempt met:** recorded with its classification; the empty-site rung is closed.
- **Hard stop (agreed in advance):** R8 is the last attempt at this rung. After R8's outcome (any of the above), the
  next step is a write-up of R1-R4 and of the empty-site attempts, decided with the user, not another variant.
  Incomplete executions are rerun as the same registered jobs and are not outcomes.

**Predictions (mine, before any data).** Stage S finds a passing point: about 50%. If Stage M runs: met in attempt 1,
about 35%; H2 met, about 40%; vacant space present in the test arm, about 85%.

**Budget.** Stage S: 24 runs of 3000 updates, a few minutes. Stage M: 160 runs, about 25 minutes; attempt 2 about the
same. Codex review of the pre-registration and code (gpt-6.2-sol, medium), wording (gpt-reserve, medium).

**Limits.** A package of rules rather than one ingredient, with two parameters chosen by a screen at fixed traits;
`d0` will be lower than in every earlier rung, so the care benefit (lower death) is smaller in absolute terms; attempt
1 drops the separate birth cost; births are local (one grid step) except in the global-dispersal arm; asexual
reproduction; one resource setting.

## Diagnostic DR8: are high helpers blocked by a full neighbourhood? (pre-registration 2026-11-20, after R8; exploratory; no DR8 data)

**Why.** In R8 attempt 2, own-young care settled near `h` 0.35 with local births but reached 0.99 under global
dispersal. One candidate explanation (local saturation, a simple form of kin competition): a helper's surviving young
fill the sites around it, so helpers more often have no vacant neighbour to breed into, and the benefit of care
saturates locally. DR8 measures this on the existing runs. It adds no model ingredient and no random draws, does not
change R8's verdict, and is exploratory (the explanation was proposed after seeing R8).

**Runs.** U2-6-local (test) and U2-6-global (comparison), R8 attempt 2 at the Stage-S point (`d0` 0.2, `g_rep` 0.5),
seeds 0-19, 6000 updates. **Validity:** each run's final mean `h` and final occupancy must equal the stored
`r8_main_runs.csv` values exactly; otherwise DR8 is void.

**Measures** (window: payoff states after 1000-5999 completed updates). A **would-be breeder** is a survivor with
`W >= θ` and `G >= g_rep` (a claimant before the vacancy requirement). At each update, would-be breeders are split
into **high** and **low** helpers: `h` above, or at or below, the mean `h` of that update's start-of-update occupants.
Per class, pooled over the window per seed: the **blocked fraction** (share of would-be breeders with no vacant grid
neighbour after the deaths), births per would-be breeder, and the share of their occupied surviving grid neighbours
that are their own offspring.

**Reading (local arm, seed-level sign count over 20 seeds).** `Δ` = blocked fraction (high) − blocked fraction (low).
If `Δ` > 0 in at least 15 seeds: **"high helpers more often blocked" (consistent with local saturation)**; if
`Δ` > 0 in at most 5 seeds: **"not supported"**; otherwise **"unclear"**. Seeds where either class has no would-be
breeder-updates are excluded and counted. Reported alongside: the same for births per would-be breeder (lower for
high helpers is consistent), the own-offspring share (higher for high helpers is consistent), and the global arm's
values (where any vacancy anywhere counts, so blocking should be near zero for both classes).

**Predictions (mine, before any data).** "High helpers more often blocked": about 65%; "unclear": 25%; "not
supported": 10%.

**Limits.** Exploratory; one setting; a high/low split at the update mean is coarse; blocking at one update is not
lifetime reproduction; it does not separate saturation by own young from saturation by other kin or non-kin.
