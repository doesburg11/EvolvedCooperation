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
   fission/fusion, inter-band marriage, soft territorial avoidance, and
   scarcity-gated inter-band conflict.
5. Kin, spouse, household, parent provisioning, and alloparental child care.
6. Ecological pressure through local grass depletion, survival, reproduction,
   and soft density pressure.
7. Social learning through bounded within-lifetime copying of nearby
   adult/elder demonstrators.

Current scope:

- The model covers the foraging-band and family ecology emphasized by the
  historical page.
- Territoriality is intentionally weak and mobile: overlapping bands usually
  drift apart or displace rather than defend fixed property, and contests become
  likely only when overlap coincides with local resource scarcity.
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
