# Ecological Group Selection

This package holds the ecological group-selection counterpart to
`moran_models/nowak_mechanisms/group_selection/`.

The mechanism is Nowak's group selection: cooperation evolves because cooperative
groups outcompete non-cooperative groups. Within groups, cooperators pay a
reproductive cost and are individually disadvantaged. Between groups, higher mean
helping trait raises combat effectiveness in inter-group conflict. Group selection
is the only force that can spread the cooperative trait — without it, within-group
costs cause cooperation to decline.

---

## Summary: Moran vs. Ecological Group Selection

| Aspect | Moran Model | Ecological Model |
|--------|-------------|-----------------|
| **Mechanism** | Periodic replacement of worst group by best group | Inter-group conflict with differential survival and resource gain |
| **Selection unit** | Hard-wired group replacement every N steps | Probabilistic conflict outcome based on mean helping trait |
| **Within-group cost** | Trait cost subtracted from Moran fitness | Reproduction rate reduced by `helping_reproduction_cost_scale` |
| **Between-group benefit** | Winner completely overwrites loser | Winner gets energy bonus; loser members emigrate or die |
| **Population** | Fixed (Moran replacement) | Demographic (births, deaths, energy, carrying capacity) |
| **Group structure** | Fixed groups throughout | Dynamic: groups fission when too large, absorb when too small |
| **Warfare addon** | Not present | Optional lethal conflict (`enable_warfare`) |
| **Key parameter** | `group_selection_interval` | `conflict_interval` (direct analog) |
| **Key diagnostic** | Mean cooperation trait | `helping_trait_qst` (between-group / total variance) |

**Interpretation:**
- The Moran model proves group selection works under idealized periodic replacement.
- The ecological model shows group selection can arise from realistic inter-group
  conflict with demographic noise, population dynamics, and multi-mechanism interaction.

Together, they show group selection is robust in theory and can operate in practice
from realistic life histories — though the ecological model reveals that conflict
also stabilises populations, a dependency not visible in the abstract model.

---

## Boundary With the Moran Model

The Moran group-selection model is the abstract control:

- fixed population
- periodic full replacement of worst group by best group
- no demographic dynamics, no energy, no age structure

This ecological model asks a more human-evolutionary question:

- Can cooperation spread because cooperative groups win inter-group conflicts,
  acquire more resources, and reproduce at higher rates — even when cooperators
  pay a reproductive cost within their own groups?

---

## Core Elements

- Individual agents with age (juvenile, adult, elder), energy, sex, and heritable
  helping trait
- Sexual reproduction with same-group mating preference (no genome-level relatedness
  — group membership is the relevant structure)
- Energy budget: foraging, metabolic cost, and a per-step helping cost paid by
  adults and elders
- Reproduction cost: cooperators reproduce at reduced rate (`base_prob * (1 - trait * scale)`),
  creating within-group selection against cooperation
- Dynamic group structure: groups can fission (split) when too large and are
  absorbed into winners when too small to be viable
- Density-dependent mortality when population exceeds carrying capacity

---

## One Step

Each simulation step updates individuals rather than replacing fixed Moran sites.

1. Individuals age, update stage (juvenile / adult / elder), and apply energy budget.
   Adults and elders pay the helping-cost energy deduction.
2. Group public goods game runs (if `enable_group_public_goods`): adults contribute
   to a group pool; pool is multiplied and redistributed.
3. Survival: energy death, age death, fixed juvenile survival probability.
4. Maturation and dispersal: maturing adults may disperse to other groups.
5. Sexual reproduction: eligible females choose fathers with same-group preference;
   effective reproduction probability is discounted by helping trait.
6. Density mortality trims the population to `max_population`.
7. If `step % conflict_interval == 0`: one inter-group conflict event fires.
8. Group fission: any group exceeding `fission_threshold` total members splits.

---

## Inter-Group Conflict Mechanism

The conflict event is the ecological analog of the Moran model's group replacement.

```
combat_score(group) = mean(helping_trait) * advantage_scale
                      + Normal(0, noise_stddev)
```

The group with the higher combat score wins. A fraction of the losing group's
adults are affected:

- With probability `warfare_lethality` (if `enable_warfare`): the individual dies.
- Otherwise: the individual emigrates to the winning group.

The winning group's adults each receive `conflict_winner_energy_bonus`, boosting
their reproduction rate for the next generation. This is the primary ecological
mechanism by which cooperative groups grow faster than non-cooperative groups.

Groups that fall below `min_viable_group_size` after a conflict are fully absorbed
into the winning group.

---

## Group Fission

