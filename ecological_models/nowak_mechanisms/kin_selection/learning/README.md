# Kin Selection With Learned Helping (design 2026-11-18)

Status: **CLOSED 2026-11-18. Step 1: T1 met, T2/T3 not met. Confirmation test: H1 met (C persists 40/40 in both starts), H2 and H3 not met (a constant effort of 0.07, or the no-update learner, does as well and more cheaply). Learning gave no detectable persistence benefit; no PredPreyGrass port.** The design below was written before any code or data existed; amendments made while building are marked.

## Question

The ecological kin-selection model (`../`, the base `kin_selection` package) shows that an inherited helping trait can spread when
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
updates by a REINFORCE step with a running baseline (normalized, see amendment 2): `e += alpha * (r - b) * (a - e) / 0.1^2`, `b += 0.1 * (r - b)` as first written.
The household signal is shared by every helper in the household and is a noisy count of deaths, so the learner must
pick out its own contribution from others' care and chance: that is the realistic difficulty, and it carries over to
the predator-prey world.

**Learning-rate calibration (fixed before step 1, no outcome data).** `alpha` is the smallest candidate at which, in a
stand-alone toy household with the model's care and death rules, a learner with a clearly profitable `k` reaches its
best effort within 30 steps (about half an adult life) and one with `k = 0` falls below 0.1 (amended below).
Recorded in this README before step 1.

**Amendments before step 0 (2026-11-18, no model outcome data yet).** Found while building and testing:

1. *Calibration toy.* Care saturates and households hold many carers (founding lineages of about 3-13 carers
   sharing one or two juveniles), so a kin-motivated learner's best effort is often far below 1: once others
   saturate a juvenile, its own extra effort buys nothing. That free riding is part of the experiment, but it made
   the fixed target "effort >= 0.8" wrong. The calibration toy now has one carer and two juveniles (measuring
   learning speed, not free riding); the target is that toy's reward-maximizing effort (about 0.69 for k = 0.65),
   within 0.1; the k = 0 learner starts at 0.5 so its test is not met trivially from 0.05.
2. *Learning rule, three fixes found by testing the learners* (no experiment data). (a) The kin term (k x 4.5 x
   deaths) is about ten times the cost term, so no single learning rate served both kinds of learner. The surprise is
   now divided by the learner's maximum stake per step, `s = care_cost_per_unit * care_capacity + k * V`. (A
   running-spread normalization was tried first and dropped: it blew pure noise up to full-size steps.) (b) The
   update uses the unclipped exploration noise `eps` (the Gaussian score function), not the clipped `a - e`, which
   with a drifting baseline pushed effort to 0 or 1 without any signal. (c) A learner learns only on steps where it
   could help (above the energy reserve, a juvenile in its group); on other steps its action has no consequence.
   Final rule: `e += alpha * ((r - b) / s) * eps / 0.1`, `b += 0.1 * (r - b)`.
3. *Candidates.* With these fixes the passing range moved up; candidates are now {0.1, 0.2, 0.3, 0.5, 1.0}, set from
   the toy alone (0.3-0.5 pass at costs 0.03-0.6). From the real 0.05 start, selfish learners fall to about 0.004 by
   step 20 (a test).
4. *Codex code review before step 0.* The stake now uses a grandmother's larger care capacity; learning is gated off
   when rearing dependency or care benefit is disabled; step 1 counts successes per cell directly and requires
   exactly one run per configured seed; a run that dies out before step 20 scores as a failure.
5. *Prediction update.* Because learners can free-ride and inherited helpers can't, T2 is now less certain than
   first written: about 50%.

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
- **My predictions.** T1 met; T2 about 50% (amendment 5); T3 uncertain (about 50%).

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

## Step 0 result (2026-11-18)

Version A, existing rare-helper start, 20 seeds per cost, existing success rule (`data/step0_runs.csv`,
`data/step0_result.json`):

| `care_cost_per_unit` | 0.03 | 0.1 | 0.2 | 0.3 | 0.45 | 0.6 |
| --- | --- | --- | --- | --- | --- | --- |
| A success rate | 0.60 | 0.20 | 0 | 0 | 0 | 0 |

By the registered rule, **c\* = 0.03**, the default cost: the only cost in the 30-70% band. Inherited helping is
already marginal at the default, because spreading from rare founders is stochastic (the original proof suite found
2 of 5), and it collapses quickly as cost rises. The design's worry that the default makes the comparison foregone
was about learners: a learner with almost any kin weight learns to help when helping is this cheap. Free riding in
large households (amendment 1) may still keep learned effort low, so the comparison is not settled in advance.

