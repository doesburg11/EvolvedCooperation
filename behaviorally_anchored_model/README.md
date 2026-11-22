# Behaviorally Anchored Model

This package is the canonical Python implementation for the small-scale
family/foraging-band layer described on:

<https://humanbehaviorpatterns.org/history-of-human-cooperation-and-competition>

The website page gives the historical target capacities. This package tests
which of those capacities are load-bearing inside a demographic simulation.

Implemented capacities:

1. Repeated interaction through persistent reciprocity bonds and bond memory.
2. Reputation-sensitive help routing and reputation-weighted mate choice.
3. Norm enforcement through energy penalties for low-reputation adults.
4. Group boundaries through concrete residential bands, migration,
   fission/fusion, inter-band marriage, territorial exclusion, soft avoidance,
   and costly resource raids.
5. Kin, spouse, household, parent provisioning, and alloparental child care.
6. Ecological pressure through local grass depletion, survival, reproduction,
   and soft density pressure.
7. Social learning through bounded within-lifetime copying of nearby
   adult/elder demonstrators.

Current scope:

- The model covers the foraging-band and family ecology emphasized by the
  historical page.
- Space is bounded, not toroidal: agents, households, bands, grass harvest, and
  bond distances all use the displayed landscape instead of wrapping across
  opposite edges.
- Territoriality is intentionally weak and mobile: overlapping bands usually
  drift apart or displace rather than defend fixed property, and local resource
  scarcity makes contests more likely and more costly.
- Competing bands now exclude foreign members and household residence points
  from their territory, so band territories are active ranges rather than only
  visual circles.
- Inter-band raids are lossy resource transfers rather than free winner
  bonuses: defenders lose surplus energy, attackers receive only part of it,
  and attackers pay direct cost plus injury risk.
- Grass ecology is tuned to make scarcity more visible: patches hold less
  energy and recover more slowly, while foraging gains are left unchanged.
- Lethal violence is modeled as rare scarcity-gated raid mortality during
  territorial contests, mostly exposing subadult/adult males and capped so a
  single raid does not automatically delete a whole band.
- Band migration is conditional rather than random churn: individuals are more
  likely to migrate when outside their band territory or when local grass is
  scarce, and target bands are weighted by available grass.
- Households have weak short-range spacing, so camp residence points repel when
  they get too close instead of letting every household collapse into one blob.
- It does not model later institutional mechanisms such as agriculture,
  property law, money, writing, bureaucracy, states, markets, or formal
  education.
- Inherited cooperation is stored as `helping_trait`.
- Learned behavior is stored separately as `learned_helping_adjustment`.
- Effective cooperative behavior is
  `clamp01(helping_trait + learned_helping_adjustment)`.
- Offspring inherit the genetic `helping_trait`, not the learned adjustment.

Run from the repository root:

```bash
./.conda/bin/python -m behaviorally_anchored_model.behaviorally_anchored_model
```

Run the proof scenarios:

```bash
./.conda/bin/python -m behaviorally_anchored_model.utils.proof_of_mechanism
```

Run the live viewer:

```bash
./.conda/bin/python -m behaviorally_anchored_model.utils.live_viewer
```

## Current Status

	- cooperation is represented by a continuous inherited `helping_trait`
	- social learning is represented separately as a bounded within-lifetime
	  `learned_helping_adjustment`; actions use effective helping
	  `clamp01(helping_trait + learned_helping_adjustment)`, while offspring
	  inherit only the genetic `helping_trait`
	- the viewer separates mean helping trait from the frequency above the
	  invasion threshold, so `Trait >= 0.10 = 100%` can coexist with a mean trait
	  near `0.25`
	- the viewer now also reports realized help: the fraction of actual helping
	  opportunities in the latest step that produced help
		- `group_id` now stores concrete band membership: bands have territory
		  centers, weak member attraction, migration, fission/fusion,
		  inter-band marriage, soft territorial avoidance, territorial
		  exclusion, and lossy resource raids
		- life history now separates dependent juveniles, non-reproductive
		  subadults, reproductive adults, and elders; default biological adulthood
		  starts at age `18`
		- agents now move during life through a stage-specific local random walk, so
		  spatial neighborhoods change through both movement and birth/death turnover
	- child rearing is now explicit: adults and elders can invest costly care in
	  nearby juveniles, with parent and kin relatedness biasing who receives care
	- reproductive co-parents can form persistent spouse bonds; spouse bonds can
	  bias repeat mating, seed local reciprocity bonds, and strengthen care for
	  shared nearby children
		- households now act as co-resident family/camp units with a residence point;
		  members are pulled toward that residence, juveniles can receive a household
		  survival bonus from living parents and adult caregivers, and maturing
		  juveniles can disperse into new households
		- local grass is now explicit: adults and elders harvest from nearby grass
		  cells instead of receiving guaranteed adult food energy, and parents can
		  pass surplus harvested food to their own nearby juveniles
		- reciprocity bonds are spatially local: new bonds form only within the
		  configured formation radius, and existing bonds dissolve if movement
		  carries bondmates beyond the configured dissolution radius
		- population regulation now uses soft density pressure rather than a hard
		  random trim to exactly the target population

