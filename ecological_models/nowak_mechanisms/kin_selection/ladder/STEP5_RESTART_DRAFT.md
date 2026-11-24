# Step 5 restart: births into free space on the parental-care base (DRAFT pre-registration, 2026-11-24)

**Status: draft for discussion; not yet agreed, no code, no data.** Revised once after a Codex review
(gpt-6.2-sol, medium, 2026-11-24). The ladder line closed at its hard stop after R8 (`README.md`, `RESULTS.md`). This
draft reopens only the step that failed, step 5 of the site's stepwise table (births need free space), as a
**smaller step**: from the step-3 base (K1) instead of the full R4 ecology. It is not a new variant of R8.

## Why this step, and why smaller

- Every achieved step (1-4) has a fixed population: dead sites are refilled at once by a lottery among neighbours.
  Every attempt to leave that rule was made on top of R4, with energy stores, birth costs, starvation and limited
  income. R5a and R6 left the lattice almost full, R5b was skipped, R7 missed the vacancy bar and R7/R7b at breeding
  age 2 lost their populations. R8 produced vacant space at fixed traits, but in its care test own-young care settled
  at about 0.35 with local births (0/20 reached the endpoint); under global births it reached 0.99 in attempt 2 (free
  endowment 0.75 with birth cost 0.5) but stayed at 0.31 in attempt 1 (energy split, no birth cost).
- R8 therefore changed the population rule and the birth economy together, and its failure does not say which one
  blocked care. Following the agreed rule (on failure, take a smaller step, never patch down), this step changes
  **the population rule** on the simplest base where care already spread (K1: 18/20 local, 20/20 global, b/c 6).
- The new rule also changes other things that cannot be avoided (see Model): turnover, the number of birth attempts
  per occupant, and how strongly fecundity is selected. A matched fixed-occupancy arm (F6-refill) uses the same birth
  rule without free space, so that a failure can be attributed to free space rather than to those changes.
- If care spreads here, energy, starvation and limited food are added back one rung at a time, then movement
  (goal A). If it spreads with refill but not with free space, free space is the blocker on this base.

## Theory screen (before any code)

- **Fixed populations.** With local replacement and a fixed number of sites, the benefit of helping nearby relatives
  can be cancelled by competition among those relatives (Taylor 1992).
- **Empty sites.** When births need a vacant site and the population can grow or shrink, helping can raise local
  density, which can relax that competition. Lattice and pair-approximation studies (for example van Baalen and Rand
  1998; Mitteldorf and Wilson 2000; Lion and van Baalen 2008) report conditions under which altruism is favoured in
  such elastic, viscous populations. They are different models from this one, so this gives a direction, not a
  threshold.
