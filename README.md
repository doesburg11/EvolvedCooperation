# EvolvedCooperation

A collection of agent-based models exploring cooperation, altruism, and
eco-evolutionary dynamics.

The current evolved-cooperation examples in this repo are:

- `spatial_altruism/`: a minimal spatial altruism model
- `cooperative_hunting/`: a spatial predator-prey-grass cooperative-hunting model
- `spatial_prisoners_dilemma/`: a spatial Prisoner's Dilemma ecology with local play, movement, reproduction, and inherited same-vs-other strategy encodings
- `retained_benefit/`: a lattice model that tests how much cooperative benefit
  must be routed back toward cooperators or their copies before cooperation can
  spread

Additional experimental module in this repo:

- `retained_kernel/`: a generalized retained-feedback kernel that makes the
  abstract routing rule behind `retained_benefit/` explicit in a separate
  Python package; it is not currently website-backed

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
`cooperative_hunting/`.

- Main runtime: `cooperative_hunting/cooperative_hunting.py`
- Active parameters: `cooperative_hunting/config/cooperative_hunting_config.py`
- Detailed model notes and theory mapping:
  `cooperative_hunting/README.md`

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
./.conda/bin/python -m cooperative_hunting.cooperative_hunting
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

The new `retained_benefit/` module is the repo's most direct attempt to test
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

- `spatial_altruism/`: local clustering plus void competition and disturbance
  can support altruist-selfish coexistence
- `spatial_prisoners_dilemma/`: conditional reciprocity can outperform pure
  defection, but it still yields coexistence rather than universal cooperation
- `cooperative_hunting/`: costly cooperation can pay when coordinated hunting
  creates real synergy, but the current active baseline is a supported-start
  threshold-synergy case rather than a pure de novo emergence test
- `retained_benefit/`: cooperation rises only when enough of the benefit it
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
	- `spatial_altruism/altruism_model.py`: Core simulation logic
	- `spatial_altruism/altruism_pygame_ui.py`: Pygame-based interactive UI
	- `spatial_altruism/config/altruism_config.py`: Active runtime configuration
	- `spatial_altruism/config/altruism_website_demo_config.py`: Frozen website replay configuration
	- `spatial_altruism/images/`: Plotting scripts and generated image or Plotly outputs
	- `spatial_altruism/utils/export_github_pages_demo.py`: Website replay and preview GIF exporter
	- `spatial_altruism/utils/altruism_grid_search.py`: Parallel grid search for extended coexistence sweeps
	- `spatial_altruism/data/grid_search_results_extended.csv`: Results from the parallel grid search
- **Usage:**
	- Run core model:
		```bash
		# edit spatial_altruism/config/altruism_config.py first if needed
		./.conda/bin/python -m spatial_altruism.altruism_model
		```
	- Run Pygame UI:
		```bash
		./.conda/bin/python -m spatial_altruism.altruism_pygame_ui
		```
	- Run grid search:
		```bash
		./.conda/bin/python -m spatial_altruism.utils.altruism_grid_search
		```
	- Regenerate website replay bundle:
		```bash
		./.conda/bin/python -m spatial_altruism.utils.export_github_pages_demo
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
	- `cooperative_hunting/cooperative_hunting.py`: core simulation and runtime entry point
	- `cooperative_hunting/config/cooperative_hunting_config.py`: active runtime parameters
	- `cooperative_hunting/utils/matplot_plotting.py`: Matplotlib plotting helpers for baseline runs
	- `cooperative_hunting/utils/sweep_dual_parameter.py`: parameter sweep tooling
	- `cooperative_hunting/utils/tune_mutual_survival.py`: coexistence tuning utilities
	- `cooperative_hunting/README.md`: detailed interpretation and experiment guide
- **Usage:**
	- Edit parameters in `cooperative_hunting/config/cooperative_hunting_config.py`
	- Run:
		```bash
		./.conda/bin/python -m cooperative_hunting.cooperative_hunting
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
	- relative to `spatial_altruism/`, this model adds explicit agents, energy budgets, pairwise Prisoner's Dilemma play, movement, and conditional reciprocity; `spatial_altruism/` is the simpler lattice model of altruist versus selfish site competition
	- relative to `cooperative_hunting/`, this model is more game-theoretic and less ecological: it has no prey, grass, hunt coalitions, or continuous cooperation trait
	- taken together, the three models form a progression from local altruist-benefit selection (`spatial_altruism/`), to local reciprocity and inherited response rules (`spatial_prisoners_dilemma/`), to ecological synergy in predator group hunting (`cooperative_hunting/`)
