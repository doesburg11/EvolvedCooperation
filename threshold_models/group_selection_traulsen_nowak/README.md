# Group selection threshold model: Traulsen and Nowak (2006) multilevel selection (`b/c > 1 + n/(m − 2)`)

**Status (2026-11-26):** pre-registration written and committed before any model code or run (it replaces the
earlier draft, commit `45a1a10`, which left the payoff convention open). The model definition is taken from Nowak
(2006), Supporting Online Material, section 5, read from the user's Dropbox copy. No Codex review. Results, when run,
go in [`RESULTS.md`](RESULTS.md).

## Question

In the minimal two-level model of Traulsen and Nowak, does a single cooperator in a population of defectors become
more likely to take over than a neutral mutant exactly where `b/c > 1 + n/(m − 2)` (finite number of groups), and is
that threshold distinguishable from the large-`m` form `b/c > 1 + n/m`?

## Model (Nowak 2006, SOM section 5; Traulsen and Nowak 2006)

- **Groups.** `m` groups, maximum group size `n`.
- **Payoffs.** Within a group of size `s` with `i` cooperators, a cooperator pays `c` for each other member to receive
  `b`: `π_C = b·(i − 1) − c·(s − 1)`, `π_D = b·i`. Payoffs are summed over group mates, not averaged.
- **Fitness.** `f = 1 − ω + ω·π`.
- **Step.** One individual from the entire population is chosen to reproduce, with probability proportional to
  fitness; its offspring (same strategy) joins the same group. If the group has reached size `n`: with probability
  `p` it splits in two, its members randomly divided, and another group, chosen uniformly among the other `m − 1`,
  dies; with probability `1 − p` a uniformly chosen member of that group dies.
- **Implementation choices (not fixed by the source text).** Splitting: the first daughter's size is binomial
  (`n`, ½), redrawn until both daughters are non-empty; its cooperators are hypergeometric. Start: every group has
  `n − 1` members (the state after a non-splitting event), all defectors except one cooperator at a uniformly chosen
  position. A run ends when cooperators are fixed or lost.

## Theory

For weak selection and rare splitting (Nowak 2006, SOM): within-group fixation of one cooperator
`φ_C = (1/n)[1 − (b + cn − c)ω/2]`, between-group fixation of one cooperator group `Φ_C = (1/m)[1 + (b − c)(m − 1)ω/2]`,
and `ρ_C = φ_C·Φ_C > 1/(nm)` exactly when **`b/c > b* = 1 + n/(m − 2)`**; for `m ≫ 1`, `1 + n/m`. Traulsen and
Nowak's simulations at `p` = 10⁻³ agree with the finite-`m` form.

**Neutral reference.** Because group sizes vary and a dying group is chosen regardless of its size, the neutral
fixation probability is not assumed to be exactly `1/(m(n − 1))`; it is **measured** with `ω` = 0 under the same
dynamics, and the test statistic is `D = ρ̂_C/ρ̂_0 − 1` (0 = neutral).

## Cells (all fixed now)

`c` = 1, `p` = 0.001, `ω` = 0.05 (lowest fitness 0.5 in G1 and 0.75 in G2).

| Setting | `n` | `m` | `b*` (finite `m`) | `1 + n/m` | `b` (offsets −1, −0.5, −0.25, +0.25, +0.5, +1 from `b*`) |
| --- | --- | --- | --- | --- | --- |
| G1 | 10 | 10 | 2.25 | 2.0 | 1.25, 1.75, 2.0, 2.5, 2.75, 3.25 |
| G2 | 5 | 10 | 1.625 | 1.5 | 0.625, 1.125, 1.375, 1.875, 2.125, 2.625 |

**Runs.** `R` = 1,000,000 fixation runs per cell; neutral reference `ω` = 0, `R₀` = 2,000,000 per setting (any `b`,
since payoffs do not matter at `ω` = 0; `b` = `b*`). Cells numbered 0-11 in table order; seed of run `j` in cell `i`:
`300,000,000 + 1,000,003·i + j`; neutral references `320,000,000 + 2,000,003·g + j` (`g` = 0 for G1, 1 for G2).

## Stage 0

Tests in `tests/` (fitness bookkeeping matches a from-scratch computation; group count stays `m`; a split conserves
members and cooperators; at `ω` = 0 the reproducing group is chosen in proportion to its size; absorbing states;
same seed, same run). Benchmark 20,000 runs of each cell and 20,000 neutral runs per setting, timing only (outcomes
discarded); if the projected run exceeds 5 hours on 2 cores, `R` and `R₀` are scaled down by the same factor to the
largest multiple of 100,000 (for `R`) that fits, recorded in `RESULTS.md` before the run.

## Registered tests

- **G-D (direction, outer cells).** In the four cells at `b* ± 1`, the 99% interval of `D` (delta method, combining
  the binomial variances of `ρ̂_C` and `ρ̂_0`) lies on the predicted side of 0.
- **G-L (location).** Per setting, weighted least-squares line of `D` on `b` over the four inner cells (`b* ± 0.25`,
  `± 0.5`); crossing `b̂*` with a 95% parametric-bootstrap interval (10,000 draws resampling all five binomial
  counts of the setting, seed 777). G-L holds if, in both settings, the interval contains `b*`.
- **Verdict:** **rule reproduced** if G-D and G-L hold; otherwise **not reproduced**, naming the failing test.
- **Secondary:** each interval excludes `1 + n/m`; `ρ̂_0·m(n − 1)`; signs of `D` in all cells; G1 `b` = 2.0 is the
  large-`m` threshold, where the finite-`m` rule predicts `D` < 0.

## Predictions (mine, before any code)

G-D: 85%. G-L: 65% (`p` = 0.001 and `ω` = 0.05 are finite; Traulsen and Nowak report agreement at `p` = 10⁻³ but with
other `ω`). Intervals exclude `1 + n/m`: G1 60%, G2 40%. No reduction of `R`: 70%.

## Limits

One small model of group fecundity selection with rare splitting and weak selection, no migration, groups of at most
10. It shows when this two-level process favours costly cooperation; whether human groups met `b/c > 1 + n/(m − 2)`
is an empirical question about group sizes, numbers of groups and splitting.

## References

- Nowak, M. A. (2006). Five rules for the evolution of cooperation. *Science*, 314(5805), 1560-1563, and its
  Supporting Online Material.
- Traulsen, A., and Nowak, M. A. (2006). Evolution of cooperation by multilevel selection. *Proceedings of the
  National Academy of Sciences*, 103(29), 10952-10955. https://doi.org/10.1073/pnas.0602530103
