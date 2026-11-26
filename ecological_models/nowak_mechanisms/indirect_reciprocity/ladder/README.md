# Indirect Reciprocity Ladder: From the Threshold Model to an Ecological Model (plan, 2026-11-26)

**Status: plan drafted 2026-11-26 at the user's request and revised the same day after a Codex review (gpt-6.1-sol,
medium); rung 1 agreed the same day and **met** (20/20 against 0/20 shuffled; an oracle-label baseline, not yet indirect reciprocity by the definition; `RESULTS.md`). Rung 2 (reputation earned by actions, simple standing) **met** the same day (20/20 against 0/20 shuffled), the ladder's first indirect-reciprocity result by its definition. Rung 2b (each act observed with probability 0.5) **met** the same day (20/20 against 0/20). Next: rung 3a, not yet pre-registered.** Built like the kin-selection ladder (`../../kin_selection/ladder/`): start from a model that
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
| 2 ✓ | Fixed | **Reputation earned from actions** under the *standing* norm, public, every act observed (full assessment table fixed in rung 2's pre-registration) | First rung that can meet the definition. Standing has an advantage over image scoring under the errors and information studied (Leimar & Hammerstein 2001; Panchanathan & Boyd 2003); not a guarantee under later extensions |
| 2b ✓ | Fixed | **Partial observation:** each act observed with probability < 1 (separate from the probability of consulting a reputation) | |
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

## Rung 2: reputation earned from actions, simple standing (pre-registration)

**Status: agreed with the user 2026-11-26 (about 16:55 CET), before any rung-2 model code; draft revised the same
day after a Codex review (gpt-6.1-sol, medium).** The theory screen `rung2/theory.py` (calculation only, no simulation) was written and run for this draft;
its values are below, with Codex's independent corrections.

**What it is:** the first rung that can meet the ladder's definition. Reputation is no longer the strategy label:
it is a public good/bad record that each act updates, so helping earns a good reputation and refusing a good
recipient earns a bad one, and discriminators help according to that record (action → reputation → help from
others).

**Change from rung 1, only this:**

- Each individual has a public reputation, good or bad; everyone is good at birth (each generation).
- In each of the k = 10 rounds, donors act **one at a time in a random order** (a new uniform permutation each
  round), each to a recipient drawn uniformly from the other N − 1, as in rung 1.
- A DISC donor consults the recipient's reputation with probability q (drawn per encounter). Not consulting →
  helps (as in rungs 0-1). Consulting → helps if the recipient is good, refuses if bad. ALLD never helps.
- **Every act is observed** and the donor's reputation is updated at once, using the recipient's public
  reputation at the time of the act (whether or not the donor consulted it). Assessment by **simple standing**
(L3 in Ohtsuki & Iwasa 2004), which looks only at the act and the recipient, not at the donor's own record:

  | Donor's action | Recipient good | Recipient bad |
  | --- | --- | --- |
  | Helps | good | good |
  | Refuses | **bad** | good (justified) |

- This differs from Leimar & Hammerstein's (2001) standing (Ohtsuki & Iwasa's STAND), in which a *bad* donor who
  refuses a bad recipient stays bad: under simple standing an ALLD can regain a good record without ever helping
  (by refusing a bad recipient). Simple standing is chosen because it needs no second-order information (the
  donor's own record); the stricter variant would make ALLD easier to spot, so simple standing is the harder case
  here.
- Payoffs, fitness (1 + s × net / k), Wright-Fisher reproduction: as rung 1. Donor order is randomised each round
  (rung 1 used a fixed order; with fixed labels this made no difference to payoffs).

**Control (shuffled reputation):** a consulting DISC donor sees the current reputation of an individual drawn
uniformly from the population excluding donor and recipient (drawn per encounter). The assessment of the donor's
act still uses the recipient's true public reputation. Everything else equal.

**Theory screen (mean field, `rung2/theory.py`).** Without errors a DISC never refuses a good recipient, so DISC
stay good. An ALLD is good after an act only if its recipient was bad, so in steady state it is good a share
g = x_A / (1 + x_A) of the time, plus while it has not yet acted (about 1/(2k) of its recipient events). At a 90%
DISC start g ≈ 0.136, so a consulting DISC is fooled that often: effective information q_eff = q(1 − g) = 0.518
at q = 0.6. Rung 1's payoffs with q_eff in place of q give:

| Quantity | Rung 1 | Rung 2 (screen) |
| --- | --- | --- |
| q needed at a 90% DISC start | 0.358 | 0.414 |
| Unstable boundary at q = 0.6 (DISC share) | 33.5% | 67% |
| Test, q = 0.6, start 90%, generation 100 | 0.99987 | 0.9996 |
| Shuffled, q = 0.6, start 90%, generation 100 | 0.029 | 0.005 (script; ignores DISC turning bad) / 0.0058 (Codex) |
| q = 0.45, start 90%, generation 100 | | 0.971 |
| q = 0.2, start 90%, generation 100 | 0.028 | 0.006 |
| Rare start 5%, q = 0.6, generation 100 | 0.001 | 0.00003 |

So the registered test should be met with margin (the 90% start is well above the 67% boundary), but the margin is
smaller than in rung 1. **Codex's check (2026-11-26):** a transient-aware mean field (ALLD records relax towards
steady state within each round) gives g = 0.1315, q needed 0.412, boundary about 66%, main test 0.99959 and
q = 0.45 0.972 at generation 100, close to the script. The script's shuffled branch assumes DISC stay good, which
is false in that arm (a consulting DISC shown a bad proxy refuses a good recipient and becomes bad); integrating
the shuffled arm's reputation dynamics gives about 0.0058 at generation 100, still a clear failure. All values
ignore finite-N correlations and Wright-Fisher noise.

