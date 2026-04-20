# Spatial Prisoner's Dilemma Module

This package is a CPU-side spatial Prisoner's Dilemma ecology inspired by
`zeyus-research/FLAMEGPU2-Prisoners-Dilemma-ABM`.

It keeps the core evolved-cooperation structure of that model:

- many agents on a spatial grid
- local Moore-neighborhood interactions
- movement when no games are played
- energy budgets
- local asexual reproduction into adjacent empty cells
- mutation and strategy inheritance
- death from energy loss and a hard population cap

This module is now website-wired. It is a canonical Python package inside
`EvolvedCooperation`, and it now has a matching replay page in the sibling
`human-cooperation-site` repo at
`/evolved-cooperation/spatial-prisoners-dilemma/`.

## Spatial Prisoners Dilemma Addition Note

On 2026-04-17, `spatial_prisoners_dilemma/` was added as a new experimental
evolved-cooperation module.

Stepwise impact:

1. The repo now contains a third package-level evolved-cooperation model beside
   `spatial_altruism/` and `cooperative_hunting/`.
2. The new package follows the same repo convention: edit the config file,
   then run the module from the repo root with `./.conda/bin/python -m ...`.
3. The implementation preserves the main external mechanics: directional local
   play, fallback movement, local reproduction, mutation, strategy inheritance,
   cost of living, and population culling.
4. The default grid and population sizes are reduced relative to the FLAMEGPU
   version so the model remains practical as a pure Python CPU run.
5. At that stage, the package exported JSON logs and Matplotlib plots instead
   of a GPU visualizer or website replay.

## Spatial Prisoner's Dilemma Website Replay Note

On 2026-04-18, the module gained a frozen website-demo config and a replay
export pipeline that feeds the `human-cooperation-site` page.

Stepwise impact:

1. `config/spatial_prisoners_dilemma_website_demo_config.py` now freezes the
   public website run separately from the editable live config.
2. `utils/export_github_pages_demo.py` now exports a sampled replay bundle with
   `manifest.json`, `summary.json`, and chunked `frames_XXXX.json` files.
3. The matching site page can now cite one deterministic canonical run rather
   than a moving target from the active config file.
4. The exported viewer colors agents by same-trait strategy family, while the
   full export still keeps trait identity and other-trait responses available.

## Spatial Prisoner's Dilemma Pygame Viewer Note

On 2026-04-18, the module gained a live Pygame grid viewer for stepwise local
inspection of the active run.

Stepwise impact:

1. `spatial_prisoners_dilemma_pygame_ui.py` now provides a direct live viewer
   for the active config file.
2. The viewer colors agents by same-trait strategy family, matching the main
   browser replay and site page.
3. The interface supports play, pause, single-step advance, reset, and FPS
   control.
4. A same-trait strategy history chart now updates inside the live viewer while
   the simulation runs.

## Relation To The FLAMEGPU Model

Faithful parts of the port:

1. Agents occupy one cell each on a wrapped Moore-neighborhood lattice.
2. Every step begins with a local neighborhood search and a die-roll ordering
   that decides which side challenges and which side responds.
3. Each neighboring edge is played at most once per step.
4. Agents only attempt movement if they played no games in that step.
5. Reproduction is local, asexual, and contested when multiple parents claim
   the same empty target cell.
6. Children inherit parental strategies with mutation, and keep the parental
   trait identity.
7. Newborns skip the same-step cost-of-living deduction unless they are
   removed by the hard population cap.

Deliberate CPU-side adaptations:

1. The default grid is much smaller than the original CUDA-scale world.
2. Directional play is resolved synchronously within each subround, which keeps
   the intended local mechanics while avoiding some message-order edge cases
   from the original GPU implementation.
3. Tit-for-tat memory is stored as directional local memory slots in Python,
   matching the intent of the original slot-based encounter memory.
4. The package now supports both headless analysis/logging and a lightweight
   live Pygame grid viewer.

## Package Contents

- `spatial_prisoners_dilemma.py`
  Main runtime, initialization, step logic, logging, and summary output.
- `spatial_prisoners_dilemma_pygame_ui.py`
  Live Pygame grid viewer for the active config file.
- `config/spatial_prisoners_dilemma_config.py`
  Active configuration module and normal source of truth for the run.
- `config/spatial_prisoners_dilemma_website_demo_config.py`
   Frozen configuration used by the website replay export.
- `utils/matplot_plotting.py`
  Matplotlib helpers for population, energy, and strategy-family plots.
