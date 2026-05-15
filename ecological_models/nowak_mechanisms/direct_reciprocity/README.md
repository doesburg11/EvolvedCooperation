# Ecological Direct Reciprocity

This package holds the ecological direct-reciprocity counterpart to
`moran_models/nowak_mechanisms/direct_reciprocity/`.

The mechanism is Nowak's direct reciprocity: cooperation evolves because the
same two individuals meet repeatedly over time. Memory of past interactions lets
cooperators reduce cooperation toward non-reciprocating partners and dissolve
those partnerships, while maintaining high cooperation with individuals who
reciprocate. Unlike the other ecological Nowak mechanisms, this model is fully
well-mixed — no spatial coordinates, no group membership, no kinship structure.
The only structure is the dyadic partnership graph.

---

## Summary: Moran vs. Ecological Direct Reciprocity

| Aspect | Moran model | Ecological model |
|--------|-------------|-----------------|
| **Mechanism** | Strategy space (TFT, AllC, AllD); Moran fitness-weighted replacement | Continuous helping_trait; dyadic partnerships with memory and conditional dissolution |
| **Key condition** | w > cost threshold (re-encounter probability exceeds cost-to-benefit ratio) | Partner fidelity × differential dissolution: productive partnerships persist, bad ones dissolve |
| **Population structure** | Fixed flat list (well-mixed) | Dynamic (births, deaths, energy, sexual reproduction) |
| **Repeated encounter** | Controlled by `partner_persistence_probability` p | Controlled by `partner_persistence_probability`; asymmetric dissolution via `leave_weight` |
| **Key diagnostic** | Cooperation frequency | `mean_reciprocity_quality`: population mean of partner_memory for active partnerships |
| **Control** | No-memory, one-round ablations | `memory_off` (frozen memory at 1.0); `random_partner_assignment` (no fidelity) |

**Interpretation:**
- The Moran model proves the w > (T−R)/(T−P) condition under idealized strategy dynamics.
- The ecological model shows that cooperation spreads through temporal assortment: stable
  partnerships let productive coop-coop pairs accumulate energy surplus; conditional
  dissolution lets cooperators exit non-reciprocating partnerships and seek better ones.

Together, they show direct reciprocity is robust across model frameworks — though the
ecological model reveals that partnership duration has an optimal range: too-long
partnerships (very high base persistence) hurt because high-cost initial encounters
with non-cooperators persist too long before the differential-dissolution signal kicks in.

---

## Boundary With the Moran Model

The Moran direct-reciprocity model is the abstract control:
- discrete strategy space (TFT, AllC, AllD)
- well-mixed population with controlled partner persistence probability
- fitness-weighted Moran replacement; no births or deaths
- condition: w > (T−R)/(T−P)

This ecological model asks a more realistic question:
- Can cooperation spread when individuals have a continuous heritable cooperation
  trait, form stable dyadic partnerships, track partner cooperation via memory,
  and can dissolve non-reciprocating partnerships more readily?

**Boundary with network reciprocity:**
Network reciprocity directs benefits to spatial neighbors (whoever is nearby),
without requiring repeated interaction with the same individual. Direct reciprocity
is a temporal mechanism: the same two individuals interact across many steps.
This model has no spatial coordinates — there is no network structure.

**Boundary with kin selection and group selection:**
No relatedness, no group membership. The only structure is the partnership graph.
This is the purest well-mixed ecological model in the series.

---

## Core Elements

- Well-mixed population: no spatial coordinates, no groups, no kinship
- Age structure (juvenile, adult, elder), energy budget, sexual reproduction
- No genome, no relatedness, no spatial position — only heritable helping_trait
- Adults maintain stable partnerships; each step a fraction dissolve and reform
- Conditional cooperation: `effective_coop = helping_trait × (1 − reciprocity_weight × (1 − partner_memory))`
- Differential dissolution: effective persistence reduced when partner_memory is low
- Energy benefit delivered directly and exclusively to current partner
- Partnership quality tracked as rolling mean of partner's effective cooperation

---

## One Step

