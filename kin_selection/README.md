# Kin Selection Module

This package is the named kin-selection wrapper over the shared
`interaction_kernel.core` Moran engine.

Mechanism:

- producers generate a positive effect proportional to trait `h`
- positive effects are routed with lineage bias
- same-lineage recipients receive more weight than other-lineage recipients
- selection remains local Moran replacement on the spatial grid

This is the clean Nowak-style kin-selection specialization of the shared core.

## Package Contents

- `kin_selection_model.py`
  Runnable kin-selection model wrapper.
- `config/kin_selection_config.py`
  Active configuration and source of truth for kin-selection runs.

## Run

From the repo root:

```bash
./.conda/bin/python -m kin_selection.kin_selection_model
```

## Live Viewer

To inspect the kin-selection run cell-by-cell:

```bash
./.conda/bin/python -m kin_selection.kin_selection_pygame_ui
```

## Parameter Sweep

To map final cooperation across kin bias and benefit/cost conditions:

```bash
./.conda/bin/python -m kin_selection.utils.sweep_kin_selection_phase
```

The sweep uses two derived experimental axes:

- `kin_bias_ratio = kin_weight_same_lineage / kin_weight_other_lineage`
- `benefit_cost_ratio = B_plus_scale / C_scale`

Stepwise behavior:

- `kin_weight_other_lineage` is fixed at `1.0`.
- `kin_weight_same_lineage` is set to the selected `kin_bias_ratio`.
- `C_scale` is fixed at `0.2`.
- `B_plus_scale` is set to `benefit_cost_ratio * C_scale`.
- Each cell records mean cooperation after `1000` simulation steps.
- The active sweep grid is focused around the noisy high-bias transition:
  `kin_bias_ratio` from `8.0` through `16.0` and `benefit_cost_ratio`
  from `3.5` through `4.75`.
- Each cell is averaged across `10` replicates.
- Outputs are written under `kin_selection/data/` as replicate CSV,
  aggregate CSV, TXT summary, 2D phase chart, and 3D surface chart.
