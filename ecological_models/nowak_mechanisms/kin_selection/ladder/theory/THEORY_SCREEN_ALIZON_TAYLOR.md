# Theory screen: Alizon and Taylor (2008), "Empty sites can promote altruistic behavior" (2026-11-25)

No simulation. Purpose: before any further attempt at step 5 (births into free space), find the conditions under
which a published model says empty sites remove kin competition, and compare them with the step-5 attempts.
Source: Evolution 62:1335-1344 (Dropbox, `01. HBP/External HBP Research/Documents`). Script:
`alizon_taylor_2008.py` (output in `alizon_taylor_2008_output.txt`).

## The model

Infinite island model, n = 10 sites per patch, each empty or holding one asexual breeder; continuous-time Moran
dynamics. Every breeder dies at rate k (0.5), independent of its trait, and produces offspring at rate 1; an
offspring stays at home with probability h_i or competes at a random patch, where i is the number of occupied sites.
**Each competing offspring fills each empty site of the patch at rate 1/n**, so a patch whose breeders are more
fecund fills its empty sites faster; offspring that find no site die. Dispersal is set at its ESS: a "bang-bang"
rule, all offspring stay when the patch is below about half full, all leave above (i ≤ 5 vs i ≥ 6 at n = 10). An
altruist gives a fecundity benefit b to one patch-mate at fecundity cost c.

**Result.** The inclusive-fitness effect of the gift (their eq. 2) has no direct competitive term: the only cost to
others is a small drop in reproductive value as the patch fills. Hamilton's rule with patch relatedness nearly holds
(threshold c/b ≈ mean relatedness ≈ 0.15), most favourable at an intermediate number of empty sites (6 of 10).
The authors' key condition (Discussion): **if empty sites become available at a fixed rate and occupants compete
for them according to fecundity, extra fecundity given to one breeder lowers the chances of the others** (kin
competition returns); it is removed only when a patch with higher fecundity fills its empty sites faster at home.

## Re-derivation (from their appendix, n = 10, k = 0.5)

| Quantity | Paper | Here |
| --- | --- | --- |
| Reproductive value, full patch vs single breeder | about 75% | 74.4% |
| Mean patch relatedness | 0.15 | 0.154 |
| Mean threshold c/b | "very close" to 0.15 | 0.139 |
| Patch type most favourable to altruism | i = 6 | i = 6 |
| Relatedness drop between i = 6 and 7 | yes | 0.161 → 0.107 |

Further numbers (beyond the paper, same equations):

- **Dispersal re-optimised (ESS) at each death rate:** occupancy 0.93 to 0.32 for k = 0.1 to 0.7, and the threshold
  stays between 0.11 and 0.21 (needed b/c about 5 to 9); the stay-home switch moves with density (i < 10 at
  k = 0.1, i < 4 at k = 0.7).
- **Dispersal switch left at n/2 while the death rate falls:** threshold 0.009 at k = 0.25 (occupancy 0.76) and
  about 0 at k = 0.1 (0.90). A dispersal rule that does not match the density regime brings kin competition back.
- **Density-independent dispersal** (same m in every patch type): threshold 0.013-0.29 at k = 0.2 and 0.021-0.76 at
  k = 0.5 depending on m, about 40-90% of relatedness. With pressure-limited filling, empty sites alone already
  relieve much of the competition.

## Comparison with the step-5 attempts (consistent with, not tested)

The step-5 restart (F6-local, `../STEP5_RESTART.md`) had trait-independent deaths, as in the paper, but differed
on the paper's key condition:

- **Births were limited by space, not by fecundity, at the family scale.** An offspring could go only to a vacant
  site next to its parent. At late occupancy 0.86, 39% of survivors had no vacant neighbour, so their birth
  attempts failed whatever their fecundity; a gift of fecundity to a relative next to them mostly raises
  competition for the same few vacancies. This is the case the paper says brings kin competition back. The refill
  benchmark (every dead site refilled at once, occupancy 1.00) gave a similar result (0.44 vs 0.47), as expected if
  both were space-limited.
- **No dispersal that responds to density in the test arm.** The exploratory dd arm (move to a random vacancy only
  when no neighbour is vacant, 20% die) went 8/20 against 4/20, not significant.
- **Different help.** The paper's altruism is a gift to a patch-mate (among non-offspring relatives); F6 was care
  for own offspring.

## What it suggests for the ladder

A next step-5 rung that ports the paper's population rule rather than tuning the lattice: patches of n sites,
births that fill a patch's empty sites at a rate rising with the number of competing offspring, trait-independent
deaths, and the paper's ESS dispersal. Its predictions can be registered both ways (help spreads above the
threshold b/c and fails below it), with a relatedness-removed control. It would be the first test in the second
block (population size not fixed), sub-case among non-offspring relatives; own-offspring care, energy and movement
would follow one rung at a time. The Kanwal-Gardner test (density-dependent dispersal in a fixed-population island
model, running 2026-11-25) bears on the dispersal ingredient.

Limits: the paper's analysis assumes weak selection, infinitely many patches and dispersal at its ESS rather than
co-evolving; a finite individual-based version must be checked against it before testing.
