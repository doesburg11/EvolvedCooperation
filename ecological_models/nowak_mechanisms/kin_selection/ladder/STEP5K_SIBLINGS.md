# Step 5K: sibling help with births into free space, kin association without viscosity (pre-registration DRAFT, 2026-11-25)

**Status: DRAFT, not agreed with the user, no Codex review, no code, no data.** Written while
`STEP5_EMPTY_SITES.md` (the Alizon and Taylor port) was running; nothing here changes that step, its arms or its
verdict. Only taken up if the user agrees.

**Update 2026-11-26, after that verdict (`RESULTS.md`, "Step 5 via empty-site islands").** Met for help to
patch-mates with own offspring not excluded (T14 20/20 at the endpoint, above neutral in 19/20); the sub-case that
excludes own offspring (NO14) was not separated (14/20 at the endpoint, above neutral in 11/20), and its control
(X14) changes several things at once. Help among non-offspring relatives alone (goal B) is therefore still open, and
that is the question this draft targets, with a control that changes only the relatedness of group mates. The draft
stays relevant; it is not started. The empty-site result also supports the direction-based criterion used here: its
neutral arm drifted from 0.05 to between 0.14 and 0.78 (8/20 above 0.60), so the endpoint alone did not separate
selection, and the registered seed-paired comparison did.

## Why

- **The restart showed a slow rise, not a reversal.** In the 2026-11-24 restart (`STEP5_RESTART.md`,
  `RESULTS.md`), own-offspring care in the test arm rose 0.07, 0.12, 0.28, 0.47 at updates 1000, 2000, 4000, 6000,
  above the drift arm (0.13) and above neighbour help in 17/20 seed pairs, but missed the fixed endpoint (0.60 at
  update 6000, 4/20). Turnover was about a fifth of K1's. That data stays closed (hard stop); re-scoring it with a
  new criterion would be post hoc. This step uses fresh seeds and fixes its criterion before any run.
- **Two features of the earlier tests are changed on purpose.**
  1. *Speed:* the horizon is set in generations, and the primary criterion is the **direction** of change against a
     paired control, with a minimum effect size, instead of a fixed level at a fixed update.
  2. *Viscosity:* in most rungs kin association came from local settlement, and the control was global settlement or
     help to neighbours. Kin selection does not require viscosity: relatives can find each other through family
     groups. Primer's sibling-alarm model (Primer, *Simulating the Evolution of Sacrificing for Family*, 2021)
     keeps siblings together and allocates homes globally, and reproduces Hamilton's rule exactly. Here relatives
     are found **by id** (siblings) and births are **global**, so neighbours are unrelated and siblings do not
     compete locally for space. The control removes kinship while keeping the group structure.
- **Goal B, not goal A.** The help goes to siblings, not offspring: costly help to non-offspring relatives, the
  table's goal B. A positive result would be the first goal-B result with births into free space.

