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
- Adaptive Parameter Sweep (Current Preset: `predator_cooperation_cost_per_unit` x `prey_reproduction_probability`)
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

## 2026-03-29 Prey Birth Simplification Update

1. Removed the prey-side global soft cap `repro_scale` and kept prey birth as a
   direct energy-gated stochastic rule.
2. Removed the temporary juvenile-establishment filter, so successful prey
   birth no longer depends on a second local grass-based survival draw.
3. Simplified the energy accounting by removing the `prey_juvenile_loss`
   channel from the active runtime and diagnostics.

## 2026-03-29 Low-Cooperation Retune

1. Retuned the active default baseline to
   `predator_cooperation_cost_per_unit=0.15` and
   `prey_reproduction_probability=0.086`.
2. After simplifying prey birth back to a direct one-stage rule, the same
   default still preserved full `1000`-step coexistence across seeds `0-4`.
3. In headless 1000-step validation over seeds `0-4`, the active default kept
   both species alive in `5/5` runs with an average tail `mean_coop_hist` of
   about `0.855` under the current movement-cost rule.

## 2026-03-29 Distance-Scaled Movement Cost Update

1. Predator and prey movement cost now scale with actual per-tick displacement
   instead of being charged as a flat amount.
2. Axial moves now cost `1x` the move-cost coefficient, diagonal moves cost
   `sqrt(2)x`, and zero-displacement draws cost `0`.
3. This change keeps movement energetically tied to realized motion rather than
   to mere move attempts or fixed per-tick charging, while still preserving
   `5/5` coexistence across seeds `0-4` at the active default.

## 2026-03-29 README Consistency Update

1. Removed stale references to old default locations and clarified that sweep
   and tuner output directories are created on demand.
2. Tightened wording around the successful-group-hunt metric so it no longer
   refers to the removed `expressed_coop` path.
3. Regenerated the worked-example SVG assets from the current
   `energy_threshold_gate` logic, active default coefficients, and
   distance-scaled movement costs.

## 2026-03-30 Parameter Naming Update

1. Replaced the old short config keys with descriptive canonical names in
   `emerging_cooperation_config.py`.
2. Added a compatibility alias layer so legacy keys such as `pred_init`,
   `coop_cost`, `hunt_r`, and `p0` still resolve when older helper presets are
   loaded.
3. Updated the runtime, sweep/tuning scripts, and the active parameter
   documentation to use the descriptive names as the primary vocabulary.

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

- among predators that participated in successful multi-hunter kills at step
  `t`, what was their mean cooperation trait?

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
- Benefit saturation is controlled by the hunt function via
  `base_hunt_success_probability`.
- Per-tick cooperation cost
  (`predator_cooperation_cost_per_unit * coop`) provides direct individual
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
  `p_kill = 1 - (1 - base_hunt_success_probability)^sum(coop)`.
- On success, captured prey energy is transferred to hunters (no fixed
  synthetic kill reward).
- Reward split mode is configurable:
  - `share_prey_equally=True`: equal split.
  - `share_prey_equally=False`: contribution-weighted split.
- Each predator still pays its own cooperation cost every tick.

This creates the core social dilemma:

- Group performance improves with higher total contribution.
- Individual incentive can weaken because private cost is individual while hunt
  benefit can be shared.

## Why Cooperation Does Not Simply Fix At 1.0

The model has a direct cost-benefit tradeoff:

- Cost: each predator pays
  `predator_cooperation_cost_per_unit * coop` every tick.
- Benefit: higher `coop` raises local hunt success and team power.
- Equal sharing can decouple individual contribution from individual payoff.

Selection is therefore not uniformly pro-cooperation, which is why interior
cooperation levels are plausible rather than a guaranteed march to full
cooperation.

Important nuance:

