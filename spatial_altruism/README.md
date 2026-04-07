# Spatial Altruism Model

A vectorized Python/NumPy implementation of the Mitteldorf-Wilson spatial altruism model. The default website replay and live demo use the steady-state variable-density population-viscosity variant, and the package also supports the paper's periodic uniform-culling disturbance variant. In both modes, altruist, selfish, and empty patches compete locally on a two-dimensional lattice through five-site weighted lotteries. It includes a Pygame UI for interactive exploration and Matplotlib plotting for population dynamics.

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

This module implements the Mitteldorf-Wilson population-viscosity model in two canonical modes: the steady-state variable-density form and the periodic uniform-culling disturbance form. In both modes, each lattice site is altruist, selfish, or empty; altruistic benefit is shared across a five-site von Neumann neighborhood; and the next occupant of each site is chosen through a local weighted lottery.

Parameter mapping to the paper:

1. `benefit_from_altruism` is the local altruistic benefit `b`.
2. `cost_of_altruism` is the altruist cost `c`.
3. `harshness` is the void fitness `eta`.
4. `disease` is the extra void lottery mass `xi` in the steady-state variant.
5. `model_variant` selects either steady-state void competition or periodic uniform culling.
6. `uniform_culling_interval` is the number of generations between disturbance events in the uniform-culling variant.
7. `uniform_culling_fraction` is the share of all sites evacuated on each uniform-culling event.

Scope note:

1. This package matches the steady-state variable-density Mitteldorf-Wilson model.
2. It also now supports the paper's periodic uniform-culling disturbance variant as a canonical model mode.
3. The compact-swath culling variant is still not implemented.

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
| `W_A` | altruist fitness | `fitness` on pink sites | `W_A = 1 - c + b * (N_A / 5)` |
| `W_S` | selfish fitness | `fitness` on green sites | `W_S = 1 + b * (N_A / 5)` |
| `eta` | void baseline fitness in the variable-density model | `harshness` | `W_V = eta = harshness` on black sites |
| `A_i` | total altruist lottery mass in the focal competition neighborhood | `alt_fitness` | sum of altruist fitness from self plus four neighbors |
| `S_i` | total selfish lottery mass in the focal competition neighborhood | `self_fitness` | sum of selfish fitness from self plus four neighbors |
| `V_i` | total void lottery mass in the focal competition neighborhood | `harsh_fitness` | sum of void fitness from self plus four neighbors |
| `xi` | extra void lottery mass in the steady-state model | `disease` | added once per site in `_find_lottery_weights(...)` |
| `P(A)` | probability that the next occupant is altruist | `alt_weight` | `P(A) = A_i / (A_i + S_i + V_i + xi)` |
| `P(S)` | probability that the next occupant is selfish | `self_weight` | `P(S) = S_i / (A_i + S_i + V_i + xi)` |
| `P(V)` | probability that the next occupant is empty | `harsh_weight` | `P(V) = (V_i + xi) / (A_i + S_i + V_i + xi)` |

## Variant Comparison

The Mitteldorf-Wilson paper discusses three variable-density extensions. `spatial_altruism` now implements two of them: the steady-state void model and the periodic uniform-culling model. The compact-swath disturbance model remains absent.

Implemented here:

1. Steady-state variable-density model with void fitness `eta` and extra void lottery mass `xi`.
2. Periodic uniform culling with scheduled random evacuation of a fixed fraction of all sites.
3. Local competition remains a five-site von Neumann lottery every generation.
4. Empty sites can persist continuously in steady-state mode because the void receives both local fitness `eta` and extra lottery mass `xi`.

Not implemented here:

1. Compact-swath culling.

What the new periodic uniform-culling mode does:

1. Keeps the same local five-site benefit, fitness, and reproduction lottery between disturbance events.
2. Uses `harshness = eta` as the void fitness term in the local lottery.
3. Disallows the steady-state `xi` term by requiring `disease = 0.0` in `uniform_culling` mode.
4. Clears a fixed fraction of all sites at a fixed generation interval, including already-empty sites, matching the paper's description of scheduled random evacuation.
5. Produces founder-effect regrowth because recolonization occurs between disturbance events rather than through a permanent extra void lottery mass.

What would need to change to implement compact-swath culling exactly:

1. Add a disturbance schedule parameter, as above.
2. On disturbance generations, choose a random center point and clear a square swath sized to cover half of the grid area, rather than clearing random isolated sites.
3. Reuse the same no-`xi` disturbance interpretation used in uniform culling, because vacancies should arise from evacuation events rather than a permanent extra void term.
4. Preserve the between-disturbance local reproduction lottery so recolonization proceeds inward from the surviving boundary into the cleared region.
5. Add explicit swath-geometry logic and a paper-faithful definition of how the cleared square interacts with world boundaries.

Mechanism difference that matters:

1. The current implementation creates emptiness continuously through `eta` and `xi`.
2. The culling variants create emptiness episodically through scheduled disturbance events.
3. That difference changes the selection mechanism: the current model is steady-state void competition, while the culling variants depend on founder effects and regrowth into newly cleared space.

## Features
- **Patch-based grid model**: Each cell can be empty (black), selfish (green), or altruist (pink)
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
- `utils/altruism_grid_search_original.py`: Original grid-search runner that writes coexistence probabilities
- `utils/altruism_grid_search_extended_original.py`: Original extended grid-search runner with population averages
- `data/grid_search_results.csv`: Baseline grid-search results
- `data/grid_search_results copy.csv`: Copied baseline grid-search results
- `data/grid_search_results_extended.csv`: Extended grid-search results
- `utils/plotly_browser.py`: Shared Plotly HTML export and browser-launch helper
- `utils/plotting.py`: Shared heatmap plotting helper used by heatmap scripts
- `utils/pygame_helpers.py`: Shared Pygame drawing and history-plot helpers
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
- `model_variant`: `steady_state` or `uniform_culling`
- `altruistic_probability`: Initial chance a patch is altruist
- `selfish_probability`: Initial chance a patch is selfish
- `benefit_from_altruism`: Benefit received from altruists
- `cost_of_altruism`: Cost paid by altruists
- `harshness`: Void fitness `eta`, which increases the competitive weight of empty patches
- `disease`: Extra void lottery mass `xi` in `steady_state`; set this to `0.0` in `uniform_culling`
- `uniform_culling_interval`: Number of generations between random evacuation events in `uniform_culling`
- `uniform_culling_fraction`: Fraction of all sites cleared on each `uniform_culling` event

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

This means the package now implements the steady-state Mitteldorf-Wilson model and the paper's periodic uniform-culling variant, but not the compact-swath variant.

## Provenance Note

What is provable from observable mechanics:

1. The implemented state space, neighborhood geometry, fitness equations, and lottery equations match the steady-state variable-density Mitteldorf-Wilson model.
2. The code-level role of `harshness` matches the paper's void fitness `eta`.
3. The code-level role of `disease` matches the paper's extra void lottery mass `xi`.
4. The package also contains a separate periodic uniform-culling mode whose scheduled disturbance matches the paper's random evacuation mechanism.
5. The package therefore can be described as implementing the Mitteldorf-Wilson steady-state model and the paper's periodic uniform-culling variant.

What is not provable from observable mechanics alone:

1. Whether the implementation was historically derived directly from the paper, from another implementation, or from a curricular intermediary.
2. Whether every parameter choice in the repository was chosen to reproduce a specific experiment reported in the paper.
3. Whether the authors intended the package to stand for the full family of Mitteldorf-Wilson models, because the compact-swath disturbance variant is still absent.
