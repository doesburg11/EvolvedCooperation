# Network reciprocity threshold model: cooperators on a lattice (Ohtsuki's rule, finite-N form)

**Status (2026-11-26):** pre-registration written and committed before any model code or run, at the user's request
("next threshold model"). No Codex review.
**Result: not reproduced as registered** (T1, the direction in all nine far cells, holds; T2, the straight-line
estimate of the threshold, misses in both graphs because the response is curved at these `w`). Details in
[`RESULTS.md`](RESULTS.md).

## Question

Does a single cooperator in a population of defectors on a regular lattice become more likely to take over than a
neutral mutant exactly where the death-birth rule for regular graphs says, with a real net cost and **no benefit
routed back to the helper**?

This is the second minimal threshold model (after `kin_selection_siblings/`). It is the standard model of network
reciprocity, built because the Moran engine's network-reciprocity wrapper spread from a low start only through the
producer's self-route (`moran_models/nowak_mechanisms/RESULTS.md`, 2026-11-26).

## Model (Ohtsuki et al. 2006)

- **Graph.** 10 × 10 torus, `N` = 100. Graph V: von Neumann neighbourhood, `k` = 4. Graph M: Moore neighbourhood,
  `k` = 8. Every site has exactly `k` neighbours; no self-loops.
- **Strategies.** Cooperator (C) or defector (D). A cooperator pays `c` = 1 for each neighbour and gives `b` to each
  neighbour. Accumulated payoff of site `i`: `π_i = b·(number of C neighbours of i) − c·k·[i is C]`. A cooperator
  never receives its own benefit.
- **Fitness.** `f_i = 1 − w + w·π_i`.
- **Death-birth updating.** Each step one site, chosen uniformly, dies; its `k` neighbours compete for the empty site
  with probability proportional to fitness, and the winner's strategy is copied into it. No mutation.
- **Start and end.** All defectors except one cooperator at a uniformly chosen site. Run until all sites are C
  (fixation) or none are (extinction).

## Theory

For death-birth updating on any connected `k`-regular graph of size `N`, under weak selection, selection favours
cooperation (a cooperator's fixation probability `ρ_C` exceeds the neutral `1/N`) if `(b/k − c)(N − 2) + b(2/k − 2) > 0`
(Chen 2013), i.e.

**`b/c > b*/c = (N − 2)/(N/k − 2)`**, and opposes it if `b/c` is below that.

This is the finite-`N` form of Ohtsuki et al.'s `b/c > k` (Taylor, Day and Wild 2007 for bi-transitive graphs). For
`N` = 100: graph V `b*` = 98/23 = **4.261** (against `k` = 4); graph M `b*` = 98/10.5 = **9.333** (against `k` = 8).
In the weak-selection limit `ρ_C − 1/N` is linear in `b` at fixed `c`, so the crossing can be located by a straight
line through the cells.

## Cells (all fixed now)

`c` = 1. Selection intensity chosen so that `w·π` stays at or below about 0.3 at the largest benefit: graph V
`w` = 0.01, graph M `w` = 0.0025.

| Graph | `k` | `w` | `b` | `b*` (finite `N`) |
| --- | --- | --- | --- | --- |
| V | 4 | 0.01 | 2, 3, 4, 5, 6, 8 | 4.261 |
| M | 8 | 0.0025 | 4, 6, 8, 9, 11, 14 | 9.333 |

**Far cells** (`|b − b*|` ≥ 1): V `b` = 2, 3, 6, 8; M `b` = 4, 6, 8, 11, 14 (nine cells). Near cells: V 4 and 5, M 9.
M `b` = 9 lies between `k` = 8 and `b*` = 9.333: the finite-`N` rule predicts `ρ_C < 1/N`, the large-`N` rule
`b/c > k` predicts `ρ_C > 1/N`.

**Runs.** `R` = 1,000,000 independent fixation runs per cell (run `j` of cell `i` uses seed `1,000,003·i + j`, with
cells numbered 0-11 in the order of the table). Estimate `ρ̂ = fixations/R`; report `ρ̂·N`.

## Stage 0 (before the registered run)

1. **Tests** (deterministic, in `tests/`): every site has exactly `k` distinct neighbours, none itself, and the
   neighbourhood is symmetric; payoffs from the incremental bookkeeping equal payoffs recomputed from scratch after
   random updates; with `w` = 0 the chosen parent is uniform over the neighbours (frequency test); a run ends only
   at 0 or `N` cooperators; same seed, same run.
2. **Neutral check:** `w` = 0, 200,000 runs per graph: `ρ̂·N` within its 99% binomial interval of 1.
3. **Benchmark:** 20,000 runs of each registered cell, timing only (the fixation counts are discarded, not printed).
   If the projected registered run exceeds 5 hours on the two available cores, `R` becomes the largest multiple of
   100,000 that fits in 5 hours, the same for every cell, written into `RESULTS.md` before the run; otherwise
   `R` = 1,000,000.

## Registered tests

- **T1 (direction, far cells).** In each of the nine far cells, the 99% binomial interval of `ρ̂·N` lies entirely on
  the side of 1 that the rule predicts (above if `b > b*`, below if `b < b*`). T1 holds if all nine do.
- **T2 (location of the threshold).** Per graph, weighted least-squares line of `y = ρ̂·N − 1` on `b` over its six
  cells (weights = inverse binomial variance); crossing `b̂* = −intercept/slope`; 95% interval from a parametric
  bootstrap (10,000 draws of binomial counts with the estimated `ρ̂` of each cell, seed 12345). T2 holds if, for both
  graphs, the interval contains the finite-`N` `b*` (4.261 and 9.333).
- **Verdict:** **rule reproduced** if T1 and T2 hold; otherwise **not reproduced**, naming the failing test and
  cells.

**Secondary (reported, not part of the verdict).**

- **H2 (finite `N` against `b/c > k`):** graph M's bootstrap interval for `b̂*` lies entirely above 8.
- **H3 (near cells):** sign of `ρ̂·N − 1` in V 4, V 5 and M 9, with intervals; the rule predicts below, above and
  below.
- **Linearity:** residuals of each fitted line, to show whether the weak-selection straight line fits at these `w`.

## Predictions (mine, before any code)

- T1 holds: 85%. T2 holds: 70% (curvature at these `w` may bias the crossing). H2: 50%. Stage 0 needs no reduction of
  `R`: 60%.

## Limits

Pure strategies, one interaction rule, death-birth updating, one small lattice and weak selection: the setting in
which the rule is derived. The model shows that network reciprocity can favour costly cooperation without any
self-benefit and where its threshold lies; it does not say whether human interaction networks met the condition.

## References

- Chen, Y.-T. (2013). Sharp benefit-to-cost rules for the evolution of cooperation on regular graphs. *Annals of
  Applied Probability*, 23(2), 637-664. https://arxiv.org/abs/1107.1513
- Ohtsuki, H., Hauert, C., Lieberman, E., and Nowak, M. A. (2006). A simple rule for the evolution of cooperation on
  graphs and social networks. *Nature*, 441, 502-505.
- Taylor, P. D., Day, T., and Wild, G. (2007). Evolution of cooperation in a finite homogeneous graph. *Nature*, 447,
  469-472.