- **Files:**
	- `spatial_prisoners_dilemma/spatial_prisoners_dilemma.py`: core runtime, logging, and summary output
	- `spatial_prisoners_dilemma/config/spatial_prisoners_dilemma_config.py`: active runtime parameters
	- `spatial_prisoners_dilemma/config/spatial_prisoners_dilemma_website_demo_config.py`: frozen website replay configuration
	- `spatial_prisoners_dilemma/utils/matplot_plotting.py`: Matplotlib plotting helpers
	- `spatial_prisoners_dilemma/utils/export_github_pages_demo.py`: website replay exporter
	- `spatial_prisoners_dilemma/README.md`: detailed mechanism and adaptation notes
- **Usage:**
	- Edit parameters in `spatial_prisoners_dilemma/config/spatial_prisoners_dilemma_config.py`
	- Run:
		```bash
		./.conda/bin/python -m spatial_prisoners_dilemma.spatial_prisoners_dilemma
		```
	- Regenerate website replay bundle:
		```bash
		./.conda/bin/python -m spatial_prisoners_dilemma.utils.export_github_pages_demo
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
	- compared with `spatial_altruism/`, it replaces binary altruist-versus-selfish site types with a continuous cooperation trait and an explicit benefit-routing split
	- compared with `spatial_prisoners_dilemma/`, it removes repeated-game memory and discrete strategy families so the feedback structure is easier to isolate
	- compared with `cooperative_hunting/`, it removes predator-prey ecology and hunt-coalition mechanics so cooperative synergy is reduced to an abstract routing problem
	- it is therefore the most abstract website-facing module in the repo and the most direct test here of the claim that cooperation requires feedback
- **Files:**
	- `retained_benefit/retained_benefit_model.py`: core runtime, local benefit-routing rule, and summary output
	- `retained_benefit/retained_benefit_pygame_ui.py`: live lattice viewer with cooperation and lineage modes
	- `retained_benefit/config/retained_benefit_config.py`: active runtime parameters
	- `retained_benefit/config/retained_benefit_website_demo_config.py`: frozen website replay configuration
	- `retained_benefit/utils/matplot_plotting.py`: Matplotlib plotting helpers
	- `retained_benefit/utils/export_github_pages_demo.py`: website replay exporter
	- `retained_benefit/README.md`: detailed rationale and model explanation
- **Usage:**
	- Edit parameters in `retained_benefit/config/retained_benefit_config.py`
	- Run:
		```bash
		./.conda/bin/python -m retained_benefit.retained_benefit_model
		```
	- Run live viewer:
		```bash
		./.conda/bin/python -m retained_benefit.retained_benefit_pygame_ui
		```
	- Regenerate website replay bundle:
		```bash
		./.conda/bin/python -m retained_benefit.utils.export_github_pages_demo
		```
- **Current status:**
	- implements continuous cooperation traits plus inherited lineage labels on a spatial lattice
	- treats `retained_benefit_fraction` as the primary abstraction parameter
	- includes a Pygame viewer that can switch between cooperation intensity and lineage structure
	- exports a sampled website replay bundle from a frozen public config
	- writes JSON logs for headless analysis and can show a small Matplotlib summary figure

### Retained Kernel
- **Description:** General non-website-backed retained-feedback kernel that
  expresses the same core routing logic as `retained_benefit/` in more neutral
  trait-and-identity language.
- **Relation to the other evolved-cooperation models:**
	- relative to `retained_benefit/`, it keeps the same local routing and replacement mechanism but removes the website-facing model framing
	- relative to `spatial_altruism/`, it still uses synchronous local copying rather than discrete altruist versus selfish site states
	- relative to `spatial_prisoners_dilemma/`, it has no explicit pairwise game, memory, or strategy family labels
	- relative to `cooperative_hunting/`, it removes ecological entities and leaves only the retained-feedback kernel itself
- **Files:**
	- `retained_kernel/retained_kernel_model.py`: core retained-kernel runtime and summary output
	- `retained_kernel/retained_kernel_pygame_ui.py`: live lattice viewer with trait and identity modes
	- `retained_kernel/config/retained_kernel_config.py`: active runtime parameters
	- `retained_kernel/utils/matplot_plotting.py`: Matplotlib plotting helpers
	- `retained_kernel/README.md`: detailed kernel description and relation to `retained_benefit/`
- **Usage:**
	- Edit parameters in `retained_kernel/config/retained_kernel_config.py`
	- Run:
		```bash
		./.conda/bin/python -m retained_kernel.retained_kernel_model
		```
	- Run live viewer:
		```bash
		./.conda/bin/python -m retained_kernel.retained_kernel_pygame_ui
		```
- **Current status:**
	- keeps the config file as the single source of truth for normal runs
	- uses general `trait`, `identity`, and `retention_fraction` naming rather than the website-facing retained-benefit terminology
	- includes a Pygame viewer that can switch between trait intensity and identity structure
	- writes JSON logs for headless analysis and can show a small Matplotlib summary figure
	- is present only in the Python repo for now and does not yet have a matching website page

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
- See `spatial_altruism/README.md` for more details
