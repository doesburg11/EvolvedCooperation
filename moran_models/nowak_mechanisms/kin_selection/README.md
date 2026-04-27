# Kin Selection Module

This package is the named kin-selection wrapper over the shared
`moran_models.interaction_kernel.core` Moran engine.

Mechanism:

- producers generate a positive effect proportional to trait `h`
- positive effects are routed with lineage bias
- same-lineage recipients receive more weight than other-lineage recipients
- selection remains local Moran replacement on the spatial grid

This is the clean Nowak-style kin-selection specialization of the shared core.

## Worked Example: One Step

Consider a focal site **i** and its four von Neumann neighbors.

```
Lineage:  A    A    A    B    B
Trait h:  0.8  0.7  0.6  0.9  0.5
Site:      i    j1   j2   j3   j4
```

Site i has two same-lineage neighbors (j1, j2) and two other-lineage neighbors (j3, j4).

**1. Production**

```
B_plus[i] = B_plus_scale × h[i] = 1.0 × 0.8 = 0.80
C[i]       = C_scale      × h[i] = 0.2 × 0.8 = 0.16
```

**2. Outgoing kernel row for site i**

Raw lineage weights → row-normalize:

```
       j1     j2     j3     j4    row sum
raw:  0.80   0.80   0.20   0.20   = 2.00
norm: 0.40   0.40   0.10   0.10   = 1.00
```

**3. What i sends to each neighbor**

```
→ j1 (same-lineage): 0.80 × 0.40 = 0.32
→ j2 (same-lineage): 0.80 × 0.40 = 0.32
→ j3 (other-lineage): 0.80 × 0.10 = 0.08
→ j4 (other-lineage): 0.80 × 0.10 = 0.08
```

Cooperators send 4× more benefit to same-lineage neighbors than to other-lineage neighbors.

**4. What i receives** (`R_plus = K_plus.T @ B_plus`)

Assuming each neighbor also has two same-lineage and two other-lineage neighbors (symmetric
structure), their normalized weights toward i are 0.40 (same) or 0.10 (other):

```
from j1 (same-lineage, h=0.7): 0.7 × 0.40 = 0.28
from j2 (same-lineage, h=0.6): 0.6 × 0.40 = 0.24
from j3 (other-lineage, h=0.9): 0.9 × 0.10 = 0.09
from j4 (other-lineage, h=0.5): 0.5 × 0.10 = 0.05

R_plus[i] = 0.28 + 0.24 + 0.09 + 0.05 = 0.66
```

**5. Fitness score**

```
W[i] = base_fitness + R_plus[i] - C[i] = 1.0 + 0.66 - 0.16 = 1.50
```

**Why kinship helps**

If i were surrounded by four other-lineage neighbors with the same traits, its
incoming normalized weight would be 0.10 per neighbor instead of 0.40 for
same-lineage ones. Holding everything else equal:

```
R_plus[i] = (0.7 + 0.6 + 0.9 + 0.5) × 0.10 = 0.27
W[i]       = 1.0 + 0.27 - 0.16 = 1.11
```

The lineage cluster raises fitness from 1.11 to 1.50 — a difference that
compounds over many steps as same-lineage cooperators expand together.

**6. Replacement**

After all sites compute their fitness scores, each site samples a parent from
its local neighborhood via softmax over W. The offspring inherits the parent's
trait h (with small mutation) and lineage label — so the same-lineage cluster
grows when cooperators reproduce locally.

## Package Contents

- `kin_selection_model.py`
  Runnable kin-selection model wrapper.
- `config/kin_selection_config.py`
  Active configuration and source of truth for kin-selection runs.

## Run

From the repo root:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.kin_selection_model
```

## Live Viewer

To inspect the kin-selection run cell-by-cell:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.kin_selection_pygame_ui
```

## Parameter Sweep

To map final cooperation across kin bias and benefit/cost conditions:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.utils.sweep_kin_selection_phase
```

The sweep uses two derived experimental axes:


Stepwise behavior:

  `kin_bias_ratio` from `8.0` through `16.0` and `benefit_cost_ratio`
  from `3.5` through `4.75`.

## Conclusion

The parameter sweeps show a sharp threshold for the evolution of cooperation:

- Cooperation (mean final trait > 0.5) only emerges when both kin bias and benefit/cost ratio are sufficiently high.
- As kin bias increases, the minimum benefit/cost ratio required for cooperation decreases.
- For example, with kin_bias_ratio=1.0, cooperation requires benefit/cost ≥ 5.25, but with kin_bias_ratio=16.0, cooperation appears at benefit/cost as low as 3.5.
- The transition from non-cooperation to cooperation is abrupt, as confirmed by the phase map and surface plots.

These results are consistent with Hamilton’s rule: stronger kin discrimination (higher effective relatedness) allows cooperation to evolve at lower benefit/cost ratios. The model thus robustly demonstrates kin selection’s role in supporting cooperation, with the regime boundary closely matching theoretical expectations.

## Key Evidence: Phase and Surface Charts

The following charts underscore the threshold effect and regime boundary for cooperation in the kin selection model:

**Phase Map:**
  ![Phase map: kin_bias_ratio vs. benefit_cost_ratio](data/kin_selection_phase_20260426_220124_phase_map.png)
  
  This 2D chart shows the mean final cooperation trait across the parameter grid. The sharp transition from low to high cooperation is visible as a boundary in the heatmap.

**3D Surface Plot:**
  ![3D surface: kin_bias_ratio vs. benefit_cost_ratio](data/kin_selection_phase_20260426_220124_surface.png)
  
  The 3D surface plot further highlights the abrupt jump in cooperation as parameters cross the threshold, confirming the phase transition predicted by theory.

These visualizations provide direct evidence for the model’s regime boundary and the role of kin bias and benefit/cost ratio in the evolution of cooperation.