- A predator with `coop = 0` pays zero cooperation surcharge.
- If `share_prey_equally=True`, that same predator can still receive an equal
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
| Players in a group | Predators in the local hunter pool around a focal prey (`hunter_pool_radius`) |
| Individual contribution | `w_i = energy_i * coop_i` |
| Public good production | Team power is aggregated and compared to prey energy (hard gate); optional extra probabilistic gate via `base_hunt_success_probability` |
| Private contribution cost | Per-tick individual cost `predator_cooperation_cost_per_unit * coop_i` (plus general metabolic/move costs) |
| Group benefit size | Captured prey energy `E_prey` on successful hunt |
| Benefit sharing rule | Equal split when `share_prey_equally=True`; contribution-weighted when `share_prey_equally=False` |
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
| Hamilton (1964) | Inclusive-fitness style tradeoff (`r b > c`) | `c`: per-step private cost `predator_cooperation_cost_per_unit * coop`; `b`: higher local hunt success/payoff via coop-weighted team power; `r`-like structure: local neighborhoods (`prey_detection_radius`, `hunter_pool_radius`) |
| Nowak (2006) | Rules for cooperation (especially spatial reciprocity) | Local interaction structure drives cooperative clustering and hunt outcomes; cooperation remains trait-based (`coop`) rather than action/learning based |
| Okasha (2006), Frank (1998) | Multilevel / Price-style decomposition | Between-group proxy: local group hunt conversion; within-group proxy: private cooperation costs plus the reward-sharing rule (`share_prey_equally`) that shapes how captured prey energy is distributed |
| Hendry (2017) | Eco-evolutionary feedbacks | Ecology: grass->prey->predator energy flows plus decay; evolution: inherited `coop`, mutation (`cooperation_mutation_probability`, `cooperation_mutation_stddev`), selection via survival/reproduction |
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

# 9. Adaptive Parameter Sweep (Current Preset: `predator_cooperation_cost_per_unit` x `prey_reproduction_probability`)

Sweep and tuner scripts write outputs under
`predpreygrass_public_goods/images/`; that directory is created on demand and
may not exist before the first sweep/tuning run.

Metric per cell: mean cooperation over tail window, averaged across successful
runs.

The active sweep script is now configured as a dedicated low-cooperation /
coexistence preset rather than a broad generic scan.

Important boundary:

- `predpreygrass_public_goods/utils/sweep_dual_parameter.py` evaluates parameter cells
  and writes heatmaps/CSV reports.
- It does not rewrite the active baseline in
  `predpreygrass_public_goods/config/emerging_cooperation_config.py`.

Current dedicated preset:

- x-axis: `predator_cooperation_cost_per_unit`
- y-axis: `prey_reproduction_probability`
- adaptive rank metric: `low_mean_coop`
- coexistence screen: `min_success_rate=1.0`

Interpretation:

- `predator_cooperation_cost_per_unit` is the direct lever that pushes evolved
  cooperation downward.
- `prey_reproduction_probability` is the ecological support lever that helps preserve
  predator-prey feedback while cooperation is being pushed down.
- `low_mean_coop` is defined as `1 - mean_coop`, so larger values mean lower
  average cooperation among successful runs.
- `min_success_rate=1.0` means adaptive refinement first looks only at cells
  that hit the full success target, so the search stays coexistence-first.

Current README scope:

- This section describes the active
  `predator_cooperation_cost_per_unit x prey_reproduction_probability` sweep
  only.
- Historical `predator_cooperation_cost_per_unit x base_hunt_success_probability`
  example panels have been removed to keep the
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

- `initial_predator_count=65`
- `initial_prey_count=575`
- `initial_predator_energy=1.4`
- `predator_metabolic_cost=0.053`
- `predator_move_cost_per_unit=0.008`
- `predator_cooperation_cost_per_unit=0.15`
- `predator_reproduction_energy_threshold=4.8`
- `predator_reproduction_probability=0.045`
- `base_hunt_success_probability=0.60`
- `prey_move_probability=0.30`
- `prey_reproduction_probability=0.086`
- `prey_offspring_energy_fraction=0.42`