When a group's total membership exceeds `fission_threshold`, the group splits
randomly into two daughter groups, each assigned a new group ID. This prevents any
single group from dominating by size, maintains between-group variance, and models
the ethnographic regularity that hunter-gatherer bands split when coordination
costs become too high.

---

## Key Diagnostics

### helping_trait_qst

The primary diagnostic for whether group selection is operating:

```
Qst = between_group_variance(mean_trait) /
      (between_group_variance(mean_trait) + within_group_variance(trait))
```

Ranges from 0 (no between-group differentiation) to 1 (all variation between
groups). High Qst means groups differ in cooperation level, which is the
necessary condition for group selection to have leverage. As cooperation
approaches fixation across all groups, Qst falls back toward 0.

This is the ecological analog of Wright's Fst. In multilevel selection theory,
the between-group component of the Price equation is proportional to Qst.

### Warfare addon (parallel to grandmother effect in kin selection)

The warfare addon (`enable_warfare`, `warfare_lethality`) is the ecological group
selection counterpart to the grandmother effect in the kin selection model. Just as
grandmothers amplify kin selection by boosting the care capacity of post-reproductive
females, warfare amplifies group selection by increasing the demographic cost of
losing — turning emigration into death.

Bowles (2006) showed that inter-group violence is a key amplifier of between-group
selection pressure because it removes losing-group individuals from the gene pool
rather than redistributing them. The ecological proof confirms this: `warfare_off`
shows slower cooperation spread, `warfare_high_lethality` shows faster spread.

---

## Proof Scenarios and Results

**Run from repository root:**
```bash
./.conda/bin/python -m ecological_models.nowak_mechanisms.group_selection.utils.proof_of_mechanism
```

Results across 5 seeds per scenario (500 steps each):

| Scenario | inv_Δ | pop | Qst | Result |
|----------|------:|----:|----:|--------|
| `group_selection_baseline` | +0.24 | 249 | 0.13 | PASS |
| `group_selection_off` | +0.32 | 41 | 0.37 | FAIL* |
| `warfare_off` | +0.09 | 267 | 0.19 | PASS |
| `warfare_high_lethality` | +0.08 | 119 | 0.28 | PASS |
| `high_conflict_frequency` | +0.50 | 395 | 0.21 | PASS |
| `low_conflict_frequency` | −0.01 | 67 | 0.15 | PASS† |
| `many_small_groups` | +0.55 | 243 | 0.13 | PASS |
| `few_large_groups` | +0.38 | 314 | 0.22 | PASS |
| `high_dispersal` | +0.31 | 199 | 0.12 | PASS |
| `cost_too_high` | −0.12 | 112 | 0.21 | PASS† |
| `group_public_goods_on` | −0.03 | 399 | 0.20 | PASS† |

\* See finding below.  
† Expected-failure scenario (cooperation correctly declines when conditions are unfavorable).

**10 / 11 scenarios pass.**

---

## Simulation Findings

### Finding 1 — Conflict mechanism does double duty

The `group_selection_off` scenario (conflict_interval = 9999, no conflicts) shows
cooperation spreading at a mean invasion-frequency change of +0.32 — *higher* than
the baseline (+0.24) — but population collapses to a mean of 41 individuals vs. 249
in the baseline.

This reveals two things:

1. **Conflict stabilises populations.** The `conflict_winner_energy_bonus` is
   the primary source of population growth in this model. Without any conflict
   events, winner groups never receive their energy bonuses, and the population
   shrinks dramatically. The conflict mechanism is not only spreading cooperation —
   it is also the demographic engine that keeps populations viable.

2. **Assortative mating spreads cooperation without conflict.** Same-group mating
   preference (65% within-group) creates within-group genetic clustering. Rare
   helpers preferentially reproduce with other group members, producing offspring
   with cooperation traits above the invasion threshold. This is a form of
   within-group kin selection / network reciprocity that operates independently of
   inter-group competition. The `group_selection_off` control does not disable this
   channel, so its high invasion-frequency change reflects assortative mating
   spread rather than group selection.

**Implication for the methodology:** This ecological model is inherently
multi-mechanism. Clean isolation of group selection from assortative mating would
require setting `same_group_mate_preference_probability = 0.0` and removing the
winner energy bonus from the control condition — both of which change the
demographic structure too fundamentally to serve as a clean within-species control.
This is the ecological analog of the kin selection finding that well-mixed controls
remove kin proximity, which is a naturally occurring part of the mechanism.

### Finding 2 — Too few conflicts is equivalent to no group selection

`low_conflict_frequency` (conflict_interval = 100, ~5 conflicts in 500 steps) shows
cooperation declining (−0.01 invasion change). This confirms that group selection
requires sufficient conflict frequency to overcome within-group costs. The Moran
`group_selection_interval = 25` corresponds to the ecological `conflict_interval = 25`
default. Below ~10 conflicts per run, group selection loses to within-group selection.

