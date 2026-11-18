# Kin Selection With Care as a Bonus: Theory Screen (2026-11-19)

Status: **theory screen done; toy test pre-registered below (2026-11-19), nothing built or run.** It asks whether a world where young survive *without* care
can still give helping a meaningful kin-selected payoff, and what that implies for a PredPreyGrass port. It follows
`../kin_selection_floor_control/` (stopped at step 0).

## 1. Why the current model cannot treat care as a bonus

In the base model (`../kin_selection/`), births are limited by energy. An adult female gains 0.20 energy per step
and pays 1.0 per birth. She matures at about 3.3 energy, needs 7 to breed, and can breed until age 45.

- **Measured fecundity.** Matured females born in steps 20-150 had 2.0-2.8 lifetime births on average (floor runs
  with `f` 0.6-0.9, seeds 0-2, no helpers).
- **Replacement threshold.** With about 2.75 births per female (half daughters), a population replaces itself only
  if at least about 73% of juveniles survive to maturity. Over four juvenile survival checks, that is per-step
  survival p >= 0.92.
- **Base survival.** Base per-step survival is 0.35, so survival to maturity is 0.35^4 ≈ 1.5%. Care therefore
  multiplies recruitment by up to about 65 times, so it is a lifeline.

This matches the floor diagnostic: populations persisted only at about 0.95 survival per step.

## 2. The payoff when care is a bonus

**Setup.**

- `F`: lifetime births per female at low density.
- `S0`: juvenile survival to maturity without care.
- `S1`: juvenile survival to maturity with full care. Care saturates, so S1 <= 1.
- A full helper loses a fraction `κ` of its own births (energy spent on care).

**Persistence without care.** This needs `F * S0 / 2 >= R` (half the births are daughters). Take R = 1.2, a margin
against chance extinction. So `S0 >= 2.4 / F`.

**Hamilton's rule.** Count recruits, under population regulation that acts on the whole population (the base
model's cap). A helper whose care covers about one adult's share of juveniles gains its recipients

```text
b = (S1 - S0) / S0      recruits per own recruit
```

and pays `c = κ`. This assumes that one full helper's care covers about one female's lifetime cohort, and that
losing a fraction κ of births loses the same fraction of recruits. The real model shares care among juveniles
alive at the same time and has an energy threshold for breeding, so this is a first-order approximation. Helping
is favoured when `r * b > c`, where `r` is the actor's relatedness to the juveniles it
cares for. In the unrelated-rearing control r ≈ 0, so helping is not favoured there.

**The headroom limit.** Persistence pushes `S0` up, and saturation caps `S1` at 1, so

```text
b <= (1 - S0) / S0 <= F / 2.4 - 1
```

The table uses r = 0.25 (a mix of siblings, nieces and own young; it should be measured) and κ = 0.2:

| `F` (births per female) | 2.75 (now) | 4 | 6 | 8 | 10 |
| --- | --- | --- | --- | --- | --- |
| `S0` needed (survival to maturity) | 0.87 | 0.60 | 0.40 | 0.30 | 0.24 |
| per-step survival needed (4 checks) | 0.97 | 0.88 | 0.80 | 0.74 | 0.70 |
| max `b` | 0.15 | 0.67 | 1.50 | 2.33 | 3.17 |
| margin `r * b - κ` | −0.16 | −0.03 | +0.18 | +0.38 | +0.59 |

**Conclusion of the toy check.** In this best case (S1 = 1, r = 0.25, κ = 0.2, full cohort coverage, no density
effects), a meaningful kin-selected payoff with care as a bonus needs about 6 or more births per female. That is a
necessary condition, not proof that such a world selects for helping: more than twice the current fecundity. Care then lifts survival from about 0.4 to about 1, a
2.5-fold bonus instead of a 65-fold lifeline. Helping must also cost no more than about a quarter of the helper's
own births. In such a world, the unrelated-rearing control persists without help, so the test can separate kin
selection from survival.

**Detectability (rough).** If the margin translated into a selection coefficient of about 0.2 per generation, a
trait would take ln[(0.5/0.5)/(0.03/0.97)]/0.2 ≈ 17 generations to spread from 3% to 50%. At a generation time of
about 30 steps, that is about 500 steps: a run 2-3 times longer, still minutes on CPU. The real selection
coefficient also depends on trait variance, mutation, overlapping generations and effective population size, so
the run length should be set generously (for example 800 steps).