In headless 1000-step validation over seeds `0-4`, this setting reached `5/5`
survival runs. Over the last 200 steps of those runs, the average
`mean_coop_hist` tail mean was about `0.855`.

The retune works through two coordinated changes:

- weaker direct selection for high cooperation:
  higher `predator_cooperation_cost_per_unit` lowers the private payoff to
  strongly cooperative predators
- faster prey recovery:
  prey reproduction remains high enough to avoid prey collapse becoming the
  dominant failure mode again

Retune summary:

- An earlier manual retune first moved the model away from near-immediate prey
  collapse by reducing predator pressure and strengthening prey recovery.
- The automatic tuner then searched a coarse 96-candidate region around that
  basin using 8 seeds per candidate.
- A later targeted low-cooperation retune raised
  `predator_cooperation_cost_per_unit` from `0.14` to `0.15` and
  `prey_reproduction_probability` from `0.078` to `0.086`.
- After the prey-birth simplification, that same parameter pair was rechecked
  and still preserved `5/5` coexistence across seeds `0-4`.
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
- Sweep and tuner outputs are written under
  `predpreygrass_public_goods/images/`, and that directory is created on
  demand.
- The sweep now writes one heatmap per configured metric in
  `heatmap_metrics`. By default this includes:
  `mean_coop`, `success_rate`, and `mean_group_hunt_effort`.
- Sweep heatmap filenames now also include the active
  `adaptive_rank_metric`, so adaptive runs are self-identifying on disk.
- If adaptive refinement is enabled, the cells used to choose the next search
  window are ranked by `adaptive_rank_metric` rather than being hard-wired to
  `mean_coop`.
- The active dedicated sweep preset varies
  `predator_cooperation_cost_per_unit` against
  `prey_reproduction_probability`, with `low_mean_coop = 1 - mean_coop` used for adaptive
  ranking and `min_success_rate=1.0` used to keep refinement coexistence-first.
- Adaptive runs also write a per-round refinement report listing the selected
  top cells and the resulting refined bounds.
- Adaptive runs also write a per-round `*_refinement_cells.csv` file with the
  selected top cells and their metric values.
- Baseline plots are shown interactively unless you add explicit save logic.
- For deterministic baselines, set `random_seed` in
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
- The tuner default horizon is `simulation_steps=1000`, and checkpoint/output stems
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

- Grid: `grid_width=60`, `grid_height=60`
- Initial populations: `initial_predator_count=65`, `initial_prey_count=575`
- Predator initial energy: `initial_predator_energy=1.4`
- Steps: `simulation_steps=1000`
- Predator costs: `predator_metabolic_cost=0.053`,
  `predator_move_cost_per_unit=0.008`,
  `predator_cooperation_cost_per_unit=0.15`
- Predator reproduction:
  `predator_reproduction_energy_threshold=4.8`,
  `predator_reproduction_probability=0.045`,
  `predator_crowding_soft_cap=800`, `offspring_birth_radius=1`
- Mutation: `cooperation_mutation_probability=0.03`,
  `cooperation_mutation_stddev=0.08`
- Hunt: `hunt_success_rule="energy_threshold_gate"`,
  `prey_detection_radius=1`,
  `hunter_pool_radius=1`, `base_hunt_success_probability=0.60`,
  `share_prey_equally=True`
- Logging: `log_reward_sharing=False`, `log_energy_accounting=False`,
  `energy_log_interval_steps=1`, `energy_invariant_tolerance=1e-6`
- Prey: `prey_move_probability=0.30`,
  `prey_reproduction_probability=0.086`,
  `initial_prey_energy_mean=1.1`, `initial_prey_energy_stddev=0.25`,
  `initial_prey_energy_min=0.10`,
  `prey_metabolic_cost=0.05`, `prey_move_cost_per_unit=0.01`,
  `prey_reproduction_energy_threshold=2.0`,
  `prey_offspring_energy_fraction=0.42`,
  `prey_grass_intake_per_step=0.24`
