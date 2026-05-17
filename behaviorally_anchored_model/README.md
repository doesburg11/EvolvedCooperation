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
