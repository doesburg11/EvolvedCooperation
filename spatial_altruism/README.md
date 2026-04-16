# Spatial Altruism Model

A vectorized Python/NumPy implementation of the Mitteldorf-Wilson spatial altruism model. The default website replay and live demo use the steady-state variable-density population-viscosity variant, and the package also supports the paper's periodic uniform-culling and compact-swath disturbance variants. In all three modes, altruist, selfish, and empty patches compete locally on a two-dimensional lattice through five-site weighted lotteries. It includes a Pygame UI for interactive exploration and Matplotlib plotting for population dynamics.

## Browser Demo

[![Spatial Altruism](../assets/spatial_altruism/spatial_altruism_demo_preview.gif)](https://doesburg11.github.io/EvolvedCooperation/spatial-altruism/)

Layout alignment across viewer surfaces:

1. The README GIF is generated offline from the sampled replay exporter.
2. The repo-level `docs/spatial-altruism/` page uses the same header/world/sidebar layout family as that GIF preview.
3. The live Pygame viewer now follows the same high-level shell, so the Python runtime, browser replay, and README preview present the same interface structure.

Reproducibility and preservation:

1. The website replay is generated from a frozen config module, not the active tuning config.
2. The exported replay bundle records the frozen config source, the full config payload, and the Git commit in `docs/data/spatial-altruism-demo/manifest.json`.
3. That means you can keep tuning the active runtime without silently changing the website experiment.

## Research Basis

This module implements the Mitteldorf-Wilson population-viscosity model in three canonical modes: the steady-state variable-density form, the periodic uniform-culling disturbance form, and the compact-swath disturbance form. In all three modes, each lattice site is altruist, selfish, or empty; altruistic benefit is shared across a five-site von Neumann neighborhood; and the next occupant of each site is chosen through a local weighted lottery.

Parameter mapping to the paper:

1. `benefit_from_altruism` is the local altruistic benefit `b`.
2. `cost_of_altruism` is the altruist cost `c`.
3. `harshness` is the void fitness `eta`.
4. `disease` is the extra void lottery mass `xi` in the steady-state variant.
5. `model_variant` selects `steady_state`, `uniform_culling`, or `compact_swath`.
6. `uniform_culling_interval` is the number of generations between disturbance events in the uniform-culling variant.
7. `uniform_culling_fraction` is the share of all sites evacuated on each uniform-culling event.
8. `compact_swath_interval` is the number of generations between disturbance events in the compact-swath variant.
9. `compact_swath_fraction` is the target share of all sites covered by the compact square swath on each disturbance event.

Scope note:

1. This package matches the steady-state variable-density Mitteldorf-Wilson model.
2. It supports the paper's periodic uniform-culling disturbance variant as a canonical model mode.
3. It also supports the paper's compact-swath disturbance variant as a canonical model mode.

## Symbol Mapping

The table below maps the paper notation to the Python state and the exact update used in the steady-state implementation.

| Paper notation | Meaning in the paper | Python variable or state | Exact update in `spatial_altruism` |
| --- | --- | --- | --- |
| `A` | altruist occupant | `pcolor == PINK`, `benefit_out = 1.0` | site state set in initialization and next-generation lottery |
| `S` | selfish occupant | `pcolor == GREEN`, `benefit_out = 0.0` | site state set in initialization and next-generation lottery |
| `V` | empty site or void | `pcolor == BLACK` | site cleared by `_clear_patch_mask(...)` |
| `N_A` | number of altruists in the focal five-site neighborhood | `benefit_out + neighbors4_sum(benefit_out)` | `N_A = benefit_out[i] + sum_{j in N4(i)} benefit_out[j]` |
| `b` | altruistic benefit strength | `benefit_from_altruism` | `altruism_benefit = b * (N_A / 5)` |
| `c` | altruist cost | `cost_of_altruism` | altruist fitness includes `1 - c` |
| `W_A` | altruist fitness | `fitness` on altruist sites | `W_A = 1 - c + b * (N_A / 5)` |
| `W_S` | selfish fitness | `fitness` on selfish sites | `W_S = 1 + b * (N_A / 5)` |
| `eta` | void baseline fitness in the variable-density model | `harshness` | `W_V = eta = harshness` on empty sites |
| `A_i` | total altruist lottery mass in the focal competition neighborhood | `alt_fitness` | sum of altruist fitness from self plus four neighbors |
| `S_i` | total selfish lottery mass in the focal competition neighborhood | `self_fitness` | sum of selfish fitness from self plus four neighbors |
| `V_i` | total void lottery mass in the focal competition neighborhood | `harsh_fitness` | sum of void fitness from self plus four neighbors |
| `xi` | extra void lottery mass in the steady-state model | `disease` | added once per site in `_find_lottery_weights(...)` |
| `P(A)` | probability that the next occupant is altruist | `alt_weight` | `P(A) = A_i / (A_i + S_i + V_i + xi)` |
| `P(S)` | probability that the next occupant is selfish | `self_weight` | `P(S) = S_i / (A_i + S_i + V_i + xi)` |
| `P(V)` | probability that the next occupant is empty | `harsh_weight` | `P(V) = (V_i + xi) / (A_i + S_i + V_i + xi)` |

## Variant Comparison

The Mitteldorf-Wilson paper discusses three variable-density extensions. `spatial_altruism` now implements all three: the steady-state void model, the periodic uniform-culling model, and the compact-swath disturbance model.

Implemented here:

1. Steady-state variable-density model with void fitness `eta` and extra void lottery mass `xi`.
2. Periodic uniform culling with scheduled random evacuation of a fixed fraction of all sites.
3. Compact-swath culling with scheduled evacuation of a compact square region.
4. Local competition remains a five-site von Neumann lottery every generation.
5. Empty sites can persist continuously in steady-state mode because the void receives both local fitness `eta` and extra lottery mass `xi`.

What the new periodic uniform-culling mode does:

1. Keeps the same local five-site benefit, fitness, and reproduction lottery between disturbance events.
2. Uses `harshness = eta` as the void fitness term in the local lottery.
3. Disallows the steady-state `xi` term by requiring `disease = 0.0` in `uniform_culling` mode.
4. Clears a fixed fraction of all sites at a fixed generation interval, including already-empty sites, matching the paper's description of scheduled random evacuation.
5. Produces founder-effect regrowth because recolonization occurs between disturbance events rather than through a permanent extra void lottery mass.

What the compact-swath mode does:

1. Keeps the same local five-site benefit, fitness, and reproduction lottery between disturbance events.
2. Uses `harshness = eta` as the void fitness term in the local lottery.
3. Disallows the steady-state `xi` term by requiring `disease = 0.0` in `compact_swath` mode.
4. Clears a compact square swath centered on a random site at a fixed generation interval.
5. Uses torus wrapping when the world is toroidal and clamps the swath into bounds when the world is finite.
6. Produces recolonization fronts from the boundary of the cleared region rather than from isolated random vacancies.

Mechanism difference that matters:

1. The steady-state implementation creates emptiness continuously through `eta` and `xi`.
2. The culling variants create emptiness episodically through scheduled disturbance events.
3. Uniform culling scatters cleared sites across the lattice, while compact swath culling creates a contiguous recolonization front.
4. That difference changes the selection mechanism: the steady-state model is void competition, while the culling variants depend on founder effects and regrowth into newly cleared space.

## Features
- **Patch-based grid model**: Each cell can be empty (light beige), selfish (blue), or altruist (burgundy-red) in the current UI and website figures
- **Altruism dynamics**: Simulates benefit/cost of altruism, fitness, and generational updates
- **Fully vectorized**: Efficient NumPy implementation for fast simulation
- **Pygame UI**: Visualize and interact with the model in real time
- **Matplotlib plots**: Track population changes over time

## Files
- `altruism_model.py`: Core simulation logic (importable class and demo runner)
- `altruism_pygame_ui.py`: Pygame-based interactive UI
- `config/altruism_config.py`: Active runtime configuration and single source of truth for model and UI defaults
- `config/altruism_website_demo_config.py`: Frozen configuration used by the GitHub Pages replay export
- `images/`: Plotting scripts and generated Plotly or image outputs
- `utils/export_github_pages_demo.py`: Export utility that regenerates the sampled browser replay bundle and README GIF
- `utils/altruism_grid_search.py`: Parallel grid-search runner for extended coexistence sweeps
- `utils/altruism_culling_grid_search.py`: Culling-specific sweep runner for `uniform_culling` and `compact_swath`
- `utils/altruism_grid_search_original.py`: Original grid-search runner that writes coexistence probabilities
- `utils/altruism_grid_search_extended_original.py`: Original extended grid-search runner with population averages
- `data/culling_grid_search_results.csv`: Culling-sweep results for the disturbance variants
- `data/grid_search_results.csv`: Baseline grid-search results
- `data/grid_search_results copy.csv`: Copied baseline grid-search results
- `data/grid_search_results_extended.csv`: Extended grid-search results
- `utils/plotly_browser.py`: Shared Plotly HTML export and browser-launch helper
- `utils/plotting.py`: Shared heatmap plotting helper used by heatmap scripts
- `utils/pygame_helpers.py`: Shared Pygame drawing and history-plot helpers
- `images/plot_culling_heatmaps.py`: Interactive culling-variant heatmap viewer
- `pop_plot.png`: Example output plot (generated by UI)

## Repository Rename Note

On 2026-04-06, this module directory was renamed from `altruism/` to `spatial_altruism/`.

Stepwise impact:

1. The module now lives at `spatial_altruism/` in the repository.
2. Repo-root run commands should now use `spatial_altruism` package/module names.
3. Analysis scripts that read or write CSV results now point at `spatial_altruism/data/grid_search_results*.csv`.
4. Website GitHub links should now reference `spatial_altruism/` rather than the old folder name.
5. `spatial_altruism/__init__.py` now marks the folder as a Python package so package-aware runners can execute these files as modules.
6. Core runtime modules now use package-relative imports, so they should be run as modules from the repo root.
7. Plotly visualization scripts now write interactive `.html` files and try to open them in a browser, instead of relying on notebook-only `fig.show()` rendering.

## Utilities Refactor Note

On 2026-04-06, reusable helper code was consolidated into `spatial_altruism/utils/`.

Stepwise impact:

1. `plotly_browser.py` moved to `spatial_altruism/utils/plotly_browser.py`.
2. The duplicated `plot_heatmap_embedded(...)` implementation was extracted into `spatial_altruism/utils/plotting.py`.
3. Pygame helper functions for grid drawing, text drawing, and history plotting were extracted into `spatial_altruism/utils/pygame_helpers.py`.
4. Plotly and heatmap scripts now import these helpers from `spatial_altruism.utils`, and the Pygame UI now does so package-relatively as a module entrypoint.
5. The package now has a dedicated `utils/__init__.py`, so shared helpers live in one place instead of being embedded across multiple scripts.

## Grid Search Relocation Note

On 2026-04-06, the grid-search runners were moved into `spatial_altruism/utils/`.

Stepwise impact:

1. `altruism_grid_search.py` moved to `spatial_altruism/utils/altruism_grid_search.py`.
2. `altruism_grid_search_original.py` moved to `spatial_altruism/utils/altruism_grid_search_original.py`.
3. `altruism_grid_search_extended_original.py` moved to `spatial_altruism/utils/altruism_grid_search_extended_original.py`.
4. The moved scripts now import `AltruismModel` from the parent package and should be run as modules from the repo root.
5. Result CSV paths remain unchanged within the dataset names, but now read and write `spatial_altruism/data/grid_search_results*.csv`.

## Data Relocation Note

On 2026-04-06, the result CSV files were moved into `spatial_altruism/data/`.

Stepwise impact:

1. `grid_search_results.csv` moved to `spatial_altruism/data/grid_search_results.csv`.
2. `grid_search_results copy.csv` moved to `spatial_altruism/data/grid_search_results copy.csv`.
3. `grid_search_results_extended.csv` moved to `spatial_altruism/data/grid_search_results_extended.csv`.
4. All analysis scripts and grid-search runners now read from or write to the `data/` subdirectory.
5. Package documentation now treats `data/` as the canonical location for stored grid-search outputs.

## Requirements Relocation Note

On 2026-04-06, the package-local requirements file was moved to the repository root.

Stepwise impact:

1. `spatial_altruism/requirements.txt` moved to `requirements.txt`.
2. The root requirements file now acts as the install entrypoint for this workspace.
3. Manual install commands should now use `./.conda/bin/python -m pip install -r requirements.txt`.
4. The package directory no longer carries its own duplicate requirements file.

## Images Rename Note

On 2026-04-06, the plotting directory was renamed from `spatial_altruism/plotting/` to `spatial_altruism/images/`.

Stepwise impact:

1. `plot_heatmaps.py` now lives at `spatial_altruism/images/plot_heatmaps.py`.
2. `plot_heatmaps_extended.py` now lives at `spatial_altruism/images/plot_heatmaps_extended.py`.
3. `plot_coexistence_body_plotly.py`, `plot_coexistence_body_plotly_extended.py`, `plot_coexistence_body_plotly_extended copy.py`, and `plot_coexistence_surface_plotly.py` now live in `spatial_altruism/images/`.
4. The generated `plot_coexistence_body_plotly.html` file now lives in `spatial_altruism/images/` so generated visual outputs sit with the image-generation scripts.
5. Package documentation now refers to `images/` as the canonical home for these visual scripts and outputs.

## Config Introduction Note

On 2026-04-06, active runtime defaults were centralized into `spatial_altruism/config/altruism_config.py`.

Stepwise impact:

1. The model and UI now read their default parameters from `config/altruism_config.py` instead of hardcoding them in multiple modules.
2. `altruism_model.py` now builds `Params` from the active config via `make_params()`.
3. The main model run no longer uses CLI argument parsing; edit the config file directly before running.
4. The Pygame UI now reads window size, plot panel size, FPS, and world dimensions from the same active config module.
5. The grid-search runners now build model parameters from the canonical config and only override the sweep dimensions they explicitly vary.
6. Package imports can now use `make_params()` as the config-backed constructor for the default model state.
7. The config-backed runtime modules now follow the same module-only execution style used in `cooperative_hunting`.

## Uniform Culling Variant Note

On 2026-04-07, the paper's periodic uniform-culling disturbance variant was added as a canonical model mode.

Stepwise impact:

1. `config/altruism_config.py` and `config/altruism_website_demo_config.py` now define `model_variant`, `uniform_culling_interval`, and `uniform_culling_fraction`.
2. `altruism_model.py` now supports both `steady_state` and `uniform_culling` under the same core lattice and lottery mechanics.
3. The steady-state mode still uses `harshness = eta` and `disease = xi`.
4. The new uniform-culling mode treats scheduled evacuation as the disturbance mechanism and therefore requires `disease = 0.0`.
5. Disturbance events now clear a fixed fraction of all sites at a fixed interval, matching the paper's random uniform-culling description.
6. `make_params()` now merges overrides on top of the active config, so the config file remains the actual source of truth when utilities override only selected fields.
7. The live Pygame viewer now reflects the active model variant more safely by hiding the `disease` slider outside steady-state mode and showing the uniform-culling schedule in the control card.
8. The website copy now states both the equation-level provenance claim and its historical limitation explicitly.
9. The existing grid-search utilities now fail fast outside `steady_state`, because their sweep dimensions are defined around the `disease` and `harshness` parameterization of the steady-state model.

## Compact Swath and Culling Analysis Note

On 2026-04-07, the paper's compact-swath disturbance variant and culling-specific analysis workflow were added.

Stepwise impact:

1. `config/altruism_config.py` and `config/altruism_website_demo_config.py` now define `compact_swath_interval` and `compact_swath_fraction` alongside the existing uniform-culling schedule keys.
2. `altruism_model.py` now supports `compact_swath` as a third canonical `model_variant`.
3. The compact-swath mode clears a contiguous square region on disturbance generations instead of scattering isolated cleared sites.
4. The Pygame viewer now labels `compact_swath` distinctly from `uniform_culling` so the active disturbance mechanism is visible in the UI.
5. `utils/altruism_culling_grid_search.py` now provides a culling-focused sweep runner that compares `uniform_culling` and `compact_swath` on shared disturbance axes.
6. `images/plot_culling_heatmaps.py` now provides an interactive heatmap viewer for culling sweep outputs and multiple outcome metrics.
7. The replay manifest exporter now includes compact-swath config keys in its config excerpt, even though the website replay still uses the steady-state frozen config.

## Static Culling Figure Note

On 2026-04-08, the browser-facing surfaces were extended with static culling heatmap figures and preview-level culling conclusions.

Stepwise impact:

1. `images/export_culling_summary_heatmaps.py` now exports two static coexistence heatmaps for the website.
2. The exported figure files live under `docs/data/spatial-altruism-demo/` beside the replay bundle.
3. `docs/spatial-altruism/index.html` now embeds those static culling images below the replay layout.
4. The website now shows a direct visual comparison between `uniform_culling` and `compact_swath` at disturbance fraction `0.50`.
5. `utils/export_github_pages_demo.py` now includes the culling-results takeaway in the generated README GIF preview text.

## Culling Experiment Results

On 2026-04-07, a first culling-only sweep was run and written to `spatial_altruism/data/culling_grid_search_results.csv`.

Experiment design:

1. The sweep compared `uniform_culling` and `compact_swath`.
2. `benefit_from_altruism` was swept from `0.00` to `1.00` in steps of `0.05`.
3. `cost_of_altruism` was swept from `0.00` to `0.35` in steps of `0.05`.
4. `harshness` was fixed at `0.96`.
5. `disturbance_interval` was fixed at `50` generations.
6. `disturbance_fraction` was tested at `0.25` and `0.50`.
7. Initial altruist and selfish probabilities were both fixed at `0.39`.
8. Each parameter set used `5` replicates and was scored at step `1000`.

Observed summary:

1. The sweep covered `672` parameter combinations in total: `336` for `uniform_culling` and `336` for `compact_swath`.
2. `uniform_culling` had a higher mean coexistence probability than `compact_swath`: about `0.0887` versus `0.0565`.
3. `uniform_culling` also maintained higher mean occupancy than `compact_swath`: about `0.5086` versus `0.4001`.
4. Both variants reached parameter sets with coexistence probability `1.0` at disturbance fraction `0.25`.
5. `uniform_culling` produced more full-coexistence cells overall: `19` rows with coexistence probability `1.0`, versus `5` for `compact_swath`.
6. At disturbance fraction `0.50`, `uniform_culling` still reached coexistence probability `1.0`, while `compact_swath` topped out at `0.8` in this sweep.
7. The strongest compact-swath coexistence row in this run appeared at `benefit_from_altruism = 0.95`, `cost_of_altruism = 0.20`, `disturbance_fraction = 0.25`, with average occupancy about `0.757`.

Conclusions from this sweep:

1. Under the current settings, both disturbance variants can support altruist-selfish coexistence, so the culling-family behavior is not restricted to the random uniform case.
2. In this parameter range, `uniform_culling` is more robust than `compact_swath` by both coexistence frequency and retained occupancy.
3. `compact_swath` appears more sensitive to stronger disturbance: moving from fraction `0.25` to `0.50` drops its mean occupancy sharply, from about `0.593` to `0.207`.
4. `uniform_culling` also loses occupancy when disturbance increases, but it still preserves broader coexistence support at fraction `0.50` than `compact_swath` does in this run.
5. The current evidence suggests that contiguous swath clearing creates a harsher recolonization bottleneck than spatially scattered clearing under the same interval and nominal cleared fraction.
6. These are sweep-level observations for one fixed `harshness` and one fixed disturbance interval, not universal claims about the full model family.

## Live Grid Styling Note

On 2026-04-06, the Pygame live-grid viewer was restyled to match the cooperative-hunting replay shell.

Stepwise impact:

1. `altruism_pygame_ui.py` now uses the same header-card, world-card, and sidebar-card presentation pattern as `cooperative_hunting`.
2. The lattice now renders inside a framed world viewport with major and minor grid lines instead of the older bare edge-to-edge grid.
3. The live viewer controls now appear as replay-style chips for play, reset, history visibility, step, and FPS.
4. The history panel and parameter panel now use the same light card palette and typography direction as the cooperative-hunting viewer.
5. `utils/pygame_helpers.py` now draws the altruism grid and history colors with the same visual language used by the new live-grid shell.
6. The history/chart panel is now visible by default when the Pygame UI starts, controlled by `ui_history_visible_default` in the config.
7. The history chart now preserves its aspect ratio when fitted into the sidebar card, so chart text is no longer horizontally squeezed.

## Website Demo Export Note

On 2026-04-06, a sampled browser replay and README GIF preview were added for `spatial_altruism`.

Stepwise impact:

1. `config/altruism_website_demo_config.py` now freezes the parameter set used by the website replay.
2. `utils/export_github_pages_demo.py` now exports a sampled replay bundle into `docs/data/spatial-altruism-demo/`.
3. The same exporter also writes `assets/spatial_altruism/spatial_altruism_demo_preview.gif` for README embedding.
4. `docs/spatial-altruism/index.html` now provides a browser replay page styled in the same family as the cooperative-hunting website demo.
5. The replay bundle records the frozen config source, commit hash, and full config payload in its manifest for reproducibility.
6. The repo-level `.github/workflows/deploy-pages.yml` workflow now publishes that replay page through GitHub Pages on pushes to `main`.

## Usage
### Run the Model
Edit `spatial_altruism/config/altruism_config.py`, then run from the repo root:
```bash
./.conda/bin/python -m spatial_altruism.altruism_model
```

### Run the Pygame UI
Edit `spatial_altruism/config/altruism_config.py` if needed, then run from the repo root:
```bash
./.conda/bin/python -m spatial_altruism.altruism_pygame_ui
```
- Controls:
  - `SPACE`: Start/Stop simulation
  - `R`: Reset
  - `S`: Step
  - `P`: Plot population history
  - `+` / `-`: Increase or decrease playback FPS

### Export Website Demo
If you want to regenerate the browser replay bundle and README GIF, run from the repo root:
```bash
./.conda/bin/python -m spatial_altruism.utils.export_github_pages_demo
```
The exported browser replay lives under `docs/spatial-altruism/`.

### Run Grid Search
Edit `spatial_altruism/config/altruism_config.py` and the sweep block in the selected utility, then run from the repo root:
```bash
./.conda/bin/python -m spatial_altruism.utils.altruism_grid_search
```
These grid-search scripts currently target the steady-state `disease`/`harshness` parameter space and will stop with a clear message if `model_variant` is not `steady_state`.

### Run Culling Grid Search
Edit `spatial_altruism/config/altruism_config.py` and the sweep block in the culling utility, then run from the repo root:
```bash
./.conda/bin/python -m spatial_altruism.utils.altruism_culling_grid_search
```
This sweep compares the disturbance variants on shared axes such as `benefit_from_altruism`, `cost_of_altruism`, `harshness`, `disturbance_interval`, and `disturbance_fraction`.

### View Culling Heatmaps
After generating `spatial_altruism/data/culling_grid_search_results.csv`, run:
```bash
./.conda/bin/python -m spatial_altruism.images.plot_culling_heatmaps
```
The viewer lets you switch between `uniform_culling` and `compact_swath`, choose the disturbance schedule, and plot multiple outcome metrics over the `benefit_from_altruism` and `cost_of_altruism` plane.

### Export Static Culling Website Figures
To regenerate the two static culling comparison panels used by the website, run:
```bash
./.conda/bin/python -m spatial_altruism.images.export_culling_summary_heatmaps
```
The exported images are written into `docs/data/spatial-altruism-demo/` and are intended to match the culling sweep summary in the README and website.

### Import as a Module
```python
from spatial_altruism import AltruismModel, make_params

model = AltruismModel(make_params())
```

## Requirements
- Python 3.8+
- numpy
- pygame (for UI)
- matplotlib (for plotting)

Install dependencies:
```bash
./.conda/bin/python -m pip install -r requirements.txt
```
Install the additional system dependency for Pygame visualization:
```bash
conda install -y -c conda-forge gcc=14.2.0
```
## Model Parameters
- `model_variant`: `steady_state`, `uniform_culling`, or `compact_swath`
- `altruistic_probability`: Initial chance a patch is altruist
- `selfish_probability`: Initial chance a patch is selfish
- `benefit_from_altruism`: Benefit received from altruists
- `cost_of_altruism`: Cost paid by altruists
- `harshness`: Void fitness `eta`, which increases the competitive weight of empty patches
- `disease`: Extra void lottery mass `xi` in `steady_state`; set this to `0.0` in `uniform_culling` and `compact_swath`
- `uniform_culling_interval`: Number of generations between random evacuation events in `uniform_culling`
- `uniform_culling_fraction`: Fraction of all sites cleared on each `uniform_culling` event
- `compact_swath_interval`: Number of generations between compact-swath disturbance events in `compact_swath`
- `compact_swath_fraction`: Target fraction of all sites covered by the compact square swath in `compact_swath`

## References
- [Mitteldorf and Wilson, Population Viscosity and the Evolution of Altruism (short paper copy)](../docs/altruism_research/Population%20Viscosity%20and%20the%20Evolution%20of%20Altruism%20-%20short-%20mitteldorf_wilson.pdf)
- [Mitteldorf and Wilson, Population Viscosity and the Evolution of Altruism (journal PDF copy)](../docs/altruism_research/Population%20viscocity%20and%20the%20evolution%20of%20altruism-full.pdf)

---
## Research Summary

For a focal site with four cardinal neighbors, the model computes local altruistic benefit from the fraction of altruists in the five-site von Neumann neighborhood. The steady-state fitness equations are:

1. altruist fitness = `1 - c + b * (N_A / 5)`
2. selfish fitness = `1 + b * (N_A / 5)`
3. void fitness = `eta`

Variable meanings:

1. `c` is the direct cost paid by an altruist.
2. `b` is the local benefit created by altruistic neighbors.
3. `N_A` is the number of altruists in the focal five-site neighborhood, including the focal site itself.
4. `eta` is the baseline competitive weight of the void.
5. `xi` is an additional void term in the local reproduction lottery.

The next occupant of each site is then drawn from the summed altruist, selfish, and void fitness in the same five-site competition neighborhood, with an additional void weight `xi`. In this implementation, `harshness = eta` and `disease = xi` for `steady_state`.

In `uniform_culling`, the same local five-site competition remains in place but scheduled disturbance events clear a fixed fraction of sites at a fixed interval, and the always-on `xi` term is removed.

In `compact_swath`, the same local five-site competition remains in place but scheduled disturbance events clear a contiguous square swath centered on a random site, again with no always-on `xi` term.

This means the package now implements the steady-state Mitteldorf-Wilson model and both paper disturbance variants: periodic uniform culling and compact swath culling.

## Provenance Note

What is provable from observable mechanics:

1. The implemented state space, neighborhood geometry, fitness equations, and lottery equations match the steady-state variable-density Mitteldorf-Wilson model.
2. The code-level role of `harshness` matches the paper's void fitness `eta`.
3. The code-level role of `disease` matches the paper's extra void lottery mass `xi`.
4. The package also contains a separate periodic uniform-culling mode whose scheduled disturbance matches the paper's random evacuation mechanism.
5. The package also contains a compact-swath mode that clears contiguous square disturbance regions and reproduces the paper's local recolonization mechanism.
6. The package therefore can be described as implementing the Mitteldorf-Wilson steady-state model and both culling variants discussed in the paper.

What is not provable from observable mechanics alone:

1. Whether the implementation was historically derived directly from the paper, from another implementation, or from a curricular intermediary.
2. Whether every parameter choice in the repository was chosen to reproduce a specific experiment reported in the paper.
3. Whether every implementation detail, such as exact swath discretization and boundary placement, matches a specific historical implementation rather than the paper-level mechanism alone.
