# Summary Table: Moran vs. Ecological Kin Selection Models

| Aspect | Moran Model (Spatial) | Ecological Model |
|--------|----------------------|------------------|
| **Mechanism** | Hard-wired kin recognition (lineage routing) | Demographic structure (limited dispersal, local rearing) |
| **Spread from rare** | 100% (spread_from_rare_kin_bias) | 40% (kin_biased_rearing) |
| **Well-mixed control** | 0% (no spread, even if common) | 0% (unrelated_rearing_groups) |
| **Kin recognition required?** | Yes (removal collapses mechanism) | No (shuffled_relatedness works) |
| **Hamilton's rule** | Sharp threshold (phase transition) | Probabilistic gradient (no hard boundary) |
| **Stochasticity** | Nearly deterministic above threshold | Stochastic; kin clusters must form |
| **What r means** | Assumed (by design) | Emergent (from life cycle) |
| **Biological realism** | Abstract, theoretical baseline | Realistic, shows how r arises |

**Interpretation:**
- The Moran model proves kin selection works if kin recognition exists.
- The ecological model shows kin selection can arise from demographic structure alone, even without kin recognition.

Together, they show kin selection is robust in theory and can emerge in practice from realistic life histories.
# Ecological Kin Selection

This package holds the ecological kin-selection counterpart to
`moran_models/nowak_mechanisms/kin_selection/`.

The intended mechanism is still Nowak's kin selection: helping can evolve when
the actor's cost is outweighed by benefits delivered to genetically related
recipients. The implementation should not start from Moran replacement. It
should start from ecological life history: sexual reproduction, pedigree
relatedness, juvenile rearing, survival, and reproduction.

## Boundary With The Moran Model

The Moran kin-selection model is the abstract control:

- fixed population
- local replacement
- inherited lineage labels
- kin-biased routing of produced benefits

This ecological kin-selection model should test a more human-evolutionary
question:

- can cooperation begin because dependent juveniles survive better when kin
  provide costly care?

## Core Elements

- diploid sexual reproduction
- explicit mother and father links
- close-kin avoidance during mate choice
- optional outside-group mating after the kin filter
- genetic relatedness `r_ij` calculated from inherited alleles
- rare high-helping founder trait class against a low-helping resident baseline
- juvenile stage requiring care before maturity
- adult or elder helpers paying an energy cost to support juveniles
- juvenile survival benefit from received care
- measured post-run diagnostics for realized `r`, recipient benefit `B`, helper
  cost `C`, and a cautious Hamilton-margin proxy
- lifetime reproductive-success accounting by rare-helper versus resident
  birth trait
- controls that remove relatedness bias, rearing dependence, or care benefit
- a fostered-rearing control that moves newborns into non-parent groups

## One Step

Each simulation step updates individuals rather than replacing fixed Moran
sites.

1. Individuals age and update energy.
2. Adults and elders with enough energy allocate care to juveniles in the same
   group.
3. Juveniles survive with probability increased by received care.
4. Surviving juveniles mature into adults at the configured maturity age.
5. Adult females search eligible males, reject close genetic kin, and then
   choose either a same-group or outside-group mate.
6. Density mortality trims the population only if it exceeds the carrying cap.

## Relatedness

The model stores a diploid genome for every individual as `genome_loci` pairs
of inherited allele IDs.

For actor `i` and recipient `j`:

```
r_ij = shared_allele_copies(i, j) / (2 * genome_loci)
```

Variables:

- `r_ij`: genetic relatedness between actor `i` and recipient `j`.
- `shared_allele_copies(i, j)`: number of diploid allele copies that both
  individuals inherited identical-by-descent.
- `genome_loci`: number of independent genetic positions in the simulation.
- `2 * genome_loci`: total diploid allele-copy slots used as the denominator.

Expected values are approximate because Mendelian inheritance is stochastic:

- parent-child: near `0.5`
- full sibling: near `0.5`
- half sibling: near `0.25`
- grandparent-grandchild: near `0.25`
- unrelated founders: near `0`

The proof logic does not treat these values as fixed labels. The life cycle
generates actual genetic relatedness first, then the model measures realized
relatedness among helper-recipient care interactions.

