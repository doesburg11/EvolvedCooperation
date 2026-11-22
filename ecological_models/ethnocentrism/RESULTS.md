# Ethnocentrism port: results

Sections 1–2: run 2026-11-21 with `utils/run_experiments.py` (9 experiments × 30 seeds, 77 s on 24 workers). Raw output in
`data/` (`runs.csv`, `lineage.csv`, `check.csv`, `summary.json`). Rules: README "Pre-registration".

## 1. The port matches NetLogo: passes

None of the 81 experiment × metric comparisons with the 10-run NetLogo tables was flagged. The smallest p was
0.003 and the largest mean difference 4.1 percentage points (Experiment 106, defection against other colours,
Python 81.0% vs NetLogo 85.0%). Six of 81 unadjusted comparisons had p < 0.05, close to the 4 expected if there were no
differences; the differences go both ways (Python's ethnocentric share was lower in 106 and higher in 104).

Ethnocentric share of the population (mean over the last 100 ticks):

| Experiment | Change from standard | Python (30 seeds) | NetLogo (10 runs) |
|---|---|---|---|
| 104 | standard: 51×51, 2000 ticks | 75.5% | 73.7% |
| 105 | 101×101 world | 76.7% | 77.7% |
| 106 | 4000 ticks | 75.4% | 78.9% |
| 107 | 1000 ticks | 73.6% | 72.6% |
| 108 | 26×26 world | 67.2% | 67.7% |
| 109 | cost of giving 0.02 | 67.8% | 66.4% |
| 110 | mutation 0.0025 | 82.2% | 82.8% |
| 111 | mutation 0.01 | 64.3% | 64.7% |
| 113 | 2 immigrants per tick | 73.3% | 71.9% |

Passing means no large, clear difference was found; it is not a formal equivalence test. Single runs cannot be
compared, because the random draws differ from NetLogo's.

## 2. Lineage (Experiment 104, final tick, 30 seeds): E1 and E2 both met (30/30)

| Measure | Same-colour neighbours | Different-colour neighbours |
|---|---|---|
| Share of all neighbour pairs | 80% | 20% |
| Same founder (descend from the same immigrant) | **90%** (86–94) | 18% (9–44) |
| At most two births apart: parent–offspring, siblings or grandparent–grandchild (of all pairs) | 43% | 1% |
| Median births separating them (same-founder pairs) | 2.5 | 78 |
| Median age of their common ancestor (ticks) | 25 | 401 |
| `r_pop`, help-own-colour flag (pre-registered) | 0.79 | −0.38 |
| `r_reg`, help-own-colour flag (added later) | **0.65** (0.50–0.74) | 0.00 |
| `r_reg`, help-other-colours flag (added later) | 0.72 | 0.07 |

- **E1 met (30/30):** same-colour neighbours share a founder far more often than different-colour neighbours
  (90% vs 18%). About 43% of same-colour neighbour pairs are at most two births apart (parent–offspring, siblings or
  grandparent–grandchild; corrected 2026-11-22, first written as "parent–offspring or siblings").
- **E2 met (30/30):** `r_pop` on the help-own-colour flag is positive among same-colour pairs. `r_pop` also
  rises when helpers are over-represented among those pairs (see README). The regression version `r_reg`, added
  after these results, gives the same picture: 0.65 among same-colour pairs, about 0 among different-colour pairs.
- Colour was strongly but imperfectly associated with descent: 95% of same-founder neighbour pairs had the same
  colour (colour mutates at 0.005 per birth), and about 49 founder lines were alive at the end.

**What this does and does not show.** In this model, same-colour neighbours were usually from the same founder
line: 90% of same-colour pairs shared a founder, and 43% of all same-colour pairs were at most two births apart (parent–offspring, siblings or grandparent–grandchild)
pairs; among same-founder pairs the median number of births separating the two was 2.5. This describes who is
helped. It does not show that kinship is *why* ethnocentrism spreads; a causal test would break the colour–descent
link (for example, children get a random colour) and compare.

## 3. Random colour (Experiment 104, 30 + 30 runs): H1 met

Run 2026-11-22 with `utils/run_random_colour.py` (16 s), after the pre-registration was committed (1d583ea).
Raw output in `data/random_colour/`. The inherited arm replayed the committed port run exactly (all reporters,
population and births, all 30 seeds).

**Manipulation check passed.** In the random condition, same-colour and different-colour neighbours shared a
founder equally often (70.3% vs 70.1%; mean gap 0.002, mean absolute gap 0.019; limits 0.05 and 0.10).

**H1 met.** The ethnocentric share fell from 75.5% to 12.9% (a drop of 62.7 percentage points; Welch p ≈ 10⁻⁵⁶;
ranges 67–82% and 7–19% do not overlap).

| Mean over 30 runs (range) | Inherited colour | Random colour |
|---|---|---|
| Ethnocentric (helps own colour only) | **75.5%** (67–82) | **12.9%** (7–19) |
| Altruist (helps everyone) | 14.6% (10–22) | 49.7% (30–59) |
| Cosmopolitan (helps other colours only) | 2.3% (1–4) | 29.3% (20–47) |
| Egoist (helps nobody) | 7.6% (6–11) | 8.1% (5–13) |
| Meetings in which help was given | 77.0% | 75.6% |
| Meetings with own colour | 80.2% | 25.0% |
| Population | 1636 | 1619 |
| Same founder: same-colour / different-colour neighbours | 90% / 18% | 70% / 70% |
| `r_reg`, help-own-colour flag, all neighbour pairs | 0.49 | 0.62 |

Interpreting the table:

- Under random colour, ethnocentrics became a minority, and the colour-neutral strategies became more common:
  altruists, and cosmopolitans, who help the ~75% of neighbours with another colour.
- How often help was given stayed about the same, 77% vs 76% of meetings. Neighbours were still close kin
  without the colour cue: 70% shared a founder, and the median common ancestor was about 24 ticks back. Offspring
  are placed next to their parent, and this spatial viscosity kept neighbours related.
- Egoists stayed at about 8% in both conditions.

**What this does and does not show.** Under these settings, breaking the colour–descent link sharply lowers how
common ethnocentrism is late in the run, without lowering how much help is given. This fits the kin-cue reading:
with inherited colour, helping one's own colour picks out the closer kin; with random colour it picks out roughly
a random quarter of neighbours, who shared a founder no more often than the rest, and colour-neutral strategies
became more common. The confound stated in the
pre-registration remains: random colour also makes same-colour neighbours rarer (25% instead of 80% of meetings),
so ethnocentrics also give help less often, and this experiment cannot separate the two changes. It also does
not show what would happen with lower viscosity, where neighbours are less related.

## 4. Lower viscosity (Experiment 104 × dispersal × colour rule, 10 × 30 runs): H1 met, H2 not met

Run 2026-11-22 with `utils/run_viscosity.py` (103 s), after the pre-registration was committed (e4eb553). Raw
output in `data/viscosity/`. Both d = 0 cells replayed the committed runs exactly.

**Manipulation check passed.** The share of neighbour pairs sharing a founder fell from 75% to 22% (inherited
colour) and from 70% to 23% (random colour) between d = 0 and d = 1. Even at d = 1 about a fifth of neighbour pairs
share a founder, because a few founder lines make up much of the population (about 37 lines alive).

**H1 met.** With random colour, cooperation fell from 75.6% of meetings at d = 0 to 4.2% at d = 1 (a drop of 71
percentage points, Welch p ≈ 10⁻⁴⁴).

**H2 not met.** At d = 1, cooperation was 4.3% with inherited colour and 4.2% with random colour (difference 0.1
points, p = 0.44). Egoists made up about 90% of the population in both.

Means over 30 runs; the intermediate dispersal levels are descriptive only:

| Dispersal d | 0 | 0.25 | 0.5 | 0.75 | 1 |
|---|---|---|---|---|---|
| **Cooperation, inherited colour** | 77.0% | 45.2% | 24.3% | 8.0% | 4.3% |
| **Cooperation, random colour** | 75.6% | 29.3% | 12.1% | 6.3% | 4.2% |
| Ethnocentric share, inherited | 75.5% | 58.7% | 40.4% | 14.7% | 7.6% |
| Egoist share, inherited | 7.6% | 28.9% | 52.3% | 80.7% | 89.3% |
| Egoist share, random | 8.1% | 45.6% | 71.6% | 85.2% | 89.8% |
| Same founder, all neighbour pairs (inherited) | 75% | 47% | 32% | 24% | 22% |
| Same founder, same- / different-colour pairs (inherited) | 90% / 18% | 63% / 20% | 49% / 13% | 40% / 17% | 32% / 19% |
| Own-colour meetings (inherited) | 80% | 65% | 53% | 33% | 28% |
| Population (inherited) | 1636 | 1766 | 1846 | 2021 | 2337 |

Interpreting the table:

- Cooperation was lower at d = 1 than at d = 0 in both colour arms, and egoists were more common at higher d.
- With inherited colour, same-colour neighbours still shared a founder more often than different-colour
  neighbours at every d (32% vs 19% at d = 1). Colour stayed a weak kin cue, but at d = 1 that was not enough to
  give more cooperation than random colour.
- At intermediate dispersal, inherited colour went with more cooperation than random colour (45% vs 29% at
  d = 0.25, 24% vs 12% at d = 0.5). This was not a registered test. The runs vary a lot at d = 0.25 (inherited
  31–72%, random 18–41%).
- Population also grew with dispersal (1636 → 2337), consistent with fewer blocked offspring placements
  (offspring per tick 165 → 233).

**What this does and does not show.** Under these settings, with offspring placed anywhere in the world,
cooperation was about 4% of meetings, and inherited colour did not sustain more: at full dispersal the two colour
rules gave the same result. Same-colour egoists can still receive help when they settle next to ethnocentrics.
This fits the reading of sections 2–3: with inherited colour, help went to same-colour neighbours, and these were
more likely to share a founder when dispersal was low; the cue did not stand in for that relatedness. The design does not separate the effect of lower relatedness
from the other things dispersal changes: fewer blocked births, more population, and fewer own-colour meetings
(28% at d = 1 instead of 80%). The pattern at intermediate d is descriptive.

## Review

Codex (gpt-6.2-sol, 2026-11-21) found no departure from the NetLogo semantics (update order, the reproduction
snapshot and order, newborn death, mutation, immigration, all 19 reporters) or in the pedigree code. Its points,
all addressed before the final run: the NetLogo tables are now validated before the test; an undefined p now
flags; the lineage output keeps the same keys when a group is empty; lineage results are only summarised after
a port pass, and E1/E2 are judged against 27/30 in code; `r_pop` is no longer described as a regression
relatedness, and `r_reg` was added; six tests were added (18 in total).

A second Codex pass (gpt-reserve, wording only) found no misreported numbers; its three wording changes to this
file were applied.

Lower-viscosity experiment: three Codex passes (gpt-6.2-sol) before the run found a manipulation check that
wrongly required a Welch test, zero-meeting runs counted as 0% cooperation, invalid verdicts flagged as met, and
births that included immigrants; all fixed before the pre-registration commit. A wording pass (gpt-reserve) on
section 4 found no misreported numbers; its four wording changes were applied.

Random-colour experiment: two Codex passes (gpt-6.2-sol) on the code and pre-registration before the run. They
found an undefined Welch test that could pass H1, shared seeds across arms, a manipulation check that opposite gaps
could fool, a weak replay check and an over-broad reading; all fixed before the pre-registration commit. A wording
pass (gpt-reserve) on section 3 found no misreported numbers; its three wording changes were applied.
