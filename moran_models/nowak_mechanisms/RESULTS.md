# Results: Moran Nowak mechanisms

Results from 2026-11-26 on. Earlier results stay inline in [`README.md`](README.md) (convention in `AGENTS.md`).

## Self-routing diagnostic (run 2026-11-26, code 3343b09, pre-registration `SELF_ROUTING_DIAGNOSTIC.md` with amendment A1)

**Verdicts, as registered:** indirect reciprocity **survives without self-routing**; network reciprocity
**self-benefit-dependent**; group selection **self-benefit-dependent**; kin selection **mixed**.

- Pre-registration at `5d0626f` (rebased as `a454b7f`), amendment A1 after an independent code review by a separate
  agent (standing in for Codex) at `a936c09`, launch commit `3343b09` (`MODE = "run"`). Run from a clean worktree at
  `3343b09`, 2026-11-26 about 08:57-09:33 CET; one process, system Python 3 in a cloud session.
- Run command (repo root): `./.conda/bin/python -m moran_models.interaction_kernel.utils.self_routing_diagnostic`
  with `MODE = "run"`. Wall time 2,158 s (832 runs).
- Stage 0: all 17 checks passed. **Reproduction:** all 288 main-cell `self`-arm replicates equal the stored
  2026-05-08 replicates (largest difference 0.0), so the `self` arm is the original comparison.
- Raw output: `moran_models/interaction_kernel/data/self_routing_diagnostic_20261126_093324_{replicates,summary}.csv`
  and `_verdicts.txt`.

**Cells of interest** (original mean gain ≥ +0.05). Mean gain over 8 seeds, successes out of 8, `noself` arm:

| Mechanism | Cell (`B`, `C`) | with self: gain, successes | without self: gain, successes | class |
| --- | --- | --- | --- | --- |
| Indirect reciprocity | (0.8, 0.1) | +0.877, 8 | +0.747, 8 | surviving |
| | (0.8, 0.2) | +0.834, 8 | +0.579, 8 | surviving |
| | (0.8, 0.3) | +0.719, 8 | +0.306, 2 | mixed |
| | (1.0, 0.1) | +0.878, 8 | +0.824, 8 | surviving |
| | (1.0, 0.2) | +0.870, 8 | +0.682, 8 | surviving |
| | (1.0, 0.3) | +0.843, 8 | +0.539, 8 | surviving |
| | (1.2, 0.1) | +0.879, 8 | +0.866, 8 | surviving |
| | (1.2, 0.2) | +0.878, 8 | +0.815, 8 | surviving |
| | (1.2, 0.3) | +0.875, 8 | +0.647, 8 | surviving |
| Network reciprocity | (0.8, 0.1) | +0.285, 2 | −0.108, 0 | dependent |
| | (1.0, 0.1) | +0.363, 4 | −0.109, 0 | dependent |
| | (1.2, 0.1) | +0.493, 8 | −0.108, 0 | dependent |
| | (1.2, 0.2) | +0.169, 0 | −0.113, 0 | dependent |
| Group selection | (0.8, 0.1) | +0.356, 4 | −0.105, 0 | dependent |
| | (1.0, 0.1) | +0.422, 5 | −0.103, 0 | dependent |
| | (1.2, 0.1) | +0.522, 8 | −0.105, 0 | dependent |
| | (1.2, 0.2) | +0.236, 0 | −0.110, 0 | dependent |
| Kin selection | (0.8, 0.1) | +0.417, 4 | +0.100, 0 | mixed |
| | (0.8, 0.2) | +0.196, 0 | −0.052, 0 | dependent |
| | (1.0, 0.1) | +0.522, 8 | +0.143, 0 | mixed |
| | (1.0, 0.2) | +0.298, 1 | +0.005, 0 | dependent |
| | (1.0, 0.3) | +0.125, 0 | −0.097, 0 | dependent |
| | (1.2, 0.1) | +0.634, 8 | +0.145, 0 | mixed |
| | (1.2, 0.2) | +0.417, 5 | +0.046, 0 | dependent |
| | (1.2, 0.3) | +0.171, 0 | −0.072, 0 | dependent |

Counts per mechanism (dependent / surviving / mixed): indirect 0 / 8 / 1 (needed 7 surviving: met); network 4 / 0 / 0
(needed 3 dependent: met); group 4 / 0 / 0 (met); kin 5 / 0 / 3 (needed 6 dependent or 6 surviving: neither, mixed).

**Seed-paired.** In every cell of every mechanism (52 cells including the descriptive ones), the `noself` final mean
trait was below the `self` one in 8/8 seeds, except kin selection at (1.2, 0.3) with 7/8.

**Descriptive high-benefit cells** (`C` = 0.2, no verdict). `noself` mean gain and successes:

| Mechanism | b/c 8 | b/c 12 | b/c 16 | b/c 24 |
| --- | --- | --- | --- | --- |
| Indirect reciprocity | +0.873, 8 | +0.879, 8 | +0.879, 8 | +0.879, 8 |
| Network reciprocity | −0.114, 0 | −0.067, 0 | +0.160, 0 | +0.221, 0 |
| Group selection | −0.111, 0 | −0.111, 0 | +0.129, 0 | +0.254, 1 |
| Kin selection | +0.141, 0 | +0.314, 1 | +0.309, 1 | +0.334, 3 |

**What this shows (at these settings, 250 steps).**

- **Network reciprocity and group selection:** the 2026-05-08 spread from a low start depended on the producer
  routing part of its own benefit to itself (one fifth under uniform routing). Without that self-route, helping
  fell in every cell of interest (0/64 successful runs over both mechanisms), and at b/c up to 24 it rose only slowly (no more than 1/8
  successes). Their engine results are weak altruism, like kin selection's step 1.
- **Indirect reciprocity:** reputation-weighted routing spread from a low start without any self-route in 8 of 9
  cells (66/72 successful runs over the nine cells), though always less than with it. Because network reciprocity
  without the self-route fails on the same grid, this spread is not explained by the grid's clustering alone: help
  that flows towards high-reputation neighbours, who are the helpers, carries it. That is the mechanism, implemented
  here with a perfect, free reputation signal (a site's reputation tracks its own helping).
- **Kin selection:** mixed. Without the self-route, kin-weighted routing still raised helping at `C` = 0.1 (+0.10
  to +0.15) and at high b/c (+0.31 to +0.33), but reached the success criterion in no main cell. This matches the
  ladder's step 0b (S-kin 0/20 at `B` = 1 without self-return).

**What this does not show.** It does not show that network reciprocity or group selection cannot support costly
cooperation, only that this implementation, at these settings and over 250 steps, did not; the rises at b/c 16-24
suggest a slow effect beyond the horizon. Indirect reciprocity's success is costly cooperation in the sense that the
helper's own direct payoff is −`C`·`h`, but its reputation signal is perfect and free; the stricter
`well_mixed_binary` model remains the reference for the mechanism under limited information.

**Predictions against outcome** (from the pre-registration): kin dependent 85% (mixed); network dependent 85%
(dependent); group dependent 70% (dependent); indirect dependent 40% (survives); network `noself` spreading only at
b/c 24, 50% (no high-benefit cell reached 4/8).
