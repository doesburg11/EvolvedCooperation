# Kin selection threshold model: sibling alarm calls (Hamilton's rule)

**Status (2026-11-26):** pre-registration written and committed before any model code or run. Not separately
agreed with the user beyond the request to build the first minimal threshold model; no Codex review.
**Result: Hamilton's rule reproduced** (all three registered tests hold; the two cells where the naive `p` rule
predicts spread lost altruism in 39/40 and 40/40 runs). Details in [`RESULTS.md`](RESULTS.md).

## Question

Does costly help to siblings evolve exactly where Hamilton's rule `b·r > c` says it should, with `r` the
relatedness by descent and not the probability `p` that a sibling carries the allele?

This is the first of a planned set of **minimal threshold models**, one per Nowak (2006) mechanism, each with a
real net cost to the helper and each checked against its own analytical condition. They are demonstrations of
sufficiency, not models of human ancestral ecology. Their role on the site is to show each mechanism working (and
failing) exactly where theory says, as a clean reference beside the ecological and Moran results.

## Amendment A1 (2026-11-26, before any model code or run)

**Problem found while planning the code.** With one puddle of `n` = 2 per sexual home, a pair of parents leaves two
children, exactly replacement, so predation would shrink the population every generation until homes stop filling.
**Change:** each **sexual** home (one pair) produces **2 puddles** of `n` full siblings; each **asexual** home (one
parent) produces **1 puddle**. Homes: **250 pairs** (sexual) and **500 parents** (asexual), so every generation enters
the forest as 500 puddles. Survivors then always exceed the places (at least 875 against 500 in every cell), so
homes fill and the population is constant. Help stays within a puddle; puddles of the same pair do not interact.
The prediction is unchanged: homes are still filled by a uniformly random subset of survivors, and within a puddle
`p = r + (1 − r)·f`. Mating among survivors of the same puddle is allowed (random pairing), which makes parents
slightly related at rate about 1/500 and is ignored by the formula. Everything below that says "one puddle per home"
or "`H` = 500" should be read with this amendment.

## Model (after Primer, *Simulating the Evolution of Sacrificing for Family*, 2021)

Rebuilt from the video's transcript; Primer's code is not public.

- **Population.** `H` homes. Each generation every home holds one puddle of `n` siblings. Generations do not
  overlap.
- **Gene.** Haploid, one locus, two alleles: coward (0) and altruist (1). No mutation.
- **Forest.** Each puddle visits one of `T` trees, chosen uniformly; exactly `round(a·T)` trees (a fixed set per
  run) hide a predator, so a puddle is attacked with probability exactly `a`.
- **Attack.** One member of the puddle, chosen uniformly, notices the predator. A **coward** noticer runs and
  survives; the other `n − 1` are eaten. An **altruist** noticer sounds the alarm: the other `n − 1` escape, and the
  noticer is eaten with probability `c`.
- **Homes.** Survivors are shuffled. Asexual: the first `H` survivors each found one home; each home produces a
  puddle of `n` copies of its parent. Sexual: the first `2·⌊min(S, 2H)/2⌋` survivors form pairs, one pair per home;
  each child takes the allele of one parent chosen uniformly (independently per child). Survivors without a home
  leave no offspring. If there are fewer survivors than places, all reproduce and fewer homes are filled.

**Hamilton's quantities.** Cost `c` (the noticer's death probability, compared with a coward noticer, who
survives); benefit `b = n − 1` (siblings saved); relatedness `r` = the probability that a sibling's allele is
identical by descent with the noticer's, i.e. copied from the same parent in the same reproduction: `r = 1`
asexual, `r = 1/2` sexual (each child picks a parent independently).

## Theory (exact one-generation prediction)

