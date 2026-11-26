# Results: direct reciprocity threshold model (TFT against ALLD)

## Stage 0 (2026-11-26)

- Tests: 6 passed (`./.conda/bin/python -m pytest threshold_models/direct_reciprocity_tft`; run with system Python 3
  and numba 0.68.1 in a cloud session).
- Benchmark (500 one-generation runs per cell and start, 2 trajectory runs per cell; timing only, outcomes
  discarded): 135 ms of CPU per one-generation run of all 12 cells and both starts, 6.5 s per trajectory run of all
  cells; projected registered run 0.41 h on 2 cores, under the 5-hour budget → **20,000** one-generation runs per
  cell and start, as registered.

## Registered run (2026-11-26, code 5bfd738, pre-registration in `README.md`)

**Verdict: reproduced.** D1, D2 and D3 hold: TFT resists a rare ALLD exactly above `w*` (close to `c/b`), and a rare
TFT loses in every cell.

- Pre-registration `115d566`; model, tests and runner `732f6dd`; Stage 0 and launch commit `5bfd738`
  (`MODE = "run"`, 20,000 one-generation runs per cell and start). Run from a clean worktree at `5bfd738`,
  2 processes, wall time 1,610 s.
- Run command (repo root): `./.conda/bin/python -m threshold_models.direct_reciprocity_tft.run_registered`.
- Raw output: `data/registered_20261126_113051_summary.csv`, `data/registered_20261126_113051_verdict.txt`.

| Series | `w` | `w*` | far | ALLD rare: mean `Δx` [99% interval] | predicted `Δx` | TFT rare: mean `Δx` | 100 generations: ALLD lost / fixed (of 40), mean final |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B3 (`b` = 3, `c/b` = 0.333) | 0.15 | 0.3362 | yes | +0.000494 [+0.000435, +0.000553] | +0.000525 | −0.000932 | 8 / 0, 0.612 |
| | 0.25 | | yes | +0.000298 [+0.000240, +0.000356] | +0.000269 | −0.000989 | 26 / 0, 0.101 |
| | 0.30 | | no | +0.000101 [+0.000044, +0.000159] | +0.000119 | −0.001005 | 25 / 0, 0.059 |
| | 0.375 | | no | −0.000152 [−0.000209, −0.000095] | −0.000139 | −0.000949 | 36 / 0, 0.006 |
| | 0.45 | | yes | −0.000452 [−0.000507, −0.000396] | −0.000450 | −0.000998 | 40 / 0, 0.000 |
| | 0.55 | | yes | −0.000977 [−0.001032, −0.000922] | −0.000976 | −0.000967 | 40 / 0, 0.000 |
| B2 (`b` = 2, `c/b` = 0.5) | 0.30 | 0.5030 | yes | +0.000506 [+0.000447, +0.000565] | +0.000501 | −0.001014 | 14 / 1, 0.534 |
| | 0.40 | | yes | +0.000293 [+0.000234, +0.000352] | +0.000291 | −0.001016 | 20 / 0, 0.232 |
| | 0.45 | | yes | +0.000198 [+0.000140, +0.000255] | +0.000161 | −0.000978 | 26 / 0, 0.062 |
| | 0.55 | | no | −0.000226 [−0.000282, −0.000170] | −0.000169 | −0.000989 | 36 / 0, 0.004 |
| | 0.60 | | yes | −0.000383 [−0.000439, −0.000327] | −0.000384 | −0.000983 | 39 / 0, 0.000 |
| | 0.70 | | yes | −0.001001 [−0.001055, −0.000947] | −0.000975 | −0.000963 | 40 / 0, 0.000 |

The TFT-rare intervals (not shown) lie between −0.001071 and −0.000878, all below 0.

**Against the registered criteria.**

- **D1 holds:** in all nine far cells the interval of the ALLD-rare `Δx` lies on the predicted side of 0 (so did the
  three near cells, including B3 0.30 and 0.375 on either side of `w*` = 0.336).
- **D2 holds (11/12, needed 10):** the predicted change lies inside the 99% interval in every cell except B2 0.55,
  where it is just outside (−0.000169 against an upper bound of −0.000170).
- **D3 holds:** a rare TFT's frequency fell in all 12 cells, by about 0.001 per generation (a tenth of its share),
  hardly depending on `w`.

**What this shows.** In this population, TFT resists invasion by a rare ALLD exactly when `w` exceeds `w*`, which is
within 0.003 of Nowak's `c/b` for `N` = 1,000, and the size of the one-generation change matches the expected-payoff
prediction. But the same payoffs make TFT unable to spread from rare at any tested `w`: a lone TFT among defectors
pays `c` in the first round against almost every partner and is repaid by almost none. Direct reciprocity here is a
maintenance mechanism, as the site's spread-versus-maintenance table says. The 100-generation runs show drift on top
of selection: below the threshold ALLD rose on average but was still lost in some runs (8/40 to 26/40), and above it
ALLD was lost in 36-40 of 40.