## 3. Kin competition (the classic catch)

The rule above assumes regulation over the whole population. If competition is *local*, so that the extra
recruits a helper saves compete with the helper's own relatives, the benefit is partly cancelled (Taylor 1992;
Queller 1994). Queller's form is

```text
b (r - r_e) > c (1 - r_e)
```

where `r_e` is the actor's relatedness, measured relative to the competitive neighbourhood, to the individuals that
the extra recruits compete with. In viscous populations where kin both receive help and compete locally, `r_e` can
approach `r`; full cancellation holds only for particular life cycles, but the risk is real.
Two things restore it:

- Competition that acts on a wider scale than help. Help goes to the group, but competition is population-wide.
- An *elastic* population, where extra local recruits can fill empty space instead of displacing neighbours
  (Mitteldorf & Wilson 2000, the EvolvedCooperation `spatial_altruism` model; Alizon & Taylor 2008). Being below
  capacity is not enough on its own: the demographic rules must let extra recruits fill empty sites.

The base model's cap is population-wide, but it is not neutral. Births stop at the cap, and excess individuals are
removed lowest energy first. Helpers spend energy on care, so near the cap they are culled preferentially: an extra
cost of helping that the formula above leaves out. A bonus-care toy should therefore regulate density by an
energy-neutral rule (for example random removal, or births stopping at the cap without energy-ranked deaths), or
report this extra cost.

## 4. What this means for a PredPreyGrass port

Young predators in PredPreyGrass spawn with energy and hunt on their own, so the "bonus" condition is plausible.
It still has to be shown that a lineage without gifts replaces itself over the predator-prey cycles. Three further
conditions, each to be checked before any training:

1. **Value of a gift.** In PredPreyGrass, care would be an energy gift, which is roughly zero-sum. To first order,
   helping kin of r ≈ 0.25-0.5 pays only if a unit of energy adds about 2-4 times more reproductive value to the
   young than it costs the giver. That happens when young are near starvation and givers have surplus. With
   hunting thresholds, reproduction thresholds and ecological feedback, the quantity that matters is the marginal
   reproductive value of energy to giver and recipient. It can be estimated from existing runs (future survival and
   reproduction as a function of current energy, by age), without training.
2. **Kin competition.** Predator offspring spawn near their parents and compete for the same local prey. If help
   and competition act on the same scale, the benefit cancels (section 3). It can be measured: relatedness of
   neighbours within the gift radius, against relatedness within the area that shares the same prey. This needs
   lineage tracking, which is cheap to add. Predator numbers cycle with prey, so the population is often
   below capacity, which may help, but whether extra young fill empty space or displace kin has to be measured.
3. **Generations.** Trait evolution needs about 15 or more generations at a margin of 0.2. The number of predator
   generations in a typical PredPreyGrass run should be counted first. Earlier evolutionary lines (ERL flagship)
   stalled partly because there were too few generations.

## 5. Recommendation

- **Toy first.** Build the "bonus care" life history in the non-spatial model: higher fecundity (about 6-8 births
  per female), lower baseline survival above replacement, and care that saturates near survival 1, at a cost of
  about 20% of own births. Reuse the floor-control design (K versus fostering-only U, neutral arms, the Hamilton
  regression), with no floor, since populations then persist on their own. Use an energy-neutral density rule. Run it for about 800 steps. If kin
  selection is not established there, it will not be in PredPreyGrass.
- **Then the PredPreyGrass measurements.** Measure items 1-3 of section 4 from existing runs, without training,
  before any PredPreyGrass design.
- **Hard stop.** One pre-registered toy test, with no tuning after results.

**Limits of this screen.** It is a first-order, regression-style approximation. `r` is assumed, not measured.
Overlapping generations and the cap's boom-and-bust dynamics are ignored. The births-per-female figure comes from
three seeds of a no-helper floor run.

## Pre-registration: bonus-care toy test (2026-11-19, before any code or data; revised per Codex review before commit)

