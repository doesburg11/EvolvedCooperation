# EvolvedCooperation

A collection of agent-based models exploring cooperation, altruism, and
eco-evolutionary dynamics.

The current website-ready evolved-cooperation examples in this repo are:

- `spatial_altruism/`: a minimal spatial altruism model
- `cooperative_hunting/`: a spatial predator-prey-grass cooperative-hunting model
- `spatial_prisoners_dilemma/`: a spatial Prisoner's Dilemma ecology with local play, movement, reproduction, and inherited same-vs-other strategy encodings

A more abstract, generalization-oriented cooperation module now also lives in:

- `retained_benefit/`: a lattice model that tests how much cooperative benefit
  must be routed back toward cooperators or their copies before cooperation can
  spread

A third, simpler evolutionary model remains available in `cooperation/` as a
possible later website example.

## Cross-Repo Mapping

`EvolvedCooperation` is the canonical implementation repo for the website-ready
evolved-cooperation models.

The public website `https://humanbehaviorpatterns.org/` is built from the
sibling `human-cooperation-site` repo and should describe these models
1-to-1.

Current required mapping:

- `spatial_altruism/` in this repo <-> the `spatial_altruism` page/section in
  `human-cooperation-site`
- `cooperative_hunting/` in this repo <-> the `cooperative_hunting`
  page/section in `human-cooperation-site`
- `spatial_prisoners_dilemma/` in this repo <-> the
	`spatial-prisoners-dilemma` page/section in `human-cooperation-site`

Working rule:

- when a model implementation changes here, review the matching website page
- when a website explanation changes there, keep it faithful to the Python code
  here

## Environments
This repo uses a project-local Conda environment stored at `.conda/` so it travels with the workspace and VS Code can auto-select it.

- Interpreter path: `/home/doesburg/Projects/EvolvedCooperation/.conda/bin/python`
- VS Code setting: see `.vscode/settings.json` (we set `python.defaultInterpreterPath`, point VS Code at the local Conda executable, and use a repo-specific terminal profile instead of fixed-script launch entries)
- Matplotlib cache/config path for VS Code runs: `.vscode/.env` sets `MPLCONFIGDIR=.matplotlib`
- Ruff editor linting: install Ruff into the project environment with `./.conda/bin/python -m pip install ruff`
- Pylance note: `.vscode/settings.json` disables `reportMissingModuleSource` so compiled Matplotlib modules do not produce false-positive import warnings in editor diagnostics

### VS Code Run/Terminal behavior
The workspace is configured so VS Code uses the repo-local `.conda` deterministically:

1. `Terminal => New Terminal` opens `bash (.conda)`, which sources the normal shell startup and then activates `/home/doesburg/Projects/EvolvedCooperation/.conda`.
2. `Run => Run Without Debugging` uses `.vscode/launch.json` plus `.vscode/run_active_python.py` to inspect the active editor file.
3. If the active file lives inside a Python package in the repo, the helper runs it with module semantics (`runpy.run_module(...)`), which matches `python -m ...` from the repo root and satisfies module-only guards.
4. If the active file is not inside a package, the helper falls back to normal script execution (`runpy.run_path(...)`).
5. The launch config still forces `${workspaceFolder}/.conda/bin/python`, so runs do not depend on whichever interpreter VS Code happened to remember previously.

Activate the environment in a terminal when running commands manually:
```bash
source /home/doesburg/miniconda3/etc/profile.d/conda.sh
conda activate "$(pwd)/.conda"
# or run without activation using the interpreter directly:
./.conda/bin/python -m pip install -r requirements.txt
./.conda/bin/python -m spatial_altruism.altruism_model
```

If you see a “bad interpreter” error, regenerate entry scripts (pip, etc.) with:
```bash
./.conda/bin/python -m pip install --upgrade --force-reinstall pip setuptools wheel
```

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

## Website Landing Page Note

On 2026-04-06, the repo-level website root was turned into a multi-demo landing page.

Stepwise impact:

1. `docs/index.html` now acts as a landing page that lists the available replay demos instead of embedding one specific simulation.
2. The cooperative-hunting browser replay now lives at `docs/cooperative-hunting/index.html`.
3. The spatial-altruism browser replay continues to live at `docs/spatial-altruism/index.html`.
4. README links now point directly to each demo route instead of assuming the root site always hosts the cooperative-hunting replay.

