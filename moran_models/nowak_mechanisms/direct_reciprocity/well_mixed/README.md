# Direct Reciprocity Well-Mixed

This package implements a well-mixed Moran model designed to isolate
**direct reciprocity** from **network reciprocity** — two of Nowak's five
mechanisms that Nowak treats as distinct.

It is a sibling of
[`moran_models/nowak_mechanisms/direct_reciprocity/pair_game/`](../pair_game/).
That package uses a 2D spatial grid, which conflates both mechanisms. This
package removes the grid entirely.

## Nowak's Distinction: Direct vs Network Reciprocity

Nowak separates these on two independent axes:

- **Direct reciprocity**: the *same two individuals* meet repeatedly over time.
  Memory of past interactions lets cooperators punish defectors in future
  rounds. Cooperation is stable when the re-encounter probability `w` is high
  enough — specifically when `w > (T − R) / (T − P)`.
- **Network reciprocity**: individuals interact only with local neighbors on a
  graph. Cooperators can cluster and preferentially interact with each other,
  even in one-shot interactions with no memory.

These mechanisms are orthogonal. A spatial model with pair memory has both. A
spatial model without pair memory has only network reciprocity. A well-mixed
model with persistent pair relationships has only direct reciprocity.

## Difference from the Spatial Sibling

| Property | `direct_reciprocity_pair_game` | `direct_reciprocity_well_mixed` |
| --- | --- | --- |
| Population structure | 2D grid (24 × 24) | Flat list (`n_sites`) |
| Pairing | Fixed local neighbors | Configurable persistence |
| Moran replacement | Local neighborhood selection | Global fitness-weighted selection |
| Clustering possible | Yes (network reciprocity) | No |
| Re-encounter with same partner | High (neighbors are stable) | Controlled by `partner_persistence_probability` |
| Mechanism tested | Direct + network reciprocity | Direct reciprocity only |

## What "Well-Mixed" Means — and the Re-Encounter Problem

Removing the grid eliminates network reciprocity. But there is a second
requirement for direct reciprocity to function: agents must re-encounter the
*same partner* across steps. If pairs are reshuffled every step, the
re-encounter probability is approximately `1 / (n_sites − 1)` — effectively
zero. Memory is useless if you never meet your partner again. ALLD will dominate
for two reasons simultaneously: no clustering *and* no repeated encounters.

This model controls re-encounter via `partner_persistence_probability` (`p`):

- Each step, each existing pair is kept with probability `p` and broken with
  probability `1 − p`.
- Freed agents are reshuffled into new random pairs.
- Moran replacement does not itself reshuffle pairs. If a site is replaced or
  mutates, its pair assignment can persist, but its pair-specific memory is
  reset according to `reset_memory_on_replacement`.
- `p = 0.0`: full reshuffle every step — no re-encounter, ALLD always wins.
- `p = 0.9`: agents stay with the same partner for ~10 steps on average —
  enough for TFT to establish and maintain mutual cooperation.

The default is `p = 0.9`, giving direct reciprocity a fair chance to operate.

## State

Each site `i` stores:

- `s_i`: strategy type
- `lineage_i`: inherited identity label
- `last_action[i, j]`: previous action by site `i` toward partner `j`
- `last_payoff[i, j]`: previous payoff received by site `i` against partner `j`

Implemented strategies:

| Strategy | Rule |
| --- | --- |
| `ALLC` | Always cooperate. |
| `ALLD` | Always defect. |
| `TFT` | Cooperate first, then copy the partner's previous action. |
| `GTFT` | Tit-for-tat with probabilistic forgiveness after partner defection. |
| `WSLS` | Win-stay lose-shift: repeat the previous action if payoff met aspiration; otherwise switch. |

## Payoff Game

Each pair plays the Prisoner's Dilemma.

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

This ordering is the definition of the Prisoner's Dilemma. Defecting against a
cooperator pays more than mutual cooperation (`T > R`), so defection is
individually tempting. Mutual cooperation pays more than mutual defection
(`R > P`), so cooperation is collectively better. Mutual defection still beats
being exploited (`P > S`), making defection the safe individual choice. The
dilemma is that individually rational agents defect even though both would be
better off cooperating.

## Moran Update

At each step:

1. Existing pairs are kept with probability `partner_persistence_probability`;
   broken pairs release both agents into a globally reshuffled pool. On the
   first step, all agents are randomly paired.
2. Current pairs play `rounds_per_pair_per_step` repeated PD rounds using
   pair-specific memory.
3. Site payoffs accumulate; fitness is computed as:

   <p>W_i = base_fitness + payoff_i</p>

4. Each site samples a parent from the **entire population** with global
   softmax fitness selection.
