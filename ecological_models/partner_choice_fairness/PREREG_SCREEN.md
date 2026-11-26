# Partner choice and fair sharing: theory screen, pre-registration (2026-11-26)

**Status: agreed with the user 2026-11-26 (about 15:20 CET), before any code for steps 2 and 3 and before
any measurement.** Revised once the same day after a Codex review (gpt-6.2-sol, medium), still before any
code: step 3 no longer places PPG on the step-2 threshold (PPG has no lasting pairs, so its catch intervals
and lifetimes do not measure search cost or partner horizon) and is now descriptive; a random start was
added; matching is labelled nominal; outcome, ties and no-verdict cases were specified. The only
computation so far is step 1's closed form, done in the chat that led to this file and recomputed by Codex
(all 12 entries agree).

## Why

The project's goal is human cooperation (humanbehaviorpatterns.org). Kin selection explains cooperation
across many social species and does not single out humans; large-scale cooperation with non-kin does. One
leading account is the interdependence / biological-market view (Tomasello; André & Baumard 2011,
*Evolution*; Debove, André & Baumard 2015, *Proc. R. Soc. B*): early humans had to hunt together, so
everyone needed partners, and partners who could leave a stingy hunter forced the catcher to offer a fair
share. Fairness is then what it costs to keep a partner, not altruism.

This builds on two earlier results. In PredPreyGrass `deer_stag_hunt` (closed positive 2026-11-10) group
hunting of adult deer was learned, but the catch is split evenly by a fixed rule, so fairness could not be
learned there. In this repo `stag_hunt_sharing` (2026-11-11) sharing with everyone nearby always hurt stag
hunting, and the conclusion was that sharing has to be targeted (partner choice named as one route).

The screen asks, before any PPG module is built: **can the option to leave a partner turn an exploitative
market into a fair one, and over what range of search costs?** Steps 1 and 2 use no learning; step 3 uses
existing PPG checkpoints only, no training.

## Step 1: closed form (done)

A pair catches a stag worth S every round; the catcher keeps 1 − s and gives s·S to the partner. An agent
without a partner gets the hare payoff h per round and finds a new partner with probability m per round
(expected search time T = 1/m); a match starts paying the round after it is found. Future rounds are
discounted by δ (H = 1/(1 − δ)). Assume the rest of the market pays a fair half (S/2 per round once paired).

A partner stays as long as its per-round income x satisfies x/(1 − δ) ≥ V_leave, where
V_leave = (h + δ m V_fair) / (1 − δ(1 − m)) and V_fair = (S/2)/(1 − δ). So the least a catcher can offer
while keeping the partner is

x_min = [(1 − δ) h + δ m S/2] / (1 − δ + δ m);  with h = 0 exactly x_min / S = (H − 1) / [2 (H − 1 + T)].

Computed (h = 0), partner's share of S:

| H \ T | 2 | 5 | 20 | 50 |
| --- | --- | --- | --- | --- |
| 100 | 0.490 | 0.476 | 0.416 | 0.332 |
| 200 | 0.495 | 0.488 | 0.454 | 0.400 |
| 1000 | 0.499 | 0.498 | 0.490 | 0.476 |

**Reading:** in a fair market, the least a catcher can offer *and keep its partner* is near fair when
finding a new partner is quick compared with the horizon (T/H small), and falls toward exploitation as
T/H grows. **Limits:** it is conditional on retention (it does not compare keeping the partner with
under-offering and rematching), and it assumes a fair market already exists. Whether one can arise is
step 2.

## Step 2: evolving market, no learning

### Model (`market.py`, to be written; numpy, one process per run)

- N = 200 haploid agents, two inherited traits in [0, 1]: offer s and acceptance threshold a. Each agent
  has an ID within the generation.
- Non-overlapping generations of H = 100 rounds. Every agent starts each generation unpaired.
- **Each round, in this order:**
  1. **Search.** Each unpaired agent succeeds with probability m = 1/T. Successful searchers are paired
     uniformly at random among themselves (one uniformly chosen odd one out stays unpaired this round).
  2. **Hunt.** Each pair catches a stag of value S = 1 (no failure). One member, chosen with probability ½,
     is the catcher; it keeps 1 − s_catcher, the partner receives s_catcher. Each unpaired agent (including
     failed searchers and the odd one out) receives h.
  3. **Leave (choice arm only).** The non-catcher compares the offer just received with its own a; if
     s_catcher < a, the pair dissolves and both become unpaired. Catchers never leave.
- **Fitness:** total income over the H rounds plus 0.01 × the population mean income. If total income is
  0 for everyone, parents are drawn uniformly.
- **Reproduction:** N offspring, each from a parent drawn from the whole population with probability
  proportional to fitness (global competition, Wright-Fisher). Each trait mutates independently with
  probability μ = 0.01: add Normal(0, 0.05), clip to [0, 1].
- G = 2,000 generations.
- **No-choice arm (control):** identical, except step 3 never runs: a pair, once formed, lasts the rest of
  the generation.

**T is nominal.** m = 1/T is each searcher's success chance; the realized chance of being matched also
depends on how many agents are unpaired (with few searchers, both must succeed, and a pool of two can only
reunite). So the thresholds below are in nominal T/H for this matching rule. The model records, per run,
the realized mean rounds from becoming unpaired to being paired again, and the share of new pairs that
reunite two agents who were partners earlier in the same generation.

### Grid

- T ∈ {1, 5, 20, 50, 100}, so nominal T/H ∈ {0.01, 0.05, 0.2, 0.5, 1}.
- h ∈ {0, 0.1, 0.3} (h/S, S = 1).
- Start ∈ {exploiter: s = 0.05, a = 0 for everyone (primary); fair: s = 0.5, a = 0.45 for everyone;
  random: s and a each drawn U(0, 1) independently per agent}.
