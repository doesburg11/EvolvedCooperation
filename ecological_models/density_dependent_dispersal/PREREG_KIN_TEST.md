# Kanwal and Gardner (2022) as a kin-selection test: pre-registration (2026-11-25)

**Stage M stopped by the registered kill rule (2026-11-26 00:38): projected 10.1 h > 6 h; no run finished, no trait value read. Stage V passed. See `RESULTS_KIN_TEST.md`.**

**Status: agreed with the user 2026-11-25 (about 21:58 CET), while Stage V was running (launched 21:53 at commit f96375d, no Stage V result seen); no Stage M data.** Revised once after a Codex review (gpt-6.2-sol, medium,
2026-11-25: runner and analysis fixes, the three design points below). The only simulations so far are the
port-equivalence checks below (small populations, authors' random start, no test arm), a deterministic theory
screen (no simulation), and a pipeline smoke test (30 generations, all stages and arms, outputs discarded; at 30
generations no arm is near equilibrium and the values carry no information about the test).

## Why

On the site's Definition and Progress page, Kanwal and Gardner (2022) is a reference row marked "–": the authors'
code, run unchanged, kept costly help to patch-mates above Taylor's cancellation value, but the trait started at
random values (no spread from rare) and there was no control run, so it was read only as consistent with kin
selection among non-offspring relatives. This test asks the definition's question directly: does costly help to
patch-mates spread from a start with no helping to a pre-set endpoint, against a control that removes relatedness
while keeping everything else?

**What "from rare" means here.** In this model helping values are reintroduced by mutation every generation: about
1% of offspring get a new value drawn from U(0, 1), about 50,000 per generation, so at least one such mutant is
present in most patches from the first generation on. The test therefore asks whether helping is *established*
from an all-zero start under recurrent mutation, against a control with the same mutation input; it does not
estimate invasion by a single rare lineage. The control's level under mutation alone is the comparison point
(theory screen below). A secondary question is the paper's own claim: does density-dependent dispersal
raise helping above what fixed dispersal gives?

The model keeps a fixed number of breeders (n per patch), so a positive result is a row in the first block of the
table (fixed population size), not the ecological step 5.

## Model and code

- `kg_model.py`: numba port of the authors' `run_simulation.py` (github.com/jkanwal/viscosity-promotes-altruism,
  commit 0a2bc74f9eae496a71f81ad58d25dde26bc026ad). Same life cycle and parameters: 50,000 breeders, k = 100
  offspring per breeder, mutation m = 0.01, G = 20,000 generations; survival 0.5 + 0.5(1 − z)·zbar times a patch
  factor U(0.5, 1); dispersal attempt probability linear in survivors per breeder (two evolving genes); dispersal
  cost c; breeders drawn from residents and immigrants. Only the random-number source differs.
- **Equivalence check (done, 2026-11-25, before this draft):** authors' unchanged functions vs the port, 500
  breeders, 150-300 generations: at (n, c) = (5, 0.4), 124 original vs 160 port runs, and at (5, 0.4) and (2, 0.8),
  28 vs 64 runs. Mean z, b1, b2 and dispersal rate agreed at generations 11, 51, 150 and 300 (largest gap 2.4
  standard errors in 32 comparisons in the first check, 1.45 in 12 comparisons in the larger check). Port speed:
  about 0.2 s per generation (about 1.2 h per 20,000-generation run, against about 77 h for the original).
- `tests/test_kg_model.py`: 12 unit tests (survival rule, breeder count, dispersal rule with and without density
  dependence and outside [0, 1], dispersal cost, empty-patch refill, sampling with replacement, uniform immigrant
  destinations, shuffle removes patch structure, mutation rates, net-cost share, zero start).

**Is it costly help (definition condition 1)?** A juvenile's own survival probability (before the patch
factor) changes with its own z by 0.5·(−zbar + (1 − z)/(n·k)), where zbar is its patch's juvenile mean and 1/(n·k)
its own share of it (at most 1/200 here). Its help lowers its own survival, after its own share, whenever
zbar > (1 − z)/(n·k). Because a breeder's k clones share its z, a single helping lineage already raises zbar to
about z/n, so this holds almost everywhere; a lone mutant in an otherwise non-helping patch is the exception.
**Measured, not assumed:** every generation the model records the sum of z over juveniles for which the
condition holds, divided by the sum of z over all juveniles (the share of all helping given at a net direct cost).
**Registered:** in every T run this share is at least 0.95 both pooled over generations 1-20,000 (which includes
the establishment phase) and over the last 1,000 generations; otherwise the cell is "not met: help not at a net
cost". This measures the direct effect on own survival only; effects through competition for breeding spots
are indirect (kin competition) and are part of what the test integrates over.
Recipients are patch-mates (siblings and other relatives by descent through limited dispersal), not the helper's
own offspring: the sub-case is **among non-offspring relatives**.

## Arms (Stage M)

All arms start with z = 0 for every breeder (no helping); b1 = b2 = the authors' starting value z*(n, c).

- **T (test):** the authors' model.
- **X (control, relatedness removed):** identical, except that after reproduction all N·n·k juveniles are randomly
  permuted across patches before survival, so patch-mates at the time of helping are a random sample of the
  population. Dispersal, competition and breeder selection then proceed as in T within the shuffled patches.
  Everything else is unchanged. Removing relatedness also changes, as consequences, the local genotype mix,
  patch productivity and who competes with whom; the focal's own share of its patch mean and chance co-location
  of relatives remain.
