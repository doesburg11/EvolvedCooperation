# Predator--Prey Cooperation Model Results

## With Formal Evolutionary Interpretation

This document summarizes the current predator--prey cooperation results
and provides a theoretical interpretation using:

- Hamilton's Rule (kin assortment framing)
- Multilevel Selection
- Price Equation
- Public Goods Game Structure
- Spatial Assortment

## Contents

- Group-Hunt Effort Metric
- What The Live Chart Means
- Raw Series Vs Live Chart
- How This Differs From Mean Cooperation
- Practical Reading Guide
- Cooperation Cost vs Hunt Income Diagnostic
- Hamilton's Rule Interpretation
- Multilevel Selection Perspective
- Price Equation Formulation
- Spatial Assortment
- Public Goods Game Structure (Current Implementation)
- Trait Reference View (Selected Chart)
- Adaptive Parameter Sweep (Current Preset: `coop_cost` x `prey_repro_prob`)
- Interpretation of the Full System
- Visualization Notes
- Reproduction of Results
- Key Parameter Settings
- Next Directions
- Mathematical Derivation (Current Reward Rule)
- Simulation Logic (Code-Level)
- One-Tick Worked Example (Visual)
- Comparison vs MARL Stag-Hunt (Updated)
- Hendry (2017) Links to This Model
- Three Concrete Experiments (Ready to Run)

## 2026-03-28 Simplification Update

1. Removed the disabled plasticity path from the active runtime and config.
2. Hunting contribution, hunt probability, reward weighting, and cooperation
   cost now use the inherited predator trait `coop` directly.
3. Removed `coop_shift` tracking from diagnostics so the code, config, and
   analysis notes all describe the same trait-only model.

## Group-Hunt Effort Metric

The module has been simplified to keep only the successful-group-hunt effort
summary in the active code path.

The main event-conditioned hunt metric is now:

- `successful_group_hunt_mean_effort_hist`

This metric asks:

- among hunters that participated in successful multi-hunter kills at time `t`,
  what was their mean cooperation
  trait level?

The denominator is:

- total hunters that participated in successful multi-hunter kills at step `t`

If `H_t` is the set of hunters in successful multi-hunter kills at time `t`,
then the chart shows:

- `(sum_{i in H_t} coop_i) / |H_t|`

If no successful multi-hunter kill occurs at step `t`, the code records `NaN`
for this history entry.

Current state:

- `cooperative_hunter_share_hist` has been removed from the active model
  outputs.
- `successful_group_hunt_mean_effort_hist` is the only event-conditioned
  successful-hunt cooperation history kept in the active run outputs.
- The sweep and tuner aggregate only this effort-based summary downstream.

## What The Live Chart Means

The lower live pygame chart is now labeled `Raw cooperation rate`.
It shows one population-wide series only:

- `Population coop raw`: the raw current-step mean cooperation trait across all
  living predators

Formally, if `N_t` is the number of living predators at step `t` and `c_i` is
predator `i`'s stored cooperation trait `p.coop`, then:

`mean_coop_t = (1 / N_t) * sum_{i=1}^{N_t} c_i`

Implementation details:

- this is the mean of stored predator trait values `p.coop`
- it is the same cooperation value used in hunting and cooperation cost
- if `N_t = 0`, the code records `mean_coop_t = 0.0`

In the live pygame side panel, the raw population value is surfaced explicitly
as:

- `Population mean coop (raw): X.XXX`

Axis styling in the live pygame charts:

- the upper population-history chart no longer shows a y-axis label
- the lower raw-cooperation chart no longer shows a y-axis label
- the upper chart y-axis ticks are rendered as whole-number population counts
- the lower chart y-axis is fixed to `0.00`, `0.50`, and `1.00`
- chart tick numbers on both charts and both axes are now drawn larger for readability
- chart tick numbers now use a monospace font so digits render with consistent width

## Raw Series Vs Live Chart

The default live display in the codebase is now the pygame viewer only:

- the live pygame lower chart shows only the raw population mean cooperation
  line
- the live pygame side panel also stays population-level only

The live chart therefore exposes the unsmoothed population-wide cooperation
signal directly.

## How This Differs From Mean Cooperation

`mean_coop_hist` is the per-step history of the population mean predator
cooperation trait over all living predators.

It asks:

- what is the average cooperation trait among all living predators?

`successful_group_hunt_mean_effort_hist` asks:

- among those same hunters, how cooperative was the average expressed effort?

So:

- `mean_coop_hist` is a whole-population trait summary
- `successful_group_hunt_mean_effort_hist` is a successful-group-hunt average effort summary

Current viewer state:

- The live pygame lower chart shows only the raw population cooperation rate.
- The live pygame side panel is also population-level for cooperation.
- The lower cooperation chart uses a fixed `0.00-1.00` axis.
- Chart tick numbers use a larger monospace font for readability.
- Standalone matplotlib cooperation and local-clustering figures are not shown
  by `main()`.
- `successful_group_hunt_mean_effort_hist` remains recorded for downstream
  analysis but is not shown in the default live viewer.

## Practical Reading Guide

- The live pygame viewer now answers one population-level question directly:
  how the mean predator cooperation trait changes over time.
- Successful-group-hunt mean effort is still recorded in the run histories and
  downstream sweep/tuning outputs, but it is no longer shown as a standalone
  matplotlib figure in the default run.