## Change Log

Moved here from the repository README on 2026-11-22. Newest first.

### 2026-05-16 Behaviorally Anchored Rename, Website Mapping, and Social Learning Update

Stepwise impact:

1. The former `top_down_model/` package was renamed to
   `behaviorally_anchored_model/` to match the public website's behaviorally
   anchored terminology.
2. The core runtime file was renamed from `top_down_model.py` to
   `behaviorally_anchored_model.py`, and the active config file was renamed
   from `top_down_config.py` to `behaviorally_anchored_config.py`.
3. Runtime commands now use:
   `./.conda/bin/python -m behaviorally_anchored_model.behaviorally_anchored_model`.
4. The model now references the website counterpart page directly:
   <https://humanbehaviorpatterns.org/history-of-human-cooperation-and-competition>.
5. The website page now links back to the canonical implementation path in this
   repository, so page and model can be checked against each other.
6. Social learning is now explicit: subadults, adults, and elders can copy
   nearby adult/elder demonstrators weighted by reputation and energetic
   success.
7. Social learning updates `learned_helping_adjustment`, a bounded
   within-lifetime offset. It changes behavior without rewriting inherited
   `helping_trait`, keeping cultural/individual learning distinct from genetic
   inheritance.
8. Effective helping now drives cooperation probability, helping cost,
   child-care investment, reproduction cost pressure, and band raid force.
9. New config keys include `social_learning_probability`,
   `social_learning_radius`, `social_learning_rate`,
   `social_learning_reputation_weight`, `social_learning_success_weight`, and
   `social_learning_max_adjustment`.
10. The proof utility now includes `no_social_learning` and
    `social_learning_only` scenarios, and reports effective helping plus social
    learning events.
11. The live viewer now reports effective helping and social-learning activity
    alongside inherited mean helping trait.

### 2026-05-16 Soft Hunter-Gatherer Territorial Competition Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now
   defines soft territorial competition controls:
   `territorial_overlap_start_fraction`, `territorial_avoidance_strength`,
   `territorial_scarcity_threshold`, `territorial_conflict_probability`,
   `territorial_conflict_scarcity_weight`,
   `territorial_conflict_energy_penalty`, and
   `territorial_displacement_distance`.
2. Bands now measure overlap between their territory circles and local grass
   availability inside those territories.
3. When bands overlap beyond the configured threshold, they usually drift apart
   through avoidance rather than treating territory as hard property.
4. Direct territorial contests require both overlap and local grass scarcity,
   so conflict remains rare when resources elsewhere make avoidance feasible.
5. Territorial contests impose an energy penalty and displacement on the losing
   band rather than immediate mortality or permanent exclusion.
6. The model now records territorial overlap pairs, mean territorial overlap,
   avoidance events, territorial conflicts, territorial displacements, and
   cumulative conflict/displacement totals.
7. The live viewer now displays territorial overlap, avoidance, conflict, and
   displacement metrics so band competition is visible during a run.

### 2026-05-16 Behaviorally Anchored Camp Spacing and Conditional Migration Update

Stepwise impact:

1. Random per-step band migration is no longer unconditional. The configured
   `group_migration_probability` now acts as the maximum migration probability,
   and actual migration requires ecological pressure.
2. Migration pressure rises when an individual is outside its current band
   territory or when local grass around the individual is scarce relative to
   `territorial_scarcity_threshold`.