## Rare Helper Setup

The default initial condition is a rare-helper invasion test. Most founders
draw `h_i` from a low resident range:

```
h_i ~ Uniform(initial_helping_trait_min, initial_helping_trait_max)
```

Variables:

- `h_i`: inherited helping trait of individual `i`.
- `initial_helping_trait_min`: lower bound of the resident trait range.
- `initial_helping_trait_max`: upper bound of the resident trait range.

A small founder fraction instead receives:

```
h_i = rare_helper_trait_value
```

Variables:

- `rare_helper_founder_probability`: probability that a founder begins as a
  rare high-helper.
- `rare_helper_trait_value`: high-helper trait value assigned to those rare
  founders.
- `helping_trait_invasion_threshold`: threshold used to report the frequency
  of high-helper descendants.

This makes the main outcome two-part: mean `h` should rise, and the fraction
of individuals above `helping_trait_invasion_threshold` should rise.

## Mate Choice

Rearing is local, but mating is not forced to stay inside the group. The model
first filters candidate males by genetic relatedness:

```
eligible_male(i, j) = r_ij <= max_mate_relatedness
```

Variables:

- `i`: reproducing female.
- `j`: candidate male.
- `r_ij`: genetic relatedness between the female and candidate male.
- `max_mate_relatedness`: highest allowed mate relatedness.

With the default `max_mate_relatedness = 0.10`, the model rejects close kin
such as parents, offspring, siblings, half siblings, and most first-cousin-like
pairings. After this filter, the female can choose a same-group eligible male
or an outside-group eligible male. The parameter
`same_group_mate_preference_probability` controls that preference when both
candidate pools exist.

This separates the two biological roles:

- local kin availability can still support juvenile rearing
- mate choice avoids close inbreeding and allows gene flow between groups

## Care Rule

For helper `i` and juvenile `j`, the care weight is:

```
weight_ij = care_baseline_weight + kin_bias_strength * r_ij
```

Variables:

- `weight_ij`: relative share of helper `i`'s care budget assigned to juvenile
  `j`.
- `care_baseline_weight`: small non-kin baseline so care is not impossible when
  relatedness is low.
- `kin_bias_strength`: strength of preferential care toward relatives.
- `r_ij`: genetic relatedness between helper and juvenile.

The helper's total care budget is:

```
care_budget_i = h_i * care_capacity_per_helper
```

Variables:

- `h_i`: helper `i`'s inherited helping trait in `[0, 1]`.
- `care_capacity_per_helper`: maximum care supplied by a helper with `h_i = 1`.

Care costs energy:

```
energy_i -= care_cost_per_unit * care_budget_i
```

Juvenile survival rises with received care:

```
P_survive_j = base_juvenile_survival_probability
              + care_benefit_to_survival * min(total_care_j, care_saturation)
```

Variables:

- `P_survive_j`: juvenile `j`'s survival probability for the current step.
- `total_care_j`: total care received by juvenile `j`.
- `care_saturation`: cap where extra care no longer gives extra survival.
- `care_benefit_to_survival`: survival gain per care unit before saturation.

## Measured Diagnostics

The simulation measures the ingredients of a Hamilton-style interpretation
after the ecological events occur.

Care-relatedness:

```
mean_care_relatedness = sum(care_ij * r_ij) / sum(care_ij)
```

Variables:

- `care_ij`: care units delivered from helper `i` to juvenile `j`.
- `r_ij`: realized genetic relatedness between helper `i` and juvenile `j`.

Available relatedness:

```
mean_available_care_relatedness = sum(uniform_care_ij * r_ij) / sum(uniform_care_ij)
```

Variables:

- `uniform_care_ij`: the care helper `i` would have delivered to juvenile `j`
  if care were spread evenly among same-group juveniles.

Assortment from care targeting:

```
care_assortment_gain = mean_care_relatedness - mean_available_care_relatedness
```

Recipient benefit:

```
B_step = sum(P_survive_with_care_j - P_survive_without_care_j)
```

Variables:

- `B_step`: expected extra juvenile survivals caused by care during one step.
- `P_survive_with_care_j`: survival probability of juvenile `j` after care.
- `P_survive_without_care_j`: survival probability of juvenile `j` without
  the care benefit.