## Cooperation Cost vs Hunt Income Diagnostic

The matplotlib macro-energy figure now includes a dedicated cooperation
tradeoff panel.

It answers a direct question:

- does cooperation pay for itself through hunt intake, or is it draining
  predator energy overall?

Current implementation:

- The simulation records `pred_coop_loss` as its own history channel.
- It also records `coop_net_hunt_return = prey_to_pred - pred_coop_loss`.
- The macro-energy figure includes a panel for `hunt income`,
  `cooperation cost`, and `net after coop`.
- The terminal run summary includes cumulative hunt income, cooperation cost,
  net after cooperation cost, and cost share of hunt income.

Interpretation:

- If `net after coop` stays mostly above zero, cooperation is costly but still
  energetically worthwhile at the system level.
- If it stays near zero or below zero, the current cooperation level is likely
  too expensive relative to the prey-energy captured.

------------------------------------------------------------------------

# 3. Hamilton's Rule Interpretation

Let cooperation level be trait `c`.

Hamilton's inequality in reduced form is:

`r b > c`

where:

- `r` is local assortment/relatedness-like structure,
- `b` is the marginal group benefit from additional contribution,
- `c` is the individual cost of contribution.

In this model:

- Local birth and movement structure can keep positive assortment.
- Benefit saturation is controlled by the hunt function via `p0`.
- Per-tick cooperation cost (`coop_cost * coop`) provides direct individual
  cost.
- Because `b` is state-dependent, selection for higher cooperation is local and
  conditional rather than globally monotone.

------------------------------------------------------------------------

# 4. Multilevel Selection Perspective

A standard decomposition is:

$$
\Delta \bar{z}=\frac{\mathrm{Cov}_g(W_g,z_g)}{\bar{w}}+\frac{\mathbb{E}_g\left[\mathrm{Cov}_i(W_i,z_i)\right]}{\bar{w}}
$$

Interpretation for this system:

- Between-group component: more cooperative local groups can convert prey
  encounters into energy more reliably.
- Within-group component: each individual pays its own cooperation cost while
  reward is shared at group level.
- Mixed outcomes are therefore expected: cooperation can persist without fixing
  at `1.0`.

------------------------------------------------------------------------

# 5. Price Equation Formulation

At population level:

$$
\Delta \bar{z}=\frac{\mathrm{Cov}(w,z)}{\bar{w}}+\frac{\mathbb{E}\left[w\,\Delta z_{\mathrm{transmission}}\right]}{\bar{w}}
$$

In this model, mutation, spatial turnover, and ecological fluctuations make the
covariance term state-dependent. The practical reading is simple:

- when local cooperative structure improves hunting enough, covariance favors
  higher `coop`;
- when private cost dominates or equal sharing weakens individual return, that
  pressure weakens.

------------------------------------------------------------------------

# 6. Spatial Assortment

## Local Clustering Heatmap

<p align="center">
  <img src="../assets/predprey_public_goods/05_clustering_heatmap.png" alt="Clustering Heatmap" width="400">
</p>

Observed in the current chart:

- Predators occupy clustered patches rather than a uniform field.
- Many dark regions are predator-empty neighborhoods.
- Occupied patches show intermediate-to-high local cooperation values.

## Live Grid Snapshot

<p align="center">
  <img src="../assets/predprey_public_goods/06_live_grid.png" alt="Live Grid" width="400">
</p>

Observed in the current snapshot:

- Predator trait colors are mostly mid-range.
- Prey density and predator occupancy are spatially heterogeneous.
- Spatial structure and trait structure are visibly coupled.

------------------------------------------------------------------------

# 7. Public Goods Game Structure (Current Implementation)

The hunt rule is a local public-goods mechanism:

- Hunters are assembled locally around each prey candidate.
- A hard gate requires coop-weighted hunter power to exceed prey energy.
- In `energy_threshold_gate` mode, success is additionally probabilistic:
  `p_kill = 1 - (1 - p0)^sum(coop)`.
- On success, captured prey energy is transferred to hunters (no fixed
  synthetic kill reward).
- Reward split mode is configurable:
  - `equal_split_rewards=True`: equal split.
  - `equal_split_rewards=False`: contribution-weighted split.
- Each predator still pays its own cooperation cost every tick.

This creates the core social dilemma:

- Group performance improves with higher total contribution.
- Individual incentive can weaken because private cost is individual while hunt
  benefit can be shared.

## Why Cooperation Does Not Simply Fix At 1.0

The model has a direct cost-benefit tradeoff:

- Cost: each predator pays `coop_cost * coop` every tick.
- Benefit: higher `coop` raises local hunt success and team power.
- Equal sharing can decouple individual contribution from individual payoff.

Selection is therefore not uniformly pro-cooperation, which is why interior
cooperation levels are plausible rather than a guaranteed march to full
cooperation.

Important nuance:

- A predator with `coop = 0` pays zero cooperation surcharge.
- If `equal_split_rewards=True`, that same predator can still receive an equal
  share of prey reward after a successful hunt.
- This is not the same as paying zero total cost of living: metabolism and move
  costs still apply.
- Zero cooperation now means zero direct hunt contribution under the current
  contribution rule `energy_i * coop_i`.

