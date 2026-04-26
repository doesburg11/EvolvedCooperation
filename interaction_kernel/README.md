# Interaction Kernel

## Purpose

`interaction_kernel/` is a **Moran-process engine** for evolving a single heritable trait
(such as cooperation or strategy) under spatially local selection. It separates:

1. trait-dependent produced effects (help, harm, or public goods),
2. routing those effects through configurable kernels to neighbors,
3. fitness computation,
4. local selection and inheritance.

Use this module to implement cooperation mechanisms like kin selection, network
reciprocity, or mixed help-harm interactions by configuring kernels and parameters without
changing the core simulation code.

## Design

`interaction_kernel/` is a general, reusable simulation engine for models that
separate:

1. action or trait-dependent produced effects,
2. routing through explicit positive and negative kernels,
3. fitness score formation,
4. selection and inheritance.

This package is designed as an abstract base module in `EvolvedCooperation` so
named mechanisms (for example kin selection, network reciprocity, or mixed
help-harm settings) can be implemented as configurations or thin wrappers.

## Shared Core Reorganization Note

On 2026-04-26, `interaction_kernel/` was reorganized into a shared Moran core
plus named Nowak-mechanism package wrappers.

Stepwise impact:

1. `interaction_kernel/core/` now holds the canonical reusable Moran engine,
   space helpers, kernel helpers, metrics, and selection logic.
2. `interaction_kernel_model.py` remains the config-driven package entrypoint,
   but now runs on top of `interaction_kernel.core` instead of owning all
   engine details directly.
3. Two named mechanism packages now run on the shared core immediately:
   `kin_selection/` and `network_reciprocity/`.
4. Three more Nowak mechanism packages now exist as explicit repo slots with
   their own config files and READMEs: `direct_reciprocity/`,
   `indirect_reciprocity/`, and `group_selection/`.
5. `direct_reciprocity/` now has a first runnable implementation using
   persistent received-help memory on top of the shared Moran core.
6. `indirect_reciprocity/` is now runnable with an explicit reputation state
   channel that biases positive routing.
7. `group_selection/` is now runnable with explicit group membership and a
   periodic between-group copying event.
8. The shared mechanism API now supports a post-reproduction update hook so
   mechanisms can implement multi-level dynamics when needed.
9. The older top-level `kernels.py`, `selection.py`, and `metrics.py` modules
   now act as compatibility re-exports while the canonical implementation lives
   under `interaction_kernel/core/`.
10. The live-grid viewer pattern is now shared through
   `interaction_kernel/live_grid_view.py`, and named mechanism packages expose
   their own pygame entrypoints instead of relying only on the generic package
   viewer.

## Why This Module Exists

The repo already contains named website-facing mechanisms and a retained-kernel
generalization. This package adds a broader interaction core with explicit
positive and negative channels and pluggable kernel behavior while keeping one
clean Moran-style evolutionary update.

The architectural goal is:

> build one canonical core once, then instantiate mechanism-specific special
> cases without duplicating simulation logic.

## Current Core Dynamics (Moran)

Each site carries:

- one continuous trait `h in [0, 1]`
- one inherited identity label

At each synchronous step:

1. Produced effects:
   - `B_plus = B_plus_scale * h`
   - `B_minus = B_minus_scale * h`
2. Kernel routing:
   - `R_plus = K_plus^T * B_plus`
   - `R_minus = K_minus^T * B_minus`
3. Score:
   - `W = base_fitness + R_plus - R_minus - C_scale * h`
4. Local replacement:
   - each site samples a parent from its neighborhood via local softmax fitness
   - trait mutates with probability `mutation_rate`
   - identity is inherited from the sampled parent

This keeps the produced -> routed -> selected chain explicit in code.

## Theory Variable Mapping

This module uses variable names chosen to stay close to the notation used on
the website theory page.

- `h`: trait value per site
- `B_plus`: produced positive effect
- `B_minus`: produced negative effect
- `K_plus`: positive routing kernel
- `K_minus`: negative routing kernel
- `R_plus`: received positive routed effect
- `R_minus`: received negative routed effect
- `C`: private cost
- `W`: fitness or selection score

Implemented core equations:

- `B_plus = B_plus_scale * h`
- `B_minus = B_minus_scale * h`
- `R_plus = K_plus^T @ B_plus`
- `R_minus = K_minus^T @ B_minus`
- `C = C_scale * h`
- `W = base_fitness + R_plus - R_minus - C`

Config note:

