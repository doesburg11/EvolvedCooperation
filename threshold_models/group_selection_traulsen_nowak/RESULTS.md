# Results: group selection threshold model (Traulsen and Nowak multilevel selection)

## Stage 0 (2026-11-26)

- Tests: 6 passed (`./.conda/bin/python -m pytest threshold_models/group_selection_traulsen_nowak`; system Python 3
  and numba 0.68.1 in a cloud session).
- Benchmark (20,000 runs of each cell and 20,000 neutral runs per setting, timing only, outcomes discarded):
  0.39 ms per run per cell, 0.69 ms per neutral run; projected registered run 1.03 h on 2 cores, under the 5-hour
  budget → **`R` = 1,000,000, `R₀` = 2,000,000**, as registered.

## Registered run (2026-11-26, code 46a7595, pre-registration in `README.md`)

**Verdict: not reproduced, as registered: G-D fails and G-L fails in setting G1 (`n` = 10).** In setting G2
(`n` = 5) the rule is reproduced closely: the sign of `D` changes exactly between the cells around `b*`, and the
estimated crossing 1.637 [1.614, 1.660] contains the finite-`m` threshold 1.625 and excludes the large-`m` value
1.5. In G1, cooperators fix less often than neutral in every cell, up to `b` = 3.25; `D` rises with `b`, but the
straight line crosses 0 only at `b` ≈ 7.0, far above `b*` = 2.25.

- Pre-registration `9392ad6`; model, tests and runner `7147bac`; Stage 0 and launch commit `46a7595`
  (`MODE = "run"`). Run from a clean worktree at `46a7595` in a cloud session (system Python 3, numba 0.68.1),
  2 processes, wall time 3,893 s.
- Run command (repo root): `./.conda/bin/python -m threshold_models.group_selection_traulsen_nowak.run_registered`.
- Raw output: `data/registered_20261126_124949_summary.csv`, `data/registered_20261126_124949_verdict.txt`.
- After the run, `MODE` was set back to `"stage0"`.

`D` = `ρ̂_C/ρ̂_0 − 1` (0 = neutral; above 0 = selection favours cooperators). `R` = 1,000,000 runs per cell,
`R₀` = 2,000,000 neutral runs per setting.

| Setting | `b` | offset from `b*` | `D` [99% interval] | predicted | fixations |
| --- | --- | --- | --- | --- | --- |
| G1 (`n` = 10, `m` = 10, `b*` = 2.25) | 1.25 | −1 (outer) | −0.895 [−0.903, −0.887] | below | 1,173 |
| | 1.75 | −0.5 | −0.807 [−0.818, −0.795] | below | 2,168 |
| | 2.00 | −0.25 | −0.768 [−0.781, −0.756] | below | 2,597 |
| | 2.50 | +0.25 | **−0.690 [−0.704, −0.675]** | above | 3,481 |
| | 2.75 | +0.5 | **−0.655 [−0.671, −0.640]** | above | 3,863 |
| | 3.25 | +1 (outer) | **−0.604 [−0.621, −0.588]** | above | 4,435 |
| G2 (`n` = 5, `m` = 10, `b*` = 1.625) | 0.625 | −1 (outer) | −0.463 [−0.476, −0.449] | below | 13,420 |
| | 1.125 | −0.5 | −0.229 [−0.246, −0.213] | below | 19,241 |
| | 1.375 | −0.25 | −0.120 [−0.138, −0.102] | below | 21,977 |
| | 1.875 | +0.25 | +0.105 [+0.084, +0.126] | above | 27,595 |
| | 2.125 | +0.5 | +0.223 [+0.200, +0.245] | above | 30,532 |
| | 2.625 | +1 (outer) | +0.423 [+0.398, +0.448] | above | 35,530 |

**Against the registered criteria.**

- **G-D fails:** three of the four outer cells lie on the predicted side; G1 `b` = 3.25 does not (`D` < 0, predicted
  above 0).
- **G-L fails in G1, holds in G2.** G1: crossing 7.026 [6.662, 7.441] against `b*` = 2.25. G2: crossing 1.637
  [1.614, 1.660] against `b*` = 1.625.
- **Secondary.** Both intervals exclude `1 + n/m` (G1 2.0, G2 1.5). Neutral check `ρ̂_0·m(n − 1)`: G1 1.009,
  G2 0.999 (expected 1), so the neutral baseline is right in both settings. In G1 `b` = 2.0, `D` < 0 as the
  finite-`m` rule predicts, but so is every G1 cell.
- **Against my predictions:** G-D 85% and G-L 65%, both wrong. The intervals excluding `1 + n/m` (G1 60%, G2 40%)
  came out yes in both. `R` was not reduced (70%), as predicted.

**Possible explanation (post hoc, not tested).** The rule is derived for weak selection, `ω` → 0, with payoffs
summed over group mates. The selection terms in the rule's derivation scale with group size: within the group with
`(b + c(n − 1))·ω/2` and between groups with `(b − c)(m − 1)·ω/2`. At `b*` these are about 0.28 for G1 and 0.14 for
G2, so at `ω` = 0.05 selection is twice as strong in G1 as in G2. Within-group selection against cooperators may then
outweigh the between-group advantage more than the weak-selection rule allows. The model is the same code in both
settings, and G2 matches the rule to within 0.012, which makes a coding error specific to `n` = 10 unlikely but does
not rule it out. A new registered test with smaller `ω` in G1 (and more runs, since the signal shrinks with `ω`)
would decide this.

## Pre-registration 2, Stage 0 (2026-11-26, code 70133aa)

- Tests: 6 passed (same model; system Python 3 and numba 0.68.1 in a cloud session).
- Benchmark (20,000 runs per cell and 20,000 neutral runs, timing only, outcomes discarded): 0.295 ms per run per
  cell, 0.465 ms per neutral run; projected registered run 1.24 h on 2 cores, under the 5-hour budget →
  **`R` = 2,000,000, `R₀` = 4,000,000**, as registered.