## Textbook PGG Mapping (Code Anchors)

The model is not a one-shot matrix game, but its hunt module maps cleanly to
public-goods components:

| Public-goods element | Current model implementation |
|---|---|
| Players in a group | Predators in the local hunter pool around a focal prey (`hunter_pool_r`) |
| Individual contribution | `w_i = energy_i * coop_i` |
| Public good production | Team power is aggregated and compared to prey energy (hard gate); optional extra probabilistic gate via `p0` |
| Private contribution cost | Per-tick individual cost `coop_cost * coop_i` (plus general metabolic/move costs) |
| Group benefit size | Captured prey energy `E_prey` on successful hunt |
| Benefit sharing rule | Equal split when `equal_split_rewards=True`; contribution-weighted when `equal_split_rewards=False` |
| Cooperation readout | The module now tracks successful-hunt mean effort rather than a dedicated free-rider metric |
| Evolutionary update | No learning policy; trait `coop` is inherited with mutation at reproduction |

Interpretation:

- This is a spatial, repeated, ecological public-goods game with endogenous
  group formation and resource-coupled payoffs.
- It is richer than canonical static PGGs because survival, prey dynamics,
  grass, and reproduction feed back into payoffs.

## Theory-to-Code Map (Intro Literature)

| Reference | Main idea | Where it appears in this model |
|---|---|---|
| Hamilton (1964) | Inclusive-fitness style tradeoff (`r b > c`) | `c`: per-step private cost `coop_cost * coop`; `b`: higher local hunt success/payoff via coop-weighted team power; `r`-like structure: local neighborhoods (`hunt_r`, `hunter_pool_r`) |
| Nowak (2006) | Rules for cooperation (especially spatial reciprocity) | Local interaction structure drives cooperative clustering and hunt outcomes; cooperation remains trait-based (`coop`) rather than action/learning based |
| Okasha (2006), Frank (1998) | Multilevel / Price-style decomposition | Between-group proxy: local group hunt conversion; within-group proxy: private cooperation costs plus the reward-sharing rule (`equal_split_rewards`) that shapes how captured prey energy is distributed |
| Hendry (2017) | Eco-evolutionary feedbacks | Ecology: grass->prey->predator energy flows plus decay; evolution: inherited `coop`, mutation (`mut_rate`, `mut_sigma`), selection via survival/reproduction |
| Perc et al. (2017) | Statistical-physics framing of cooperation, especially public-goods and spatial pattern dynamics | Public-goods hunt mechanics, spatial neighborhoods, stochastic update order, and phase-like regime changes across parameter sweeps |

This map is intentionally conceptual: the code is an ecological ABM, not an
analytical closed-form model, but each theoretical construct has a direct
mechanistic counterpart in the implementation.

------------------------------------------------------------------------

# 8. Trait Reference View (Selected Chart)

<p align="center">
  <img src="../assets/predprey_public_goods/03_trait_mean.png" alt="Trait mean" width="400">
</p>

This selected reference chart shows:

- an early transient increase,
- then long-run intermediate cooperation,
- with no terminal drop-to-zero event in this figure.

------------------------------------------------------------------------

# 9. Adaptive Parameter Sweep (Current Preset: `coop_cost` x `prey_repro_prob`)

Sweep outputs currently used here are in `predpreygrass_public_goods/images/`.
Metric per cell: mean cooperation over tail window, averaged across successful runs.

The active sweep script is now configured as a dedicated low-cooperation /
coexistence preset rather than a broad generic scan.

Important boundary:

- `predpreygrass_public_goods/utils/sweep_dual_parameter.py` evaluates parameter cells
  and writes heatmaps/CSV reports.
- It does not rewrite the baseline defaults in
  `predpreygrass_public_goods/emerging_cooperation.py`.

Current dedicated preset:

- x-axis: `coop_cost`
- y-axis: `prey_repro_prob`
- adaptive rank metric: `low_mean_coop`
- coexistence screen: `min_success_rate=1.0`

Interpretation:

- `coop_cost` is the direct lever that pushes evolved cooperation downward.
- `prey_repro_prob` is the ecological support lever that helps preserve
  predator-prey feedback while cooperation is being pushed down.
- `low_mean_coop` is defined as `1 - mean_coop`, so larger values mean lower
  average cooperation among successful runs.
- `min_success_rate=1.0` means adaptive refinement first looks only at cells
  that hit the full success target, so the search stays coexistence-first.

Current README scope:

- This section describes the active `coop_cost x prey_repro_prob` sweep only.
- Historical `coop_cost x p0` example panels have been removed to keep the
  README aligned with the current default sweep regime.
- Generate fresh sweep outputs by running
  `predpreygrass_public_goods/utils/sweep_dual_parameter.py`; outputs are
  written to `predpreygrass_public_goods/images/`.

Important limit of interpretation:

- These heatmaps do not identify a single minimum cooperation threshold needed
  for coexistence.
- They summarize cooperation levels in successful finite-horizon runs; they are
  not direct equilibrium-threshold maps.

------------------------------------------------------------------------

# 10. Interpretation of the Full System

Current combined evidence supports:

- persistent predator--prey oscillations,
- non-fixating intermediate cooperation in the baseline trait trajectory,
- spatial clustering that shapes both ecology and selection,
- parameter-dependent cooperation regimes in sweep analysis.

