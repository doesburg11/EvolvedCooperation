# Nowak Mechanisms - Investigation Findings

This file records the investigation history: what was tested, why it was
tested, what was misspecified, and how the final interpretation changed. It is
not only a final conclusion page.

---

## Chronological Investigation Log

This is the direct history of the investigation. Dates are included where the
repo has dated artifacts or notes. Earlier steps are marked as pre-dated context
instead of assigning a false date.

| When | What was investigated | What was learned |
| --- | --- | --- |
| Pre-2026-04-25 | Continuous-trait spatial interaction modes | Mean cooperation could rise, but these runs mixed continuous help, local routing, local Moran replacement, and spatial clustering. They were not clean tests of one Nowak mechanism. |
| 2026-04-25 | Moran-only rollback in `interaction_kernel` | The interaction-kernel package was simplified back to one update rule: local Moran replacement. This made later mechanism comparisons more controlled. |
| 2026-04-26 | Shared Moran core and named wrappers | The reusable Moran engine moved under `moran_models/interaction_kernel/core/`, and named Nowak wrapper slots were created for kin selection, network reciprocity, direct reciprocity, indirect reciprocity, and group selection. |
| 2026-04-26 | First runnable wrapper comparisons | Early matched sweeps compared runnable wrappers. These showed the engine could run multiple mechanisms on the same update loop, but direct reciprocity was still represented by a continuous memory/routing style rather than a clean repeated-game baseline. |
| 2026-04-26 | Kin-selection phase sweeps | Kin selection showed a visible cooperation boundary across benefit/cost and kin-bias parameters. This supported the spatial kin-selection model but did not yet separate kin bias from spatial clustering. |
| 2026-04-27 | Nowak mechanism packages moved under `moran_models/nowak_mechanisms/` | The investigation became organized around five explicit mechanism packages rather than ad hoc experiments in the shared engine. |
| 2026-04-29 | Spatial direct-reciprocity pair-game proof | A rare spatial cluster of reciprocal strategies spread in 5 / 5 seeds. Memory and repeated rounds were load-bearing, because no-memory and one-round ablations failed. |
| 2026-04-30 | Direct-reciprocity well-mixed validation | A well-mixed direct-reciprocity model was used to remove spatial clustering. `p = 0.9` created repeated partners, but synchronous global replacement still let `ALLD` dominate. |
| 2026-04-30 | Sync-vs-async replacement comparison | Async one-birth/one-death replacement plus weak selection made cooperation possible, while no-memory and no-persistence ablations collapsed. This showed direct reciprocity needs repeated partners, memory, and slow enough turnover. |
| 2026-05-01 to 2026-05-02 | Stability-vs-invasion tests for direct reciprocity | Direct reciprocity maintained cooperation from a reciprocal majority, sometimes amplified a 5% reciprocal foothold, but weakly invaded from a single `TFT` mutant. This separated maintenance, amplification, and origin. |
| 2026-05-02 | `rare_invaders` renamed to `small_reciprocal_foothold` | The naming was corrected because 5% reciprocal agents are not a literal single-mutant rare-invasion test. |
| 2026-05-02 | Spatial direct reciprocity moved into `scaffolds/spatial_clustering/` | The spatial model was explicitly classified as a scaffold because it combines direct reciprocity with network reciprocity. |
| 2026-05-07 | Spatial and well-mixed direct-reciprocity proof reruns | The scaffold result remained strong, while the well-mixed result remained much more conditional. This reinforced that spatial structure was doing real work. |
| 2026-05-08 | Direct-reciprocity kin-clustering scaffold | Same-lineage interaction clustering also supported reciprocal strategies, but the no-kin-bias result showed that a fixed interaction graph itself can be a powerful scaffold. |
| 2026-05-08 | Low-start emergence baseline comparison for non-direct wrappers | Indirect reciprocity, kin selection, network reciprocity, and group selection were tested from low initial cooperation. Results varied strongly by mechanism and parameters, showing that "starts from rare" depends on both mechanism and implementation details. |
| 2026-05-08 | Spatial kin-selection proof | Spatial kin selection spread from rare in 5 / 5 seeds and maintained common cooperation in 5 / 5 seeds. The no-kin-bias ablation was weaker, and below-Hamilton-rule settings failed. |
| 2026-05-08 | Indirect-reciprocity proof | The continuous reputation-routing implementation spread and maintained cooperation strongly, but this also showed that implementation details can make a mechanism look much stronger than a stricter binary or well-mixed formulation. |
| 2026-05-09 | Network-reciprocity proof | Network reciprocity maintained common cooperation and spread from rare in only some seeds. It was a real emergence mechanism, but not uniformly successful under every parameter setting. |
| 2026-05-09 | Group-selection proof | Group selection spread from rare in some seeds and maintained common cooperation. Follow-up ablations showed group-selection claims depend on avoiding hidden spatial/network structure. |
| 2026-05-10 | Kin-selection invasion trajectory plotting | The kin-selection story was visualized as trajectories, emphasizing how spatial kin clusters form and expand over time. |
| 2026-05-11 | Well-mixed kin-selection control | Kin bias without spatial kin proximity failed in all tested scenarios. This initially caused an overcorrection, but the corrected interpretation is that this is an artificial "kin preference without kin proximity" control. |

