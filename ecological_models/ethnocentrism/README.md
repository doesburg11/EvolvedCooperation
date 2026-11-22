# Ethnocentrism (Python port, with lineage tracking)

A Python port of the NetLogo **Ethnocentrism** model (Wilensky 2003, NetLogo Models Library), which follows
Hammond & Axelrod's agent-based model of the evolution of ethnocentrism (*J. Conflict Resolution* 2006). It adds a
**pedigree**, so we can ask how related the neighbours an agent helps actually are. That is the kin-selection
reading of the model: colour is an inherited, imperfect cue of shared descent, and offspring are placed next to
their parent.

- Model: [`ethnocentrism_model.py`](ethnocentrism_model.py); parameters: [`config/ethnocentrism_config.py`](config/ethnocentrism_config.py)
- Runner: `./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_experiments`
- Tests: `../PredPreyGrass/.conda/bin/python -m pytest ecological_models/ethnocentrism/tests -q` (this repo's `.conda` has no pytest)
- Reference code (unmodified, untracked): [`../spatial_altruism/hammond-axelrod-ethnocentrism/`](../spatial_altruism/hammond-axelrod-ethnocentrism/)
  (NetLogo model and the authors' Java code).

## The model (same as NetLogo)

A torus of cells (51×51 by default), each empty or holding one agent. An agent has a colour (one of 4) and two
inherited strategy flags: help neighbours of the **same** colour or not, and help neighbours of a **different**
colour or not. One tick:

1. **Immigration**: one new agent (random colour, each flag on with probability 0.5) arrives on a random empty cell.
2. Every agent's potential to reproduce (PTR) is reset to 0.12.
3. **Interaction**: every agent meets each of its four neighbours and, according to its flags, helps or not. Helping
   costs the helper 0.01 PTR and gives the neighbour 0.03.
4. **Reproduction**: in random order, each agent reproduces with probability PTR into a random **empty** neighbouring
   cell (none free: no offspring). The offspring copies colour and flags; each mutates with probability 0.005.
5. **Death**: every agent dies with probability 0.10, which keeps empty cells available.

The four strategies are altruist (helps everyone), ethnocentric (helps own colour only), cosmopolitan (helps
other colours only) and egoist (helps nobody).

## Lineage tracking (added)

Each agent records its parent, its **founder** (the immigrant its line descends from) and its birth tick. Every
100 ticks, all neighbouring pairs are split into same-colour and different-colour pairs and measured:

- share of pairs with the same founder;
- for those, the number of births separating the two through their most recent common ancestor (1 = parent and
  offspring, 2 = siblings) and the common ancestor's age;
- `r_pop` for each strategy flag x: (mean of x_i·x_j over the pairs − x̄²) / var(x), with x̄ and var(x) taken over
  the whole living population. This is the statistic named in the pre-registration. It is **not** a regression
  relatedness (correction 2026-11-21, after Codex review): it is not bounded by 1, and it rises when helpers are
  over-represented among the pairs as well as when partners resemble each other.
- `r_reg` (added 2026-11-21 after the first results, so not pre-registered): Hamilton's regression of a partner's
  flag on one's own flag over the pairs of that kind, i.e. the correlation with the pairs' own mean and variance.

## Pre-registration (written 2026-11-21, before the full runs)

**1. Does the port match NetLogo?** All nine NetLogo BehaviorSpace experiments (104–111, 113; 10 NetLogo runs each,
already done) are re-run in Python with 30 seeds each. For each experiment and each of the 9 reporters in
`CHECK_METRICS` (strategy shares over the last 100 ticks, and cooperation / ethnocentric-consistency / meeting
shares over the last 100 ticks), Welch's t-test on Python vs NetLogo runs.
- **Port passes** if no experiment-metric pair has both p < 0.001 and a mean difference above
  5 percentage points. (The original text said "about 0.05/81"; that is 0.0006. The cutoff stays 0.001 as written.)
- **Port fails** otherwise; then the difference is found and fixed before any lineage result is used.
- One smoke run (seed 0, experiment 104) was looked at while writing the code, which does not affect the rule.

**2. Lineage: descriptive, with stated expectations** (standard case, experiment 104, final tick, 30 seeds):
- E1: same-colour neighbour pairs share a founder more often than different-colour pairs, in at least 27 of 30 seeds.
- E2: relatedness on the help-own-colour flag (`r_pop` for cs) is positive among same-colour pairs, in at least
  27 of 30 seeds.
(Note 2026-11-21, after the results: "relatedness" in E2 means the `r_pop` statistic above, which is not a
regression relatedness.) These describe whether colour works as a kin cue in this model. They do not test whether kinship *causes* the
spread of ethnocentrism; that needs a separate experiment, for example breaking the link between colour and descent.

## Results

See [`RESULTS.md`](RESULTS.md).