The system is best interpreted as state-dependent selection under ecological
feedbacks, rather than a globally monotonic drive to full cooperation.

## Mutual-Survival Retune

The default ecological parameters were retuned to make mutual predator--prey
survival more likely.

The practical goal of the retune was not to eliminate all extinctions. It was
to move the default regime away from the earlier pattern where prey collapse was
the dominant outcome across seeds.

The current defaults are no longer the earlier automated coarse-search winner.
That older setting remained too cooperative in the active 1000-step baseline.
After the dedicated low-cooperation/coexistence sweep was added, the baseline
was retuned again with targeted multi-seed headless checks.

The current promoted low-cooperation baseline is:

- `pred_init=65`
- `prey_init=575`
- `pred_energy_init=1.4`
- `metab_pred=0.053`
- `move_cost=0.008`
- `coop_cost=0.14`
- `birth_thresh_pred=4.8`
- `pred_repro_prob=0.045`
- `p0=0.60`
- `prey_move_prob=0.30`
- `prey_repro_prob=0.078`
- `prey_birth_split=0.42`

In headless 1000-step validation over seeds `0-4`, this setting reached `5/5`
survival runs. Over the last 200 steps of those runs, the average
`mean_coop_hist` tail mean dropped from about `0.910` under the previous
baseline to about `0.814`.

The retune works through three coordinated changes:

- lower initial predator pressure:
  fewer predators start the run and each starts with less energy
- weaker direct selection for high cooperation:
  higher `coop_cost` lowers the private payoff to strongly cooperative
  predators
- coexistence support:
  slightly lower `metab_pred`, slightly higher `p0`, and higher
  `prey_repro_prob` keep predator-prey feedback alive even after cooperation
  is made more costly
- faster prey recovery:
  prey reproduction remains high enough to avoid prey collapse becoming the
  dominant failure mode again

Retune summary:

- An earlier manual retune first moved the model away from near-immediate prey
  collapse by reducing predator pressure and strengthening prey recovery.
- The automatic tuner then searched a coarse 96-candidate region around that
  basin using 8 seeds per candidate.
- The current promoted baseline came from a later targeted low-cooperation
  search that raised `coop_cost` to `0.14`, raised `p0` to `0.60`, raised
  `prey_repro_prob` to `0.078`, and lowered `metab_pred` to `0.053`.
- Older timestamped tuner artifacts have been pruned; the retained in-repo
  tuner outputs are the active checkpoint files.

------------------------------------------------------------------------

# 11. Visualization Notes

Core ecology/trait figures are generated from:

- `predpreygrass_public_goods/emerging_cooperation.py`

Sweep figures are generated from:

- `predpreygrass_public_goods/utils/sweep_dual_parameter.py`
- `predpreygrass_public_goods/utils/tune_mutual_survival.py` for automatic
  mutual-survival parameter search

Animation views:

- Disentangled 3-panel live view (`animate=True`):
  panel 1 local cooperation heatmap,
  panel 2 prey density heatmap (log-scaled, zeros masked),
  panel 3 predator trait map (positions colored by cooperation),
  each with its own legend/colorbar.
- Optional simple live grid (`animate_simple_grid=True`):
  grass heatmap background with prey and predator markers.
- Optional macro-flow figure (`plot_macro_energy_flows=True`):
  per-tick channels
  `photosynthesis->grass`, `grass->prey`, `prey->predator`,
  `prey->decay`, `predator->decay`,
  plus cumulative energy stocks per tick
  (`grass`, `prey`, `predator`, and total sum).

Live pygame viewer:

- `run_sim()` constructs `PyGameRenderer(..., auto_fit=True)`.
- `live_render_cell_size` is treated as an upper bound and is clamped to the
  current display size.
- The side panel uses a compact responsive layout so population and cooperation
  charts stay visible on smaller displays.
- `utils/pygame_renderer.py` now contains only the active
  `emerging_cooperation.py` live viewer path.

------------------------------------------------------------------------

# 12. Reproduction of Results

From repo root:

```bash
./.conda/bin/python predpreygrass_public_goods/emerging_cooperation.py
./.conda/bin/python predpreygrass_public_goods/utils/sweep_dual_parameter.py
./.conda/bin/python predpreygrass_public_goods/utils/tune_mutual_survival.py
./.conda/bin/python predpreygrass_public_goods/utils/resume_mutual_survival_until_done.py
```

Notes:

- `predpreygrass_public_goods/emerging_cooperation.py` now reads its runtime
  parameters from `predpreygrass_public_goods/config/emerging_cooperation_config.py`.
- `emerging_cooperation.py` imports that `config` dict and copies it into a
  single module-level `CFG`, which `run_sim()` and the other
  config-aware helpers use unless an explicit config override is passed.
- The sweep and tuner no longer mutate imported module globals. They clone
  `eco.CFG`, override the selected parameters in that per-run dict, and pass it
  into `run_sim(config=...)`.
- Auxiliary scripts now live under `predpreygrass_public_goods/utils/`,
  including the sweep, tuner, resume wrapper, tick-logic generator, and live
  pygame renderer.
- Sweep images are saved under `predpreygrass_public_goods/images/`.
- The sweep now writes one heatmap per configured metric in
  `heatmap_metrics`. By default this includes:
  `mean_coop`, `success_rate`, and `mean_group_hunt_effort`.
