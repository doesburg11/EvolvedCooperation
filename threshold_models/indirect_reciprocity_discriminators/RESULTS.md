# Results: indirect reciprocity threshold model (discriminators against ALLD)

## Stage 0 (2026-11-26)

- Tests: 5 passed (`./.conda/bin/python -m pytest threshold_models/indirect_reciprocity_discriminators`; system
  Python 3 and numba 0.68.1 in a cloud session), including encounter-by-encounter play on a small population
  against the closed-form payoffs.
- Benchmark (500 one-generation runs per cell and start, 2 trajectory runs per cell; timing only, outcomes
  discarded): projected registered run 0.02 h on 2 cores → **20,000** one-generation runs per cell and start, as
  registered.

## Registered run (2026-11-26, code 4c9041b, pre-registration in `README.md`)

**Verdict: reproduced.** D1, D2 and D3 hold: discriminators resist a rare ALLD exactly above `q*` (close to `c/b`),
and a rare discriminator loses in every cell.

- Pre-registration `08b5857`; model, tests and runner `93a4e27`; Stage 0 and launch commit `4c9041b`. Run from a
  clean worktree at `4c9041b`, 2 processes, wall time 61 s.
- Run command (repo root): `./.conda/bin/python -m threshold_models.indirect_reciprocity_discriminators.run_registered`.
- Raw output: `data/registered_20261126_123048_summary.csv`, `data/registered_20261126_123048_verdict.txt`.

| Series | `q` | `q*` | far | ALLD rare: mean `Δx` [99% interval] | predicted | DISC rare: mean `Δx` | 100 generations: ALLD lost (of 40), mean final |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B3 (`b` = 3, `c/b` = 0.333) | 0.15 | 0.3362 | yes | +0.000482 [+0.000424, +0.000541] | +0.000459 | −0.000849 | 23, 0.286 |
| | 0.25 | | yes | +0.000228 [+0.000170, +0.000286] | +0.000213 | −0.000780 | 23, 0.108 |
| | 0.30 | | no | +0.000080 [+0.000023, +0.000137] | +0.000089 | −0.000677 | 31, 0.040 |
| | 0.375 | | no | −0.000092 [−0.000149, −0.000035] | −0.000096 | −0.000630 | 37, 0.004 |
| | 0.45 | | yes | −0.000291 [−0.000348, −0.000234] | −0.000281 | −0.000567 | 39, 0.000 |
| | 0.55 | | yes | −0.000513 [−0.000569, −0.000458] | −0.000527 | −0.000446 | 40, 0.000 |
| B2 (`b` = 2, `c/b` = 0.5) | 0.30 | 0.5030 | yes | +0.000388 [+0.000329, +0.000446] | +0.000364 | −0.000694 | 21, 0.190 |
| | 0.40 | | yes | +0.000159 [+0.000101, +0.000217] | +0.000185 | −0.000579 | 26, 0.054 |
| | 0.45 | | yes | +0.000078 [+0.000021, +0.000136] | +0.000095 | −0.000528 | 32, 0.011 |
| | 0.55 | | no | −0.000029 [−0.000086, +0.000029] | −0.000084 | −0.000436 | 33, 0.006 |
| | 0.60 | | yes | −0.000179 [−0.000236, −0.000122] | −0.000174 | −0.000377 | 38, 0.001 |
| | 0.70 | | yes | −0.000329 [−0.000385, −0.000273] | −0.000354 | −0.000303 | 39, 0.000 |

ALLD was fixed in no 100-generation run. The DISC-rare intervals lie between −0.000904 and −0.000246, all below 0.

**Against the registered criteria.**

- **D1 holds:** all nine far cells on the predicted side. Near cells: B3 0.30 and 0.375 on the predicted sides of
  `q*` = 0.336; B2 0.55 below 0 in its mean but with an interval that contains 0.
- **D2 holds (12/12).**
- **D3 holds:** a rare discriminator fell in all 12 cells.

**What this shows.** Discriminators resist invasion by a rare defector exactly when the chance of knowing a
reputation exceeds `q*`, within 0.003 of Nowak's `c/b`, and the size of the change matches the prediction. A rare
discriminator still loses at every tested `q`, but less as `q` rises (from −0.00085 at `q` = 0.15 to −0.00030 at
0.70 for `b` = 3 and 2), because it is exploited less often; unlike a rare TFT in `direct_reciprocity_tft/`, whose
loss hardly depended on `w`. As in direct reciprocity, the condition is one of maintenance: indirect reciprocity holds
cooperation once common and does not start it below `q` ≈ 0.98.