Immediate helper cost proxy:

```
C_step = expected lost births from female helpers pushed below reproduction energy
```

This is not the full lifetime cost of helping. It is a conservative immediate
direct-fitness proxy that is measured in expected births. The model also
reports the raw helper energy cost.

Lifetime reproductive success:

```
LRS_i = total offspring produced by individual i
```

Variables:

- `LRS_i`: observed lifetime reproductive success of individual `i`.
- `total offspring produced`: count of births for which `i` was mother or
  father.

The proof utility reports mean observed `LRS_i` for individuals born above the
high-helper threshold and for resident-background individuals. This is still
censored by finite simulation time, but it exposes whether rare helpers are
paying an individual reproductive cost while the heritable helping trait
spreads through relatives.

Hamilton-margin proxy:

```
margin_step = sum(weighted_r_j * benefit_j) - C_step
```

Variables:

- `weighted_r_j`: care-weighted relatedness of the helpers who supported
  juvenile `j`.
- `benefit_j`: expected survival-probability gain for juvenile `j`.
- `C_step`: immediate expected helper reproduction cost.

This margin is a diagnostic, not an assumed rule. A positive margin is useful
only when paired with actual invasion of the rare helping trait.

## Run

From the repo root:

```bash
./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.kin_selection_model
```

For the live Pygame grid viewer:

```bash
./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.kin_selection_pygame_ui
```

The active parameters live in:

```text
ecological_models/nowak_mechanisms/kin_selection/config/kin_selection_config.py
```

The model writes the latest active run to:

```text
ecological_models/nowak_mechanisms/kin_selection/data/latest_run.json
```

The live viewer uses a group-grid layout because this ecological model has no
spatial coordinates. Each block is one group, and each filled cell is one living
individual. The viewer has four modes:

- `Trait`: helping trait `h`
- `Stage`: juvenile, adult, elder
- `Group`: group identity
- `Energy`: current energy level

Controls:

- `Space`: play or pause
- `S` or right arrow: single step
- `R`: reset
- `V`: cycle view mode
- `1` to `4`: choose a view mode directly
- `+` / `-`: change FPS

## Proof Utility

Run the ablation suite from the repo root:

```bash
./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.utils.proof_of_mechanism
```

The configured scenarios are:

- `kin_biased_rearing`
- `no_relatedness_bias`
- `shuffled_relatedness`
- `no_rearing_dependency`
- `unrelated_rearing_groups`
- `cost_too_high`
- `high_juvenile_dispersal`

The mechanism is supported when the kin-biased rearing scenario shows all of
the following:

1. mean helping trait increases
2. high-helper frequency increases from rare
3. measured relatedness-weighted benefit exceeds the immediate cost proxy
4. the pattern weakens or fails when relatedness bias, rearing dependency,
   or local kin availability is broken

The `shuffled_relatedness` control randomizes the relatedness cue used for care
targeting. If it still performs well, that means local group kin structure
alone is doing some work; it is not evidence for kin recognition specifically.

The `unrelated_rearing_groups` control sets
`foster_to_nonparent_group_probability = 1.0`, so newborns are reared away from
both parents' groups. This is the stronger control for local kin availability:
if it fails, the default result depends on juveniles actually being near
relatives during the rearing stage.

## Static Visuals

Generate PNG plots from the latest model and proof outputs:

```bash
./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.utils.plot_latest_run
```

The plotting utility reads:

- `data/latest_run.json`
- the latest `data/ecological_kin_selection_proof_*_summary.csv`

It writes:

- `data/latest_run_trajectory.png`
- `data/latest_proof_summary.png`

## Simulation Conclusions

Running the ablation proof suite yields two main findings.

### Kin selection can amplify cooperation from rare

In the `kin_biased_rearing` scenario (full mechanism), the high-helper invasion
frequency rises from ~4% to ~78% in 2 out of 5 replicates, with a positive
Hamilton-margin proxy throughout. Rare helpers pay a real individual reproductive
cost — their lifetime offspring count is roughly half that of residents — yet the
helping trait spreads through the population via its benefit to kin.

The mechanism requires two structural conditions:

