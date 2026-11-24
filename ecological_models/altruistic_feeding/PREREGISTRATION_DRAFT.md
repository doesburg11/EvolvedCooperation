# Altruistic feeding (Taylor-Davies et al. 2024): replication pre-registration (DRAFT, 2026-11-24)

**Status: draft for discussion; not agreed, no code run, no data.** Revised once after a Codex review
(gpt-6.2-sol, medium, 2026-11-24), which read the paper and the authors' code at the pinned commit.

## Why this paper

On the site's stepwise table
([Kin Selection: Definition and Progress](https://humanbehaviorpatterns.org/evolved-cooperation/kin-selection-progress)),
goal A is kin selection through parental care in a full ecology: energy, limited renewable food, starvation, births
into free space and agents that move. Every achieved step so far has a fixed population. Taylor-Davies, Hamon,
Boulet and Moulin-Frier (2024), *Emergent kin selection of altruistic feeding via non-episodic neuroevolution*
(arXiv 2411.10536; EvoStar/ALIFE proceedings 2025, doi 10.1007/978-3-031-90062-4_31; PDF in the Dropbox collection,
Kin selection index) report feeding of own infants in such an ecology. Following the agreed rule to port known
mechanisms rather than invent new rungs, this replicates the paper's main computational claims. It is a **candidate
ecology for goal A**; whether it meets the site's definition is a separate question (last section).

| Goal A needs | Taylor-Davies et al. 2024 (paper and code) |
| --- | --- |
| Costly help to own offspring | `transfer` ('feed') moves one food unit (20 energy) from the actor to the agent it faces; infants (age < 100) cannot reproduce |
| Energy, starvation | energy capped at 200, death at 0 and at age 500 |
| Limited renewable food | plants regrow stochastically on a 100 × 100 grid |
| Births need free space | offspring born into the tile the parent faces, if free; at most 2500 agent slots |
| Agents move | forward, turn left, turn right |
| Controls | kin-recognition ablation; random birth locations (viscosity ablation) |

## The code, and what it does not contain

- **Authors' code:** `github.com/maxtaylordavies/EcoJAX`, last commit `24524cc` (2024-11-14, "tidying up for
  conference submission"; upstream `tboulet/EcoJAX`, co-author T. Boulet). The arXiv HTML links an anonymised copy
  (`anonymous.4open.science/r/EcoJAX-F6D4`). Its `analysis/` scripts produce the paper's figure types, and
  `gridworld.py` has the transfer action, the three infant parameters, the offspring channel and parent bookkeeping.
  Identification as the paper's code rests on these matches; the paper does not name the public repository.
- **Not in the repository** (Codex review, 70 visible commits): the paper's run configuration (overrides), the swept
  values of the three infant parameters, the seed lists, and working ablations. Random birth placement exists only as
  commented code; the offspring channel is appended unconditionally (no switch to remove it).
- **Paper versus code:**
  1. Default config: reproduction threshold 80 (paper 85; the code tests strictly `>`), reproduction cost 20 (paper
     30), energy loss 1.0 per non-idle action and 0.0 idle; the paper's "0.1 lost passively" plus a per-action cost
     cannot be set through the config alone. Transfer is exempt from the action drain, even when it fails.
  2. Birth placement: the paper says "nearest empty square" (Section 2) and "the tile their parent was facing"
     (Section 4.4); the code (commit `65c411f`) uses the faced tile.
  3. Measurement: the paper's equations count all successful feeds per mean population over the final 50k steps and
     pool events for selectivity; the authors' regression script counts only feeds to infants, uses the final 25k
     steps, and min-max scales selectivity before log(1 + x). The facing counter also counts vacant agent slots.
  4. Logging: advanced event logging is hard-coded off; enabling it hits a field-name mismatch
     (`indexes_parents_agents` against `indexes_parents`); removing the transfer action breaks the basic logger.
     Parent slots can be reused while offspring still point to them.
- **Consequence:** "unmodified code" is not possible. Stage 0 writes one **frozen patch** limited to (a) logging and
  measurement fixes, (b) a correct parent identity (unique ids, not reusable slots), (c) switches for the two
  ablations and for the energy rule, and (d) the paper's values as a config. No other model logic changes. The patch
  gets a Codex review and its own tests before any hypothesis run.

## Stage 0: environment, configuration, patch (no hypothesis test)

1. **Ask the authors** for the resolved run configs, swept values, seeds and ablation diffs (needs the user's
   go-ahead: an outward-facing request). If no answer within a set time (two weeks), **reconstruct**: the paper's text
   values, Figure 2's plotted parameter levels transcribed, and the code's behaviour where the paper is silent. A0
   then labels the replication a reconstruction.
2. Separate Python environment (not the repository's `.conda`). The authors pin JAX 0.4.24 and flax 0.8.3; the GPU here
   (RTX 5070 Ti, Blackwell) may need a newer JAX. Try the pins first, then the oldest JAX that runs on this GPU, with
   flax adjusted only as needed. Version changes are listed.
3. The frozen patch (above), its tests (parent identity across slot reuse; ablation switches change only what they
   should; measures on hand-built event logs equal the paper's equations), and a Codex review.
4. Smoke run, one seed, 5000 steps: speed and GPU memory. From it, the **design rung** is chosen from the fixed ladder
   below by the projected wall time, and recorded in amendment A0 before any hypothesis run.

**Design ladder** (the first rung that fits in about 3 GPU-days for Stage 1 is used; anything below rung 1 is reported
as a **reduced design**):

| Rung | Infant parameter values | Seeds per value | Steps (feeding-enabled) | Window |
| --- | --- | --- | --- | --- |
| 1 | all of the paper's levels | 20 | 500k | final 50k |
| 2 | all of the paper's levels | 10 | 500k | final 50k |
| 3 | three levels (lowest, middle, highest) | 10 | 500k | final 50k |
| 4 | three levels | 10 | 250k | final 25k |

Feeding-disabled runs for the infant survival rate: 100k steps, final 10k, same values and seed counts, as in the
paper.

## Measures (registered)

Primary measures follow the paper's equations; the authors' script versions are reported as a sensitivity analysis.

- **ISR** (feeding-disabled runs): 1 − infant deaths / all deaths over the window, as in the paper (a share of deaths,
  not a cohort survival probability).
- **b̂** (feeding-enabled runs): mean age at death of infants fed at least once, divided by that of infants never fed,
  minus 1, over agents that die within the window; agents alive at the end are censored (excluded). The authors'
  per-feed-count-group estimator is reported as a sensitivity analysis. If either group is empty, b̂ is undefined
  and the run is counted in the undefined tally.
- **Amount:** successful feeds in the window divided by the mean population size in the window.
- **Selectivity:** (feeds to own offspring / all feeds) − (facing events where the faced agent is own offspring /
  facing events where the faced tile holds a living agent), over the window; undefined if either denominator is 0.
- **Validity counts, per arm:** runs whose population went extinct, runs that hit the 2500 cap (and the share of
  steps at the cap), and runs with undefined measures.

## What the paper claims, and the tests

Stage 1 uses one parameter first, infant move success probability (largest slopes in the paper's Table 1).

1. **Validity first.** An arm with fewer than 90% of its runs alive to the end, or with undefined primary measures in
   more than 10% of runs, makes the stage **not interpretable** (reported, no verdict).
2. **H1 (manipulation, C1):** ISR (feeding disabled) falls, and b̂ rises, as infants become less able to move:
   Spearman correlation with the assigned parameter value across runs, one-sided, alpha 0.01; endpoints (most versus
   least hostile) reported as secondary.
3. **H2 (C2):** amount rises with b̂: OLS slope of log(1 + amount) on b̂ over runs > 0, one-sided, alpha 0.01; also
   reported against the assigned parameter value (b̂ is computed from the same runs, so the parameter is the cleaner
   regressor) with effect sizes and seed-bootstrap confidence intervals.
4. **H3 (C3):** as H2, for selectivity (paper's equation; log(1 + x) defined since selectivity lies in (−1, 1)).
5. **Verdict:** **replicated** if H1-H3 are met; **partly** if H1 and one of H2/H3; **not replicated** otherwise. The
   paper's Table 2 (amount rises with selectivity) is reported descriptively.
6. **Interim kill check:** after all levels are run with half the seeds, if the slope of log(1 + amount) on the
   assigned parameter has the wrong sign (amount does not rise as infants become less able to move), Stage 1 stops as
   **not replicated (stopped at interim)**. The comparison is within the same batch.
7. **Then:** if replicated, the other two parameters (infant food-energy proportion, eat success probability) with the
   same rules, as budget allows.

**Stage 2 (only if Stage 1 replicates): ablations (C4, C5).** Same levels and seeds (paired by seed). KR off: the
'is own offspring' channel set to zero (the 'is infant' channel kept). Random births: offspring placed on a uniformly
random empty tile, with the same birth eligibility as in the baseline; simultaneous births to the same tile resolved
as the baseline resolves them. **H4 / H5:** in one OLS fit per outcome with the parameter value as the regressor, the
ablation × parameter interaction is negative (one-sided, alpha 0.01); scored for amount and selectivity separately,
and an ablation is said to weaken feeding only if both are met. b̂ overlap between ablated and baseline runs is
reported. The paper showed weakening graphically across all three sweeps; this is a narrower confirmatory test.

## Against the site's definition (a reading, reported after the replication)

- **Cost:** a feed debits 20 energy from the feeder. That is an immediate energy cost; a net cost in survival or
  reproduction (condition 1) is **not established** without a counterfactual, for example the feeder's own
  reproduction with and without feeding, which this design does not have.
- **Relatives:** recipient identity (own offspring) is checked once parent identity is fixed (patch item b); the
  benefit to recipients (b̂) is observational.
- **Spread from rare against a control (condition 3): not what the paper tests.** Policies start from random weights,
  so feeding starts at a random-action level, and the outcome is a level-versus-benefit relationship. Neither
  ablation redirects the benefit away from relatives by design. A positive replication therefore makes this a
  **candidate ecology for goal A**, not a result that meets the definition. Meeting it would need a separate
  pre-registration: a measured low-feeding start, a pre-set endpoint, a net-cost measure, and a control that sends
  the same feeding to non-relatives.
- **Population rule:** births only into a free faced tile, hard cap of 2500: the not-fixed block of the table, like
  steps 7 and 8; how often the cap binds is reported.

## Budget and hard stop

- Stage 0: about two working days including the patch and its review; **stop** if the code cannot run on this GPU
  without changing model logic, then decide with the user.
- Stage 1: at most about 3 GPU-days at the chosen rung. Stage 2: at most about 6 GPU-days. GPU memory checked before
  any concurrent run (16 GB card).
- A budget stop is reported as **incomplete**, not as not replicated. No tuning beyond the paper's configuration; a
  failure is a reported result, not a reason for variants.

## Predictions (mine, before any data)

- Stage 0 runs on this GPU with only the frozen patch: about 65%. The authors send configs: about 40%.
- H1: about 90%. H2: about 70%. H3: about 55%. Replicated: about 50%.
- Given Stage 1 replicates: H4 (KR off weakens both) about 50%; H5 (random births weaken both) about 55%.

## Limits

- The authors' codebase with a measurement and ablation patch: a replication of the computational result, not an
  independent implementation; if the configs are reconstructed, the replication is approximate.
- Neuroevolution with fixed lifetime weights; no learning. Kin recognition is an observed bit, not evolved.
- b̂ is an outcome of the same runs, so H2/H3 on b̂ are associations; the assigned parameter is the manipulated
  variable.
