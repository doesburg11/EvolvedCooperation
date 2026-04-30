# Direct Reciprocity

Three implementations showing when and why direct reciprocity can — and cannot
— sustain cooperation.

## The Condition

Direct reciprocity works through repeated encounters between the *same two
individuals*. A cooperator can punish a defector next round and reward a
cooperator. Nowak (2006) shows cooperation is stable when:

<p>w &gt; (T &minus; R) / (T &minus; P)</p>

where `w` is the probability of meeting the *same partner again* in the next
interaction. With the default Prisoner's Dilemma payoffs (T=1.7, R=1.0,
P=0.0, S=−0.5):

<p>w &gt; (1.7 &minus; 1.0) / (1.7 &minus; 0.0) &asymp; 0.41</p>

**The re-encounter probability is the critical variable.** Everything else
follows from it.

---

## Step 1 — Pure direct reciprocity fails (`well_mixed`, `p = 0.0`)

In a population of 200 agents with random re-pairing every step, the
probability of meeting the same partner again is:

<p>w &asymp; 1 / (n &minus; 1) &asymp; 0.005</p>

This is far below the threshold of 0.41. Memory is useless: even if TFT
punished a defector last round, it will almost certainly never meet that
defector again. ALLD exploits the first-round cooperator every time it is
paired with one, accumulates higher fitness, and sweeps the population.

**Result: ALLD dominates. Cooperation cannot emerge.**

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_model
# set partner_persistence_probability = 0.0 in config
```

See [`well_mixed/`](well_mixed/).

---

## Step 2 — Partner persistence enables direct reciprocity (`well_mixed`, `p = 0.9`)

Adding partner persistence gives agents a 90% chance of staying with the same
partner next step. The effective re-encounter probability is now:

<p>w &asymp; 0.9 &gt; 0.41 &#10003;</p>

The condition is satisfied. Pairs of TFT agents that find each other build
mutual cooperation over many rounds (payoff R=1.0 per round, fitness ≈ 4.0
for 3 rounds). ALLD exploits TFT in round 1 (payoff T=1.7) but TFT retaliates
from round 2 onwards, so the ALLD–TFT pair quickly becomes mutual defection
(payoff P=0.0). Over time, TFT–TFT pairs have higher mean fitness than
ALLD–ALLD pairs and spread.

**Result: Cooperation emerges through direct reciprocity alone, without any
spatial structure.** The population cycles: TFT takes over, mutation
reintroduces ALLD, and direct reciprocity re-establishes cooperation. The
time-averaged cooperation rate is ~0.52 vs ~0.33 with `p = 0.0`.

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_model
# partner_persistence_probability = 0.9 (default)
```

See [`well_mixed/`](well_mixed/).

---

## Step 3 — Spatial structure adds network reciprocity (`pair_game`)

Fixing agents to a 2D grid and restricting both interactions and Moran
replacement to local neighbors adds a second mechanism: **network reciprocity**.
Cooperators can form spatial clusters and preferentially interact with each
other, even before any trust has been established through repeated interaction.

This means:
- Pair memory sustains cooperation within established pairs (direct reciprocity).
- The grid prevents ALLD from reaching the interior of a cooperator cluster
  (network reciprocity).

Both mechanisms are active simultaneously. The ablation tests in
[`pair_game/utils/proof_of_mechanism.py`](pair_game/utils/proof_of_mechanism.py)
confirm that removing either memory or repeated rounds collapses cooperation —
but the spatial structure is load-bearing too: a 5% cluster of TFT agents in a
sea of ALLD survives and spreads on the grid, but the equivalent
`rare_invaders_start` scenario in `well_mixed` is much harder.

**Result: Cooperation emerges more robustly, but the mechanism is no longer
pure direct reciprocity.**

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.pair_game.direct_reciprocity_pair_game_model
```

See [`pair_game/`](pair_game/).

---

## Note: Continuous interaction-kernel model (`continuous`)

A separate, continuous-trait implementation wraps the shared interaction-kernel
engine. Agents carry a cooperation capacity `h` and pair-specific partner
memory. This model is not a Prisoner's Dilemma — it uses a benefit–cost
framework — and is not directly comparable to the discrete-strategy models
above. It demonstrates the same qualitative logic (memory biases help toward
helpers) in a different modelling tradition.

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.continuous.direct_reciprocity_model
```

See [`continuous/`](continuous/).

---

## Summary

| | `well_mixed` `p=0.0` | `well_mixed` `p=0.9` | `pair_game` |
| --- | --- | --- | --- |
| Re-encounter probability `w` | ≈ 0.005 | ≈ 0.9 | High (fixed neighbors) |
| Condition `w > 0.41` met | No | Yes | Yes |
| Spatial clustering | No | No | Yes |
| Mechanism | — | Direct reciprocity | Direct + network reciprocity |
| Cooperation emerges | No | Yes (moderate) | Yes (robust) |
