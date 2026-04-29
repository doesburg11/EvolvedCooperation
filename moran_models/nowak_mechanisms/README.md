# Nowak Mechanisms

This directory contains five named Moran-process packages, one for each of the
five mechanisms for the evolution of cooperation identified in Nowak (2006).
Each package is a thin wrapper over the shared
`moran_models.interaction_kernel.core` engine.

## Shared Engine

All five mechanisms run on the same Moran update loop:

1. Each site produces `B_plus = B_plus_scale * h` from its cooperation trait `h`.
2. Positive effects are routed to neighbors through a mechanism-specific kernel.
3. Each site receives routed benefit `R_plus` and pays private cost `C_scale * h`.
4. Fitness score: `W = base_fitness + R_plus - C`.
5. Local replacement: each site samples a parent from its neighborhood via local
   softmax fitness; trait and lineage are inherited with mutation.

What differs across mechanisms is step 2 — the routing kernel and any
additional per-site state (memory, reputation, group membership) that modulates it.

See `moran_models/interaction_kernel/README.md` for the full engine description.

## The Five Mechanisms

### Kin Selection

**Website page:** https://humanbehaviorpatterns.org/evolved-cooperation/kin-selection

Positive benefit is routed with a lineage bias: same-lineage neighbors receive
more weight than other-lineage neighbors. Cooperators that reproduce pass their
lineage label to offspring, so cooperator clusters accumulate same-lineage
neighbors over time, progressively recirculating more benefit back to cooperators.

This operationalises Hamilton's rule $rB > C$ by setting effective relatedness
through `kin_weight_same_lineage` and `kin_weight_other_lineage`.

Key config:

```python
"positive_kernel_mode": "kin_weighted",
"kin_weight_same_lineage": 0.8,
"kin_weight_other_lineage": 0.2,
"C_scale": 0.2,
```

Run: `./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.kin_selection_model`

---

### Direct Reciprocity

**Website page:** https://humanbehaviorpatterns.org/evolved-cooperation/direct-reciprocity

Each site carries pair-specific memory of which neighboring sites helped it.
Future help is routed preferentially back toward neighbors that helped before:
if site `j` helped site `i`, then `i` is more likely to route help back to `j`
in later steps. After local Moran replacement, offspring inherit the parent's
partner-memory row, so reciprocal local lineages can persist and spread.

Key config:

```python
"positive_kernel_mode": "uniform",
"direct_reciprocity_mode": "partner_memory",
"direct_reciprocity_cost_mode": "expressed",
"include_self_in_neighborhood": True,
"direct_reciprocity_include_self_interaction": False,
"B_plus_scale": 8.0,
"memory_decay": 0.35,
"memory_baseline_expression": 0.35,
"memory_expression_gain": 0.85,
"C_scale": 0.2,
```

Run: `./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.direct_reciprocity_model`

---

### Indirect Reciprocity

**Website page:** https://humanbehaviorpatterns.org/evolved-cooperation/indirect-reciprocity

Each site carries a public reputation score. The positive routing kernel is
biased toward higher-reputation recipients so agents with a history of helping
receive more benefit. Reputation updates after each step from observed helping
output, sustaining cooperation through a reputation channel rather than direct
encounter memory.

Key config:

```python
"positive_kernel_mode": "reputation_weighted",
"reputation_default": 0.5,
"reputation_observation_weight": 0.35,
"reputation_kernel_bias": 0.10,
"C_scale": 0.2,
```

Run: `./.conda/bin/python -m moran_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_model`

---

### Network Reciprocity

**Website page:** https://humanbehaviorpatterns.org/evolved-cooperation/network-reciprocity

Positive benefit is routed uniformly over local grid neighbors with no
additional bias. The mechanism relies entirely on spatial structure: the local
neighborhood restricts who receives benefit and who competes for replacement.
Cooperator clusters can maintain higher local average fitness than their
surroundings and expand, without any memory or lineage bias.

Key config:

```python
"positive_kernel_mode": "uniform",
"C_scale": 0.2,
```