**Test:** b = 3, c = 1, s = 0.1, N = 1000, k = 10, q = 0.6, start 90% DISC, generations 1-500, seeds 0-19 paired
across arms. **Endpoint:** DISC share ≥ 0.8 after generation 500. **Met if** test ≥ 16/20 and shuffled ≤ 4/20.

**Sanity check (registered):** under simple standing without errors, no DISC is ever bad in the test arm (a
non-consulting DISC helps; a consulting one helps good recipients and refuses only bad ones). It need not hold in
the shuffled or image-scoring arms. If any DISC is recorded bad in any
test-arm run, the verdict is **INVALID** pending one inspection.

**Also reported, not tests:** q = 0.45 (near the screen's 0.414) and q = 0.2, both arms; rare start (5%); and an
**image-scoring** arm at q = 0.6 (refusing anyone → bad; known to punish justified refusals: Leimar & Hammerstein
2001), to show whether the norm matters here. Descriptive: among encounters of a consulting DISC with an ALLD,
the share in which the ALLD's record was good (screen: about 0.13-0.14 at the start; among *all* consulting DISC
encounters, about 0.013).

**No verdict** if any run is missing or invalid. **Compute:** seconds. **Attempts:** at most two; a second gets its
own pre-registration.

## Rung 2b: partial observation (pre-registration)

**Status: agreed with the user 2026-11-26 (about 17:55 CET), before any rung-2b model code; draft revised the same
day after a Codex review (gpt-6.1-sol, medium).** Theory screen `rung2b/theory.py` (calculation only) was written and run for this draft; Codex's refined
mean field is given next to it.