- Sweep heatmap filenames now also include the active
  `adaptive_rank_metric`, so adaptive runs are self-identifying on disk.
- If adaptive refinement is enabled, the cells used to choose the next search
  window are ranked by `adaptive_rank_metric` rather than being hard-wired to
  `mean_coop`.
- The active dedicated sweep preset varies `coop_cost` against
  `prey_repro_prob`, with `low_mean_coop = 1 - mean_coop` used for adaptive
  ranking and `min_success_rate=1.0` used to keep refinement coexistence-first.
- Adaptive runs also write a per-round refinement report listing the selected
  top cells and the resulting refined bounds.
- Adaptive runs also write a per-round `*_refinement_cells.csv` file with the
  selected top cells and their metric values.
- Baseline plots are shown interactively unless you add explicit save logic.
- For deterministic baselines, set `seed` in
  `predpreygrass_public_goods/config/emerging_cooperation_config.py`.
- The mutual-survival tuner uses an in-file parameter grid and now evaluates
  candidates in batches, writing checkpoint files after each batch so long runs
  can resume instead of restarting.
- The tuner can also re-enter from its own checkpoint in repeated passes inside
  one invocation when `run_until_complete=True`.
- Checkpoint outputs are written as
  `predpreygrass_public_goods/images/mutual_survival_tuning_<ranking_mode>_steps<steps>_checkpoint.csv`
  and
  `predpreygrass_public_goods/images/mutual_survival_tuning_<ranking_mode>_steps<steps>_checkpoint_top.txt`.
- The tuner default horizon is `steps=1000`, and checkpoint/output stems
  include `steps<steps>` so different run horizons do not reuse each other's
  checkpoints by default.
- Legacy uppercase checkpoint headers are normalized on load, so explicit
  legacy `steps=500` resume runs can still read the retained old checkpoint.
- At the end of a completed run it also writes a timestamped ranked CSV plus a
  short top-results summary into `predpreygrass_public_goods/images/`.
- The tuner top-summary now reports successful-run hunt cooperation as one
  named field:
  `mean_group_hunt_effort_success`.
- `successful_group_hunt_mean_effort_hist` remains available from `run_sim()`
  for downstream aggregation, while the older successful-hunt share metric has
  been removed.
- The tuner ranking behavior is now controlled by `ranking_mode`:
  `coexistence` keeps the original coexistence-first ordering, while
  `prey_collapse_penalty` adds a stronger penalty for prey-collapse-heavy
  candidates.
- If you want a dedicated resume-only entrypoint, use
  `predpreygrass_public_goods/utils/resume_mutual_survival_until_done.py`, which
  forces `resume=True` and can clamp worker count to a safer value for long
  runs.
- There are no fallback defaults in the model source. The config file is the
  active source of truth, and `run_sim(config=...)` /
  `step_world(..., config=...)` accept explicit per-run overrides.

------------------------------------------------------------------------

# 13. Key Parameter Settings

Active runtime parameters for `predpreygrass_public_goods/emerging_cooperation.py`
are now loaded from `predpreygrass_public_goods/config/emerging_cooperation_config.py`.
The active source of truth is the Python `config = {...}` dict in that file.

- Grid: `w=60`, `h=60`
- Initial populations: `pred_init=65`, `prey_init=575`
- Predator initial energy: `pred_energy_init=1.4`
- Steps: `steps=1000`
- Predator costs: `metab_pred=0.053`, `move_cost=0.008`, `coop_cost=0.14`
- Predator reproduction: `birth_thresh_pred=4.8`, `pred_repro_prob=0.045`,
  `pred_max=800`, `local_birth_r=1`
- Mutation: `mut_rate=0.03`, `mut_sigma=0.08`
- Hunt: `hunt_rule="energy_threshold_gate"`, `hunt_r=1`,
  `hunter_pool_r=1`, `p0=0.60`,
  `equal_split_rewards=True`
- Logging: `log_reward_split=False`, `log_energy_budget=False`,
  `energy_log_every=1`, `energy_invariant_tol=1e-6`
- Prey: `prey_move_prob=0.30`, `prey_repro_prob=0.078`, `prey_max=3200`,
  `prey_energy_mean=1.1`, `prey_energy_sigma=0.25`, `prey_energy_min=0.10`,
  `prey_metab=0.05`, `prey_move_cost=0.01`, `prey_birth_thresh=2.0`,
  `prey_birth_split=0.42`, `prey_bite_size=0.24`
- Grass: `grass_init=0.8`, `grass_max=3.0`, `grass_regrowth=0.055`
- Clustering radius: `clust_r=2`
- Live pygame viewer: `live_render_pygame=True`, `live_render_fps=30`,
  `live_render_cell_size=14` with display auto-fit enabled in `run_sim()`

Current baseline notes:

- The baseline run horizon is `steps=1000`.
- Runtime parameters are externalized in
  `predpreygrass_public_goods/config/emerging_cooperation_config.py`.
- The current promoted low-cooperation baseline uses
  `coop_cost=0.14`, `prey_repro_prob=0.078`, `p0=0.60`, and
  `metab_pred=0.053`.
- In earlier headless validation over seeds `0-4`, that baseline survived the
  full `1000` steps in `5/5` runs while lowering the average tail
  `mean_coop_hist` from about `0.910` to about `0.814`.

