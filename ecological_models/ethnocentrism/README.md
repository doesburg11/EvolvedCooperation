# Ethnocentrism (Python port, with lineage tracking)

A Python port of the NetLogo **Ethnocentrism** model (Wilensky 2003, NetLogo Models Library), which follows
Hammond & Axelrod's agent-based model of the evolution of ethnocentrism (*J. Conflict Resolution* 2006). It adds a
**pedigree**, so we can ask how related the neighbours an agent helps actually are. That is the kin-selection
reading of the model: colour is an inherited, imperfect cue of shared descent, and offspring are placed next to
their parent.

- Model: [`ethnocentrism_model.py`](ethnocentrism_model.py); parameters: [`config/ethnocentrism_config.py`](config/ethnocentrism_config.py)
- Runner: `./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_experiments`
- Tests: `./.conda/bin/python -m pytest ecological_models/ethnocentrism/tests -q`
- Speed: the per-agent loops are compiled with numba: an Experiment-104 run takes 0.5-0.8 s instead of
  3.4 s, and a 101x101 Experiment-105 run 1.6 s instead of 13 s. Random draws come from the same generator in
  the same order, so all committed runs replay bit for bit. Tests check this against committed runs and,
  tick by tick, against a frozen copy of the pure-Python model ([`tests/reference_model_pure_python.py`](tests/reference_model_pure_python.py)).
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
  offspring, 2 = siblings or grandparent and grandchild) and the common ancestor's age;
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

## Pre-registration: random-colour experiment (written 2026-11-22, before running)

**Question.** Does ethnocentrism's late-run prevalence in this model change when colour is no longer inherited,
i.e. when colour stops being a cue of shared descent?

**Design.** Experiment 104 (standard settings), 30 runs per condition, both conditions in the same batch:

- **inherited**: as NetLogo (the child copies its parent's colour, which mutates with probability 0.005). Seeds
  0–29, the seeds of the committed port run. This arm must replay that run exactly (all reporters, population
  and birth counts, every seed), or there is no verdict.
- **random**: each child's colour is drawn uniformly from the 4 colours, independent of its parent. Strategy
  inheritance and mutation, placement next to the parent, immigration and everything else are unchanged. Seeds
  1000–1029, so the two arms use separate random streams and are treated as independent samples.

Runner: `utils/run_random_colour.py`; thresholds in `config/ethnocentrism_config.py` (`RC_*`). One batch, no
re-runs with changed settings; any follow-up needs a new agreed plan.

**Endpoint.** `cd-percent`: ethnocentric agents as a share of all agents, pooled over agent-ticks in the last 100
ticks (NetLogo's reporter, whose denominator is floored at one agent).

**Manipulation check (must pass, or there is no verdict).** For each random-condition run, the gap = same-founder
share among same-colour neighbour pairs minus that among different-colour pairs, at the final tick. Passes if the
mean gap over the 30 runs is below 0.05 in absolute value **and** the mean of the absolute per-run gaps is below
0.10 (so large gaps of opposite sign cannot cancel). Per-run gaps and pair counts are reported. A pass shows only
that, at the final tick, the founder-sharing gap between same- and different-colour pairs is within these bounds;
how recent the common ancestors are is reported, not tested.

**H1.** The ethnocentric share is lower in the random condition than in the inherited one by at least 10
percentage points, with a two-sided Welch p < 0.001. Missing or undefined values, a wrong number of runs, or a
test without a standard error give "invalid", not "not met".

**Reported without a rule:** the shares of the other three strategies, overall cooperation
(`last100coop-percent`), the share of same-colour meetings, population, and per pair group (same colour,
different colour, all) the same-founder share, median births separating the pair, median common-ancestor age and
`r_reg` on both strategy flags.

**Expectation.** H1 met. With random colour, helping only one's own colour means helping whichever neighbours
happen to share one's colour, with no gain in how related they are; we expect these to be roughly a quarter of
neighbours, but that is an outcome, not given.

**Reading.**

- *H1 met:* under these settings, breaking the colour–descent link lowers ethnocentrism's late-run prevalence.
  It does not show that shared descent is *the* reason: see the confound.
- *H1 not met:* the batch did not show a drop of the registered size and strength. A smaller effect remains
  possible.
- *Confound, either way:* random colour changes two things at once. By design it removes inherited colour as a
  cue of descent (the manipulation check measures only founder sharing, within the bounds above), and same-colour
  neighbours will probably also become rarer, so ethnocentrics help fewer neighbours. This experiment cannot
  separate the two.

## Pre-registration: lower-viscosity experiment (written 2026-11-22, before running)

**Question.** In the random-colour experiment, cooperation was similar with and without the colour cue (77.0% vs
75.6% of meetings), and neighbours stayed related because offspring are placed next to their parent. What happens when offspring disperse,
so that neighbours are less related? In particular: does cooperation then need inherited colour?

**Design.** Experiment 104 settings with a new `dispersal` setting d: at each reproduction attempt, with probability d, the
child is placed in a random empty cell anywhere in the world instead of a neighbouring one (the dispersal draw is
made only when d > 0). d = 0, 0.25, 0.5, 0.75, 1, crossed with colour rule inherited / random (as in the
random-colour experiment): 10 cells × 30 runs, one batch. Seeds: 10000 × (level index) plus 0–29 (inherited) or
plus 1000–1029 (random), so d = 0 uses the seeds of the two earlier runs. Both d = 0 cells must replay those committed
runs exactly (all reporters, population and births, every seed), or there is no verdict. Runner:
`utils/run_viscosity.py`; thresholds `VISC_*` in the config. One batch, no re-runs with changed settings.

**Manipulation check (must pass, or there is no verdict).** In both colour arms, the share of neighbour pairs
(all pairs) that share a founder, at the final tick, falls by at least 0.20 from d = 0 to d = 1 (difference of
means over the 30 runs per cell, all values defined; no significance test). This is a coarse check on the average
final-tick drop: some local assortment can remain after a pass.

**Endpoint.** Cooperation, `last100coop-percent`: the share of meetings in the last 100 ticks in which the agent
helped its neighbour (NetLogo's reporter). A run with no meetings in that window has an undefined value. Tests:
the observed difference of means reaches the stated minimum and a two-sided Welch test (of zero difference) gives
p < 0.001 (minimums compared with a 1e-9 floating-point tolerance); undefined values, a wrong number of runs or no standard error (at most 1e-12, i.e. rounding) give
"invalid".

- **H1** (without the cue, dispersal lowers cooperation): random colour, cooperation at d = 1 is at least 20
  percentage points below d = 0.
- **H2** (the cue can stand in for viscosity): at d = 1, cooperation with inherited colour is at least 10
  percentage points above cooperation with random colour.

**Reported without a rule:** for every cell, the four strategy shares, population, offspring per tick, the share
of offspring placed by dispersal (it can exceed d, since local placements are blocked far more often than global
ones, which fail only in a full world), share of
same-colour meetings, neighbour founder sharing (all, same-colour and different-colour pairs), median
common-ancestor age and `r_reg` on both flags.

**Expectations.** H1 met: with random colour and global dispersal, we expect much weaker local assortment, so
helping neighbours should pay less. H2: no confident expectation, leaning not met. Inherited colour with dispersal
is like a green beard only loosely linked to the helping trait: egoists of the same colour receive help from
adjacent ethnocentrics wherever they settle, so we expect them to spread within each colour.

**Reading.**

- *H1 met:* with random colour, global placement of offspring lowered cooperation by at least the registered
  amount. This does not show cooperation needs viscosity (some may remain), nor which part of the change did it.
- *H1 not met:* the batch did not show a drop of the registered size and strength.
- *H2 met:* at d = 1, inherited colour gave more cooperation than random colour. This alone does not show that the
  cue *substitutes* for viscosity; that would need a registered comparison of the dispersal effects across arms.
- *H2 not met:* the batch did not show that inherited colour sustains cooperation (by the registered amount)
  once offspring disperse; a smaller effect remains possible.
- *Confound, either way:* global dispersal changes more than relatedness. Offspring are no longer blocked by a
  full neighbourhood (more births, less competition between relatives for nearby space), and colour clusters
  break up, so ethnocentrics meet their own colour less often. Offspring per tick and own-colour meetings are reported
  so this is visible, but the design cannot separate these effects. The intermediate d values are descriptive only.

## Pre-registration: confound-separating experiment (written 2026-11-22, before running)

**Question.** In the random-colour experiment the ethnocentric share fell from 75.5% to 12.9%. Two things changed
at once: same-colour neighbours stopped being closer kin, and own-colour meetings fell from about 80% to 25%. Does
the ethnocentric share still fall when colour is unrelated to descent but the overall own-colour meeting share is
brought back to about 80%? This narrows the confound; it does not fully separate the two.

**Design.** Experiment 104 settings, 30 runs per arm, one batch:

- **inherited** (seeds 0–29): as NetLogo; must replay the committed port run exactly.
- **random_uniform** (seeds 1000–1029): child colour uniform over the 4 colours, as in the random-colour
  experiment; must replay that committed arm exactly.
- **random_skewed** (seeds 3000–3029): child colour drawn independently of the parent, but from weights 0.892 for
  one colour and 0.036 for each of the others. Two independent draws from these newborn weights have the same
  colour with probability 0.80, the own-colour meeting share of the inherited arm; the realised share among living
  neighbours can differ (immigrants, selection) and is checked below. Immigrants keep uniform colours, as in every
  arm.

Runner: `utils/run_confound.py`; thresholds `CF_*` (and the founder-gap limits `RC_MANIP_*`) in the config. One
batch, no re-runs with changed settings.

**Manipulation checks (both must pass, or there is no verdict)**, in the random_skewed arm:

1. Own-colour meetings (`last100meetown-percent`, mean over runs) between 0.75 and 0.85.
2. Same-colour and different-colour neighbours share a founder about equally often at the final tick, by the
   rule of the random-colour experiment: mean gap below 0.05 in absolute value and mean absolute gap below 0.10.
   This bounds founder sharing only; recent kinship (share of pairs at most two births apart, common-ancestor
   age) is reported, not tested.

**Endpoint and tests.** The ethnocentric share `cd-percent` (last 100 ticks). Each test: the observed difference
of means is at least 10 percentage points and a two-sided Welch test gives p < 0.001 (same handling of undefined
values, run counts and standard error as the lower-viscosity experiment).

- **H1** (with the overall own-colour meeting share matched, random colour still lowers the ethnocentric share):
  inherited minus random_skewed ≥ 10 points.
- **H2** (without inheritance, skewing the colour distribution raises it): random_skewed minus random_uniform ≥ 10
  points.

**Reported without a rule:** the other strategy shares, cooperation, own-colour meetings, founder sharing, recent
kinship and `r_reg` per pair group, per arm; and, at the final tick, the share of occupied neighbours with the own
colour for ethnocentric agents and for agents of the most common colour versus the others.

**Expectations.** H1 met: in random_skewed we expect ethnocentrics to meet (and help) their own colour roughly as
often as in the inherited arm, but colour is not inherited there; their actual exposure is measured only at the
final tick. Neighbours are still kin through local birth, so helping all of them (altruists)
should do better, as altruists did under uniform random colour. H2: leaning met, less confident. Without the cue,
ethnocentrics and altruists differ in only about 20% of meetings in random_skewed (against 75% in random_uniform),
so selection against ethnocentrics should be weaker.

**Reading.**

- *H1 met:* with the overall own-colour meeting share matched, random colour still went with a lower ethnocentric
  share; the pooled own-colour meeting share alone does not explain the earlier drop. Ethnocentrics' own exposure
  can still differ between arms (reported at the final tick), and the arms differ in colour inheritance, colour
  frequencies and colour clustering, so this does not pin the drop on lost kinship.
- *H1 not met:* the batch did not meet the registered criterion (a difference of at least 10 points with
  p < 0.001); a smaller effect remains possible. It would not show that fewer own-colour meetings caused the
  earlier drop.
- *H2 met / not met:* whether, with colour not inherited, the effect of skewing newborn colours (which changes who
  meets whom) on the ethnocentric share met the registered criterion (at least 10 points with p < 0.001).
- *Remaining differences between the arms:* matching the average meeting share does not match the colour
  structure. In random_skewed we expect one colour to hold roughly 89% of agents (its newborn weight), meeting
  their own colour about 89% of the time, while the other agents rarely do; in the inherited arm the four colours form local clusters. The
  experiment matches (approximately, within 0.75–0.85) the average only; per-strategy exposure is reported.

## Pre-registration: shuffle experiment (written 2026-11-22, before any code or runs)

**Question.** The earlier experiments are consistent with kin selection: cooperation needed offspring to stay
near their parents, which keeps neighbours related. But global dispersal also changed other things: how often
births are blocked, population size and whom agents meet. Does removing the spatial assortment by descent, while
keeping local birth, lower cooperation?

**Why random colour.** The main test uses the random-colour model (child colour uniform, independent of the
parent; section 3 of RESULTS.md): cooperation there was 75.6% of meetings, carried by local birth alone (altruists
most common), and own-colour meetings were already at the random-mixing level (25%). Shuffling should therefore
hardly change the colour of the neighbours an agent meets. With about 25% own-colour meetings within each donor
strategy, the expected share of meetings with help is the altruists' share of meetings plus 0.25 times the
ethnocentrics' share plus 0.75 times the cosmopolitans' share. So a shuffle is not expected to change how often help
is given unless the strategy mix among meetings changes. This is a reference, not a guarantee: meetings are
counted per donor and neighbour (an agent with four neighbours counts four times), and colour-dependent
reproduction can shift exposure among living agents. Both are reported below. With inherited colour the shuffle
would change help mechanically: shuffling breaks the colour clusters, and ethnocentrics
(three quarters of that population) help only their own colour. So with inherited colour a drop in cooperation
would partly be mechanical. Inherited colour is run as a descriptive arm only.

**Manipulation.** A new `shuffle_fraction` setting f. At the end of each tick, after death and before the
statistics and lineage samples, each occupied cell is selected independently with probability f (one
`rng.random()` per occupied cell, in cell order). The agents in the selected cells are then permuted among those
cells by one `rng.permutation(k)` (k = number selected, also when k is 0 or 1). Each agent moves with its id,
colour, both strategy flags and PTR. PTR is reset before the next interaction, so moving it has no effect. The
draws are made only when f > 0, so f = 0 replays earlier runs exactly.

What this holds fixed: at the moment of the shuffle, the occupied cells, population and strategy counts. The birth
rule is unchanged: offspring are placed in an empty neighbouring cell of the parent, or not at all. What it does
not hold fixed: over later ticks the arms can develop different occupancy, meeting counts, birth success,
competition for vacancies and immigrant exposure. With f = 1, a newborn that survives its first tick is moved
before it meets anyone, although it can land next to its parent by chance.

**Design.** Experiment 104 settings, 30 runs per cell, one batch:

| Cell | Colour rule | f | Seeds | Role |
|---|---|---|---|---|
| R0 | random | 0 | 1000–1029 | test (must replay the committed random-colour arm, `data/random_colour/runs.csv`, condition `random`) |
| R0.1 | random | 0.1 | 6000–6029 | descriptive |
| R0.5 | random | 0.5 | 7000–7029 | descriptive |
| R1 | random | 1 | 8000–8029 | test |
| I0 | inherited | 0 | 0–29 | descriptive (must replay the committed port run, `data/runs.csv`, experiment 104) |
| I1 | inherited | 1 | 9000–9029 | descriptive |

No earlier experiment used seeds 6000–9029. Runner: `utils/run_shuffle.py`; thresholds `SHUF_*` in the config.
One batch, no re-runs with changed settings.

**Validity rules (fail closed).**

1. Every registered (cell, seed) must give exactly one well-formed result (all reporters, counts and lineage
   samples present), with exactly the registered seed set per cell. A failed, malformed, missing or duplicate
   result, or a missing or unreadable replay file, invalidates the whole batch, descriptive cells included.
2. Replay: R0 and I0 must reproduce their committed runs exactly: same seed set, the full reporter key set and
   values, final population and `births_total` (which includes immigrants). Otherwise every verdict is
   "invalid". A unit test also checks that f = 0 makes no shuffle draws (Generator state identical to a run
   without the setting).
3. Manipulation check (below) failing makes H1 and H2 "invalid".
4. An endpoint with a non-finite value, the wrong number of runs, a zero raw denominator (no meetings in the last
   100 ticks for H1, no agent-ticks for H2; checked from the raw counts, because the NetLogo reporters return 0 in
   that case and are kept unchanged for the replay), a Welch standard error of at most 1e-12 (on the 0–1 scale) or
   a non-finite p-value makes that hypothesis "invalid".
5. "Met" and "not met" are given only for valid comparisons; "not met" means the observed difference or the
   p-value missed its threshold.

**Manipulation check: excess founder sharing among interacting neighbours.** In every tick of the last 100,
measured after immigration and just before interaction, over all unordered pairs of occupied von Neumann
neighbours: the observed share of pairs whose two agents descend from the same founder, minus the share expected
under random mixing of the same living population, the sum over founders i of n_i(n_i − 1) / (N(N − 1)), with n_i
the living agents of founder i and N the population. Each tick's two shares are weighted by its number of pairs
(pooled over the 100 ticks), and the excess per run is observed minus expected. The check passes if, in the random
arm, the mean excess falls by at least 0.20 from R0 to R1 (difference of means over 30 runs, all values defined,
same 1e-9 tolerance, no significance test). A tick with no pairs, or a run with fewer than 100 such ticks, makes
that run's value undefined. The raw observed and expected shares are reported.
Before fixing the 0.20, we computed only the baseline from the committed R0 runs (already published; no shuffled
run was made). At the final tick, neighbours shared a founder 70.1% of the time against 5.9% expected under random
mixing, an excess of 0.64 (lowest run 0.61). This motivates the 0.20, but it is a final-tick figure, so it does
not guarantee the registered 100-tick statistic can reach it.

**Endpoints and tests (random arm, R1 versus R0).** Each test passes when the observed difference of means reaches
the stated minimum (1e-9 floating-point tolerance) and a two-sided Welch test gives p < 0.001.

- **H1** (removing spatial assortment lowers cooperation): cooperation (`last100coop-percent`, the share of meetings
  in the last 100 ticks in which help was given; undefined with no meetings) is at least 20 percentage points
  lower in R1.
- **H2** (it raises the egoist share): the egoist share (`dd-percent`: egoist agent-ticks over all agent-ticks in
  the last 100 ticks, at the end of each tick; undefined if that total is 0) is at least 20 percentage points
  higher in R1.

**Reported without a rule:** for every cell, the four strategy shares, cooperation, population, offspring per
tick, own-colour meetings, the raw and expected founder sharing among interacting neighbours, final-tick founder
sharing (all, same-colour and different-colour pairs), share of pairs at most two births apart, median
common-ancestor age and `r_reg` on both flags. Also, over the last 100 ticks, the donor strategy shares among
meetings, the own-colour meeting share within each donor strategy, and the help rate these imply (altruists
always help, ethnocentrics in own-colour meetings, cosmopolitans in other-colour meetings). This shows whether a
drop in help comes from the strategy mix among meetings or from whom agents meet.

**Expectations (predictions).** H1 and H2 met. Agents have no memory and no strategy conditional on anything other
than colour, and in the random arm colour is not linked to descent. Without spatial assortment, a helper's
neighbours are close to a random draw from the population, so helping should no longer go preferentially to
helpers. We predict that strategy assortment among neighbours falls, and egoists spread, as at full dispersal
(about 90% there). We also expect the population to shrink as help, and with it PTR, falls. In the inherited arm
we predict a drop in help that is partly due to lost colour clusters. f = 0.1 and 0.5: no confident expectation.

**Reading.**

- *H1 met, checks passed:* in this model the shuffle reduced founder assortment among interacting neighbours, and
  the observed drop in cooperation met the registered criterion (a drop of at least 20 points, with p < 0.001
  against no difference). That is an effect of the shuffle, with local birth unchanged. It is consistent with
  relatedness among neighbours (kin selection through viscosity) sustaining cooperation here. It does not identify
  how much of the effect is due to relatedness, because the shuffle also changes other things. Strategy assortment falls with pedigree
  assortment. Competition among relatives for nearby vacancies (kin competition) also changes, and its net
  direction is not resolved by this design.
- *H1 not met:* the batch did not meet the registered criterion. That does not establish that the true drop is
  below 20 points, and a smaller effect remains possible. The kin-selection reading would not be supported by this
  test.
- *H2:* whether the egoist share rose by the registered amount. It measures prevalence, not reproductive success.
- *Inherited-colour arm (descriptive):* shows what shuffling does when colour is a kin cue. Part of any change
  there is mechanical, through lost colour clusters.
- *Intermediate f:* describe the sampled levels and do not locate a threshold.
- *Hard stop:* one batch, then the write-up. No follow-up variants without a new agreed plan.

## Results

See [`RESULTS.md`](RESULTS.md).