**Question.** In a life history where populations persist without care and care is a bonus, does inherited helping
spread from rare only when juveniles are reared near kin, beyond drift, with Hamilton's rule visible in measured
costs and benefits? If yes, ecological kin selection is established in the toy. If not, the PredPreyGrass kin
port is not pursued.

**Model.** The base ecological model (`../kin_selection/`) with the floor-control code (`../kin_selection_floor_control/`,
floor 0), plus four changes:

1. **Random birth slots.** In the base model births stop once the population reaches the cap (320). When fewer
   slots remain than females who could breed, the base model fills them in list order, which favours older
   individuals; density mortality then never acts, since the cap is never exceeded. Here the breeding females are
   taken in random order. Energy still decides who can breed (the threshold of 7), and that is the intended cost of
   care: a helper's energy spent on care delays its next birth.
2. **Births limited by energy.** `female_reproduction_probability` is raised from 0.35 to 0.9, so that
   probability rarely limits births at any cost in the grid (0.9 × 0.35 = 0.315 > 0.20 surplus per step). Births
   are then set by energy income, and care energy costs births.
3. **Higher fecundity.** `reproduction_energy_cost` is set by step 0 (a lower cost per birth means more births).
4. **Care as a bonus.** `base_juvenile_survival_probability` (`p0`) is set by step 0, high enough that a population
   with no helpers persists. Care still adds `0.75 x min(care, 0.9)` to survival, capped at 1.

**Care cost.** `care_cost_per_unit` = **0.016**, so full effort (capacity 2.5) costs 0.04 energy per step: an
energy-flow choice of 20% of an adult's net income (0.20 per step). The cost in *births* is measured in step 0
(the cost probe), not assumed. Males pay only through energy (starvation risk), since their breeding is not
energy-limited, so the realized average cost is lower than the female cost.

**Run length.** 800 steps (theory screen: about 17 generations of roughly 30 steps for a margin of about 0.2).

### Step 0: choose the life history (no helpers, no helping data)

- **Control:** every founder has `h` = 0; mutation and rare founders are off. Rearing modes K and U (as in the
  floor control: U = fostering into a group with neither parent, no matured dispersal). Seeds 0-19, 800 steps.
- **Grid:** `reproduction_energy_cost` in {1.0, 0.7, 0.5, 0.35}, crossed with `p0` in {0.65, 0.7, 0.75, 0.8,
  0.85, 0.9}.
- **Persistence:** population >= 100 at every step from 761 to 800.
- **Rule:** among the cells where the control persists in all 20 seeds in *both* rearing modes, choose the lowest
  `p0` (the most headroom for care). Ties go to the highest `reproduction_energy_cost` (the fecundity closest to
  the current model).
- **Stop:** if no cell qualifies, stop and report.
- **Cost probe, in the chosen cell (K rearing, seeds 0-19).**
  - Half the founders get `h` = 0.65 and half `h` = 0 (no mutation).
  - Helper care is not counted toward survival, but its energy cost is paid.
  - Helpers and non-helpers therefore share the same population and density.
  - Realized full-effort cost: `κ` = minus the slope of (lifetime births / mean lifetime births) on own `h`, over
    females that matured, pooled over the 20 seeds. This is approximate, since births are nonlinear in energy.
  - If `κ` < 0.05, helping is nearly free: stop and report (the test would not be about a costly trait).
- **Recorded with step 0:** lifetime births per matured female, the realized `κ`, and the theory screen's
  best-case margin `0.25 × (1 − p0^4) / p0^4 − κ`.
  If that margin is <= 0, the main test still runs, with the prediction recorded as "theory predicts no
  kin-selected spread".

### Main test

Seeds 400-439 (40 runs per arm), 800 steps, the chosen cell, the base rare-founder start (3% of founders at
`h` = 0.65, the rest uniform in [0, 0.04]).

| Arm | Rearing | Helping acts |
| --- | --- | --- |
| K | kin | yes |
| U | unrelated (fostering only) | yes |
| K-N | kin | no (neutral: helper care not counted, care costs nothing) |
| U-N | unrelated | no (neutral) |

The arms share seed numbers, but their random streams diverge from the first birth, so arms are compared as
independent samples.

**Outcomes and Hamilton regression.** As in the floor-control pre-registration, with these windows:

