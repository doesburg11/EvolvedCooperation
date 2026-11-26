# Indirect Reciprocity Ladder: From the Threshold Model to an Ecological Model (plan, 2026-11-26)

**Status: plan drafted 2026-11-26 at the user's request and revised the same day after a Codex review (gpt-6.1-sol,
medium); rung 1 agreed the same day and **met** (20/20 against 0/20 shuffled; an oracle-label baseline, not yet indirect reciprocity by the definition; `RESULTS.md`). Next: rung 2, not yet pre-registered.** Built like the kin-selection ladder (`../../kin_selection/ladder/`): start from a model that
works and add one ingredient per rung, each rung tested against a control before the next.

## Why this ladder

The project's goal is human cooperation. Indirect reciprocity (help those with a good reputation; your own
reputation then earns you help from third parties) is a leading candidate for what is distinctively human, because
at scale it needs language and gossip (Alexander 1987; Nowak & Sigmund 1998, 2005). Two same-day screens in
`ecological_models/partner_choice_fairness/` used reputation for partner choice in a sharing market and failed
(registered KILL twice); classic reputation-gated helping, by contrast, works in this repo's threshold model.
So the ladder starts there.

## Definition used on this ladder

A result counts as **indirect reciprocity** here only if all of these hold:

1. **A real cost.** Each act of help costs the donor c and returns nothing to it from that recipient in that
   encounter.
2. **Return through reputation, not kin or personal experience.** Whether a donor helps depends on third-party
   information about the recipient (its reputation), not on what that recipient previously did *to this donor*
   (that would be direct reciprocity) and not on relatedness. Help counts as indirect reciprocity only once
   reputation is earned by actions (from rung 2): action → reputation → help from others. Where a rung adds
   structure that could create relatedness (local births) or repeated personal interaction (space, memory), its
   control must remove that route, or the result is reported as *consistent with* indirect reciprocity.
3. **Against a control that removes the information.** The registered test compares a test arm with an arm in
   which reputations are **shuffled** (each observer sees the reputation of a random other individual, so the
   distribution of reputations is kept but its link to behaviour is cut). Everything else is unchanged.

**Two sub-cases**, as kin selection has two: **maintained** (discriminators resist invasion by defectors from a
common start, registered at about 90% discriminators) and **spreads from rare** (discriminators rise from a rare
start). In Nowak's simplest form indirect reciprocity is bistable: discriminators resist defectors above
q\* ≈ c/b but a rare discriminator does not spread (the threshold model confirmed both). So the ladder's main
criterion is **maintenance**; spread from rare is a side rung of its own. Maintenance over a finite horizon from a
90% start shows only that, not general invasion resistance. From rung 4 on (when unconditional cooperators can be
present), the endpoint is the **cooperation rate** together with resistance to defectors, not the share of
discriminators, since stable cooperative mixtures of discriminators and unconditional cooperators exist.

**The goal** (as on the kin ladder): indirect reciprocity in an **ecological setting**, with energy reserves,
limited renewable food, death by starvation, births that need resources and free space, and individuals that move,
so that population size follows resources; ultimately a PredPreyGrass-style world in which hunters share food
with others according to reputation.

## Rules carried over from the kin ladder

- One ingredient per rung, and a **theory screen** (closed form or deterministic recursion, no simulation) before
  any code for that rung.
- Each rung is pre-registered (test, control, endpoint, seeds, kill rule) and reviewed by Codex before code.
- **At most two attempts per rung.** On failure, take a smaller step towards the same ingredient, never patch the
  lower rungs; a second attempt gets its own pre-registration after the first result; after two failed attempts
  the rung gets a hard stop and the user decides.
- Every pre-registration fixes seeds and arm pairing, the generation-count convention, and what counts as no
  verdict (incomplete or invalid data).
- The definition's three conditions are checked on every rung, not only at the end (the kin ladder found late that
  its early successes were weak altruism).
- Results go into `RESULTS.md` from the first result on; the site gets a "Definition and Progress" page like the
  kin ladder's once rung 1 has a result.

## The rungs (planned; each needs its own agreement)

