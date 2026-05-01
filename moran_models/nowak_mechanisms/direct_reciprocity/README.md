# Direct Reciprocity

Three implementations showing when and why direct reciprocity can — and cannot
— sustain cooperation, starting from the pure theoretical case and adding one
feature at a time.

---
TODO: Mental accounting, implement a range of in-debtness, to model the concept of friend/informal business. For instance if defected x-times in a row / or if the accumulated investement is 'fair'.

## The Condition

Direct reciprocity works through repeated encounters between the *same two
individuals*. A cooperator can punish a defector in the next round and reward a
cooperator. Nowak (2006) shows cooperation is stable when:

<p>w &gt; (T &minus; R) / (T &minus; P)</p>

where:

- **w** — probability of meeting the *same partner again* in the next interaction
- **T** — temptation payoff: what a defector earns against a cooperator
- **R** — reward payoff: what both earn under mutual cooperation
- **P** — punishment payoff: what both earn under mutual defection

With the default Prisoner's Dilemma payoffs (T = 1.7, R = 1.0, P = 0.0,
S = −0.5):

<p>w &gt; (1.7 &minus; 1.0) / (1.7 &minus; 0.0) &asymp; 0.41</p>

**The re-encounter probability w is the critical variable.** Everything below
follows from whether it meets this threshold.

**Important: this condition describes stability, not invasion.**
It states that a population of TFT players can *resist* invasion by ALLD — not
that TFT can *spread into* an ALLD-majority population. When TFT is rare it
almost always meets ALLD first. That encounter yields fitness 0.5 for TFT
against an average ALLD fitness of ~1.0 (most ALLD agents meet other ALLD,
earning P = 0.0 → fitness 1.0). Selection pushes TFT down before pair history
can accumulate. Meeting the threshold w > 0.41 is necessary but not sufficient
for cooperation to emerge from a minority.

### Payoff matrix

| Actor / Partner | Partner cooperates | Partner defects |
| --- | --- | --- |
| Actor cooperates | R = 1.0 (reward) | S = −0.5 (sucker) |
| Actor defects | T = 1.7 (temptation) | P = 0.0 (punishment) |

This satisfies T > R > P > S — the standard definition of the Prisoner's
Dilemma. Defection is individually tempting (T > R), mutual cooperation beats
mutual defection (R > P), and defecting is the safe choice (P > S). The
dilemma is that rational individuals defect even though both would be better
off cooperating.

### Strategies

The `ALL` labels are standard repeated-game notation: `ALLC` means "all C"
(cooperate in every round), and `ALLD` means "all D" (defect in every round).
They are readable labels, not exact acronyms.

| Strategy | How to read it | Rule |
| --- | --- | --- |
| ALLC | All-C / Always Cooperate | Cooperate unconditionally. |
| ALLD | All-D / Always Defect | Defect unconditionally. |
| TFT | Tit for Tat | Cooperate on the first round; then copy the partner's previous action. |
| GTFT | Generous Tit for Tat | Like TFT, but forgive a defection with fixed probability. |
| WSLS | Win-Stay Lose-Shift | Repeat the previous action if it paid at or above aspiration; otherwise switch. |

---

## Step 1 — Pure direct reciprocity fails

**Model:** [`well_mixed/`](well_mixed/) with `partner_persistence_probability = 0.0`

In a population of 200 agents with random re-pairing every step, the
probability of meeting the same partner again is:

<p>w &asymp; 1 / (n &minus; 1) &asymp; 0.005</p>

This is far below the threshold of 0.41. Memory is useless: even if TFT
punished a defector last round, it will almost certainly never meet that
defector again. ALLD exploits every cooperator it encounters in round 1,
accumulates higher fitness, and sweeps the population.

