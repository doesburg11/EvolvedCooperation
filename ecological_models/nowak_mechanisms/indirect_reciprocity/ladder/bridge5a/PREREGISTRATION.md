# Bridge to rung 5a: pre-registration DRAFT (2026-11-27)

**Status: draft, not agreed.** The user chose (2026-11-27) to reopen the indirect-reciprocity ladder for this bridge
line, with a hard stop of **at most two steps**, and chose definition option A: a pass is judged on cooperative
strategies and the shuffled control, as on every earlier rung; the discriminator share is reported, not tested.

## Why

Rung 5a (private views, simple standing) was not met: 45/100 test runs met both maintenance endpoints (bar 80;
shuffled 0/100). The external check of Kawakatsu, Kessinger and Plotkin (2024) found that, in the authors' model,
simple standing with private views kept cooperation without gossip. The bridge theory screen
(`THEORY_SCREEN_BRIDGE5A.md`, commit 6f7d606) ranked the parameter differences: raising b/c from 3 to 5 moves rung 5a's
finite-time mutation cliff furthest (0.00116 → 0.0067, 5.8×). The screen cannot predict stochastic pass rates (it
predicted 0.932 cooperators for rung 5a itself), so the bridge is simulated.

## Design: rung 5a unchanged except the listed setting

Model: rung 5a's `../rung5a/model.py`, unchanged. Runner: a thin adapter `bridge5a/run.py` that reuses
`../rung5a/run.py` (jobs, run_one, validate, benchmark, watcher) and sets, for the step being run and for both
running and validation: `B_` = 5.0; `E`, `Q` = 0.1, 0.8 (B1) or 0.02, 1.0 (B2); `SEEDS` = the step's block;
`CONDITIONS` = main condition only (test and shuffled arms); `DATA` = `bridge5a/data/b1/` or `bridge5a/data/b2/`,
each with its own attempt marker (rung 5a's outputs untouched). These are the **only** changes; the model's
parameters otherwise stay exactly rung 5a's. Everything else is exactly rung 5a's: N = 1,000, k = 10 encounters per
individual per generation, Wright-Fisher reproduction, c = 1, selection s = 0.1, observation o = 0.5, assessment
error a = 0.02, mutation μ = 0.001, start 10% ALLC / 80% DISC / 10% ALLD, 2,000 generations, private views reset each
generation, test and shuffled arms.

| Step | Change from rung 5a | Seeds | Runs only if |
| --- | --- | --- | --- |
| **B1** | b = 5 (b/c 5) | 3100-3199 | (always) |
| **B2** | b = 5, execution error e = 0.02, consultation q = 1 | 3200-3299 | B1 is a valid **not met** |

B2 bundles two further changes (the next two levers in the screen) because the user's two-step limit allows no
third step; a B2 pass would not say which of the two mattered.

**Theory screen values (same mean field, calculation only):** B1 cooperators 0.966 late, shuffled 0.014, final
ALLC/DISC/ALLD 0.494/0.472/0.034, cliff μ ≈ 0.0067 (base μ at 0.15 of it). B2 (screen row "B2" in
`theory_output.txt`): boundary 0.366, cooperators 0.984 late, shuffled 0.015, final ALLC/DISC/ALLD
0.605/0.379/0.016, cliff μ ≈ 0.024.

## Criteria: exactly rung 5a's

**Met** if at least 80/100 test runs meet both endpoints (cooperators, ALLC + DISC, ≥ 0.8 at generation 500, and a
mean cooperator share ≥ 0.8 over generations 1,501-2,000, in the same run) and the shuffled arm meets each endpoint in
at most 20/100. Validity, in-model checks, sanity rule, benchmark gate (at most 40 CPU-hours per step, projected from
seed 9999 over 100 generations at that step's parameters, trajectory not read; rung 5a's formula projects the step's
200 runs; launch only if at most 40 CPU-hours), heartbeat watcher (a sampled check: 100-generation heartbeats, 60 s
polling) and the one-repair rule: rung 5a's. Every run resets its random stream to its seed; arms are paired by seed
identifier, not by matched encounters. The
reported-only conditions of rung 5a (μ = 0.002, all-DISC, all-ALLD, image scoring) are **not** run: 200 runs per step.

**Reported, not tested (option A):** per run, DISC_g500 (DISC share at generation 500) and DISC_window (mean DISC
share over generations 1,501-2,000); per arm, their means and the numbers of runs with DISC_g500 ≥ 0.5 and with
DISC_window ≥ 0.5; the ALLC and ALLD shares; the three criterion counts (test joint, shuffled per endpoint); and rung
5a's diagnostics with its definitions (realised help rate, disagreement penalty, undefined when its denominator is
zero; good-view shares per strategy over generation 1 only). The adapter adds these summaries from the saved
trajectories.

## What follows from each outcome

**Transition rule.** B2 starts only after all 200 B1 runs pass validation and B1 is **not met** for any reason
(including failure only of the shuffled criterion). A benchmark rejection, invalid run or technical no-verdict in B1
does not authorise B2; a permitted repair must resolve B1 first.

- **B1 met:** the increased-benefit setting meets the registered maintenance-and-control criterion. Other things
  changed with b (payoff and selection magnitudes) and the seeds differ from rung 5a's, so this does not identify the
  cause of rung 5a's failure. The ladder cannot simply continue from rung 5a at b/c 5: rungs 2-4b were confirmed at b/c 3. Re-confirming them at b/c 5 (as the q = 0.8 rebase did) and re-running
  rung 5a there would be a **new proposal** needing the user's agreement; it is outside this two-step line.
- **B1 not met, B2 met:** the three-change setting meets the criterion; no attribution between b, e and q. If B1
  failed only on the shuffled criterion, that is reported as such, not as a test-arm failure explained by B2.
- **Both validly not met:** neither tested setting meets the criterion; the bridge line ends at its hard stop.
  Other settings (o, N, μ), interactions and structural differences (updating rule, re-judging schedule) remain
  unresolved.
- **A technical stop** gives no verdict and no progression (one documented repair allowed per step).

## Hard stop

At most two steps (B1, B2). No other settings, seeds or conditions. No relabelling of a scientific failure as a
technical defect.

## Interpretation limits

As rung 5a: maintenance of cooperative strategies from a cooperative start over 2,000 generations at the setting
tested, not recovery, spread from rare or indefinite stability. With a large ALLC share, the result is cooperation
in an ALLC-DISC mixture, not dominance of discriminators. A low shuffled count supports the importance of
recipient-specific information; it is consistent with, not proof of, discriminators sustaining cooperation by
excluding defectors.

## Forecasts (mine, before any data)

B1 met: 70%. B1 test arm with DISC ≥ 0.5 over generations 1,501-2,000 in at least half of its runs: 45%. If B1 is not
met, B2 met: 60%.