**Main chronological arc:** The investigation started with continuous spatial
modes that showed rising cooperation, then moved to explicit Moran-process
mechanism wrappers, then focused on direct reciprocity because spatial memory
was confounded with network reciprocity. Well-mixed models were introduced to
isolate pure mechanisms. That worked cleanly for direct reciprocity, but for kin
selection the well-mixed control removed a biologically natural part of the
mechanism: offspring proximity.

---

## Phase 0 - Continuous-trait spatial modes first showed rising cooperation

**Question tested:** Could a heritable cooperation trait rise under a local
Moran process?

**Implementation path:** The early work used the shared interaction-kernel
engine. Each site carried a continuous cooperation trait `h in [0, 1]`.
Cooperators produced benefit, paid cost, routed benefit through a kernel, and
then local Moran replacement copied higher-fitness neighbors.

**What looked promising:** Several continuous modes showed rising mean
cooperation. Visually and numerically, cooperation could spread on the grid.

**Why this was not a clean proof:** These runs mixed too many mechanisms:

- continuous help trait `h`, not discrete repeated-game strategies
- local spatial interaction and local Moran replacement
- benefit routing kernels
- sometimes memory-like or partner-history effects
- spatial clustering, which is already network reciprocity

**Conclusion at this stage:** The continuous modes were useful hypothesis
generators, but they did not prove a pure Nowak mechanism. Rising cooperation
showed that the engine could produce cooperative regimes; it did not isolate
which mechanism caused them.

---

## Phase 1 - Direct reciprocity became the first hard isolation problem

**Question tested:** Can direct reciprocity alone start cooperation, or does it
only maintain cooperation after reciprocators are already common?

**Why direct reciprocity became central:** The earlier continuous memory-style
models looked like direct reciprocity because agents could condition help on
past interaction. But they still used a local grid. That meant direct
reciprocity and network reciprocity were entangled.

**Modeling shift:** Direct reciprocity was rebuilt around a more explicit Moran
process with repeated Prisoner's Dilemma strategies:

- `ALLC`: always cooperate
- `ALLD`: always defect
- `TFT`: tit for tat
- `GTFT`: generous tit for tat
- `WSLS`: win-stay lose-shift

The relevant direct-reciprocity condition was the repeated-interaction
stability condition:

```text
w > (T - R) / (T - P)
```

where `w` is the probability of meeting the same partner again, `T` is the
temptation payoff, `R` is the mutual-cooperation reward, and `P` is the mutual
defection payoff.

**Key conceptual correction:** The condition is a stability condition, not an
origin-from-rarity condition. It says a reciprocal resident population can
resist rare defectors when repeated encounters are likely enough. It does not
say one rare reciprocal mutant can invade an `ALLD` population.

---

## Phase 2 - Well-mixed direct reciprocity was introduced as the pure test