**Result: ALLD dominates. Cooperation cannot emerge.**

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_model
```

Set `partner_persistence_probability = 0.0` in
[`well_mixed/config/direct_reciprocity_well_mixed_config.py`](well_mixed/config/direct_reciprocity_well_mixed_config.py).

---

## Step 2 — Partner persistence enables direct reciprocity

**Model:** [`well_mixed/`](well_mixed/) with `partner_persistence_probability = 0.9`

`partner_persistence_probability` (p) is the probability that an existing pair
stays together in the next step. Each step, for every pair (i, j):

- with probability p: the pair is kept; i and j play together again
- with probability 1 − p: the pair is dissolved; both agents are pooled with
  other dissolved agents and re-paired at random

When p = 0.9, the effective re-encounter probability is:

<p>w &asymp; 0.9 &gt; 0.41 &#10003;</p>

The repeated-game condition is satisfied at the pair level. TFT–TFT pairs that
find each other build mutual cooperation across rounds. ALLD exploits TFT in
round 1 (earning T = 1.7), but TFT retaliates from round 2 onwards; the
persistent ALLD–TFT pair quickly becomes mutual defection (P = 0.0 for both).
TFT–TFT pairs earn R = 1.0 per round.

**Current implementation result:** this is not sufficient by itself in the
synchronous global-replacement well-mixed model. A 2026-04-30 validation found:

- current config, `p = 0.0`, `mutation_rate = 0.01`: mean cooperation after
  burn-in ≈ 0.019 across 10 seeds
- current config, `p = 0.9`, `mutation_rate = 0.01`: mean cooperation after
  burn-in ≈ 0.027 across 10 seeds
- `p = 0.9`, `mutation_rate = 0.001`: mean cooperation after burn-in ≈ 0.001
  across 10 seeds

So the current supported conclusion is that `p = 0.9` creates repeated
encounters, but the current synchronous replacement regime still lets ALLD
dominate.

`rounds_per_pair_per_step = 3` may contribute to this outcome, but it is not
the main supported explanation. It controls how many repeated Prisoner's
Dilemma rounds a current pair plays before replacement is applied in that step.
The persistence parameter `p` controls whether that same pair survives into the
next step. With `p = 0.9`, a pair lasts about `1 / (1 - p) = 10` steps on
average, so a stable pair can experience roughly `10 * 3 = 30` rounds before
being dissolved by partner reshuffling.

The short-run payoff logic is still important. For a fresh three-round
TFT-ALLD pair:

```text
round 1: TFT cooperates, ALLD defects -> TFT = -0.5, ALLD = 1.7
round 2: TFT retaliates, ALLD defects -> TFT = 0.0,  ALLD = 0.0
round 3: TFT defects,    ALLD defects -> TFT = 0.0,  ALLD = 0.0

total: TFT = -0.5, ALLD = 1.7
```

But for a fresh three-round TFT-TFT pair:

```text
round 1: both cooperate -> TFT = 1.0, TFT = 1.0
round 2: both cooperate -> TFT = 1.0, TFT = 1.0
round 3: both cooperate -> TFT = 1.0, TFT = 1.0

total: TFT = 3.0, TFT = 3.0
```

So three rounds are already enough for reciprocal pairs to outperform ALLD when
they meet each other. The failure in the synchronous well-mixed case is more
population-level: many reciprocal strategies first meet ALLD, strong selection
amplifies ALLD's immediate exploitation payoff, and synchronous global
replacement resets many pair histories before reciprocal pairs can accumulate
enough stable advantage.

Follow-up tests point to replacement schedule and selection pressure as the
bottleneck. The committed one-birth/one-death async variant with `p = 0.9`,
weaker selection (`selection_temperature = 1.0`), and 5000 simulation steps
reached mean cooperation after burn-in ≈ 0.511 across five seeds. Its
no-memory ablation fell to ≈ 0.010 and its no-persistence (`p = 0.0`) ablation
fell to ≈ 0.086, so the improvement depends on pair memory and repeated
encounters.

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_model
```

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_async_model
```

Default `partner_persistence_probability = 0.9` is set in
[`well_mixed/config/direct_reciprocity_well_mixed_config.py`](well_mixed/config/direct_reciprocity_well_mixed_config.py).

A display-only grid viewer makes this persistence visible without changing the
well-mixed mechanism. The grid positions are fixed agent-ID slots; interaction
and replacement remain global:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_grid_pygame_ui
```