Defaults in `predpreygrass_public_goods/utils/sweep_dual_parameter.py`:

- Dedicated preset axes:
  `x_param='coop_cost'`, `y_param='prey_repro_prob'`
- `coop_cost` range: `0.08-0.18` (step `0.01`)
- `prey_repro_prob` range: `0.068-0.088` (step `0.004`)
- `successes=6`, `max_attempts=24`, `tail_window=200`, `steps=1500`
- `heatmap_metrics=['mean_coop', 'success_rate', 'mean_group_hunt_effort']`
- `adaptive_rank_metric='low_mean_coop'`
- Adaptive defaults: `adaptive=True`, `rounds=2`, `top_k=6`,
  `min_success_rate=1.0`,
  `refine_step_factor=0.5`
- `name_prefix='low_coop_coexistence_sweep'`
- Adaptive report output: one `*_refinement.txt` file per round
- Adaptive selected-cell CSV output: one `*_refinement_cells.csv` file per round

Defaults in `predpreygrass_public_goods/utils/tune_mutual_survival.py`:

- `steps=1000`
- `ranking_mode='prey_collapse_penalty'`
- alternative: `ranking_mode='coexistence'`
- `run_until_complete=True`
- `max_resume_passes=12`

Defaults in `predpreygrass_public_goods/utils/resume_mutual_survival_until_done.py`:

- `force_workers=1`
- `max_passes_override=24`

------------------------------------------------------------------------

# 14. Next Directions

- Add an explicit coexistence probability map (`Pr[survival to T]`) alongside
  mean cooperation maps.
- Track and report extinction boundary curves in (`coop_cost`, `p0`) space.
- Estimate effective assortment `r(t)` directly from local trait correlation.
- Compare single-seed trajectories against multi-seed confidence intervals.
- Add optional deterministic export pipeline for baseline figures.
- Expand the mutual-survival tuner into a two-stage coarse-to-fine search once a
  preferred coexistence score is fixed.

------------------------------------------------------------------------

# 15. Mathematical Derivation (Current Reward Rule)

This section summarizes the implemented hard-gate reward logic in the shortest
useful form.

For a candidate prey `v` and local hunter set `g`:

- Team power:
  `W_g = sum_{i in g} energy_i * coop_i`
- Team effort:
  `S_g = sum_{i in g} coop_i`
- Prey energy:
  `E_prey`

Kill rule:

- `p_kill = 0`, if `W_g < E_prey`
- `p_kill = 1`, if `hunt_rule == "energy_threshold"` and `W_g >= E_prey`
- `p_kill = 1 - (1 - p0)^(S_g)`, if `hunt_rule == "energy_threshold_gate"`
  and `W_g >= E_prey`

Reward rule after a successful kill:

- `gain_i = E_prey / n_hunters`, if `equal_split_rewards=True`
- `gain_i = E_prey * (energy_i * coop_i) / W_g`, if
  `equal_split_rewards=False`

Per-step private cost:

- `cost_i = metab_pred + move_cost + coop_cost * coop_i`

Thresholded and saturating benefits combined with linear private cost make
interior cooperation regimes plausible.

Core macro flow channels per tick:

`photosynthesis_to_grass = grass_regen`

`grass_to_prey = sum(bite_i)`, with `bite_i = min(prey_bite_size, grass_cell_i)`

`prey_to_predator = sum(E_prey over successful kills)`

`prey_to_decay = prey_metab_loss + prey_move_loss`

`predator_to_decay = pred_metab_loss + pred_move_loss + pred_coop_loss`

Energy-balance identity checked each tick:

`delta_total = grass_regen - (prey_to_decay + predator_to_decay) + residual`

with `residual` expected near zero (tracked against `energy_invariant_tol`).

Cumulative stock view:

`E_grass(t) = sum(grass[y, x])`

`E_prey(t) = sum(prey.energy)`

`E_predator(t) = sum(predator.energy)`

`E_total(t) = E_grass(t) + E_prey(t) + E_predator(t)`

------------------------------------------------------------------------

# 16. Simulation Logic (Code-Level)

This section documents the exact update order used in
`predpreygrass_public_goods/emerging_cooperation.py`.

## State Variables

- Predator agent: `(x, y, energy, coop)` where `coop in [0,1]`.
- Prey agent: `(x, y, energy)`.
- Grass field: per-cell energy `grass[y, x]`.
- Space is a wrapped torus (`wrap`), so movement beyond an edge re-enters on
  the opposite side.

## Per-Tick Update Order

1. Grass regrowth (`grass_regrowth`, capped by `grass_max`).
2. Prey phase: movement, clamped energy costs, single grass bite, reproduction.
3. Build spatial indexes for prey and predators.
4. Prey-centric engagement resolution (capture only; uses raw `coop`).
5. Explicit prey cleanup (starved + hunted), then append prey newborns.
6. Predator phase: clamped costs, movement, reproduction, mutation, cleanup
   (cooperation cost uses raw `coop`).
7. Optional run-level diagnostics: reward split and energy-budget invariant.

## Prey Dynamics

- Each prey moves with probability `prey_move_prob` by a local step in
  `{ -1, 0, 1 }` for x and y.
