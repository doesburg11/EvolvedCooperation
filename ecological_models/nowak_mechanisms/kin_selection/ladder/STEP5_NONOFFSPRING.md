# Step 5, help among non-offspring relatives, in the empty-site islands: pre-registration (2026-11-26)

**Status: agreed with the user 2026-11-26 (about 17:21 CET), before any model change or test run.** Revised once after a Codex review
(gpt-6.1-sol, medium, 2026-11-26): singleton-class rule, what the control preserves, a measured relatedness check
on the gift routes, the control's theory stated as an approximation, b/c 5 screened, power proxy recomputed,
completion and reporting rules. Rung 1 of the kin-ladder close-out
agreed with the user on 2026-11-26 (at most two rungs in the empty-site islands, one attempt each, then a hard stop
and a write-up). Follows `theory/THEORY_SCREEN_NO_OFFSPRING.md` (commit 21ef227).

## Why

`STEP5_EMPTY_SITES.md` met step 5 for help to patch-mates, but left the sub-case open: the arm that excluded the
donor's own offspring (NO14) reached the endpoint in 14 of 20 runs (bar 15) and ended above neutral in 11 of 20
pairs (bar 16). The theory screen found that own offspring, 2-7% of a donor's patch-mates, carry about a third of
its patch relatedness, so at b/c 14 the selection gradient on non-offspring help is 0.12 to 0.36 times T14's on
the way to the endpoint, and it reaches zero near h = 0.8. At **b/c 28** the help is favoured at every screened level of h (actual
c/b 0.036 against a lowest break-even of 0.047, ratio 0.76) with a gradient at least T14's from h = 0 to 0.6.

