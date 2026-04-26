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