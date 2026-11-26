# Rung 4b theory screen: mutation, on the rebased setting q = 0.8 (2026-11-26)

Rung 4b adds one ingredient to rung 4a (met on q = 0.8, 2026-11-26): **mutation** among ALLC, DISC and ALLD. Each
offspring takes one of the two other strategies (equally likely) with probability μ. This screen (`theory.py`,
output `theory_output.txt`; calculation only, no simulation) runs rung 4a's deterministic Wright-Fisher recursion on
the rebased setting (q = 0.8, o = 0.5, e = 0.1, a = 0.02, b = 3, c = 1, s = 0.1; records and payoffs from
`rebase/theory.py`), selection then mutation.

| μ | Gen 500 from rung 4a's start (ALLC / DISC / ALLD) | Gen 5,000 | Gen 5,000 from all-DISC | Shuffled, gen 500, ALLD |
| --- | --- | --- | --- | --- |
| 0 | 0.007 / 0.994 / 0.000 | 0.000 / 1.000 / 0.000 | 0 / 1 / 0 | 1.000 |
| **0.001** | 0.076 / 0.912 / 0.012 | 0.075 / 0.913 / 0.012 | the same | 0.986 |
| 0.002 | 0.125 / 0.845 / 0.030 | 0.126 / 0.845 / 0.030 | the same | 0.972 |
| 0.005 | 0.136 / 0.599 / 0.266 | 0.029 / 0.045 / **0.926** | the same | 0.930 |
| 0.01 | 0.059 / 0.091 / 0.850 | the same | the same | 0.866 |
| 0.02 | 0.123 / 0.180 / 0.697 | the same | the same | 0.754 |
| 0.05 | 0.243 / 0.298 / 0.460 | the same | the same | 0.550 |

- **A sharp cliff.** The cooperative equilibrium disappears in a fold (saddle-node) at μ ≈ 0.00461 (Codex's
  fixed-point calculation; shares there about 0.152 / 0.679 / 0.168). A finite-time bisection in `theory.py`
  (cooperators ≥ 0.8 at generation 3,000 from all-DISC) puts the threshold between μ = 0.00458 (0.847) and 0.00463
  (0.068); just above the fold the collapse is slow (at μ = 0.00461, 0.83 at generation 3,000 but 0.07 by 20,000).
  Equilibrium cooperator shares on the cooperative branch: 0.988 (μ = 0.001), 0.970 (0.002), 0.903 (0.004).
- **Two basins.** The two screened starts (rung 4a's 10/80/10 and all-DISC) converge to the same cooperative state,
  but this is not global: at μ = 0.001 a defector-dominated stable state also exists (about 0.006 / 0.009 / 0.986),
  separated by an unstable one. Rung 4b tests maintenance from favourable starts, not recovery from defection.
- **Why it collapses (interpretation).** Mutation keeps supplying ALLC, which selection removes only slowly while
  defectors are rare (at μ = 0.001 the payoffs are about 1.589 / 1.660 / 1.179: ALLC is still selected against), so
  ALLC holds at 0.075 (μ = 0.001) and 0.126 (0.002); ALLC feed defectors, as in rung 4a's q = 0.6 attempts, and
  mutation also reintroduces ALLD directly. The screen does not separate these two routes.
- **The control.** With shuffled reputations, defectors take over at every μ, but at high μ mutation alone keeps
  every strategy present (ALLD 0.55 at μ = 0.05), so the test-control contrast shrinks there.

**Reading.** The screen passes for a test at **μ = 0.001**: cooperators 0.988 at the cooperative equilibrium (ALLC
0.075, ALLD 0.012), the shuffled control lost (ALLD 0.986 by generation 500). The fold is about 4.6 times higher in
μ, a parameter distance, not a stochastic safety margin. Sensitivity values for a pre-registration: 0.002, 0.004 and
0.005 (at 0.005 cooperators are still 0.734 at generation 500 but 0.074 asymptotically, so a 500-generation endpoint
alone cannot support a persistence claim). A Codex review (gpt-6.1-sol, medium) checked the mutation step, the reuse
of the records (reset each generation, recomputed from current shares) and the fixed points, and supplied the fold
location and the second basin.

**Limits and design notes for the stochastic test.** Noise-free and large-N. At N = 1000 and μ = 0.001 about one
mutant appears per generation (none in about 37% of generations), and demographic and encounter noise can push runs
out of the cooperative basin below the deterministic fold. The test should draw mutants exactly (Binomial per
strategy, then split equally), drop rung 4a's stop-at-fixation shortcut (mutation reintroduces strategies), register
the finite-time endpoint and a late-window persistence measure separately, and include an all-ALLD start as a basin
check.