The linked viewer shows that display grid and the aggregate charts in one
window, both driven by the same model state:

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.well_mixed.direct_reciprocity_well_mixed_linked_pygame_ui
```

---

## Conditions for cooperation in well-mixed populations

The table below walks from the worst case (p = 0) through progressively better
conditions. All numbers come from the replacement-schedule proof on 2026-04-30
(five seeds, 5 000 steps, 20 % burn-in fraction), except the p = 0 sync row
which uses 10 seeds from an earlier run.

| Condition | Seeds cooperating | Mean coop after burn-in | Verdict |
| --- | ---: | ---: | --- |
| p = 0, sync, strong selection | 0 / 10 | 0.019 | w ≈ 0.005 far below 0.41; memory useless |
| p = 0, async, weak selection | 1 / 5 | 0.086 | one lucky seed; 4/5 → ALLD |
| p = 0.9, sync, strong selection | 0 / 5 | 0.024 | w met; ALLD sweeps before pair histories form |
| p = 0.9, sync, weak selection | 2 / 5 | 0.226 | bimodal: possible but unreliable |
| p = 0.9, async, weak selection | 3 / 5 | 0.511 | bimodal: more likely but not guaranteed |
| p = 0.9, async, weak — memory off | 0 / 5 | 0.010 | reciprocal strategies blind; ALLD always wins |
| p = 0.9, async, weak — 1 round/step | 3 / 5 | 0.439 | slower history build-up; still bimodal |

### What each condition contributes

**Partner persistence (p > 0.41) — necessary, not sufficient.**
When p = 0, every step is a first meeting. w ≈ 1/(n − 1) ≈ 0.005, far below the
threshold. TFT's punishment is delivered to a random stranger, never the original
defector. ALLD dominates in every seed regardless of selection or replacement
schedule. Raising p to 0.9 clears the threshold (w ≈ 0.9 > 0.41) but three
further conditions must also hold.

**Pair-specific memory — necessary.**
Without memory, TFT, GTFT and WSLS cannot read their partner's previous action.
They default to cooperating every round, which makes them indistinguishable from
ALLC. ALLD exploits them unconditionally and dominates all 5 seeds even under
async weak selection with p = 0.9. Removing memory collapses cooperation from
0.51 to 0.01.

**Weak selection — necessary.**
Under strong selection (temperature = 0.18) ALLD's immediate advantage — earning
T = 1.7 in round 1 against any cooperator — is amplified before pair histories
can accumulate. ALLD sweeps all 5 seeds. Weak selection (temperature = 1.0)
flattens the fitness landscape and gives reciprocal pairs time to build history.

**Slow population turnover (async replacement) — helpful, not sufficient alone.**
Synchronous replacement turns over the entire population each step, frequently
destroying pair histories before they stabilise. One-birth/one-death replacement
changes at most one site per step, giving established pairs more time. This
shifts cooperating seeds from 2/5 (sync) to 3/5 (async). It is not sufficient
by itself: the memory and persistence ablations collapse cooperation regardless
of replacement schedule.

### Required conditions

All three of the following are required for cooperation to be **possible**:

1. **Persistence**: p > (T − R) / (T − P) ≈ 0.41
2. **Memory**: pair-specific action history enabled
3. **Weak selection**: selection pressure low enough for pair histories to
   matter before ALLD sweeps

Even with all three, outcomes are **stochastic**. In a finite population of 200
agents, ALLD can fix by drift before cooperators establish. Under the best
tested conditions (async + weak selection + p = 0.9 + memory), cooperation
emerges in roughly 3 of 5 independent runs.

### Why synchronous strong selection fails: a worked example

The following traces one representative step using the default config
(T = 1.7, R = 1.0, P = 0.0, S = −0.5, base_fitness = 1.0,
rounds_per_pair_per_step = 3, reset_memory_on_replacement = True).

**Round-by-round payoffs for a TFT–ALLD pair:**

- Round 1: TFT cooperates (first-move rule). ALLD defects.
  TFT receives S = −0.5. ALLD receives T = 1.7.
- Round 2: TFT copies ALLD's defection. Both defect.
  Both receive P = 0.0.
- Round 3: same. Both receive P = 0.0.
- **Step total: TFT = −0.5, ALLD = +1.7.**

Compare two other pairs in the same step:

| Pair | Step payoff each |
| --- | --- |
| TFT – TFT (3 rounds mutual C) | +3.0 |
| ALLD – TFT | ALLD +1.7, TFT −0.5 |
| ALLD – ALLC (5 % of initial pop) | ALLD +5.1, ALLC −1.5 |
| ALLD – ALLD | 0.0 |

**Fitness = base_fitness + step payoff:**

| Agent situation | Fitness |
| --- | --- |
| ALLD exploiting ALLC | 1.0 + 5.1 = **6.1** |
| TFT with TFT | 1.0 + 3.0 = **4.0** |
| ALLD exploiting TFT | 1.0 + 1.7 = **2.7** |
| ALLD with ALLD | 1.0 + 0.0 = **1.0** |
| TFT exploited by ALLD | 1.0 − 0.5 = **0.5** |
| ALLC exploited by ALLD | 1.0 − 1.5 = **−0.5** |

**Softmax selection probability** is proportional to exp((f − f_max) / temperature),
centred on the maximum fitness (6.1) to avoid overflow. With f_max = 6.1:

| Agent situation | Strong selection (T = 0.18) | Weak selection (T = 1.0) |
| --- | --- | --- |
| ALLD exploiting ALLC | exp(0) = 1.0 (reference) | exp(0) = 1.0 |
| TFT with TFT | exp(−11.67) ≈ 8 × 10⁻⁶ | exp(−2.1) ≈ 0.12 |
| ALLD exploiting TFT | exp(−18.89) ≈ 6 × 10⁻⁹ | exp(−3.4) ≈ 0.03 |
| TFT exploited by ALLD | exp(−31.11) ≈ 3 × 10⁻¹⁴ | exp(−5.6) ≈ 0.004 |

Under strong selection the single ALLD-exploiting-ALLC site concentrates
essentially all selection weight. The TFT–TFT pair that earned fitness 4.0 is
10⁵× less likely to be copied than that ALLD. Under weak selection the
TFT–TFT pair (0.12) is 12 % as likely to propagate as the dominant ALLD,
so multiple strategies remain in the running.

**Population-level pairing at step 1 (n = 200, default initial frequencies):**

The initial mix is 55 % ALLD (110), 15 % TFT (30), 15 % GTFT (30), 10 % WSLS
(20), 5 % ALLC (10). With random pairing, the expected counts of agents in each
situation are:

| Agent situation | Expected count | Fitness |
| --- | ---: | ---: |
| ALLD exploiting ALLC | ≈ 5–6 | 6.1 |
| TFT / GTFT / WSLS with reciprocal partner | ≈ 32 | 4.0 |
| ALLD exploiting a reciprocal agent | ≈ 44 | 2.7 |
| ALLD with ALLD | ≈ 60 | 1.0 |
| TFT / GTFT / WSLS exploited by ALLD | ≈ 44 | 0.5 |
| ALLC exploited by ALLD | ≈ 5–6 | −0.5 |

Most reciprocal agents (~44 of 80) are paired with ALLD in the very first step,
earning fitness 0.5. Only ~32 find another reciprocal partner and earn 4.0.

**Aggregate selection weight per group under strong selection (T = 0.18):**

Multiply per-agent weight by count. All weights are relative to an ALLD-ALLC
agent (= 1.0):

| Group | Count | Per-agent weight | Group total weight |
| --- | ---: | ---: | ---: |
| ALLD exploiting ALLC | ≈ 5.5 | 1.0 | **≈ 5.5** |
| Reciprocal with reciprocal | ≈ 32 | ≈ 8 × 10⁻⁶ | ≈ 0.00026 |
| ALLD exploiting reciprocal | ≈ 44 | ≈ 6 × 10⁻⁹ | ≈ 0.00000027 |
| Everything else | ≈ 118 | ≤ 10⁻¹⁰ | ≈ 0 |

The ~5–6 ALLD-exploiting-ALLC agents hold virtually 100 % of the selection
weight. With 200 synchronous replacement draws, every site samples a parent
almost exclusively from that tiny group. The entire population is overwritten
by copies of ALLD in one step.

Under weak selection (T = 1.0) the same ALLD-ALLC group holds weight ≈ 5.5,
but the reciprocal-with-reciprocal group now contributes ≈ 32 × 0.12 = 3.8,
and ALLD-exploiting-reciprocal contributes ≈ 44 × 0.03 = 1.3. Total weight
≈ 11. Reciprocal strategies still lose ground but are not wiped out in one step:
roughly 35 of the 200 offspring are reciprocal (from TFT–TFT pairs), giving
them a foothold for the next step.

**The cascade under strong selection:**

- Step 1: ~5–6 ALLD-ALLC pairs dominate. Synchronous replacement fills ≈ 200
  sites with ALLD. ALLC is eliminated. Reciprocal strategies near-zero.
- Step 2: all pairs are now ALLD–ALLD (fitness 1.0). No ALLC remains to
  exploit. Selection is near-flat because all agents have the same fitness.
  Mutation occasionally introduces a TFT agent.
- Step 3+: any TFT introduced by mutation is a lone reciprocal agent in a
  sea of ALLD. It is paired with ALLD, earns fitness 0.5, and is 10³× less
  likely to be copied than an ALLD-ALLD agent (fitness 1.0, weight 1.0 at
  the new f_max). TFT cannot establish. ALLD fixes permanently.

**Why weak selection can recover (sometimes):**

With weak selection, ~35 reciprocal agents survive step 1. In step 2, ALLC is
gone, so the fitness landscape inverts: ALLD-ALLD pairs earn 1.0 while the
surviving reciprocal-with-reciprocal pairs earn 4.0. If enough reciprocal
agents survived step 1 to find each other in step 2, they now have the fitness
advantage. Whether this rescue happens is stochastic: it depends on whether the
~35 survivors happen to be paired with each other or with ALLD. In 2 of 5 seeds
they do; in 3 of 5 they do not.

**How synchronous replacement destroys pair histories:**

Say agents A (TFT) and B (TFT) have been paired for several steps and built
mutual cooperation history with `last_action[A,B] = last_action[B,A] = C`.

1. Step t: A and B play 3 cooperative rounds, each earning fitness 4.0.
2. Synchronous replacement: every site in the population simultaneously samples
   a new parent from the global fitness-weighted distribution. A's site picks
   parent X (most likely ALLD under strong selection). B's site independently
   picks parent Y.
3. Both A and B are overwritten. `reset_memory_on_replacement = True` wipes all
   pair memory at their positions.
4. Step t + 1: the new agents at A's and B's positions are strangers to each
   other, starting with blank memory. The cooperative history is gone.

The pair history never accumulates long enough for A and B's fitness to exceed
ALLD's one-step exploitation payoff. The cooperation signal is erased as fast
as it is built.

**How async replacement lets histories survive:**

Under one-birth/one-death replacement only one site changes per step.

1. Step t: A (TFT) and B (TFT) play cooperatively, each earning fitness 4.0.
2. Replacement: one site C (say, an ALLD) is chosen to die uniformly at random.
   One parent is chosen to reproduce by fitness weight (C is replaced).
3. A and B both survive. Their pair-specific memory carries over to step t + 1.
4. Over many steps A and B consistently earn fitness 4.0. Selection gradually
   promotes TFT. ALLD agents, once they have exhausted the small ALLC minority,
   earn 0.0 against each other — far below the TFT–TFT pair's 4.0.

The pair history persists long enough to produce a durable fitness advantage for
reciprocal strategies.

### Conclusion: stability vs invasion

**Pure direct reciprocity in a well-mixed population can reliably maintain
cooperation if reciprocal cooperators are already common and unconditional
cooperators (ALLC) are absent. It cannot reliably produce cooperation from a
minority.**

The Nowak condition w > 0.41 is met with p = 0.9. But the condition describes
evolutionary stability — TFT resisting ALLD invasion — not the ability to invade
an ALLD-majority population. Those are different problems:

- **Stability** (TFT resists ALLD when TFT is common): the condition w > 0.41
  is sufficient. TFT–TFT pairs earn 4.0; any invading ALLD earns 2.7 in round 1
  then 0.0 as TFT retaliates, so ALLD cannot spread.
- **Invasion** (TFT spreads when TFT is rare): the condition is not sufficient.
  When rare, TFT almost always meets ALLD first. That encounter yields fitness
  0.5 for TFT, while the typical ALLD in the population earns fitness ~1.0
  (meeting other ALLD). TFT is below the population average and is selected out
  before pair history can accumulate. The rare TFT even makes things worse: the
  one ALLD it meets earns fitness 2.7 instead of 1.0, creating a locally
  super-fit ALLD that accelerates its removal.

**What the stability-vs-invasion proof shows (2026-05-01, five seeds, 5 000 steps,
async + weak selection + p = 0.9):**

| Scenario | Initial mix | Seeds cooperating | Mean coop |
| --- | --- | ---: | ---: |
| `coop_majority_no_allc` | 95 % reciprocal, 5 % ALLD, **0 % ALLC** | **5 / 5** | **0.985** |
| `coop_majority_with_allc` | 90 % reciprocal, 5 % ALLD, 5 % ALLC | 3–4 / 5 | 0.681 |
| `alld_majority` | 55 % ALLD, 40 % reciprocal, 5 % ALLC | 3 / 5 | 0.511 |
| `rare_invaders` | 95 % ALLD, **5 % reciprocal, 0 % ALLC** | 4 / 5 | 0.501 |

The clean stability test (`coop_majority_no_allc`) confirms the claim: 5/5 seeds
maintain cooperation with mean cooperation 0.985. When ALLC is absent, an ALLD
invader can earn at most 2.7 (one exploit against TFT, then mutual defection),
while TFT–TFT pairs earn 4.0. ALLD cannot grow.

The confound is **ALLC**. Any unconditional cooperators in the population give
ALLD a fitness of 6.1 (3 rounds of exploitation, fitness = 1.0 + 5.1). That
signal is so strong under any selection pressure that it can destabilise even a
cooperator majority (`coop_majority_with_allc`: one seed lost to ALLD despite
starting at 95 % reciprocal). The `rare_invaders` scenario succeeds in 4/5
seeds for the same reason: it has no ALLC, so ALLD tops out at 2.7.

**ALLC is not a cooperator in any useful sense under these dynamics.** It
provides no defence against exploitation and actively endangers every reciprocal
strategy around it.

**What is needed for cooperation to emerge from scratch:**

From a minority of reciprocal strategies in an ALLD majority, cooperation cannot
emerge reliably without some form of assortment — a mechanism that lets
cooperators meet each other more often than chance:

- **Kin selection**: cooperators share genetic identity and are preferentially
  paired with relatives.
- **Network reciprocity**: a fixed interaction graph (the `pair_game` model)
  lets cooperator clusters form. Cooperators in the interior predominantly meet
  other cooperators before ALLD reaches them from the edges.

In the `pair_game` model both mechanisms operate simultaneously. Direct
reciprocity stabilises cooperation within established pairs; network reciprocity
shields cooperator clusters long enough for pair histories to build. Removing
either collapses cooperation. This is why Nowak treats them as separate
mechanisms — direct reciprocity alone is not sufficient for reliable emergence.

---

## Step 3 — Spatial structure adds network reciprocity

**Model:** [`pair_game/`](pair_game/)

Placing agents on a 2D grid and restricting both interactions and Moran
replacement to local neighbors adds a second mechanism on top of direct
reciprocity: **network reciprocity**. Cooperators can form spatial clusters and
preferentially interact with each other, even before any trust has been
established.

This means:
- Pair memory and repeated rounds sustain cooperation within established pairs
  (direct reciprocity).
- The grid prevents ALLD from reaching the interior of a cooperator cluster
  (network reciprocity).

Both mechanisms are active simultaneously. A 5% spatial cluster of TFT agents
in a sea of ALLD survives and spreads on the grid. The ablation tests in
[`pair_game/utils/proof_of_mechanism.py`](pair_game/utils/proof_of_mechanism.py)
confirm that removing either memory or repeated rounds collapses cooperation —
but spatial clustering is also load-bearing.

**Result: Cooperation emerges more robustly, but the mechanism is no longer
pure direct reciprocity.**

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.pair_game.direct_reciprocity_pair_game_model
```

