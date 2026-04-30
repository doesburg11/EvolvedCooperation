# Direct Reciprocity

Three implementations showing when and why direct reciprocity can — and cannot
— sustain cooperation, starting from the pure theoretical case and adding one
feature at a time.

---

## The Condition

Direct reciprocity works through repeated encounters between the *same two
individuals*. A cooperator can punish a defector in the next round and reward a
cooperator. Nowak (2006) shows cooperation is stable when:

<p>w &gt; (T &minus; R) / (T &minus; P)</p>

where:

- **w** — probability of meeting the *same partner again* in the next interaction
- **T** — temptation payoff: what a defector earns against a cooperator
- **R** — reward payoff: what both earn under mutual cooperation
- **P** — punishment payoff: what both earn under mutual defection

With the default Prisoner's Dilemma payoffs (T = 1.7, R = 1.0, P = 0.0,
S = −0.5):

<p>w &gt; (1.7 &minus; 1.0) / (1.7 &minus; 0.0) &asymp; 0.41</p>

**The re-encounter probability w is the critical variable.** Everything below
follows from whether it meets this threshold.

### Payoff matrix

| Actor / Partner | Partner cooperates | Partner defects |
| --- | --- | --- |
| Actor cooperates | R = 1.0 (reward) | S = −0.5 (sucker) |
| Actor defects | T = 1.7 (temptation) | P = 0.0 (punishment) |

This satisfies T > R > P > S — the standard definition of the Prisoner's
Dilemma. Defection is individually tempting (T > R), mutual cooperation beats
mutual defection (R > P), and defecting is the safe choice (P > S). The
dilemma is that rational individuals defect even though both would be better
off cooperating.

### Strategies

| Strategy | Full name | Rule |
| --- | --- | --- |
| ALLC | Always Cooperate | Cooperate unconditionally. |
| ALLD | Always Defect | Defect unconditionally. |
| TFT | Tit for Tat | Cooperate on the first round; then copy the partner's previous action. |
| GTFT | Generous Tit for Tat | Like TFT, but forgive a defection with fixed probability. |
| WSLS | Win-Stay Lose-Shift | Repeat the previous action if it paid at or above aspiration; otherwise switch. |

---

## Step 1 — Pure direct reciprocity fails

**Model:** [`well_mixed/`](well_mixed/) with `partner_persistence_probability = 0.0`

In a population of 200 agents with random re-pairing every step, the
probability of meeting the same partner again is:

<p>w &asymp; 1 / (n &minus; 1) &asymp; 0.005</p>

This is far below the threshold of 0.41. Memory is useless: even if TFT
punished a defector last round, it will almost certainly never meet that
defector again. ALLD exploits every cooperator it encounters in round 1,
accumulates higher fitness, and sweeps the population.

**Result: ALLD dominates. Cooperation cannot emerge.**

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_model
```

Set `partner_persistence_probability = 0.0` in
[`well_mixed/config/direct_reciprocity_well_mixed_config.py`](well_mixed/config/direct_reciprocity_well_mixed_config.py).

---

## Step 2 — Partner persistence enables direct reciprocity

**Model:** [`well_mixed/`](well_mixed/) with `partner_persistence_probability = 0.9`

`partner_persistence_probability` (p) is the probability that an existing pair
stays together in the next step. Each step, for every pair (i, j):

- with probability p: the pair is kept; i and j play together again
- with probability 1 − p: the pair is dissolved; both agents are pooled with
  other dissolved agents and re-paired at random

When p = 0.9, the effective re-encounter probability is:

<p>w &asymp; 0.9 &gt; 0.41 &#10003;</p>

The condition is satisfied. TFT–TFT pairs that find each other build mutual
cooperation across rounds. ALLD exploits TFT in round 1 (earning T = 1.7), but
TFT retaliates from round 2 onwards; the persistent ALLD–TFT pair quickly
becomes mutual defection (P = 0.0 for both). TFT–TFT pairs earn R = 1.0 per
round and spread.

**Result: Cooperation emerges through direct reciprocity alone, without any
spatial structure.** The time-averaged cooperation rate rises from ~0.33
(p = 0.0) to ~0.52 (p = 0.9). The population cycles: TFT takes over, mutation
reintroduces ALLD, direct reciprocity re-establishes cooperation.

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_model
```

Default `partner_persistence_probability = 0.9` is set in
[`well_mixed/config/direct_reciprocity_well_mixed_config.py`](well_mixed/config/direct_reciprocity_well_mixed_config.py).

A display-only grid viewer makes this persistence visible without changing the
well-mixed mechanism. The grid positions are fixed agent-ID slots; interaction
and replacement remain global:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_grid_pygame_ui
```

The linked viewer shows that display grid and the aggregate charts in one
window, both driven by the same model state:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_linked_pygame_ui
```

---

## Step 3 — Spatial structure adds network reciprocity

**Model:** [`pair_game/`](pair_game/)

Placing agents on a 2D grid and restricting both interactions and Moran
replacement to local neighbors adds a second mechanism on top of direct
reciprocity: **network reciprocity**. Cooperators can form spatial clusters and
preferentially interact with each other, even before any trust has been
established.

This means:
- Pair memory and repeated rounds sustain cooperation within established pairs
  (direct reciprocity).
- The grid prevents ALLD from reaching the interior of a cooperator cluster
  (network reciprocity).

Both mechanisms are active simultaneously. A 5% spatial cluster of TFT agents
in a sea of ALLD survives and spreads on the grid. The ablation tests in
[`pair_game/utils/proof_of_mechanism.py`](pair_game/utils/proof_of_mechanism.py)
confirm that removing either memory or repeated rounds collapses cooperation —
but spatial clustering is also load-bearing.

**Result: Cooperation emerges more robustly, but the mechanism is no longer
pure direct reciprocity.**

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.pair_game.direct_reciprocity_pair_game_model
```

See [`pair_game/`](pair_game/).

---

## Note: Continuous interaction-kernel model

**Model:** [`continuous/`](continuous/)

A separate, continuous-trait implementation wraps the shared interaction-kernel
engine. Agents carry a cooperation capacity h and pair-specific partner memory.
Help is routed preferentially back toward neighbors that helped before. This
model uses a benefit–cost framework rather than a Prisoner's Dilemma and is not
directly comparable to the discrete-strategy models above.

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.continuous.direct_reciprocity_model
```

See [`continuous/`](continuous/).

---

## Summary

| | `well_mixed` p = 0.0 | `well_mixed` p = 0.9 | `pair_game` |
| --- | --- | --- | --- |
| Re-encounter probability w | ≈ 0.005 | ≈ 0.9 | High (fixed neighbors) |
| Condition w > 0.41 | No | Yes | Yes |
| Spatial clustering | No | No | Yes |
| Active mechanisms | None | Direct reciprocity | Direct + network reciprocity |
| Cooperation emerges | No | Yes (moderate) | Yes (robust) |

---

## References

- Nowak, M. A. (2006). *Five rules for the evolution of cooperation*. *Science*, 314(5805), 1560–1563. https://doi.org/10.1126/science.1133755
- Axelrod, R., & Hamilton, W. D. (1981). *The evolution of cooperation*. *Science*, 211(4489), 1390–1396. https://doi.org/10.1126/science.7466396
