# Step 5, help to own offspring after they settle, in the empty-site islands: pre-registration (2026-11-26)

**Status: agreed with the user 2026-11-26 (about 18:27 CET), before any model change or test run.** Revised once after a Codex review
(gpt-6.1-sol, medium, 2026-11-26): control wording, the control prediction as an approximation, rung 1's A1
safeguards written out, pedigree edge cases, power-proxy specification, smoke blinding. Rung 2 of the kin-ladder close-out
agreed with the user on 2026-11-26 (two rungs in the empty-site islands, one attempt each, then a hard stop and a
write-up). Follows `theory/THEORY_SCREEN_OWN_OFFSPRING.md` (commit 87007a9). It mirrors rung 1
(`STEP5_NONOFFSPRING.md`, met 2026-11-26) and keeps its rules; the one change is the recipient rule.

## Why

The site's table has no second-block result (population size not fixed, births need free space) for kin
selection **through parental care** (goal A's sub-case): care for own young spread at every step up to energy and
limited food on an almost-full grid, but never once births needed free space (R5a-R8, the 2026-11-24 restart). In
the islands, a parent's grown offspring settle at home when the patch has at most 5 breeders. The theory screen found
that at any time about 19% of breeders have an offspring at home, at relatedness about 0.999, so help to them pays
above b/c about 5.4 (break-even c/b 0.185). At **b/c 14** (the values of the step-5 test T14) the actual c/b is 0.39
of the break-even, and the gradient (+0.0039 per unit h per time unit) is about 1.7 times T14's near h = 0 (and above T14's at every
screened level).

**What the help is.** A parent raises the fecundity of its own offspring that settled in its patch (breeders from
birth); the model has
no juvenile stage, so this is help to own offspring after they settle, not care for dependent young. Under the site's
broad definition (offspring included) a positive result counts as kin selection through parental care.

## Model

The step-5 island model, unchanged apart from the two new gift modes (`empty_sites_model.py`; `STEP5_EMPTY_SITES.md`,
section "Model"): P = 1,000 patches of n = 10 sites; death rate k = 0.5; birth rate f_j = 1 − c·h_j + gifts
received; offspring stay home if the parent's patch has at most 5 breeders, otherwise go to a uniformly random patch,
and settle only on an empty site; clonal inheritance, h mutates with probability 0.02 by N(0, 0.04) clipped to
[0, 1]; neutral marker mutation 0.001; start: each site occupied with probability 0.5, h ~ N(0.05, 0.02) clipped.

**Gift rules.** Each donor d gives b·h_d in total and always pays c·h_d. Its *eligible* recipients are the living
breeders r in its patch with parent[r] = id[d] (its own immediate offspring at home). A donor with none at home is
*locally ineligible*: its gift is lost, in both arms with this rule. Edge cases (unit tests): a dead parent gives
nothing and its gifts stop at once; a breeder that later takes the dead parent's site does not inherit its identity;
an offspring that dispersed to another patch gets no `ownoff` gift; an offspring whose random dispersal draw returns
it to the natal patch does qualify once it has settled. The dispersal switch uses the parent patch's occupancy
before the birth; eligibility uses the state after settlement.

- **`ownoff` (test, new):** the gift is shared equally among d's own offspring in its patch.
- **`offpool` (control, new):** as `classpool` in rung 1, with this eligibility: the gift of a locally eligible donor
  goes into a pool for its patch class i, and each breeder j in a class-i patch p receives
  gift_j = (D_i − D_p) / (M_i − i), where D_p is the summed b·h of p's locally eligible donors, D_i the sum over
  class-i patches and M_i the number of breeders in class-i patches; with only one class-i patch its donors' gifts
  are lost. The two kinds of loss are recorded separately.

**What the control keeps and changes.** As in rung 1: at a given population state, for every class with at least two
patches, it keeps the class's total delivered gift and its mean fecundity per breeder, and the same donors are locally
ineligible. It changes how gifts are spread within the class: it removes delivery within the donor's patch (so none reaches its
offspring at home), while dispersed offspring and other relatives in other patches of the same size remain possible
recipients. It also changes the local feedback and the demography that follows. Recipient relatedness is expected
near the between-patch level but is not zero by construction, so it is measured. A test-control separation is read as
*consistent with* kin selection, not as relatedness isolated.

**Theory (weak-selection, infinite-island approximation; `theory/own_offspring_screen.py`, four seeds, eight resident
levels h = 0 to 1, delivery and relatedness measured at the neutral state).**

- Test rule at b/c 14 (b = 0.07, c = 0.005): break-even c/b 0.185 at every screened level; actual 0.071 (ratio 0.39);
  gradient +0.0039 at every screened level.
- Test rule at b/c 3.5 (b = 0.0175): actual c/b 0.286 (ratio 1.54); gradient −0.00086.
- Control: ignoring effects on remote relatives and using OF14's resident demographic values, the local cost-only
  approximation W_i = −c (A_i + B_i) gives a gradient of −0.00245 to −0.00243. This supports H3 as a prediction, not
  as an exact result for the implemented control.
