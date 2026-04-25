# Interaction Kernel

`interaction_kernel/` is a general, reusable simulation engine for models that
separate:

1. action or trait-dependent produced effects,
2. routing through explicit positive and negative kernels,
3. fitness score formation,
4. selection and inheritance.

This package is designed as an abstract base module in `EvolvedCooperation` so
named mechanisms (for example kin selection, network reciprocity, or mixed
help-harm settings) can be implemented as configurations or thin wrappers.

## Why This Module Exists

The repo already contains named website-facing mechanisms and a retained-kernel
generalization. This package adds a broader interaction core with explicit
positive and negative channels and pluggable kernel and selection behavior.

The architectural goal is:

> build one canonical core once, then instantiate mechanism-specific special
> cases without duplicating simulation logic.

## Interaction Kernel Rename Note

On 2026-04-25, this package was renamed from `interaction_module/` to
`interaction_kernel/`.

Stepwise impact:

1. The Python package now lives at `interaction_kernel/`.
2. The main runtime entry point is now
   `interaction_kernel/interaction_kernel_model.py`.
3. The active config file is now
   `interaction_kernel/config/interaction_kernel_config.py`.
4. The default JSON log path is now
   `interaction_kernel/data/latest_run.json`.
5. The module-run command is now:

```bash
./.conda/bin/python -m interaction_kernel.interaction_kernel_model
```

The rename keeps the mechanism intent explicit: this package is a reusable
interaction-kernel engine, not a generic module placeholder.

## Current Core Dynamics

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

- `interaction_kernel_model.py`: main simulation loop and runtime entry point
- `kernels.py`: kernel construction helpers
- `selection.py`: local selection/inheritance update
- `metrics.py`: per-step summary metrics
- `config/interaction_kernel_config.py`: active runtime config

## Minimal Run

Run from repository root:

```bash
./.conda/bin/python -m interaction_kernel.interaction_kernel_model
```

Default output log:

- `interaction_kernel/data/latest_run.json`

## Implementing Kin Selection As A Special Case

Set:

- `positive_kernel_mode = "kin_weighted"`
- `B_minus_scale = 0.0`
- `negative_kernel_mode = "uniform"` (or `"none"`)
- `kin_weight_same_lineage > kin_weight_other_lineage`

This turns the abstract module into a kin-biased positive-return model without
changing core simulation code.

## Stepwise Build Summary

1. Added a standalone `interaction_kernel/` package as a reusable core.
2. Implemented explicit produced, routed, and selected stages in one runtime.
3. Added modular kernel construction in `kernels.py`.
4. Added local neighborhood selection in `selection.py`.
5. Added central runtime config and default JSON logging.
6. Documented how to instantiate kin selection as a parameterized special case.