| Rung | Population | Ingredient added | Why this order |
| --- | --- | --- | --- |
| 0 ✓ | Fixed (Wright-Fisher, N = 1000) | **Base:** Nowak's threshold model, `threshold_models/indirect_reciprocity_discriminators` (reproduced 2026-11-26: discriminators resist ALLD exactly above q\*; a rare discriminator loses) | Working start |
| 1 ✓ | Fixed | **Sampled, sequential encounters** (k donor turns per generation with random recipients). Reputation still the strategy label: an **oracle-label baseline**, a plumbing check, *not* indirect reciprocity by the definition | Needed before reputations can change over time; theory unchanged in expectation |
| 2 | Fixed | **Reputation earned from actions** under the *standing* norm, public, every act observed (full assessment table fixed in rung 2's pre-registration) | First rung that can meet the definition. Standing has an advantage over image scoring under the errors and information studied (Leimar & Hammerstein 2001; Panchanathan & Boyd 2003); not a guarantee under later extensions |
| 2b | Fixed | **Partial observation:** each act observed with probability < 1 (separate from the probability of consulting a reputation) | |
| 3a | Fixed | **Execution errors** (an intended help fails) | |
| 3b | Fixed | **Assessment errors** (an observer records the wrong reputation) | |
| 4a | Fixed | **Unconditional cooperators** (ALLC, ALLD, DISC), no mutation | ALLC may drift in and open the door to ALLD; mixtures can also be stable |
| 4b | Fixed | **Mutation** among the three strategies | |
| 5a | Fixed | **Private assessment:** each observer keeps its own view of others (disagreement) | Known to undermine norms (Hilbe et al. 2018) |
| 5b | Fixed | **Gossip:** views spread between individuals | The human-specific channel; may repair 5a (Radzvilavicius et al. 2019) |
| 6 | Fixed | **Overlapping generations** (death-birth updating) | Bridge to ecology |
| 7a | Fixed | **Energy accounting:** help is an energy transfer, fitness from energy | Start of the ecological block |
| 7b | Fixed → | **Births need an energy threshold** | |
| 8a | Not fixed | **Limited renewable food** | |
| 8b | Not fixed | **Starvation** | |
| 9 | Not fixed | **Births need free space** (population size follows resources) | Where the kin ladder stalled; may need a ported published model, as the kin ladder's step 5 did |
| 10 | Not fixed | **Movement in space** (encounters by proximity; control must remove kin and personal-experience routes) | |
| Goal | Not fixed | PPG-style hunters sharing catches by reputation | |

Spread from rare is tested as a side rung once a rung's maintenance result is met, not as part of the main line.

## Rung 1: sampled, sequential encounters, oracle-label baseline (pre-registration)

**Status: agreed with the user 2026-11-26 (about 16:45 CET), before any rung-1 model code.** The theory script
`rung1/theory.py` (written after agreement, before model code) reproduces the registered screen values: threshold
0.3579, boundary 33.5%, payoffs 1.760 / 1.081, test 0.99987, q = 0.2 0.0283, rare start 0.00103 at generation 100;
shuffled control 0.0287 against 0.0288 (the script rounds the DISC count to an integer each generation). The payoff-noise value (SD 0.062 of the population-mean payoff difference) is not in the script; Codex's code review recomputed it independently (0.0619, mean 0.6787).

**What it is:** a plumbing check that the sampled-encounter machinery reproduces rung 0. Reputation is still the
fixed strategy label, so a pass is **not** indirect reciprocity by the definition (no action → reputation link);
it is reported as an oracle-label baseline.

**Change from rung 0, only this:** instead of every ordered pair meeting once, each generation runs k = 10 rounds;
in each round every individual is donor once to a recipient drawn uniformly from the other N − 1 (independently per
donor; recipients may repeat). The donor knows the recipient's label with probability q, drawn per encounter, and
helps a DISC recipient always and an ALLD recipient only when it does not know (as in rung 0). **Fitness:**
1 + s × (benefits received − costs paid) / k, then rung 0's Wright-Fisher reproduction.

**Control (shuffled reputation):** in each encounter, when the donor "knows", it sees the label of an individual
drawn uniformly from the population excluding donor and recipient, drawn independently per encounter (the
reputation distribution is preserved in expectation; the link to the recipient is cut). Everything else equal.

**Theory screen (registered values from Codex's review, 2026-11-26; to be reproduced by the rung's own theory
script before code):** at a 90% DISC start, rung 0's exact threshold is q = 0.358 (large-N c/b = 0.333); the
deterministic unstable boundary at q = 0.6 is 33.5% DISC. Deterministic recursion with expected payoffs: test
(q = 0.6, 90% start) reaches DISC 0.9999 by generation 100; shuffled control falls to 0.029 by generation 100;
q = 0.2 falls to 0.028; rare start (5%) falls to 0.001. Payoff noise from k = 10: standard deviation of the
population-mean payoff difference about 0.062 against a mean difference of 0.679.

**Test:** b = 3, c = 1, s = 0.1, N = 1000, q = 0.6, start 90% DISC / 10% ALLD, generations 1-500 (generation 500
is the 500th reproduction), seeds 0-19 paired across arms. **Endpoint:** DISC share ≥ 0.8 after generation 500.
**Met if** the test arm meets the endpoint in ≥ 16/20 seeds and the shuffled control in ≤ 4/20. **No verdict** if
any run is missing or invalid. Also reported, not tests: q = 0.2 (expected to fail in both arms) and a rare start
(5% DISC, expected not to spread).

**Compute:** minutes. **Attempts:** at most two; a second gets its own pre-registration.