**Relation to `STEP5_EMPTY_SITES.md`.** That step also has a relatedness-removed control (X14, mean-field gifts) and
a seed-paired comparison against a neutral arm, but it keeps the 0.60 endpoint as a condition, and X14 also changes
demography (lone breeders' gifts are delivered, the local fecundity boost disappears). Here the control keeps group
sizes, birth timing, dose, delivery failures and distance, and changes only whether group-mates are related.

## Theory screen (before any code)

- **Hamilton's rule with delivery failure.** A helper with `h` sends `B·h` in equal shares to its living siblings
  and always pays `C·h`; with no living sibling the gift is lost. With `q` = the fraction of donor-updates with at
  least one living sibling, the expected benefit delivered per unit `h` is `B·q`. Selection on `h` is favoured,
  to first order, when `r·B·q > C`, with `r` the regression relatedness between donor and recipient.
- **Clonal inheritance.** Siblings carry their parent's `h` with mutation (probability 0.02, SD 0.04), so `r` among
  siblings is close to 1. In the shuffled control, group-mates are random newborns of the same update, so `r` is
  close to 0 and the help is a pure cost. **Caveat:** `r` ≈ 1 makes sibling help close to help to clones. It is help to
  relatives by descent under the site's definition, but a sexual version (`r` = ½, attempt 2 below) is the
  stronger test.
- **No kin competition.** With global births a newborn takes a random vacancy anywhere, so siblings do not compete
  for the same nearby sites (Taylor 1992 does not apply). F6-global in the restart had neighbour `h` correlation
  −0.004, so global placement removes viscosity in this model.
- **Saturation.** In a sibling group of size `m`, each of the other `m − 1` siblings sends at most `B/(m − 1)` to a
  given sibling, so the benefit received is at most `B`. With `W_i = 1 + R_i − C·h_i`, `p_i = p0·W_i` ≤ 1 holds
  whenever `p0 ≤ 1/(1 + B)`. The same bound holds in the shuffled control, which has the same group structure.
- **Expected risk.** With `d` ≈ 0.1 and about one birth per occupant per lifetime, living siblings may be rare, so
  `q` may be low. Stage S measures `q` and sets the benefit level from it. Global births in the restart kept late
  occupancy at 0.98, so Stage S may find no point with enough free space; then the step stops.

## Model (from `step5_model.py`, births = `global`)

**Kept from the restart model.** 24 × 24 torus; deaths with probability `d` per update, independent of `h`; each
surviving occupant attempts one birth with probability `p_i = p0·max(0, W_i)`, `W_i = 1 + R_i − C·h_i`, `C` = 0.2;
global births: the target is drawn uniformly among all vacancies; a site claimed by several parents goes to one of
them uniformly at random; clonal inheritance of `h` with mutation (0.02, SD 0.04, clipped to [0, 1]); fresh ids and
`parent_id`; random streams as in the restart.

**New care modes.**

- `siblings`: donor `i` sends `B·h_i` in equal shares to its living siblings (occupants with the same `parent_id`,
  `i` excluded) present at the start of the update, found by id at any distance; lost if none; cost always paid.
  Founders have no parent and therefore no siblings.
- `shuffled`: as `siblings`, but group membership uses a **pseudo-parent label**. At each birth update, the true
  `parent_id`s of that update's newborns are randomly permuted among them (stream `seed + 18,000,000`, used only by
  this arm); a newborn keeps its pseudo label for life. Each parent attempts at most one birth per update, so every
  label appears at most once per update; the permutation keeps, for every label, the number of newborns carrying it
  in every update. Group sizes over time, birth timing, dose, delivery failures and distance are therefore matched to
  the `siblings` rule; only the relatedness of group-mates is removed. A newborn may draw its own parent's label
  (probability 1 / number of newborns that update); this is kept and its frequency reported.

**Generation clock.** `G(t)` = cumulative births up to update `t` divided by the time-averaged number of occupants up
to `t`. Each run stops at the first update with `G` ≥ 300, or at the cap of 60,000 updates (reported; a capped run
is valid and uses its final state).

## Stage S: demographic screen (fixed traits, no mutation, before any care test)

`h` = 0 everywhere and, separately, `h` = 0.6 everywhere with `siblings` care at `B` = 1.2; global births.
Grid: `p0` in {0.2, 0.3, 0.45} × `d` in {0.05, 0.1, 0.2}; seeds 50-53; 6000 updates; window = states after updates
1000-5999. **A point passes** if, for both `h` levels and all four seeds, the run does not go extinct and its window
occupancy is between 0.50 and 0.90 inclusive. **Choice:** the passing point with the highest `q` measured at
`h` = 0 (pooled over seeds), then the highest `d`, written before Stage M runs. **If no point passes, the step stops.**

**Benefit level (fixed from Stage S, before Stage M).** From `q̂` at the chosen point and `h` = 0: the test level
`B_T` is the smallest of {0.6, 1.2, 2.4} (b/c 3, 6, 12) with `B·q̂/C` ≥ 2 and `p0 ≤ 1/(1 + B)`; the below-rule level
is `B_L = 0.5·C/q̂` (so `B·q̂/C` = 0.5). If no listed level meets both conditions, the step stops.

## Stage M: the test (only if Stage S chose a point and a level)

Seeds 0-19 per arm, shared across arms; low-helping start `h` ~ N(0.05, 0.02) unless stated; generation clock as
above.

| Arm | Care | `B` | Births | Start | Role |
| --- | --- | --- | --- | --- | --- |
| **S-global** | siblings | `B_T` | global | low | test |
| **SS-global** | shuffled | `B_T` | global | low | kin-association control |
| S-local | siblings | `B_T` | vacant neighbour | low | secondary: viscosity added (kin competition) |
| S-below | siblings | `B_L` | global | common, N(0.9, 0.05) | below-rule control |
| S-null | none (`B` = `C` = 0) | – | global | low | drift reference |
| S2-global | siblings | 2·`B_T` | global | low | descriptive |

**Measures per run.** Final mean `h` = mean `h` over occupants averaged over the last 10% of the run's generations.
`D_s` = final mean `h` (S-global) − final mean `h` (SS-global) for seed `s`. Recorded every 50 updates: mean `h`,
variance of `h`, occupancy, `G`, mean living siblings per occupant, `q`, gifts lost, own-parent-label draws
(SS-global). **Relatedness:** gift-weighted regression of recipient `h` on donor `h` over all transfers in the last
50% of generations, `r̂ = Cov(h_d, h_r)/Var(h)` (population variance at the same samples). **Selection gradient:**
per run, the slope of births per occupant-update on `h` over the last 50% of generations.