- Limits as in the screen: the neutral-state quantities are held fixed at every resident h, so the flat break-even is
  not evidence about demographic feedback; the test arm is the check at positive h.

## Stage 0: checks (before any test arm)

- **Existing modes unchanged:** with the new modes added, modes 0-4 (`none`, `patch`, `nonoff`, `global`, `classpool`)
  give byte-identical output to the code of rung 1 (commit 2558c37) at the same seeds, and modes 0-3 to the frozen
  step-5 code (unit tests, and rerun at the launch of Stage M).
- **New modes, unit tests:** `ownoff` delivers only to the donor's own offspring in its patch, equally, and loses the
  gift with none; a recipient's gift is at most b (one parent), so f ≤ 1 + b; `offpool` as `classpool` (class totals
  and means kept for classes with at least two patches, singleton classes deliver nothing, no gift to the donor's own
  patch, f ≤ 1 + b) with the `ownoff` eligibility; dynamic cache tests as in rung 1, including eligibility changes
  when an own offspring settles at home, dies, or its parent dies.
- **Power proxy (a planning proxy, not a power calculation for the classification rules):** as in rung 1,
  t* = the first sampled time at which 0.00388·∫V reaches 0.55 (0.00388 = the smallest OF14 gradient on 0.05-0.60),
  by the trapezoid rule on the Stage 0c variance series stored in `data/step5_empty_sites/stage_0_summary.json`
  (every 1,000 time units). Passes if t* ≤ 25,000. Computed: 8,000 (0.534 at 7,000, 0.637 at 8,000).
- **Runtime:** one benchmark run per arm (seed 999, 5,000 time units, only events and CPU time read); the projected
  Stage M total (80 runs) must fit in 8 CPU-hours.

**Gate:** all checks pass. **If any fails:** stop and report; Stage M is not run.

## Stage M: the test

20 seeds per arm (200-219, shared across arms; not the seeds of the earlier island tests), 100,000 time units, sampled
every 1,000, c = 0.005 except N0.

| Arm | b | Gift rule | Role |
| --- | --- | --- | --- |
| **N0** | 0 (c = 0) | none | neutral reference (drift and mutation only) |
| **OF14** | 0.07 | `ownoff` | test |
| **XO14** | 0.07 | `offpool` | control: delivery to other patches of the same size |
| **OF3.5** | 0.0175 | `ownoff` | below the theory's threshold |

**Measures (as in rung 1):** final mean h = mean h over breeders, averaged over the 10 samples after 90,000 (an
extinct run has none). **Endpoint:** final mean h ≥ 0.60. **Viable:** at least one breeder at 100,000. Recorded every
1,000 time units: mean and variance of h, occupancy, patch-type distribution, marker relatedness, mean fecundity, the
two loss shares, class sizes, and the share of donors with an own offspring at home.

**Gift-route relatedness (contrast check), as in rung 1:** for each delivering donor d with delivered gift g_d,
q_d = identity with its recipients (OF arms: the mean over its own offspring at home; XO14: the mean over 10 breeders
drawn from other patches of its class) and q_ref,d = identity with 10 breeders drawn uniformly from all patches other
than d's; pooled over the samples after 50,000 and over seeds, R_route = (Q_route − Q_ref)/(1 − Q_ref).
Pooling covers exactly the living samples after 50,000, including the living part of a run that later goes extinct;
route statistics must be finite in every living sample of the gift arms (validation), the pooled delivery weight must
be positive and Q_ref below 1. **Check:** R_route(OF14) − R_route(XO14) ≥ 0.02 (theory: about 1 for OF14, about 0
for XO14). A missing or undefined contrast counts as failing the check.

**Validity:** every run must complete (a crash or interruption stops the stage; it is reported, not rerun), with every
sample time present, a finite final mean h for every viable run and, for `offpool`, a cache error of at most 1e-9 in
every living sample. Fewer than 18 of 20 viable runs → the arm is not interpretable. **Paired comparisons:** a pair
counts only if both runs are viable and the difference has the predicted sign; a pair with an extinct run counts
against. The 16-of-20 rules are registered replication criteria, not exact sign tests (shared seeds give
reproducible pairing, not matched event histories). There is no registered paired OF14-versus-XO14 criterion.

**Classification, in this order:**

1. N0, OF14 or XO14 not interpretable → **not interpretable**.
2. The gift-route relatedness contrast is below 0.02, missing or undefined → **not interpretable: no relatedness
   contrast between the arms' gift routes**.
3. XO14 at the endpoint in more than 2 of 20 → **not met: the control did not separate**.
4. OF14 at the endpoint in at least 15 of 20 **and** final mean h of OF14 above N0 in at least 16 of 20 seed pairs →
   **met: through parental care (help to own offspring after they settle)**; otherwise **not met**.