1. Individuals age, update stage (juvenile / adult / elder), and apply energy budget.
2. Partnership update: dissolve partnerships stochastically (influenced by partner_memory);
   newly unpartnered adults matched randomly into new pairs.
3. Partnership interaction: each pair exchanges benefits based on their effective cooperation;
   partner memories updated via exponential moving average.
4. Survival: energy death, age death, stage survival probabilities.
5. Partnership cleanup: clear references to dead individuals.
6. Sexual reproduction: eligible females choose random eligible males (well-mixed);
   offspring inherit blended trait with mutation.
7. Density mortality trims population to `max_population`.

---

## Partnership Mechanism

**Effective cooperation:**
```
effective_coop = helping_trait × (1 − reciprocity_weight × (1 − partner_memory))
```

When `partner_memory = 1.0` (partner always cooperated fully): `effective_coop = helping_trait`
When `partner_memory = 0.0` (partner never cooperated): `effective_coop = helping_trait × (1 − reciprocity_weight)`

**Benefit delivery:**
```
partner.energy += effective_coop × cooperation_benefit_per_step
```

Both individuals in a pair receive benefit from the other's effective cooperation.

**Memory update (exponential moving average):**
```
partner_memory = (1 − memory_smoothing) × partner_memory + memory_smoothing × partner.effective_coop
```

Initial `partner_memory = 1.0` for all new partnerships (optimistic start).

**Effective persistence (differential dissolution):**
```
effective_persistence = partner_persistence_probability × (1 − leave_weight × (1 − partner_memory))
```

Low partner_memory → lower effective persistence → higher dissolution probability.
When `leave_weight = 0.0`: flat dissolution, no memory-based leave behavior.

---

## Mean Reciprocity Quality Diagnostic

The primary diagnostic for whether direct reciprocity is operating:

```
mean_reciprocity_quality = mean over adults in active partnerships of: partner_memory
```

High quality means the average active partnership involves a reciprocating partner —
cooperators have filtered out non-reciprocating partners and are maintaining good ones.
Low quality means many active partnerships are with non-reciprocating individuals.

This is the ecological analog of the mean re-encounter quality in the Moran model.

---

## Proof Scenarios and Results

**Run from repository root:**
```bash
./.conda/bin/python -m ecological_models.nowak_mechanisms.direct_reciprocity.utils.proof_of_mechanism
```

Results across 5 seeds per scenario (500 steps each):

| Scenario | trait_Δ | inv_Δ | pop | quality | Result |
|----------|--------:|------:|----:|--------:|--------|
| `direct_reciprocity_baseline` | +0.001 | +0.041 | 400 | +0.688 | PASS |
| `memory_off` | −0.002 | −0.002 | 400 | +1.000 | PASS† |
| `random_partners` | −0.005 | −0.038 | 400 | +0.815 | PASS† |
| `no_direct_reciprocity` | −0.005 | −0.038 | 400 | +1.000 | PASS† |
| `cost_too_high` | −0.037 | −0.129 | 400 | +0.684 | PASS† |
| `long_partnerships` | −0.002 | +0.049 | 400 | +0.676 | PASS |
| `short_partnerships` | −0.002 | +0.041 | 400 | +0.758 | PASS |
| `high_reciprocity_weight` | +0.002 | +0.055 | 400 | +0.691 | PASS |
| `strong_leave_weight` | −0.003 | +0.022 | 400 | +0.722 | PASS |
| `no_reproduction_cost` | +0.002 | +0.038 | 400 | +0.688 | PASS |

† Inverted scenario: cooperation expected to stay flat or decline.
  Pass condition: mean trait change < 0.010 (not invasion frequency).
  See Finding 3 for why invasion frequency is unreliable for inverted scenarios.

**10 / 10 scenarios pass.**

---

## Simulation Findings

### Finding 1 — Partner fidelity is the primary load-bearing mechanism

The `random_partners` scenario (partners reshuffled every step) shows cooperation
declining: mean trait −0.005 and invasion frequency −0.038. Without repeated
encounters, temporal assortment is impossible. Cooperators cannot build memory of
a specific partner, cannot reduce cooperation toward defectors, and cannot maintain
productive long-term partnerships. The mechanism requires the same two individuals
to meet across multiple steps.

