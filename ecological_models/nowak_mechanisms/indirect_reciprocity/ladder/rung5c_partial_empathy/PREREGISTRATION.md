# Rung 5c: partial empathy, pre-registration (2026-11-28)

**Outcome (2026-11-28): C1 (p 0.5) not met, 71/100; C2 (p 0.75) met, 92/100; shuffled 0/100 in both. See `RESULTS.md`.**

**Status: agreed with the user 2026-11-28, before the model copy or any run.** The user chose (2026-11-28) to test how much empathy is needed before the ecological
rungs, with a hard stop of **at most two steps**. If agreed, this is an explicit, dated exception to the earlier
stops for these two steps, like rungs 5a′ and 5b′; all earlier results stand.

## Why

Rung 5b′ (rung 5a's setting with full empathy: every observer judges an unhelped act by the donor's view of the
recipient) met 95/100 with mutation; rung 5a (no empathy) met 45/100. Full empathy is a strong informational
assumption. The theory screen `THEORY_SCREEN_PARTIAL_EMPATHY.md` (commit 2218a4e) shows most of the deterministic
margin already at partial empathy, but its margins have not predicted simulated pass rates.

## Change from rung 5b′: one parameter

Setting: rung 5b′'s exactly (rung 5a's setting: N = 1,000, k = 10, Wright-Fisher, b/c 3, s = 0.1, q = 0.8,
o = 0.5, e = 0.1, a = 0.02, μ = 0.001, private views reset each generation, start 10% ALLC / 80% DISC / 10% ALLD,
2,000 generations, test and shuffled arms, main condition only). **The only change:** each observation is
empathetic **independently with probability p**: an empathetic observer judges by the donor's pre-act view of the
recipient VT[r, d] (rung 5b′), a non-empathetic one by its own pre-act view VT[r, w] (rung 5a). The draw is per
observation, independent of the observation and flip draws; the same rule applies in both arms and for every donor
type (seed identifiers do not give matched encounters or masks); helped acts are good under both rules (before
flips). The extra draws change trajectories relative to earlier rungs.

| Step | p | Seeds | Runs only if |
| --- | --- | --- | --- |
| **C1** | 0.5 | 3500-3599 | (always) |
| **C2** | 0.25 if C1 is met; 0.75 if C1 is a valid not met | 3600-3699 | C1 has a valid verdict |

**Code.** A copy of rung 5b′'s model (`rung5c_partial_empathy/model.py`) with the empathy mask. **Exact draw:** the
mask is cleared every encounter; after the complete flip loop in `draw_masks`, immediately before it returns,
observers are visited in ascending index order and `empathetic[w] = np.random.random() < p` (same seeded stream);
non-observers stay false. The mask is passed through `encounter` to `apply_act` and `check_act`. **Checks:** (i) every stored observer view
satisfies bad ⇔ ((not helped) AND [VT[r, d] good if empathetic, else VT[r, w] good]) XOR flip, in every arm and for
every donor type; (ii) sanity rule, test arm, cooperators:
`view_good = (rec_before[d] == 1) if empathetic[w] else (rec_before[w] == 1)`; `refused = consulted and view_bad`;
`cause = (failed or refused) and view_good`; stored view bad ⇔ cause XOR flip; ALLC never refuses intentionally
(for a DISC refusal the donor sees the recipient bad, so empathetic assessment excuses it and own-view assessment
condemns it iff the observer sees the recipient good). `check_act`'s non-observer and recipient-unchanged checks are
kept. Any mismatch → invalid. Diagnostics keep the observer's
own pre-act view, as in rung 5b′. A new counter records the empathetic observations. A copy of rung 5b′'s runner
with P_EMP and SEEDS set per step, its own data folder per step and its own attempt marker; the step is a constant
(no CLI parameters), switched by a commit.

**Tests before the run.** Extend rung 5b′'s independent reference with the empathy mask; the model must match it on
scripted acts with mixed masks. p = 1 must reproduce rung 5b′'s model and p = 0 rung 5a's assessment on the same
scripted acts. Corruption tests: a mask ignored (always empathetic, never empathetic), mask applied to non-observers.
Sampling test (frozen: 20,000 encounters, N = 64, p = 0.5 and 0.25): conditional on observing, the empathetic share
is within 0.01 of p, its correlation with the flip status and between successive observations is below 0.02 in
absolute value, and non-observers are never empathetic.
Rung 5b′'s other tests retargeted.

## Criteria: exactly rung 5a's, per step

**Met** if at least 80/100 test runs meet both endpoints (cooperators ≥ 0.8 at generation 500, and mean cooperators
≥ 0.8 over generations 1,501-2,000) and the shuffled arm meets each endpoint in at most 20/100. Rung 5a's validity
rules, in-model checks, benchmark gate (40 CPU-hours per step), heartbeat watcher and one-repair rule. **Transition:**
C2 starts only after C1's 200 runs pass validation and C1 has a MET or NOT MET verdict; a technical stop in C1 does
not authorise C2. The C2 runner re-validates C1's saved 200 runs (at C1's settings) and derives its p from C1's
final verdict alone, never from individual criterion counts, diagnostics, forecasts or partial results. Every run row
records the step and p, and validation rejects a row whose p, seeds or step differ from the step's frozen values.

**Reported, not tested:** the realised empathetic share per arm; rung 5b′'s reported summaries (DISC shares and
counts, ALLC and ALLD, first drop below 0.8 after generation 500, per-run values, residual disagreement, help rate).

## What follows

The lowest p that met is carried into the next proposal (the ecological rungs). If neither step met, the next
proposal carries full empathy (p = 1, rung 5b′) and states that assumption. Either way the next rung needs the user's
agreement.

| C1 (p 0.5) | C2 | Reading |
| --- | --- | --- |
| met | p 0.25 met | 0.5 met; 0.25 met |
| met | p 0.25 not met | 0.5 met; 0.25 did not meet |
| not met | p 0.75 met | 0.5 did not meet; 0.75 met |
| not met | p 0.75 not met | 0.5 and 0.75 did not meet (p = 1, rung 5b′, met) |

These are results at two prespecified, adaptively selected settings with fresh seeds, not an estimated threshold;
a not met can also come from the shuffled-control criterion, which the report states.

## Hard stop

At most two steps (C1, C2). No other p, seeds or conditions.

## Interpretation limits

As rung 5b′: maintenance from a cooperative start over 2,000 generations at this setting, not recovery, spread from
rare or indefinite stability. Empathy is a fixed probability per observation (the realised share varies), not a cost, a trait or learned
inference.

## Forecasts (mine, before any data)

C1 (p 0.5) met: 60%. If C1 met, C2 (p 0.25) met: 35%. If C1 not met, C2 (p 0.75) met: 60%.