Let `f` be the altruist frequency in the generation entering the forest and `p` the probability that a sibling of
an altruist noticer is an altruist. With random mating, `p = r + (1 − r)·f`. Per attacked puddle, the expected number
of altruist survivors is `A = f·[(n − 1)·p + (1 − c)]` and of all survivors `N = f·[(n − 1) + (1 − c)] + (1 − f)`;
an unattacked puddle contributes `n·f` and `n`. Homes are filled by a uniformly random subset of survivors (and
children copy parents' alleles without bias), so the expected altruist frequency of the next generation is

`f' = [(1 − a)·n·f + a·A] / [(1 − a)·n + a·N]`, and

**`f' − f = a·f·(1 − f)·[(n − 1)·r − c] / D`**, with `D = (1 − a)·n + a·N`.

So the direction is exactly the sign of `b·r − c`, and the size is predicted. The naive rule with `p` in place of
`r` (`b·p − c`, the video's first, wrong prediction) gives a different sign in the cells marked † below. The
expectation is over groups formed by random mating from the previous generation, which holds at the start
(founders drawn independently with frequency `f0`) and after every random-mating generation; finite-population
sampling makes the realised change noisy but not biased. (Asexual reproduction keeps puddles clonal, so the
expression holds with `r = 1` in every generation.)

## Cells (all fixed now)

`H` = 500 homes, `T` = 100 trees, `a` = 0.25, start `f0` = 0.5.

| Cell | Reproduction | `n` | `b` | `r` | `c` | `b·r − c` | naive `b·p − c` at `f` = 0.5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S3-0.80 | sexual | 3 | 2 | ½ | 0.80 | +0.20 | +0.70 |
| S3-0.90 | sexual | 3 | 2 | ½ | 0.90 | +0.10 | +0.60 |
| S3-1.00 | sexual | 3 | 2 | ½ | 1.00 | 0 | +0.50 † |
| S2-0.30 | sexual | 2 | 1 | ½ | 0.30 | +0.20 | +0.45 |
| S2-0.40 | sexual | 2 | 1 | ½ | 0.40 | +0.10 | +0.35 |
| S2-0.50 | sexual | 2 | 1 | ½ | 0.50 | 0 | +0.25 † |
| S2-0.60 | sexual | 2 | 1 | ½ | 0.60 | −0.10 | +0.15 † |
| S2-0.70 | sexual | 2 | 1 | ½ | 0.70 | −0.20 | +0.05 † |
| A2-0.80 | asexual | 2 | 1 | 1 | 0.80 | +0.20 | +0.20 |
| A2-1.00 | asexual | 2 | 1 | 1 | 1.00 | 0 | 0 |

## Registered tests

**Q1, direction over many generations.** Per cell 40 runs (seeds 0-39), 200 generations. Statistic: `Δ200` = final
frequency − 0.5 per run (an extinct or fixed run keeps 0 or 1). Mean and 95% t-interval over the 40 runs.

- Cells with `b·r − c` ≠ 0: the interval lies entirely on the predicted side of 0.
- Cells with `b·r − c` = 0: the interval contains 0.
- **Q1 holds** if all 7 non-neutral cells and at least 2 of the 3 neutral cells meet their condition.

**Q2, size of the one-generation change.** Per cell 4,000 independent one-generation runs (seeds 100,000-103,999),
each from fresh founders at `f0` = 0.5. Statistic: realised change in altruist frequency (next generation's
puddles against the founders). **Q2 holds** if the predicted `f' − f` (formula above, `f` = the realised founder
frequency of each run, averaged) lies inside the 99% t-interval of the mean realised change in at least 9 of 10
cells.

**Q3, `r` against `p`.** Over all alarm events in the Q2 runs of the sexual cells, pooled per cell: pedigree
relatedness `r̂` = fraction of (noticer, saved sibling) pairs whose alleles came from the same parent, and `p̂` =
fraction of saved siblings carrying the altruist allele; regression relatedness `r̂_reg = (p̂ − f̄)/(1 − f̄)`, with
`f̄` the mean founder frequency. **Q3 holds** if, in every sexual cell, `r̂` is within 0.02 of 0.5 and `r̂_reg` is
within 0.03 of 0.5, while `p̂` is within 0.03 of 0.75 (the quantity that the naive rule uses).

**Verdict.** **Hamilton's rule reproduced** if Q1, Q2 and Q3 all hold. Otherwise **not reproduced**, with the
failing test and cells named. No other cells, seeds or horizons under this pre-registration.

**Checks before the registered run (deterministic tests, in `tests/`):** with `c` = 0 and `n` = 2, an altruist
noticer's group loses no one; with `a` = 0 the expected change is 0 and survivors are the whole population; an
asexual puddle is clonal; sexual children take only parental alleles and the recorded parent of origin matches;
exactly `round(a·T)` predator trees; the formula equals `f` when `b·r = c`; homes never exceed `H`; same seed gives
the same run.

## Predictions (mine, before any code)

- Q1 holds: 90%. Q2 holds: 85%. Q3 holds: 95%.
- The discriminating cells: S2-0.60 and S2-0.70 decline although the naive rule predicts spread (95%).

## Limits

Well-mixed, one locus, haploid, no mutation, non-overlapping generations, kin association built in (siblings stay
together) and competition global (homes are a lottery). These are the conditions under which Hamilton's rule is
exact; the model shows the rule and the `r`-versus-`p` distinction, not when relatives meet or compete in an ecology.
