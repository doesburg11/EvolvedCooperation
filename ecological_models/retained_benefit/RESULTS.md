# Retained Benefit: results

## Retained-fraction sweep (run 2026-11-22/23): P1, P2, P3 and P4 all met

Run 2026-11-22 23:29 to 2026-11-23 00:51 CET with `utils/run_r_sweep.py` (340 runs, 5 workers, 82 min), after the
pre-registration, its amendments A1 and A2, the runner, the analysis and the tests were committed (a14eee1). Rules:
README, "Pre-registration: retained-fraction sweep". Raw output in `data/r_sweep/` (`runs.csv`, `trajectories.csv`,
`manifest.json`, `verdict.json` from `utils/analyze_r_sweep.py`).

**Validity: passed.** Before the sweep, the website-demo arm reproduced the published replay exactly at the
exporter's precision, steps 0–250. All 340 runs were present and 1000 steps long, every row's parameters matched
its registered arm, and every outcome was finite and in [0, 1]. The manifest records `module_tree_clean: false`:
the check ran at the end of the run, when the run's own untracked output (`data/r_sweep.partial/` and the run log)
was inside the module. A separate check right after the run, before any later edit, found no tracked change in the
module since a14eee1 (`git diff a14eee1`). The runner now excludes `data/` from that check.

**Outcome:** mean cooperation over steps 901–1000, per run; each cell compared with the seed-matched neutral arm
(b = c = 0) by one-sided paired t-tests, p < 0.01. The neutral arm ended at **0.190** (start 0.120).

| r | b/c = 3 | b/c = 5 | b/c = 8 |
| --- | --- | --- | --- |
| 0.0 | 0.090 ↓ | 0.188 | 0.641 ↑ |
| 0.1 | 0.112 ↓ | 0.412 ↑ | 0.762 ↑ |
| 0.2 | 0.194 | 0.594 ↑ | 0.840 ↑ |
| 0.3 | 0.327 ↑ | 0.680 ↑ | 0.879 ↑ |
| 0.4 | 0.438 ↑ | 0.761 ↑ | 0.920 ↑ |
| 0.5 | 0.566 ↑ | 0.817 ↑ | 0.935 ↑ |
| 0.6 | 0.632 ↑ | 0.843 ↑ | 0.940 ↑ |
| 0.7 | 0.673 ↑ | 0.877 ↑ | 0.945 ↑ |
| 0.8 | 0.733 ↑ | 0.897 ↑ | 0.954 ↑ |
| 0.9 | 0.770 ↑ | 0.921 ↑ | 0.959 ↑ |
| 1.0 | 0.792 ↑ | 0.932 ↑ | 0.962 ↑ |

Mean over 10 seeds. ↑ rise, ↓ decline against neutral (paired, p < 0.01); blank: flat. Per-cell p-values in
`verdict.json`.

- **P1 met:** at b/c = 8, all 11 cells rose (p ≤ 9e-8).
- **P2 met:** at b/c = 3, r = 0, cooperation did not rise. (Observed in addition, not part of the registered
  criterion: it declined below neutral, 0.090 against 0.190, p = 8e-7.)
- **P3 met:** at b/c = 3, the r = 1.0 cell's tail mean was 0.70 above the r = 0.0 cell's (paired p = 3e-11).
- **P4 met:** at b/c = 3, r = 1.0 rose above neutral (0.792 against 0.190, p = 1e-10).

As registered (amendment A2), P2–P4 together are **consistent with** cooperation needing enough retained benefit at
b/c = 3: full retention improved on zero retention and rose above neutral, while zero retention did not rise. This
does not establish that retention is necessary.

**Exploratory (not registered tests).**

- *Where the rise starts follows the lone helper's direct payoff.* The smallest r from which every higher r rises
  was 0.3 at b/c = 3, 0.1 at b/c = 5 and 0.0 at b/c = 8. Against the theory screen's direct payoff of a helper with
  no same-lineage neighbours (own share only), cells declined where it was clearly negative (b/c = 3, r = 0 and 0.1:
  −0.040, −0.016), were flat where it was about zero (b/c = 3, r = 0.2: +0.008; b/c = 5, r = 0: 0.000) and rose
  where it was clearly positive. The onset pattern is aligned with the sign of the producer's own return, i.e. with weak
  versus strong altruism for a lone helper, but that is not evidence that this payoff causes the onset. Retained
  benefit always includes the producer's own share, so the sweep does not separate benefit kept by same-lineage
  neighbours from that self-return.
- *Neutral drift is substantial.* With no selection, mean cooperation rose from 0.120 to 0.130 by step 250 and 0.190
  by step 1000, from mutation followed by clamping at 0. At step 250 the neutral arm ranged 0.117–0.151 over seeds,
  so the original website demo's rise to 0.147 at step 250 (b/c = 3, r = 0.35) was within neutral drift. Several
  swept arms had already moved clearly away from neutral by step 250 (for example b/c = 3, r = 1.0: about 0.26;
  b/c = 8, r = 0.0: about 0.17), and the differences grew by step 1000.
- *Lineage structure.* Final local assortment (cell means) was 0.63 in the neutral arm and 0.63–0.80 across the
  swept cells. The largest lineage held 23% of the lattice in the neutral arm and, on average, 19–61% in the swept
  cells (lowest at b/c = 3, r = 0.1; highest at b/c = 5, r = 0.7). In 2 of the 330 swept runs (b/c = 5, r = 0.6, seed 1; b/c = 8, r = 0.7, seed 4), and none of the
  neutral runs, a single lineage held the whole lattice at step 1000; once that happens every neighbour shares the
  producer's lineage, so retention no longer separates relatives from others.

**What this shows and does not show.** In this model and at these settings, outcomes were associated with the
retained fraction: at b/c = 3, cooperation was below neutral at r = 0 and about 0.8 at r = 1; at b/c = 8 it rose
at every r. One grid size, one neighbourhood, one
mutation setting, 1000 steps, 10 seeds per cell. The design does not identify whether this reflects the
producer's own share, benefit to relatives, or both. For that reason, under the broad definition in
`ecological_models/nowak_mechanisms/kin_selection/README.md`, the sweep does not count as kin selection (it sits with
step 1 of the site's stepwise table).

### Review

Two Codex passes (gpt-6.2-sol) on the pre-registration and code before the run found a replay check that would
have failed on export rounding, an analysis that crashed on a missing arm before its validity gate, spurious
p-values from constant samples, a seed pairing the Welch tests ignored (confirmed real across all 34 arms), an
interpretation that P2 and P3 alone could pass without any rise, and fragile worker and output handling; all fixed
before the run (amendments A1, A2).
