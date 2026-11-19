# Kin Selection Ladder: Results

## Steps 0-1 (run 2026-11-19, code 5be1dda, pre-registration 4c5fefb)

**Verdict: T0a not met (14/20, one run short of 15); T0b not met (S-kin succeeded in 0/20). Step 1 not run, as registered.** The
ladder has no working base yet; the next step is to be decided with the user.

| Arm | Routing | Start | Successes (final mean `h` >= 0.60) | Mean final `h` | Mean `h` at steps 50 / 250 / 450 / 650 / 850 |
| --- | --- | --- | --- | --- | --- |
| A-kin | self in, label weights 0.8/0.2 | rare | 14/20 | 0.74 | 0.14 / 0.34 / 0.45 / 0.59 / 0.70 |
| A-nobias | self in, uniform | rare | 3/20 | 0.44 | 0.05 / 0.09 / 0.15 / 0.24 / 0.35 |
| A-below | self in, label, B = 0.05 | common | 0/20 maintained | 0.01 | 0.77 / 0.21 / 0.01 / 0.01 / 0.01 |
| S-kin | self out, label weights | rare | 0/20 | 0.01 | 0.06 / 0.03 / 0.01 / 0.01 / 0.01 |
| S-nobias | self out, uniform | rare | 0/20 | 0.01 | 0.02 / 0.01 / 0.01 / 0.01 / 0.01 |
| S-below | self out, label, B = 0.05 | common | 0/20 maintained | 0.01 | 0.77 / 0.20 / 0.01 / 0.01 / 0.01 |

**T0a, replication (self in routing).**

- A-kin 14/20 against the registered 15/20: not met.
- The kin-versus-uniform comparison itself was clear: 14 vs 3, Fisher p = 0.0005; final `h` Mann-Whitney p = 2.6e-6.
  A-below was maintained in 0/20.
- Mean `h` in A-kin was still rising at step 850. The registered rule is scored as it stands; no re-scoring at a
  longer run.

**T0b, kin bias without self-benefit (self out of routing only).**

- S-kin 0/20 and S-nobias 0/20. Helping fell from its rare start (0.05) to about 0.01 in both arms, so the B = 0.6
  diagnostic was not triggered (it needed S-nobias >= 8/20).
- Label-biased routing showed no detectable advantage over uniform routing once a helper's own benefit was taken
  away, at these settings (B = 1.0, C = 0.2, temperature 0.12, 1000 steps).

**What this suggests (interpretation, not tested here).**

- At these settings, spread from rare was seen only with self-inclusive routing. Removing self from routing also
  spreads each helper's benefit over four neighbours instead of five sites, so this bundled change, not self-benefit
  alone, is what was tested. Without self in routing, neither kin-biased nor uniform helping spread in any run.
- This matches two known results, although neither was tested here.
  - *Kin competition* (Taylor 1992): in a population of fixed size and local replacement, helping neighbours who
    are relatives is largely cancelled by competing with those same relatives for sites.
  - *Spatial thresholds* (Ohtsuki et al. 2006, weak selection, death-birth updating): roughly b/c > k per
    neighbour. Here the per-neighbour benefit is B/4, so B/(4C) = 1.25, far from k = 4. That theory is only a
    rough guide for synchronous softmax replacement under strong selection.
- Label diversity also falls: mean final label count is 1.05 in A-kin, 1.30 in A-nobias, 1.20 in S-kin, 2.45 in
  S-nobias and about 1 in the below arms. Where a single label remains, label weights act like uniform routing; local
  label composition was not recorded.

**Not concluded.** This does not show that kin selection cannot work in this model; only that it was not detected at
these registered settings. The 14/20 replication miss is one run, and the A-kin trajectory had not settled.

Data: `data/runs.csv` (per run), `data/verdict.json`, `data/run_log.txt`. Run time about 3 minutes on 8 cores.

## Step 0c, the half-step (run 2026-11-19, code 112ff5b, pre-registration 1252e8f)

**Verdict: T0c not met in either attempt. As registered, the ladder stops at the Moran level and the next move is
decided with the user.** This was a data-informed follow-up (README), so its results are exploratory.

3000 steps, seeds 0-19, B = 1.0, C = 0.2.

