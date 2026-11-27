# Kawakatsu, Kessinger and Plotkin (2024) as an external check: pre-registration (DRAFT, 2026-11-27)

**Status: DRAFT, not yet agreed with the user; no registered run.** Revised once after a Codex review (gpt-6.1-sol,
medium): per-start basin predictions, Stage 2 reframed, Stage 3 theory recorded now, censoring rules, exact generation
definition and strategy ordering, a seed manifest, verdict wording. Only a timing check of the authors' code has been
run (10 generations at τ_code = 0 and 0.2; no strategy frequency read; about 0.006 s per generation at τ_code = 0.2).

## Why

The indirect-reciprocity ladder ended at rung 5a (private views, simple standing: 45/100, bar 80), and a separate
follow-up with opinion-copying gossip was not met (44/100). Kawakatsu, Kessinger and Plotkin (2024) report that this
kind of gossip (an individual adopts another's view of a third) stabilises cooperation under private assessment. This
check runs the authors' code unchanged on their headline setting and then, as a bridge to the ladder's null, switches
the norm to simple standing. It is an external check, separate from the closed ladder.

## The authors' code and model

Code: <https://github.com/tkessinger/NeutralGossip>, commit `9d894a79a63f5276817ec2ca3c82a39d107fc376`, cloned and
run unchanged in `~/simulation_results/kawakatsu2024_gossip/NeutralGossip/` (no license file, so not copied here);
Julia 1.13.4 with the project environment there (the paper used 1.8.2). Our driver (`run_check.jl`, to be written and
reviewed) calls only the module's exported functions and follows the authors' `sample_trajectories.jl`.

N = 100; strategies ALLC, ALLD, DISC; donation game b = 5, c = 1; assessment error u_a = 0.02 (each view flipped
independently), execution error u_e = 0.02 (an intended cooperation fails; defection is never flipped); selection
strength ω = 1; no mutation (rate 0). **One generation** = one call of `evolve_modified_loop!` (module lines
208-215): (1) synchronous private assessment, each observer judging each donor by the donor's previously stored action
towards one random recipient and the observer's own pre-update view of that recipient, then independent assessment
flips; (2) the gossip events, each a random triplet (i, j, k) in which i adopts j's view of k; (3) a new complete
action matrix (everyone plays everyone), with execution errors; (4) payoffs; (5) one Fermi copying opportunity: a
random i copies a random j with probability 1 / (1 + exp[ω(Π_i − Π_j)]); (6) mutation (none). Each run first
performs 100 gossip-only rounds (as `sample_trajectories.jl`; the paper's methods describe all steps except strategy
updating repeated 100 times; we follow the script and report the difference).

**Norm indexing.** `social_norm[observer's view of the recipient + 1, donor's action + 1]` (view 0 = bad, 1 = good;
action 0 = defect, 1 = cooperate). Stern judging `SJ_norm = [1 0; 0 1]` (defecting against a bad recipient and
cooperating with a good one are good, the other two bad); simple standing `SS_norm = [1 1; 0 1]` (only defecting
against a good recipient is bad). **Strategy ordering:** starts and our outputs use ALLC / ALLD / DISC; the module's
`permitted_strategies` and `get_frequencies` use ALLD, ALLC, DISC; the driver maps them in one place and a preflight
test checks the mapping.

**Gossip scaling.** The paper defines τ by T = τN³/2 gossip events; the code uses `glen = floor(τ_code · N³)`. So
τ_code = 0.2 (the authors' `sample_trajectories.jl`) is the paper's τ = 0.4 (Fig. 2A, B). Below, τ is the paper's;
the driver passes τ_code = τ/2.

## Theory recorded before any run (the paper's equations; deterministic reconstruction by Codex)

- **Stern judging, local stability of all-DISC:** b/c > (b/c)* = 1/[(1 − 2u_a)(1 − u_e)] = 1.063 and τ > τ\* =
  log{[2 − (b/c)/((b/c) − 1/(2(1 − u_a)))] · (b/c)/((b/c) − (b/c)*)} = **0.118** (b/c = 5, u_a = u_e = 0.02).
- **Stern judging, deterministic basins from the six starts** (ALLC / ALLD / DISC):

| Start | 0.6/0.3/0.1 | 0.4/0.4/0.2 | 0.2/0.5/0.3 | 0.6/0.1/0.3 | 0.4/0.2/0.4 | 0.2/0.3/0.5 |
| --- | --- | --- | --- | --- | --- | --- |
| τ = 0 | ALLD | ALLD | ALLD | ALLD | ALLD | ALLD |
| τ = 0.4 | ALLD | ALLD | ALLD | **DISC** | **DISC** | **DISC** |

- **Stern judging, start 0.2/0.3/0.5 against τ:** ALLD at τ = 0.05-0.28, DISC at τ = 0.30 (the mixed start's basin
  boundary lies far above τ\*, which concerns invasion near all-DISC).
- **Simple standing:** the all-DISC resistance threshold is τ*_ALLD = τ*_SJ − log 2 = −0.575 (supplement Eq. S5, as
  evaluated by Codex; at τ = 0, all-DISC equilibrium reputations r_DISC = 5/6, r_ALLD = 0.18, and the ALLD invasion
  eigenvalue is negative): **no gossip is needed** for all-DISC to resist rare ALLD in this model. Deterministic
  endpoints from the six starts, at both τ = 0 and τ = 0.4: ALLD from 0.6/0.3/0.1 and 0.4/0.4/0.2, an ALLC-DISC
  mixture from the other four.

These are deterministic, large-population predictions; they do not give N = 100 fixation probabilities.

## Outcomes and censoring

Each run records one of four outcomes: ALLC fixed, ALLD fixed, DISC fixed, or **censored** (no strategy fixed after
200,000 generations, i.e. 200,000 calls of `evolve_modified_loop!` after the burn-in, about 2,000 imitation
opportunities per individual). For any fixation share, the bounds observed / total and (observed + censored) / total
are reported. For a criterion comparing two treatments A and B (C2, C3), with shares in [L_A, U_A] and [L_B, U_B],
the difference lies in [L_A − U_B, U_A − L_B]: the criterion **holds** only if the lower bound reaches the bar, **fails**
if the upper bound does not, and is otherwise **unresolved at the cap**; single-share criteria (C1, the majority part
of C2) hold if the lower bound reaches the bar, fail if the upper bound does not, and are otherwise unresolved. In simple standing,
**ALLD extinction** (irreversible without mutation) is recorded separately, with its generation.

## Stage 1: the headline result (Fig. 2B, D), stern judging (600 runs)

Six starts × τ ∈ {0, 0.4} × 50 runs.

- **C1 (no gossip):** at τ = 0, at least 90% of the 300 runs fix ALLD.
- **C2 (gossip, per start):** at τ = 0.4, each of the three DISC-basin starts (0.6/0.1/0.3, 0.4/0.2/0.4, 0.2/0.3/0.5)
  fixes DISC in a majority (at least 26/50) of its runs, and in at least 20 more runs than the same start at τ = 0.
- **Reported:** all four outcome counts and fixation times per start and τ, with binomial intervals; the three
  ALLD-basin starts at τ = 0.4 against their predicted ALLD.
- Stage 1 **meets the registered replication criteria** if C1 and C2 hold (and neither is unresolved).

## Stage 2: mixed-start basin response (only if Stage 1 meets its criteria)

Start 0.2/0.3/0.5, stern judging, τ ∈ {0.05, 0.10, 0.15, 0.20, 0.30}, 50 runs each.

- **C3:** the share fixing DISC at τ = 0.30 is at least 0.30 higher than at τ = 0.05. Reported: the share at each τ,
  against the deterministic prediction (ALLD up to 0.28, DISC at 0.30). This tests how the mixed start's outcome
  responds to gossip; it is not an estimate of τ*. The bar is an operational tolerance, not a paper-derived value.

## Stage 3: bridge to the ladder's null (only if Stage 1 meets its criteria)

Simple standing, all six starts, τ ∈ {0, 0.4}, 50 runs each (600 runs). Descriptive, no pass/fail: ALLD extinction,
ALLD fixation, censoring, the final composition and the realised cooperation rate (successful cooperative actions per
donor-recipient pair, averaged over every generation of the run after the burn-in, up to and including the fixation
generation or the cap; the actions of a generation precede its strategy update, as in the authors' loop), against the recorded predictions
(ALLD from the first two starts; an ALLC-DISC mixture from the other four; no difference needed between τ = 0 and
0.4). It shows whether, in the authors' model, simple standing with private views sustains cooperation with and
without gossip. Changing the norm inside the authors' model is a bridge comparison: it cannot by itself attribute the
ladder's null to any one difference between the two models.

## Seeds, preflight, validity, attempts

**Seed manifest (frozen):** seed = 100,000 × stage + 1,000 × (start index 1-6) + 100 × (τ index, from 0 in the
listed order) + replicate (1-50). Each run calls `Random.seed!(seed)` before constructing `Population` (which draws
random initial views and actions). Seeds are shared by design across nothing else; each (stage, start, τ, replicate)
has its own seed.

**Preflight (before Stage 1; results recorded, no outcome read):** the number of gossip events per generation equals
floor(τ_code N³); norm indexing (scripted single-step cases); the strategy-order mapping; initial strategy counts;
payoffs against a hand computation on a small population; fixation detection. Driver commit, Julia environment
(Manifest), raw-output path (`~/simulation_results/kawakatsu2024_gossip/runs/`) and analysis script are frozen before
Stage 1, and the driver is reviewed by Codex.

**Validity:** a crash stops the stage. One documented technical repair is allowed per stage; it must concern the
driver's mechanics, never an unwelcome outcome or a setting, reruns the frozen design exactly, and keeps the aborted
records. **Hard stop:** each stage once; no settings beyond those listed; Stage 3 is the last step.

**Verdict wording.** "Meets / does not meet / unresolved at the cap for the registered operational replication
criteria." If not met, the
interpretation distinguishes stochastic uncertainty, censoring, implementation discrepancies and disagreement with the
predicted basin pattern; it is not stated as a refutation of the paper without that analysis.

## Predictions (mine, before any data)

Stage 1 meets its criteria: 75%. Stage 2 C3 (given Stage 1): 55%. Stage 3, simple standing without gossip, ALLD goes
extinct in most runs from the four mixture-basin starts: 65%.