- Juveniles must depend on care for survival (`no_rearing_dependency` fails
  immediately at success rate 0.0).
- Juveniles must be reared near relatives (`unrelated_rearing_groups` collapses
  the population entirely, care relatedness drops to ~0.025).

### The amplification is driven by demographic structure, not kin recognition

The `shuffled_relatedness` control randomizes the relatedness cues used for care
targeting so helpers cannot preferentially identify relatives. It succeeds at the
same rate (0.4) with nearly the same effect size (+0.066 vs +0.073 trait change).

The reason is that the available care relatedness within groups is already ~0.21
from the life cycle alone (limited dispersal, offspring placed in the mother's
group, repeated reproduction within bands). Active kin targeting adds only +0.009
on top of that baseline. The demographic structure is doing the heavy lifting;
explicit kin recognition is a small refinement.

This is the viscous-population version of kin selection that Hamilton identified:
you do not need to know who your relatives are if your relatives are simply the
individuals around you. The r in rB > C comes from limited dispersal generating
local kin clusters, not from helpers identifying high-r recipients.

## How Cooperation Evolved in Humans

This model captures one proposed stage of a multi-stage process. No single
mechanism explains the full breadth of human cooperation.

### Stage 1 — Kin selection and cooperative breeding (what this model captures)

Early hominids lived in small bands with limited dispersal, exactly the
viscous-population conditions the simulation demonstrates. The human-specific
factor is cooperative breeding (Hrdy): humans have an unusually costly life
history in which dependent juveniles overlap before older siblings are
independent, and mothers cannot provision all of them alone. Post-menopausal
grandmothers and other co-residing kin remained productive helpers. This created
strong selection pressure for prosocial psychology among group members. Kin
selection via demographic structure — not recognition — is a plausible mechanism
for this phase.

### Stage 2 — Reciprocal altruism among non-kin

As bands grew and individuals interacted repeatedly, direct reciprocity (Trivers
1971) extended cooperation beyond relatives. The condition is that individuals
meet again: if the probability of future interaction is high enough, cooperation
with non-kin can be evolutionarily stable. This is the direct-reciprocity
mechanism modelled elsewhere in this repository.

### Stage 3 — The scale problem

Modern humans cooperate in armies, cities, and anonymous markets with strangers
they will never meet again, at scales of millions. Kin selection (r ≈ 0 for
strangers) and direct reciprocity (no repeated interaction) cannot reach this
scale. The leading explanations are:

- **Altruistic punishment / strong reciprocity** (Fehr and Gächter): humans
  punish norm violators at personal cost, even anonymously. This stabilises
  cooperation in large groups because defection becomes costly regardless of
  whether the victim can retaliate.
- **Cultural group selection** (Boyd and Richerson): groups with
  cooperation-enforcing norms outcompeted groups without them. Selection acted
  on cultural variants — norms, institutions, religions — faster than on genes.
  Cultural inheritance can create group-level heritability even when genetic
  relatedness is low.
- **Gene-culture coevolution**: cultural norms fed back to create genetic
  selection for prosocial psychology, language, and theory of mind — the
  cognitive infrastructure that makes large-scale cooperation possible.

### Summary

| Scale | Primary mechanism |
|---|---|
| Small kin bands | Kin selection via demographic structure |
| Repeated dyads | Direct reciprocity |
| Reputation networks | Indirect reciprocity |
| Large anonymous groups | Norms, punishment, cultural institutions |

This model addresses the first row. The open debate concerns how much weight to
give genetic versus cultural selection in the later transitions.

## Ecological Kin Selection Scaffold Note

On 2026-05-13, `ecological_models/nowak_mechanisms/kin_selection/` was added as
the ecological counterpart to the Moran kin-selection wrapper.

Stepwise impact:

1. The package exists separately from the Moran implementation, so the
   existing Nowak/Moran investigation remains untouched.
2. The folder name matches the Moran counterpart for one-to-one comparison.
3. The initial scaffold named the planned sexual/pedigree/rearing
   kin-selection model before runtime code was added.
4. Future implementation should keep configuration in this package's config
   file as the source of truth and should validate the mechanism with explicit
   ablation tests.