- Grass: `initial_grass_energy=0.8`,
  `max_grass_energy_per_cell=3.0`,
  `grass_regrowth_per_step=0.055`
- Clustering radius: `clustering_radius=2`
- Live pygame viewer: `enable_live_pygame_renderer=True`,
  `live_render_frames_per_second=30`,
  `live_render_cell_size=14` with display auto-fit enabled in `run_sim()`

Legacy short keys such as `pred_init`, `metab_pred`, `hunt_r`, and `p0` still
work through the compatibility alias layer, but the descriptive names above are
now the canonical ones.

Current baseline notes:

- The baseline run horizon is `simulation_steps=1000`.
- Runtime parameters are externalized in
  `predpreygrass_public_goods/config/emerging_cooperation_config.py`.
- The current promoted low-cooperation baseline uses
  `predator_cooperation_cost_per_unit=0.15`,
  `prey_reproduction_probability=0.086`,
  `base_hunt_success_probability=0.60`, and
  `predator_metabolic_cost=0.053`.
- In earlier headless validation over seeds `0-4`, that baseline survived the
  full `1000` steps in `5/5` runs while lowering the average tail
  `mean_coop_hist` to about `0.855`.

Defaults in `predpreygrass_public_goods/utils/sweep_dual_parameter.py`:

- Dedicated preset axes:
  `x_param='predator_cooperation_cost_per_unit'`,
  `y_param='prey_reproduction_probability'`
- `predator_cooperation_cost_per_unit` range: `0.08-0.18` (step `0.01`)
- `prey_reproduction_probability` range: `0.068-0.088` (step `0.004`)
- `successes=6`, `max_attempts=24`, `tail_window=200`,
  `simulation_steps=1500`
- `heatmap_metrics=['mean_coop', 'success_rate', 'mean_group_hunt_effort']`
- `adaptive_rank_metric='low_mean_coop'`
- Adaptive defaults: `adaptive=True`, `rounds=2`, `top_k=6`,
  `min_success_rate=1.0`,
  `refine_step_factor=0.5`
- `name_prefix='low_coop_coexistence_sweep'`
- Adaptive report output: one `*_refinement.txt` file per round
- Adaptive selected-cell CSV output: one `*_refinement_cells.csv` file per round

Defaults in `predpreygrass_public_goods/utils/tune_mutual_survival.py`:

- `simulation_steps=1000`
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
- Track and report extinction boundary curves in
  (`predator_cooperation_cost_per_unit`, `base_hunt_success_probability`)
  space.
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
- `p_kill = 1`, if `hunt_success_rule == "energy_threshold"` and `W_g >= E_prey`
- `p_kill = 1 - (1 - base_hunt_success_probability)^(S_g)`, if
  `hunt_success_rule == "energy_threshold_gate"` and `W_g >= E_prey`

Reward rule after a successful kill:

- `gain_i = E_prey / n_hunters`, if `share_prey_equally=True`
- `gain_i = E_prey * (energy_i * coop_i) / W_g`, if
  `share_prey_equally=False`

Per-step private cost:

- `cost_i = predator_metabolic_cost + predator_move_cost_per_unit * d_i + predator_cooperation_cost_per_unit * coop_i`

where `d_i in {0, 1, sqrt(2)}` is predator `i`'s realized one-tick step
distance on the Moore neighborhood grid.

Thresholded and saturating benefits combined with linear private cost make
interior cooperation regimes plausible.

Core macro flow channels per tick:

`photosynthesis_to_grass = grass_regrowth_per_step`

`grass_to_prey = sum(bite_i)`, with
`bite_i = min(prey_grass_intake_per_step, grass_cell_i)`

`prey_to_predator = sum(E_prey over successful kills)`

`prey_to_decay = prey_metabolic_loss + prey_move_loss`

with `prey_move_loss = sum(prey_move_cost_per_unit * d_i over prey move realizations)`

`predator_to_decay = pred_metab_loss + pred_move_loss + pred_coop_loss`