3. Migration target choice now weights candidate bands by local grass
   availability around the target band, so movement is more likely to pull
   people toward better foraging territory rather than merely toward nearby
   bands.
4. `interband_marriage_preference` and `interband_marriage_distance` were
   reduced so inter-band marriage remains possible but no longer overwhelms
   residential band structure.
5. `band_member_attraction` was reduced so band territories guide long-range
   belonging without pulling all members into a central point.
6. Households now have short-range camp spacing through
   `household_spacing_radius` and `household_spacing_strength`. Household
   residences repel each other when too close, which addresses individual camp
   clustering without deleting small bands or adding hard territorial killing.

### 2026-05-16 Behaviorally Anchored Scarcity-Gated Raid Mortality Update

Stepwise impact:

1. Territorial contests can now cause lethal raid casualties, but only after
   the existing overlap-and-scarcity conflict gate has already produced a
   territorial contest.
2. New config keys define this mechanism:
   `territorial_raid_mortality_probability`,
   `territorial_raid_mortality_scarcity_weight`,
   `territorial_raid_mortality_size_imbalance_weight`,
   `territorial_raid_mortality_adult_male_weight`,
   `territorial_raid_mortality_other_weight`, and
   `territorial_raid_mortality_max_loser_fraction`.
3. Raid mortality is applied to the losing band only. Subadult/adult males have
   the highest exposure by default; other non-juvenile members can still be at
   lower risk.
4. Mortality risk increases with scarcity and winner-loser size imbalance, and
   a per-raid cap prevents one contest from automatically erasing an entire
   band.
5. Juveniles are not direct raid targets under the default rule; they can still
   be affected indirectly when parents or caregivers die.
6. The model now records `territorial_raid_deaths` and
   `cumulative_territorial_raid_deaths`.
7. The live viewer now reports cumulative raid deaths in the side panel, and
   the command-line summary includes raid deaths in the territorial statistic.

### 2026-05-16 Behaviorally Anchored Bounded Space and Competitive Band Exclusion Update

Stepwise impact:

1. `behaviorally_anchored_model/behaviorally_anchored_model.py` no longer treats
   the spatial world as a torus. Individual, household, band, offspring, and
   fission positions are clamped inside the bounded landscape.
2. Spatial distances for movement, mate choice, reciprocity bonds, social
   learning, child care, food transfer, territorial overlap, and reproduction
   now use direct bounded Euclidean distance instead of wrapped shortest-path
   distance.
3. Grass harvesting no longer wraps across the edge of the grid. Foragers near
   a boundary harvest only cells that actually exist inside the landscape.
4. Competing bands now actively exclude foreign members found inside their
   territory. Intruding individuals are displaced away from the visited band
   center and non-juvenile intruders pay a small energy penalty.
5. Territorial overlap can now produce occasional direct contests even before
   severe scarcity; local grass scarcity still raises the chance and cost of
   those contests.
6. Household residence points also get pushed out of foreign band territories,
   making camps follow band boundaries instead of sitting passively inside a
   competitor's range.
7. The model records `territorial_exclusions` and
   `cumulative_territorial_exclusions`, and the command-line territorial
   statistic is now overlap/avoidance/exclusion/conflict/death.
8. `behaviorally_anchored_model/utils/live_viewer.py` now draws band
   territories and bond lines only once in bounded screen space. Circles and
   lines no longer reappear across the opposite edge.

### 2026-05-16 Behaviorally Anchored Lossy Resource Raid Update

Stepwise impact:

1. `_apply_group_conflict()` was replaced by `_apply_resource_raids()` in
   `behaviorally_anchored_model/behaviorally_anchored_model.py`.
2. The old shortcut parameters `conflict_winner_bonus` and
   `conflict_loser_penalty` were removed. The model no longer creates winner
   energy separately from loser loss.
3. New config keys define the ecological raid rule:
   `raid_min_combatants`, `raid_base_probability`, `raid_scarcity_weight`,
   `raid_force_advantage_weight`, `raid_defender_energy_reserve`,
   `raid_steal_fraction`, `raid_transfer_efficiency`,
   `raid_attacker_cost_per_combatant`, `raid_attacker_injury_probability`,
   `raid_defender_injury_probability`, and `raid_injury_energy_cost`.