**Change from rung 2, only this:** each act is **observed with probability o** (drawn per act, independently of
whether the donor consulted the recipient's record). An observed act updates the donor's record by simple standing
as in rung 2; an unobserved act leaves the record unchanged. Consulting (probability q) and observing (probability
o) are separate. Everything else as rung 2 (records good at birth, random donor order per round, k = 10, shuffled
control: a consulting DISC sees the record of a random other individual, assessment uses the recipient's true
record).

**Theory screen (mean field).** A DISC still never becomes bad (it never refuses a good recipient). An ALLD stays
good from birth until its first *observed* act, which takes 1/o acts on average, so it keeps its birth record
longer; afterwards its record reflects the recipient of its last observed act (good iff that recipient was bad),
steady state x_A / (1 + x_A) as in rung 2. With P_pre the share of the generation before an ALLD's first observed
act, g = P_pre + (1 − P_pre) x_A / (1 + x_A) and q_eff = q(1 − g):

| o | P_pre | g at 90% DISC | q needed at 90% DISC | Unstable boundary at q = 0.6 | Test q = 0.6, gen 100 / 500 | q = 0.45, gen 100 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 (rung 2) | 0.050 | 0.136 | 0.414 | 67% | 0.9996 / 1.000 | 0.971 |
| **0.5** | 0.150 | 0.227 | 0.463 | 74% | 0.998 / 1.000 | 0.846 |
| 0.25 | 0.330 | 0.391 | 0.588 | 89% | 0.927 / 0.9997 | 0.095 |
| 0.1 | 0.619 | 0.653 | none (> 1) | none | 0.013 / 0.000 | 0.004 |

**Codex's refined screen (2026-11-26).** The steady state is unchanged under partial observation
(g_ss = (1 − o) g_ss + o x_A (1 − g_ss) gives x_A / (1 + x_A)), but the script gives an ALLD the steady-state share
right after its first observed act, whereas early recipients are mostly good, so that act usually makes it bad. The
script therefore overstates g, the q needed and the boundary. Integrating the round-wise dynamics
(dg/du = o[x_A(1 − g) − g(0)] within each round, fresh donor order) gives:

| o | g at 90% DISC | q needed at 90% DISC | Boundary at q = 0.6 | Test q = 0.6, gen 100 / 500 | q = 0.45, gen 100 | Shuffled q = 0.6, gen 100 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.132 | 0.412 | 66.0% | 0.9996 / ≈1 | 0.972 | 0.0058 |
| **0.5** | 0.214 | 0.456 | 71.5% | 0.998 / ≈1 | 0.881 | 0.0050 |
| 0.25 | 0.368 | 0.566 | 85.5% | 0.953 / 0.9999 | 0.207 | 0.0038 |
| 0.1 | 0.630 | 0.966 | none at q = 0.6 | 0.035 / ≈0 | 0.008 | 0.0020 |

At o = 0.1 and q = 1 the refined screen gives a boundary of 86.7% and DISC 0.933 / 0.9987 at generations 100 / 500
(the script's "none" was an artefact). So partial observation costs discriminators margin quickly: at o = 0.5 the
test should be met (start 90% against a boundary of about 72%); at o = 0.25 the start is a few points above the
boundary; at o = 0.1 discriminators need nearly full consultation. In the shuffled arm, lower observation keeps
more good birth records, so discriminators help indiscriminately more and lose faster (the script's shuffled
branch ignores o). These are mean-field values, not success probabilities: finite-N correlations and Wright-Fisher
noise have no guaranteed direction.

**Test:** b = 3, c = 1, s = 0.1, N = 1000, k = 10, **q = 0.6, o = 0.5**, start 90% DISC, generations 1-500,
seeds 0-19 paired across arms. **Endpoint:** DISC ≥ 0.8 after generation 500. **Met if** test ≥ 16/20 and shuffled
≤ 4/20. **Sanity (registered):** no DISC is ever assessed bad in any test-arm run; otherwise INVALID pending one
inspection.

**Also reported, not tests (test arm only unless stated):** o = 0.25 and o = 0.1 at q = 0.6; o = 0.1 at q = 1.0;
o = 0.5 at q = 0.45; o = 1 at q = 0.6 (should reproduce rung 2's distribution, not its exact runs, because the
observation draws change the random stream). *Note added before the run, 2026-11-26: the code makes no
observation draw at o = 1, so these runs reproduce rung 2's runs exactly (unit test).* Descriptive: the share of consulting-DISC encounters with an ALLD in
which its record was good, in **generation 1 only** (comparable with the screen's g at the 90% start; refined
screen 0.214 at o = 0.5) and pooled until fixation; and the share of ALLD with no observed act by the end of
generation 1. Generation-500 fixation is expected to hide most of the difference from rung 2; these diagnostics
are what show the cost of partial observation.

**No verdict** if any run is missing or invalid. **Compute:** seconds. **Attempts:** at most two; a second gets its
own pre-registration.

## Rung 3a: execution errors (pre-registration DRAFT, not agreed)

**Status: draft 2026-11-26, revised the same day after a Codex review (gpt-6.1-sol, medium); not agreed, no model
code.** Theory screen `rung3a/theory.py` (calculation only) was written and run for this draft.

**Change from rung 2b, only this:** a donor that intends to help **fails with probability e** (drawn per intended
help): it pays no cost and the recipient gets no benefit, and the act counts as a refusal. Observation (o = 0.5),
consultation (q = 0.6), simple standing with the recipient's true record, records good at birth, random donor
order, k = 10, shuffled control: all as rung 2b. Error draws are independent across intended helps and independent
of consultation and observation; intended refusals (including every ALLD act) get no error draw. With e = 0 no
error draw is made (rung 2b exactly).

**Why this matters.** Under simple standing a discriminator whose intended help to a *good* recipient fails is
assessed bad, so errors create bad discriminators; other discriminators then refuse them, which is justified and
does not spread the bad record. Errors also make defectors look good more often (more bad recipients to "justly"
refuse).

**Theory screen (round-wise mean field, the refinement Codex used for rung 2b; `rung3a/theory.py`).** With e = 0 it
reproduces Codex's rung-2b values (defector good 0.2144, q needed 0.4555, boundary 71.5%). At the 90% DISC start,
q = 0.6, o = 0.5:

| e | DISC records good | ALLD records good | q needed | Unstable boundary | Test gen 100 / 500 | Shuffled gen 100 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 (rung 2b) | 1.000 | 0.214 | 0.455 | 71.5% | 0.998 / ≈1 | 0.005 |
| 0.05 | 0.962 | 0.240 | 0.487 | 75.2% | 0.993 / ≈1 | 0.007 |
| **0.1** | 0.926 | 0.265 | 0.520 | 79.4% | 0.982 / 0.999999 | 0.011 |
| 0.2 | 0.862 | 0.309 | 0.595 | 89.3% | 0.908 / 0.985 | 0.024 |
| 0.3 | 0.805 | 0.349 | 0.681 | none | 0.756 / 3 × 10⁻⁸ | 0.050 |

(Recursion with continuous composition; a first version rounded to whole individuals and stopped at fixation,
which produced artificial generation-500 values, corrected after the Codex review.)

Errors are expected to cost discriminators margin gradually up to e ≈ 0.2 (the 90% start is then barely above the
boundary) and to break maintenance at e = 0.3 with q = 0.6. A bad discriminator receiving less help is already
in the mean payoff (through its strategy's average record). The screen ignores finite-N exclusions, proxy-recipient
dependence in the shuffled arm and Wright-Fisher noise; their combined bias has no established direction.

**Test:** b = 3, c = 1, s = 0.1, N = 1000, k = 10, q = 0.6, o = 0.5, **e = 0.1**, start 90% DISC, generations 1-500,
seeds 0-19 paired across arms. **Endpoint:** DISC ≥ 0.8 after generation 500. **Met if** test ≥ 16/20 and shuffled
≤ 4/20.

**Sanity (registered, replaces rung 2's):** in the test arm, for every act of a discriminator, *new record bad* ⇔
*observed* and *intended help* and *execution failed* and *recipient's record good at the encounter* (consulting or
not: a non-consulting discriminator intends help regardless of the record). The model counts violations in both
directions, and unobserved acts that changed a record; any violation in any test-arm run makes the verdict
**INVALID** pending one inspection. Unit tests also check that qualifying failures occur both with and without
consultation.

**Also reported, not tests (test arm only unless stated):** e = 0 (should reproduce rung 2b's main runs exactly),
e = 0.05, 0.2 and 0.3; **image-scoring** arms at e = 0.1 and e = 0 (decision on the recipient's true record as in the
test arm; observed successful help → good; every observed refusal, justified or failed → bad; unobserved act →
unchanged; all other settings and seeds as the main test; the sanity rule does not apply). The pair shows how the
image-scoring norm's outcome changes with errors; it is not a test of the norm. Descriptive, in generation 1 and pooled until fixation: the share
of DISC and of ALLD records that are good when met by a consulting DISC (comparable with the screen's columns).

**No verdict** if any run is missing or invalid. **Compute:** seconds. **Attempts:** at most two; a second gets its
own pre-registration.