**Caveat recorded before alpha calibration and step 1 (2026-11-18, no learner data).** In the one-carer toy at
c\* = 0.03, the reward-maximizing effort is 0 for k <= 0.005 and about 0.69 for k >= 0.01. The weak start draws k
uniform in [0, 0.04], so about three quarters of C's founders are already above that threshold. A T3 pass would
therefore mostly say "helping is nearly free here", not that learning amplifies a weak motive; it should be read
that way. Conversely, if C's learners already help by step 20, the rise-from-step-20 success rule can score C as a
failure for that reason alone, so a T3 fail is not clean evidence against amplification either. T1 and T2 are not
affected. Step 1 runs as registered, unchanged.

## Alpha calibration result (2026-11-18, before step 1)

Toy at c\* = 0.03, k = 0.65, target effort e\* = 0.694 (`data/alpha_result.json`):

| alpha | 0.1 | 0.2 | 0.3 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- | --- |
| k = 0.65 learner, from 0.05 | 0.538 | 0.737 | 0.784 | 0.756 | 0.701 |
| k = 0 learner, from 0.5 | 0.210 | 0.050 | 0.017 | 0.011 | 0.019 |
| passes | no | yes | yes | yes | yes |

By the registered rule (smallest passing candidate), **alpha = 0.2**.

## Step 1 result (2026-11-18)

c\* = 0.03, alpha = 0.2, 40 seeds (100-139) per cell (`data/step1_runs.csv`, `data/step1_verdict.json`).

| Success rate (registered rule) | A genetic | B selfish learner | C kin-regard learner |
| --- | --- | --- | --- |
| Rare start | 0.30 | 0 | 0 |
| Weak start | 0 | 0 | 0 |

- **T1 met** (B 0 in both starts).
- **T2 not met** (C rare 0 vs A rare 0.30).
- **T3 not met** (C weak 0 vs A weak 0, Fisher p = 1).
- **Registered decision: T2 fails, stop. No PredPreyGrass port from this design.**

**Exploratory, not pre-registered.** The success rule needs mean expressed helping to *rise* after step 20. C never
does: mean change from step 20 to the end was −0.061 (rare) and −0.067 (weak), negative in every C run. In the one
traced run (seed 100, `data/step1_trace_seed100.csv`), C's mean effort peaked early (0.13 at step 9 rare, 0.12 at
step 7 weak) and then fell. Over the same step-1 runs the populations differ sharply:

| Final population >= 100 | A genetic | B selfish learner | C kin-regard learner |
| --- | --- | --- | --- |
| Rare start | 13/40 | 0/40 | 40/40 |
| Weak start | 0/40 | 0/40 | 40/40 |

C's final populations were 270-320 (the cap is 320); A's weak-start runs and nearly all B runs went extinct (B's
largest final population was 55). In the traced run, C's population grew from 128 to about 300 by step 40 while its
mean effort peaked and fell. One reading is that learners raise care while juveniles are short of it and lower it
once many carers share them; this was not tested, and alternatives remain: the reward counts household-wide deaths
(so effort also tracks other carers and household conditions), the mean effort mixes learning with which helpers
survive, and once C reaches the cap, density mortality (lowest energy first) shapes who is left. B and C use the
same learner code; C's inherited kin weight enters both the death term of the reward and the stake that scales each
update. The C-versus-A contrast differs in more than one way (conditional learned effort versus a fixed trait). The
mean kin-regard gene changed little in C (+0.011 to +0.012), so persistence went with learned helping rather than a
large shift in mean kin regard; without a frozen-k or no-learning C control this does not separate learning from
selection.

These persistence counts were found after seeing the step-1 results. They suggest, but do not establish, that the
registered measure (a rise in mean effort) was a poor fit for a learner whose effort can fall once care is no longer
scarce. Persistence is also near-saturated (most C runs end at or near the cap), so it may depend on the cap and run
length. This is a hypothesis, not a result: a confirming test would need its own pre-registration (persistence as
the outcome, fresh seeds) and the user's approval.

## Confirmation test: persistence (pre-registration 2026-11-18, before any code or data for it; revised per Codex review before commit)

