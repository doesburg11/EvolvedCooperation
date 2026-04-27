# Indirect Reciprocity Module

This package is the indirect-reciprocity wrapper over the shared
`moran_models.interaction_kernel.core` Moran engine.

Mechanism:

- agents carry an inherited public reputation state in `[0, 1]`
- cooperative action raises reputation through an observer-style update
- positive routing weights are biased toward recipients with stronger
	reputation
- local Moran replacement inherits both trait and reputation state

This is a first runnable indirect-reciprocity implementation for the shared
core.

## Package Contents

- `indirect_reciprocity_model.py`
	Runnable indirect-reciprocity model wrapper.
- `config/indirect_reciprocity_config.py`
	Active configuration and source of truth for indirect-reciprocity runs.

## Run

From the repo root:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_model
```

## Live Viewer

To inspect the indirect-reciprocity run cell-by-cell:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_pygame_ui
```
