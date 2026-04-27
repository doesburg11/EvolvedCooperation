# EvolvedCooperation

A collection of agent-based models exploring cooperation, altruism, and
eco-evolutionary dynamics.

The current evolved-cooperation examples in this repo are:

- `ecological_models/spatial_altruism/`: a minimal spatial altruism model
- `ecological_models/cooperative_hunting/`: a spatial predator-prey-grass cooperative-hunting model
- `ecological_models/spatial_prisoners_dilemma/`: a spatial Prisoner's Dilemma ecology with local play, movement, reproduction, and inherited same-vs-other strategy encodings
- `ecological_models/retained_benefit/`: a lattice model that tests how much cooperative benefit
  must be routed back toward cooperators or their copies before cooperation can
  spread

Additional experimental module in this repo:

- `moran_models/interaction_kernel/`: a general interaction-kernel engine with explicit
	positive/negative routing and pluggable selection dynamics that can be used
	to instantiate mechanisms such as kin selection

## Model Directory Refactor Note

On 2026-04-27, model packages were grouped under `ecological_models/` and
`moran_models/`.

Stepwise impact:

1. Website-facing spatial ecology packages now live under `ecological_models/`.
2. Moran-process mechanism packages now live under `moran_models/`.
3. Python module entrypoints now use the category prefix, for example
   `./.conda/bin/python -m ecological_models.cooperative_hunting.cooperative_hunting`
   and `./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.kin_selection_model`.
4. Generated model logs and analysis outputs now write under the moved package
   directories instead of recreating old top-level folders.
5. Existing public website routes and root `assets/` paths are unchanged.

## Nowak Mechanisms Directory Note

On 2026-04-27, the explicit Nowak mechanism Moran wrappers were nested under
`moran_models/nowak_mechanisms/`.

Stepwise impact:

1. `moran_models/nowak_mechanisms/direct_reciprocity/`,
   `moran_models/nowak_mechanisms/group_selection/`,
   `moran_models/nowak_mechanisms/indirect_reciprocity/`,
   `moran_models/nowak_mechanisms/kin_selection/`, and
   `moran_models/nowak_mechanisms/network_reciprocity/` now hold the five
   wrapper packages.
2. `moran_models/interaction_kernel/` remains the shared engine and comparison
   layer rather than a named Nowak wrapper.
3. Imports now use `moran_models.nowak_mechanisms.<mechanism>`.
4. Module entrypoints now include the `nowak_mechanisms` segment.
5. Mechanism-specific log and sweep output paths now write under
   `moran_models/nowak_mechanisms/<mechanism>/`.

## Cross-Repo Mapping

`EvolvedCooperation` is the canonical implementation repo for the
website-facing evolved-cooperation models.

The public website `https://humanbehaviorpatterns.org/` is built from the
sibling `human-cooperation-site` repo, so the matching website pages should
stay faithful to the Python implementations here.

For detailed cross-repo mapping and repository maintenance notes, see
`AGENTS.md`.

## Environments
This repo uses a project-local Conda environment stored at `.conda/` so it travels with the workspace and VS Code can auto-select it.

- Interpreter path: `/EvolvedCooperation/.conda/bin/python`
- VS Code setting: see `.vscode/settings.json` (we set `python.defaultInterpreterPath`, point VS Code at the local Conda executable, and use a repo-specific terminal profile instead of fixed-script launch entries)
- Matplotlib cache/config path for VS Code runs: `.vscode/.env` sets `MPLCONFIGDIR=.matplotlib`
- Ruff editor linting: install Ruff into the project environment with `./.conda/bin/python -m pip install ruff`
- Pylance note: `.vscode/settings.json` disables `reportMissingModuleSource` so compiled Matplotlib modules do not produce false-positive import warnings in editor diagnostics

### VS Code Run/Terminal behavior
The workspace is configured so VS Code uses the repo-local `.conda` deterministically:

1. `Terminal => New Terminal` opens `bash (.conda)`, which sources the normal shell startup and then activates `/EvolvedCooperation/.conda`.
2. `Run => Run Without Debugging` uses `.vscode/launch.json` plus `.vscode/run_active_python.py` to inspect the active editor file.
3. If the active file lives inside a Python package in the repo, the helper runs it with module semantics (`runpy.run_module(...)`), which matches `python -m ...` from the repo root and satisfies module-only guards.
4. If the active file is not inside a package, the helper falls back to normal script execution (`runpy.run_path(...)`).
5. The launch config still forces `${workspaceFolder}/.conda/bin/python`, so runs do not depend on whichever interpreter VS Code happened to remember previously.


