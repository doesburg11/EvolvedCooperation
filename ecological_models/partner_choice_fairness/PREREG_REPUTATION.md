# Partner choice with reputation: theory screen, pre-registration (2026-11-26)

**Status: agreed with the user 2026-11-26 (about 16:10 CET), before any code for the reputation step and before
any reputation run.** Revised once the same day after a Codex review (gpt-6.1-sol, medium), still before any
code: T = 1 now enters a mechanism verdict, with a separate gate for a PPG module; draw and update rules fixed;
V2 compares full trajectories; step-1 scope narrowed. The only computation so far is the step-1 closed form
(recomputed by Codex: all entries agree).

## Why

The partner-choice screen (`PREREG_SCREEN.md`, `RESULTS_SCREEN.md`, same day) gave the registered verdict KILL:
with anonymous random rematching, leaving a stingy partner did not make splits fair, and did not keep them fair.
A descriptive reading was that nothing made a fair partner easier to find than a stingy one. The smallest next
step (one ingredient added to the model that failed) is **reputation**: searchers can see a candidate's past
offer before pairing and refuse. This is partner choice informed by reputation (Baumard, André & Sperber's
mutualistic account of fairness), not reputation-gated helping, which this repo already covers
(`threshold_models/indirect_reciprocity_discriminators`: q > c/b reproduced; `moran_models/.../indirect_reciprocity`;
`ecological_models/nowak_mechanisms/indirect_reciprocity`).

**Question:** if a searcher sees a candidate partner's last offer with probability q and can refuse, does fair
sharing emerge or hold in the market, and from what q?

## Model (changes to `market.py`; everything else as in `PREREG_SCREEN.md` step 2)

- **Reputation:** an agent's last offer as catcher in the current generation (set at each catch it makes);
  unknown at the start of each generation until its first catch.
- **Known** means the agent has made at least one catch this generation; the record is public (every observer
  sees the same value) and is updated after every catch it makes, including a catch after which the pair
  dissolves, and kept until the generation ends. Because s is fixed within a generation, a known reputation
  equals the agent's current offer exactly. Observers keep no memory of their own.
- **Matching:** successful searchers are paired at random as before (same draws as before). Then, for each
  candidate pair (i, j) in pairing order, two independent draws are made when q > 0, always both, whatever the
  first shows: i observes j with probability q, then j observes i with probability q. An observer refuses if the
  observed agent is known and its reputation is below the observer's own a. If either refuses, the pair is not
  formed and both stay unpaired this round (they earn h; no second attempt this round). Unknown reputations are
  accepted. Refusals are counted per refused candidate pair.
- **Hunting** happens in the same round as a pair forms (as in `market.py`); the leave rule then applies as
  before, so an accepted partner can still leave after a low offer.
- **Leave rule, payoffs, fitness, global Wright-Fisher reproduction, mutation, N = 200, H = 100, G = 2,000:**
  unchanged.
- **q = 0 is the KILLed model exactly.** With q = 0 the code makes no extra random draws and every existing draw
  keeps its place and order, so q = 0 runs must reproduce, seed for seed, the corresponding runs of the earlier
  screen (`data/screen_runs.csv` and `data/screen_traj.npz` as committed in 1e5638a).
- **No-choice arm (control):** as before, no leaving and no refusal (q has no effect, so it is run once per T,
  h, start).

## Step 1: closed form (done, before this file)

A fully stingy mutant (offer s' = 0) in a resident population with offers 0.5 and thresholds a = 0.45 (the fair
start), mutant's own threshold 0.45. Once its reputation is known, each match it gets is refused with
probability q, so it is matched with probability p = m(1 − q) per round of search (m = 1/T; pool-size effects
ignored). When paired, it is catcher with probability ½ per round: it keeps 1, the partner leaves; otherwise it
receives 0.5 and the pair stays. So a paired spell lasts 2 rounds on average and pays 0.75 − s'/2 per round, and
each search lasts on average (1 − p)/p rounds paying h. Residents earn about 0.5 per round. The mutant does better
iff 0.5 − s' > (0.5 − h)(1 − p)/p; for s' = 0, iff p > (0.5 − h)/(1 − h), i.e.

**q < q_inv = 1 − (0.5 − h) / ((1 − h) m).**

| | T = 1 | T = 5 | T = 20 |
| --- | --- | --- | --- |
| h = 0 | 0.500 | never (even q = 0) | never |
| h = 0.1 | 0.556 | never | never |

