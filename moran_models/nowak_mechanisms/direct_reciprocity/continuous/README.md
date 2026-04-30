# Direct Reciprocity Module

This package is the direct-reciprocity wrapper over the shared
`moran_models.interaction_kernel.core` Moran engine.

Mechanism:

- agents carry an evolving cooperation trait `h`
- each site stores pair-specific memory of which neighboring sites helped it
- future positive routing is biased back toward the remembered helper
- that partner-memory state is carried forward through local Moran replacement,
  so reciprocating local lineages can reinforce one another over time

## Pair-Specific Memory Note

On 2026-04-28, direct reciprocity was changed from general received-help memory
to pair-specific local partner memory.

Stepwise impact:

1. The default mode is now `direct_reciprocity_mode="partner_memory"`.
2. The model stores `partner_memory[i, j]`, meaning how strongly site `i`
   remembers being helped by site `j`.
3. Help from `i` to `j` is routed by the expression
   `memory_baseline_expression + memory_expression_gain * partner_memory[i, j]`,
   clipped to `[0, 1]`.
4. The positive routing matrix is not row-normalized to full output. Its row
   sum is the expressed fraction of the producer's possible help.
5. With `direct_reciprocity_cost_mode="expressed"`, private cost is paid on
   expressed help rather than raw cooperation capacity.
6. The direct-reciprocity config keeps self available for Moran replacement
   but excludes self from direct-reciprocity help routing, so memory and help
   operate between neighboring sites rather than through self-help.
7. The older `received_help_memory` mode remains available if the config
   explicitly selects it, but it is no longer the default direct-reciprocity
   mechanism.
8. The default benefit scale is now `B_plus_scale=8.0`, because partner help is
   divided across local neighbors; the previous `B_plus_scale=1.0` setting was
   too weak for the low-start direct-reciprocity demonstration.

Core variables:

- `h_i`: inherited cooperation capacity at site `i`
- `M_ij`: `partner_memory[i, j]`, site `i`'s memory that site `j` helped it
- `e_ij`: expressed help fraction from `i` to `j`
- `B_i`: maximum positive output available from site `i`
- `K_ij`: positive routing weight from `i` to `j`
- `C_i`: private cooperation cost paid by site `i`

Implemented pair-memory equations:

<p>e<sub>ij</sub> = clip(baseline + gain &times; M<sub>ij</sub>, 0, 1)</p>

<p>K<sub>ij</sub> = e<sub>ij</sub> &divide; n<sub>i</sub> for neighboring sites j</p>

<p>B<sub>i</sub> = B<sub>plus</sub> &times; h<sub>i</sub></p>

<p>C<sub>i</sub> = C &times; h<sub>i</sub> &times; sum<sub>j</sub>K<sub>ij</sub></p>

<p>M'<sub>ij</sub> = decay &times; M<sub>ij</sub> + (1 - decay) &times; help_received_from_j</p>

Where:

- `baseline` is `memory_baseline_expression`
- `gain` is `memory_expression_gain`
- `n_i` is the number of neighbors available to site `i`
- `B_plus` is `B_plus_scale`
- `C` is `C_scale`
- `help_received_from_j` is the realized help sent from `j` to `i`,
  normalized by the maximum per-neighbor help scale

## Package Contents

- `direct_reciprocity_model.py`
	Runnable direct-reciprocity model wrapper.
- `config/direct_reciprocity_config.py`
	Active configuration and source of truth for direct-reciprocity runs.

## Run

From the repo root:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.direct_reciprocity_model
```

## Live Viewer

To inspect the direct-reciprocity run cell-by-cell:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.direct_reciprocity_pygame_ui
```
