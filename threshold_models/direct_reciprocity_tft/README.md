# Direct reciprocity threshold model: Tit-for-Tat against Always-Defect (`w > c/b`)

**Status (2026-11-26):** pre-registration written and committed before any model code or run, at the user's request
(third minimal threshold model). No Codex review. Results, when run, go in [`RESULTS.md`](RESULTS.md).

## Question

In a well-mixed population playing the repeated donation game, does Tit-for-Tat (TFT) resist invasion by
Always-Defect (ALLD) exactly when the probability of another round `w` exceeds `c/b` (Nowak 2006), and does a rare
TFT fail to spread for every `w` below about 0.98, as the same payoffs predict? The first is the maintenance
condition Nowak's rule states; the second is the spread-from-rare limit the site reports for direct reciprocity.

## Model

- **Population.** `N` = 1,000, well mixed, two strategies (TFT, ALLD), haploid, no mutation, non-overlapping
  generations.
- **Game.** Every pair of individuals plays one repeated donation game per generation. The number of rounds `L` is
  geometric: after each round another follows with probability `w` (so `L` ≥ 1, mean `1/(1 − w)`), drawn
  independently for each pair. A cooperating player pays `c` and the partner gains `b`. TFT cooperates in round 1
  and then copies the partner's previous move; ALLD always defects. So a TFT pair earns `(b − c)·L` each; TFT
  against ALLD earns `−c` (TFT) and `b` (ALLD) in round 1 and nothing after; two ALLD earn 0. Only TFT-TFT pairs
  depend on `L`.
- **Fitness.** `f = 1 + s·π̄`, with `π̄` the payoff summed over all `N − 1` partners divided by `N − 1`; `s` = 0.1.
- **Reproduction.** Wright-Fisher: the next generation's number of ALLD is binomial with `N` trials and probability
  `Σ_ALLD f / Σ_all f`.

## Theory

With `n` ALLD and `N − n` TFT, the expected payoffs are
`π̄_ALLD = b·(N − n)/(N − 1)` and `π̄_TFT = [(b − c)(N − n − 1)/(1 − w) − c·n]/(N − 1)`.
ALLD does better, and its expected frequency rises, exactly when `w < w*(n)` with

**`w*(n) = 1 − (b − c)(N − n − 1)/(b(N − n) + c·n)`**,

which tends to **`c/b`** as `N → ∞` and `n/N → 0` (Nowak's rule). With `n` = 10 (1% ALLD): `b` = 3, `c` = 1:
`w*` = 0.3362 (`c/b` = 0.3333); `b` = 2, `c` = 1: `w*` = 0.5030 (`c/b` = 0.5).

For a rare TFT (`m` TFT among `N − m` ALLD), TFT does better only if
`w > 1 − (m − 1)(b − c)/(b·m + c(N − m))`: with `m` = 10, 0.9824 (`b` = 3) and 0.9911 (`b` = 2). Below that, rare TFT
loses.

**Prediction for one generation** (expected payoffs, ignoring the small variance of `L`): with `x = n/N`,
`E[x'] − x ≈ x·f_ALLD/(x·f_ALLD + (1 − x)·f_TFT) − x`.

## Cells (all fixed now)

| Series | `b` | `c` | `c/b` | `w*` (`n` = 10) | `w` |
| --- | --- | --- | --- | --- | --- |
| B3 | 3 | 1 | 0.333 | 0.3362 | 0.15, 0.25, 0.30, 0.375, 0.45, 0.55 |
| B2 | 2 | 1 | 0.500 | 0.5030 | 0.30, 0.40, 0.45, 0.55, 0.60, 0.70 |

**Far cells** (`|w − w*|` ≥ 0.05): B3 0.15, 0.25, 0.45, 0.55; B2 0.30, 0.40, 0.45, 0.60, 0.70 (nine). Near: B3 0.30,
0.375; B2 0.55.

**Runs** (cells numbered 0-11 in table order):

- *ALLD rare, one generation:* 20,000 runs per cell from `n` = 10 ALLD; seed of run `j` in cell `i`:
  `10,000,000 + 100,003·i + j`. Statistic: `Δx` = next-generation ALLD frequency − 0.01.
- *TFT rare, one generation:* 20,000 runs per cell from 10 TFT among 990 ALLD; seed `30,000,000 + 100,003·i + j`.
  Statistic: `Δx_TFT` = next-generation TFT frequency − 0.01.
- *ALLD rare, 100 generations:* 40 runs per cell; seed `50,000,000 + 1,009·i + j`. Statistic: final ALLD frequency.

## Stage 0

Tests in `tests/` (payoffs equal a brute-force round-by-round simulation on a small population; mean `L` matches
`1/(1 − w)`; at `w*(n)` the expected payoffs are equal; reproduction probability equals the fitness share; absorbing
states stay absorbed; same seed, same run). Benchmark 500 runs per cell and start, timing only; if the projected run
exceeds 5 hours on 2 cores, the one-generation runs are reduced to the largest multiple of 5,000 that fits (same for
every cell), recorded in `RESULTS.md` before the run.

## Registered tests

- **D1 (maintenance, direction).** In each of the nine far cells, the 99% t-interval of the mean `Δx` (ALLD rare)
  lies on the predicted side of 0: above if `w < w*`, below if `w > w*`.
- **D2 (size).** The predicted one-generation change lies inside the 99% t-interval of the mean `Δx` in at least 10
  of 12 cells.
- **D3 (spread from rare fails).** In all 12 cells, the 99% t-interval of the mean `Δx_TFT` lies below 0.
- **Verdict:** **reproduced** (TFT resists ALLD exactly above `w*` ≈ `c/b`, and cannot spread from rare) if D1, D2
  and D3 hold; otherwise **not reproduced**, naming the failing test and cells.
- **Secondary:** the 100-generation runs (ALLD rare): number of runs per cell in which ALLD is lost, fixed, or
  neither; near-cell signs of `Δx`.

## Predictions (mine, before any code)

D1 holds: 95%. D2 holds: 85%. D3 holds: 99%. Near cells B3 0.30 and 0.375 show the predicted signs: 60%.

## Limits

Two pure strategies, no errors, no mutation, a well-mixed population and weak selection. TFT's success here is the
maintenance condition: once common it resists ALLD when interactions repeat often enough. It does not show how TFT
becomes common, which is the spread-from-rare question that D3 answers negatively.

## References

- Axelrod, R., and Hamilton, W. D. (1981). The evolution of cooperation. *Science*, 211(4489), 1390-1396.
- Nowak, M. A. (2006). Five rules for the evolution of cooperation. *Science*, 314(5805), 1560-1563.