**Scope of step 1.** This is a long-run renewal approximation after the mutant's reputation is known: a new pair
hunts in the round it forms (as in `market.py`; the earlier screen's step 1 assumed payment from the next round),
and it ignores generation boundaries (H = 100), the initial search, residents' own search costs and pool-size
effects (with only two searchers, both must succeed: m²(1 − q) rather than m(1 − q)). It concerns only a fully
stingy mutant against a fair, choosy resident population; it does not cover smaller undercuts, threshold
evolution, or emergence from an exploitative start, and it does not predict the evolutionary q\*.

**Expectation (stated in advance, not derived).** At T ≥ 5, leaving alone already makes a fully stingy mutant lose,
so step 1 gives reputation no extra role there against such mutants; in the earlier screen fairness was lost
there while thresholds declined (descriptive reading). Reputation adds selection on thresholds only while offers
vary. At T = 1, where leaving is no punishment, refusal does cost the refused pair a round, and step 1 suggests a
role above q of about 0.5-0.56. Expected: if fairness is supported anywhere, mainly at T = 1 and high q; no
module gate.

## Step 2: grid

- q ∈ {0, 0.25, 0.5, 0.75, 1}; T ∈ {1, 5, 20}; h ∈ {0, 0.1}; start ∈ {exploiter, fair, random} (as defined in
  `PREREG_SCREEN.md`).
- Choice arm with reputation: 5 × 3 × 2 × 3 = 90 cells. No-choice arm: 3 × 2 × 3 = 18 cells. 20 seeds each
  (0-19). 2,160 runs.
- **Outcome (primary, as in the earlier screen):** partner share = population mean offer s over generations
  1,801-2,000; a run is fair if ≥ 0.4. The verdict is therefore about the offers agents carry. Reputation changes
  who hunts, so realized exchanges can differ: the **catch-weighted share** (mean offer received per catch) is
  reported for every cell next to it, and a cell where it is ≥ 0.4 while mean s is below is described as "fair
  exchanges among a subset", not counted as fair. Also recorded: mean a, fraction paired, break-ups,
  refusals per generation.

## Validity checks

- **V1:** every no-choice cell's mean partner share ≤ 0.25.
- **V2:** every q = 0 choice run reproduces the corresponding earlier run (same T, h, start, seed; baseline files
  at commit 1e5638a): per-generation mean s and mean a identical to the stored float32 trajectories in
  `screen_traj.npz` (exact equality after casting to float32), and partner share, mean a, catch-weighted share,
  fraction paired and break-ups equal to `screen_runs.csv` to 1e-12.
- If V1 or V2 fails: one inspection for a bug (any fix disclosed with the failing numbers), then all cells re-run;
  a second failure makes the screen **INVALID**.

## Verdict (registered)

For each start, T and h, **q\*** = the smallest q on the grid such that the cell is fair in ≥ 16 of 20 seeds at
that q and at every larger q on the grid; none otherwise. (So q\* exists only if q = 1 qualifies; it is a robustness
threshold on the grid. Seed counts at every q are reported, including successes at intermediate q that do not
persist.)

**Mechanism verdict** (all T):

- **EMERGES:** V1 and V2 hold, and for some T, q\*(exploiter, T, h) exists for both h. (The T values where it
  holds are reported.)
- **MAINTAINED ONLY:** V1 and V2 hold, EMERGES fails, and for some T, q\* exists for both h from the fair start or
  from the random start.
- **KILL:** V1 and V2 hold, neither of the above.
- **INVALID:** as above. **NO VERDICT (compute):** if, after the first 60 runs, the projected wall time exceeds
  1 h (expected: about 1 min), the run stops.

**PPG module gate** (separate): a PPG module with recognisable hunters, a seen-offer channel and a learned split is
worth proposing (its own pre-registration) only if EMERGES holds at T = 5 or T = 20 (PPG hunters wait hundreds of
physics steps between joint catches, `RESULTS_SCREEN.md` step 3, so instant rematching does not describe PPG).
EMERGES only at T = 1 is reported as a mechanism result without a module.

**Hard stop:** run once; results go into `RESULTS_REPUTATION.md`; no tweak rounds of this model.

## Known limits

- Reputation here is exact, free to observe and shows only the last offer; gossip, errors and deception are
  left out.
- Thresholds are used both to leave and to refuse; separate traits are not tested.
- Agents follow inherited rules; learning agents in PPG might behave differently.
