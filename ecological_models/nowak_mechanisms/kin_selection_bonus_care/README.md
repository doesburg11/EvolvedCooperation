# Kin Selection With Care as a Bonus: Theory Screen (2026-11-19)

Status: **theory screen only, nothing built or run.** It asks whether a world where young survive *without* care
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