**Goal:** Remove spatial clustering so direct reciprocity could be tested
without network reciprocity.

**Approach:** Build `direct_reciprocity/well_mixed/`, where interaction and
replacement are global rather than local. A display grid can visualize agents,
but grid position does not affect interaction, payoff, replacement, or mutation.

**Tests investigated:**

| Test | Purpose | Result |
| --- | --- | --- |
| `p = 0.0` partner persistence | No repeated partners; memory should be useless | Cooperation collapses |
| `p = 0.9`, synchronous replacement | Repeated partners present, but full-population replacement each step | Cooperation still usually collapses |
| `p = 0.9`, async weak selection | Repeated partners plus slower turnover | Cooperation becomes possible but stochastic |
| no-memory ablation | Remove partner-specific memory | Cooperation collapses |
| no-persistence ablation | Keep memory but remove partner re-encounter | Cooperation collapses |

**Important result:** Pure direct reciprocity can maintain cooperation once
reciprocal strategies are common, but it does not reliably originate
cooperation from a single rare reciprocal mutant.

The 2026-05-02 stability-vs-invasion proof made this distinction explicit:

| Scenario | Question | Result |
| --- | --- | --- |
| `coop_majority_no_allc` | Can reciprocal cooperators resist rare `ALLD`? | 100 / 100 successes |
| `small_reciprocal_foothold` | Can a 5% reciprocal foothold cross the basin boundary? | 62 / 100 successes |
| `single_tft_invader` | Can one rare `TFT` invade 199 `ALLD`? | 15 / 100 successes |

**Conclusion at this stage:** Direct reciprocity is mostly a maintenance and
amplification mechanism. It needs stable partners and memory, but it also needs
enough reciprocal cooperators to find each other before defectors fix.

---

## Phase 3 - Spatial direct reciprocity worked, but it was not pure

**Question tested:** Does adding spatial structure let reciprocal strategies
start from rarity?

**Approach:** The `direct_reciprocity/scaffolds/spatial_clustering/` model put
the repeated Prisoner's Dilemma strategies on a 2D grid with local interaction
and local Moran replacement.

**Result:** A rare spatial cluster of reciprocal agents could spread reliably.
The proof runs showed:

| Scenario | Result |
| --- | --- |
| `rare_cluster_start` | 5 / 5 successes |
| `no_memory_ablation` | 0 / 5 successes |
| `one_round_ablation` | 0 / 5 successes |

**Interpretation:** The result was real, but it was direct reciprocity plus
network reciprocity. Pair memory and repeated rounds mattered, but the grid was
also load-bearing because it shielded cooperator clusters from immediate global
defector contact.

**Consequence:** These models were classified as scaffolds, not pure direct
reciprocity baselines. The earlier continuous spatial-memory mode belonged in
the same conceptual category: useful, but not a pure well-mixed test.

---

## Phase 4 - Scaffold tests exposed the general isolation problem

**Question tested:** What kinds of structure can help direct reciprocity get
started?

**Scaffolds investigated:**

| Scaffold | What it added | Interpretation |
| --- | --- | --- |
| Small reciprocal foothold | More than one reciprocal invader | Can cross the basin boundary stochastically |
| Spatial clustering | Fixed local graph | Direct reciprocity + network reciprocity |
| Kin clustering | Same-lineage agents interact more often | A kin/assortment scaffold for reciprocal pairs |
| Continuous spatial memory | Continuous help trait plus local partner memory | Not a pure direct-reciprocity baseline |

**Important lesson:** If a mechanism succeeds only after adding a scaffold, the
scaffold must be named. Otherwise the result gets misread as evidence for the
focal mechanism alone.

---

## Phase 5 - The first broad comparison was unfair

**Question tested:** Which of Nowak's mechanisms can amplify rare cooperation
from a low initial frequency?

**Initial claim, too strong:** Kin selection is the only mechanism that starts
from rare.

**Why the claim looked plausible:** The spatial kin-selection model produced
convincing cooperator clusters. Compared casually against weaker or less
scaffolded runs, it looked uniquely strong.