4. Raids are local: they can occur only between overlapping band territories
   and only when both bands have enough non-juvenile combatants.
5. Defender energy loss is bounded by surplus above
   `raid_defender_energy_reserve`; attackers receive only
   `raid_transfer_efficiency` of stolen energy, so part of the stolen resource
   is wasted.
6. Attackers pay direct energetic costs and can be injured, so raiding is not a
   free winner bonus. Defenders can also be injured.
7. The model now records resource-raid events, stolen energy, attacker gain,
   attacker cost, and injuries in both latest-step and cumulative metrics.
8. The live viewer now reports cumulative raid transfer and raid risk in the
   side panel.

### 2026-05-16 Behaviorally Anchored Scarcer Grass Tuning Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now makes
   the local grass ecology less abundant without changing the foraging gain
   parameters.
2. `grass_regrowth_per_step` was reduced from `0.18` to `0.07`, so depleted
   patches recover more slowly after clustered foraging.
3. `grass_max_per_cell` was reduced from `2.0` to `1.5`, lowering the carrying
   capacity of each grass patch.
4. `grass_initial_fraction` remains `1.0`, so the model still starts with a full
   landscape; scarcity now emerges from depletion and slower recovery rather
   than from an immediately poor initial condition.
5. Adult, elder, and subadult foraging gains were intentionally left unchanged,
   so changes in migration, child food, raids, and juvenile survival can be
   attributed to the resource ecology rather than a simultaneous foraging
   rewrite.

### 2026-05-15 Behaviorally Anchored Grass Foraging and Parent Food Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now defines a local grass ecology:
   `grass_grid_size`, `grass_max_per_cell`, `grass_initial_fraction`,
   `grass_regrowth_per_step`, and `grass_harvest_radius`.
2. `behaviorally_anchored_model/behaviorally_anchored_model.py` now initializes a bounded grass grid and
   regrows grass each step before foraging.
3. Subadult, adult, and elder `*_foraging_energy_gain` parameters now act as
   maximum grass harvest per step. They are no longer unconditional energy added
   from nowhere.
4. Harvesting uses a local radius around the forager, so clustered households can
   deplete nearby grass even when grass elsewhere in the world remains available.
5. Parents then keep an energy reserve
   (`parent_food_transfer_energy_reserve`) and distribute surplus food up to
   `parent_food_transfer_capacity` to their own juvenile children within
   `parent_food_transfer_radius`.
6. Parent food allocation is weighted by proximity and by shared household
   membership through `parent_food_transfer_household_weight_bonus`.
7. The kin/household ablation now disables parent surplus feeding by setting
   `parent_food_transfer_capacity` to `0`, while grass itself remains part of the
   background ecology.
8. The model now records `mean_grass_fraction`, `grass_harvest`,
   `parent_food_transfer`, `fed_juvenile_count`, and
   `fed_juvenile_fraction`.
9. `behaviorally_anchored_model/utils/live_viewer.py` now supports `g` for the grass
   background and reports grass availability, harvested grass, and food passed
   to juveniles in the side panel.

### 2026-05-15 Behaviorally Anchored Food Survival and Fertility Tuning Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now defines
   `juvenile_food_survival_benefit`,
   `juvenile_food_survival_saturation`, and
   `juvenile_no_food_survival_penalty`.
2. Juvenile survival in `behaviorally_anchored_model/behaviorally_anchored_model.py` now includes a
   saturating food term from actual parent food received in the current step.
   Fed juveniles receive a survival boost; unfed juveniles receive a small
   penalty.
3. The model now records `mean_juvenile_food_survival_effect`, so the net
   survival contribution of parent feeding is visible in history and summaries.
4. Parent provisioning was retuned to be visible under the longer childhood:
   `parent_food_transfer_capacity = 0.90`,
   `parent_food_transfer_energy_reserve = 6.0`, and
   `parent_food_transfer_radius = 24.0`.
5. Fertility and energetic thresholds were retuned after adding human-length
   childhood: `female_reproduction_probability = 0.90`,
   `reproduction_energy_threshold = 3.5`, `reproduction_energy_cost = 0.6`,
   and `child_energy = 4.0`.
6. Adult and elder grass harvest ceilings were increased to `0.40` and `0.24`
   respectively so adults can support replacement under local resource
   depletion.
