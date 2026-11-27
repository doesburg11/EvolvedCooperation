# Rung 5b: empathetic judging with mutation, pre-registration DRAFT (2026-11-27)

**Status: draft, not agreed.** Proposed after rung 5a′ (private views without mutation) was met (94/100) and the
theory screen `THEORY_SCREEN_EMPATHY.md` (commit 5a2ee08). If agreed, this is an explicit, dated exception to the
ladder's earlier stops for this one step, like rung 5a′. Rung 5a's failure (45/100) and both bridge failures stand.

## Why

On the reordered ladder, private views are in place (rung 5a′) but only without mutation. With mutation, rung 5a
failed. In the bridge runs that failed, unconditional cooperators first rose at discriminators' expense, then
defectors rose. A candidate reason is that, under private views, a discriminator's justified refusal is often judged
bad by observers who see the recipient differently. **Empathetic judging** (Radzvilavicius, Stewart and Plotkin 2019,
*eLife* 8:e44269) removes the pre-flip assessment penalty for justified test-arm DISC refusals: the observer judges
the act using the donor's view of the recipient. Private views can still disagree (flips, missed observations).

## Change: one ingredient

Setting: rung 5a's exactly (equivalently rung 5a′ with mutation μ = 0.001 switched back on): N = 1,000, k = 10,
Wright-Fisher reproduction, b/c 3, s = 0.1, q = 0.8, o = 0.5, e = 0.1, a = 0.02, μ = 0.001, private views reset to
good at the start of every generation, start 10% ALLC / 80% DISC / 10% ALLD, 2,000 generations. **The only change:**
in the assessment of an unhelped act, each observer w uses the **donor's** view of the recipient, VT[r, d], instead
of its own view VT[r, w]:

- the donor's decision is unchanged (a consulting DISC reads its own view of the recipient; shuffled arm: of a
  uniformly random z other than d and r);
- every individual other than d and r observes independently with probability o; an observer sets its view of the
  donor to good if the donor helped, otherwise good iff VT[r, d] = bad, then flips it with probability a;
- VT[r, d] is read **before the act** (the act changes only views of the donor, so it cannot change VT[r, d]); it is
  read for every donor type (non-consulting DISC, ALLC, ALLD) and in the shuffled arm too, where it is the donor's
  view of the actual recipient, not of z;
- the donor and recipient do not observe; non-observers' views stay unchanged and can be stale; views are updated
  act by act in rung 5a's encounter order.

**Code.** A copy of rung 5a's model (`rung5b_empathy/model.py`): `apply_act` reads VT[r, d] in place of VT[r, w];
`check_act` uses the donor's pre-act view of the recipient (rec_before[d]) for every observer. **Checks:** (i) in every
arm and for every donor type, each stored observer view satisfies bad ⇔ ((not helped) AND donor's view of the
recipient good) XOR flip; (ii) sanity rule, test arm, cooperators only: stored view bad ⇔ (execution failure while the
donor's view of the recipient is good) XOR flip, and ALLC never refuses intentionally. Any mismatch → invalid, as in
rung 5a. **Diagnostics keep the observer's own pre-act view** (rec_before[w]): the residual-disagreement counters
(rung 5a's intent_refusal_obs_recgood and shuffled_refusal_obs_recgood) still count observer-good recipients, so they
measure disagreement, not judging. A copy of rung 5a's runner (`rung5b_empathy/run.py`) with its own data folder,
seeds 3400-3499 and the main condition only (200 jobs, frozen; the benchmark projects these 200 runs), plus the
reported summaries below. A copy of rung 5a's runner
(`rung5b_empathy/run.py`) with its own data folder, seeds and conditions. Everything else is rung 5a's code, and
rung 5a's in-model checks against the stored views apply with the empathetic rule.

**Tests before the run.** An independent plain-Python reference of the assessment rule on scripted acts (all four
combinations of donor's and observer's view of the recipient, helped and refused, flips, the shuffled case with the
donor's view of z differing from its view of r, a stale view after a missed observation, generation reset). The model
must match it, and its checks must catch a deliberately reverted rule (observer's own view), a wrong index
(VT[d, r]) and an update of a non-observer. Rung 5a's remaining tests are retargeted to the copied
model; tests that encode the observer's-view rule (rung 5a's reference and the expectation it implies) are replaced by
the empathetic reference, and production `encounter` is tested for every donor category, both arms, flips and the
counters.

## Test and criteria: exactly rung 5a's

Main condition only: test and shuffled arms, 100 runs each, **seeds 3400-3499** (fresh; streams reset per run; arms
paired by seed identifier, not by matched encounters). **Met** if at least 80/100 test runs meet both endpoints
(cooperators ≥ 0.8 at generation 500, and mean cooperators ≥ 0.8 over generations 1,501-2,000) and the shuffled arm
meets each endpoint in at most 20/100. Rung 5a's validity rules, in-model checks, benchmark gate (40 CPU-hours,
projected from seed 9999 over 100 generations, trajectory not read), heartbeat watcher and one-repair rule.

**Theory screen (mean field):** cooperators 0.988 at generation 500 and over generations 1,501-2,000; final ALLC /
DISC / ALLD 0.075 / 0.913 / 0.012; shuffled 0.014. Rung 5a's own screen predicted 0.932 and the simulation gave
45/100, so this is not a forecast of the pass rate.

**Reported, not tested:** the three criterion counts; per run and arm DISC_g500 and DISC_window and the counts with
DISC ≥ 0.5; mean ALLC and ALLD over the window; runs ever below 0.5 cooperators; the generation of the first drop
below 0.8 after generation 500; rung 5a's diagnostics (help rate; good-view shares over generation 1); and the
**residual disagreement** (test arm): the share of observations of an intentional DISC refusal in which the
observer's own view of the recipient was good (rung 5a's disagreement penalty, now not used for judging); in the
shuffled arm, rung 5a's separate shuffled ratio (observer-good actual recipients). Ratios with a zero denominator
are reported as undefined.

## Hard stop

This one step. A valid **not met** ends it; no other settings, seeds or conditions. A pass puts empathetic judging
with mutation on the reordered ladder as rung 5b; the next rung (gossip, or the ecological rungs) needs a new
proposal and the user's agreement.

## Interpretation limits

A pass would show maintenance of cooperative strategies under private views with recurrent mutation **when observers
judge by the donor's view**, from a cooperative start over 2,000 generations at this setting. It assumes observers
know the donor's view of the recipient (the paper's empathy), a strong informational assumption that is not
modelled as a cost or a learned trait. It would not show recovery, spread from rare, indefinite stability, or
that empathy evolves. A valid failure means this fixed setting did not meet the registered maintenance-and-control
criterion; the report states which component failed.

## Forecast (mine, before any data)

Met: 55%. If not met, failures follow the bridge's two-phase pattern (ALLC rising before ALLD): 60%.