- Canonical keys are `B_plus_scale`, `B_minus_scale`, and `C_scale`.
- Legacy keys `positive_output_scale`, `negative_output_scale`, and
   `trait_cost_scale` are still accepted for backward compatibility.

## Kernel Modes

Current kernel options are intentionally small and explicit:

- positive kernel:
  - `uniform`
  - `kin_weighted`
- negative kernel:
  - `none`
  - `uniform`

The `kin_weighted` option uses separate weights for same-lineage and
other-lineage recipients, then row-normalizes so each producer's routed share
is interpretable.

## Configuration Source Of Truth

As with other repo modules, runtime parameters live in:

- `interaction_kernel/config/interaction_kernel_config.py`

The active `config` dict is the intended source of truth for normal runs.

## Package Files

- `interaction_kernel_model.py`: config-driven runtime entry point for the
   general interaction-kernel package.
- `core/engine.py`: reusable Moran engine with pluggable mechanism logic.
- `core/space.py`: neighborhood and adjacency helpers.
- `core/kernels.py`: canonical kernel construction helpers.
- `core/selection.py`: canonical local selection and inheritance helpers.
- `core/metrics.py`: per-step summary metrics.
- `core/mechanisms.py`: mechanism classes shared by named packages.
- `config/interaction_kernel_config.py`: active runtime config.

## Named Nowak Mechanism Packages

Current repo-level organization for the five mechanisms:

- `kin_selection/`
   Runnable named wrapper over the shared core using lineage-biased positive
   routing.
- `network_reciprocity/`
   Runnable named wrapper over the shared core using local graph structure and
   uniform neighbor routing.
- `direct_reciprocity/`
   Runnable named wrapper using persistent received-help memory as the direct
   reciprocity state.
- `indirect_reciprocity/`
   Runnable named wrapper with explicit inherited reputation and
   reputation-weighted positive routing.
- `group_selection/`
   Runnable named wrapper with explicit group membership and periodic
   between-group replacement.

## Minimal Run

Run from repository root:

```bash
./.conda/bin/python -m interaction_kernel.interaction_kernel_model
```

Default output log:

- `interaction_kernel/data/latest_run.json`

## Live Grid Viewer

To watch the trait field evolve cell-by-cell in real time, run from repository
root:

```bash
./.conda/bin/python -m interaction_kernel.interaction_kernel_pygame_ui
```

Viewer controls:

- `space`: play/pause
- `n`: single-step when paused
- `r`: reset run
- `up/down`: change FPS
- `esc`: quit

Note:

- `interaction_kernel/data/latest_run.json` stores summary history, not per-cell
   snapshots. Use the live viewer for cell-level dynamics.

Named mechanism viewers now also exist:

- `./.conda/bin/python -m kin_selection.kin_selection_pygame_ui`
- `./.conda/bin/python -m network_reciprocity.network_reciprocity_pygame_ui`
- `./.conda/bin/python -m direct_reciprocity.direct_reciprocity_pygame_ui`
- `./.conda/bin/python -m indirect_reciprocity.indirect_reciprocity_pygame_ui`
- `./.conda/bin/python -m group_selection.group_selection_pygame_ui`

## Comparison Utilities

Matched comparison for kin/network/direct:

- `./.conda/bin/python -m interaction_kernel.utils.compare_runnable_mechanisms`

Matched comparison for all five Nowak mechanism wrappers:

- `./.conda/bin/python -m interaction_kernel.utils.compare_all_nowak_mechanisms`

Unified launcher for all five live viewers:

- `./.conda/bin/python -m interaction_kernel.utils.launch_nowak_live_viewers`

Summary plotting utility (reads latest all-five summary CSV by default):

- `./.conda/bin/python -m interaction_kernel.utils.plot_nowak_comparison_summary`


## Implementing Kin Selection As A Special Case

Set:

- `positive_kernel_mode = "kin_weighted"`
- `B_minus_scale = 0.0`
- `negative_kernel_mode = "uniform"` (or `"none"`)
- `kin_weight_same_lineage > kin_weight_other_lineage`

This turns the abstract module into a kin-biased positive-return model without
changing core simulation code.

## Moran Rollback Note

On 2026-04-25, the module was intentionally simplified back to Moran-only
operation.

Stepwise impact:

1. Ecological update paths were removed from the main runtime.
2. The package now uses one update rule: local Moran replacement.
3. Ecological-only config keys were removed from the active interaction-kernel
   config.
4. Predator-prey-grass runtime files were removed from this package.
5. Module exports were reduced back to Moran interaction-kernel symbols.
6. Documentation now matches the Moran-only implementation and run path.
