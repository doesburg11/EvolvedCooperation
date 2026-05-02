# Direct Reciprocity Pair Game

This package implements a pure direct-reciprocity Moran model with explicit
repeated pair encounters.

It is a sibling of
[`moran_models/nowak_mechanisms/direct_reciprocity/`](../direct_reciprocity/).
The existing package keeps the continuous partner-memory routing model. This
package uses discrete strategy rules and binary repeated Prisoner's Dilemma
actions.

Stepwise impact:

1. The package import path is
   `moran_models.nowak_mechanisms.direct_reciprocity.pair_game`.
2. The model evolves discrete strategy IDs rather than a continuous help trait.
3. Local neighboring pairs play repeated Prisoner's Dilemma rounds before Moran
   replacement.
4. Each ordered pair stores partner-specific action and payoff memory.
5. Moran replacement copies successful local strategies, with mutation switching
   strategy type.
6. The live viewer colors cells by strategy and charts action-level cooperation.
7. The proof utility runs default, rare-cluster, no-memory, and one-round
   ablation scenarios.

## State

Each site `i` stores:

- `s_i`: strategy type
- `lineage_i`: inherited identity label
- `last_action[i, j]`: previous action by site `i` toward neighbor `j`
- `last_payoff[i, j]`: previous payoff received by site `i` against neighbor `j`

Implemented strategies:

## Cooperation Rate vs Reciprocal Strategy Frequency

**Cooperation rate** is the fraction of all actions in the current step that are cooperation actions (`C`).

Formula:

   cooperation_rate = number_of_C_actions / total_number_of_actions

Where:
- `C` means cooperate, `D` means defect.
- Every neighboring pair produces two actions per round (from `i` to `j` and from `j` to `i`).
- With `rounds_per_pair_per_step=3`, each neighboring pair contributes 6 actions per Moran step.

For example, if 1000 actions happen in a step and 850 are cooperation actions:

   cooperation_rate = 850 / 1000 = 0.85

In code, this is computed in [direct_reciprocity_pair_game_model.py](direct_reciprocity_pair_game_model.py):

```python
cooperation_count += int(action_i == COOPERATE) + int(action_j == COOPERATE)
action_count += 2
cooperation_rate = cooperation_count / max(1, action_count)
```

**Important distinction:**

- **Cooperation rate** = what agents actually do this step (behavioral output).
- **Reciprocal strategy frequency** = how many agents carry strategies like `TFT`, `GTFT`, or `WSLS` (genotype/strategy distribution).

A population can have many reciprocal strategies but low cooperation if they are surrounded by defectors and respond by defecting.

| Strategy | Rule |
| --- | --- |
| `ALLC` | Always cooperate. |
| `ALLD` | Always defect. |
| `TFT` | Cooperate first, then copy the partner's previous action. |
| `GTFT` | Tit-for-tat with probabilistic forgiveness after partner defection. |
| `WSLS` | Win-stay lose-shift: repeat the previous action if payoff met aspiration; otherwise switch. |

Actions:

- `C`: cooperate
- `D`: defect

## Payoff Game

Each neighboring pair plays the Prisoner's Dilemma.

| Actor / Partner | Partner C | Partner D |
| --- | --- | --- |
| Actor C | `R` | `S` |
| Actor D | `T` | `P` |

The default config uses:

- `T = temptation_payoff = 1.7`
- `R = reward_payoff = 1.0`
- `P = punishment_payoff = 0.0`
- `S = sucker_payoff = -0.5`

This satisfies:

<p>T &gt; R &gt; P &gt; S</p>

This ordering is the definition of the Prisoner's Dilemma. Defecting against a cooperator pays more than mutual cooperation (`T > R`), so defection is individually tempting. Mutual cooperation pays more than mutual defection (`R > P`), so cooperation is collectively better. Mutual defection still beats being exploited (`P > S`), making defection the safe individual choice. The dilemma is that individually rational agents defect even though both would be better off cooperating.

The default run uses `rounds_per_pair_per_step=3`. With only one round per
pair, defectors usually dominate because reciprocal strategies do not get
enough repeated interaction to punish exploitation and recover mutual
cooperation.

## Moran Update

At each step:

1. Each local neighboring pair plays `rounds_per_pair_per_step` repeated PD
   rounds.
2. Strategy rules choose binary actions from pair-specific memory.
3. Pair payoffs accumulate into site payoff.
4. Fitness is computed as:

   <p>W_i = base_fitness + payoff_i</p>

5. Each site samples a parent from its local replacement neighborhood with
   softmax fitness selection.
6. The offspring inherits the parent's strategy and lineage.
7. With probability `mutation_rate`, the offspring switches to another strategy.
8. Pair memory is reset for replaced or mutated sites; persistent sites keep
   memory with other persistent sites.

## Emergence Criterion

The proof utility treats cooperation as emerging when all three conditions hold:

- final action cooperation rate is at least `0.60`
- final reciprocal-strategy frequency is at least `0.50`
- final `ALLD` frequency is at most `0.25`

The most important mechanism checks are:

1. `rare_cluster_start`: reciprocal strategies begin as a 5% spatial cluster
   and should spread.
2. `no_memory_ablation`: the same rare cluster starts without partner memory
   and should collapse.
3. `one_round_ablation`: the same rare cluster starts with only one round per
   pair and should collapse.

This is empirical proof-of-mechanism, not a mathematical theorem.

## Files

- `direct_reciprocity_pair_game_model.py`: core pair-game Moran model.
- `direct_reciprocity_pair_game_pygame_ui.py`: strategy-colored live viewer.
- `config/direct_reciprocity_pair_game_config.py`: active config.
- `utils/proof_of_mechanism.py`: replicate checks and ablations.

## Run

From the repository root:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.pair_game.direct_reciprocity_pair_game_model
```

Live viewer:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.pair_game.direct_reciprocity_pair_game_pygame_ui
```

Proof utility:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.pair_game.utils.proof_of_mechanism
```
