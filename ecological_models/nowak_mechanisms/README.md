# Ecological Nowak Mechanisms

This directory is the ecological counterpart to
`moran_models/nowak_mechanisms/`.

The purpose is to investigate the same five Nowak cooperation mechanisms on
equal conceptual footing, but with ecological life-history dynamics instead of
requiring a Moran replacement process.

The Moran counterpart remains the abstract fixed-population benchmark. This
ecological counterpart is for models where cooperation changes survival,
development, reproduction, dispersal, group persistence, or other demographic
conditions.

## Mechanism Map

Planned ecological mechanism folders should mirror the Moran names:

- `direct_reciprocity/`
- `indirect_reciprocity/`
- `kin_selection/`
- `network_reciprocity/`
- `group_selection/`

Implemented ecological mechanism folders:

- `kin_selection/`
  Tests rare-helper invasion with sexual reproduction, diploid relatedness,
  juvenile rearing, care costs, juvenile survival benefits, and measured
  relatedness/benefit/cost diagnostics, including lifetime reproductive
  success and unrelated-rearing controls.

- `group_selection/`
  Tests cooperation spread through probabilistic inter-group conflict with
  winner energy bonus, dynamic group structure (fission/absorption), and
  Qst diagnostic. Shows conflict doubles as demographic engine; assortative
  mating is a parallel genetic channel.

- `network_reciprocity/`
  Tests rare-helper invasion in continuous space with spatial offspring
  placement, local benefit delivery, and spatial mating preference.
  Primary finding: local offspring placement (not explicit benefit routing)
  is the load-bearing mechanism; spatial reproductive assortment spreads
  cooperation independently through the genetic channel.

- `direct_reciprocity/`
  Tests rare-helper invasion in a fully well-mixed population with dyadic
  partnerships, partner memory, conditional cooperation, and differential
  dissolution. First ecological model without spatial structure. Primary
  finding: partner fidelity (repeated encounters) and memory (conditional
  dissolution) are jointly necessary; optimal partnership length exists —
  very high persistence traps cooperators in bad partnerships.

- `indirect_reciprocity/`
  Tests rare-helper invasion in a fully well-mixed population with public
  reputation scores, reputation-gated energy routing, and reputation-weighted
  mate choice. Primary finding: the genetic channel (reputation-based mate
  preference) is the load-bearing mechanism; energy routing alone cannot
  sustain invasion from rare with blending inheritance, but the genetic
  channel works even when energy routing is completely ablated.

Each folder should make clear which Nowak mechanism is being tested and which
ecological machinery is being added.

---

## Cross-Mechanism Comparison

All five mechanisms have working ecological models that pass proof-of-mechanism.
Starting condition for all: 10% rare helpers (trait = 0.65) against a near-defector
resident background (trait ≈ 0.02). Results averaged across 5 seeds, 500 steps.

| Mechanism | inv_Δ | trait_Δ | Invasion strength | Load-bearing channel |
|-----------|------:|--------:|-------------------|----------------------|
| Kin selection | strong | strong | **Strong** | Kin-biased rearing; spatial reproductive assortment |
| Group selection | strong | strong | **Strong** | Inter-group conflict + assortative mating |
| Network reciprocity | strong | strong | **Strong** | Local offspring placement (spatial reproductive assortment) |
| Indirect reciprocity | +0.63 | +0.04 | **Strong** | Reputation-weighted mate choice (genetic assortment) |
| Direct reciprocity | +0.04 | +0.001 | **Weak but real** | Partner fidelity + memory (temporal assortment) |

**Direct reciprocity is the weak link.** It passes the proof threshold (inv_Δ > 0.02)
but the invasion signal is ~15× weaker than indirect reciprocity and mean trait barely
moves (+0.001). The mechanism is real but fragile when starting from rare with blending
inheritance in a well-mixed population. This mirrors the Moran result, where direct
reciprocity passes maintenance more convincingly than invasion from rare — it appears
to be an inherent property of the mechanism rather than a modeling artifact.

**A consistent finding across all five models:** The load-bearing ecological channel
is always some form of reproductive assortment — kin proximity, group-level assortment,
spatial offspring clustering, or reputation-weighted mate choice. Nowak's original
energy-routing conditions (w > threshold, q > c/b, B/C > 1/r, etc.) are necessary
but not sufficient for invasion from rare with blending inheritance. The genetic
reproductive channel is what carries cooperation through the reproductive bottleneck
each generation.