## Ecological Kin Selection Runtime Note

On 2026-05-13, the package gained the first runtime model and proof utility.

Stepwise impact:

1. `config/kin_selection_config.py` is now the source of truth for active
   parameters and proof scenarios.
2. `kin_selection_model.py` now implements sexual reproduction, diploid
   inheritance, genetic relatedness, juvenile rearing, helper energy costs,
   juvenile survival benefits, reproduction, dispersal, and density mortality.
3. `utils/proof_of_mechanism.py` now runs the configured ablation scenarios and
   writes replicate and summary CSV files under `data/`.
4. The implementation remains an ecological Nowak-mechanism model rather than
   a Moran model: selection acts through survival and reproduction, not fixed
   population replacement.

## Ecological Kin Selection Visuals Note

On 2026-05-13, the package gained static Matplotlib visual exports for the
latest ecological kin-selection outputs.

Stepwise impact:

1. `utils/plot_latest_run.py` now reads the latest JSON run and proof summary
   CSV without command-line parameters.
2. `data/latest_run_trajectory.png` shows population structure, helping-trait
   evolution, juvenile survival, care relatedness, kin-care fraction, and total
   care over time.
3. `data/latest_proof_summary.png` compares proof scenarios by helping-trait
   change and care targeting.
4. These visuals are diagnostic artifacts only; the config file remains the
   source of truth for simulation and proof settings.

## Ecological Kin Selection Live Viewer Note

On 2026-05-13, the package gained a live Pygame viewer for the ecological
kin-selection model.

Stepwise impact:

1. `kin_selection_pygame_ui.py` now runs the active config in an interactive
   window.
2. The viewer packs individuals into group blocks rather than adding spatial
   coordinates to the model.
3. View modes show helping trait, life stage, group identity, and energy.
4. The sidebar plots mean helping, care relatedness, kin-care fraction, and
   population relative to the cap while the simulation runs.
5. Viewer dimensions and speed defaults are configured in
   `config/kin_selection_config.py`.

## Ecological Kin Selection Kin-Avoidant Mating Note

On 2026-05-13, sexual reproduction was revised to avoid biologically unrealistic
close-kin mating.

Stepwise impact:

1. `config/kin_selection_config.py` now includes `max_mate_relatedness` and
   `same_group_mate_preference_probability`.
2. `kin_selection_model.py` now filters candidate fathers by genetic
   relatedness before choosing a mate.
3. Same-group mating is still possible only when the male is not too closely
   related to the female.
4. Outside-group mating is now possible and is tracked as
   `outside_group_mating_fraction`.
5. The model now keeps the intended biological separation: local kin can help
   rear juveniles, while mating avoids close kin.

## Grafen/Relatedness Diagnostic Note

On 2026-05-13, the model was revised after reviewing Alan Grafen's
`A geometric view of relatedness` in `/home/doesburg/Downloads/oseb.pdf`.

Stepwise impact:

1. The default initial condition now tests invasion from a rare high-helping
   founder trait class rather than broad resident variation alone.
2. Relatedness remains generated by diploid inheritance and the model now
   records realized relatedness among actual care interactions.
3. The proof utility now reports finite measured diagnostics for realized care
   relatedness, available relatedness, care-assortment gain, expected juvenile
   survival benefit, immediate helper reproduction-cost proxy, helper energy
   cost, and a Hamilton-margin proxy.
4. Hamilton's rule is treated as an after-the-run diagnostic, not as the
   mechanism hard-coded into the simulation.

## Ecological Kin Selection Strong-Control Note

On 2026-05-13, the proof was extended with lifetime reproductive-success
accounting and a stronger unrelated-rearing control.

Stepwise impact:

1. `foster_to_nonparent_group_probability` can now place newborns into groups
   containing neither parent, breaking the local kin-rearing channel.
2. `unrelated_rearing_groups` was added to the proof scenarios as the hard
   control for local kin availability.
3. The model now records parent-offspring counts for every individual and
   reports observed lifetime offspring for rare-helper versus resident birth
   classes.
4. The latest proof summary reports that kin-biased rearing still amplifies
   rare helpers in some seeds, while unrelated rearing groups fail and show
   near-zero care relatedness.
