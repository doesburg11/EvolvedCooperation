# Direct Reciprocity Module

This package is the direct-reciprocity wrapper over the shared
`interaction_kernel.core` Moran engine.

Mechanism:

- agents carry an evolving cooperation trait `h`
- each site also stores a direct-reciprocity memory of recently received help
- agents that were helped more in the recent past express more cooperation in
	the next step
- that memory state is carried forward through local Moran replacement, so
	reciprocating local lineages can reinforce one another over time

This is a first runnable direct-reciprocity implementation for the shared core.
It uses persistent received-help memory rather than a full explicit partner log,
which keeps the mechanism compatible with the current synchronous local Moran
update.

## Package Contents

- `direct_reciprocity_model.py`
	Runnable direct-reciprocity model wrapper.
- `config/direct_reciprocity_config.py`
	Active configuration and source of truth for direct-reciprocity runs.

## Run

From the repo root:

```bash
./.conda/bin/python -m direct_reciprocity.direct_reciprocity_model
```

## Live Viewer

To inspect the direct-reciprocity run cell-by-cell:

```bash
./.conda/bin/python -m direct_reciprocity.direct_reciprocity_pygame_ui
```