**Question.** Is step 1's exploratory result real, and if so, is it learning that does it? Three possibilities:
(a) chance or a quirk of the step-1 seeds; (b) C simply acts with more effort than A's weak founders (0.05 plus
noise, a mean action of about 0.07 after clipping, against `h` in [0, 0.04]), so a constant effort of that size would
do as well; (c) the updates matter: effort that rises when juveniles are short of care and falls when they are not
keeps a population alive where a constant effort does not, or does so more cheaply.

**Arms.** All at c\* = 0.03, alpha = 0.2, 220 steps, the step-1 code. Fresh seeds 200-239, the same 40 seeds in every
arm, so arms are compared seed by seed.

| Arm | What sets care effort | Starts |
| --- | --- | --- |
| A | inherited trait `h` | rare, weak |
| B | learned, no kin term (`k` = 0) | rare, weak |
| C | learned, inherited `k`, as in step 1 | rare, weak |
| C-nolearn | C with alpha = 0: acts at 0.05 plus the same noise, never updates | rare, weak |
| C-frozen | C, but each newborn draws `k` uniformly from [0, 0.04] instead of from its parents (no heritability, so no selection on `k`) | weak |
| D0.05, D0.07, D0.10, D0.15, D0.20, D0.30 | the same constant effort for every carer, no noise, no learning | weak |
| N0.10, N0.15, N0.20 | constant mean effort plus the learners' noise (sigma 0.1, clipped), no learning; C-nolearn is the N0.05 arm | weak |

The constant arms do not use `h` or `k`, so they run in the weak start only. Their grid (0.05-0.30) brackets the
efforts C showed in step 1 (about 0.02-0.13).

**Outcomes.**

- *Persistence*: the population stays >= 100 at every step from 181 to 220 (a terminal window, not one snapshot).
- *Cost*: per run, the care energy paid per carer step, `sum(total_helper_energy_cost) / sum(adult_count +
  elder_count)` over steps 1-60. This is the growth phase, before any arm reaches the cap of 320; it is counted for
  every run, including runs that later fail, over the steps it is alive.
- *Paired test*: for two arms on the same seeds, a one-sided exact sign test on the seeds where exactly one arm
  persists (McNemar); p = 1 if there are none. A difference counts only if both the size threshold and p < 0.05 hold.

**Hypotheses.**

- **H1, replication.** In both starts, C persists in >= 80% of runs and beats A and B each by >= 0.40 (paired test).
- **H2, the updates matter (weak start).** C beats C-nolearn by >= 0.30 (paired test). This compares the same noisy
  action process with and without updates. The rare start is reported, not tested.
- **H3, a constant effort does not do as well (weak start).** Call a constant arm (D or N) *matching* if its
  persistence is >= C's minus 0.10.
  - No constant arm matches: H3 is met, provided C's mean expressed effort over steps 1-60 lies inside the grid
    (0.05-0.30). Outside the grid, H3 is inconclusive.
  - Some constant arm matches: take the matching arm with the lowest mean effort. H3 is met if its cost per run is
    >= 1.25 times C's (the median of the seed-by-seed ratios over seeds where both persist), with a seed-bootstrap
    95% interval above 1.0. Otherwise H3 is not met.

**Descriptive only.**

- Persistence and cost of every arm, each with a seed-bootstrap interval.
- C-frozen against C (does selection on `k` matter?).
- Mean `k` over time in C.
- A feedback signature: within C, the correlation between a step's juveniles-per-carer and the next step's change in
  mean effort, compared with the same correlation after shuffling steps.
- A run-length check: A, B, C and C-nolearn in the weak start, run from step 0 to 440 steps on the same seeds, with
  persistence over steps 401-440.

**Decision.**

- H1 fails: the step-1 exploratory result is not confirmed. Recorded as such; the kin-learning line closes.
- H1 met, H2 fails: the result comes from the noisy starting effort, not from updates. The line closes.
- H1 and H2 met, H3 not met: updates matter, but a constant effort does as well at about the same cost. The port is
  weakly motivated; decide with the user.
- H1, H2 and H3 met: write a PredPreyGrass theory screen (does a predator's food gift to its young pay at
  predator-prey costs?) for the user to approve. That is a paper check, not a training run.
- H3 inconclusive is treated as H3 not met.

**Predictions (mine, before any data).** H1 about 85%. H2 about 60%: a mean action of about 0.07 may already be
enough, since A's weak founders average only 0.02. H3 about 35%: the higher constant efforts (0.15-0.30) will likely
persist, and the cost test then decides.