with `pred_move_loss = sum(predator_move_cost_per_unit * d_i over predator move realizations)`

Energy-balance identity checked each tick:

`delta_total = grass_regen - (prey_to_decay + predator_to_decay) + residual`

with `residual` expected near zero (tracked against
`energy_invariant_tolerance`).

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

1. Grass regrowth (`grass_regrowth_per_step`, capped by
   `max_grass_energy_per_cell`).
2. Prey phase: movement, clamped energy costs, single grass bite, reproduction.
3. Build spatial indexes for prey and predators.
4. Prey-centric engagement resolution (capture only; uses raw `coop`).
5. Explicit prey cleanup (starved + hunted), then append prey newborns.
6. Predator phase: clamped costs, movement, reproduction, mutation, cleanup
   (cooperation cost uses raw `coop`).
7. Optional run-level diagnostics: reward split and energy-budget invariant.

## Prey Dynamics

- Each prey moves with probability `prey_move_probability` by a local step in
  `{ -1, 0, 1 }` for x and y.
- Each prey pays `prey_metabolic_cost` every tick.
- If a prey moves, its move cost is `prey_move_cost_per_unit * d`, where
  `d in {0, 1, sqrt(2)}` is the realized Euclidean step length from the drawn
  `(dx, dy)`.
- Because the move branch can draw `(0, 0)`, a prey can enter the movement
  branch and still pay zero move cost if it does not change cell.
- Each prey consumes grass at its cell up to `prey_grass_intake_per_step`.
- Prey with `energy <= 0` are removed.
- Birth is energy-gated
  (`energy >= prey_reproduction_energy_threshold`) and stochastic at the
  parent level: `random < prey_reproduction_probability`.
- On birth, the child gets
  `child_energy = prey_offspring_energy_fraction * parent_energy`
  and the parent loses that energy immediately.
- The child is placed in a local neighbor cell and is appended after
  engagements, so it acts from the next tick onward.
- Newborn prey are buffered and appended only after engagements, so they act
  from the next tick.

## Hunting Logic

- Engagements iterate over live prey (prey-centric order).
- Candidate hunters are collected from cells in square neighborhood radius
  `prey_detection_radius` (Chebyshev radius) around each prey.
- Hunters are pooled around each victim using `hunter_pool_radius`.
- Hard gate: cooperative weighted power must exceed prey energy.
- In `energy_threshold_gate` mode, an additional probabilistic gate is applied:
  `p_kill = 1 - (1 - base_hunt_success_probability)^S`
  with `S = sum(coop_i)`.
- If a kill occurs, prey energy is transferred to hunters.
- Split is equal when `share_prey_equally=True`, otherwise
  contribution-weighted.

## Predator Energy, Reproduction, Mutation

- Each predator pays per tick:
  `predator_metabolic_cost + predator_move_cost_per_unit * d + predator_cooperation_cost_per_unit * coop`
  via clamped drains, where
  `d in {0, 1, sqrt(2)}` is the realized step length from its sampled
  `(dx, dy)`.
- Predators then apply that local wrapped step.
- Reproduction is thresholded and probabilistic:
  `energy >= predator_reproduction_energy_threshold` and
  `random < predator_reproduction_probability * predator_reproduction_scale`.
- `predator_reproduction_scale` includes predator crowding
  (`predator_crowding_soft_cap`) and prey availability
  (`len(preys) / initial_prey_count`).
- On reproduction, parent energy is halved; child inherits parent trait and
  local position.
- Child mutates with probability `cooperation_mutation_probability`:
  `coop_child = clamp01(coop_parent + Normal(0, cooperation_mutation_stddev))`.
- Predators with `energy <= 0` are removed.

## Run Termination and Outputs

- A run stops early if either predators or prey go extinct (`pred_n == 0` or
  `prey_n == 0`); this is an extinction run.
- A run is marked successful only if no extinction occurs before
  `simulation_steps`.