- Each prey pays `prey_metab` and (if moved) `prey_move_cost` via clamped
  drains (`drain_energy`), so paid cost cannot exceed current energy.
- Each prey consumes grass at its cell up to `prey_bite_size`.
- Prey with `energy <= 0` are removed.
- Reproduction is density-limited by:
  `repro_scale = max(0, 1 - prey_count / prey_max)`.
- Birth is energy-gated (`energy >= prey_birth_thresh`) and stochastic:
  `prey_repro_prob * repro_scale`.
- On birth, child gets `prey_birth_split * parent_energy` and the parent loses
  that energy.
- Newborn prey are buffered and appended only after engagements, so they act
  from the next tick.

## Hunting Logic

- Engagements iterate over live prey (prey-centric order).
- Candidate hunters are collected from cells in square neighborhood radius
  `hunt_r` (Chebyshev radius) around each prey.
- Hunters are pooled around each victim using `hunter_pool_r`.
- Hard gate: cooperative weighted power must exceed prey energy.
- In `energy_threshold_gate` mode, an additional probabilistic gate is applied:
  `p_kill = 1 - (1 - p0)^S` with `S = sum(coop_i)`.
- If a kill occurs, prey energy is transferred to hunters.
- Split is equal when `equal_split_rewards=True`, otherwise
  contribution-weighted.

## Predator Energy, Reproduction, Mutation

- Each predator pays per tick:
  `metab_pred + move_cost + coop_cost * coop` via clamped drains.
- Predators then move by a local wrapped step.
- Reproduction is thresholded and probabilistic:
  `energy >= birth_thresh_pred` and
  `random < pred_repro_prob * pred_repro_scale`.
- `pred_repro_scale` includes predator crowding (`pred_max`) and prey
  availability (`len(preys) / prey_init`).
- On reproduction, parent energy is halved; child inherits parent trait and
  local position.
- Child mutates with probability `mut_rate`:
  `coop_child = clamp01(coop_parent + Normal(0, mut_sigma))`.
- Predators with `energy <= 0` are removed.

## Run Termination and Outputs

- A run stops early if either predators or prey go extinct (`pred_n == 0` or
  `prey_n == 0`); this is an extinction run.
- A run is marked successful only if no extinction occurs before `steps`.
- With `restart_on_extinction=True`, `main()` retries up to `max_restarts`.
- If enabled, the run logs:
  - reward split metrics (kills, captured energy, split inequality),
  - per-step energy budget fields:
    `d_total`, `grass_in`, `grass_to_prey`, `prey_to_pred`, `dissipative_loss`,
    expected delta, and residual with `[OK]/[WARN]` against
    `energy_invariant_tol`,
  - run-level flow totals:
    `grass_regen`, `grass_to_prey`, `prey_to_pred`,
    `prey_birth_transfer`, `pred_birth_transfer`, and all dissipative
    subcomponents.
- Recorded outputs include:
  predator count history, prey count history, mean/variance cooperation history,
  mean-effort history for successful multi-hunter kills,
  optional animation snapshots, final predator list, `success` flag, and
  `extinction_step`.
- In the live pygame panel, the current step now shows only the raw population
  cooperation value; the successful-group-hunt mean-effort summary remains
  available in the recorded histories and downstream sweep/tuning summaries.
- The default baseline run no longer opens a standalone local clustering
  heatmap figure; local clustering remains available in the optional animation
  path and through `compute_local_clustering_field()`.

Sweep and tuner artifacts now also expose this cooperation-facing successful-
hunt summary:

- `sweep_dual_parameter.py` CSV rows include `mean_group_hunt_effort`
  alongside `mean_coop`.
- `tune_mutual_survival.py` ranked CSV and top-summary files include
  `mean_group_hunt_effort_success` for successful runs.

------------------------------------------------------------------------

# 17. One-Tick Worked Example (Visual)

This diagram visualizes one concrete tick using the same numeric example used
to explain the update logic.

![One Tick Worked Example](../assets/predprey_public_goods/tick_logic_example.svg)

## Gridworld View of the Same Tick

This version shows the same numerical example in a concrete local grid:

- Predators `A,B,C` occupy one cell.
- The highlighted blue square is the `hunt_r=1` neighborhood used to collect
  prey candidates.
- Left panel: before hunt (all candidate prey present).
- Right panel: after hunt, where one candidate prey is removed because
  `draw < p_kill`.

![One Tick Gridworld](../assets/predprey_public_goods/tick_logic_gridworld.svg)

To regenerate:

```bash
./.conda/bin/python predpreygrass_public_goods/utils/visualize_tick_logic.py
```

------------------------------------------------------------------------

# 18. Comparison vs MARL Stag-Hunt (Updated)

This project intentionally keeps one core difference from
`predpreygrass/rllib/stag_hunt_forward_view`:

- Nature-focused cooperation here: cooperation is a heritable trait (`coop`).
- Nurture-focused cooperation there: cooperation is an action decision
  (`join_hunt`) each step.

What is now aligned more closely with the MARL ecology:

- Prey have explicit energy household and can starve.
- Grass is explicit, regrows each tick, and is consumed by prey.
- Predator reproduction is energy-driven with additional regulation.
- Cooperative hunt uses local pooling plus energy-threshold gating.
- Engagement order is prey-centric with explicit cleanup phases.
- Hunt reward is transferred from captured prey energy (no fixed kill reward).