7. `base_juvenile_survival_probability` is now `0.88`; food and care still
   modulate survival, but the baseline no longer collapses just because children
   remain dependent longer.
8. `behaviorally_anchored_model/behaviorally_anchored_model.py` now records stage counts:
   `juvenile_count`, `subadult_count`, `adult_count`, and `elder_count`.
9. `behaviorally_anchored_model/utils/live_viewer.py` now reports stage composition as
   `Stages J/S/A/E` and shows the latest food survival effect as `Food surv`.

### 2026-05-15 Behaviorally Anchored Fed-Juvenile Overlay Update

Stepwise impact:

1. `behaviorally_anchored_model/utils/live_viewer.py` now has a separate fed-juvenile overlay
   controlled by `f`.
2. The existing `c` control still toggles gold child-care rings only.
3. Juveniles that received parent food in the latest step now receive a cyan
   ring, scaled by food amount.
4. Care and food can now be inspected independently, so alloparental care and
   parent provisioning are no longer visually conflated.
5. The viewer legend now distinguishes `Gold ring = received care this step`
   from `Cyan ring = received parent food`.

### 2026-05-15 Behaviorally Anchored Viewer Chart Layout Update

Stepwise impact:

1. `behaviorally_anchored_model/utils/live_viewer.py` now places the readable legend in the
   lower-left of the side panel.
2. The viewer window and side panel are wider, so charts can sit to the right of
   the legend instead of forcing compact labels.
3. The existing mean-helping-trait chart now sits at the top of the right-side
   chart stack.
4. `behaviorally_anchored_model/behaviorally_anchored_model.py` now records per-band population counts
   as `band_<id>_count`, with dynamic IDs when fission creates new bands.
5. `behaviorally_anchored_model/utils/live_viewer.py` now draws a second chart for band
   sizes beneath the mean-helping-trait chart, using the band colors as line
   colors.
6. The legend keeps readable labels such as `Band 0`,
   `Gold ring = received care this step`, `Cyan ring = received parent food`,
   and `Square = household residence`.

### 2026-05-15 Behaviorally Anchored Band Territory and Fission/Fusion Update

Stepwise impact:

1. `behaviorally_anchored_model/behaviorally_anchored_model.py` now adds explicit `Band` objects with
   territory centers and territory radii. The existing `group_id` individual
   field is retained as the storage slot for band membership.
2. `n_groups` now seeds the initial number of bands instead of only defining
   abstract color groups.
3. Founder families are initialized around band territories, so the starting
   population has spatially concrete residential bands from step `0`.
4. Movement now includes a weak attraction toward the individual's band
   territory through `band_member_attraction`, in addition to the existing
   household residence attraction.
5. Band territory centers update toward their current subadult/adult/elder
   members through `band_territory_update_weight`, so bands can move as their
   members move.
6. `group_migration_probability` is now interpreted as per-step individual
   migration between bands for agents at least `band_migration_min_age`, rather
   than random newborn group reassignment.
7. Large bands can fission using `band_fission_interval`,
   `band_fission_size_threshold`, `band_fission_min_size`, and
   `band_fission_dispersal_std`; small bands can fuse with nearby bands using
   `band_fusion_interval`, `band_fusion_size_threshold`, and
   `band_fusion_distance`.
8. Mate choice now includes inter-band marriage: different-band fathers receive
   an additional mate-choice weight when the two bands or the two individuals
   are close enough under `interband_marriage_distance`.
9. When an inter-band spouse joins the mother's household, the father migrates
   into the mother's band, making marriage a migration pathway as well as a
   reproduction pathway.
10. Spouse bonds are now stable while both spouses are alive, so births no
    longer constantly overwrite living spouse bonds. The inter-band marriage
    counter increments only when a new cross-band spouse bond forms.
11. The model now records `band_count`, `mean_band_size`, `band_migrations`,
    `band_fissions`, `band_fusions`, `interband_marriages`, and dynamic
    `band_<id>_count` histories, plus cumulative totals for migration,
    fission, fusion, and inter-band marriage.
12. `behaviorally_anchored_model/utils/live_viewer.py` now labels these identities as
    bands, draws optional band territory outlines with `t`, reports band event
    counters, and plots dynamic band-size histories.