Run: `./.conda/bin/python -m moran_models.nowak_mechanisms.network_reciprocity.network_reciprocity_model`

---

### Group Selection

**Website page:** https://humanbehaviorpatterns.org/evolved-cooperation/group-selection

Sites are partitioned into a fixed number of groups. Individual Moran
replacement runs each step. Every `group_selection_interval` steps a
between-group event fires: the highest-mean-fitness group is copied into the
lowest-mean-fitness group. This adds an explicit second level of selection on
top of individual competition.

Key config:

```python
"group_count": 8,
"group_selection_interval": 25,
"group_selection_mode": "copy_best_group_into_worst_group",
"C_scale": 0.2,
```

Run: `./.conda/bin/python -m moran_models.nowak_mechanisms.group_selection.group_selection_model`

---

## Live Viewers

Each mechanism has a pygame live viewer:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.kin_selection.kin_selection_pygame_ui
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.direct_reciprocity_pygame_ui
./.conda/bin/python -m moran_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_pygame_ui
./.conda/bin/python -m moran_models.nowak_mechanisms.network_reciprocity.network_reciprocity_pygame_ui
./.conda/bin/python -m moran_models.nowak_mechanisms.group_selection.group_selection_pygame_ui
```

To launch all five viewers in sequence:

```bash
./.conda/bin/python -m moran_models.interaction_kernel.utils.launch_nowak_live_viewers
```

## Comparison Utilities

Run all five mechanisms under matched parameters and collect summary statistics:

```bash
./.conda/bin/python -m moran_models.interaction_kernel.utils.compare_all_nowak_mechanisms
```

Plot a winner map and delta panels from the latest comparison run:

```bash
./.conda/bin/python -m moran_models.interaction_kernel.utils.plot_nowak_comparison_summary
```

## Beyond These Five

Nowak's taxonomy is a useful compact framework but not an exhaustive list.
Important cooperation mechanisms outside the five include:

- **Partner choice**: agents preferentially interact with cooperative partners and abandon poor ones.
- **Partner control**: agents alter partner incentives through sanctions, punishment, or exclusion.
- **Byproduct mutualism**: an action benefits others because it directly benefits the actor at the same time.
- **Policing**: third parties suppress selfish behavior or stabilize collective rules.
- **Pseudoreciprocity**: an actor benefits another because a more productive partner later improves the actor's own payoff.
- **Greenbeard effects**: a recognizable trait marks cooperators and directs help toward others carrying the same marker.
- **Niche construction and ecological feedback**: cooperative behavior changes the environment, which then feeds back on selection.
- **Institutional enforcement**: norms, monitoring, and punishment stabilize cooperation at social scales.
- **General assortment**: cooperators interact with cooperators more often than random mixing predicts, whether caused by kinship, space, partner choice, tags, ecology, or institutions.

These mechanisms can overlap and combine. The shared condition across all of
them mirrors the repo-level feedback framing: cooperation spreads when enough
of the value it creates returns to cooperators or copies of the cooperative
rule to outweigh the private cost.

## References

- Nowak, M. A. (2006). *Five rules for the evolution of cooperation*. *Science*, 314(5805), 1560–1563. https://doi.org/10.1126/science.1133755
- Hamilton, W. D. (1964). *The genetical evolution of social behaviour. I*. *Journal of Theoretical Biology*, 7(1), 1–16. https://doi.org/10.1016/0022-5193(64)90038-4
- Axelrod, R., & Hamilton, W. D. (1981). *The evolution of cooperation*. *Science*, 211(4489), 1390–1396. https://doi.org/10.1126/science.7466396
- Nowak, M. A., & Sigmund, K. (1998). *Evolution of indirect reciprocity by image scoring*. *Nature*, 393, 573–577. https://doi.org/10.1038/31225
- Ohtsuki, H., Hauert, C., Lieberman, E., & Nowak, M. A. (2006). *A simple rule for the evolution of cooperation on graphs and social networks*. *Nature*, 441, 502–505. https://doi.org/10.1038/nature04605
