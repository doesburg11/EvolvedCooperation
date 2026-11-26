# Results: network reciprocity threshold model (lattice, death-birth)

## Stage 0 (2026-11-26, code at the commit that adds this section)

- Tests: 8 passed (`./.conda/bin/python -m pytest threshold_models/network_reciprocity_lattice`; run with system
  Python 3 and numba 0.68.1 in a cloud session). One test was corrected before Stage 0: its own choice of `w` = 0.5
  made fitness negative; the runner now refuses any cell where `1 − w − w·c·k` ≤ 0 (all registered cells pass).
- Neutral check (`w` = 0, 200,000 runs per graph): graph V `ρ̂·N` = 1.004 [0.947, 1.062], graph M 1.006
  [0.949, 1.064]; both contain 1 → pass.
- Benchmark (20,000 runs per cell, timing only, counts discarded): 48-84 µs per run; projected registered run at
  `R` = 1,000,000: 0.10 h on 2 cores, under the 5-hour budget → **`R` = 1,000,000** as registered.

## Registered run (2026-11-26, code f4e1f5c, pre-registration in `README.md`)

**Verdict: not reproduced, as registered: T1 holds, T2 fails in both graphs.** The direction of selection matched
the rule in all nine far cells, but the registered straight-line estimate of the threshold missed the theoretical
value in both graphs, because `ρ̂·N` is clearly curved in `b` at these selection intensities (residual pattern
below). The near cells and a post hoc local estimate (labelled as such) put the crossing close to the finite-`N`
threshold, and graph M's crossing lies above `k`, as the finite-`N` rule says.

- Pre-registration `ab796f9`; model, tests and runner `00991c6`; Stage 0 and launch commit
  `f4e1f5c` (`MODE = "run"`, `RUNS` = 1,000,000). Run from that commit in a cloud session (system Python 3,
  numba 0.68.1), 2 processes, wall time 391 s.
- Run command (repo root): `./.conda/bin/python -m threshold_models.network_reciprocity_lattice.run_registered`.
- Raw output: `data/registered_20261126_103211_summary.csv`, `data/registered_20261126_103211_verdict.txt`.
- Check after the run: V `b` = 3 and M `b` = 4 both had exactly 5,475 fixations. Their first 100,000 runs give 568
  and 556 fixations, and swapping seeds between the two cells gives 569 and 563, so the cells are independent and
  the equal totals are a coincidence.

| Graph | `b` | `b*` | `ρ̂·N` [99% interval] | predicted | far cell | residual of the straight line |
| --- | --- | --- | --- | --- | --- | --- |
| V (`k` = 4, `w` = 0.01) | 2 | 4.261 | 0.294 [0.280, 0.308] | below | yes | +0.083 |
| | 3 | | 0.547 [0.528, 0.567] | below | yes | −0.081 |
| | 4 | | 0.889 [0.865, 0.913] | below | no | −0.156 |
| | 5 | | 1.345 [1.315, 1.375] | above | no | −0.118 |
| | 6 | | 1.891 [1.856, 1.926] | above | yes | +0.011 |
| | 8 | | 3.085 [3.041, 3.130] | above | yes | +0.371 |
| M (`k` = 8, `w` = 0.0025) | 4 | 9.333 | 0.547 [0.528, 0.567] | below | yes | +0.024 |
| | 6 | | 0.704 [0.682, 0.725] | below | yes | −0.009 |
| | 8 | | 0.866 [0.842, 0.890] | below | yes | −0.036 |
| | 9 | | 0.982 [0.956, 1.007] | below | no | −0.015 |
| | 11 | | 1.181 [1.154, 1.209] | above | yes | −0.004 |
| | 14 | | 1.511 [1.480, 1.543] | above | yes | +0.043 |

**Against the registered criteria.**

- **T1 holds:** all nine far cells have their 99% interval on the predicted side of 1.
- **T2 fails:** straight-line crossing V 3.891 [3.873, 3.909] against `b*` 4.261; M 9.041 [8.958, 9.129] against
  9.333. Neither interval contains the theoretical value.
- **H2 (secondary): yes.** Graph M's interval lies entirely above `k` = 8.
- **H3 (secondary):** V 4 below 1 and V 5 above 1, as predicted; M 9 at 0.982 with an interval that reaches 1.007,
  below 1 as predicted but not separated from it.

**Why T2 failed (reading, not a registered test).** The residuals are U-shaped in graph V (positive at both ends,
negative in the middle) and weakly so in M: `ρ̂·N` rises faster than linearly in `b`, so selection is not weak
enough at `w` = 0.01 (V) for the weak-selection straight line over `b` = 2-8. A straight line through a convex curve
crosses 1 too early, which is the direction of both misses. The pre-registration named this risk ("curvature at these
`w` may bias the crossing", T2 predicted at 70%) but did not guard against it.

**Post hoc, descriptive only.** Interpolating linearly between the two cells that bracket 1 gives crossings of
4.243 (V, between `b` = 4 and 5) and 9.184 (M, between 9 and 11), against 4.261 and 9.333. This estimate was chosen
after seeing the data and carries no verdict.

**What this shows.** On a lattice with death-birth updating and **no benefit routed back to the helper**, a single
cooperator's fixation probability is below neutral at low `b/c` and above it at high `b/c` in every far cell, and
the change of sign lies between `b` = 4 and 5 (V) and between 8 and 11 (M; most likely between 9 and 11), above
the large-`N` values `k` = 4 and 8 in both. Network reciprocity therefore favours costly cooperation here, without self-benefit, in contrast with the
Moran engine's wrapper (`moran_models/nowak_mechanisms/RESULTS.md`). The registered test of the exact threshold
location failed because of the estimator, not because of a sign error; a test of the location needs either weaker
selection or cells closer to `b*`, which would be a new pre-registration.
