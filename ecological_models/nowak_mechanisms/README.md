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

Each folder should make clear which Nowak mechanism is being tested and which
ecological machinery is being added.

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