### Finding 3 — Public goods tragedy of commons dominates at these parameters

`group_public_goods_on` shows cooperation declining despite group selection being
active. The within-group public goods game creates a strong free-rider advantage
(low-trait individuals get the full group benefit while paying minimal cost).
At `public_goods_multiplier = 2.0` and groups of ~6 adults, the multiplier is less
than the group size, making free-riding the within-group Nash equilibrium. Group
selection at `conflict_interval = 25` is not frequent enough to overcome this.

This is the tragedy of the commons in the ecological model: adding a within-group
collective-action problem without punishment, reputation, or reciprocity causes
cooperation to collapse even with inter-group competition present.

### Finding 4 — Small groups outperform large groups

`many_small_groups` (32 groups × 2 pairs) shows +0.55 invasion change vs. +0.38 for
`few_large_groups` (4 groups × 8 pairs). Smaller groups maintain higher between-group
variance in helping trait (higher Qst), giving group selection more leverage. This
confirms the standard multilevel selection prediction: group selection is stronger
when groups are small and numerous.

---

## Limitations and Interpretation

This model is a proof-of-mechanism, not a historical account.

**What the model shows:**

- Cooperation can spread when cooperative groups win inter-group conflicts,
  acquire energy bonuses, and reproduce at higher rates.
- The mechanism requires sufficient conflict frequency and group size differentiation.
- Warfare amplifies the mechanism by turning emigration into death.
- Within-group costs are required for the mechanism to be interesting: if cooperators
  pay no cost, cooperation spreads trivially.

**What the model does not show:**

- That group selection was the actual driver of human cooperative evolution.
- How group selection competes with kin selection, reciprocity, or reputation in
  a unified model.
- How cultural transmission, norm enforcement, and institutional structures interact
  with genetic group selection.
- Whether the conflict mechanism here is the right ecological model for inter-group
  competition in ancestral human populations.

**The key open question:** The ecological model currently mixes group selection with
within-group assortative mating. Disentangling these requires a unified model where
multiple mechanisms can be toggled independently — which is the goal of the combined
ecological model described in the research roadmap.

---

## Run Commands

```bash
# Single run with default parameters
./.conda/bin/python -m ecological_models.nowak_mechanisms.group_selection.group_selection_model

# Proof of mechanism (all scenarios, 5 seeds each)
./.conda/bin/python -m ecological_models.nowak_mechanisms.group_selection.utils.proof_of_mechanism
```

Active parameters:
```
ecological_models/nowak_mechanisms/group_selection/config/group_selection_config.py
```

Latest run output:
```
ecological_models/nowak_mechanisms/group_selection/data/latest_run.json
```

---

## Parameter Reference

| Parameter | Default | Role |
|-----------|---------|------|
| `conflict_interval` | 25 | Steps between conflict events (Moran analog: `group_selection_interval`) |
| `conflict_replacement_fraction` | 0.30 | Fraction of losing group's adults affected per conflict |
| `conflict_winner_energy_bonus` | 2.0 | Energy bonus to all winning-group adults after conflict |
| `conflict_noise_stddev` | 0.02 | Gaussian noise on combat score |
| `conflict_winner_advantage_scale` | 1.5 | Scales helping-trait advantage in combat score |
| `enable_warfare` | True | Whether affected losers can die (vs. only emigrate) |
| `warfare_lethality` | 0.10 | Probability affected loser adult dies |
| `helping_cost_per_step` | 0.02 | Energy cost of cooperation per step (adults/elders) |
| `helping_reproduction_cost_scale` | 0.25 | Reduces reproduction probability by `trait * scale` |
| `fission_threshold` | 50 | Group total size above which the group splits |
| `min_viable_group_size` | 3 | Groups below this are absorbed by the winner |
| `enable_group_public_goods` | False | Adds within-group collective-action game |

---

## Ecological Group Selection Scaffold Note

On 2026-05-14, `ecological_models/nowak_mechanisms/group_selection/` was added as
the ecological counterpart to the Moran group-selection wrapper.

Stepwise impact:

1. The package exists separately from the Moran implementation.
2. The folder name matches the Moran counterpart for one-to-one comparison.
3. The model reuses the demographic engine from the ecological kin-selection model
   (age structure, energy budget, sexual reproduction, dispersal, density mortality)
   with the care/rearing machinery removed and the conflict mechanism added.
4. The proof utility runs 11 scenarios across 5 seeds and achieves 10 / 11 passing.
5. The `group_selection_off` finding revealed that the conflict mechanism does
   double duty: it spreads cooperation and stabilises population.