| Arm | Self routing weight (self-share alone / among 4 kin) | Kin bias | Start | Successes | Mean final `h` | Mean `h` at steps 50 / 550 / 1050 / 1550 / 2050 / 2550 |
| --- | --- | --- | --- | --- | --- | --- |
| A-kin-3k | 0.8 (0.50 / 0.20) | labels | rare | 20/20 | 0.93 | 0.14 / 0.52 / 0.76 / 0.88 / 0.92 / 0.93 |
| H-nobias | 0.5, uniform (0.20 / 0.20) | none | rare | 20/20 | 0.92 | 0.05 / 0.20 / 0.46 / 0.72 / 0.87 / 0.92 |
| H-kin | 0.2 (0.20 / 0.06) | labels | rare | 0/20 | 0.01 | 0.08 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 |
| H2-kin | 0.5 (0.38 / 0.14) | labels | rare | 0/20 | 0.02 | 0.11 / 0.10 / 0.03 / 0.02 / 0.01 / 0.01 |
| H-below | 0.2, B = 0.05 | labels | common | 0/20 maintained | 0.01 | 0.76 / 0.01 / ... |
| H2-below | 0.5, B = 0.05 | labels | common | 0/20 maintained | 0.01 | 0.77 / 0.01 / ... |

- **Attempt 1:** H-kin 0/20 against H-nobias 20/20 (Fisher p = 1.0). Not met.
- **Attempt 2:** H2-kin 0/20 against the same H-nobias runs (p = 1.0, threshold 0.025). Not met.
- **The control spread in every run.** H-nobias is the A-nobias model rerun for 3000 steps; at 1000 steps it had 3/20
  successes, at 3000 steps 20/20. So T0a's 14-versus-3 contrast at 1000 steps mostly reflected speed: label
  routing with the boosted self-share spread faster, and uniform routing spread more slowly but just as far.

**Pattern across all arms run so far (descriptive, not a registered test).** Classify each arm by the helper's
marginal direct payoff from its own helping, `B × self-share − C`:

| Direct payoff | Arms | Spread from rare |
| --- | --- | --- |
| >= 0 at every kin count | A-kin (+0.3 to 0), uniform routing (0) | 14/20 at 1000 steps for A-kin, 3/20 for A-nobias; 20/20 for both at 3000 |
| < 0 at some or all kin counts | S-kin, S-nobias (−0.2); H-kin (0 to −0.14); H2-kin (+0.19 to −0.07) | 0/20 in every arm |

- In this model and these settings, helping spread only in arms where it never had a net direct cost. That is
  consistent with *weak* altruism (Wilson 1990: no absolute cost to the helper, but a relative disadvantage within
  the local group) in a viscous population, where offspring settle next to their parents, so neighbours tend to be
  relatives, without any kin recognition. Viscosity was not varied (no global-dispersal control), so this is not
  shown to be the cause.
- Label-biased routing (kin discrimination) gave no lasting advantage in eventual success at 3000 steps. A-kin did
  spread faster at 1000 steps (14/20 against 3/20, p = 0.0005), but A-kin also had the kin-count-dependent
  self-share, so the design does not separate the label bias from the extra self-return. Wherever label bias
  lowered the helper's self-share, there was no spread at all.
- This is a correlation across arms that also differ in routing and dynamics. It does not show that the direct
  payoff is the cause. Strong altruism (a net direct cost) failing in a fixed-density, locally replaced population
  matches the classic kin-competition result (Taylor 1992), but that was not tested separately.

Data: `data/step0c_runs.csv`, `data/step0c_verdict.json`, `data/step0c_log.txt`. About 9 minutes on 8 cores.

## Step 0d: local versus global-competitor replacement (run 2026-11-19, code ac13d19, pre-registration 697928d)

**Verdict: T0d met.** At these settings, spread differs sharply between the local and the global-competitor
replacement rules, consistent with weak altruism favoured by viscosity. This is the revised ladder's base. The step
is a data-informed follow-up (README), and the V-global control bundles several changes, so this shows dependence on
the local-replacement package, not on recipient relatedness alone.

3000 steps, seeds 0-19, uniform routing over self plus four neighbours, B = 1.0, C = 0.2 unless stated.