**H2 (below the threshold):** OF3.5 and N0 interpretable and OF3.5's final mean h below N0's in at least 16 of 20 pairs
→ **supported**; either not interpretable → **not interpretable**; otherwise **not supported**. Supports the predicted
directions at the two tested ratios, not the location of the threshold.

**H3 (control direction):** XO14 and N0 interpretable and XO14 below N0 in at least 16 of 20 pairs → **supported**;
either not interpretable → **not interpretable**; otherwise **not supported**.

H2 and H3 are separate outcomes: the verdict can be met while either is not supported. The endpoint counts of every
arm are reported whatever the classification.

**Site table:** met → a second-block row "5 (empty-site islands, help to own offspring)" marked ✓, worded
*consistent with* kin selection through parental care, as help to own offspring after they settle (not care for
dependent young); not met (including "the control did not separate") → that row marked ✗; not interpretable, a failed
Stage 0 or a stopped Stage M → the row marked – with the reason. The earlier step-5 rows are unchanged.

**Interim rule (enforced, as rung 1's A1):** progress files only; STOP on any failed run, any run without progress for
15 minutes, or a projected total above 8 CPU-hours; a systemd watcher checks every 30 minutes from 30 minutes after
launch.

**Hard stop:** one attempt; no other b, c, n, k, switches, arms or seeds under this pre-registration. This is rung 2,
the last of the two agreed rungs; after it the kin line stops for the write-up, whatever the outcome.

**Before Stage M (an implementation amendment, as rung 1's A1):** code hashes frozen; the regression baselines
(commit 2558c37 for modes 0-4, the frozen step-5 code for modes 0-3) and output paths named; crash markers and a
refusal to relaunch. **Smoke checks** of the pipeline print no trait summaries, endpoint counts or verdicts (only
completion, timing and validation status); any accidental exposure is disclosed.

**Predictions (mine, before any data):** Stage 0 passes: 90%. Verdict "met" (full classification): 70% (larger
margin and gradient than rung 1's test; the neutral arm still drifts widely). XO14 at or below 2 of 20: 90%. Contrast
check passes: 95%. H2 supported: 80% (ratio 1.54, gradient smaller than rung 1's NO5). H3 supported: 75%.

## What this would and would not show

A positive result is costly help from parents to their own settled offspring spreading from a low-helping start against
a control that redirects the gifts outside the donor's patch (and with them the patch's own boost), reducing
gift-route relatedness if the registered contrast passes, in a population whose size is not fixed and
whose births need free space: step 5 for goal A's sub-case (through parental care), in a ported published model. It
would not be care for dependent young (the model has no juvenile stage). The islands are an abstraction of space;
there is no energy, limited food, starvation or movement; dispersal follows the paper's fixed ESS switch; inheritance
is clonal, so offspring are near-clones of their parent. A met result would not show that relatedness alone caused
the spread, locate the threshold, or show that helping rose steadily.

## Amendment A1 (2026-11-26, implementation, before Stage 0 and any registered run)

Implementation decisions after two Codex code reviews (gpt-6.1-sol, medium; the second found no remaining blockers)
of `empty_sites_model.py`, `run_ownoffspring.py` and `tests/test_ownoffspring.py`; none changes a registered rule.

- **Model.** New gift modes `ownoff` (5, the per-patch gift cache recomputed for the patch of every death and settled
  birth, as for `nonoff`) and `offpool` (6, the class-pool caches of rung 1 with the own-offspring eligibility).
  Column 21 records the share of breeders with an own offspring at home (modes 5 and 6 only). Column 22 records, at
  every sample, the largest gap between the cached gifts and a full recomputation: per breeder for `ownoff` (the
  cache is checked, not replaced), per patch and class for `offpool` (as in rung 1). It must be at most 1e-9 in every
  living sample of both modes.
- **Regression baselines.** The rung-1 model is frozen as `empty_sites_model_rung1.py` (byte-identical to the file
  at 2558c37). Stage 0 and the Stage M launch check that modes 0-4 give byte-identical output (all columns, route
  statistics on) to it, and modes 0-3 to the frozen step-5 code (columns 0-14).
- **Runner.** `run_ownoffspring.py`. Raw output: `~/simulation_results/step5_ownoffspring/stage_m/`. Summaries:
  `data/step5_ownoffspring/`. Stage 0 runs 32 unit tests (`tests/test_empty_sites.py`, `tests/test_nonoffspring.py`,
  `tests/test_ownoffspring.py`), the byte-identity checks, the power proxy and the CPU benchmarks, and stops at the
  first failed check. Stage M refuses to start unless Stage 0 passed for the same code hash and refuses any
  relaunch. A crash or a dead worker fails the stage. Smoke runs at reduced scale use folders outside the registered
  ones, and their analysis prints only validation status.
- **Interim rule.** As in rung 1: `interim M` gives STOP on any failed run, any run without progress for 15
  minutes, or a projected total above 8 CPU-hours. A systemd watcher runs it every 30 minutes from 30 minutes after
  launch and stops the runner unit on STOP (which stops its workers too).