## Landing Page Feedback Loop Note

On 2026-04-10, the landing page gained a conceptual display that clarifies the eco-evolutionary feedback loop around learning and plasticity.

Stepwise impact:

1. `docs/index.html` now includes a full-width `Why the feedback loop matters` section beneath the demo cards.
2. The new display presents the loop as a four-step sequence: evolution shapes learning capacities, learning reshapes ecological structure, ecological structure reshapes selection gradients, and plasticity closes the loop.
3. The landing page now also contrasts unstable and stable environments so the selection logic behind higher versus lower plasticity is visible at a glance.
4. `docs/style.css` now includes responsive home-page styles for that explanatory display while staying in the existing card-based visual system.

## GitHub Pages Deployment Note

On 2026-04-06, the repo gained an explicit GitHub Pages deployment workflow for the interactive viewers.

Stepwise impact:

1. `.github/workflows/deploy-pages.yml` now publishes the repo-level `docs/` site on pushes to `main`.
2. `docs/index.html` now labels both demo entry points as `Open Interactive Viewer` so the viewer routes are explicit.
3. The public routes remain `docs/cooperative-hunting/index.html` and `docs/spatial-altruism/index.html`; the workflow only changes how those pages are deployed.
4. If the repository Pages setting is not already using `GitHub Actions`, switch it there so this workflow becomes the active publisher.

Project convention for this model:

- prefer editing parameters inside the config file rather than passing CLI
  parameter overrides
- run from repo root with `./.conda/bin/python`

Minimal run example:
```bash
./.conda/bin/python -m cooperative_hunting.cooperative_hunting
```

## Website Roadmap

Current website examples under evolved cooperation:

- `Spatial Altruism` -> `spatial_altruism/altruism_model.py`
- `Cooperative Hunting` -> `cooperative_hunting/cooperative_hunting.py`
- `Spatial Prisoner's Dilemma` -> `spatial_prisoners_dilemma/spatial_prisoners_dilemma.py`

Generalization-oriented experimental module:

- `Retained Benefit` -> `retained_benefit/retained_benefit_model.py`

Strong next candidate for later addition:

- `Cooperative vs Greedy Grazing` -> `cooperation/cooperation_model.py`

## Cross-Model Synthesis

Taken together, the three current website-facing evolved-cooperation modules do
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

The three modules implement that protection in different ways:

- `spatial_altruism/`: local clustering plus void competition and disturbance
  can support altruist-selfish coexistence
- `spatial_prisoners_dilemma/`: conditional reciprocity can outperform pure
  defection, but it still yields coexistence rather than universal cooperation
- `cooperative_hunting/`: costly cooperation can pay when coordinated hunting
  creates real synergy, but the current active baseline is a supported-start
  threshold-synergy case rather than a pure de novo emergence test

So the strongest repo-level conclusion at this stage is modest:

- the minimal conditions are not one magic parameter, but a bundle of
  assortment, feedback, inheritance, and a favorable cost-benefit ratio
- without such protection, selfish behavior usually wins
- with it, cooperation can persist, spread, or coexist, depending on the
  mechanism
- these models are mechanism-level demonstrations, not a universal law of the
  evolution of cooperation

## Cooperative Hunting Rename Note

On 2026-04-06, the package directory for the predator-prey-grass model was renamed from `predpreygrass_cooperative_hunting/` to `cooperative_hunting/`.

Stepwise impact:

1. The Python package now lives at `cooperative_hunting/`.
2. Module entrypoints now use `./.conda/bin/python -m cooperative_hunting...` from the repo root.
3. Internal asset paths moved from `assets/predprey_cooperative_hunting/` to `assets/cooperative_hunting/`.
4. Utility output paths now write to `cooperative_hunting/images/`.
5. The package rename initially affected the Python/package layer; the public viewer route was renamed separately on 2026-04-07.

## Public Viewer Rename Note

On 2026-04-07, the cooperative-hunting browser viewer and website slug were renamed from `predator-prey-cooperative-hunting` to `cooperative-hunting`.

Stepwise impact:

1. The repo-level replay page moved from `docs/predator-prey-cooperative-hunting/index.html` to `docs/cooperative-hunting/index.html`.
2. GitHub Pages links now point to `/cooperative-hunting/`.
3. The `humanbehaviorpatterns.org` page and replay paths now use `/evolved-cooperation/cooperative-hunting/`.
4. The public viewer title and landing-page label now read `Cooperative Hunting`, while the descriptive copy still explains that it is a predator-prey-grass ecology.

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

### Cooperative vs Greedy Grazing
- **Description:** Evolutionary model of greedy vs cooperative cows competing for regrowing grass.
- **Features:**
	- Agents move, eat, reproduce, and die based on energy and grass availability
	- Cooperative cows avoid eating low grass, greedy cows eat regardless
	- Grass regrows at different rates depending on height
	- Pygame UI for visualization
- **Files:**
	- `cooperation/cooperation_model.py`: Core simulation logic
	- `cooperation/cooperation_pygame_ui.py`: Pygame-based interactive UI
	- `cooperation/Cooperation.nlogox`: Original NetLogo model
- **Usage:**
	- Run CLI demo:
		```bash
		./.conda/bin/python cooperation/cooperation_model.py
		```
	- Run Pygame UI:
		```bash
		./.conda/bin/python cooperation/cooperation_pygame_ui.py
		```
- **Requirements:**
	- Python 3.8+
	- numpy
	- pygame
	- matplotlib

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
- **Description:** Abstract lattice model designed to test a more general
  cooperation claim: cooperation rises when enough of its benefit is routed
  back to cooperators, or to copies of the cooperative rule, to offset its
  private cost.
- **Relation to the other evolved-cooperation models:**
	- unlike `spatial_altruism/`, it does not fix cooperation as a binary altruist-versus-selfish site type
	- unlike `spatial_prisoners_dilemma/`, it does not rely on repeated-game memory or discrete strategy families
	- unlike `cooperative_hunting/`, it does not rely on a predator-prey ecological story or hunt coalition mechanics
	- it is therefore the most abstraction-first module in the repo and the closest thing here to a direct `no cooperation without feedback` test
- **Files:**
	- `retained_benefit/retained_benefit_model.py`: core runtime, local benefit-routing rule, and summary output
	- `retained_benefit/retained_benefit_pygame_ui.py`: live lattice viewer with cooperation and lineage modes
	- `retained_benefit/config/retained_benefit_config.py`: active runtime parameters
	- `retained_benefit/utils/matplot_plotting.py`: Matplotlib plotting helpers
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
- **Current status:**
	- implements continuous cooperation traits plus inherited lineage labels on a spatial lattice
	- treats `retained_benefit_fraction` as the main abstraction knob
	- now includes a Pygame viewer that can switch between cooperation intensity and lineage structure
	- writes JSON logs for headless analysis and can show a small Matplotlib summary figure

## Spatial Prisoner's Dilemma Addition Note

On 2026-04-17, `spatial_prisoners_dilemma/` was added as a new experimental
module in this repository.

Stepwise impact:

1. The repo now contains a dedicated spatial Prisoner's Dilemma package rather
   than only a future experiment note.
2. The new module follows the same package-run convention as the newer models:
   edit the config file, then run it from the repo root with `python -m`.
3. The implementation keeps the external model's central mechanism family:
   local pairwise PD interactions, fallback movement, local reproduction,
   inheritance, mutation, death, and a hard population cap.
4. The default world size is reduced so the model remains practical as a pure
   Python CPU simulation in this repo.
5. The package is canonical on the Python side now and has a matching
	`human-cooperation-site` page and replay route.

## Spatial Prisoner's Dilemma Website Replay Note

On 2026-04-18, `spatial_prisoners_dilemma/` gained a frozen website-demo config
and replay export pipeline.

Stepwise impact:

1. `spatial_prisoners_dilemma/config/spatial_prisoners_dilemma_website_demo_config.py`
	now freezes the public site run.
2. `spatial_prisoners_dilemma/utils/export_github_pages_demo.py` now exports a
	sampled static replay bundle under `docs/data/spatial-prisoners-dilemma-demo/`.
3. The sibling `human-cooperation-site` repo now has a matching page and replay
	route at `/evolved-cooperation/spatial-prisoners-dilemma/`.
4. Cross-repo fidelity for this module now includes both the explanatory docs
	page and the sampled browser replay data bundle.

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
- See `spatial_altruism/README.md` and `cooperation/Cooperation.nlogox` for more details