| Arm | Replacement | Successes | Sustained (>= 0.60 at every sample, 2500-3000) | Mean final `h` | Mean `h` at steps 50 / 550 / 1050 / 1550 / 2050 / 2550 | Neighbour `h` correlation, steps 500-3000 |
| --- | --- | --- | --- | --- | --- | --- |
| V-local | local | 20/20 | 20/20 | 0.92 | 0.05 / 0.20 / 0.46 / 0.72 / 0.87 / 0.92 | 0.34-0.37 |
| V-global | global, 5 random candidates | 1/20 | 0/20 | 0.14 | 0.05 / 0.09 / 0.11 / 0.10 / 0.15 / 0.16 | −0.02 to 0.00 |
| V-null | global, B = C = 0 (drift only) | 1/20 | 1/20 | 0.22 | 0.05 / 0.11 / 0.15 / 0.16 / 0.18 / 0.21 | −0.01 to 0.00 |
| V-below | local, B = 0.05 | 0/20 maintained | - | 0.01 | 0.77 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.18-0.20 |

- **T0d:** V-local 20/20 (>= 15), a 19-success difference, 20/20 versus 1/20 (>= 8), one-sided Fisher p = 1.5e-10 (final `h`
  Mann-Whitney p = 3.4e-8); V-below maintained in 0/20 (<= 2). All met.
- **Code check:** V-local reproduced the step-0c H-nobias final values exactly for all 20 seeds, as required.
- **Assortment:** under local replacement, neighbours' `h` stayed correlated (about 0.35); under global replacement
  the correlation was about 0, as intended.
- **Drift:** V-global's one success (seed 1, final `h` 0.63) was not sustained. V-null reached the bar in one run
  (0.69), which shows that a single crossing can occur under the drift baseline. V-global's mean final `h` (0.14) was below V-null's (0.22); not tested.
- **Labels:** the label-sharing contrast between neighbours and random pairs fell to 0 by step 1500 in V-local, as one
  label took over, while `h` kept rising. Founder labels carry no kin information late in these runs; the
  neighbour assortment in `h` does.

Data: `data/step0d_runs.csv`, `data/step0d_verdict.json`, `data/step0d_log.txt`. About 7 minutes on 8 cores.

## Step 1 (revised ladder): overlapping generations (run 2026-11-19, code 68d9c6d, pre-registration ad9c75c)

**Verdict: met in attempt 1** (`d` = 0.5, 6000 steps); attempt 2 was not run, as registered. This version is the base
for step 1b. As registered, the two-attempt rule is exploratory: a working base, not a confirmed effect.

Each occupant dies with probability 0.5 per step, independent of `h`; dead sites get the base lottery's offspring.
Uniform routing, B = 1.0, C = 0.2 unless stated; seeds 0-19.

| Arm | Dead sites filled from | Successes | Sustained (>= 0.60 at every sample, 5000-6000) | Mean final `h` | Mean `h` at steps 1 / 1000 / 2000 / 3000 / 4000 / 5000 | Neighbour `h` correlation, steps 1000-6000 |
| --- | --- | --- | --- | --- | --- | --- |
| O-local | self + 4 neighbours | 20/20 | 20/20 | 0.99 | 0.06 / 0.78 / 0.98 / 0.98 / 0.98 / 0.98 | 0.36-0.45 |
| O-global | 5 random sites | 0/20 | 0/20 | 0.17 | 0.05 / 0.09 / 0.10 / 0.12 / 0.14 / 0.18 | −0.01 to 0.01 |
| O-below | local, B = 0.05, common start | 0/20 maintained | - | 0.01 | 0.84 / 0.01 / ... | 0.29-0.35 |
| O-null | local, B = C = 0 (drift) | 1/20 | 1/20 | 0.20 | 0.05 / 0.13 / 0.14 / 0.20 / 0.20 / 0.21 | 0.44-0.51 |

- **Classification:** control valid (O-global mean neighbour correlation −0.003 <= 0.10); O-local 20/20 (>= 15);
  O-below 0/20 (<= 2); a 20-success difference (>= 8), one-sided Fisher p = 7.3e-12 (< 0.025). **Met.**
- **Higher mean `h` at matched turnover (descriptive, not tested).** With half the sites replaced per step, step 1000
  of O-local is about 500 expected replacements per site. At step 500 in 0d's V-local (the same turnover) the base
  had a mean `h` of about 0.18; O-local had 0.78. Why is not tested; one possibility is that survivors staying in
  place keep helper clusters intact longer.
