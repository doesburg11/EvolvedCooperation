# Direct Reciprocity

Three implementations of Nowak's direct reciprocity mechanism, progressing
from a continuous interaction-kernel model to discrete-strategy spatial and
well-mixed variants.

## The Mechanism

Direct reciprocity requires repeated encounters with the *same partner* and
memory of past interactions. A cooperator can punish a defector in the next
round and reward a cooperator. Cooperation is stable when the re-encounter
probability satisfies:

<p>w &gt; (T &minus; R) / (T &minus; P)</p>

This condition links the payoff structure of the Prisoner's Dilemma to the
minimum relationship length needed for reciprocity to work.

## Variants

| Property | `continuous` | `pair_game` | `well_mixed` |
| --- | --- | --- | --- |
| Strategy | Continuous cooperation trait `h` | Discrete: ALLC, ALLD, TFT, GTFT, WSLS | Same discrete strategies |
| Population | 2D spatial grid | 2D spatial grid | Flat list — no grid |
| Pairing | Local neighbors (fixed by grid) | Local neighbors (fixed by grid) | Uniformly random, configurable persistence |
| Mechanism tested | Direct reciprocity + network reciprocity | Direct reciprocity + network reciprocity | Direct reciprocity only |
| Key parameter | `memory_expression_gain`, `memory_decay` | `rounds_per_pair_per_step` | `partner_persistence_probability` |

### [`continuous/`](continuous/)

Wraps the shared interaction-kernel engine. Agents carry a continuous
cooperation trait `h` and pair-specific partner memory. Help is routed
preferentially back to neighbors that helped before. Cooperating lineages
reinforce each other through local Moran replacement.

### [`pair_game/`](pair_game/)

Standalone discrete-strategy model. Agents play repeated Prisoner's Dilemma
rounds with local grid neighbors using five named strategies. The spatial grid
introduces network reciprocity alongside direct reciprocity — cooperators can
cluster and shield each other from ALLD.

### [`well_mixed/`](well_mixed/)

Same discrete strategies, no grid. Agents are paired uniformly at random each
step, with a configurable probability of staying with the same partner across
steps (`partner_persistence_probability`). This isolates direct reciprocity
from network reciprocity: cooperation can only be sustained by pair memory and
repeated interaction.

## Run

```bash
# Continuous interaction-kernel model
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.continuous.direct_reciprocity_model

# Spatial pair-game model
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.pair_game.direct_reciprocity_pair_game_model

# Well-mixed model (pure direct reciprocity)
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_model
```
