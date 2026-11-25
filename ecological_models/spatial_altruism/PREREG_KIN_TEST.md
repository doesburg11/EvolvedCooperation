# Mitteldorf and Wilson (2000) as a kin-selection test: pre-registration (2026-11-25)

**Result (2026-11-25): not met, local failure (0/50 at harshness 0.9); the paper's 0.96 failed the screen. See
`RESULTS_KIN_TEST.md`.**

**Status: agreed with the user 2026-11-25 (including the Stage S rule and the annotation of the site's reference row if the paper's point fails the screen); no data.** Revised once after a Codex review (gpt-6.2-sol, medium,
2026-11-25). One informal run was made before drafting (seed 1, harsh setting, altruists starting at 5%): the
population went fully extinct by step 233. It motivated the demographic screen; seed 1 is not used below.

## Why

On the site's stepwise table
([Kin Selection: Definition and Progress](https://humanbehaviorpatterns.org/evolved-cooperation/kin-selection-progress)),
Mitteldorf and Wilson's (2000) model in its harsh setting is a reference row marked "–": costly help survives with
empty sites, but in one seeded run that starts with 39% altruists, without a control. This test asks the
definition's third condition directly: **does costly help spread from rare to a pre-set endpoint in this
variable-density model, and does it fail when relatedness among neighbours is broken?**

**What a positive result would and would not be.** In this model every site, occupied or empty, is redrawn each step
by a local lottery, so occupied sites are replaced too; it is a variable-density replacement model in which
vacancies can be recolonised, not a model where births go only into free space. A ✓ would turn the reference row
into a tested result for help to non-offspring neighbours (by viscosity) with empty space present; it would **not**
count as step 5's milestone (births that need free space) and has no energy, food or movement.

## The model (unchanged: `altruism_model.py`, NetLogo-faithful port)

51 × 51 torus. Each site is altruist, selfish or empty. Every step, synchronously: altruist fitness
`1 − c + b·(altruists among self + 4 neighbours)/5`, selfish `1 + b·(...)/5`, empty `harshness`. Each site's next
state is drawn by a lottery over itself and its 4 neighbours: each altruist candidate contributes its fitness to the
altruist weight, each selfish candidate to the selfish weight, each empty candidate `harshness` to the empty weight,
and `disease` is added once per site to the empty weight (the `steady_state` variant). The site's own occupant is one
of the candidates, so it can be replaced by its own descendant. Types are inherited exactly (no mutation); every
site is redrawn every step (non-overlapping generations).

**Cost.** Holding neighbours fixed, switching from selfish to altruist changes an individual's own lottery weight by
`b/5 − c`; with b = 0.468 and c = 0.156 that is −0.062, a net direct cost (strong altruism by the definition's first
condition). Helping also raises occupied neighbours' weights, including competitors', so this is a difference in
lottery weight, not in realised offspring.

## The confound to rule out first

In the harsh setting an all-selfish population may struggle on its own: an isolated selfish founder has about
`5 / (1 + 4·0.96 + 0.213) ≈ 0.99` expected descendants per step. If selfish populations collapse while altruist
clusters persist, altruism could win as a **survival aid**, the problem that stopped
`nowak_mechanisms/kin_selection/floor_control/`. So a setting is used only if both homogeneous populations persist
on their own.

## Stage S: demographic screen (no test; fixed types)

All-altruist and all-selfish populations, initial occupancy 0.78 (the paper's), b = 0.468, c = 0.156, `disease`
0.213, `harshness` in {0.96 (the paper's), 0.9, 0.8, 0.7, 0.6, 0.5}, seeds 500-509, 1000 steps. **A point passes** if,
for both populations and all 10 seeds: not extinct at step 1000; mean occupied fraction over steps 901-1000 between
0.10 and 0.95; and no steady decline (mean occupied fraction over steps 901-1000 at least 0.8 times that over steps
401-500). **Choice:** the highest passing `harshness`. The grid and rule are fixed now; each point's outcome and
failure reason are reported. **If no point passes, the test stops** with "no screened point qualified".

The paper's point (0.96) is reported whatever happens. If it fails the screen, the site's reference row is annotated
that, at that point, all-selfish populations did not persist on their own under these criteria; that alone does not
show that the published result is a survival-aid effect.

## Stage M: the test (only if Stage S chose a point)

At the chosen `harshness` (`disease` 0.213), seeds 100-149 (fresh), 1000 steps. **Rare start:** each site altruist
with probability 0.05 (5% of sites, about 6.4% of occupied sites), selfish with probability 0.73, else empty;
initial clustering (share of altruists with an altruist neighbour) is reported.

| Arm | Change | Role |
| --- | --- | --- |
| T (test) | none | costly help (b/c 3), rare start |
| X (control: shuffled occupants) | before every help round, the occupants (with their type and founder id) are permuted uniformly among the occupied sites (separate random stream); the vacancy map is kept | breaks the clustering of relatives while keeping where empty space is; the local lottery is unchanged |
| D (dense reference) | `harshness` 0, `disease` 0 (the paper's baseline) | descriptive |
| W (weak-altruism reference) | b = 1.0 (own share 0.2 > c) | descriptive: help that pays for itself |

**Descent.** Every initial occupant gets a founder id. When a site is won by a type, the parent is drawn among that
type's candidates in proportion to their fitness (an added draw on a separate random stream, used only for this
bookkeeping, which does not change the dynamics), and the newborn inherits its founder id. Reported: the share of
occupied neighbour pairs that share a founder, against the share expected under random mixing of the same occupants.

**Per-run measures** (steps 901-1000): mean altruist share of occupied sites; mean occupied fraction; extinction step
(if any); number of births into previously empty sites. **Success per run:** not extinct, mean occupied fraction
between 0.10 and 0.95, and mean altruist share >= 0.60.

**Classification (mechanical, in order):**

1. **Not a valid test** if fewer than 40/50 T runs, or fewer than 40/50 X runs, are not extinct with mean occupied
   fraction >= 0.10 (too few populations to judge spread, or a control that fails by collapse). Reported, no verdict.
2. **Local failure** if T succeeds in fewer than 30/50 runs.
3. **Comparison failed** if X succeeds in more than 10/50 runs, or T leads X by fewer than 20 successes.
4. Otherwise **met**. Because the shuffle can still change later vacancy patterns, the result is reported as
   **consistent with** kin selection among non-offspring relatives (by viscosity), with founder sharing reported as
   the check on descent. Seeds are shared across arms; paired outcomes are reported descriptively.

**Descriptive:** altruist share and occupancy every 50 steps; arms D and W; the paper's harshness 0.96 from the rare
start in all 50 seeds, whatever Stage S chose.

## Budget and hard stop

Each run takes under a second; the whole design is minutes. New code (runner, occupied-only shuffle, founder
bookkeeping) gets tests and a Codex review before running; the model's dynamics are unchanged (a test checks that a
run with bookkeeping on gives identical states to the original model for the same seed). **Hard stop:** one attempt.
If not met, the result is recorded and no variants (other benefits, costs, starts) are run under this
pre-registration.

## Predictions (mine, before any data)

- Stage S: the paper's 0.96 fails: about 70%. Some screened point passes: about 60%.
- Given a passing point: T met: about 30%; X at most 10/50: about 80%.

## Limits

- Two discrete types and no mutation: "spread from rare" is invasion by a fixed strategy from randomly scattered
  founders (about 81% start with no altruist neighbour), not evolution of a continuous trait; a failure applies to
  this starting pattern and horizon.
- Relatedness is inferred from viscosity and checked by founder sharing, not by a pedigree.
- Non-overlapping generations; occupied sites are replaced as well as empty ones; no energy, food or movement.

## Amendment A1 (2026-11-25, after the Codex code review, before any run)

Fixes in `utils/run_kin_test.py`, all made before the registered run: (1) an extinction on the step that empties the
grid (including step 1000) is now recorded at that step, so such a run is never viable; (2) the occupancy cutoffs
(0.10, 0.95, the 0.8 decline factor) are applied to exact fractions of integer counts, not rounded floats; (3) births
into previously empty sites are counted over steps 901-1000, as registered; (4) the founder draw picks the first
candidate whose cumulative weight is strictly above the scaled draw, so a zero-weight candidate is never chosen;
(5) founder sharing is reported twice for the final step: after the lottery, and immediately before the help round
(where the control's shuffle acts); (6) the runner asserts the registered 51 × 51 torus. Regression tests added.