- **Assortment without payoffs.** O-null's neighbours were as correlated in `h` (about 0.47) as O-local's, with no
  benefit or cost at all. That is consistent with local offspring settlement generating assortment (no global null
  arm was run). Spread differed when the registered benefit-and-cost payoff was active (O-local 20/20 against O-null
  1/20).

Data: `data/step1_runs.csv`, `data/step1_verdict.json`, `data/step1_log.txt`. About 10 minutes on 8 cores.

## Step 1b (revised ladder): selection on survival (run 2026-11-19, code c37f7b7, pre-registration a3a180e)

**Verdict: not met in either attempt (both classified "local failure").** As registered, the next, smaller step is
decided with the user. Step 1 (overlapping generations, selection through births) remains the last working base.

Death lottery `d_i = min(1, 0.5 · w_i / mean(w over self + 4 grid neighbours))`, `w = exp(−λ·x/0.12)`; births by a
softmax over `(1 − λ)·W` among the start-of-step occupants of self + 4 neighbours (or 5 random sites in the global
arms). 6000 steps, seeds 0-19, uniform routing, B = 1.0, C = 0.2 unless stated.

| Arm | `λ` | Successes | Mean final `h` (step 6000) | Mean `h` at steps 50 / 1050 / 2050 / 3050 / 4050 / 5050 | Death rate | Neighbour `h` correlation |
| --- | --- | --- | --- | --- | --- | --- |
| S-local | 1 | 0/20 | 0.008 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.50 | 0.33-0.35 |
| S-global | 1 | 0/20 | 0.005 | 0.03 / 0.01 / 0.01 / 0.00 / 0.01 / 0.01 | 0.50 | −0.01 to 0.01 |
| S-below | 1 | 0/20 maintained | 0.01 | 0.85 / 0.02 / ... | 0.50 | |
| S-null | 1 (no payoffs) | 1/20 | 0.20 | 0.05 / 0.13 / 0.14 / 0.20 / 0.20 / 0.21 | 0.50 | 0.44-0.51 |
| S2-local | 0.5 | 0/20 | 0.023 | 0.05 / 0.02 / 0.02 / 0.02 / 0.02 / 0.02 | 0.50 | 0.40-0.44 |
| S2-global | 0.5 | 0/20 | 0.011 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.50 | −0.01 to 0.00 |
| S2-below | 0.5 | 0/20 maintained | 0.01 | 0.84 / 0.01 / ... | 0.50 | |
| S2-null | 0.5 (no payoffs) | 1/20 | 0.20 | as S-null (identical runs) | 0.50 | |

- **Classification:** the control was valid in both attempts (S-global −0.004, S2-global −0.001); S-local and S2-local
  succeeded in 0/20 (< 15), so both are local failures. The comparison was not scored.
- **Helping finished below the drift baseline.** With the payoff acting on deaths, local helping fell from 0.05 to
  about 0.01-0.02, below the no-payoff arm (0.20), consistent with selection against it. In step 1, with the same
  payoff acting on births, it rose to 0.99. Even half the selection through deaths (`λ` = 0.5) gave no spread.
- **The mean death rate stayed at 0.50** in all arms, as intended; who died, and where, did change.

