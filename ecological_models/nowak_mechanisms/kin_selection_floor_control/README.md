# Kin Selection With a Survival Floor (pre-registration 2026-11-18)

Status: **pre-registered 2026-11-18 (revised twice per Codex review before commit), nothing built or run.** Detailed results will go in `RESULTS.md`.

## Question

Is kin selection established in the ecological model (`../kin_selection/`)? Its evidence so far:

- Inherited helping spreads from rare founders in some runs: 2 of 5 in the original proof, 12 of 20 in
  `../kin_selection_learning/` step 0, 15 of 40 in its confirmation test.
- Rare helpers have about half the offspring of residents, yet the trait spreads.

Two weaknesses stop this from being an established result:

1. **The control is confounded.** Without kin rearing (`unrelated_rearing_groups`), the population dies out. Kin
   selection predicts that helping is not favoured there; extinction alone would give the same zero. The
   kin-learning confirmation test showed that survival in this model needs only a small steady amount of care, so
   "no kin nearby" and "too little care to survive" are hard to tell apart.
2. **Only surviving runs count.** A run succeeds only if helping rose *and* the population survived. Part of the
   apparent favouring of helping may be that only populations where helping happened to rise survived.

This test removes the extinction confound and most of the survivorship bias. Every population gets a fixed,
costless amount of external care for each juvenile, enough that a population with no helpers survives. Helping is
then judged on how it spreads *within* populations that all survive. Against a drift baseline, the test also
measures Hamilton's rule directly from individuals' costs and benefits. Demography can still differ between arms
(population size, time at the cap), so it is reported alongside (see Descriptive).

## Model changes

- **Floor (all main arms).** Each juvenile receives external care `f` (care units), added to the care it gets from
  helpers before saturation. Juvenile survival is then

  ```text
  base 0.35 + benefit 0.75 x min(f + helper care, saturation 0.9)
  ```

  The external care costs no one energy and does not depend on anyone's helping trait, so it leaves the cost of
  helping unchanged. It does use up care headroom: helper care beyond `0.9 - f` is worthless. The grid therefore
  stops at `f` = 0.4, which leaves at least 0.5 care units of headroom, and the fraction of juveniles whose care
  saturates is reported per arm.
- **Neutral control (arms K-N, U-N).** Helper care is not counted toward survival, and care costs nothing; the
  floor stays. The helping trait then has no effect at all and changes only by drift and mutation (mutation
  probability 0.20 per birth). This gives the no-selection baseline for trait change.

Everything else is the base model's defaults, at cost `care_cost_per_unit` 0.03.

## Rearing modes

- **K, kin rearing:** the base default. Newborns stay in their mother's group; no dispersal.
- **U, unrelated rearing:** newborns are fostered into a group containing neither parent
  (`foster_to_nonparent_group_probability` 1.0). Matured dispersal stays 0, as in K, so the only difference is
  where juveniles are reared. The base `unrelated_rearing_groups` scenario also sets matured dispersal 0.85; that
  version runs as the descriptive arm U-disp.

## Step 0: choose the floor `f` (no helpers, no outcome data on helping)

- **Control:** every founder has `h` = 0; mutation and rare founders are off. Nobody helps.
- **Grid:** `f` in {0.05, 0.1, 0.15, 0.2, 0.3, 0.4}. Rearing modes K and U, seeds 0-19, 220 steps.
- **Persistence:** population >= 100 at every step from 181 to 220.
- **Rule:** `f*` is the smallest `f` at which the control persists in all 20 seeds in *both* rearing modes. This
  is a conservative bound, so that H0 below does not fail through sampling error at a borderline floor.
- **Stop:** if no `f` qualifies, stop and report that the floor approach cannot test this model.

## Main test

All arms use seeds 300-339 (40 runs), 220 steps, and the base model's rare-founder start (3% of founders at
`h` = 0.65, the rest uniform in [0, 0.04]).

| Arm | Rearing | Floor | Helping acts |
| --- | --- | --- | --- |
| K | kin | `f*` | yes |
| U | unrelated | `f*` | yes |
| K-N | kin | `f*` | no (neutral) |
| U-N | unrelated | `f*` | no (neutral) |
| K0, U-disp0 | kin; unrelated + dispersal 0.85 (the base scenarios) | none | yes (descriptive, replicates the old result) |
| U-disp | unrelated + dispersal 0.85 | `f*` | yes (descriptive) |

The arms use the same seed numbers, but their random streams diverge from the first birth, so arms are compared as
independent samples.

**Outcomes per run.**

- *Persistence*: as in step 0.
- *Spread*: the base proof rule without its Hamilton-margin proxy. Mean `h` rises by >= 0.015, the high-helper
  frequency rises by >= 0.02, and the run persists.
