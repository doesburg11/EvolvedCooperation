# Group Selection Module

This package is the group-selection wrapper over the shared
`moran_models.interaction_kernel.core` Moran engine.

Mechanism:

- each site has explicit group membership in one of `group_count` groups
- normal local Moran selection runs each step within the shared spatial world
- every `group_selection_interval` steps, the highest-fitness group overwrites
	the lowest-fitness group by copying its members
- this adds an explicit between-group selection channel on top of local
	individual selection

This is a first runnable group-selection implementation for the shared core.

## Package Contents

- `group_selection_model.py`
	Runnable group-selection model wrapper.
- `config/group_selection_config.py`
	Active configuration and source of truth for group-selection runs.

## Run

From the repo root:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.group_selection.group_selection_model
```

## Live Viewer

To inspect the group-selection run cell-by-cell:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.group_selection.group_selection_pygame_ui
```