**Problem identified:** The comparison mixed pure controls and scaffolded
models. Direct reciprocity plus spatial structure had also spread from rare
reliably. Network reciprocity and group selection had weaker isolated results.
Some indirect-reciprocity results also depended strongly on implementation and
state assumptions.

**Corrected empirical snapshot from that investigation stage:**

| Mechanism | Spread from rare |
| --- | --- |
| Kin selection, spatial | 5 / 5 seeds |
| Direct reciprocity + spatial scaffold | about 5 / 5 seeds |
| Network reciprocity alone | about 2 / 5 seeds |
| Group selection alone | about 2 / 5 seeds |
| Indirect reciprocity, then-current well-mixed test | 0 / 5 seeds |

**Conclusion at this stage:** The uniqueness claim was wrong. Kin selection was
not the only model that could start from rare. The correct question became:
which structural requirements are natural to the mechanism, and which are extra
scaffolds?

---

## Phase 6 - Discovery: spatial kin selection embeds network reciprocity

**Problem identified:** The kin-selection spatial model was not pure kin
selection. It used:

- a kin-biased routing kernel, preferentially sending benefit to same-lineage
  neighbors
- local replacement on a grid, where offspring replace nearby sites

Local replacement on a grid creates spatial clusters. That is network
reciprocity by mechanism: cooperators can be surrounded by cooperators and
shielded from defectors.

**Implication:** The spread-from-rare results attributed to kin selection were
actually kin selection plus local spatial clustering.

---

## Phase 7 - A well-mixed kin-selection control was built

**Goal:** Test whether kin-biased help alone works when spatial clustering is
removed.

**Approach:** Add a fully connected neighborhood mode, then build
`kin_selection/well_mixed/`. Every site can interact with every other site, and
replacement is global. The kin-biased routing kernel remains active.

**Code change:** Added `"fully_connected"` neighborhood mode to `space.py`:

```python
if mode == "fully_connected":
    n_sites = width * height
    all_sites = np.arange(n_sites, dtype=np.int32)
    neighbors = []
    for i in range(n_sites):
        neighbors.append(np.delete(all_sites, i))
    return neighbors
```

**New files:**

- `kin_selection/well_mixed/config/kin_selection_well_mixed_config.py`
- `kin_selection/well_mixed/utils/proof_of_mechanism.py`

**Scenarios tested:**

| Scenario | Description |
| --- | --- |
| `spread_from_rare_kin_bias` | Cooperation rare, fully connected, kin bias active |
| `spread_from_rare_no_kin_bias` | Cooperation rare, fully connected, equal weights |
| `maintenance_common_start` | Cooperation common, fully connected, kin bias active |

**Results, 5 seeds each:**

| Scenario | Success rate | Mean final trait |
| --- | ---: | ---: |
| `spread_from_rare_kin_bias` | 0 / 5 | about 0.005 |
| `spread_from_rare_no_kin_bias` | 0 / 5 | about 0.004 |
| `maintenance_common_start` | 0 / 5 | about 0.006 |

**Immediate interpretation:** Kin bias alone, without spatial kin proximity,
failed to spread or maintain cooperation.

---

## Phase 8 - First documentation rewrite overcorrected

**Mistake made:** The well-mixed kin-selection result was initially written as
if kin selection itself failed to start from rare. A documentation table was
changed to show kin selection as red No/No.

**Why that was wrong:** The well-mixed control removed more than an incidental
confound. It removed offspring proximity, which is normally part of how kin
selection arises. In a biological population, relatives are not just arbitrary
labels scattered uniformly through space; kin structure is produced by
reproduction.

**Correct interpretation:** The well-mixed test is a control for "kin preference
without kin proximity." It is useful, but it is not a biologically complete
kin-selection model.

---

## Phase 9 - Worked example explained why well-mixed kin bias fails

To understand the 0 / 5 result mechanically, a four-site example was worked
through.

**Setup:** Four sites, one cooperator and three defectors. The cooperator shares
lineage with one defector. Kin routing gives same-lineage recipients more
benefit than other-lineage recipients.