See [`pair_game/`](pair_game/).

---

## Note: Continuous interaction-kernel model

**Model:** [`continuous/`](continuous/)

A separate, continuous-trait implementation wraps the shared interaction-kernel
engine. Agents carry a cooperation capacity h and pair-specific partner memory.
Help is routed preferentially back toward neighbors that helped before. This
model uses a benefit–cost framework rather than a Prisoner's Dilemma and is not
directly comparable to the discrete-strategy models above.

```bash
./.conda/bin/python -m moran_models.nowak_mechanisms.direct_reciprocity.continuous.direct_reciprocity_model
```

See [`continuous/`](continuous/).

---

## Summary

| | `well_mixed` p = 0.0 | sync `well_mixed` p = 0.9 | async `well_mixed` p = 0.9 | `pair_game` |
| --- | --- | --- | --- | --- |
| Re-encounter probability w | ≈ 0.005 | ≈ 0.9 | ≈ 0.9 | High (fixed neighbors) |
| Condition w > 0.41 | No | Yes | Yes | Yes |
| Memory enabled | Yes | Yes | Yes | Yes |
| Spatial clustering | No | No | No | Yes |
| Active mechanisms | None | Direct reciprocity attempt | Direct reciprocity | Direct + network reciprocity |
| Cooperation emerges | Never (0/10 seeds) | Rarely (0/5 strong, 2/5 weak) | Sometimes (3/5 seeds, stochastic) | Yes (robust) |

---

## References

- Nowak, M. A. (2006). *Five rules for the evolution of cooperation*. *Science*, 314(5805), 1560–1563. https://doi.org/10.1126/science.1133755
- Axelrod, R., & Hamilton, W. D. (1981). *The evolution of cooperation*. *Science*, 211(4489), 1390–1396. https://doi.org/10.1126/science.7466396
