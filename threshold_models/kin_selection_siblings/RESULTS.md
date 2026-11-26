# Results: kin selection threshold model (sibling alarm calls)

## Registered run (2026-11-26, code 9132218, pre-registration and amendment A1 in `README.md`)

**Verdict: Hamilton's rule reproduced.** Q1 (direction), Q2 (size of the one-generation change) and Q3 (`r`
against `p`) all hold.

- Pre-registration committed at `1636a81` before any model code; amendment A1 (two puddles per sexual home) and the
  code, 9 tests and runner committed at `9132218` before the registered run. The run was made from a clean worktree
  at `9132218`.
- Run command (repo root): `./.conda/bin/python -m threshold_models.kin_selection_siblings.run_registered`
  (made with the system Python 3 in a cloud session; NumPy, SciPy 1.18.1). Wall time 16 s.
- Raw output: `data/registered_20261126_085959_summary.csv`, `data/registered_20261126_085959_q1_trajectories_every10.csv`
  (every 10th generation), `data/registered_20261126_085959_verdict.txt`.
- No review of the code by Codex; an independent agent reviewed the companion self-routing diagnostic, not this
  model.

| Cell | `b·r − c` | naive `b·p − c` | Q1: mean Δ200 [95% CI] | runs up / down | Q2: predicted | Q2: realised mean [99% CI] | `r̂` | `p̂` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S3-0.80 | +0.20 | +0.70 | +0.470 [+0.454, +0.487] | 40 / 0 | +0.00471 | +0.00452 [+0.00368, +0.00536] | 0.500 | 0.749 |
| S3-0.90 | +0.10 | +0.60 | +0.344 [+0.290, +0.397] | 39 / 1 | +0.00237 | +0.00223 [+0.00141, +0.00306] | 0.500 | 0.749 |
| S3-1.00 | 0 | +0.50 | +0.017 [−0.073, +0.106] | 22 / 18 | 0 | +0.00003 [−0.00081, +0.00088] | 0.500 | 0.749 |
| S2-0.30 | +0.20 | +0.45 | +0.491 [+0.483, +0.499] | 40 / 0 | +0.00679 | +0.00679 [+0.00600, +0.00758] | 0.500 | 0.750 |
| S2-0.40 | +0.10 | +0.35 | +0.424 [+0.391, +0.457] | 40 / 0 | +0.00342 | +0.00311 [+0.00231, +0.00391] | 0.500 | 0.750 |
| S2-0.50 | 0 | +0.25 | +0.038 [−0.047, +0.123] | 22 / 18 | 0 | +0.00031 [−0.00047, +0.00110] | 0.500 | 0.750 |
| **S2-0.60** | **−0.10** | **+0.15** | **−0.417 [−0.458, −0.376]** | 1 / 39 | −0.00347 | −0.00358 [−0.00436, −0.00279] | 0.500 | 0.750 |
| **S2-0.70** | **−0.20** | **+0.05** | **−0.498 [−0.501, −0.496]** | 0 / 40 | −0.00698 | −0.00658 [−0.00736, −0.00580] | 0.500 | 0.750 |
| A2-0.80 | +0.20 | +0.20 | +0.493 [+0.488, +0.497] | 40 / 0 | +0.00703 | +0.00671 [+0.00608, +0.00735] | 1.000 | 1.000 |
| A2-1.00 | 0 | 0 | +0.011 [−0.067, +0.088] | 24 / 16 | 0 | +0.00026 [−0.00038, +0.00091] | 1.000 | 1.000 |

**Against the registered criteria.**

- **Q1 holds:** all 7 non-neutral cells have their 95% interval on the predicted side of 0 (needed 7/7); all 3
  neutral cells have an interval containing 0 (needed 2/3).
- **Q2 holds:** the predicted one-generation change lies inside the 99% interval of the realised mean in 10/10
  cells (needed 9/10).
- **Q3 holds:** in every sexual cell `r̂` = 0.500 (within 0.02 of 0.5), `r̂_reg` = 0.499-0.500 (within 0.03) and
  `p̂` = 0.749-0.750 (within 0.03 of 0.75). Pairs per cell: 500,466 (n = 3), 249,510 (sexual n = 2), 249,128
  (asexual n = 2). Within one `n`, alarm events are the same in every cell because the seeds are shared and the
  noticer's death is drawn after the event is recorded.

**What this shows.**

- In this model, costly help to siblings evolves exactly where `b·r − c` is positive, stays neutral where it is 0,
  and is lost where it is negative, from a 50/50 start and at a real net cost (the alarm-sounder dies with
  probability `c`; a coward noticer survives).
- **The `r`-versus-`p` distinction is decisive.** In S2-0.60 and S2-0.70, the naive rule with `p` (the 0.75
  probability that a sibling carries the allele) predicts spread; Hamilton's rule with `r` = ½ predicts loss.
  Altruism was lost in 39/40 and 40/40 runs.
- The size of the one-generation change matches the exact expression `a·f(1 − f)·(b·r − c)/D` in every cell, not
  only its sign.

**What this does not show.** Kin association is built in (siblings stay together) and competition is global (homes
are a lottery). These are the conditions under which the rule is exact. The model shows the rule and the
`r`-versus-`p` distinction, not when relatives meet or compete in an ecology (see the ladder and
`STEP5_EMPTY_SITES.md` for that).
