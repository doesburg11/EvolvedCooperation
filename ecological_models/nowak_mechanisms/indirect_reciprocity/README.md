# Ecological Indirect Reciprocity

This package holds the ecological indirect-reciprocity counterpart to
`moran_models/nowak_mechanisms/indirect_reciprocity/`.

The mechanism is Nowak's indirect reciprocity: cooperation evolves because
public reputation makes past cooperative behaviour visible to new partners.
Donors observe a recipient's reputation with probability q and help only if
reputation ≥ threshold. Nowak's condition: q > c/b.

Unlike kin selection, group selection, and network reciprocity, this model is
fully well-mixed — no spatial coordinates, no group membership. The only
structure is the public reputation score and the dyadic pairing that occurs
each step.

---

## Summary: Moran vs. Ecological Indirect Reciprocity

| Aspect | Moran model | Ecological model |
|--------|-------------|-----------------|
| **Mechanism** | Strategy space; Moran fitness-weighted replacement | Continuous helping_trait; public reputation; reputation-gated energy routing |
| **Key condition** | q > c/b (observation probability exceeds cost-to-benefit ratio) | q > c/b for energy routing AND reputation-weighted mate choice for genetic channel |
| **Population structure** | Fixed flat list (well-mixed) | Dynamic (births, deaths, energy, sexual reproduction) |
| **Reputation** | Binary or continuous public score | Exponential moving average of per-step cooperation rate |
| **Ecological channel** | None | Reputation-weighted mate choice: high-rep males sire more offspring |
| **Invasion from rare** | Conditional on q and benefit level | Requires genetic channel (mate preference); energy routing alone insufficient |

**Interpretation:**
- The Moran model proves the q > c/b condition for cooperation maintenance under
  idealized strategy dynamics.