**Validity.** Viable = not extinct and final occupancy ≥ 0.50. An arm with fewer than 18/20 viable runs is not
interpretable. A seed pair with an extinct run counts against the hypothesis.

**Classification (mechanical, in this order):**

1. **Not interpretable** if S-global, SS-global or S-null has fewer than 18/20 viable runs.
2. **Not a step-5 test** if fewer than 15/20 S-global runs have late-window occupancy ≤ 0.90.
3. **Control failed** if SS-global's final mean `h` is above S-null's in more than 10/20 seed pairs with median
   difference ≥ 0.10 (help without relatedness spread: the comparison cannot be read as kinship).
4. **Met** if all of:
   - `D_s` > 0 in at least 15/20 seeds (one-sided sign test, p = 0.021);
   - median `D_s` ≥ 0.10;
   - S-below falls: final mean `h` below its start mean in at least 15/20 seeds, median change ≤ −0.10.
5. Otherwise **not met**.

**Sanity (reported; a failure is flagged, not a verdict).** S-null's final mean `h` within ±0.10 of its start (the
restart's drift arm rose 0.05 → 0.13 at 6000 updates, so mutation bias under clipping is expected and reported).
`r̂` above 0.8 in S-global and within ±0.1 of 0 in SS-global in at least 18/20 runs; otherwise the arms did not
implement the intended contrast, and a met verdict is withheld and reported as such.

**Secondary (reported separately, no effect on the verdict).**

- **H2 (Hamilton direction):** in every arm, the sign of `r̂·B·q̂ − C` (run-level estimates) predicts the sign of the
  selection gradient in at least 16/20 runs.
- **H3 (kin competition):** S-local against S-global, seed-paired final mean `h`; prediction S-local lower in at
  least 12/20 pairs (descriptive; the R8 pattern).
- **Endpoint counts:** final mean `h` ≥ 0.60 per arm, for comparison with the earlier rungs; not used in the verdict.

**Site table:** met → a second-block row "5K (sibling help, global births)" under goal B, worded *consistent with*
kin selection among non-offspring relatives (clonal siblings, `r` ≈ 1); not met → the row marked ✗.

## Attempt 2 (fixed now; runs only if attempt 1 is not met and was interpretable)

Haploid sexual reproduction: each birth needs a second parent drawn uniformly from the focal parent's surviving
occupied grid neighbours (none → the attempt fails); the newborn takes `h` from either parent with probability ½
(then mutation). Siblings are newborns sharing both parent ids (full siblings, `r` ≈ ½); half siblings are not
recipients. Stage S is rerun for this rule (same grid and criteria; `B_T` chosen with `B·q̂/(2C)` ≥ 2, i.e. using
`r` = ½), then the same arms and classification.

## Checks (deterministic tests, before running)

With `B` = `C` = 0, `siblings`, `shuffled` and `none` give identical trajectories at the same seed; the shuffled
stream is used only by SS-global; per update and label, newborn counts are equal under `siblings` and `shuffled`;
a donor never receives its own gift; received benefit ≤ `B` per recipient per update; gifts reach only living group
mates present at the start of the update; global births only onto vacancies; generation clock and stopping rule;
classification precedence; extinct pairs counted against.

## Budget and hard stop

Stage S: 72 runs of 6000 updates. Stage M: 120 runs to `G` = 300 (cap 60,000 updates). Runtime is benchmarked per
arm in Stage S; if the projected Stage M total exceeds 8 CPU-hours, stop and report. Code gets a Codex review before
running. **Hard stop:** at most two attempts; no other `B`, `p0`, `d`, arms or criteria under this
pre-registration.

## Predictions (mine, before any data)

- Stage S finds a passing point and level: about 45% (global births kept occupancy near 0.98 in the restart).
- Attempt 1 met, given Stage M runs: about 70%.
- Control failed: about 10%.
- H3 (S-local lower than S-global in ≥ 12/20): about 60%.
- Attempt 2 met, if run: about 45%.

## Limits

- Clonal siblings (`r` ≈ 1) in attempt 1: close to help to clones.
- Kin are recognised by id, a mechanism the model grants, not one that evolves.
- No energy, limited food or movement: a positive result is step 5 for goal B on a minimal base, not goal B itself.
- The direction criterion with a minimum effect size answers whether kin-directed help is selected, not how fast or
  how far it spreads.