What still differs (beyond the intended trait-vs-action distinction):

- No explicit `join_cost` / scavenger action channel.
- No RL action/observation API or per-agent termination/truncation outputs.
- No bounded-grid wall/LOS movement constraints.
- Single-species predator + scalar trait evolution, rather than typed MARL agent
  populations.

------------------------------------------------------------------------

# 19. Hendry (2017) Links to This Model

The model supports several core eco-evolutionary patterns discussed in Hendry's
intro framework, with direct code-level hooks:

| Hendry theme | Code-level mechanism here | Primary observables |
|---|---|---|
| Ecology-evolution feedback | Predator trait `coop` changes hunt conversion, which changes predator/prey/grass densities, which changes selection | `mean_coop_hist`, `pred_hist`, `prey_hist`, macro energy stocks |
| Selection under density dependence | Predator reproduction scales by crowding and prey availability (`pred_repro_scale`) | predator persistence, extinction timing, oscillation amplitude |
| Heritable trait + mutation | Offspring inherit `coop` with mutation (`mut_rate`, `mut_sigma`) | trait mean/variance trajectories |
| Resource-mediated fitness | Energy transfer chain grass->prey->predator with dissipative decay | `grass_to_prey`, `prey_to_pred`, `prey_decay`, `pred_decay` |
| Spatial structure | Local hunt pools (`hunt_r`, `hunter_pool_r`) and local birth | clustering heatmap, local coexistence patterns |
| Trait-only behavior | The inherited trait `coop` is used directly in hunt conversion and private cooperation cost each tick | `mean_coop_hist`, `successful_group_hunt_mean_effort_hist`, energy-flow diagnostics |

Interpretation boundary:

- This remains an ABM, not an analytical derivation of Hendry models.
- The mapping is mechanism-level: same causal ingredients, different formalism.

## Perc et al. (2017) Direct Links

- Main article (DOI): [https://doi.org/10.1016/j.physrep.2017.05.004](https://doi.org/10.1016/j.physrep.2017.05.004)
- Local copy used here:
  `/home/doesburg/Dropbox/00. Planning/00. Lopende zaken/HBP/research HBP/Research_current_eco_evolution_simulation/Perc_et_al_Physics_Reports_2017.pdf`

## Perc Sections Most Relevant to This Simulation

| Perc section | Why it maps to this model | Where to inspect in code |
|---|---|---|
| 3.1 Public goods game as null model (p.11) | Your hunt interaction is a repeated, local public-goods mechanism | `hunt_rule`, `hunter_pool_r`, `equal_split_rewards` |
| 4 Monte Carlo methods (pp.15-18) | Stochastic sequential updates and random local movement in each tick | `step_world()`, prey/predator shuffle and random moves |
| 5 Peer-based strategies (pp.20-24) | Local interaction and clustering effects on cooperative outcomes | `compute_local_clustering_field()`, prey-centric local engagements |
| 7 Self-organization of incentives (pp.29-32) | Endogenous reward/cost structure from energy transfers and costs | prey-energy capture, `coop_cost`, energy-flow diagnostics |
| 9 Tolerance and cooperation (pp.38-40) | Coexistence regimes and interior cooperation levels instead of fixation | sweep heatmaps and long-run `mean_coop_hist` behavior |

------------------------------------------------------------------------

# 20. Three Concrete Experiments (Ready to Run)

Each experiment is designed to isolate one mechanism while preserving the core
nature framing (trait-based cooperation).

## Experiment A: Equal Split vs Contribution-Weighted Rewards

Question: how strongly does equal sharing support free-riding and interior
cooperation?

Setups:

- A1 (baseline): `equal_split_rewards=True`
- A2 (counterfactual): `equal_split_rewards=False`

Compare:

- extinction rate over replicated seeds,
- `mean_coop_hist` tail mean,
- `successful_group_hunt_mean_effort_hist`,
- energy-flow channels and total stock drift.

Expected signature:

- A2 should reduce free-riding pressure by tying reward more tightly to direct
  contribution, which should raise selected cooperation relative to equal split
  if coexistence is maintained.

## Experiment B: Cost-Sensitivity of Cooperation

Question: where does cooperation collapse under private cost pressure?

Setups:

- Run sweep script with current logic:
  `./.conda/bin/python predpreygrass_public_goods/utils/sweep_dual_parameter.py`
- Focus on `coop_cost` axis at fixed `prey_repro_prob` slices.

Compare:

- tail mean cooperation,
- coexistence frequency (successful runs),
- successful-group-hunt mean effort (`mean_group_hunt_effort`).

Expected signature:

- higher `coop_cost` lowers mean cooperation and narrows coexistence regime.

## Experiment C: Hunter Pool Radius

Question: how much does local coalition size shape coexistence and selected
cooperation?

Setups:

- C1: `hunter_pool_r=0`
- C2: `hunter_pool_r=1` (current baseline)
- C3: `hunter_pool_r=2`

Compare:

- long-run mean cooperation,
- successful-group-hunt mean effort,
- extinction timing and predator-prey oscillation amplitude.

Expected signature:

- Larger hunter pools should make threshold crossing easier, but may also
  weaken the link between individual contribution and personal payoff if more
  hunters are routinely included in successful kills.
