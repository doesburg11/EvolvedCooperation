# EvolvedCooperation

A collection of agent-based models exploring cooperation, altruism, and
eco-evolutionary dynamics. The current most actively documented model is
`predpreygrass_cooperative_hunting`, a spatial predator-prey cooperation model
with heritable continuous cooperation traits.

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
./.conda/bin/python -m pip install -r altruism/requirements.txt
./.conda/bin/python altruism/altruism_model.py
```

If you see a “bad interpreter” error, regenerate entry scripts (pip, etc.) with:
```bash
./.conda/bin/python -m pip install --upgrade --force-reinstall pip setuptools wheel
```

## Current Focus

The active predator-prey cooperation model lives in
`predpreygrass_cooperative_hunting/`.

- Main runtime: `predpreygrass_cooperative_hunting/cooperative_hunting.py`
- Active parameters: `predpreygrass_cooperative_hunting/config/cooperative_hunting_config.py`
- Detailed model notes and theory mapping:
  `predpreygrass_cooperative_hunting/README.md`

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

[![Predator-Prey-Grass Cooperative Hunting](assets/predprey_cooperative_hunting/cooperative_hunting_demo_preview.gif)](https://doesburg11.github.io/EvolvedCooperation/)

Click the full-window animation preview to open the GitHub Pages replay viewer.

Project convention for this model:

- prefer editing parameters inside the config file rather than passing CLI
  parameter overrides
- run from repo root with `./.conda/bin/python`

Minimal run example:
```bash
./.conda/bin/python -m predpreygrass_cooperative_hunting.cooperative_hunting
```

## Models

### Altruism Model
- **Description:** Patch-based grid simulation of altruism vs selfishness, ported from NetLogo to Python/NumPy.
- **Features:**
	- Each cell can be empty (black), selfish (green), or altruist (pink)
	- Simulates benefit/cost of altruism, fitness, and generational updates
	- Fully vectorized NumPy implementation for fast simulation
	- Pygame UI for interactive exploration
	- Matplotlib plots for population dynamics
	- Grid search for parameter sweeps
- **Files:**
	- `altruism_model.py`: Core simulation logic (importable class, CLI demo, and plotting)
	- `altruism_pygame_ui.py`: Pygame-based interactive UI
	- `altruism_grid_search.py`: Grid search for coexistence probabilities
	- `plot_coexistence_surface.py`, `plot_heatmaps.py`: Visualization scripts
	- `grid_search_results.csv`: Results from grid search
- **Usage:**
	- Run CLI demo:
		```bash
		python altruism/altruism_model.py --steps 200 --width 101 --height 101 --seed 42
		```
	- Run Pygame UI:
		```bash
		python altruism/altruism_pygame_ui.py
		```
	- Run grid search:
		```bash
		python altruism/altruism_grid_search.py
		```
- **Requirements:**
	- Python 3.8+
	- numpy
	- pygame (for UI)
	- matplotlib (for plotting)
	- torch (for surface fitting)

### Cooperation Model
- **Description:** Evolutionary biology model of greedy vs cooperative agents (cows) competing for grass, ported from NetLogo.
- **Features:**
	- Agents move, eat, reproduce, and die based on energy and grass availability
	- Cooperative cows avoid eating low grass, greedy cows eat regardless
	- Grass regrows at different rates depending on height
	- Pygame UI for visualization
- **Files:**
	- `cooperation_model.py`: Core simulation logic
	- `cooperation_pygame_ui.py`: Pygame-based interactive UI
	- `Cooperation.nlogox`: Original NetLogo model
- **Usage:**
	- Run CLI demo:
		```bash
		python cooperation/cooperation_model.py
		```
	- Run Pygame UI:
		```bash
		python cooperation/cooperation_pygame_ui.py
		```
- **Requirements:**
	- Python 3.8+
	- numpy
	- pygame
	- matplotlib

### Predator-Prey Cooperative Hunting Model
- **Description:** Spatial predator-prey ecology where predators evolve a
  continuous cooperation trait that affects group hunting success, payoff
  sharing, and private cooperation cost.
- **Files:**
	- `predpreygrass_cooperative_hunting/cooperative_hunting.py`: core simulation and runtime entry point
	- `predpreygrass_cooperative_hunting/config/cooperative_hunting_config.py`: active runtime parameters
	- `predpreygrass_cooperative_hunting/utils/matplot_plotting.py`: Matplotlib plotting helpers for baseline runs
	- `predpreygrass_cooperative_hunting/utils/sweep_dual_parameter.py`: parameter sweep tooling
	- `predpreygrass_cooperative_hunting/utils/tune_mutual_survival.py`: coexistence tuning utilities
	- `predpreygrass_cooperative_hunting/README.md`: detailed interpretation and experiment guide
- **Usage:**
	- Edit parameters in `predpreygrass_cooperative_hunting/config/cooperative_hunting_config.py`
	- Run:
		```bash
		./.conda/bin/python -m predpreygrass_cooperative_hunting.cooperative_hunting
		```
- **Current status:**
	- uses raw inherited `hunt_investment_trait` directly for hunt effort and cooperation cost
	- supports equal-split or contribution-weighted prey sharing
	- includes headless analysis, pygame live rendering, and sweep/tuning helpers

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
- See `altruism/README.md` and `cooperation/Cooperation.nlogox` for more details