5. The offspring inherits the parent's strategy and lineage.
6. With probability `mutation_rate`, the offspring switches to another strategy.
7. Pair memory is reset for replaced or mutated sites; persistent sites keep
   memory with other persistent sites.

## Emergence Criterion

The proof utility uses the same thresholds as the spatial sibling:

- final action cooperation rate ≥ `0.60`
- final reciprocal-strategy frequency ≥ `0.50`
- final `ALLD` frequency ≤ `0.25`

### What the spatial sibling has that this model does not

The spatial sibling combines two mechanisms:

1. **Pair memory and repeated rounds** (direct reciprocity): TFT can punish a
   defector in the next round with the same partner.
2. **Grid topology** (network reciprocity): TFT agents interact mainly with
   their local neighbors. A cluster of TFT agents spend most interactions with
   *each other*, building high fitness, while ALLD can only erode the cluster
   from the outside edge.

Both matter in the spatial model — the ablations confirm that removing memory
or reducing rounds collapses cooperation — but the grid is also load-bearing:
it guarantees high re-encounter probability *and* spatial shielding.

This model removes only the grid. With high `partner_persistence_probability`,
it still tests whether direct reciprocity alone — repeated encounters with the
same partner, without spatial clustering — can sustain cooperation.

### Expected results

**Final-step snapshots are misleading** for small populations. Because the
population is finite, stochastic drift causes the population to occasionally
fix on ALLD even when direct reciprocity is operating. The time-averaged
cooperation rate across all steps is the right metric.

With `p = 0.9` (default) and `mutation_rate = 0.001`: avg cooperation rate
≈ 0.52 — cooperation is maintained roughly half the time, with the population
regularly returning to high-cooperation states after ALLD invasions.

With `p = 0.0` (full reshuffle): avg cooperation rate ≈ 0.33 — ALLD dominates
most of the time; cooperation only arises transiently before being eroded.

The `rare_invaders_start` scenario (5% random reciprocal agents, rest ALLD)
is a stronger test than the spatial sibling's `rare_cluster_start`, because
invaders cannot benefit from clustering. If cooperation emerges here, it is
driven by direct reciprocity alone.

The ablation scenarios (`no_memory_ablation`, `one_round_ablation`) confirm
that whatever cooperation emerges depends on memory and repeated rounds.

## Display-Only Grid Viewer

The model is still well mixed, so the core state is a flat population rather
than a spatial world. The display-grid viewer adds a visual layout only:

1. Agent IDs are placed into a fixed display grid, usually 20 x 10 for the
   default `n_sites = 200`.
2. Cell color shows the current strategy at that agent ID.
3. Lines show `current_pairs`, including long-distance links across the grid.
4. Retained pair links are drawn more strongly than newly reshuffled links.

This viewer does not add network reciprocity. Grid position does not affect
interaction, payoff, replacement, or mutation. It exists only to make
`p = 0.9` visible: most partner links persist from one step to the next, while a
small fraction breaks and re-pairs globally.

## Linked Viewer

The linked viewer runs one shared `DirectReciprocityWellMixedModel` and renders
two synchronized views in the same pygame window:

1. The left panel shows the display-only grid and global pair links.
2. The right panel shows the aggregate composition bars and time-series charts.
3. One event loop controls stepping, pause, reset, and speed for both panels.

This is the preferred viewer when comparing the microscopic pair-persistence
mechanism against the macroscopic cooperation and strategy-frequency dynamics.
Because both panels read from the same model object after each `model.step()`,
there is no risk that the views drift into separate simulation histories.

### Why ALLD dominates at `p = 0.0`

With full reshuffling, re-encounter probability is ~`1 / (n_sites − 1)`. A
TFT agent that punishes a defector today will almost certainly never meet that
defector again — so punishment has no deterrent effect. Every step is
effectively a first meeting, and ALLD exploits the first-round cooperator every
time. ALLD accumulates higher fitness and sweeps the population.

## Files

- `direct_reciprocity_well_mixed_model.py`: core well-mixed Moran model.
- `direct_reciprocity_well_mixed_pygame_ui.py`: live viewer with frequency bars.
- `direct_reciprocity_well_mixed_grid_pygame_ui.py`: display-only grid viewer
  with global pair links.
- `direct_reciprocity_well_mixed_linked_pygame_ui.py`: linked single-window
  viewer that shows both the display grid and aggregate charts from one model.
- `config/direct_reciprocity_well_mixed_config.py`: active config.
- `utils/proof_of_mechanism.py`: replicate checks and ablations.

## Run

From the repository root:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_model
```

Live viewer:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_pygame_ui
```

Display-grid live viewer:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_grid_pygame_ui
```

Linked live viewer:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_linked_pygame_ui
```

Proof utility:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.utils.proof_of_mechanism
```