**Mechanism:** The cooperator pays the cost of helping and preferentially sends
benefit to its same-lineage neighbor. But if that same-lineage neighbor is a
defector, the cooperator has just enriched the most dangerous local competitor.

**Resulting logic:**

- the cooperator pays cost
- the same-lineage defector receives extra benefit
- the same-lineage defector can get the highest fitness
- global replacement then often copies the defector over the cooperator

**Conclusion:** In a well-mixed population, kin bias can backfire because kin
preference is not enough. Kin proximity and inherited cooperative clusters are
what make kin selection work biologically.

---

## Phase 10 - The u-turn: kin proximity is not an optional scaffold

**Key insight:** In the spatial kin-selection model, offspring replace nearby
sites and inherit both trait and lineage. Over time, cooperator offspring create
same-lineage cooperator clusters.

That is not a separate artificial add-on. It is the normal demographic route by
which kin structure appears.

**Biologically incoherent scenario:** "Kin preference without kin proximity" -
preferentially helping same-lineage individuals while those same-lineage
individuals are uniformly scattered and not locally produced by reproduction.

**Consequence:** The well-mixed kin-selection test does not falsify kin
selection. It shows that kin bias alone, stripped of kin proximity, is
insufficient. The failure is expected and useful as an isolation control.

---

## Phase 11 - Corrected final interpretation

After the u-turn, the question changed:

**If kin selection plus local clustering is not strictly unique, why is kin
selection still special?**

**Answer:** The structural requirements are not equally natural.

| Mechanism | Structural requirement | How natural is it? |
| --- | --- | --- |
| Kin selection | Offspring stay near parents, creating related clusters | Built into local reproduction |
| Direct reciprocity | Stable repeated partners plus memory | Requires partner stability and recognition |
| Network reciprocity | Persistent spatial or graph clustering | Requires graph/local interaction structure |
| Group selection | Persistent groups and between-group competition | Requires metapopulation structure |
| Indirect reciprocity | Observation, assessment, and reputation memory | Requires social information infrastructure |

**Corrected conclusion:** Kin selection is not unique because no other model can
ever start cooperation. It is the most biologically robust initiator in this
comparison because its key structural precondition - offspring near parents - is
the least extra thing to assume once reproduction is local.

---

## Phase 12 - Final documentation state

**nowak-mechanisms.md:**

- Display 2 table: kin selection row should remain green Yes/Yes, with the
  explanation that offspring stay near parents and automatically create kin
  clusters.
- Display 3 well-mixed control: should be framed as "kin preference without kin
  proximity," not as a falsification of kin selection.
- Origin section: should explain trivial versus non-trivial structural
  requirements.

**kin-selection.md:**

- The positive claim should be "most biologically robust initiator," not
  "unique initiator."
- Well-mixed ablations should be framed as controls showing what happens when
  kin proximity is artificially removed.
- The spatial kin-selection result should acknowledge that local replacement and
  lineage clustering are doing real work.

---

## Summary of Lessons

1. **History matters.** The investigation did not start with the final
   kin-selection conclusion. It passed through continuous spatial modes,
   direct-reciprocity Moran tests, well-mixed controls, scaffold experiments,
   and then the kin-selection correction.

2. **Rising cooperation is not enough.** A model can show increasing
   cooperation while still mixing several mechanisms.

3. **Well-mixed controls are useful but not always biologically complete.**
   They cleanly isolate direct reciprocity from network reciprocity. For kin
   selection, they test kin preference without kin proximity, which is a valid
   control but an artificial biological scenario.

4. **Origin, amplification, and maintenance are different tests.** Direct
   reciprocity passes maintenance much more cleanly than origin from a single
   rare mutant.

5. **Confounds must be named, not erased.** Spatial direct reciprocity is direct
   plus network reciprocity. Spatial kin selection includes local kin
   clustering. Those are not trivial details; they are the mechanisms that make
   the runs succeed.

6. **The final claim is comparative, not absolute.** Kin selection is best
   described as the most biologically robust initiator among the mechanisms
   tested here, because local reproduction naturally creates kin proximity.
