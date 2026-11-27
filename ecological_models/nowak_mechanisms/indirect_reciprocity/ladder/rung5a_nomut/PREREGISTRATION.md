# Rung 5a′: private views before mutation, pre-registration (2026-11-27)

**Outcome (2026-11-27): MET, 94/100 test against 0/100 shuffled; ALLD extinct in the 94 passing runs. See `RESULTS.md`.**

**Status: agreed with the user 2026-11-27 (about 21:50 CET), before the adapter was written or any run.** The user chose (2026-11-27) to reopen the ladder for this one step after the bridge's
post-hoc diagnosis (`../bridge5a/RESULTS.md`): it reorders the ladder so that private views come before mutation.
**Explicit exception:** this is a new branch agreed after seeing earlier results. It supersedes, for this single
experiment only, the ladder's stops after rung 5a (`../README.md`) and the bridge's hard stop. Rung 5a's and both
bridge failures stand unchanged; a pass establishes only this branch's criterion.

## Why

In the authors' model (Kawakatsu, Kessinger and Plotkin 2024), which has no mutation, simple standing with private
views kept cooperation. On our ladder, mutation (rung 4b) came before private views (rung 5a), and rung 5a failed
(45/100), as did both bridge steps (59, 60/100). In the bridge runs that failed, unconditional cooperators first rose
at discriminators' expense, then defectors rose. The hypothesis (not tested) is that mutation, which keeps
re-introducing defectors, is needed for the second phase. The order of ingredients is a design
choice. This step adds private views to the last working base without mutation (rung 4a attempt 3: q = 0.8, met
100/100) and leaves mutation for a later rung.

## Design

Rung 5a's model and runner, unchanged, through an adapter `rung5a_nomut/run.py` like the bridge's: it sets rung
5a's runner globals `CONDITIONS = {"main": (0.0, MAIN, ("test", "shuffled"))}`, `SEEDS = range(3300, 3400)`,
`DATA = rung5a_nomut/data/` and keeps `B_ = 3`, `E = 0.1`, `Q = 0.8` (rung 5a's); requires forked workers; no
step selection and no prerequisite. Rung 5a's attempt marker, seed-identifier pairing, generation conventions and
benchmark projection (over these 200 runs) are inherited. The only change from rung 5a:
**mutation μ = 0** (rung 4a attempt 3's setting). Everything else is rung 5a's: N = 1,000, k = 10, b/c 3, s = 0.1,
q = 0.8, o = 0.5, e = 0.1, a = 0.02, private views reset each generation, start 10% ALLC / 80% DISC / 10% ALLD,
2,000 generations, test and shuffled arms, **seeds 3300-3399** (fresh). Main condition only: 200 runs.

**Theory screen (rung 5a's mean field at μ = 0):** cooperators 1.000 at generation 500 and over generations
1,501-2,000; final ALLC / DISC / ALLD 0.296 / 0.704 / 0.000; shuffled 0.000.

## Criteria: exactly rung 5a's

**Met** if at least 80/100 test runs meet both endpoints (cooperators ≥ 0.8 at generation 500, and mean
cooperators ≥ 0.8 over generations 1,501-2,000) and the shuffled arm meets each endpoint in at most 20/100. Rung 5a's
validity rules, in-model checks, sanity rule, benchmark gate (40 CPU-hours), watcher and one-repair rule apply.
**Added validity check (μ = 0):** before a verdict is accepted, the adapter requires every run's mutation audit
columns (mutants and transfers) to be zero in every generation and its mutant summaries to be zero; otherwise
**no verdict**.

**Reported, not tested:** per run and arm, the ALLD extinction generation, the first g in [0, 2000] with ALLD
count zero (null if none), the number of runs per arm with extinction, and a check that ALLD never reappears after
it (it cannot without mutation); DISC_g500, DISC_window and the counts with DISC ≥ 0.5 (as in the bridge); final composition;
rung 5a's diagnostics.

## Hard stop

This one step. A valid **not met** ends it; no other settings. A **pass** puts private views on the ladder (as a
reordered rung 5a′) but does not by itself authorise the next rung: mutation on top of private views already failed
(rung 5a), so the next step needs a new proposal and the user's agreement.

## Interpretation limits

A pass would show maintenance under private views **without recurrent mutation**: once defectors are lost they cannot
return, so part of the result may come from losing the threat rather than resisting it. The extinction times are
reported so that this is visible. It shows nothing about recovery, spread from rare or resistance to re-invading
defectors. A valid failure would mean that this fixed setting did not meet the registered maintenance-and-control criterion;
the report states which component failed (test count, joint endpoint or control). As in rung 5a: 2,000 generations
from a cooperative start, cooperative strategies (ALLC + DISC) rather than the measured help rate, and no claim of
indefinite stability.

## Forecast (mine, before any data)

Met: 90%. ALLD extinct by generation 500 in at least 80 test runs: 70%.