**Amendments from the Codex code review (2026-11-18, before any data for this test).**

1. All thresholds compare whole numbers of runs (0.40 of 40 = 16 runs, 0.30 = 12, 0.10 = 4, 0.80 = 32), so float
   rounding cannot fail an exact boundary.
2. *Effort* in the H3 grid check is the realized mean action of carers that could help (noise and clipping
   included), averaged over steps 1-60, not the latent learned effort. C-nolearn's realized mean is about 0.07.
3. H3's "matching arm with the lowest mean effort" is replaced by **the matching arm with the lowest median cost per
   run** (over its persisting runs), ties broken by lower nominal effort. This is the stricter choice for H3, and it
   settles ties between a D and an N arm at the same level.
4. C-frozen draws its newborns' `k` from a separate random stream, so it shares C's main random stream.
5. Mean `k` over time in C is saved as a series (every 10 steps, `data/confirm_k_series_C.json` per run).

**Budget and hard stop.** About 880 runs, a few minutes on CPU. One session. Code gets a Codex review before the
run, and the wording a Codex review before commit. No arm, threshold or parameter changes after seeing results; a
failure is recorded, not tuned.

**Limits.**

- The cap (320) and run length are the model's defaults.
- The kin weight acts on household-wide deaths, not on the learner's own effect.
- The grid is coarse: a constant effort between grid points is not tested.
- The cost window (steps 1-60) is set here before data. If some arm reaches the cap before step 60, that is
  reported.

## Confirmation test result (2026-11-18)

Seeds 200-239, 880 runs: 720 main runs plus 160 long-run checks (`data/confirm_runs.csv`, `data/confirm_verdict.json`, `data/confirm_k_series_C.json`).

| Persisting runs (of 40) | A | B | C | C-nolearn | C-frozen |
| --- | --- | --- | --- | --- | --- |
| Rare start | 15 | 0 | 40 | 40 | - |
| Weak start | 0 | 0 | 40 | 40 | 40 |

| Constant effort (weak start), persisting runs (of 40) | 0.05 | 0.07 | 0.10 | 0.15 | 0.20 | 0.30 |
| --- | --- | --- | --- | --- | --- | --- |
| No noise (D) | 33 | 40 | 40 | 40 | 37 | 35 |
| With learners' noise (N; 0.05 is C-nolearn) | 40 | - | 40 | 40 | 40 | - |

- **H1 met.** C persisted 40/40 in both starts and beat A (rare: 25 seeds only C persisted, 0 only A, p = 3e-8;
  weak: 40 to 0) and B (40 to 0 in both starts).
- **H2 not met.** C and C-nolearn persisted on the same 40 seeds (difference 0, p = 1).
- **H3 not met.** Eight constant arms matched C. The cheapest, C-nolearn, paid 0.72 times C's cost per carer step
  (seed-by-seed median, 95% interval 0.70-0.76), so it was cheaper, not 1.25 times dearer. C's realized mean
  action over steps 1-60 was 0.10.
- **Registered decision: H1 met, H2 failed. Persistence was already reached by the noisy starting effort; the
  updates added no detectable persistence benefit. The kin-learning line closes.**

**What this means.** The step-1 persistence difference is real, but learning did not detectably improve it. A small
steady care effort was enough: 0.07 without noise persisted 40/40, 0.05 without noise 33/40 (the grid is too coarse
to place a threshold). C's learners start at 0.05 and act with noise, a realized mean of about 0.07. A's weak-start
founders average 0.02, and A persisted 0/40 there. Learning and heritable kin regard showed no persistence advantage
here: C-nolearn and C-frozen (no heritable `k`) also persisted 40/40, at the ceiling and without an equivalence test.

**Descriptive.**

- Cost comparisons are tied to growth. C reached the 320 cap by step 60 in 39 of 40 weak-start runs and C-nolearn
  in none. The cost window therefore covers different densities in the two arms. This was not a free pass for H3:
  it failed.
- High constant efforts (0.20-0.30, no noise) persisted slightly less often (37/40, 35/40) than 0.07-0.15.
- In C, juveniles per carer at a step correlated with the next step's change in mean learned effort (r = 0.25,
  95% interval 0.24-0.27; shuffled ≈ 0). The learners do respond to need, but that response produced no
  detectable persistence advantage here.
- Long runs (440 steps, weak start): C and C-nolearn 40/40, A and B 0/40.