- **F (secondary, fixed dispersal):** identical to T, except that the dispersal attempt probability is b1
  whatever the density (Taylor's 1992 setting; the gene b2 still mutates but is unused).

**Cells:** (n, c) = (2, 0.8) and (5, 0.8). **Seeds:** 100-109, shared across arms (paired). 60 runs.

**Why these cells (theory screen, deterministic, no simulation):** with relatedness removed, helping is held up
only by mutation (new z values drawn from U(0, 1)). A well-mixed recursion of the model's selection and mutation
rules gives a floor of zbar ≈ 0.101, A ≈ 0.11 (0.094 at generation 100 and 0.100 at 1,000 from the zero start; 0.127
and 0.104 from a random start; 0.101 from both by 20,000). At n = 10
that is above Taylor's value 1/n = 0.10, so the control would reach the endpoint there; at n = 2 and n = 5 the
endpoint (0.5 and 0.2) is well above the floor and below the authors'-code equilibrium from a random start
(A = 0.62 and 0.45 at c = 0.8). c = 0.8 is the cost where the paper's predicted gap to 1/n is largest.

## Measures

As in the authors' notebook: zbar = mean over the last 1,000 generations of the population mean of z;
A = zbar / (1 − zbar); d = dispersal attempts / survivors averaged over all patch-generation rows with survivors
in the last 1,000 generations (pooled as in the notebook). Also recorded: z every generation, empty-patch refills, the two
halves of the last 1,000 generations.

**Endpoint:** A ≥ 1/n (Taylor's cancellation value: 0.5 at n = 2, 0.2 at n = 5).

## Stage V: port validation (gate)

The port with the authors' start (random z), all 25 cells (n ∈ {1, 2, 3, 5, 10} × c ∈ {0, 0.2, 0.4, 0.6, 0.8}),
seed 1, compared with the authors'-code runs of 2026-11-21 to 25. **Passes if** all four hold: A above 1/n in 20
of 20 cells with n > 1; the mixed-model slope of A on d (random intercept per n, as in the notebook) is negative;
|A_port − A_orig| ≤ 0.03 in at least 23 of 25 cells; no cell differs in A by more than 0.06;
|d_port − d_orig| ≤ 0.03 in at least 23 of 25 cells; and the fit converges. **If it fails,** stop
and report; Stage M is not run.

## Hypotheses and classification (per cell, then both)

- **H1 (definition):** T reaches the endpoint in at least 8 of 10 runs **and** X in at most 2 of 10.
- **H2 (paper's mechanism, secondary):** T's A exceeds F's A in at least 8 of 10 seed pairs.
- **Net-cost check:** as registered above (share of helping at a net direct cost ≥ 0.95 in every T run, both
  windows). H1 is reported as the endpoint counts; the net-cost check enters the classification below.

**Validity:** all 60 runs complete without error; empty-patch refills reported (expected none).

**Per-cell classification, in this order:** X at the endpoint in more than 2 of 10 runs → "control did not
separate"; otherwise T at the endpoint in at least 8 of 10 runs and the net-cost check passed → "met"; T at
the endpoint in at least 8 but the net-cost check failed → "not met: help not at a net cost"; otherwise "not met".

**Overall verdict:** both cells "met" → **met**: costly help to patch-mates was established from no helping to
the endpoint against a relatedness-removed control, in a fixed-population model (sub-case among non-offspring
relatives); the site's reference row becomes ✓, still in the first block. Exactly one cell "met" → **met at one
setting only** (row stays "–", text updated). Neither cell "met": if either cell is "control did not separate" →
**not met: the control did not separate**, otherwise **not met** (row ✗ in both cases). H2 is reported
separately; it does not change the row.

**Interim check (at generation 2,000 of every run, about a tenth of the way), done by hand with
`interim_check.py`, which reads only the progress files (generation and elapsed time), never trait values:** all
runs alive and writing, and the projected finish within 6 hours of the start of Stage M. **Kill rule:** stop the
runner (`systemctl --user stop`) and report if any run has crashed or stopped advancing, or the projected finish
exceeds 6 hours. A crash in any run also stops the runner by itself. No look at A until all runs are complete.

**Budget:** Stage V about 1.5 h, Stage M about 3 h (30 runs in parallel, 32 cores). Raw output goes to
`~/simulation_results/kg_kin_test/` (outside the repository); summaries to `data/` (committed). Code: `kg_model.py`,
`run_test.py`, `analyze_test.py`; 12 unit tests. **Hard stop:** one attempt.
No other cells, endpoints, arms or seeds under this pre-registration.

**Predictions made before the data:** Stage V passes: 90%. H1 met in both cells: 70% (risks: T at n = 2 sits
only 0.12 above the endpoint in the random-start runs; the rare start may settle lower). X at or below 2/10 in
both cells: 90%. H2 in both cells: 75%.

## What this would and would not show

A positive result shows kin selection among non-offspring relatives in the authors' model by the site's
definition, in a fixed-population island model with no free space, no energy and no movement. It does not test
step 5 or the ecological goal. H2, if met, is consistent with the paper's density-dependence mechanism; F differs
from T only in the dispersal rule, but the dispersal genes then evolve differently (mean dispersal and dispersal
mortality differ), so it is not a single-change test of the mechanism. Seeds are shared across arms for pairing,
but the arms use their random numbers differently from the first generation (X) or once their paths diverge (F),
so pairs share labels, not random streams.