- **The Kanwal-Gardner replication now running is not a test of empty space.**
  (`~/simulation_results/kanwal_gardner_viscosity/full_grid/PREREGISTRATION.md`, `run_simulation.py`.) It is an
  island model with non-overlapping generations and a fixed number of breeder slots: an under-filled patch fills its
  slots by sampling its surviving juveniles with replacement, and an empty patch gets fresh founders. Its escape from
  kin competition is dispersal that rises with the number of surviving juveniles per breeder, so a productive patch
  exports surplus relatives. Its strict prediction (altruism above Taylor's value 1/n) applies to the optimal
  dispersal strategy, for n > 1 and dispersal cost 0 < c < 1. The dispersal arm below is only loosely inspired by it
  (dispersal triggered by a full neighbourhood, which also changes access to breeding sites) and is **exploratory
  whatever the grid shows**.
- **Viability.** Without care the population is a contact-process-like lattice: persistence needs a high enough
  ratio of birth to death rate. No threshold is assumed; Stage S finds viable settings empirically.

## Model (from the base K1, attempt 1)

**Kept from K1.** Lattice and von Neumann neighbourhoods; clonal inheritance with mutation (probability 0.02 per birth,
SD 0.04, clipped to [0, 1]); `C` = 0.2; helper `i` sends `B·h_i` in equal shares to its living offspring present at
the start of the update, found by individual id at any distance, and the benefit is lost if it has none; the helper
always pays `C·h_i` and never receives its own benefit; care raises the recipient's fecundity; ids and parent ids as
in K1.

**Changed: births need free space.** Each update, from one snapshot of the start-of-update occupants:

1. **Payoff:** `W_i = 1 + R_i − C·h_i`, as in K1.
2. **Deaths:** each occupant dies with probability `d`, independent of `h`; its site becomes vacant.
3. **Birth attempts:** each **surviving** occupant attempts one birth with probability `p_i = p0 · max(0, W_i)`.
   `p0` is chosen so that `p_i` <= 1 at the test level (below). An attempting occupant with at least one vacant grid
   neighbour draws its target uniformly among them; with none, the attempt fails.
4. **Resolution:** a site claimed by several parents goes to one of them uniformly at random. `W` already acts
   through the attempt probability; a second selection on `W` (R8's softmax) is not added.
5. **Birth:** the newborn takes the parent's `h` (with mutation), lineage label, a fresh id and `parent_id`.

**What else changes against K1 (stated, not avoided).** K1 used `d` = 0.5, filled every dead site by a softmax
lottery (temperature 0.12) over `W` among start-of-step occupants, and let an occupant that died in that step still
parent, possibly more than once. Here turnover is set by `d`, each survivor gets at most one attempt per update, and
selection on `W` is linear in the attempt probability. F6-refill holds these changes fixed and removes only the free
space.

**Saturation.** `p0` must satisfy `p0 · (1 + 1.2)` <= 1 (a parent at `h` = 0 whose offspring receives care from a
parent at `h` = 1 at b/c 6), i.e. `p0` <= 0.45; clipping can then occur only in the b/c 12 and 24 arms, which are
descriptive, and the fraction of clipped attempts is reported per arm.

**Founders and starts.** Founders fill the whole lattice (as in earlier rungs), age 0, no parents. Low-helping start:
initial `h` 0.05, SD 0.02 (called a **low-helping start**, not a rare-lineage invasion). Common start (below-rule
control): initial `h` 0.9, SD 0.05.

## Stage S: demographic screen (fixed traits, no mutation, before any care test)

`h` = 0 everywhere and, separately, `h` = 0.6 everywhere (own-offspring care, `B` = 1.2); local births; also the same
two populations under refill (to check the refill arm is viable at that point). Grid: `p0` in {0.2, 0.3, 0.45} × `d`
in {0.05, 0.1, 0.2}; seeds 50-53; **6000 updates**; window = states after updates 1000-5999. **A point passes** if,
for both `h` levels and all four seeds under local births, the run does not go extinct and its window occupancy is
between 0.50 and 0.90 inclusive, and the fraction of surviving occupants with at least one vacant neighbour (after
deaths) is at least 0.10. **Choice:** the passing point with the highest `d`, then the lowest `p0`, written before
Stage M runs. Requiring the `h` = 0 population to persist on its own keeps care from being needed for survival (the
problem that stopped `../floor_control/`). Completeness as in R8 (exactly one finished run per job; an extinct run is
a valid result; missing, duplicated or truncated jobs make the screen incomplete and are rerun). **If no point
passes, the step stops.**

## Stage M: the care test (only if Stage S chose a point)

Seeds 0-19, 6000 updates, low-helping start unless stated; `C` = 0.2; b/c = B/C; window = states after updates
1000-5999; late window = states after updates 4000-5999.

| Arm | Care goes to | b/c | Births | Start | Role |
| --- | --- | --- | --- | --- | --- |
| F6-local | own offspring | 6 | vacant neighbour only | low | test |
| FN6-local | uniform over 4 neighbours (never self; share to an empty neighbour is lost) | 6 | vacant neighbour only | low | control |
| F6-refill | own offspring | 6 | no vacancies: each dead site is refilled at once by one parent drawn from its surviving neighbours with probability proportional to `p_i` (if none survives, from the whole lattice) | low | fixed-occupancy benchmark |
| F-below | own offspring | 0.25 | vacant neighbour only | common | below-rule control |
| F3 / F12 / F24-local | own offspring | 3, 12, 24 | vacant neighbour only | low | descriptive |
| F6-global | own offspring | 6 | random vacancy anywhere | low | secondary test (H2) |
| F6-dd | own offspring | 6 | vacant neighbour; if none, a random vacancy anywhere, surviving the move with probability 0.8 | low | exploratory |
| F-null | none (`B` = `C` = 0) | – | vacant neighbour only | low | drift reference |

Ten arms, 200 runs. **Viability per run:** not extinct and final occupancy >= 0.50. **Trait success per run:**
viable and final mean `h` over occupied sites >= 0.60. **Vacancy exposure per run:** late-window occupancy <= 0.90 and
late-window fraction of surviving occupants with a vacant neighbour >= 0.10.

**Classification (mechanical, in this order):**

1. **Not interpretable** if fewer than 18/20 runs are viable in F6-local, FN6-local or F-below (a care effect cannot
   then be told apart from population rescue or collapse). Reported, no verdict; counts as one of the two attempts.
2. **Not a step-5 test** if fewer than 15/20 F6-local runs have vacancy exposure (free space did not persist once
   care evolved). Reported, no verdict; counts as one of the two attempts; does not trigger attempt 2 automatically
   (decided with the user).
3. **Local failure** if F6-local has fewer than 15/20 trait successes, or F-below more than 2/20.
4. **Comparison failed** if F6-local leads FN6-local by fewer than 8 trait successes, or the one-sided Fisher
   p >= 0.025.
5. Otherwise **met**: at these settings, the own-offspring care package spread with births that need free space (step
   5 of the site table, without energy), against untargeted neighbour help.

**Reading a failure.** If F6-local fails while F6-refill reaches >= 15/20, the result is read as free space blocking
care on this base. If both fail, it is a missed endpoint for this birth-rule package; free space is not identified as
the blocker.

**Secondary (reported separately, no effect on the verdict).** H2: F6-global >= 15/20 trait successes, with mean
neighbour `h` correlation over occupied neighbour pairs in the window <= 0.10 (as in K1; otherwise H2 is reported as
not interpretable). F6-dd against F6-local: trait successes and mean final `h`, exploratory. Seeds are shared across
arms; tests are unpaired (Fisher), and seed-paired differences are reported descriptively.

**Descriptive.** Window and late-window occupancy and vacancy exposure; births and failed attempts per occupant;
clipped-attempt fraction; living offspring per occupant and benefit lost; parent-offspring and neighbour `h`
correlations; share of a parent's occupied neighbours that are its own offspring (as in DR8); mean `h` every 50
updates.

**Package-level claim.** FN6-local differs from F6-local in who receives, how many receive, how often a donor's
benefit is lost, and recipient distance. A positive result supports the own-offspring care package, not parentage
alone. A recipient-matched control (random non-offspring recipients, same count and dose) is possible but not
included here.

**Attempt 2 (fixed now; runs only if attempt 1 is local failure or comparison failed).** Care acts half on survival,
half on fecundity, with R1's passing rule (attempt 2 there, `λ` = 0.5): `d_i = d · exp(−0.5·R_i/T)` with `T` = 0.12,
and `W_i = 1 + 0.5·R_i − C·h_i`. Stage S is rerun for this rule over the same grid and criteria, and the point is
reselected (survival care changes density); if no point passes, attempt 2 stops. Same arms and classification.

## Checks (deterministic tests, before running)

Births only onto vacant sites; at most one birth per parent and per site per update; occupants that died in the update
do not breed; no vacancy, no births; refill arm keeps occupancy at 1 and draws parents only from surviving neighbours
(or the lattice if none); parent ids correct; care reaches only living offspring; with `B` = `C` = 0 the own-offspring
and neighbour-help rules give identical trajectories at the same seed; global and dispersal arms place offspring only
on vacancies; `p_i` <= 1 at b/c 6 at the chosen `p0`.

## Budget and hard stop

Stage S: 72 runs of 6000 updates (minutes). Stage M: 200 runs of 6000 updates per attempt, probably under an hour on
8 cores. Code gets a Codex review (gpt-6.2-sol, medium) before running; wording before commit. **Hard stop:** at most
two attempts (any outcome that counts as an attempt uses one). If neither is met, the Moran-derived route to step 5 is
closed, and the next route is to host kin-directed care in a model built with empty space and movement (Cooperative
Hunting or the Spatial Prisoner's Dilemma), decided with the user. No further variants of this rung.

## Predictions (mine, before any data)

- Stage S finds a passing point: about 65%.
- Attempt 1 met: about 35%.
- F6-refill >= 15/20: about 55%.
- H2 (F6-global >= 15/20): about 50%.
- Neither attempt met: about 45%.

## Limits

- Clonal inheritance with rare mutation; care raises fecundity (attempt 1) or survival and fecundity (attempt 2).
- The low-helping start is not a rare-lineage invasion into an established population of non-helpers.
- The dispersal arm changes where offspring go, how many survive the move and access to breeding sites; it does not
  isolate kin competition.
- No energy, food or movement: a positive result is step 5 on a minimal base, not goal A.