### 2026-05-15 Behaviorally Anchored Human Age-Structure Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now replaces the compressed
   `juvenile_maturity_age = 5` life history with `juvenile_dependency_age = 12`
   and `adult_maturity_age = 18`.
2. `behaviorally_anchored_model/behaviorally_anchored_model.py` now has a fourth life stage,
   `subadult`, for ages between dependent childhood and biological adulthood.
3. Default stage ranges are now: juvenile `0-11`, subadult `12-17`, adult
   `18-54`, and elder `55-84`.
4. Female reproduction now starts at age `18`, and male reproduction now starts
   at age `20`, so age `5-6` agents can no longer reproduce.
5. Founder adults now start between ages `18` and `36`, and initial dependent
   children now start between ages `0` and `11`.
6. Subadults can move, remain attached to households, survive with their own
   stage probability, and harvest grass at a lower rate than adults.
7. Subadults do not reproduce, do not provide full child-care investment, and do
   not count as adult/elder anchors for household residence updates.
8. Adult household dispersal now happens when a juvenile/subadult first becomes
   an adult at `adult_maturity_age`.
9. `behaviorally_anchored_model/utils/live_viewer.py` now renders subadults as an
   intermediate dot size between dependent juveniles and adults.
10. Under the fertility retuning above, `no_kin_selection` remains
    demographically viable; it disables kin, spouse, household, child-care, and
    parent-food channels without making population collapse the expected result.

### 2026-05-15 Behaviorally Anchored Household Ecology Update

Stepwise impact:

1. `behaviorally_anchored_model/behaviorally_anchored_model.py` now has explicit `Household` objects and
   every individual carries a `household_id`.
2. Founder pairs start in the same household, and each household has a residence
   point that updates toward its adult/elder members.
3. Movement now combines individual random walk with stage-specific attraction
   toward the household residence, making co-residence a spatial mechanism.
4. Reproductive children inherit the mother's household. When a spouse bond is
   formed or refreshed, the father can join the mother's household through
   `spouse_household_join_probability`.
5. Juvenile survival now includes a household bonus from living parents and
   adult/elder household caregivers, in addition to direct child-care
   investment.
6. Maturing juveniles can disperse and found a new household through
   `maturity_new_household_probability` and
   `maturity_household_dispersal_std`.
7. Household membership also biases child-care allocation through
   `child_rearing_household_member_weight_bonus`.
8. The live viewer now supports `h` for household residence centers and reports
   household count, average household size, and latest household survival bonus.

### 2026-05-15 Behaviorally Anchored Spouse-Bond and Care-Overlay Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now makes child rearing more
   visible by lowering `base_juvenile_survival_probability` from `0.92` to
   `0.88` and increasing the maximum care survival benefit from `0.08` to
   `0.12`.
2. Individuals now store `spouse_id`, a persistent co-parent pair bond separate
   from the direct-reciprocity `reciprocity_bond_id`.
3. Initial founder pairs are placed near each other, form spouse bonds, and can
   seed local reciprocity bonds if both are unbonded and within the configured
   spouse-reciprocity radius.
4. Reproduction now forms or refreshes a spouse bond between the mother and
   father. Existing spouses are weighted upward in mate choice through
   `spouse_mate_preference`.
5. Spouse reciprocity bonds now get a higher persistence floor while the
   spouses remain local, so co-parent reciprocity can be maintained but still
   dissolves if distance or bond history breaks it.
6. Child-care allocation now gives extra weight when the helper's spouse is
   also the juvenile's parent, and another bonus when both co-parents are near
   the juvenile.
7. The model now records spouse-pair counts, spouse reciprocity counts, cared
   juvenile counts, and spouse/coparent contributions to child care.
8. `behaviorally_anchored_model/utils/live_viewer.py` now supports `s` for spouse-bond lines
   and `c` for the cared-juvenile overlay. The overlay draws a gold ring around
   juveniles that received care in the latest step.

### 2026-05-15 Behaviorally Anchored Child-Rearing Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now defines child-rearing
   parameters under the kin-selection capacity, including care radius, helper
   care capacity, care cost, caregiver energy reserve, juvenile survival
   benefit, saturation, and parent/kin allocation weights.
