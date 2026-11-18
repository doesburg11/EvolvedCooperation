# Kin Selection With Learned Helping (design, 2026-11-18, not yet built)

Status: **design for review, nothing run.** Written before any code or data for this module exists.

## Question

The ecological kin-selection model (`../kin_selection/`) shows that an inherited helping trait can spread when
dependent juveniles are reared near relatives. Human helping is largely learned. Two questions follow:

1. **Does kin selection survive when helping is learned rather than inherited?** A learner that only maximizes its
   own energy should never learn to help: the benefit lands on the juvenile, not on the learner. So a learner needs
   an inherited motive, a weight on how much its household's juveniles count in its own reward. Genes set the
   motive, learning sets the behaviour.
2. **Does learning help kin selection get started?** A small inherited motive could be turned into real helping by
   learning, so helping could spread from a start where nobody is a strong helper. This is the Baldwin-style
   amplification seen in this project's ERL results.

This is the first rung of a ladder: the predator-prey (PredPreyGrass) version is only planned if this rung passes.

## Why the existing settings would make this foregone

At the default cost (`care_cost_per_unit` 0.03), full care costs a helper about 0.075 energy per step against
0.32 foraging income, and can raise a juvenile's survival by up to 0.75. The benefit is about 25 times the cost, so a
learner with almost any kin weight learns to help at once. Step 0 therefore first raises the cost until inherited
helping is only marginally favoured.

## Versions

All three share the existing life cycle, care rule, households and relatedness. They differ only in what sets a
helper's care effort.

| Version | Care effort | Inherited trait | Reward of the learner |
| --- | --- | --- | --- |
| **A, genetic** | inherited helping trait `h` (unchanged model) | `h` | none (no learning) |
| **B, selfish learner** | learned effort `e` | none acting (`h` drifts) | own energy cost of care only |
| **C, kin-regard learner** | learned effort `e` | kin regard `k` (inherited exactly as `h` is now) | own care cost + `k` x household juvenile losses |

**Learning rule (B and C).** Each adult and elder has a learned effort `e` in [0, 1], set to 0.05 at maturity and not
inherited. Each step it acts with `a = clamp(e + noise)`, noise ~ N(0, 0.1), and care budget `a * care_capacity`
replaces `h * care_capacity`. After the survival step it gets reward

```
r = -(care energy cost paid this step) - k * V * (household juveniles that died this step)
```

with `V` = 4.5 (child energy 3.5 + reproduction cost 1.0, the energy price of a juvenile) and `k = 0` in B. It
updates by a REINFORCE step with a running baseline: `e += alpha * (r - b) * (a - e) / 0.1^2`, `b += 0.1 * (r - b)`.
The household signal is shared by every helper in the household and is a noisy count of deaths, so the learner must
pick out its own contribution from others' care and chance: that is the realistic difficulty, and it carries over to
the predator-prey world.

**Learning-rate calibration (fixed before step 1, no outcome data).** `alpha` is the smallest value from
{0.002, 0.005, 0.01, 0.02, 0.05} at which, in a stand-alone test with the model's household sizes and death noise,
a learner with a clearly profitable `k` reaches effort >= 0.8 within 30 steps (about half an adult life) and one
with `k = 0` falls below 0.1. Recorded in this README before step 1.

## Steps

**Step 0, cost calibration (version A only, no learning).** Sweep `care_cost_per_unit` over
{0.03, 0.1, 0.2, 0.3, 0.45, 0.6} with the existing rare-helper start, 20 seeds each, 220 steps, the existing success
rule of `utils/proof_of_mechanism.py`. Choose `c*` = the cost whose A success rate is closest to 50%, and in [30%, 70%]
(highest cost on a tie). If no cost lands in that band, stop and report: the model has no marginal regime to test.

**Step 1, main comparison at `c*`.** Two starts, three versions, 40 seeds each (240 runs, minutes on CPU):

- **Rare start:** the existing rare-founder start (3% founders at 0.65).
- **Weak start:** no rare founders; all founders' `h` (A) or `k` (C) uniform in [0, 0.04].

Success per run, adapted from the existing rule: mean *expressed* helping (A: `h`; B, C: `e` of adults and elders)
rises by >= 0.015 from its step-20 value (after learning settles from its 0.05 start), and final population >= 100.

## Pre-registered tests

- **T1, sanity.** B succeeds in <= 10% of runs in both starts.
- **T2, learning keeps kin selection (rare start).** C's success rate is no more than 0.15 below A's, and at least
  0.30 above B's.
- **T3, learning helps it start (weak start).** C's success rate exceeds A's by >= 0.20, Fisher exact one-sided
  p < 0.05 (40 vs 40 runs).
- **Decision.**
  - T1 + T2 + T3: plan the PredPreyGrass version (dependent young, inherited kin regard, learned help), with its own
    payoff check and budget, for the user to approve.
  - T1 + T2 only: learning neither breaks nor helps kin selection here. Porting is less motivated; decide with the
    user.
  - T2 fails: stop. No PredPreyGrass port.
  - T1 fails: the reward or learning code is wrong; debug before reading any other result.
- **My predictions.** T1 met, T2 met, T3 uncertain (about 50%).

## Descriptive measures

Mean `k` and `h` trajectories, expressed effort by age, care relatedness and household care fraction (existing
diagnostics), helper lifetime reproductive success by birth `k`, and how far learned effort sits from the effort
that maximizes the learner's own reward.

## Limits

- The model is non-spatial: groups and households, not positions.
- The reward weight on household juvenile deaths is hand-designed. Households here follow the maternal line, so they
  are mostly kin; the learner gets no relatedness cue beyond household membership.
- The learning rule is a simple one-parameter learner, far from PPO in a gridworld. A pass here is necessary, not
  sufficient, for the predator-prey version.

## Budget and hard stop

One session for step 0 plus step 1. No parameter changes after seeing step-1 results; `c*` and `alpha` are fixed by
the rules above before step 1. Code gets a Codex review before step 0, and the results wording a Codex review
before commit.