A positive result would be the first in the table's second block (population size not fixed, births need free
space) for help **among non-offspring relatives** (goal B's sub-case), against a control that breaks the link between giving and recipient relatedness.
It would not add energy, limited food or movement.

## Model

The step-5 island model, unchanged (`empty_sites_model.py`; `STEP5_EMPTY_SITES.md`, section "Model"): P = 1,000
patches of n = 10 sites; death rate k = 0.5; birth rate f_j = 1 − c·h_j + gifts received; offspring stay home if
the parent's patch has at most 5 breeders, otherwise go to a uniformly random patch, and settle only on an empty
site; clonal inheritance, h mutates with probability 0.02 by N(0, 0.04) clipped to [0, 1]; neutral marker mutation
0.001; start: each site occupied with probability 0.5, h ~ N(0.05, 0.02) clipped.

**Gift rules.** Each donor d gives b·h_d in total and always pays c·h_d. Its *eligible* patch-mates are the other
breeders of its patch that are not its own immediate offspring (the existing `nonoff` mode; its parent, siblings,
grandchildren and more distant kin are eligible). A donor with no eligible patch-mate is *locally ineligible*: its
gift is lost, in both arms with this rule.

- **`nonoff` (test):** the gift is shared equally among d's eligible patch-mates.
- **`classpool` (control, new):** the gift of a locally eligible donor goes into a pool for its patch class i (the
  number of breeders in its patch). Each breeder j in a class-i patch p receives
  gift_j = (D_i − D_p) / (M_i − i), where D_p is the summed b·h of p's locally eligible donors, D_i the sum of D_p
  over all class-i patches, and M_i the number of breeders in class-i patches. If p is the only class-i patch, its
  donors' gifts are lost. The two kinds of loss (locally ineligible; no other patch of the class) are recorded
  separately. This is the expectation of giving to the same number of breeders in a random other patch of the same
  class.

**What the control keeps and changes.** At a given population state, for every class with at least two patches,
it keeps the class's total delivered gift and its mean fecundity per breeder, and the same donors are locally
ineligible. It changes how gifts are spread within the class (no gift stays in the donor's own patch), so the
fecundity variance, the local feedback of a helping patch on itself and the demography that follows can differ.
It removes delivery within the donor's patch; recipient relatedness is then expected to be near the between-patch
level but is not zero by construction (relatives can live in other patches of the same class), so it is measured
(below). Because the control changes several things, a test-control separation is read as *consistent with* kin
selection (the site's convention for such controls), not as relatedness isolated.

**Theory (weak-selection, infinite-island approximation; `theory/no_offspring_screen.py`, two seeds, eight
resident levels h = 0 to 1).**

- Test rule at b/c 28 (b = 0.14, c = 0.005): break-even c/b 0.095, 0.075, 0.062 and 0.047 at h = 0, 0.3, 0.6 and
  1, so helping is favoured at every screened level (actual c/b 0.036, 0.76 of the lowest break-even); gradient
  per unit h per time unit +0.0041 (h = 0), +0.0016 (0.6), +0.0007 (1).
- Test rule at b/c 5 (b = 0.025, screened): break-even 0.095 to 0.085, actual c/b 0.2 (2.35 times the lowest);
  gradient −0.0013 at every screened level.
- Control: with recipients in unrelated patches, the exported gift has a negligible effect on the donor's lineage,
  and the local effect is the cost alone, including its demographic effect on the donor's patch:
  W_i = −c (A_i + B_i). With the NO28 resident values this gives a gradient of about −0.0025 to −0.0022 at every
  screened level (Codex's recomputation). This is an approximation: remote relatives and the control's own
  resident distribution are ignored.

## Stage 0: checks (before any test arm)

- **Existing modes unchanged:** with the new mode added, the modes `none`, `patch`, `nonoff` and `global` give
  byte-identical output to the code of `STEP5_EMPTY_SITES.md` (commit 909255f) at the same seeds (unit test, and
  rerun at the launch of Stage M). The step-5 Stage 0 results (demography and relatedness against the theory)
  therefore carry over.
- **Control mode, unit tests:** at a fixed state, for classes with at least two patches, the class total and mean
  gift per breeder equal the test rule's; for a singleton class, nothing is delivered and the loss is counted as
  such; no gift reaches the donor's own patch (checked donor by donor); locally ineligible donors as in `nonoff`;
  fecundity bound f ≤ 1 + b (the `nonoff` bound 1 + b·(n − 1) is kept for `nonoff`).
- **Dynamic cache tests:** after random sequences of births and deaths, the cached per-patch and per-class sums
  equal a full recomputation; class transitions 0↔1 and 5↔6; classes with 0, 1 and 2 patches; eligibility changes
  when an own offspring settles or dies; chunk restarts; the fecundity used in acceptance equals the one recorded
  at sampling.
- **Power proxy (a planning proxy, not a power calculation for the 15-of-20 and 16-of-20 rules):** as in
  `STEP5_EMPTY_SITES.md` 0c, t* = the first sampled time at which 0.00164·∫V (0.00164 = the smallest NO28 gradient
  on 0.05-0.60, at h = 0.6) reaches 0.55, from the Stage 0c variance series stored in
  `data/step5_empty_sites/stage_0_summary.json` (every 1,000 time units). Passes if t* ≤ 25,000. Computed on that
  series: 13,000 (T14's coefficient on the same series: 14,000; the registered 13,800 used the 100-unit series).
- **Runtime:** one benchmark run per arm (seed 999, 5,000 time units, only events and CPU time read); the
  projected Stage M total (80 runs) must fit in 8 CPU-hours.

**Gate:** all checks pass. **If any fails:** stop and report; Stage M is not run.

## Stage M: the test

20 seeds per arm (100-119, shared across arms; not the seeds of `STEP5_EMPTY_SITES.md`), 100,000 time units
(about 50,000 generations), sampled every 1,000, c = 0.005 except N0.

| Arm | b | Gift rule | Role |
| --- | --- | --- | --- |
| **N0** | 0 (c = 0) | none | neutral reference (drift and mutation only) |
| **NO28** | 0.14 | `nonoff` | test |
| **XC28** | 0.14 | `classpool` | control: relatedness removed |
| **NO5** | 0.025 | `nonoff` | below the theory's threshold |

**Measures (as in `STEP5_EMPTY_SITES.md`):** final mean h = mean h over breeders, averaged over the 10 samples after
90,000 (an extinct run has none). **Endpoint:** final mean h ≥ 0.60. **Viable:** at least one breeder at 100,000.
Recorded every 1,000 time units: mean and variance of h, occupancy, patch-type distribution, marker relatedness,
mean fecundity, the two loss shares, class sizes (patches per class), and (NO arms) the share of a donor's
patch-mates that are its own offspring.

**Gift-route relatedness (contrast check).** At every sample, for each delivering donor d with delivered gift g_d:
q_d = identity between d's marker and its recipients' (NO arms: the mean over its eligible patch-mates, each with
its share; XC28: the mean over 10 recipients drawn from the breeders of other patches of its class), and
q_ref,d = identity between d's marker and that of 10 breeders drawn uniformly from all patches other than d's.
Pooled over the samples after 50,000 and over the seeds of an arm: Q_route = Σ g_d q_d / Σ g_d and
Q_ref = Σ g_d q_ref,d / Σ g_d (numerators and weights summed), R_route = (Q_route − Q_ref)/(1 − Q_ref). The
reference uses the same donors and weights, so a control whose recipients are no more related than random
breeders in other patches gives R_route near 0. **Check:** R_route(NO28) − R_route(XC28) ≥ 0.02. Theory gives
about 0.11 for NO28's route relatedness at h = 0, 0.075 at h = 0.6 and 0.06 at h = 1 (fixed-trait screen), and
about 0 for XC28. This is a check that the arms differed in recipient relatedness as intended, not of the code
(which the Stage 0 tests check); both values are reported.

**Validity:** every run must complete (a crash or interruption stops the stage; it is reported, not rerun), with
every sample time present and a finite final mean h for every viable run. An extinct run does not
reach the endpoint. An arm with fewer than 18 of 20 viable runs is not interpretable. **Paired comparisons** (seed by
seed): a pair counts for the hypothesis only if both runs are viable and the difference has the predicted sign; a
pair with an extinct run counts against it.

**Classification, in this order:**

1. N0, NO28 or XC28 not interpretable → **not interpretable**.
2. The gift-route relatedness contrast is below 0.02 → **not interpretable: no relatedness contrast between the
   arms' gift routes**.
3. XC28 at the endpoint in more than 2 of 20 → **not met: the control did not separate**.
4. NO28 at the endpoint in at least 15 of 20 **and** final mean h of NO28 above N0 in at least 16 of 20 seed pairs
   → **met: among non-offspring relatives**; otherwise **not met**.

**H2 (below the threshold, reported separately):** NO5 and N0 interpretable and NO5's final mean h below N0's in at
least 16 of 20 pairs → **supported**; either not interpretable → **not interpretable**; otherwise **not supported**.
Together with a met NO28 this supports the predicted directions at the two tested ratios, not the location of the
threshold.

**H3 (control direction, reported separately):** XC28 and N0 interpretable and XC28's final mean h below N0's in at
least 16 of 20 pairs → **supported** (theory: the control is cost-only); either not interpretable → **not
interpretable**; otherwise **not supported**.

The 16-of-20 rules are registered replication criteria, not exact sign tests: shared seeds give reproducible
pairing, not matched event histories.

The endpoint counts of every arm are reported whatever the classification.

**Site table:** met → a second-block row "5 (empty-site islands, own offspring excluded)" marked ✓, worded
*consistent with* kin selection among non-offspring relatives; not met (including "the control did not separate")
→ that row marked ✗; not interpretable, a failed Stage 0 or a stopped Stage M → the row marked – with the reason.
The earlier step-5 row is unchanged in every case.

**Interim check (at 10,000 time units), from progress files only (time reached, breeders alive), never h:** stop and
report if any run has crashed or stopped advancing, or the projected finish exceeds the budget. Extinctions are not
a kill reason.

**Hard stop:** one attempt; no other b, c, n, k, switches, arms or seeds under this pre-registration. This is rung 1
of the two agreed rungs.

**Before Stage M (an implementation amendment, as A1 of `STEP5_EMPTY_SITES.md`):** code hashes of model, runner and
theory frozen; the regression baseline (commit 909255f) and output paths named; crash markers and a refusal to
relaunch, as in the earlier runner.

**Predictions (mine, before any data):** Stage 0 passes: 90%. Verdict "met: among non-offspring relatives" (the full
classification, control separation included): 60% (the neutral arm drifts widely, 8 of 20 above 0.60 in the earlier
test, so the paired bar of 16 of 20 is the harder one). XC28 at or below 2 of 20: 90%. Manipulation check passes:
85%. H2 supported: 85%. H3 supported: 70%.

## What this would and would not show

A positive result is costly help to non-offspring patch-mates spreading from a low-helping start against a control
that removes relatedness (and the patch's own boost with it), in a population whose size is not fixed and whose
births need free space: step 5 for goal B's sub-case, in a ported published model. The islands are an abstraction
of space; there is no energy, limited food, starvation or movement; dispersal follows the paper's fixed ESS switch.
Recipients are the donor's patch-mates other than its immediate offspring (its parent, siblings, grandchildren and
more distant kin); relatedness comes from limited dispersal, not from kin recognition. A met result would not show
that relatedness alone caused the spread, locate the threshold, or show that helping rose steadily.

## Amendment A1 (2026-11-26, implementation, before Stage 0 and any registered run)

Implementation decisions after two Codex code reviews (gpt-6.1-sol, medium) of `empty_sites_model.py`,
`run_nonoffspring.py` and `tests/test_nonoffspring.py`; none changes a registered rule.

- **Model.** New gift mode `classpool` (4) with per-patch and per-class caches, updated around every death and
  settled birth and rebuilt from scratch at every sample. The largest gap found at the rebuild is recorded (column
  `cache_err`) and must be at most 1e-9 in every living sample. Gift-route statistics (columns 15-21) use their own
  xorshift random stream, so recording them leaves the main stream and every other column unchanged. A donor whose
  patch holds the only breeders left has no reference population and is skipped in the route statistics.
- **Regression baseline.** The model as validated in `STEP5_EMPTY_SITES.md` is frozen as `empty_sites_model_step5.py`
  (byte-identical to the file at 909255f). Stage 0 and the Stage M launch check that modes 0-3 give byte-identical
  output to it (full size, two seeds; also unit tests).
- **Runner.** `run_nonoffspring.py`. Raw output: `~/simulation_results/step5_nonoffspring/stage_m/`. Summaries:
  `data/step5_nonoffspring/`. Stage 0 runs the 24 unit tests (`tests/test_empty_sites.py`, `tests/test_nonoffspring.py`),
  the byte-identity check, the power proxy and the CPU benchmarks. Stage M refuses to start unless Stage 0 passed
  for the same code hash, and it refuses any relaunch once its launch record exists. A crash or a dead worker fails
  the stage. Smoke runs at reduced scale must use folders outside the registered ones.
- **Interim rule enforced.** `interim M` gives one verdict (STOP or ok) from progress files only: any failed run, any
  run without progress for 15 minutes, or a projected total above 8 CPU-hours (each run's process CPU time projected
  to its full length; finished runs at their recorded CPU time) → STOP. A systemd watcher runs it every 30 minutes
  from 30 minutes after launch and stops the runner on STOP.
- **Gift-route pooling.** Validation requires finite route statistics in every living sample of the gift arms;
  the analysis pools exactly the living samples after 50,000 (extinct samples have none).
