# Draft Pre-registration: Gossip after Private Assessment

**Status: registered, 2026-11-26.** This is a separate follow-up study to the completed indirect-
reciprocity ladder, not a continuation of it. Rung 5a remains a valid **not
met** result, and the original ladder remains closed at rung 4b. The frozen
implementation, tests and theory screen are in this directory.

## Question

In rung 5a, private views made a discriminator's justified refusal look bad to
observers who regarded the recipient as good. Can exchanging views about the
same third party reduce that disagreement enough for the **same fixed-
population maintenance test** to meet its endpoint?

The follow-up uses the opinion-copying form of gossip: a recipient of gossip
adopts a source's view of a target. This follows the basic information-
synchronization mechanism studied by Kawakatsu, Kessinger and Plotkin (2024)
and Murase and Hilbe (2024). It is not a claim that either paper's result will
reproduce under this ladder's different model.

## Frozen Base

All donation, assessment, reproduction and mutation rules remain rung 5a's:

- `N = 1000`, `k = 10`, benefit `b = 3`, cost `c = 1`, selection intensity
  `s = 0.1`;
- consultation `q = 0.8`, observation `o = 0.5`, execution error `e = 0.1`,
  assessment error `a = 0.02`, mutation `μ = 0.001`;
- simple standing, private binary views reset to good at each generation's
  start, and 2,000 generations; and
- start: 10% ALLC, 80% DISC, 10% ALLD; fresh paired seeds 4000–4099;
- endpoints: cooperator share at least 0.8 at generation 500 **and** mean
  cooperator share at least 0.8 over generations 1,501–2,000, in the same
  run.

This is maintenance from a cooperative start, not recovery or spread from rare.

## Only New Ingredient: Accurate, Target-Specific Gossip

Each generation keeps the same ten encounter rounds, but is split in two:

1. rounds 1–5: the rung-5a private assessment and helping process;
2. one gossip phase; then
3. rounds 6–10: the same private assessment and helping process, now able to
   use the views shaped by gossip; reproduction follows all ten rounds.

The main gossip arm uses the single-source form analysed by Kawakatsu,
Kessinger and Plotkin (2024). One source `u` is drawn uniformly per generation.
For every target `t` other than `u`, and every receiving observer `v` other
than `u` and `t`, the receiver independently consults the source with fixed
probability `Q = 0.8`. On consultation it sets its view of target `t` to the
source's view of that **same target**. The exclusions matter: the rung-5a
matrix has no meaningful self-view, and the source never overwrites its own
view. Thus a phase has `(N - 1) × (N - 2)` eligible cells, each consulted with
probability `Q`. The source and receiver do not observe a new action; gossip
has no payoff, reproductive or mutation effect; it copies an existing opinion.

The dose is fixed before model code. Under independently exchangeable binary
source and receiver views, the cited calculation gives the expected
disagreement multiplier `E[D']/E[D] = 1 − Q²`; thus `Q = 0.8` gives `0.36`.
The accompanying screen enumerates that expectation. It is a synchronization
screen, not an identity for every fixed configuration and not a prediction of
cooperation. Its success does not guarantee that the endpoint will be met.

## Registered Arms

Each arm uses all 100 seeds and the frozen base above (300 runs total). Within
each seed, T, N and S share the same initial population and the same legacy
NumPy stream for encounters, reproduction and mutation; this is what permits
an exact rung-5a replay in N. Gossip has its own seed-keyed stream; N consumes
none of it. Diagnostics have a third stream and never change the model path:

| Arm | Change after private assessment | Role |
| --- | --- | --- |
| **T: target-specific gossip** | Receiver copies source's view of the same target | Main test |
| **N: no gossip** | No post-assessment copying | Fresh replication of rung 5a's private-view condition |
| **S: sham gossip** | Receiver copies the source's view of a different target `z` into target `t` | Checks the registered alternative copying rule |

For sham gossip, one uniform random derangement of the eligible targets is
drawn per phase: for each target `t`, it chooses a different eligible target
`z`, and every receiver of `t` consults the source's view of that same `z`.
This preserves the shared-source structure, volume and timing of T while
deliberately damaging target identity. It is therefore a mechanism-specific
negative control, not the primary causal comparison and not the existing
shuffled-reputation control.

## Registered Decision Rules

**Restored maintenance** only if both hold:

1. at least 80 of 100 T runs meet both endpoints;
2. in the paired T-versus-N comparison, let `b` be seeds where T passes and N
   fails, and `c` seeds where N passes and T fails. `b − c` is at least 20 and
   the exact one-sided McNemar probability `P[Binomial(b + c, 0.5) ≥ b]` is
   below `0.01`.