- `utils/export_github_pages_demo.py`
   Website replay exporter for the sampled static JSON bundle.

## Quick Start

Use the repo-local Python environment from the repository root:

```bash
./.conda/bin/python -m spatial_prisoners_dilemma.spatial_prisoners_dilemma
```

For the live Pygame viewer:

```bash
./.conda/bin/python -m spatial_prisoners_dilemma.spatial_prisoners_dilemma_pygame_ui
```

Normal workflow:

1. Edit `config/spatial_prisoners_dilemma_config.py`.
2. Run the module with the command above.
3. Inspect the terminal summaries, exported JSON log, and optional plots.

To regenerate the website replay bundle from the frozen public config:

```bash
./.conda/bin/python -m spatial_prisoners_dilemma.utils.export_github_pages_demo
```

## Strategy Encoding

Strategies:

- `always_cooperate`
- `always_defect`
- `tit_for_tat`
- `random`

Traits:

- each agent carries one trait index in `0..trait_count-1`
- the default run uses `trait_count = 4`

The default encoding matches the external repo defaults:

1. `pure_strategy = False`
2. `strategy_per_trait = False`
3. each agent therefore carries one strategy for same-trait encounters and one
   strategy for other-trait encounters

The stored `strategy_id` matches the external analysis convention:

<p>`strategy_id = 10 * own_strategy + other_strategy`</p>

Examples:

1. `00` = co-op pure
2. `13` = defect contingent (random)
3. `22` = tit-for-tat pure

## One Step Of Simulation

The main update order is:

1. All agents search their eight neighboring cells and draw a local die roll.
2. Each neighboring pair is ordered by that roll, so one side challenges and
   the other responds.
3. The Prisoner's Dilemma is resolved across eight directional subrounds.
4. Agents that played no games pay the travel cost and may compete to move into
   an adjacent empty cell.
5. Agents above the reproduction threshold may compete to place offspring into
   adjacent empty cells.
6. Newborns are appended to the population.
7. Agents above the hard index-based cap are culled.
8. Remaining non-newborn agents pay the environmental cost of living.

Variables used in the game phase:

1. `payoff_cc`: reward to both agents if both cooperate.
2. `payoff_cd`: reward to the cooperator if the opponent defects.
3. `payoff_dc`: reward to the defector if the opponent cooperates.
4. `payoff_dd`: reward to both agents if both defect.
5. `env_noise`: independent probability that an intended action is flipped.

Variables used in the demographic phase:

1. `travel_cost`: flat energy cost of attempting movement.
2. `reproduce_min_energy`: minimum energy required to attempt reproduction.
3. `reproduce_cost`: direct energy payment for a successful birth.
4. `reproduction_inheritance`: child starting energy as a fraction of the
   parent's post-cost energy when this value is in `(0, 1]`.
5. `cost_of_living`: per-step environmental energy loss for surviving
   non-newborn agents.

## Logged Outputs

When `write_log` is enabled, the module writes a JSON payload containing:

1. the resolved config values
2. per-step histories for population, births, deaths, movement, and game counts
3. same-trait and other-trait strategy-family counts
4. the final population state

Default output path:

```text
spatial_prisoners_dilemma/data/latest_run.json
```

## Conclusion From The Current Default Run

Under the active default config, this experiment does not collapse to universal
cooperation or universal defection. It reaches a mixed spatial regime in which
same-trait tit-for-tat becomes the largest strategy family, while co-op,
defect, and random all remain present.

The default run also fills the world very quickly. On a `60 x 60` grid with a
`50%` carrying-capacity cap, the population reaches the `1800`-agent hard
limit by about step `26`, and movement then becomes rare because most agents
play at least one local game each step.

So the current default result should be read narrowly:

1. conditional reciprocity outperforms pure defection under these local rules
2. coexistence persists rather than a single inherited rule taking over
3. the outcome is strongly shaped by a fast-crowding, energy-rich ecology

In that sense, the current experiment supports tit-for-tat as the strongest
same-trait strategy in a dense local interaction regime, not a general claim
that cooperation always evolves.

## Current Status

This module is ready for both canonical Python-side experimentation and the
matching sampled website replay pipeline.

## References

- Axelrod, R., & Hamilton, W. D. (1981). The Evolution of Cooperation.
  *Science*, 211(4489), 1390-1396.
- Hammond, R. A., & Axelrod, R. (2006). The evolution of ethnocentrism.
  *Journal of Conflict Resolution*, 50(6), 926-936.
- `zeyus-research/FLAMEGPU2-Prisoners-Dilemma-ABM`
