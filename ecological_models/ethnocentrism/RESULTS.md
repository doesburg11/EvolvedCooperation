# Ethnocentrism port: results

Run 2026-11-21 with `utils/run_experiments.py` (9 experiments × 30 seeds, 77 s on 24 workers). Raw output in
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
| Parent–offspring or siblings (of all pairs) | 43% | 1% |
| Median births separating them (same-founder pairs) | 2.5 | 78 |
| Median age of their common ancestor (ticks) | 25 | 401 |
| `r_pop`, help-own-colour flag (pre-registered) | 0.79 | −0.38 |
| `r_reg`, help-own-colour flag (added later) | **0.65** (0.50–0.74) | 0.00 |
| `r_reg`, help-other-colours flag (added later) | 0.72 | 0.07 |

- **E1 met (30/30):** same-colour neighbours share a founder far more often than different-colour neighbours
  (90% vs 18%). About 43% of same-colour neighbour pairs are a parent with its offspring or two siblings.
- **E2 met (30/30):** `r_pop` on the help-own-colour flag is positive among same-colour pairs. `r_pop` also
  rises when helpers are over-represented among those pairs (see README). The regression version `r_reg`, added
  after these results, gives the same picture: 0.65 among same-colour pairs, about 0 among different-colour pairs.
- Colour was strongly but imperfectly associated with descent: 95% of same-founder neighbour pairs had the same
  colour (colour mutates at 0.005 per birth), and about 49 founder lines were alive at the end.

**What this does and does not show.** In this model, same-colour neighbours were usually from the same founder
line: 90% of same-colour pairs shared a founder, and 43% of all same-colour pairs were parent–offspring or sibling
pairs; among same-founder pairs the median number of births separating the two was 2.5. This describes who is
helped. It does not show that kinship is *why* ethnocentrism spreads; a causal test would break the colour–descent
link (for example, children get a random colour) and compare.

## Review

Codex (gpt-6.2-sol, 2026-11-21) found no departure from the NetLogo semantics (update order, the reproduction
snapshot and order, newborn death, mutation, immigration, all 19 reporters) or in the pedigree code. Its points,
all addressed before the final run: the NetLogo tables are now validated before the test; an undefined p now
flags; the lineage output keeps the same keys when a group is empty; lineage results are only summarised after
a port pass, and E1/E2 are judged against 27/30 in code; `r_pop` is no longer described as a regression
relatedness, and `r_reg` was added; six tests were added (18 in total).

A second Codex pass (gpt-reserve, wording only) found no misreported numbers; its three wording changes to this
file were applied.