**A hypothesis (not tested).** In the death lottery, a helper's own death probability is normalized over self plus
its four neighbours, the same five sites that receive its help. Raising those neighbours' payoffs lowers their death
weights and so raises the helper's own death probability. That resembles the case in which helping neighbours is
offset by competing with them (Taylor 1992). The contrast with the birth lottery is not clean, though: a helped
neighbour's changed weight also enters the death normalizations of sites two steps from the helper, and in the
birth lottery the helper competes for vacancies up to one site away, which places its competitors up to two sites
away. Births among start-of-step occupants, including those dying, may also dilute survival selection (README).
None of these factors was varied here. A death lottery normalized over the whole grid (so that survival depends on
a site's own payoff, with only the mean death rate fixed) would test the local-normalization part directly.

Data: `data/step1b_runs.csv`, `data/step1b_verdict.json`, `data/step1b_log.txt`. About 24 minutes on 8 cores.

## Step 1c (revised ladder): survival selection, globally normalized death lottery (run 2026-11-19, code 79daf38, pre-registration 5067eed)

**Verdict: attempt 1 (`λ` = 1) not met (local failure); attempt 2 (`λ` = 0.5) met.** As registered, attempt 2 is the
base for step 2 (age structure), and **the full move to survival selection was not achieved**: the working base has
selection acting half through births and half through deaths. The two-attempt rule is exploratory.

Death `d_i = min(1, 0.5 · w_i / mean(w over all 576 sites))`, `w = exp(−λ·x/0.12)`; births by a softmax over
`(1 − λ)·x/0.12` among the start-of-step occupants of self + 4 neighbours (or 5 random sites in the global arms).
6000 steps, seeds 0-19, uniform routing, B = 1.0, C = 0.2 unless stated.

| Arm | `λ` | Successes | Sustained (5000-6000) | Mean final `h` (step 6000) | Mean `h` at steps 50 / 1050 / 2050 / 3050 / 4050 / 5050 | Death rate | Neighbour `h` correlation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L-local | 1 | 0/20 | 0/20 | 0.026 | 0.05 / 0.03 / 0.03 / 0.03 / 0.03 / 0.03 | 0.50 | 0.42-0.46 |
| L-global | 1 | 14/20 | 11/20 | 0.67 | 0.05 / 0.12 / 0.25 / 0.36 / 0.47 / 0.60 | 0.50 | −0.01 to 0.02 |
| L-below | 1 | 0/20 maintained | - | 0.01 | 0.85 / 0.02 / ... | 0.50 | |
| L-null | 1 (no payoffs) | 1/20 | 1/20 | 0.20 | as O-null (identical runs) | 0.50 | 0.44-0.51 |
| L2-local | 0.5 | 20/20 | 20/20 | 0.95 | 0.05 / 0.31 / 0.66 / 0.90 / 0.95 / 0.95 | 0.50 | 0.41-0.48 |
| L2-global | 0.5 | 0/20 | 0/20 | 0.31 | 0.05 / 0.09 / 0.14 / 0.19 / 0.23 / 0.27 | 0.50 | −0.01 to 0.01 |
| L2-below | 0.5 | 0/20 maintained | - | 0.01 | 0.84 / 0.01 / ... | 0.50 | |
| L2-null | 0.5 (no payoffs) | 1/20 | 1/20 | 0.20 | as O-null | 0.50 | |

- **Attempt 1:** control valid (L-global correlation 0.004); L-local 0/20 (< 15): local failure. The comparison
  was not scored.
- **Attempt 2:** control valid (−0.002); L2-local 20/20, L2-below 0/20, a 20-success difference with one-sided
  Fisher p = 7.3e-12 (< 0.025): **met**.
- **At `λ` = 0.5 the observed outcome differed under global normalization** (step 1b: S2-local 0/20, final `h` 0.02; here L2-local
  20/20, 0.95), consistent with a normalization-scope effect at these parameters. At `λ` = 1 the local arm failed
  under both normalizations.

**An unexpected reversal at `λ` = 1 (descriptive, not registered).** With all selection through deaths, helping
spread in 14/20 runs when offspring settled at random sites (L-global, final `h` 0.67, well above the no-payoff
baseline of 0.20), and in none when they settled locally (L-local, 0.026, below that baseline). So at `λ` = 1, the
global-settlement arm does not behave as a neutral control: something favours helping without local settlement.
L2-global (`λ` = 0.5) also finished above the baseline (0.31 against 0.20), though with no successes.

**A hypothesis for the reversal (not tested).** A site's death weight depends only on its neighbours' helping
(its own payoff `x_i = 0.2 × sum of its neighbours' h`, since its self-share equals its cost).

- *Global settlement.* Two adjacent helpers keep each other alive. A helper next to a non-helper protects the
  non-helper but receives no benefit from it, so, all else equal, it has higher mortality than in a mutual-helper
  pair. If so, helper-helper contacts would last longer than helper-non-helper contacts, which could build helping up through who survives together, even though births are
  random. The measured neighbour correlation stayed near 0, so any such assortment is small.
- *Local settlement.* A helping cluster protects its non-helping border, so few vacancies open next to it for its
  offspring. Helpers at the edge, with fewer helping neighbours, die more often, and their vacancies are filled from
  a mixed neighbourhood, so the cluster may erode rather than grow. This is a version of the "helping neighbours
  reduces your own offspring's room" problem (Taylor 1992).
- Neither mechanism was isolated; both are offered as leads.

Data: `data/step1c_runs.csv`, `data/step1c_verdict.json`, `data/step1c_log.txt`. About 23 minutes on 8 cores.

## Step 2a (revised ladder): ages, with only adults helping (run 2026-11-19, code 69c0204, pre-registration 3db3b5e)

**Verdict: not met in either attempt (both classified "comparison failed").** Helping spread in every local run, but
also in every global-settlement run, so the spread was not shown to depend on local settlement. As registered, the
next, smaller step is decided with the user. Step 1c (attempt 2) remains the last working base.

On the step-1c attempt-2 base (`λ` = 0.5, globally normalized death lottery), occupants are juveniles at age 0 and
adults from age 1. Attempt 1: juveniles neither help nor pay. Attempt 2: juveniles help and pay at half strength.
6000 steps, seeds 0-19, uniform routing over self plus four neighbours, B = 1.0, C = 0.2 unless stated.

| Arm | Successes | Sustained (5000-6000) | Mean final `h` | Mean `h` at steps 50 / 1050 / 2050 / 3050 / 4050 / 5050 | Death rate | Juvenile fraction | Neighbour `h` correlation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-local | 20/20 | 20/20 | 0.99 | 0.05 / 0.63 / 0.99 / 0.99 / 0.99 / 0.99 | 0.38 | 0.38 | 0.39-0.50 |
| A-global | 20/20 | 20/20 | 0.99 | 0.05 / 0.21 / 0.59 / 0.89 / 0.99 / 0.99 | 0.42 | 0.42 | −0.00 to 0.01 |
| A-below | 0/20 maintained | - | 0.02 | 0.87 / 0.12 / 0.01 / ... | 0.50 | 0.50 | |
| A-null | 1/20 | 1/20 | 0.20 | as O-null | 0.50 | 0.50 | 0.44-0.51 |
| A2-local | 20/20 | 20/20 | 0.99 | 0.05 / 0.42 / 0.93 / 0.99 / 0.99 / 0.99 | 0.50 | 0.50 | 0.36-0.46 |
| A2-global | 20/20 | 20/20 | 0.99 | 0.05 / 0.18 / 0.50 / 0.87 / 0.98 / 0.99 | 0.50 | 0.50 | −0.01 to 0.01 |
| A2-below | 0/20 maintained | - | 0.01 | 0.85 / 0.02 / ... | 0.50 | 0.50 | |
| A2-null | 1/20 | 1/20 | 0.20 | as O-null | 0.50 | 0.50 | |

- **Classification:** controls valid (A-global correlation 0.0006, A2-global 0.0009); A-local and A2-local 20/20,
  below arms 0/20; but each local arm led its global arm by 0 successes (Fisher p = 1.0): comparison failed.
- **Local settlement made the spread faster, not more frequent.** At step 1050, mean `h` was 0.63 locally against
  0.21 globally (attempt 1), and 0.42 against 0.18 (attempt 2); by step 4050 both were near 0.99.
- **Ages changed the global arm.** Without ages (the step-1c control L2-global, which this model reproduces exactly
  when everyone is an adult, as tested), global settlement gave 0/20 (final `h` 0.31). With ages, it gave 20/20 in both
  attempts. So in this model, something linked to the ages favours helping without local settlement.
- **Turnover fell in attempt 1:** the mean death rate was 0.38 locally and 0.42 globally instead of about 0.5. Without
  the cap at 1, global normalization makes the mean death probability exactly 0.5, so the cap necessarily caused the
  drop; widely spread payoffs from age-dependent expression are a plausible reason it binds (untested). In attempt 2
  the rate stayed at 0.50. With a one-step juvenile period, the juvenile fraction is mechanically the previous
  step's death rate, so the failed juvenile-fraction prediction (0.45-0.55) is the same turnover result, not separate
  evidence.

**Not explained here.** The neighbour `h` correlation in the global arms was near 0, so the spread does not come from
the assortment that local settlement creates. Two unregistered, untested leads (neither is an identified mechanism):

- *Local ecological effects without kinship.* "Global settlement" globalizes only who parents a vacancy; benefits stay
  local, and survivors keep their sites. Adults repeatedly benefit their neighbours whatever their relatedness, and
  in attempt 1 a newborn carrier has a juvenile step in which it receives help but neither produces nor pays. This
  could create age-conditioned reciprocity or shielding among neighbours without genetic assortment.
- *Survivor-conditioned helping.* Only occupants that outlived their first step express helping (fully, in attempt
  1), so mutually helping adults that keep each other alive (the lead from step 1c's reversal) could build up among
  adults even under random settlement. The correlation was measured over all sites, not among adults only.

An age-stratified analysis of payoffs and survival would be needed to tell these apart.

Data: `data/step2a_runs.csv`, `data/step2a_verdict.json`, `data/step2a_log.txt`. About 24 minutes on 8 cores.

## Diagnostic D2a: where the selection on helping comes from (run 2026-11-19, code 1a5dc94 + test-fixture fix, pre-registration 422ccd6)

**Reading for A-global: "expected selection positive, association mixed", a case the pre-registered readings do not
cover.** Exploratory, 5 seeds per arm, the first 2000 steps. The code check passed: recomputed death probabilities
equal the engine's in every step (maximum difference 0), and the summed expected change (A-global 0.49) agrees with the
realized change (0.46).

Exact expected fitness `w_i = (1 − d_i) + Σ_k d_k p_ik`; `cov(h, w)` summed over steps 1-2000 is the expected change in
mean `h` before mutation. Means over runs, with the per-run range for the totals:

| Arm | Expected selection, total (per-run range) | Survival part | Birth part | Adult share of the total | Spearman of own `h` with payoff: all / adults / juveniles (per-run range for adults) | Final mean `h` at step 2000 |
| --- | --- | --- | --- | --- | --- | --- |
| A-global (ages, global settlement) | 0.49 (0.31 to 0.85) | 0.25 | 0.23 | 99.6% | 0.008 / 0.020 / −0.004 (−0.028 to 0.056) | 0.51 |
| A-local (ages, local settlement) | 0.93 (0.88 to 0.97) | 4.76 | −3.83 | 17% | 0.29 / 0.28 / 0.29 (0.24 to 0.34) | 0.98 |
| L2-global (no ages, global) | −0.011 (−0.031 to 0.010) | −0.006 | −0.006 | 100% (all adults) | 0.009 / 0.009 / undefined (−0.008 to 0.034) | 0.12 |

**Classification (as registered).** A-global: expected selection positive (all 5 runs), mostly through survival
(the survival part was positive and larger in at least 4 runs), association mixed. A-local: positive, survival,
present. L2-global: absent, association mixed (juvenile correlations undefined, since there are no juveniles). The
references behaved as expected except that L2-global's association is "mixed" rather than "absent", for the same
undefined juvenile class.

**What the measurements show (descriptive).**

- **In A-global there is expected selection for helping, carried by adults**, through survival and births about
  equally. It is not death- or parent-lottery sampling drift (it is computed from the probabilities, given the
  states and candidate sets). It is about half of A-local's net selection. Where the association behind it comes
  from was not established.
- **Its association with payoff is too small for this diagnostic's threshold.** The adult Spearman correlation
  ranged from −0.03 to +0.06 across runs, around the registered threshold of 0.02. A rough estimate (per-step
  `cov(h, w)` of about 2.4e-4, against rough standard deviations of about 0.15 for `h` and 0.5 for `w`) suggests that a
  correlation of about 0.003 between own `h` and fitness would be enough, at this selection strength. So the
  threshold could not rule an association in or out. The run with the most selection (seed 3) had a negative mean
  adult correlation; the correlations were sampled every 250 steps, while selection was summed every step.
- **Local settlement creates large opposing parts.** In A-local, helping is strongly favoured through survival
  (+4.76) and strongly opposed through births (−3.83), with a net of +0.93; adults carry only 17% of the net. One
  hypothesis consistent with the signs, not tested here (relatedness and competition were not measured): helpers
  keep nearby relatives alive, and relatives then compete for the same vacancies (Taylor 1992).

**Note on the run.** The diagnostic code was committed (1a5dc94) and run while one new unit test of the
classification rules was failing. The failure was in the test's fixture: it gave the drift reference a small
positive total in all 5 runs, which the registered rule (checked first) classifies as "positive". The test was
corrected; the diagnostic code and its results are unchanged. The registered rules for "positive" and "absent" overlap
for small positive totals; it made no difference here, since L2-global's totals were not all positive.

Data: `data/d2a_verdict.json`, `data/d2a_log.txt`.

## Step K0: a costly-helping base (run 2026-11-19, code 4b06a10, pre-registration 9e81fb5)

**Verdict: met in attempt 1** (K12-local 20/20 against K12-global 0/20, one-sided Fisher p = 7e-12; K-below
maintained in 0/20; manipulation check: K12-global neighbour `h` correlation 0.003). Attempt 2 (death-birth-like) was
not run, as registered. With self out of routing, a helper pays `0.2·h` and gets none of its own benefit back, so
this is the ladder's first base in which helping has a direct cost to the helper.

| Arm | b/c = B/C | Replacement | Start | Successes | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Mean neighbour `h` correlation (steps 1000-6000) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K3-local | 3 | local | rare | 0/20 | 0.009 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.35 |
| K6-local | 6 | local | rare | 0/20 | 0.014 | 0.04 / 0.03 / 0.01 / 0.01 / 0.01 / 0.01 | 0.40 |
| K12-local (test) | 12 | local | rare | 20/20 (20 sustained) | 0.97 | 0.05 / 0.13 / 0.33 / 0.67 / 0.97 / 0.97 | 0.40 |
| K24-local | 24 | local | rare | 20/20 (20 sustained) | 0.99 | 0.07 / 0.34 / 0.67 / 0.99 / 0.99 / 0.99 | 0.31 |
| K12-global (control) | 12 | 5 random sites | rare | 0/20 | 0.006 | 0.03 / 0.01 / 0.00 / 0.01 / 0.01 / 0.01 | 0.003 |
| K-below | 0.25 | local | common | 0/20 maintained | 0.007 | 0.83 / 0.57 / 0.23 / 0.01 / 0.01 / 0.01 | 0.33 |
| K-null (drift) | – (B = C = 0) | local | rare | 1/20 | 0.20 | 0.05 / 0.06 / 0.08 / 0.12 / 0.15 / 0.20 | 0.47 |

The realized survival fraction was 0.50 in every arm.

**What this shows (at these settings).**

- **Costly helping spread under local settlement at b/c = 12 and 24, and not under global-competitor replacement at
  b/c = 12.** The spread depended on the local-replacement package: in the control, a vacancy's parent comes from 5 random
  sites, so offspring land away from their parents and the competitor pool is no longer local. The control bundles
  these changes, so this does not isolate relatedness alone.
- **Descriptively, the outcome switched between b/c = 6 and 12** (0/20 at 3 and 6, 20/20 at 12 and 24). This is
  consistent with the imitation-updating screen of Ohtsuki et al. (2006), `b/c > k + 2 = 6`. Only four levels were
  run, the screen assumes weak selection and asynchronous updates, and raising B also raised selection strength,
  so this places the switch in that interval for this engine; it does not confirm the theoretical threshold.
- **Below the switch, helping declined, below the drift baseline.** At b/c = 3 and 6, mean `h` fell to about
  0.01, against 0.20 in K-null (descriptive; no selection estimate), as did the global control at b/c = 12.
- **Spread together with spatial assortment (association, not an isolated pathway).** Neighbour `h` correlation was about 0.3-0.4 in the local arms and about 0
  in the global control. This step does not show that assortment is the pathway, and could not separate kin selection by
  viscosity from network reciprocity, which both work through helpers clustering with helpers.

**Comparison with 0b.** 0b (self out of routing, label kin weights, 1000 steps, base engine) ran at b/c = B/C = 5 and
failed (0/20). That fits K0's finding that b/c 6 was too low here, though 0b used a different engine (non-overlapping
generations), so the two are not a direct comparison.

**Predictions made before the data.** Attempt 1 met: 55% (it was met). K3-local <= 2/20: 85% (0/20). K24-local >= 15/20:
65% (20/20).

**Next (registered):** the second level, parental care (benefit only to the helper's own offspring among its
neighbours), pre-registered after this verdict; then the ladder rebuilt on this base with costly helping at every
step. Both on the user's go.

Data: `data/k0_runs.csv`, `data/k0_verdict.json`, `data/k0_log.txt`.