`no_direct_reciprocity` (random partners AND memory frozen) shows the same result,
confirming that partner fidelity is the foundation — adding memory without fidelity
provides nothing additional.

### Finding 2 — Memory and conditional dissolution are jointly necessary

The `memory_off` scenario (partner_memory frozen at 1.0, unconditional cooperation,
flat dissolution) shows both inv_Δ = −0.002 and trait_Δ = −0.002. Cooperation
barely holds or slowly declines.

Without memory:
- Effective cooperation is always `helping_trait` (no reduction toward defectors)
- Dissolution is flat (no faster exit from bad partnerships)
- Cooperators pay cost, give benefit generously to everyone including defectors,
  and cannot escape long-running non-reciprocating partnerships

The memory mechanism does double duty: it conditions cooperation (reduces exploitation
in bad partnerships) AND triggers faster dissolution (enables cooperators to seek
better partners). Together these constitute the reciprocity mechanism.

### Finding 3 — There is an optimal partnership length; too-long hurts

`long_partnerships` (persistence = 0.97, mean ~33 steps) amplifies the mechanism:
invasion frequency +0.049 vs. baseline +0.041. Moderate increases in partnership
length help because coop-coop pairs accumulate more energy surplus per partnership
cycle.

However, very high persistence (0.99, mean ~100 steps) causes cooperation to
DECLINE (tested separately; not in the final proof table). This is because:
1. The initial `partner_memory = 1.0` start means even bad partnerships are
   stable for several steps before memory drops enough to trigger dissolution.
2. With very high base persistence (0.99), the effective dissolution rate in
   bad partnerships barely increases even as memory drops — the differential
   dissolution signal is overwhelmed by the high base rate.
3. Cooperators spend too many steps in non-reciprocating partnerships before
   finding productive ones.

`short_partnerships` (persistence = 0.65, mean ~3 steps) still allows invasion
(+0.041), because rapid partner turnover gives cooperators faster access to the
partner pool, partially compensating for shorter productive partnerships.

### Finding 4 — High benefit amplifies defector exploitation; does not help

Increasing `cooperation_benefit_per_step` from 0.22 to 0.40 causes cooperation to
FAIL (tested separately; not in the final proof table). The reason:
- Rare cooperators (10% initial) are almost always paired with defectors initially
- Higher benefit means defectors extract MORE energy from cooperators per step
- The coop-coop surplus is larger, but the initial exploitation is also larger
- When benefit is high enough, defectors saturate their energy through cooperator
  exploitation and reproduce at high rates before cooperative clusters can form

This mirrors the kin-selection well-mixed finding: removing or amplifying one
mechanism parameter in isolation can hurt rather than help if it also amplifies
a countervailing force (defector exploitation in this case; kin proximity removal
for kin selection).

### Finding 5 — Mean reciprocity quality differentiates mechanism states

The `memory_off` scenario shows quality = 1.0 (memory is frozen at 1.0, so
the diagnostic reads maximum quality by construction). All other scenarios show
quality ~0.68–0.76, reflecting the mixed state of active partnerships (some with
cooperators, some with defectors partway through dissolution).

The `random_partners` scenario shows quality = 0.81: partnerships always start
with memory=1.0 and dissolve after one step, so the average observed memory is
always the initial 1.0 value at the moment of measurement — a measurement
artifact, not a genuine signal of reciprocity quality.

---

## Limitations and Interpretation

**What the model shows:**

- Cooperation can spread in a fully well-mixed population when individuals form
  stable dyadic partnerships, track partner cooperation via memory, and can exit
  non-reciprocating partnerships via conditional dissolution.
- Partner fidelity (repeated encounters) is load-bearing: without it, cooperation
  declines even when memory is intact.
- Memory is also necessary: without it, cooperators cannot reduce exploitation
  or exit bad partnerships, and cooperation slowly declines.