## Current Focus

The most actively documented ecology model in the repo lives in
`ecological_models/cooperative_hunting/`.

- Main runtime: `ecological_models/cooperative_hunting/cooperative_hunting.py`
- Active parameters: `ecological_models/cooperative_hunting/config/cooperative_hunting_config.py`
- Detailed model notes and theory mapping:
  `ecological_models/cooperative_hunting/README.md`

Current mechanics in that model:

- predators carry a heritable continuous hunt investment trait `hunt_investment_trait in [0,1]`
- hunt contribution is `predator_energy * hunt_investment_trait`
- predator cooperation cost is paid directly as
  `predator_cooperation_cost_per_unit * hunt_investment_trait`
- the config file now uses descriptive canonical parameter names, while legacy
  short aliases remain accepted for backward compatibility
- optional plasticity has been removed from the active code path, so the stored
  trait is the value used for hunting and cost

Browser replay preview:

[![Cooperative Hunting](assets/cooperative_hunting/cooperative_hunting_demo_preview.gif)](https://doesburg11.github.io/EvolvedCooperation/cooperative-hunting/)

Click the full-window animation preview to open the GitHub Pages replay viewer.

Project convention for this model:

- prefer editing parameters inside the config file rather than passing CLI
  parameter overrides
- run from repo root with `./.conda/bin/python`

Minimal run example:
```bash
./.conda/bin/python -m ecological_models.cooperative_hunting.cooperative_hunting
```

## Cross-Model Synthesis

Taken together, the four current website-facing evolved-cooperation modules do
not support a strong claim that cooperation simply appears by default. They
support a more specific claim: cooperation persists only when the update rules
and ecology give cooperators some protection against immediate exploitation.

A useful near-universal formulation is: cooperation evolves when the benefits
created by cooperation flow back to cooperators, or to copies of the
cooperative rule, strongly enough to outweigh the private cost. In shorthand:
there is no cooperation without feedback.

The new `ecological_models/retained_benefit/` module is the repo's most direct attempt to test
that claim in a deliberately abstract form.

Shared pattern across the current models:

1. There must be heritable variation in a cooperative trait or strategy.
2. Interactions must be local enough that cooperative benefits are not spread
   completely at random.
3. Some feedback mechanism must return enough of the cooperative benefit back
   toward cooperators.
4. Reproduction and turnover must allow successful local structures to spread.
5. The private cost of cooperation must stay low enough relative to the
   protected benefit.

The four modules implement that protection in different ways:

- `ecological_models/spatial_altruism/`: local clustering plus void competition and disturbance
  can support altruist-selfish coexistence
- `ecological_models/spatial_prisoners_dilemma/`: conditional reciprocity can outperform pure
  defection, but it still yields coexistence rather than universal cooperation
- `ecological_models/cooperative_hunting/`: costly cooperation can pay when coordinated hunting
  creates real synergy, but the current active baseline is a supported-start
  threshold-synergy case rather than a pure de novo emergence test
- `ecological_models/retained_benefit/`: cooperation rises only when enough of the benefit it
  creates is routed back toward cooperators or their copies rather than leaking
  broadly to free-riders

So the strongest repo-level conclusion at this stage is modest:

- the minimal conditions are not one magic parameter, but a bundle of
  assortment, feedback, inheritance, and a favorable cost-benefit ratio
- without such protection, selfish behavior usually wins
- with it, cooperation can persist, spread, or coexist, depending on the
  mechanism
- these models are mechanism-level demonstrations, not a universal law of the
  evolution of cooperation

## Models

### Spatial Altruism
- **Description:** Patch-based grid simulation of altruism vs selfishness, ported from NetLogo to Python/NumPy.
- **Browser replay preview:**

[![Spatial Altruism](assets/spatial_altruism/spatial_altruism_demo_preview.gif)](https://doesburg11.github.io/EvolvedCooperation/spatial-altruism/)

- **Features:**
	- Each cell can be empty (black), selfish (green), or altruist (pink)
	- Simulates benefit/cost of altruism, fitness, and generational updates
	- Fully vectorized NumPy implementation for fast simulation
	- Pygame UI for interactive exploration
	- Matplotlib plots for population dynamics
	- Grid search for parameter sweeps
	- Sampled browser replay and README GIF preview
- **Files:**
	- `ecological_models/spatial_altruism/altruism_model.py`: Core simulation logic
	- `ecological_models/spatial_altruism/altruism_pygame_ui.py`: Pygame-based interactive UI
	- `ecological_models/spatial_altruism/config/altruism_config.py`: Active runtime configuration
	- `ecological_models/spatial_altruism/config/altruism_website_demo_config.py`: Frozen website replay configuration
	- `ecological_models/spatial_altruism/images/`: Plotting scripts and generated image or Plotly outputs
	- `ecological_models/spatial_altruism/utils/export_github_pages_demo.py`: Website replay and preview GIF exporter
	- `ecological_models/spatial_altruism/utils/altruism_grid_search.py`: Parallel grid search for extended coexistence sweeps
	- `ecological_models/spatial_altruism/data/grid_search_results_extended.csv`: Results from the parallel grid search
- **Usage:**
	- Run core model:
		```bash
		# edit ecological_models/spatial_altruism/config/altruism_config.py first if needed
		./.conda/bin/python -m ecological_models.spatial_altruism.altruism_model
		```
	- Run Pygame UI:
		```bash
		./.conda/bin/python -m ecological_models.spatial_altruism.altruism_pygame_ui
		```
	- Run grid search:
		```bash
		./.conda/bin/python -m ecological_models.spatial_altruism.utils.altruism_grid_search
		```
	- Regenerate website replay bundle:
		```bash
		./.conda/bin/python -m ecological_models.spatial_altruism.utils.export_github_pages_demo
		```
- **Requirements:**
	- Python 3.8+
	- numpy
	- pygame (for UI)
	- matplotlib (for plotting)
	- torch (for surface fitting)

### Cooperative Hunting
- **Description:** Spatial predator-prey ecology where predators evolve a
  continuous cooperation trait that affects group hunting success, payoff
  sharing, and private cooperation cost.
- **Files:**
	- `ecological_models/cooperative_hunting/cooperative_hunting.py`: core simulation and runtime entry point
	- `ecological_models/cooperative_hunting/config/cooperative_hunting_config.py`: active runtime parameters
	- `ecological_models/cooperative_hunting/utils/matplot_plotting.py`: Matplotlib plotting helpers for baseline runs
	- `ecological_models/cooperative_hunting/utils/sweep_dual_parameter.py`: parameter sweep tooling
	- `ecological_models/cooperative_hunting/utils/tune_mutual_survival.py`: coexistence tuning utilities
	- `ecological_models/cooperative_hunting/README.md`: detailed interpretation and experiment guide
- **Usage:**
	- Edit parameters in `ecological_models/cooperative_hunting/config/cooperative_hunting_config.py`
	- Run:
		```bash
		./.conda/bin/python -m ecological_models.cooperative_hunting.cooperative_hunting
		```
- **Current status:**
	- uses raw inherited `hunt_investment_trait` directly for hunt effort and cooperation cost
	- supports equal-split or contribution-weighted prey sharing
	- includes headless analysis, pygame live rendering, and sweep/tuning helpers

### Spatial Prisoner's Dilemma
- **Description:** Spatial Prisoner's Dilemma ecology inspired by the
  FLAMEGPU implementation from `zeyus-research/FLAMEGPU2-Prisoners-Dilemma-ABM`.
  Agents interact locally, move when isolated, reproduce into neighboring empty
  cells, and inherit mutable strategies.
- **Relation to the other evolved-cooperation models:**
	- relative to `ecological_models/spatial_altruism/`, this model adds explicit agents, energy budgets, pairwise Prisoner's Dilemma play, movement, and conditional reciprocity; `ecological_models/spatial_altruism/` is the simpler lattice model of altruist versus selfish site competition
	- relative to `ecological_models/cooperative_hunting/`, this model is more game-theoretic and less ecological: it has no prey, grass, hunt coalitions, or continuous cooperation trait
	- taken together, the three models form a progression from local altruist-benefit selection (`ecological_models/spatial_altruism/`), to local reciprocity and inherited response rules (`ecological_models/spatial_prisoners_dilemma/`), to ecological synergy in predator group hunting (`ecological_models/cooperative_hunting/`)
- **Files:**
	- `ecological_models/spatial_prisoners_dilemma/spatial_prisoners_dilemma.py`: core runtime, logging, and summary output
	- `ecological_models/spatial_prisoners_dilemma/config/spatial_prisoners_dilemma_config.py`: active runtime parameters
	- `ecological_models/spatial_prisoners_dilemma/config/spatial_prisoners_dilemma_website_demo_config.py`: frozen website replay configuration
	- `ecological_models/spatial_prisoners_dilemma/utils/matplot_plotting.py`: Matplotlib plotting helpers
	- `ecological_models/spatial_prisoners_dilemma/utils/export_github_pages_demo.py`: website replay exporter
	- `ecological_models/spatial_prisoners_dilemma/README.md`: detailed mechanism and adaptation notes
- **Usage:**
	- Edit parameters in `ecological_models/spatial_prisoners_dilemma/config/spatial_prisoners_dilemma_config.py`
	- Run:
		```bash
		./.conda/bin/python -m ecological_models.spatial_prisoners_dilemma.spatial_prisoners_dilemma
		```
	- Regenerate website replay bundle:
		```bash
		./.conda/bin/python -m ecological_models.spatial_prisoners_dilemma.utils.export_github_pages_demo
		```
- **Current status:**
	- preserves the intended spatial play, movement, reproduction, mutation, and culling logic from the external model family
	- uses smaller CPU-friendly defaults instead of the original CUDA-scale population sizes
	- now exports both JSON run logs for analysis and a sampled website replay bundle from a frozen public config
	- now maps to the `human-cooperation-site` page at `/evolved-cooperation/spatial-prisoners-dilemma/`

### Retained Benefit
- **Description:** Abstract lattice model that tests a general cooperation
  condition: cooperation spreads when enough of the value it creates is routed
  back toward cooperators, or copies of the cooperative rule, to offset its
  private cost.
- **Relation to the other evolved-cooperation models:**
	- compared with `ecological_models/spatial_altruism/`, it replaces binary altruist-versus-selfish site types with a continuous cooperation trait and an explicit benefit-routing split
	- compared with `ecological_models/spatial_prisoners_dilemma/`, it removes repeated-game memory and discrete strategy families so the feedback structure is easier to isolate
	- compared with `ecological_models/cooperative_hunting/`, it removes predator-prey ecology and hunt-coalition mechanics so cooperative synergy is reduced to an abstract routing problem
	- it is therefore the most abstract website-facing module in the repo and the most direct test here of the claim that cooperation requires feedback
- **Files:**
	- `ecological_models/retained_benefit/retained_benefit_model.py`: core runtime, local benefit-routing rule, and summary output
	- `ecological_models/retained_benefit/retained_benefit_pygame_ui.py`: live lattice viewer with cooperation and lineage modes
	- `ecological_models/retained_benefit/config/retained_benefit_config.py`: active runtime parameters
	- `ecological_models/retained_benefit/config/retained_benefit_website_demo_config.py`: frozen website replay configuration
	- `ecological_models/retained_benefit/utils/matplot_plotting.py`: Matplotlib plotting helpers
	- `ecological_models/retained_benefit/utils/export_github_pages_demo.py`: website replay exporter
	- `ecological_models/retained_benefit/README.md`: detailed rationale and model explanation
- **Usage:**
	- Edit parameters in `ecological_models/retained_benefit/config/retained_benefit_config.py`
	- Run:
		```bash
		./.conda/bin/python -m ecological_models.retained_benefit.retained_benefit_model
		```
	- Run live viewer:
		```bash
		./.conda/bin/python -m ecological_models.retained_benefit.retained_benefit_pygame_ui
		```
	- Regenerate website replay bundle:
		```bash
		./.conda/bin/python -m ecological_models.retained_benefit.utils.export_github_pages_demo
		```
- **Current status:**
	- implements continuous cooperation traits plus inherited lineage labels on a spatial lattice
	- treats `retained_benefit_fraction` as the primary abstraction parameter
	- includes a Pygame viewer that can switch between cooperation intensity and lineage structure
	- exports a sampled website replay bundle from a frozen public config
	- writes JSON logs for headless analysis and can show a small Matplotlib summary figure

### Interaction Kernel
- **Description:** General non-website-backed interaction-kernel engine that
  separates trait-dependent production, positive and negative effect routing,
  fitness score formation, local selection, and inheritance.
- **Relation to the other evolved-cooperation models:**
	- relative to `ecological_models/retained_benefit/`, it is broader than retained benefit routing because it supports separate positive and negative kernels
	- relative to `ecological_models/spatial_altruism/`, it keeps the spatial local-selection structure but uses continuous traits and configurable routing kernels
	- relative to `ecological_models/spatial_prisoners_dilemma/`, it has no explicit pairwise game, memory, or strategy family labels unless those are added as mechanism-specific extensions
	- relative to `ecological_models/cooperative_hunting/`, it removes ecological entities and leaves a reusable produced-effect, routed-effect, and selection core
- **Files:**
	- `moran_models/interaction_kernel/interaction_kernel_model.py`: core interaction-kernel runtime and summary output
	- `moran_models/interaction_kernel/kernels.py`: positive and negative routing-kernel builders
	- `moran_models/interaction_kernel/selection.py`: local replacement and inheritance logic
	- `moran_models/interaction_kernel/metrics.py`: per-step summary metrics
	- `moran_models/interaction_kernel/config/interaction_kernel_config.py`: active runtime parameters
	- `moran_models/interaction_kernel/README.md`: detailed kernel description and rename note
- **Usage:**
	- Edit parameters in `moran_models/interaction_kernel/config/interaction_kernel_config.py`
	- Run:
		```bash
		./.conda/bin/python -m moran_models.interaction_kernel.interaction_kernel_model
		```
- **Current status:**
	- keeps the config file as the single source of truth for normal runs
	- uses theory-aligned `h`, `B_plus`, `B_minus`, `K_plus`, `K_minus`, `R_plus`, `R_minus`, `C`, and `W` notation
	- currently supports uniform and kin-weighted positive kernels plus none or uniform negative kernels
	- writes JSON logs for headless analysis
	- is present only in the Python repo for now and does not yet have a matching website page

## Ecological Models vs Moran Models: Feature Comparison

The table below summarizes the main differences between the ecological models and the Moran-process-based models in this repository:

| Feature / Aspect                | Ecological Models (`ecological_models/`)                | Moran Models (`moran_models/`)                       |
|----------------------------------|--------------------------------------------------------|------------------------------------------------------|
| **Purpose**                      | Mechanistic, spatial, ecological scenarios             | Mechanism-level, abstract, theory-aligned wrappers   |
| **Typical Use**                  | Website-facing, interactive, ecological demonstrations | Mechanism comparison, theory testing, Nowak mapping  |
| **Spatial Structure**            | Explicit grid/lattice, local movement, patch dynamics  | Explicit grid/lattice with configurable von Neumann or Moore neighborhoods|
| **Agent Representation**         | Explicit agents (cells, predators, prey, etc.)         | Implicit or explicit, often trait vectors            |
| **Trait Inheritance**            | Local reproduction, mutation, ecological turnover      | Moran process (birth-death, replacement, mutation)   |
| **Interaction Mechanism**        | Local play, ecological feedback, explicit payoffs      | Kernel-based routing, payoff matrices, mechanism plug-ins |
| **Selection Dynamics**           | Ecological (birth, death, predation, movement)         | Moran process (random replacement, fitness-proportional) |
| **Model Complexity**             | Higher (multiple species, explicit ecology)            | Lower (single trait, abstracted mechanism)           |
| **Parameterization**             | Ecological parameters (e.g., cost, benefit, synergy)   | Mechanism parameters (e.g., relatedness, group size) |
| **Output/Analysis**              | Population time series, spatial plots, browser replay   | JSON logs, summary statistics, pygame live viewers; no browser replay export|
| **Website Integration**          | Yes (browser replay, public viewers)                   | No (Python only, not directly website-backed)        |
| **Example Modules**              | spatial_altruism, cooperative_hunting,                | kin_selection, group_selection,                     |
|                                  | spatial_prisoners_dilemma, retained_benefit           | direct_reciprocity, indirect_reciprocity,           |
|                                  |                                                    | network_reciprocity, interaction_kernel             |

This distinction helps clarify which models are intended for ecological realism and browser demonstration, and which are for mechanism-level, theory-driven comparison.

## Installation
Install dependencies:
```bash
pip install numpy pygame matplotlib torch
```
For Pygame visualization, you may need:
```bash
conda install -y -c conda-forge gcc=14.2.0
```

## References
- Original NetLogo models from Uri Wilensky and the EACH unit (Evolution of Altruistic and Cooperative Habits)
- See `ecological_models/spatial_altruism/README.md` for more details