The `N` arm is the causal comparison for adding gossip. If T meets the absolute
endpoint but misses the paired comparison, the outcome is valid but
**inconclusive about gossip**. If T misses its endpoint, the follow-up is **not
met**, regardless of any diagnostic improvement. The sham result does not alter
either verdict: it supports a target-specific interpretation only if T also
beats S under the same paired rule (`b − c ≥ 20`, exact one-sided McNemar
`p < 0.01`), with `b` and `c` defined for T/S. This comparison has no separate
S success threshold. If S itself reaches 80 of 100 endpoint successes, that is
reported as evidence that this sham was not a clean negative control, not as an
invalid run.

## Mechanism Diagnostics

The implementation must report, for each arm:

- agreement available to later decisions: per seed and generation, 10,000
  eligible observer-pair/third-party-target triples drawn without replacement
  from a diagnostic stream, fixed across the three arms and measured both
  immediately before and immediately after the gossip phase, before round 6;
- the existing disagreement penalty: among observations of an intentional DISC
  refusal, the share for which the observer judged the recipient good before
  flips, reported separately for rounds 1–5 and 6–10;
- target-specific copy attempts, bit-changing copies and no-op copies (and the
  corresponding sham counts);
- the good-view marginal for each target strategy, the numerator and denominator
  of the disagreement penalty (reported as undefined when its denominator is
  zero), and successful helps per encounter; and
- the existing encounter, observation, flip, mutation and strategy-count
  audits.

These diagnostics are explanatory only. They cannot replace the endpoint and
control decision rules.

## Validity and Tests Required Before a Run

The new implementation must preserve rung 5a exactly when gossip events are
disabled. Unit and independent-reference tests must show:

1. a scripted target-specific event changes exactly one receiver-target view,
   and a scripted no-op leaves the matrix unchanged but increments its own
   count;
2. a scripted sham event copies the source's other-target view, not its view of
   the displayed target;
3. source, receiver and target exclusions are uniform and no self-view is
   written; an independent reference phase checks the full per-cell consultation
   mask and the one-per-phase sham derangement;
4. with identical supplied views, actions and random draws, the local encounter
   payoff and reproduction functions match rung 5a exactly; a scripted gossip
   event may nevertheless change a later DISC decision and hence a trajectory;
5. with zero consultation probability, the private-view trajectory and counters
   exactly replay a rung-5a run on a separate, fixed encounter/reproduction
   random stream; and
6. corrupted target indexing, a wrong source row, an illegal self-view and a
   changed non-target cell are caught.

All 300 runs must pass the existing stored-view checks, private-standing sanity
check, trajectory and mutation audits, plus exact gossip-count and view-update
audits. Gossip, encounter/reproduction and diagnostic random draws must use
separate streams, so adding gossip does not change the no-gossip path merely by
consuming random numbers. Any failed check gives **no verdict** pending one
documented technical repair of the frozen design.

## Compute Guardrail

Before launch, a fixed benchmark runs each arm with seed 9999 for 100
generations; only CPU time is retained. The projected cost is the sum of each
arm's benchmark extrapolated to its 100 registered seeds. The stage may launch
only if that total is at most 45 CPU-hours. Every worker writes a generation-0
heartbeat before model construction and every 100 generations thereafter. A
run error, failed in-model check, a worker that never writes its first heartbeat
within 15 minutes, a 15-minute stale heartbeat, or total completed-plus-live
worker CPU use above 45 hours stops the stage with no verdict. Stopped outputs
are retained; one documented technical repair must rerun the whole frozen arm
and seed set.

## Interpretation Limits

A restored-maintenance result would show that this exact accurate,
target-specific gossip rule meets the finite-horizon maintenance endpoint and
outperforms its paired no-gossip baseline under the tested private-view
conditions. It would not establish that gossip generally
solves private assessment, that human gossip works this way, recovery from
defection, spread from rarity, indefinite stability or ecological cooperation.

## References

- Kawakatsu, M., Kessinger, T. A., and Plotkin, J. B. (2024). *A mechanistic
  model of gossip, reputations, and cooperation*. Proceedings of the National
  Academy of Sciences, 121, e2400689121.
- Murase, Y., and Hilbe, C. (2024). *Indirect reciprocity under opinion
  synchronization*. Proceedings of the National Academy of Sciences, 121,
  e2418364121.