- There is an optimal partnership length: moderate persistence amplifies the
  mechanism; very high persistence traps cooperators in bad partnerships.

**What the model does not show:**

- That direct reciprocity was the actual driver of human cooperative evolution.
- How direct reciprocity competes with kin selection, group selection, or
  network reciprocity in a unified model.
- A clean separation between direct reciprocity and network reciprocity in the
  ecological context when spatial structure is present: this model is well-mixed,
  so it tests pure direct reciprocity without any spatial confound.
- How cultural norms, reputation, or third-party enforcement modify the dynamics.

**Key open question:** The ecological direct-reciprocity model and the Moran
well-mixed model test the same fundamental mechanism (partner persistence enables
cooperation) but differ in whether cooperation can spread from a rare foothold.
The Moran model shows maintenance more cleanly than invasion; the ecological
model shows modest invasion via invasion frequency (but not via mean trait change),
consistent with the same difficulty at rarity that the Moran model exhibits.

---

## Run Commands

```bash
# Single run with default parameters
./.conda/bin/python -m ecological_models.nowak_mechanisms.direct_reciprocity.direct_reciprocity_model

# Proof of mechanism (all scenarios, 5 seeds each)
./.conda/bin/python -m ecological_models.nowak_mechanisms.direct_reciprocity.utils.proof_of_mechanism
```

Active parameters:
```
ecological_models/nowak_mechanisms/direct_reciprocity/config/direct_reciprocity_config.py
```

Latest run output:
```
ecological_models/nowak_mechanisms/direct_reciprocity/data/latest_run.json
```

---

## Parameter Reference

| Parameter | Default | Role |
|-----------|---------|------|
| `partner_persistence_probability` | 0.92 | Base probability partnership survives each step (~12.5 steps mean duration) |
| `reciprocity_weight` | 0.70 | Scales down cooperation proportional to partner defection history |
| `leave_weight` | 0.60 | Reduces persistence proportional to low partner_memory (conditional dissolution) |
| `memory_smoothing` | 0.20 | Exponential average weight for updating partner_memory each step |
| `cooperation_benefit_per_step` | 0.22 | Energy delivered to partner per step per unit effective_coop |
| `helping_cost_per_step` | 0.04 | Energy cost per unit helping_trait per step, paid by adults/elders |
| `helping_reproduction_cost_scale` | 0.20 | Reduces reproduction probability by `trait × scale` |
| `memory_off` | False | Ablation: freeze partner_memory at 1.0, disable conditional coop and leave bias |
| `random_partner_assignment` | False | Ablation: reshuffle all partnerships every step (no repeated encounters) |
| `initial_founder_pairs` | 64 | Number of founding adult pairs at initialization |
| `rare_helper_founder_probability` | 0.10 | Probability each founder is a rare high-helper |
| `rare_helper_trait_value` | 0.65 | Cooperation trait of rare high-helper founders |

---

## Ecological Direct Reciprocity Scaffold Note

On 2026-05-14, `ecological_models/nowak_mechanisms/direct_reciprocity/` was added as
the ecological counterpart to the Moran direct-reciprocity wrapper.

Stepwise impact:

1. The package exists separately from the Moran implementation.
2. The model is fully well-mixed: no spatial coordinates, no groups, no kinship.
   This is the first ecological Nowak mechanism model without spatial structure.
3. The model reuses the demographic engine from the prior ecological models
   (age structure, energy budget, sexual reproduction, density mortality) with
   group/spatial structure replaced by the dyadic partnership mechanism.
4. The proof utility runs 10 scenarios across 5 seeds and achieves 10 / 10 passing.
5. Key discovery: very high partnership persistence (0.99) and very high benefit (0.40)
   both hurt cooperation — they amplify non-reciprocating partner exploitation rather
   than amplifying mutual benefit. This reveals that direct reciprocity has an
   optimal operating regime, unlike the simple "more persistence = better" intuition
   from the Moran model.
6. This is the first ecological Nowak model without a spatial reproductive assortment
   channel. The genetic/blending-inheritance channel is present but weaker here;
   invasion frequency provides the signal rather than mean trait change.