- *Trait change*: final mean `h` minus initial mean `h`. A run that dies out uses its last recorded mean `h` and
  stays in every test; it never counts as spreading. No run is dropped from H1, H1b or H2.

**Hamilton's rule, measured (Queller's regression form).** The cohort is every individual born in steps 20-144,
including those that die as juveniles. Its reproduction ends by age 55, so its offspring have matured by step 220.
For each individual:

- `w`: the number of its offspring that reach maturity (recruited offspring), 0 if it died as a juvenile.
- `h`: its own helping trait.
- `s`: the *effective* helper care it received per juvenile step, averaged over the juvenile steps it was alive:
  `min(f + helper care, 0.9) - f` each step. This is the social partners' helping that reached it and could still
  raise survival. It is an average, not a total, so a juvenile that lives longer does not collect more `s` simply
  by being alive longer.

Per run, regress `w / mean(w)` on `h`, `s` and sex jointly:

- `b_h` is the direct effect of own helping. The cost is `c = -b_h`.
- `b_s` is the benefit of help received.
- `r` is the slope of `s` on `h`: how much more help carriers of high `h` receive. This is phenotypic
  assortment, the relatedness that enters Queller's rule, not pedigree relatedness.

The Hamilton margin is `r * b_s - c`. Each quantity is averaged over runs, with a 95% interval from resampling runs
(10,000 draws). A run is analysable if its cohort has >= 50 individuals, `mean(w)` > 0, `h` and `s` both vary, and the
regression design has full rank. If fewer than 30 of 40 runs
in an arm are analysable, H3 is inconclusive (counted as not met). A pooled individual-level estimate with
run-resampled intervals is reported as a robustness check.

## Hypotheses

- **H0, the floor works.** K, U, K-N and U-N each persist in >= 36 of 40 runs. *Manipulation check: if it fails,
  the test cannot answer the question; stop and report.*
- **H1, helping spreads more with kin nearby.** K's spread exceeds U's by >= 10 runs (0.25), with one-sided
  Fisher exact p < 0.05. K's trait change also exceeds U's: one-sided Mann-Whitney p < 0.05.
- **H1b, this is selection, not drift.** K's trait change exceeds K-N's: one-sided Mann-Whitney p < 0.05.
- **H2, no spread without kin.** U spreads in <= 4 of 40 runs, and U's median trait change is no more than
  0.005 above U-N's.
- **H3, Hamilton's rule holds in K and not in U.** All four must hold:
  - K's margin is above 0 (interval above 0).
  - K's cost `c` is above 0 (interval above 0).
  - U's margin interval does not lie above 0.
  - The interval of K's margin minus U's margin lies above 0.

## Decision

- **H0 fails:** not testable with this floor. Recorded; the base module keeps its caveat.
- **H0, H1, H1b, H2 and H3 met:** kin selection in the ecological model is established, for this life cycle,
  these parameters and the rare-founder start. Update the base module's README and the site page, then move on.
- **H0, H1, H1b and H2 met, H3 not:** spread depends on kin rearing and beats drift, but the measured costs and
  benefits do not show Hamilton's rule. Recorded as partly established.
- **H0 met, any of H1, H1b or H2 not:** kin selection in the ecological model is not established beyond population
  survival. The base module's README gets that caveat.

**Predictions (mine, before any data).**

- H0 about 85%: `f*` uses the strict all-seeds rule.
- H1 about 50%.
- H1b about 65%.
- H2 about 75%.
- H3 about 45%: the regression is noisy, and in U the trait may hardly vary once rare founders die.

## Descriptive

- Persistence, spread and trait change for K0, U-disp0 and U-disp (comparison with the old results and with the
  dispersal version of U).
- Mean `h` over time per arm.
- Per arm: population size, steps at the cap, births, sex ratio, and the fraction of juveniles whose care saturates.
- Care relatedness and household care fraction (base diagnostics).
- Per-run `c`, `b_s`, `r`, and the number of analysable runs.

## Budget and hard stop

- About 520 runs: 240 in step 0 and 280 in the main test. Minutes on CPU, one session.
- Code gets a Codex review before step 0, and the results wording a Codex review before commit.
- `f*` comes from step 0's rule alone. No arm, threshold or parameter changes after seeing main-test results; a
  failure is recorded, not tuned.

## Limits

- Non-spatial groups. One life cycle and one cost (0.03).
- The external care is a modelling device, not a biological claim: it stands in for any source of juvenile survival
  that does not depend on the helping trait.
- `r` is phenotypic assortment in help received, not genealogical relatedness.
- Demography (population size, time at the cap) can still differ between K and U; it is reported, not
  controlled.
- No shuffled-relatedness arm: the base module found that kin recognition is not needed (`shuffled_relatedness`
  succeeds at the same rate), so this test is about rearing near kin, not recognising kin.