2. `behaviorally_anchored_model/behaviorally_anchored_model.py` now lets adults and elders provide
   costly care to nearby juveniles before the survival pass.
3. Care recipient choice is local first, then biased by pedigree: parents get
   the strongest allocation bonus, other recognized kin get a smaller bonus,
   and non-kin juveniles can still receive low-baseline alloparental care.
4. Juvenile survival now uses the configured base juvenile survival probability
   plus a saturating care bonus, then applies the existing soft density
   survival pressure.
5. The model now records `juvenile_survival_rate`,
   `total_child_rearing_care`, `mean_child_rearing_care`,
   `mean_child_rearing_relatedness`, `kin_child_rearing_fraction`, and
   `parent_child_rearing_fraction`.
6. The live viewer now displays latest child-care investment and juvenile
   survival, so child rearing is visible as a demographic mechanism rather
   than being conflated with reciprocity bonds or mating.

### 2026-05-15 Behaviorally Anchored Reciprocity-Bond Rename

Stepwise impact:

1. The direct-reciprocity pair-bond concept is now named `reciprocity_bond`
   instead of `partner` in the behaviorally anchored Python model and viewer.
2. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now uses
   `reciprocity_bond_persistence_probability`,
   `reciprocity_bond_formation_radius`, and
   `reciprocity_bond_dissolution_radius`.
3. `behaviorally_anchored_model/behaviorally_anchored_model.py` now stores
   `reciprocity_bond_id` and `reciprocity_bond_memory` on each individual.
4. The history metric formerly called `mean_partner_memory` is now
   `mean_reciprocity_bond_memory`.
5. The live viewer labels these lines and controls as reciprocity bonds, making
   clear that they are direct-reciprocity social bonds rather than mating,
   group, kin, or reputation links.

### 2026-05-15 Behaviorally Anchored Local Reciprocity-Bond Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now defines
   `reciprocity_bond_formation_radius` and
   `reciprocity_bond_dissolution_radius`.
2. `behaviorally_anchored_model/behaviorally_anchored_model.py` now uses bounded spatial distance when
   managing direct-reciprocity bonds.
3. Newly unbonded adults can only form reciprocity bonds with adults within
   `reciprocity_bond_formation_radius`.
4. Existing bonds dissolve immediately when bondmates drift beyond
   `reciprocity_bond_dissolution_radius`, in addition to the existing bond-memory
   dissolution rule.
5. The live viewer now draws reciprocity bonds as bounded-space segments, so
   bond lines reflect direct spatial separation in the displayed landscape.

### 2026-05-15 Behaviorally Anchored Lifetime Movement Update

Stepwise impact:

1. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` now defines
   `juvenile_movement_step_std`, `adult_movement_step_std`, and
   `elder_movement_step_std`.
2. `behaviorally_anchored_model/behaviorally_anchored_model.py` now moves every living individual once
   per step after age and energy updates, before spatial interaction routing
   and mate choice are evaluated.
3. Movement is a local Gaussian random walk on the bounded landscape, so agents
   are clamped at the space edges instead of wrapping around.
4. Juveniles move fastest, subadults remain fairly mobile, adults move
   moderately, and elders move slowest under the default config.
5. The live viewer now shows real model movement because `x` and `y` positions
   change during lifetime, not only when new offspring are born.

### 2026-05-15 Behaviorally Anchored Viewer and Density Update

Stepwise impact:

1. `behaviorally_anchored_model/utils/live_viewer.py` now labels the threshold statistic as
   `Trait >= 0.10` instead of `Helpers >10%`, and the chart title now says
   `Mean helping trait over time`.
2. `behaviorally_anchored_model/behaviorally_anchored_model.py` now records `realized_helping_rate`,
   `helping_events`, and `helping_opportunities` from actual interaction
   events, making trait propensity and observed helping behavior distinct.
3. The viewer side panel now displays realized help rate and the raw
   help-event/opportunity count for the latest step.
4. `behaviorally_anchored_model/config/behaviorally_anchored_config.py` replaced the hard
   `max_population` cap with `density_target_population`,
   `density_reproduction_pressure`, and `density_survival_pressure`.
5. The core model no longer randomly removes every individual above 400 after
   reproduction. Crowding above the density target now reduces reproduction and
   survival probabilities, so population can fluctuate around the target rather
   than pinning exactly to it.