- With `restart_after_extinction=True`, `main()` retries up to
  `max_restart_attempts`.
- If enabled, the run logs:
  - reward split metrics (kills, captured energy, split inequality),
  - per-step energy budget fields:
    `d_total`, `grass_in`, `grass_to_prey`, `prey_to_pred`, `dissipative_loss`,
    expected delta, and residual with `[OK]/[WARN]` against
    `energy_invariant_tolerance`,
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

These diagrams visualize one concrete tick using an illustrative example that
now matches the current `energy_threshold_gate` hunt logic, active default
coefficients, and distance-scaled movement-cost rule.

![One Tick Worked Example](../assets/predprey_public_goods/tick_logic_example.svg)

## Gridworld View of the Same Tick

This version shows the same numerical example in a concrete local grid:

- Predators `A,B,C` occupy one cell.
- The highlighted blue square is the `prey_detection_radius=1` neighborhood
  used to collect
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
| Selection under density dependence | Predator reproduction scales by crowding and prey availability (`predator_reproduction_scale`) | predator persistence, extinction timing, oscillation amplitude |
| Heritable trait + mutation | Offspring inherit `coop` with mutation (`cooperation_mutation_probability`, `cooperation_mutation_stddev`) | trait mean/variance trajectories |
| Resource-mediated fitness | Energy transfer chain grass->prey->predator with dissipative decay | `grass_to_prey`, `prey_to_pred`, `prey_decay`, `pred_decay` |
| Spatial structure | Local hunt pools (`prey_detection_radius`, `hunter_pool_radius`) and local birth | clustering heatmap, local coexistence patterns |
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
| 3.1 Public goods game as null model (p.11) | Your hunt interaction is a repeated, local public-goods mechanism | `hunt_success_rule`, `hunter_pool_radius`, `share_prey_equally` |
| 4 Monte Carlo methods (pp.15-18) | Stochastic sequential updates and random local movement in each tick | `step_world()`, prey/predator shuffle and random moves |
| 5 Peer-based strategies (pp.20-24) | Local interaction and clustering effects on cooperative outcomes | `compute_local_clustering_field()`, prey-centric local engagements |
| 7 Self-organization of incentives (pp.29-32) | Endogenous reward/cost structure from energy transfers and costs | prey-energy capture, `predator_cooperation_cost_per_unit`, energy-flow diagnostics |
| 9 Tolerance and cooperation (pp.38-40) | Coexistence regimes and interior cooperation levels instead of fixation | sweep heatmaps and long-run `mean_coop_hist` behavior |

------------------------------------------------------------------------

# 20. Three Concrete Experiments (Ready to Run)

Each experiment is designed to isolate one mechanism while preserving the core
nature framing (trait-based cooperation).

## Experiment A: Equal Split vs Contribution-Weighted Rewards

Question: how strongly does equal sharing support free-riding and interior
cooperation?

Setups:

- A1 (baseline): `share_prey_equally=True`
- A2 (counterfactual): `share_prey_equally=False`

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
- Focus on `predator_cooperation_cost_per_unit` axis at fixed
  `prey_reproduction_probability` slices.

Compare:

- tail mean cooperation,
- coexistence frequency (successful runs),
- successful-group-hunt mean effort (`mean_group_hunt_effort`).

Expected signature:

- higher `predator_cooperation_cost_per_unit` lowers mean cooperation and
  narrows coexistence regime.

## Experiment C: Hunter Pool Radius

Question: how much does local coalition size shape coexistence and selected
cooperation?

Setups:

- C1: `hunter_pool_radius=0`
- C2: `hunter_pool_radius=1` (current baseline)
- C3: `hunter_pool_radius=2`

Compare:

- long-run mean cooperation,
- successful-group-hunt mean effort,
- extinction timing and predator-prey oscillation amplitude.

Expected signature:

- Larger hunter pools should make threshold crossing easier, but may also
  weaken the link between individual contribution and personal payoff if more
  hunters are routinely included in successful kills.