- Arm ∈ {choice, no-choice}.
- 20 seeds per cell (seeds 0-19, shared across cells). 5 × 3 × 3 × 2 × 20 = 1,800 runs.

**What each start asks.** From the exploiter start, a rare generous offer lowers the catcher's income, and
a rare high threshold breaks pairs while there is not yet a better partner to find; selection near that
start can oppose both changes fairness needs. So the exploiter start tests *emergence* by small mutations,
the hardest case. The random start tests emergence from wide standing variation. The fair start tests
*maintenance* once thresholds already punish undercutting. A failure from the exploiter start alone does not
show that partner choice cannot produce fairness in general.

### Outcome per run

**Partner share** (primary) = population mean s, averaged over generations 1,801-2,000. A run is **fair**
if ≥ 0.4, **exploited** if ≤ 0.25.

Also recorded, not tests: the **catch-weighted share** (mean offer actually received per catch, same window;
partner choice can change which types get paired, so it can differ from mean s), its spread across catches,
mean a, fraction of rounds paired, break-ups per generation, realized rematching delay, reunion share.

### Validity check V1 (registered)

In the no-choice arm, pairing and pair length do not depend on offers, and an agent's expected paired income
is (1 − s_own + s_partner)/2, so lower own offers are favoured. **V1:** every no-choice cell's mean partner
share over its 20 seeds is ≤ 0.25. If V1 fails in any cell, the code is inspected once for a bug (any fix
disclosed in RESULTS with the failing numbers) and V1 is re-run on all cells. If it still fails, with or
without a fix, the control does not separate and the screen is **INVALID**. V1 gates every verdict below.

V2 (descriptive): choice arm, fair start, partner share next to step 1's value at the same T, H = 100, h.
Only rough agreement is expected (nominal vs realized matching, fixed vs geometric horizon, rotating roles).

### Compute budget

Expected about 1 h on the available cores (independent runs in parallel, OMP / MKL threads = 1). **Kill
rule:** after the first 60 runs, if the projected wall time for all 1,800 exceeds 4 h, stop: **NO VERDICT
(compute)**, reported; no grid change without a new agreement with the user.

### Threshold x\*(start, h)

For each start and h, the seed count fair out of 20 is reported at every T/H. **x\*(start, h)** is the
largest T/H on the grid such that the choice arm is fair in ≥ 16 of 20 seeds there *and* at every smaller
T/H on the grid. If T/H = 0.01 fails, x\* = none (an isolated success at a higher T/H is reported but does
not count). x\* = 1 means the whole grid qualifies.

## Verdict (registered; step 2 only)

- **PASS (emergence):** V1 holds and x\*(exploiter, h) ≥ 0.05 for all three h. Partner choice alone turns an
  exploitative market fair at low search cost. A PPG module is then worth proposing (its own
  pre-registration) in which the catcher's split is a learned action and hunters can recognise and refuse
  or leave partners.
- **MARGINAL (needs variation or only maintains):** V1 holds, PASS fails, and x\*(random, h) ≥ 0.05 or
  x\*(fair, h) ≥ 0.05 for all three h. Reported as such; no module without a new agreement with the user.
- **KILL:** V1 holds and neither PASS nor MARGINAL. Leaving a partner, in this simple form, does not
  support fair splits even when search is cheap; the PPG fairness module is not built on this mechanism.
- **INVALID:** V1 fails (above). **NO VERDICT (compute):** the kill rule above.

**Hard stop:** this screen is run once. Whatever the verdict, the result goes into `RESULTS_SCREEN.md` and
the line gets no further tweak rounds of the step-2 model.

## Step 3: what PPG offers a partner market (descriptive, no verdict role)

PPG has no lasting pairs: each catch assembles a party from whoever touched the deer within the window. Its
catch intervals and lifetimes therefore do not measure step 2's search cost or retained-partner horizon,
and step 3 is not used to place PPG on x\*. It answers a design question for a possible module: **do the
same hunters meet again often enough for choosing partners to matter?**

**Checkpoints:** PredPreyGrass `deer_stag_hunt`, section 2 touch-rule runs `touch_1`, `touch_2`, `touch_3`,
final checkpoints (iteration 1000), the section 2.2 evaluation settings (50 episodes per run, the run's own
config). A new eval-only script logs every catch with physics step, deer class, deer energy, participant
IDs and each participant's realized energy gain after the cap, and each predator's death step with cause
(starvation vs episode end). No change to `environment.py`, no training.

**Reported per run** (all descriptive):

- Joint catches (two or more participants), split by adult and middle deer.
- **Repeat-partner rate:** of joint catches, the share in which at least two participants have caught
  together before in the same episode; and, per predator pair that ever co-catches, the number of
  co-catches (distribution).
- **Co-catch cadence:** per predator, physics steps between its consecutive joint catches (Kaplan-Meier
  median, with death and episode end as censoring, not dropped).
- **Solo income rate:** energy per physics step from catches made alone, over all predator-alive time
  including time with no catches; and the realized energy per participant from a joint adult catch.

If the repeat-partner rate is near zero, a PPG module would first need repeated encounters (for example
recognisable individuals and a smaller or more structured population) before partner choice could act;
that would be recorded as a design requirement, not a test result.

## Known limits

- Partner choice explains fair splits within cooperating pairs, not help to strangers met once; that is
  reputation (indirect reciprocity), a separate mechanism.
- Step 2's agents follow fixed inherited rules; learning agents could do better or worse. Step 2 shows
  whether this market can support fairness, not that PPG agents would learn it.
- The leave rule uses only the last offer received (memory 1, also late in a generation) and only the
  non-catcher can leave; richer memory or two-sided leaving might change x\*. Not tested here.