**Direct reciprocity is the exception that tests the rule:** it has no spatial,
group, or reputation-based reproductive assortment channel. Its invasion signal
is correspondingly the weakest of the five — consistent with the prediction that
the mechanism should be hardest to evolve from rare without a genetic channel.

### Two Channels, Not One

Each ecological model has two separate channels through which cooperation
could in principle be carried forward:

1. **The energy channel.** During a cooperator's lifetime, does routing
   benefit toward it let it survive or reproduce better than a defector?
   This is the same thing Nowak's original B/C conditions are about.
2. **The reproductive channel.** When a cooperator has offspring, do those
   offspring end up disproportionately near, or paired with, other
   cooperators — so the next generation stays assorted instead of being
   randomly remixed with defectors?

For four of the five mechanisms, the energy channel alone was not enough to
sustain invasion from rare. What actually carried it was the reproductive
channel — a mechanism-specific way that offspring placement or mate choice
stayed non-random across generations:

| Mechanism | What the reproductive channel turned out to be |
|-----------|--------------------------------------------------|
| Kin selection | Juveniles are reared near their (related) parents, so relatedness carries into the next generation rather than resetting each lifetime. |
| Network reciprocity | Offspring are placed near their parent on the grid, so cooperator clusters persist because children stay put. |
| Group selection | Mating happens preferentially within groups, so a cooperative group's advantage is not diluted by outside genes. |
| Indirect reciprocity | Agents preferentially mate with high-reputation partners, so reputation decides who has offspring together, not only who receives help. |

Ablating the reproductive channel while keeping the energy channel intact
collapses invasion in each of these four (see the per-mechanism ablations
under `utils/proof_of_mechanism.py` in each folder). Direct reciprocity has no
analogous reproductive channel — its assortment is temporal (partner memory),
not genetic — which is consistent with it being the weakest performer of the
five.

## Ecological Nowak Mechanisms Directory Note

On 2026-05-13, `ecological_models/nowak_mechanisms/` was added as a separate
namespace for ecological versions of Nowak's five cooperation mechanisms.

Stepwise impact:

1. The existing `moran_models/nowak_mechanisms/` directory stays untouched as
   the Moran-style reference implementation.
2. The new ecological namespace allows the same mechanisms to be tested with
   life-history dynamics such as sexual reproduction, pedigree relatedness,
   juvenile rearing, survival, dispersal, and group persistence.
3. The first ecological mechanism package is `kin_selection/`, matching the
   existing Moran counterpart by name.
4. These models should be described as Nowak-mechanism ecological models, not
   as Moran models, unless a future implementation explicitly uses a Moran
   update rule.

## Ecological Kin Selection Runtime Note

On 2026-05-13, `kin_selection/` gained the first ecological runtime and
proof-of-mechanism utility.

Stepwise impact:

1. `kin_selection/config/kin_selection_config.py` now defines the active model
   parameters and proof scenarios.
2. `kin_selection/kin_selection_model.py` now implements a non-Moran
   sexual/pedigree/rearing model for kin selection.
3. `kin_selection/utils/proof_of_mechanism.py` now runs ablations for kin
   bias, shuffled relatedness, rearing dependency, unrelated rearing groups,
   care cost, and juvenile dispersal.
4. The Moran counterpart remains untouched and should still be used as the
   abstract fixed-population control.

## Ecological Kin Selection Diagnostic Note

On 2026-05-13, `kin_selection/` was tightened into a rare-helper invasion test
with post-run Hamilton-style diagnostics.

Stepwise impact:

1. The active initial condition now includes rare high-helper founders against
   a low-helper resident background.
2. The model reports realized care relatedness, available relatedness,
   assortment gain, expected juvenile survival benefit, helper cost proxies,
   and a Hamilton-margin proxy.
3. The proof utility now requires both helping-trait increase and rare-helper
   frequency increase, paired with a positive measured margin proxy.
4. The Hamilton-style quantities are measured from the ecological simulation;
   they are not used as the model's update rule.

## Ecological Kin Selection Strong-Control Note

On 2026-05-13, `kin_selection/` gained the stronger controls needed to compare
the ecological model against the Moran investigation.

Stepwise impact:

1. `foster_to_nonparent_group_probability` now lets proof scenarios move
   newborns away from both parents' groups.
2. `unrelated_rearing_groups` tests whether the mechanism still works when
   local rearing no longer pairs juveniles with close kin.
3. The model now counts parent-offspring events for every individual and
   reports observed lifetime reproductive success for rare-helper and resident
   birth classes.
4. The proof table can now separate trait invasion, realized care relatedness,
   individual reproductive cost, and population survival.