- The ecological model reveals that energy routing alone (Nowak's original channel)
  cannot sustain invasion from rare with blending inheritance. The reputation-weighted
  mate choice creates reproductive assortment — the same genetic channel that is
  load-bearing in all five ecological Nowak models.

---

## Boundary With the Moran Model

The Moran indirect-reciprocity model is the abstract control:
- discrete or simplified strategy space
- well-mixed population with controlled reputation observation probability q
- fitness-weighted Moran replacement; no births or deaths
- condition: q > c/b

This ecological model asks a more realistic question:
- Can cooperation spread when individuals have a continuous heritable cooperation
  trait, public reputation updates dynamically, energy is routed to high-reputation
  individuals, and reputation acts as a mate-quality signal?

**Why energy routing alone fails for invasion from rare:**
With 10% initial cooperators and blending inheritance, full cooperators (trait=0.65)
produce offspring with trait ≈ 0.33. These offspring have reputation → 0.33 (below
threshold 0.50), so they cannot participate in energy routing. The energy advantage
from reputation routing does not persist across generations when traits blend toward
the defector mean. The genetic channel (mate preference) is required to cluster
cooperator × cooperator pairings and keep offspring traits above threshold.

**Boundary with direct reciprocity:**
Direct reciprocity requires the same two individuals to meet repeatedly (temporal
assortment). Indirect reciprocity involves different partners across interactions
— cooperation is motivated by reputation observable to future partners, not by
repeated encounters with the same individual. Both models are fully well-mixed.

---

## Core Elements

- Well-mixed population: no spatial coordinates, no groups, no kinship
- Age structure (juvenile, adult, elder), energy budget, sexual reproduction
- Public reputation per individual (not heritable): dynamically updated each step
- Exponential moving average: `rep = (1 − w) × rep + w × coop_rate_this_step`
- Energy routing: donor helps recipient only if recipient reputation ≥ threshold,
  and donor observes reputation with probability q
- Reputation-weighted mate choice: males selected proportionally to reputation
  (genetic channel — the load-bearing ecological mechanism)

---

## One Step

1. Individuals age, update stage (juvenile / adult / elder), and apply energy budget.
2. Active adults shuffled and paired consecutively for this step.
3. Indirect reciprocity interactions: for each pair (A, B), A observes B's reputation
   with probability q; if observed and B.rep ≥ threshold, A decides to help with
   probability A.helping_trait. Help count and eligible count updated. Same
   for B observing A.
4. Reputation update: for each adult, `new_rep = (1−w)×rep + w×(help_count/eligible_count)`.
   If eligible_count = 0, reputation decays: `new_rep = (1−w)×rep`.
5. Survival: energy death, age death, stage survival probabilities.
6. Sexual reproduction: eligible females choose males weighted by reputation (if
   `reputation_mate_preference > 0`); offspring inherit blended trait with mutation.
7. Density mortality trims population to `max_population`.

---

## Reputation Mechanism

**Conditional cooperation:**
```
if rng.random() < q:              # observe recipient reputation
    if recipient.reputation >= threshold:
        eligible_count[donor] += 1
        if rng.random() < donor.helping_trait:
            recipient.energy += cooperation_benefit
            help_count[donor] += 1
```

**Reputation update (exponential moving average):**
```
if eligible_count > 0:
    coop_rate = help_count / eligible_count
    reputation = (1 − weight) × reputation + weight × coop_rate
else:
    reputation = (1 − weight) × reputation   # decay when not observed
```

At steady state, cooperator reputation → helping_trait (not q × helping_trait).
The `eligible_count` is placed INSIDE the threshold check, so the denominator
counts only observed-and-eligible events — giving the true conditional cooperation
rate, not a probability-discounted rate.

**Reputation-weighted mate choice:**
```
mate_weight[male] = male.reputation × pref + (1 − pref)
```

With `pref = 1.0`, `rep_coop = 0.65`, `rep_defector = 0.02`:
cooperators are selected as mates 32× more often than defectors.

---

## Proof Scenarios and Results

**Run from repository root:**
```bash
./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.utils.proof_of_mechanism
```

Results across 5 seeds per scenario (500 steps each):

| Scenario | trait_Δ | inv_Δ | pop | rep | Result |
|----------|--------:|------:|----:|----:|--------|
| `indirect_reciprocity_baseline` | +0.0431 | +0.6265 | 400 | 0.410 | PASS |
| `random_benefit_routing` | +0.1656 | +0.8525 | 400 | 0.334 | PASS |
| `no_mate_preference` | −0.0091 | −0.0500 | 400 | 0.401 | PASS† |
| `impossible_threshold` | −0.0130 | −0.0665 | 400 | 0.650 | PASS† |
| `no_mate_preference_low_q` | −0.0063 | −0.0229 | 400 | 0.581 | PASS† |
| `cost_too_high` | −0.0137 | −0.0711 | 396 | 0.395 | PASS† |
| `high_observation_prob` | +0.0726 | +0.7645 | 400 | 0.395 | PASS |
| `fast_reputation_update` | +0.1712 | +0.8525 | 400 | 0.312 | PASS |
| `slow_reputation_update` | +0.0125 | +0.2139 | 399 | 0.461 | PASS |
| `no_reproduction_cost` | +0.0368 | +0.5496 | 399 | 0.410 | PASS |

† Inverted scenario: cooperation expected to stay flat or decline.
  Pass condition: mean trait change < 0.010 (not invasion frequency).

**10 / 10 scenarios pass.**

---

## Simulation Findings

### Finding 1 — The genetic channel (mate preference) is the load-bearing mechanism

The `random_benefit_routing` scenario (energy routing ablated — benefits distributed
to random adults regardless of reputation, while mate preference remains fully intact)
achieves inv_Δ = +0.8525 — STRONGER than the baseline (+0.6265). The genetic channel
alone is not only sufficient but is actually the dominant driver of invasion.

The `no_mate_preference` scenario (mate choice random regardless of reputation, while
energy routing remains fully intact) shows cooperation declining: trait_Δ = −0.009,
inv_Δ = −0.050. Ablating only the mate preference prevents invasion.

**Conclusion:** Nowak's original energy-routing channel contributes secondary energy
advantage but is not the primary driver of invasion from rare in an ecological model
with blending inheritance. The reproductive assortment created by reputation-weighted
mate choice is required.

### Finding 2 — Energy routing alone cannot overcome blending inheritance

With 10% initial cooperators (trait=0.65) and blending inheritance, full cooperators
produce offspring with trait ≈ 0.33 (blending toward resident mean ≈ 0.02). These
offspring have reputation → 0.33, below threshold 0.50, so they do not participate
in energy routing. The cooperator's energy advantage dissipates within one generation.

The mate-preference channel bypasses this by pairing cooperator × cooperator, keeping
offspring traits near 0.65. The genetic structure survives across generations even
when the energy structure does not.

### Finding 3 — impossible_threshold cleanly ablates both channels

Setting `reputation_threshold = 0.99` (unreachable from initial rep = 0.65) ensures
eligible_count is never incremented, so reputation never updates. All individuals
retain their initial reputation = 0.65 identically:
- Energy routing: never fires (nobody meets threshold)
- Mate preference: all males have identical reputation, so weights are equal → random

This is the cleanest double-ablation: both channels are broken simultaneously by a
single parameter change, with no stochastic drift from demographic flush.

### Finding 4 — Faster reputation update strengthens both channels

`fast_reputation_update` (weight = 0.50) shows inv_Δ = +0.8525 (matching the
random_benefit_routing result, which was the strongest). Faster updates mean
defectors are detected and excluded from both energy routing and mate choice
within a few steps. Cooperators build high reputation quickly and attract mates.

`slow_reputation_update` (weight = 0.05) still passes (inv_Δ = +0.2139), confirming
the mechanism is robust to sluggish reputation dynamics — but invasion is weaker,
because cooperators take longer to differentiate from defectors via reputation.

### Finding 5 — Invasion frequency and trait change are both reliable metrics

Unlike the direct-reciprocity model (where blending inheritance is weak without
spatial clustering), the indirect-reciprocity model shows both strong trait changes
(+0.04 to +0.17 in positive scenarios) and strong invasion frequency changes
(+0.22 to +0.85). The reputation-weighted mate choice creates tight reproductive
assortment between cooperators, sustaining cooperator × cooperator lineages across
generations and producing large trait-level changes in the population.

---

## Limitations and Interpretation

**What the model shows:**

- Cooperation can spread in a fully well-mixed population when reputation is public
  and high-reputation cooperators are preferred as mates.
- Reputation-weighted mate choice is the load-bearing ecological mechanism:
  ablating energy routing does not prevent invasion; ablating mate preference does.
- Energy routing alone (Nowak's q > c/b condition) is insufficient for invasion
  from rare with blending inheritance — it requires the genetic assortment channel.
- This finding is consistent across all five ecological Nowak models: genetic
  assortment through the reproductive channel is necessary and sometimes sufficient.

**What the model does not show:**

- That indirect reciprocity was the actual driver of human cooperative evolution.
- How indirect reciprocity competes with other mechanisms in a unified model.
- Whether moral norms, gossip, or third-party enforcement modify the dynamics.
- How reputation updating works in populations with structured information flow.

**Key open question:** The Moran indirect-reciprocity model and ecological model
agree that q > c/b enables cooperation. They disagree on whether energy routing
alone is sufficient: the Moran model's idealized discrete-strategy space allows
this, but the ecological model with continuous traits and blending inheritance
requires the additional genetic assortment channel to sustain invasion from rare.

---

## Run Commands

```bash
# Single run with default parameters
./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_model

# Proof of mechanism (all scenarios, 5 seeds each)
./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.utils.proof_of_mechanism
```

Active parameters:
```
ecological_models/nowak_mechanisms/indirect_reciprocity/config/indirect_reciprocity_config.py
```

Latest run output:
```
ecological_models/nowak_mechanisms/indirect_reciprocity/data/latest_run.json
```

---

## Parameter Reference

| Parameter | Default | Role |
|-----------|---------|------|
| `reputation_observation_prob` | 0.70 | Probability q that a donor observes recipient reputation before deciding to help (Nowak's q) |
| `reputation_threshold` | 0.50 | Minimum reputation for a donor to help a recipient |
| `reputation_initial` | 0.65 | Starting reputation for all individuals (near cooperator steady state) |
| `reputation_update_weight` | 0.10 | Exponential average weight for reputation update per step |
| `reputation_mate_preference` | 1.0 | Strength of reputation-based male mate preference [0,1] |
| `random_benefit_routing` | False | Ablation: distribute benefits to random adults, ignoring reputation |
| `cooperation_benefit_per_step` | 0.25 | Energy delivered to recipient per unit trait when helped |
| `helping_cost_per_step` | 0.04 | Energy cost per unit helping_trait per step, paid by adults/elders |
| `helping_reproduction_cost_scale` | 0.10 | Reduces reproduction probability by `trait × scale` |
| `initial_founder_pairs` | 64 | Number of founding adult pairs at initialization |
| `rare_helper_founder_probability` | 0.10 | Probability each founder is a rare high-helper |
| `rare_helper_trait_value` | 0.65 | Cooperation trait of rare high-helper founders |

---

## Ecological Indirect Reciprocity Scaffold Note

On 2026-05-14, `ecological_models/nowak_mechanisms/indirect_reciprocity/` was added
as the ecological counterpart to the Moran indirect-reciprocity wrapper.

Stepwise impact:

1. The package exists separately from the Moran implementation.
2. The model is fully well-mixed: no spatial coordinates, no groups, no kinship.
   This is the second ecological Nowak mechanism model without spatial structure
   (after direct_reciprocity).
3. The model reuses the demographic engine from the prior ecological models
   (age structure, energy budget, sexual reproduction, density mortality) with
   group/spatial structure replaced by the public reputation mechanism.
4. Key implementation note: `eligible_count` must be incremented INSIDE the
   `if recipient.reputation >= threshold:` block, not outside it. Placing it
   outside causes reputation to converge to q × helping_trait (not helping_trait),
   which collapses below threshold 0.50 and breaks the mechanism entirely.
5. The proof utility runs 10 scenarios across 5 seeds and achieves 10 / 10 passing.
6. Key discovery: the reputation-weighted mate-choice channel (ecological addition)
   is more powerful than the reputation-gated energy-routing channel (Nowak's
   original). This is the fifth ecological Nowak model to show that the genetic
   reproductive channel dominates over the direct-energy channel.