- *Persistence*: population >= 100 at every step from 761 to 800.
- *Spread*: mean `h` rises by >= 0.015 and the high-helper frequency by >= 0.02 over the run, and the run persists.
- *Trait change*: final minus initial mean `h`. A run that dies out uses its last recorded mean `h`, stays in every
  test, and never counts as spreading.
- *Cohort*: individuals born in steps 50-735 with at least one juvenile survival check. Reproduction ends by age
  55 and offspring mature 5 steps later, so births by step 735 have completed recruitment by step 800. The number
  without a check is reported. It should be about 0, since births never overshoot the cap.
- `w`: recruited offspring; `h`: own trait; `s`: effective helper care received per juvenile step.
- Per run, regress `w / mean(w)` on `h`, `s` and sex. Cost `c = -b_h`; benefit `b_s`; `r` = slope of `s` on `h`;
  margin `r * b_s - c`.
- Analysable runs: cohort >= 50, `mean(w)` > 0, `h` and `s` vary, full-rank design. Intervals come from 10,000
  run resamples. If fewer than 30 of 40 runs are analysable, H3 is inconclusive.

**Hypotheses.** All thresholds are whole numbers of runs.

- **H0, care is a bonus.** K, U, K-N and U-N each persist in >= 36 of 40 runs.
- **H0b, the unrelated arm removes kin.** U's care-weighted relatedness is <= 0.05, and <= one third of K's.
  - Per run, it is `Σ(total care × mean care relatedness) / Σ(total care)` over all steps (base diagnostics:
    genomic relatedness of carer to juvenile, weighted by care).
  - These per-run values are then averaged over runs.
- **If H0 or H0b fails,** H1-H3 are not testable: stop and report.
- **H1, helping spreads more with kin nearby.** K's spread exceeds U's by >= 10 runs, one-sided Fisher exact
  p < 0.05, and K's trait change exceeds U's, one-sided Mann-Whitney p < 0.05.
- **H1b, selection, not drift.** K's trait change exceeds K-N's, one-sided Mann-Whitney p < 0.05.
- **H2, no spread without kin.** U spreads in <= 4 of 40 runs, and U's median trait change is no more than 0.005
  above U-N's.
- **H3, Hamilton's rule.** All four must hold:
  - K's margin interval is above 0.
  - K's cost interval is above 0.
  - U's margin interval is not above 0.
  - The interval of K's margin minus U's margin is above 0.

**Decision.**

- **Step 0 stops, H0 fails or H0b fails:** not testable; recorded. The PredPreyGrass kin port is not pursued on
  this basis.
- **H0, H0b, H1, H1b, H2 and H3 met:** ecological kin selection is established in the toy, with care as a bonus.
  Next are the four PredPreyGrass measurements of section 4, without training, for the user to approve.
- **All but H3 met:** partly established. Decide with the user whether the PredPreyGrass measurements are still
  worth doing.
- **H0 and H0b met, any of H1, H1b or H2 not:** not established even with care as a bonus. The kin-selection line
  closes, and the PredPreyGrass kin port is not pursued.

**Predictions (mine, before any data).**

- Step 0 finds a cell and passes the cost probe: about 70%.
- H0 and H0b given step 0: about 85%.
- H1 about 40%: the bonus is smaller than the old lifeline, so selection is weaker.
- H1b about 50%.
- H2 about 80%.
- H3 about 35%.

**Budget and hard stop.**

- About 1,180 runs of 800 steps: 960 in the step-0 grid, 20 in the cost probe and 160 in the main test. Roughly
  30 minutes on 8 CPU cores, one session.
- Code gets a Codex review before step 0, and the wording a Codex review before commit.
- The cell comes from step 0's rule alone. No arm, threshold or parameter changes after main-test results; a
  failure is recorded, not tuned.

**Limits.**

- Non-spatial, with population-wide regulation (random birth slots at the cap). That is the favourable case for
  kin selection (no local kin competition, section 3), so a pass here is necessary, not sufficient, for a spatial
  world.
- `p0` and fecundity are chosen for persistence, not from biology.
- The care cost is one energy-flow choice; its cost in births is measured once, in the cost probe.
- Care relatedness uses the base model's genomic relatedness; relatedness-biased care allocation stays on in both
  arms.
