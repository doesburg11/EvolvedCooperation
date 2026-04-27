# Network Reciprocity Module

This package is the named network-reciprocity wrapper over the shared
`moran_models.interaction_kernel.core` Moran engine.

Mechanism:

- agents interact and compete locally on the same sparse spatial graph
- positive returns are routed uniformly across each site's allowed neighbors
- cooperation can persist because local clusters support one another under
  repeated local replacement

This is the clean network-reciprocity specialization of the shared core.

## Package Contents

- `network_reciprocity_model.py`
  Runnable network-reciprocity model wrapper.
- `config/network_reciprocity_config.py`
  Active configuration and source of truth for network-reciprocity runs.

## Run

From the repo root:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.network_reciprocity.network_reciprocity_model
```

## Live Viewer

To inspect the network-reciprocity run cell-by-cell:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.network_reciprocity.network_reciprocity_pygame_ui
```