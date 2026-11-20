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

## Step K1: parental care on the costly-helping base (run 2026-11-19, code 430ee79, pre-registration 3615065)

**Verdict: met in attempt 1** (P6-local 18/20 against the known K6 benchmark 0/20; P-below maintained in 0/20).
**H2 met:** P6-global 20/20, with neighbour `h` correlation −0.003 (measured spatial assortment of `h` near zero; recipients
are still the helper's offspring by design). N6-local reproduced K0's K6-local exactly (checked by the runner). Attempt 2
(hybrid) was not run, as registered.

| Arm | Routing | b/c | Settlement | Successes | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Neighbour `h` corr. | Living offspring per occupant | Occupants with none | Benefit lost | Parent-offspring `h` corr. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1.5-local | offspring | 1.5 | local | 0/20 | 0.010 | 0.04 / 0.02 / 0.01 / 0.01 / 0.01 / 0.01 | 0.36 | 0.27 | 0.79 | 0.79 | 0.97 |
| P3-local | offspring | 3 | local | 0/20 | 0.016 | 0.05 / 0.03 / 0.02 / 0.02 / 0.02 / 0.02 | 0.40 | 0.27 | 0.79 | 0.79 | 0.99 |
| **P6-local (test)** | offspring | 6 | local | **18/20** (18 sustained) | 0.83 | 0.06 / 0.22 / 0.37 / 0.54 / 0.73 / 0.83 | 0.57 | 0.27 | 0.82 | 0.82 | 1.00 |
| P12-local | offspring | 12 | local | 20/20 | 0.98 | 0.09 / 0.28 / 0.45 / 0.69 / 0.98 / 0.98 | 0.53 | 0.26 | 0.82 | 0.82 | 0.99 |
| N6-local (benchmark) | 4 neighbours | 6 | local | 0/20 | 0.014 | 0.04 / 0.03 / 0.01 / 0.01 / 0.01 / 0.01 | 0.40 | – | – | – | – |
| P-below | offspring | 0.25 | local, common start | 0/20 maintained | 0.008 | 0.83 / 0.57 / 0.22 / 0.01 / 0.01 / 0.01 | 0.33 | 0.27 | 0.79 | 0.79 | 0.97 |
| P3-global | offspring | 3 | global | 0/20 | 0.016 | 0.05 / 0.03 / 0.02 / 0.02 / 0.02 / 0.02 | 0.00 | 0.33 | 0.76 | 0.76 | 0.98 |
| **P6-global (H2)** | offspring | 6 | global | **20/20** | 0.96 | 0.07 / 0.29 / 0.48 / 0.66 / 0.89 / 0.96 | −0.003 | 0.33 | 0.81 | 0.81 | 0.99 |
| P12-global | offspring | 12 | global | 20/20 | 0.99 | 0.12 / 0.36 / 0.58 / 0.89 / 0.99 / 0.99 | −0.005 | 0.33 | 0.81 | 0.81 | 0.97 |

Diagnostics are means over the payoff states after 1000-5999 updates, then over runs. Fisher exact P6-local against
N6-local (descriptive, since N6's outcome was known): p = 1.7e-9.

**What this shows (at these settings).**

- **Routing costly help to own offspring let it spread at b/c = 6, where the same help spread over neighbours did
  not** (18/20 against 0/20). The tested difference is the whole offspring-routing package: recipients chosen by
  parentage, benefit concentrated on fewer recipients, and benefit lost without offspring.
- **It spread without local settlement too.** Under global settlement (neighbour `h` correlation about 0) parental care
  spread at b/c = 6 and 12 in 20/20 runs each. So, in this model, care aimed by parentage did not need local
  settlement to spread. Descriptively (no registered comparison), the global arms had more living offspring per
  occupant (0.33 against 0.27), P6 succeeded in 20/20 against 18/20, and mean `h` rose earlier; competition among
  relatives for nearby vacancies (Taylor 1992) is one candidate explanation, not tested here.
- **Outcomes changed between the tested ratios b/c = 3 and 6** under both settlement rules (0/20 at 3, at least
  18/20 at 6), whereas neighbour help in K0 failed at 6 and spread at 12. Only these levels were run, so this does
  not locate a threshold for either.
- **Most benefit was lost**: about 80% of occupants (weighted by their `h`, about the same) had no living offspring.
  The pre-registered rough screen (about three quarters lost, switch near b/c 4) was close: the delivered quarter
  or fifth of B exceeded the cost at b/c = 6 and not at 3. This is consistent with the screen, not a test of it.
- **Parent-offspring `h` correlation was about 0.97-1.00**, as expected with clonal inheritance and rare mutation.
  Sexual inheritance (parent-offspring relatedness 1/2) would change this, and its effect here was not tested.

**Note on the run.** Before the main run, a timing check ran the test arm (P6-local, seed 0) for 1500 steps and
showed its mean `h` (0.65) at that point. The pre-registered design and rules were not changed after it.

**Predictions made before the data.** P6-local >= 15/20: 40% (18/20). P12-local >= 15/20: 75% (20/20). H2: 45% (met).
P1.5-local >= 15/20: 10% (0/20).

**Next:** which base (K0 neighbour help or K1 parental care) the ladder is rebuilt on, decided with the user.

Data: `data/k1_runs.csv`, `data/k1_verdict.json`, `data/k1_log.txt`.

## Step R1: care raises the offspring's survival (run 2026-11-19, code 56f1775, pre-registration 0231603)

**Verdict: attempt 1 (`λ` = 1, care only on survival) not met, classified local failure (R6-local 0/20). Attempt 2
(`λ` = 0.5, care half on survival, half on fecundity) met**: R2-6-local 20/20 against R2-N6-local 0/20 (one-sided
Fisher p = 7e-12), R2-below maintained in 0/20. **H2 met in attempt 2** (R2-6-global 20/20, neighbour `h` correlation
0.002), not met in attempt 1 (R6-global 0/20). By the registered decision rule, the base for R2 keeps half of the
care benefit on fecundity.

**Review note.** Codex could not review the code before the run (usage limit). Its review came during the run and
found no error affecting the verdict. It found one mislabelled diagnostic: "benefit lost" for the neighbour-help
arms, which never lose benefit. That is corrected below (shown as 0) and in the code (333c42d), with added tests.

| Arm | b/c | Settlement | Successes | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Neighbour `h` corr. | Death rate | Death: cared / uncared / parents | Cared fraction | Benefit lost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Attempt 1, `λ` = 1** | | | | | | | | | | |
| R3-local | 3 | local | 0/20 | 0.014 | 0.04 / 0.02 / 0.02 / 0.01 / 0.01 / 0.01 | 0.38 | 0.49 | 0.45 / 0.50 / 0.50 | 0.12 | 0.77 |
| R6-local (test) | 6 | local | 0/20 | 0.037 | 0.05 / 0.05 / 0.05 / 0.04 / 0.04 / 0.04 | 0.44 | 0.46 | 0.34 / 0.50 / 0.48 | 0.22 | 0.75 |
| R12-local | 12 | local | 0/20 | 0.119 | 0.06 / 0.09 / 0.11 / 0.11 / 0.12 / 0.12 | 0.46 | 0.35 | 0.11 / 0.50 / 0.41 | 0.38 | 0.70 |
| R24-local | 24 | local | 0/20 | 0.100 | 0.06 / 0.09 / 0.10 / 0.10 / 0.10 / 0.10 | 0.46 | 0.31 | 0.05 / 0.50 / 0.38 | 0.42 | 0.68 |
| RN6-local (control) | 6 | local | 0/20 | 0.006 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.33 | 0.47 | 0.45 / 0.50 / 0.47 | 0.60 | 0 |
| R-below | 0.25 | local, common | 0/20 maintained | 0.008 | 0.83 / 0.59 / 0.26 / 0.01 / 0.01 / 0.01 | 0.33 | 0.50 | 0.50 / 0.50 / 0.50 | 0.09 | 0.79 |
| R6-global | 6 | global | 0/20 | 0.243 | 0.06 / 0.14 / 0.19 / 0.23 / 0.24 / 0.24 | −0.001 | 0.32 | 0.13 / 0.50 / 0.38 | 0.47 | 0.67 |
| R12-global | 12 | global | 0/20 | 0.226 | 0.08 / 0.16 / 0.22 / 0.23 / 0.23 / 0.23 | −0.005 | 0.26 | 0.05 / 0.50 / 0.32 | 0.53 | 0.65 |
| **Attempt 2, `λ` = 0.5** | | | | | | | | | | |
| R2-3-local | 3 | local | 0/20 | 0.014 | 0.04 / 0.03 / 0.02 / 0.01 / 0.02 / 0.01 | 0.39 | 0.50 | 0.47 / 0.50 / 0.50 | 0.13 | 0.78 |
| R2-6-local (test) | 6 | local | **20/20** | 0.99 | 0.05 / 0.18 / 0.44 / 0.85 / 0.98 / 0.99 | 0.49 | 0.21 | 0.04 / 0.50 / 0.28 | 0.62 | 0.58 |
| R2-12-local | 12 | local | 20/20 | 0.99 | 0.09 / 0.38 / 0.67 / 0.97 / 0.99 / 0.99 | 0.47 | 0.18 | 0.01 / 0.50 / 0.25 | 0.66 | 0.58 |
| R2-24-local | 24 | local | 20/20 | 1.00 | 0.13 / 0.44 / 0.73 / 0.99 / 0.99 / 1.00 | 0.42 | 0.17 | 0.00 / 0.50 / 0.24 | 0.66 | 0.58 |
| R2-N6-local (control) | 6 | local | 0/20 | 0.008 | 0.04 / 0.02 / 0.01 / 0.01 / 0.01 / 0.01 | 0.35 | 0.48 | 0.47 / 0.50 / 0.48 | 0.67 | 0 |
| R2-below | 0.25 | local, common | 0/20 maintained | 0.008 | 0.83 / 0.57 / 0.25 / 0.01 / 0.01 / 0.01 | 0.33 | 0.50 | 0.50 / 0.50 / 0.50 | 0.09 | 0.79 |
| R2-6-global (H2) | 6 | global | **20/20** | 0.98 | 0.07 / 0.32 / 0.59 / 0.90 / 0.99 / 0.98 | 0.002 | 0.20 | 0.06 / 0.50 / 0.24 | 0.68 | 0.61 |
| R2-12-global | 12 | global | 20/20 | 0.99 | 0.14 / 0.43 / 0.67 / 0.95 / 0.99 / 0.99 | −0.006 | 0.15 | 0.02 / 0.50 / 0.18 | 0.73 | 0.61 |

Diagnostics are means over payoff states after 1000-5999 updates, then over runs. "Death rate" is the mean death
probability over those states (the realized fraction dying over whole runs, `1 − survival_fraction`, is close to
it); "uncared" is 0.50 by construction. In the neighbour-help arms, every occupant with a helping neighbour
counts as cared. Drift baseline (K-null): final mean `h` 0.20.

**What this shows (at these settings).**

- **With care acting only on survival, helping did not spread at any tested b/c** (0/20 at 3, 6, 12 and 24 under
  local settlement, and at 6 and 12 under global settlement). It did not collapse either, at b/c >= 6 under global settlement and >= 12 under local settlement: mean
  `h` rose early and then stayed nearly flat (about 0.10-0.12 locally at b/c 12 and 24, about 0.23-0.24 globally),
  well above the local costly controls (about 0.01). Only the global plateaus were above the drift baseline (0.20);
  both the costly controls and the drift baseline used local settlement, so these comparisons with the global arms
  are descriptive, with no matched global control. A
  stable intermediate level is one reading of these trajectories, not a tested one. One candidate explanation, not
  tested: the survival benefit saturates (`d = 0.5·exp(−R/T)` approaches 0, so once a cared-for offspring's death
  risk is near 0, more care adds little), while the parent's fecundity cost keeps rising linearly with `h`.
  Consistent with this, in the b/c 12-24 arms cared-for offspring had mean death probabilities of 0.05-0.11, while
  final mean `h` was only 0.10-0.23 (population mean `h` is not the care dose an offspring received).
- **With half of the care on survival and half on fecundity, it spread** at b/c 6, 12 and 24 (20/20 each), and did
  not at 3. Untargeted neighbour help with the same split did not spread at b/c 6 (0/20). As in K1, the contrast is
  the whole offspring-care package against neighbour help, not parentage alone.
- **It again spread without local settlement** (R2-6-global 20/20, neighbour correlation about 0).
- **Demography in the attempt-2 arms where helping spread:** the mean death probability over steps 1000-5999 was
  about 0.15-0.21 (the no-care value is 0.5), and cared-for offspring had about 0-0.06, against 0.50 for
  occupants receiving no care. Occupants with living offspring had about 0.18-0.28; whether they were themselves
  receiving care was not measured directly.

**Predictions made before the data.** Attempt 1 met: 50% (not met). RN6-local <= 3/20: 70% (0/20). H2 in attempt 1:
55% (not met). Attempt 2 met given attempt 1 not: 50% (met).

**Next:** step R2 (ages) on the `λ` = 0.5 base, pre-registered on the user's go. Open question for the user: whether
to first test the saturation explanation for the attempt-1 plateau (for example a non-saturating survival rule).

Data: `data/r1_runs.csv`, `data/r1_verdict.json`, `data/r1_log.txt`.

## Diagnostic DR1: does survival care settle at a level approached from both sides? (run 2026-11-19, code d95c682, pre-registration 8317f48)

**Verdict: T1 supported (4 of 4 pairs), T2 supported.** With care only on survival (`λ` = 1), mean `h` started at
0.9 ended within 0.002-0.015 of the level reached from the rare start, and was settled over steps 5000-6000
(first below rare + 0.03 at steps 1200-1650); both drift references
stayed above 0.50 (0.71 local, 0.82 global). In the registered T2 comparison (local, high start), the settled level was lower at b/c 48 than at 24; from the rare
start it was also lower (0.078 against R1's 0.100, descriptive). Codex (gpt-6.2-astra, high effort) reviewed the code before the run.

**T1, convergence from above.**

| Pair (high start vs R1 rare start) | High-start final `h` | Rare-start final `h` | Abs. difference | Settled range, steps 5000-6000 | First sample below rare + 0.03 | Paired diff. (Wilcoxon p) | Met |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D12-local-high vs R12-local | 0.117 | 0.119 | 0.002 | 0.007 | step 1250 | −0.002 (0.65) | yes |
| D24-local-high vs R24-local | 0.103 | 0.100 | 0.003 | 0.005 | step 1200 | +0.003 (0.16) | yes |
| D6-global-high vs R6-global | 0.228 | 0.243 | 0.015 | 0.012 | step 1400 | −0.015 (0.08) | yes |
| D12-global-high vs R12-global | 0.238 | 0.226 | 0.012 | 0.017 | step 1650 | +0.012 (0.14) | yes |

**T2, lower level at higher benefit.** D48-local-high settled at mean final `h` 0.074 against 0.103 for
D24-local-high (paired difference −0.029, Wilcoxon p = 2e-6; both settled, ranges 0.003 and 0.005; D48-local-high first below
D48-local's final + 0.03 at step 1200), and its cared
offspring had a lower mean death probability (0.023 against 0.048). D48-local from the rare start settled at 0.078
(range 0.008).

**Trajectories and demography (descriptive).**

| Arm | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 5000 / 6000 | Death: cared / mean | Neighbour `h` corr. |
| --- | --- | --- | --- |
| D12-local-high | 0.86 / 0.70 / 0.49 / 0.19 / 0.12 / 0.11 / 0.12 | 0.11 / 0.35 | 0.47 |
| D24-local-high | 0.86 / 0.70 / 0.51 / 0.18 / 0.10 / 0.10 / 0.10 | 0.05 / 0.31 | 0.48 |
| D48-local-high | 0.86 / 0.70 / 0.51 / 0.16 / 0.08 / 0.07 / 0.07 | 0.02 / 0.29 | 0.48 |
| D48-local (rare) | 0.06 / 0.07 / 0.08 / 0.08 / 0.08 / 0.08 / 0.08 | 0.02 / 0.29 | 0.46 |
| D6-global-high | 0.85 / 0.72 / 0.58 / 0.33 / 0.22 / 0.23 / 0.23 | 0.13 / 0.32 | −0.003 |
| D12-global-high | 0.85 / 0.74 / 0.62 / 0.39 / 0.23 / 0.22 / 0.24 | 0.05 / 0.26 | −0.002 |
| D-null-local-high | 0.90 / 0.90 / 0.89 / 0.89 / 0.85 / 0.76 / 0.71 | – / 0.50 | 0.47 |
| D-null-global-high | 0.90 / 0.90 / 0.91 / 0.88 / 0.88 / 0.82 / 0.82 | – / 0.50 | −0.003 |

**What this shows (at these settings).**

- **Care on survival alone settled at a modest level, reached from below and from above.** From 0.9 it fell below
  rare + 0.03 by steps 1200-1650, while the drift references were still at 0.71 and 0.82 after 6000 steps (they
  have constant death 0.5, so mutation per step differs from the treatment arms). That is
  consistent with a level held by selection, though DR1 did not measure selection directly above and below it.
- **The level fell with benefit under local settlement** (0.12 at b/c 12, 0.10 at 24, 0.07-0.08 at 48; only the
  48-against-24 high-start comparison was the registered test, and the 12-to-24 fall was known before), as the saturation heuristic
  predicts in direction. Its values were not matched: predicted 0.094, 0.063, 0.040, observed higher. The heuristic
  ignores several offspring per parent, benefit loss and competition among relatives; other explanations of the
  trend are not excluded.
- **At b/c 12-48, survival-only care settled at a modest level rather than failing to evolve.** That level lay
  far below R1's success threshold of 0.60, which the heuristic also puts below 0.60 at every tested benefit. DR1
  did not test b/c 6 locally from above, where R1's test arm ended at 0.037, so it does not explain that arm. R1's
  registered verdict and the `λ` = 0.5 base for R2 are unchanged.
- **Under global settlement the level was higher** at the one matched benefit (b/c 12: 0.238 against 0.117 locally,
  high start); one candidate
  explanation, not tested, is competition among relatives for nearby vacancies under local settlement.

**Predictions made before the data.** T1 supported: 65% (supported). T2 supported: 60% (supported). Both drift
references above 0.50: 85% (0.71 and 0.82).

**Next (registered):** whether to define a separate endpoint for survival care (a settled intermediate level
against costly controls) is decided with the user before R2.

Data: `data/dr1_runs.csv`, `data/dr1_verdict.json`, `data/dr1_log.txt`.

## Step R2: care only for young offspring (run 2026-11-19, code 84203c6, pre-registration aa957de)

**Verdict: met in attempt 1 (`J` = 2).** Y6-local 20/20 against YN6-local 0/20 (one-sided Fisher p = 7e-12), Y-below
maintained in 0/20. **H2 met:** Y6-global 20/20, neighbour `h` correlation −0.001. Attempt 2 (`J` = 5) was not run,
as registered. Codex could not review the pre-registration or the code before the run (usage limit). **Post-run
Codex review (2026-11-20, gpt-6.2-astra, high):** no verdict-changing finding; counts, Fisher p and H2 recomputed from
the archive, seed 0 of Y6-local replayed to step 6000 with every archived value matching. Wording and table
corrections below are from that review.

| Arm | Care goes to | b/c | Settlement | Successes | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Neighbour `h` corr. | Death: cared / uncared / parents / mean | Juvenile fraction | Living juvenile offspring per occupant | Benefit lost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Y3-local | own young | 3 | local | 0/20 | 0.014 | 0.04 / 0.02 / 0.02 / 0.02 / 0.01 / 0.01 | 0.38 | 0.47 / 0.50 / 0.50 / 0.50 | 0.75 | 0.25 | 0.79 |
| **Y6-local (test)** | own young | 6 | local | **20/20** | 0.98 | 0.05 / 0.13 / 0.35 / 0.77 / 0.98 / 0.98 | 0.50 | 0.03 / 0.50 / 0.42 / 0.30 | 0.57 | 0.43 | 0.69 |
| Y12-local | own young | 12 | local | 20/20 | 0.99 | 0.08 / 0.41 / 0.75 / 0.99 / 0.99 / 0.99 | 0.44 | 0.00 / 0.50 / 0.42 / 0.28 | 0.56 | 0.44 | 0.69 |
| Y24-local | own young | 24 | local | 20/20 | 0.99 | 0.13 / 0.48 / 0.88 / 0.99 / 0.99 / 0.99 | 0.40 | 0.00 / 0.50 / 0.42 / 0.28 | 0.55 | 0.44 | 0.69 |
| YN6-local (control) | young neighbours | 6 | local | 0/20 | 0.008 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.34 | 0.46 / 0.50 / 0.49 / 0.48 | 0.73 | 0.25 | 0.007 |
| Y-below | own young | 0.25 | local, common | 0/20 maintained | 0.008 | 0.83 / 0.57 / 0.23 / 0.01 / 0.01 / 0.01 | 0.33 | 0.50 / 0.50 / 0.50 / 0.50 | 0.75 | 0.25 | 0.80 |
| **Y6-global (H2)** | own young | 6 | global | **20/20** | 0.98 | 0.07 / 0.27 / 0.52 / 0.88 / 0.98 / 0.98 | −0.001 | 0.05 / 0.50 / 0.40 / 0.30 | 0.57 | 0.45 | 0.71 |
| Y12-global | own young | 12 | global | 20/20 | 0.99 | 0.13 / 0.47 / 0.78 / 0.99 / 0.99 / 0.99 | −0.004 | 0.01 / 0.50 / 0.39 / 0.28 | 0.55 | 0.45 | 0.71 |

Diagnostics are means over payoff states after 1000-5999 updates, then over runs; "juvenile" is age < 2. Benefit
lost is the fraction of total helping output produced by helpers with no recipient (no living juvenile offspring; for
YN6-local, no juvenile neighbour).

**What this shows (at these settings).**

- **Care limited to own young (the first two steps after birth) spread at b/c = 6, 12 and 24, and not at 3**, the
  same pattern as care without an age limit (R1 attempt 2). Help to young neighbours of any parentage did not spread
  at b/c = 6 (0/20). The contrast is the own-young-care package against help to young neighbours, not parentage alone.
- **It spread without local settlement too** (Y6-global 20/20, neighbour correlation about 0).
- **Compared with R1's base (no age limit; descriptive, different batch):** more of the benefit was lost (about
  0.69-0.71 against 0.58-0.61), parents had higher death probabilities (about 0.39-0.42 against 0.18-0.28) and the
  mean death probability was higher (about 0.28-0.30 against 0.15-0.21). Withdrawing care from older offspring is
  one route to these differences, but the averages do not separate it from changes in population composition.
  Helping still reached mean `h` 0.98-0.99.
- **In the young-neighbour control almost no benefit was lost** (0.007), since most sites hold a juvenile
  (juvenile fraction 0.73 there), yet it did not spread.
- **Clarification (2026-11-20, from the Codex review):** the pre-registration said only adults give care. That is
  wrong for `J` = 2: an age-1 parent is itself juvenile, and in Y6-local seed 0, 90 age-1 helpers had newborn
  offspring. Founders (age 0) also counted as juvenile neighbours in YN6-local. The engine followed the registered
  recipient rule. So R2 shows spread when **recipients** are restricted to young offspring; it does not test an
  adult-only donor rule.

**Predictions made before the data.** Attempt 1 met: 55% (met). YN6-local <= 3/20: 60% (0/20). H2: 55% (met).

**Next:** step R3 (energy) on this base, pre-registered on the user's go.

Data: `data/r2_runs.csv`, `data/r2_verdict.json`, `data/r2_log.txt`.

## Step R3a: care and its cost carry over as body condition (run 2026-11-19, code e3ff897, pre-registration 415b90c)

**Verdict: met in attempt 1 (`ρ` = 0.8).** E6-local 20/20 against EN6-local 0/20 (one-sided Fisher p = 7e-12),
E-below maintained in 0/20. **H2 met:** E6-global 20/20, neighbour `h` correlation −0.009. Attempt 2 (`ρ` = 0.4) was
not run, as registered. Codex could not review the pre-registration or the code before the run (usage limit).
**Post-run Codex review (2026-11-20, gpt-6.2-astra, high):** no verdict-changing finding; counts, Fisher p and H2
recomputed, engine checked site by site over 60 updates, seed 0 of the four decision arms replayed to step 6000 with
every archived value matching. Wording and table corrections below are from that review.

| Arm | Care goes to | b/c | Settlement | Successes (sustained) | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Neighbour `h` corr. | Death: cared / uncared / parents / mean | Juvenile fraction | Benefit lost | Mean `S` / `D`: all, juveniles, parents |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E3-local | own young | 3 | local | 0/20 | 0.011 | 0.04 / 0.02 / 0.01 / 0.01 / 0.01 / 0.01 | 0.36 | 0.47 / 0.50 / 0.50 / 0.50 | 0.75 | 0.79 | S 0.00, D 0.00 (parents' D 0.01) |
| **E6-local (test)** | own young | 6 | local | **20/20** (20) | 0.73 | 0.07 / 0.25 / 0.41 / 0.55 / 0.66 / 0.73 | 0.59 | 0.02 / 0.13 / 0.11 / 0.11 | 0.21 | 0.84 | S 0.59, 0.94, 0.54; D 0.46, 0.19, 0.53 |
| E12-local | own young | 12 | local | 20/20 (20) | 0.95 | 0.11 / 0.30 / 0.42 / 0.59 / 0.78 / 0.95 | 0.59 | 0.00 / 0.08 / 0.08 / 0.07 | 0.14 | 0.88 | S 1.19, 2.56, 0.97; D 0.64, 0.24, 0.72 |
| E24-local | own young | 24 | local | 20/20 (20) | 0.98 | 0.11 / 0.29 / 0.41 / 0.56 / 0.79 / 0.98 | 0.59 | 0.00 / 0.06 / 0.06 / 0.06 | 0.11 | 0.90 | S 2.09, 5.37, 1.56; D 0.70, 0.25, 0.77 |
| EN6-local (control) | young neighbours | 6 | local | 0/20 | 0.006 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.33 | 0.46 / 0.48 / 0.47 / 0.47 | 0.72 | 0.01 | S 0.01, D 0.00 |
| E-below | own young | 0.25 | local, common | 0/20 maintained | 0.005 | 0.80 / 0.40 / 0.03 / 0.01 / 0.00 / 0.00 | 0.28 | 0.50 / 0.50 / 0.50 / 0.50 | 0.75 | 0.80 | S 0.00, D 0.00 |
| **E6-global (H2)** | own young | 6 | global | **20/20** (20) | 0.97 | 0.12 / 0.38 / 0.54 / 0.73 / 0.94 / 0.97 | −0.009 | 0.01 / 0.11 / 0.09 / 0.09 | 0.18 | 0.86 | S 0.72, 1.28, 0.65; D 0.64, 0.26, 0.72 |
| E12-global | own young | 12 | global | 20/20 (20) | 0.98 | 0.15 / 0.40 / 0.57 / 0.78 / 0.97 / 0.98 | −0.001 | 0.00 / 0.08 / 0.07 / 0.07 | 0.14 | 0.89 | S 1.26, 2.76, 1.05; D 0.72, 0.27, 0.79 |

Diagnostics are means over payoff states after 1000-5999 updates, then over runs; "cared" means care received this
step (`R > 0`), "uncared" everyone with `R = 0` this step (juveniles included, so not an adult-only rate),
"juvenile" age < 2. E6-local final `h` ranged from 0.64 to 0.82 across runs.

**What this shows (at these settings).**

- **Care for own young still spread with carry-over** (b/c 6, 12, 24; not 3), and help to young neighbours did not
  (0/20). As before, the contrast is the own-young-care package, not parentage alone. My prediction (35%) was wrong.
- **Carry-over changed demography far more than expected.** Condition gained as a juvenile persisted into
  adulthood: occupants not receiving care this step had death probabilities of about 0.06-0.13 (0.50 in R2), the
  mean death probability fell to about 0.06-0.11, and juveniles became a small fraction of the population (about
  0.11-0.21 against 0.55-0.57 in R2; descriptive, different batch). The asymmetry anticipated in the
  pre-registration (lifetime cost against two steps of benefit) did not prevent spread. Stored care raised both
  survival and fecundity, and stored cost lowered fecundity; the run shows spread with all three operating together
  and does not identify which effect drove it.
- **At b/c 6 under local settlement, helping rose more slowly and ended lower** (mean `h` 0.66 at step 2000, about
  0.76 near step 5000, 0.73 at step 6000; final range 0.64-0.82; no convergence criterion was registered) than with random settlement (0.97) or at b/c 12-24 (0.95-0.98). Local
  competition among long-lived relatives is one candidate explanation, not tested.
- **More of the benefit was lost** (about 0.84-0.90): with long lives and few juveniles, most helpers had no living
  juvenile offspring at a given step, yet paid the cost every step.

**Predictions made before the data.** Attempt 1 met: 35% (met). EN6-local <= 3/20: 75% (0/20). H2: 35% (met).

**Archive gaps (Codex):** the verdict file records `care_lam` and `care_juvenile` but not `care_rho` (0.8, from the
committed config), and the CSV drops per-seed correlation samples (H2 is reproducible from the verdict file's
archived means).

**Next:** R3b (births need energy) on this base, pre-registered on the user's go.

Data: `data/r3a_runs.csv`, `data/r3a_verdict.json`, `data/r3a_log.txt`.

## Step R3b: a birth costs the parent condition (run 2026-11-20, code 31374ab, pre-registration 4b81e7f)

**Verdict: met in attempt 1 (`c_b` = 0.5).** Q6-local 19/20 against QN6-local 0/20 (one-sided Fisher p = 2e-10;
descriptive paired McNemar on matched seeds 19 against 0, p = 2e-6), Q-below maintained in 0/20. **H2 met:**
Q6-global 20/20, neighbour `h` correlation −0.003. Attempt 2 (`c_b` = 0.2) was not run, as registered. The
pre-registration was reviewed by Codex (gpt-6.2-sol, medium) before any code; the code review hit the usage limit
partway (its one interim note, that a perfectly uniform trait field can give a correlation of 1.0 instead of
undefined, cannot produce a false H2 pass) and was completed after the run. **Post-run Codex review (2026-11-20, gpt-6.2-sol, medium):** no
verdict-changing finding; counts, Fisher and McNemar p and H2 recomputed from all 160 runs; the charging rule,
`last_parents` semantics on both settlement paths, store resets and diagnostic timing checked. It confirmed the
uniform-field bug: on this grid a uniform `h` field gave a correlation of 1.0, so one such sample could have let
the H2 mean gate pass where the pre-registration says "uninterpretable". No archived R3b sample was affected (all
between −0.072 and 0.075). Fixed after the run (undefined below a numerical tolerance; undefined values now written
as JSON null), with two added tests (uniform field, forced global step). Wording check (gpt-reserve, medium): no
problems.

| Arm | Care goes to | b/c | Settlement | Successes (sustained) | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Neighbour `h` corr. | Death: cared / uncared / parents / mean | Juvenile fraction | Benefit lost | Births per occupant per step / fraction charged | Birth part of `D` (mean) | `D` of recent breeders | Mean `S` / `D`: all, juveniles, parents |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q3-local | own young | 3 | local | 0/20 | 0.014 | 0.04 / 0.02 / 0.01 / 0.02 / 0.01 / 0.01 | 0.35 | 0.46 / 0.50 / 0.49 / 0.49 | 0.74 | 0.79 | 0.49 / 0.40 | 0.13 | 0.51 | S 0.00, 0.00, 0.00; D 0.14, 0.08, 0.48 |
| **Q6-local (test)** | own young | 6 | local | **19/20** (19) | 0.68 | 0.06 / 0.24 / 0.40 / 0.54 / 0.63 / 0.68 | 0.54 | 0.02 / 0.14 / 0.11 / 0.11 | 0.22 | 0.83 | 0.11 / 0.87 | 0.15 | 0.83 | S 0.56, 0.86, 0.52; D 0.58, 0.24, 0.76 |
| Q12-local | own young | 12 | local | 20/20 (20) | 0.91 | 0.10 / 0.29 / 0.40 / 0.55 / 0.74 / 0.91 | 0.57 | 0.00 / 0.08 / 0.08 / 0.07 | 0.14 | 0.88 | 0.07 / 0.97 | 0.12 | 0.97 | S 1.15, 2.41, 0.92; D 0.72, 0.26, 0.89 |
| Q24-local | own young | 24 | local | 20/20 (20) | 0.97 | 0.12 / 0.28 / 0.41 / 0.57 / 0.79 / 0.97 | 0.59 | 0.00 / 0.06 / 0.06 / 0.06 | 0.11 | 0.90 | 0.06 / 0.99 | 0.10 | 1.05 | S 2.08, 5.34, 1.54; D 0.79, 0.27, 0.95 |
| QN6-local (control) | young neighbours | 6 | local | 0/20 | 0.009 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.34 | 0.45 / 0.47 / 0.45 / 0.46 | 0.71 | 0.02 | 0.46 / 0.42 | 0.14 | 0.50 | S 0.02, 0.02, 0.03; D 0.14, 0.08, 0.47 |
| Q-below | own young | 0.25 | local, common | 0/20 maintained | 0.007 | 0.81 / 0.42 / 0.03 / 0.01 / 0.01 / 0.01 | 0.29 | 0.50 / 0.50 / 0.50 / 0.50 | 0.75 | 0.80 | 0.50 / 0.40 | 0.13 | 0.50 | S 0.00, 0.00, 0.00; D 0.13, 0.08, 0.48 |
| **Q6-global (H2)** | own young | 6 | global | **20/20** (20) | 0.93 | 0.09 / 0.38 / 0.53 / 0.68 / 0.85 / 0.93 | −0.003 | 0.01 / 0.11 / 0.10 / 0.09 | 0.18 | 0.85 | 0.09 / 0.98 | 0.15 | 0.98 | S 0.71, 1.24, 0.63; D 0.75, 0.30, 0.94 |
| Q12-global | own young | 12 | global | 20/20 (20) | 0.98 | 0.17 / 0.39 / 0.56 / 0.74 / 0.95 / 0.98 | 0.004 | 0.00 / 0.08 / 0.07 / 0.07 | 0.14 | 0.88 | 0.07 / 1.00 | 0.12 | 1.07 | S 1.27, 2.78, 1.04; D 0.83, 0.30, 1.01 |

Diagnostics are means over payoff states after 1000-5999 updates, then over runs. "Cared" means care received this
step (`R > 0`); "uncared" is everyone with `R = 0` this step, juveniles included. "Fraction charged" is the share of
realized births whose parent survived the step and paid. "Birth part of `D`" is a diagnostic-only copy of the
charges with the same decay. "`D` of recent breeders" is `D` at the payoff computation one step after a charged
birth. Q6-local final `h` ranged from 0.59 to 0.79; the one unsuccessful run ended at 0.592, just below the bar.

**What this shows (at these settings).**

- **Care for own young still spread with a delayed fecundity cost per birth** (b/c 6, 12, 24; not 3), and help to
  young neighbours did not (0/20). As before, the contrast is the own-young-care package against help to young
  neighbours, not parentage alone.
- **It spread without local settlement too** (Q6-global 20/20, neighbour correlation about 0).
- **The cost was real but modest on average.** The birth part of `D` averaged about 0.10-0.15, below the
  pre-registered upper bound of 0.25. A parent one step after a charged birth carried `D` of about 0.83-1.07 in the
  arms where helping spread.
- **Compared with R3a (descriptive, different batch):** at b/c 6 under local settlement, helping ended a little
  lower (0.68 against 0.73) and one run fell just short of the bar (19/20 against 20/20); with random settlement it
  ended at 0.93 against 0.97. Mean `D` was higher by about the birth part (0.58 against 0.46 at Q6-local). Ages and
  death rates were close to R3a's. The two batches are not paired, so these differences are not tested.
- **The charge mostly fell on survivors where helping spread** (87-100% of births charged), and on fewer than half
  of the births where it did not (40-42%), consistent with death probabilities near 0.5 there: many parents died
  in the step they bred.

**Predictions made before the data.** Attempt 1 met: 45% (met). QN6-local <= 3/20: 80% (0/20). H2: 55% (met).

**Next:** R3c (births need a minimum condition, with empty sites) on this base, pre-registered on the user's go,
after the Codex code review of R3b.

Data: `data/r3b_runs.csv`, `data/r3b_verdict.json`, `data/r3b_log.txt`.

## Step R3c: births need a minimum condition, so sites can stay empty (run 2026-11-20, code 8cc4d94, pre-registration da353fd)

**Verdict: met in attempt 1 (`θ` = 0.25).** V6-local 20/20 against VN6-local 0/20 on the joint endpoint (final mean
`h` over occupied sites >= 0.60 and final occupancy >= 0.5; one-sided Fisher p = 7e-12; descriptive paired McNemar
20 against 0, p = 1e-6), V-below maintained in 0/20. **H2 met:** V6-global 20/20, neighbour `h` correlation −0.003.
Attempt 2 (`θ` = 0) was not run, as registered. The pre-registration and the code were reviewed by Codex
(gpt-6.2-sol, medium) before the run; its code findings (survival denominator, per-step occupancy, extra stream and
mixed-pool tests) were fixed before the batch.

**Main caveat: the threshold acted, but sites almost never stayed empty.** The threshold excluded 3-29% of
occupants from breeding and trimmed 16-80% of the lotteries for a site, but no candidate pool was ever fully
ineligible except in at most 0.3% of fills, occupancy stayed at 1.00 throughout, and no run went extinct. So R3c
tested a breeding threshold that changes who wins births; it did not test life with vacant space.

| Arm | Care goes to | b/c | Settlement | Successes | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Neighbour `h` corr. | Death: cared / uncared / parents / mean | Juvenile fraction | Benefit lost | Ineligible: all / `h` < 0.5 / `h` >= 0.5 | Fills trimmed / emptied | Occupancy (window, final) | Mean `S` / `D`: all, juveniles, parents |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V3-local | own young | 3 | local | 0/20 | 0.015 | 0.04 / 0.02 / 0.02 / 0.01 / 0.01 / 0.01 | 0.34 | 0.46 / 0.50 / 0.49 / 0.49 | 0.74 | 0.79 | 0.04 / 0.04 / – | 0.17 / 0.000 | 1.00, 1.00 | S 0.00, 0.00, 0.00; D 0.14, 0.08, 0.48 |
| **V6-local (test)** | own young | 6 | local | **20/20** | 0.67 | 0.06 / 0.25 / 0.40 / 0.54 / 0.65 / 0.67 | 0.54 | 0.03 / 0.14 / 0.11 / 0.12 | 0.22 | 0.83 | 0.05 / 0.02 / 0.05 | 0.21 / 0.000 | 1.00, 1.00 | S 0.55, 0.84, 0.51; D 0.57, 0.23, 0.75 |
| V12-local | own young | 12 | local | 20/20 | 0.85 | 0.10 / 0.29 / 0.40 / 0.55 / 0.70 / 0.85 | 0.57 | 0.00 / 0.09 / 0.08 / 0.07 | 0.15 | 0.87 | 0.11 / 0.00 / 0.11 | 0.49 / 0.001 | 1.00, 1.00 | S 1.10, 2.29, 0.89; D 0.69, 0.25, 0.86 |
| V24-local | own young | 24 | local | 20/20 | 0.97 | 0.12 / 0.28 / 0.41 / 0.56 / 0.76 / 0.97 | 0.58 | 0.00 / 0.06 / 0.06 / 0.06 | 0.11 | 0.90 | 0.17 / 0.00 / 0.17 | 0.69 / 0.003 | 1.00, 1.00 | S 2.07, 5.29, 1.53; D 0.78, 0.27, 0.94 |
| VN6-local (control) | young neighbours | 6 | local | 0/20 | 0.009 | 0.04 / 0.02 / 0.01 / 0.01 / 0.01 / 0.01 | 0.33 | 0.45 / 0.47 / 0.45 / 0.46 | 0.71 | 0.02 | 0.03 / 0.03 / – | 0.16 / 0.000 | 1.00, 1.00 | S 0.02, 0.02, 0.03; D 0.14, 0.08, 0.47 |
| V-below | own young | 0.25 | local, common | 0/20 maintained | 0.007 | 0.81 / 0.44 / 0.05 / 0.01 / 0.01 / 0.01 | 0.29 | 0.50 / 0.50 / 0.50 / 0.50 | 0.75 | 0.80 | 0.04 / 0.04 / – | 0.17 / 0.000 | 1.00, 1.00 | S 0.00, 0.00, 0.00; D 0.13, 0.08, 0.48 |
| **V6-global (H2)** | own young | 6 | global | **20/20** | 0.89 | 0.09 / 0.38 / 0.54 / 0.71 / 0.84 / 0.89 | −0.003 | 0.01 / 0.11 / 0.10 / 0.09 | 0.18 | 0.85 | 0.24 / 0.02 / 0.24 | 0.72 / 0.002 | 1.00, 1.00 | S 0.69, 1.20, 0.62; D 0.73, 0.29, 0.92 |
| V12-global | own young | 12 | global | 20/20 | 0.97 | 0.16 / 0.38 / 0.54 / 0.75 / 0.93 / 0.97 | 0.001 | 0.00 / 0.08 / 0.07 / 0.07 | 0.13 | 0.88 | 0.29 / 0.00 / 0.29 | 0.80 / 0.003 | 1.00, 1.00 | S 1.27, 2.78, 1.04; D 0.83, 0.30, 1.01 |

Diagnostics are means over payoff states after 1000-5999 updates, then over runs, over occupied sites. "Ineligible"
is the fraction of occupants with `W < θ`, split by helping level (– where no occupant had `h` >= 0.5). "Fills
trimmed" is the share of sites needing a birth whose pool lost at least one occupant to the threshold; "emptied" is
the share left empty. Occupancy is shown as the mean over the diagnostic window and the final value (the mean over
the last 1000 steps was also 1.00 in every arm; the lowest final occupancy of any run was 0.997). V6-local final
`h` ranged from 0.61 to 0.76.

**What this shows (at these settings).**

- **Care for own young still spread with a breeding threshold** (b/c 6, 12, 24; not 3), and help to young
  neighbours did not (0/20). As before, the contrast is the own-young-care package against help to young
  neighbours, not parentage alone. It also spread without local settlement (V6-global 20/20).
- **Ineligibility was concentrated among helpers.** Among occupants with `h` >= 0.5, 5-29% were ineligible at a given
  step; among those with `h` < 0.5, at most 4%. That matches the direction of the pre-registered benchmark
  (depletion from caring lowers `W`).
- **Compared with R3b (descriptive, different batch):** helping ended a little lower at b/c 6 local (0.67 against
  0.68), 12 local (0.85 against 0.91) and 6 global (0.89 against 0.93). The batches are not paired, so these
  differences are not tested; their direction fits ineligibility being concentrated among helpers.
- **Vacancies did not occur in practice** (see the caveat above): in every pool of five candidates at least one was
  almost always eligible.

**Predictions made before the data.** Attempt 1 met: 40% (met). VN6-local <= 3/20: 80% (0/20). H2: 50% (met).
Occupancy above 0.9 in the successful arms: 65% (1.00).

**Next:** R3d (starvation) on this base, pre-registered on the user's go. Since R3c produced no vacant space,
whether care survives with empty sites is still untested; starvation is a natural way to create them.

Data: `data/r3c_runs.csv`, `data/r3c_verdict.json`, `data/r3c_log.txt`.

## Step R3d: starvation, death when condition falls too low (run 2026-11-20, code c1d29c5, pre-registration 1a5830a)

**Verdict: met in attempt 1 (`σ` = 0), starvation active, but only just.** F6-local 19/20 against FN6-local 0/20 on
the joint endpoint (one-sided Fisher p = 2e-10; descriptive paired McNemar 19 against 0, p = 2e-6), F-below
maintained in 0/20. **H2 met:** F6-global 20/20, neighbour `h` correlation −0.003. **Activation:** added starvation
deaths (`W < σ` while the base draw said survive) were 1.33% of all deaths in F6-local over the diagnostic window,
above the pre-registered 1% bar, so the label is "active". Attempt 2 (`σ` = −0.1) was not run, as registered. The
pre-registration and the code were reviewed by Codex (gpt-6.2-sol, medium) before the run.

| Arm | Care goes to | b/c | Settlement | Successes | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Neighbour `h` corr. | Death: cared / uncared / parents / mean | Added starvation share of deaths | Starvation rate: `h` < 0.5 / `h` >= 0.5 / recent parents / juveniles | Ineligible: all / `h` < 0.5 / `h` >= 0.5 | Fills emptied | Occupancy (window, final) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F3-local | own young | 3 | local | 0/20 | 0.014 | 0.04 / 0.02 / 0.02 / 0.01 / 0.01 / 0.01 | 0.34 | 0.46 / 0.50 / 0.49 / 0.49 | 0.004 | 0.003 / – / 0.022 / 0.003 | 0.03 / 0.03 / – | 0.000 | 1.00, 1.00 |
| **F6-local (test)** | own young | 6 | local | **19/20** | 0.65 | 0.06 / 0.25 / 0.40 / 0.54 / 0.63 / 0.65 | 0.53 | 0.03 / 0.14 / 0.11 / 0.12 | **0.013** | 0.001 / 0.002 / 0.021 / 0.001 | 0.04 / 0.02 / 0.04 | 0.000 | 1.00, 1.00 |
| F12-local | own young | 12 | local | 20/20 | 0.87 | 0.10 / 0.31 / 0.43 / 0.57 / 0.72 / 0.87 | 0.57 | 0.00 / 0.08 / 0.08 / 0.07 | 0.021 | 0.000 / 0.002 / 0.026 / 0.000 | 0.12 / 0.01 / 0.12 | 0.001 | 1.00, 1.00 |
| F24-local | own young | 24 | local | 20/20 | 0.97 | 0.11 / 0.29 / 0.41 / 0.57 / 0.77 / 0.97 | 0.58 | 0.00 / 0.06 / 0.06 / 0.06 | 0.019 | 0.000 / 0.001 / 0.021 / 0.000 | 0.17 / 0.00 / 0.17 | 0.003 | 1.00, 1.00 |
| FN6-local (control) | young neighbours | 6 | local | 0/20 | 0.008 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.34 | 0.45 / 0.47 / 0.45 / 0.46 | 0.004 | 0.003 / – / 0.020 / 0.003 | 0.03 / 0.03 / – | 0.000 | 1.00, 1.00 |
| F-below | own young | 0.25 | local, common | 0/20 maintained | 0.007 | 0.81 / 0.42 / 0.04 / 0.01 / 0.01 / 0.01 | 0.29 | 0.50 / 0.50 / 0.50 / 0.50 | 0.004 | 0.004 / – / 0.022 / 0.003 | 0.03 / 0.03 / – | 0.000 | 1.00, 1.00 |
| **F6-global (H2)** | own young | 6 | global | **20/20** | 0.86 | 0.10 / 0.40 / 0.55 / 0.70 / 0.82 / 0.86 | −0.003 | 0.02 / 0.11 / 0.10 / 0.10 | 0.043 | 0.001 / 0.005 / 0.056 / 0.000 | 0.20 / 0.01 / 0.20 | 0.001 | 1.00, 1.00 |
| F12-global | own young | 12 | global | 20/20 | 0.97 | 0.15 / 0.37 / 0.52 / 0.74 / 0.96 / 0.97 | −0.006 | 0.00 / 0.08 / 0.07 / 0.07 | 0.033 | 0.000 / 0.002 / 0.039 / 0.000 | 0.28 / 0.00 / 0.28 | 0.002 | 1.00, 1.00 |

Diagnostics are means over payoff states after 1000-5999 updates, then over runs, over occupied sites; the added
starvation share is pooled (added starvation deaths over all deaths of start-of-step occupants, summed over the
window and seeds). Starvation rates are per occupant per step; "recent parents" were charged for a birth in the
previous step. – where no occupant had `h` >= 0.5. F6-local final `h` ranged from 0.599 to 0.70; the one
unsuccessful run ended at 0.599, just below the bar. No run went extinct; the lowest final occupancy was 0.997.

**What this shows (at these settings).**

- **Care for own young still spread with starvation added** (b/c 6, 12, 24; not 3), and help to young neighbours
  did not (0/20). As before, the contrast is the own-young-care package against help to young neighbours, not
  parentage alone. It also spread without local settlement (F6-global 20/20).
- **Starvation acted, but weakly.** It caused 0.4-4.3% of deaths, and in the test arm 1.3%, just above the
  pre-registered activation bar; read the "active" label with that in mind.
- **Starvation was more common among recent breeders, as the screen predicted.** Occupants charged for a birth in the previous step
  starved at about 2-6% per step; other occupants at at most 0.5%, and juveniles at at most 0.3%. Where helping
  spread, starvation was more common among high helpers than among low ones (0.1-0.5% against at most 0.1%). In
  the arms where helping stayed near 0, recent breeders starved at a similar rate (about 2%), consistent with
  repeated births at high birth rates (about 0.5 per occupant per step there).
- **Compared with R3c (descriptive, different batch):** final `h` was close at b/c 6 local (0.65 against 0.67) and
  12 local (0.87 against 0.85), and a little lower at b/c 6 global (0.86 against 0.89). The batches are not paired,
  so these differences are not tested.
- **Vacancies stayed rare** (at most 0.3% of fills emptied, occupancy 1.00), as expected: vacant space is still
  untested.

**Predictions made before the data.** Attempt 1 met: 40% (met). Starvation active in F6-local: 70% (active, 1.3%).
FN6-local <= 3/20: 80% (0/20). H2: 50% (met). Fills left empty below 1% in every arm: 75% (at most 0.3%).

**Next:** the energy steps R3a-R3d are complete; what comes next (vacant space, income, or a first PPG-style port)
is decided with the user.

Data: `data/r3d_runs.csv`, `data/r3d_verdict.json`, `data/r3d_log.txt`.

## Step R4: income from a limited, renewable site resource (run 2026-11-20, code 4190a81, pre-registration b0104c2)

**Verdict: met in attempt 1 (`γ` = 0.15); income limitation active.** G6-local 19/20 against GN6-local 0/20 on the
joint endpoint (one-sided Fisher p = 2e-10; descriptive paired McNemar 19 against 0, p = 2e-6), G-below maintained
in 0/20. **H2 met:** G6-global 20/20, neighbour `h` correlation −0.003. **Activation:** pooled harvest in G6-local
was 0.150 per occupant-step (unlimited: 0.2; bar: at most 0.19), so the label is "income limitation active". As
pre-registered, this measures exposure to limitation, not an effect of it. Attempt 2 (`γ` = 0.18) was not run, as
registered. The pre-registration and the code were reviewed by Codex (gpt-6.2-sol, medium) before the run. The code
review found one runner bug (a float-rounding error at the inclusive 0.19 cutoff), fixed before the run; the fixes
themselves were not re-reviewed.

| Arm | Care goes to | b/c | Settlement | Successes | Mean final `h` | Mean `h` at steps 50 / 250 / 500 / 1000 / 2000 / 6000 | Neighbour `h` corr. | Harvest per occupant-step (pooled) | `G`: all / juveniles / parents | Resource: occupied / empty sites | Added starvation share of deaths | Starvation rate: `h` < 0.5 / `h` >= 0.5 / recent parents / juveniles | Ineligible: all / `h` < 0.5 / `h` >= 0.5 | Fills emptied | Occupancy (window, final) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G3-local | own young | 3 | local | 0/20 | 0.014 | 0.04 / 0.02 / 0.01 / 0.01 / 0.01 / 0.01 | 0.35 | 0.150 | 0.92 / 0.94 / 0.89 | 0.150 / 0.150 | 0.004 | 0.004 / – / 0.024 / 0.004 | 0.05 / 0.05 / – | 0.000 | 1.000, 1.000 |
| **G6-local (test)** | own young | 6 | local | **19/20** | 0.900 | 0.06 / 0.21 / 0.39 / 0.53 / 0.65 / 0.90 | 0.53 | 0.150 | 0.85 / 0.93 / 0.82 | 0.150 / 0.198 | 0.256 | 0.006 / 0.038 / 0.096 / 0.003 | 0.31 / 0.08 / 0.31 | 0.009 | 0.998, 0.998 |
| G12-local | own young | 12 | local | 20/20 | 0.933 | 0.10 / 0.31 / 0.42 / 0.57 / 0.78 / 0.93 | 0.56 | 0.150 | 0.83 / 0.93 / 0.81 | 0.150 / 0.208 | 0.487 | 0.002 / 0.047 / 0.077 / 0.000 | 0.31 / 0.04 / 0.32 | 0.014 | 0.999, 0.998 |
| G24-local | own young | 24 | local | 20/20 | 0.960 | 0.12 / 0.27 / 0.39 / 0.56 / 0.77 / 0.96 | 0.58 | 0.150 | 0.81 / 0.93 / 0.79 | 0.150 / 0.213 | 0.558 | 0.001 / 0.042 / 0.048 / 0.000 | 0.26 / 0.02 / 0.26 | 0.012 | 0.999, 0.999 |
| GN6-local (control) | young neighbours | 6 | local | 0/20 | 0.008 | 0.04 / 0.01 / 0.01 / 0.01 / 0.01 / 0.01 | 0.34 | 0.150 | 0.91 / 0.94 / 0.89 | 0.150 / – | 0.004 | 0.004 / – / 0.023 / 0.004 | 0.05 / 0.05 / – | 0.000 | 1.000, 1.000 |
| G-below | own young | 0.25 | local, common | 0/20 maintained | 0.008 | 0.82 / 0.44 / 0.05 / 0.01 / 0.01 / 0.01 | 0.30 | 0.150 | 0.92 / 0.94 / 0.89 | 0.150 / – | 0.004 | 0.004 / – / 0.024 / 0.004 | 0.05 / 0.05 / – | 0.000 | 1.000, 1.000 |
| **G6-global (H2)** | own young | 6 | global | **20/20** | 0.961 | 0.09 / 0.39 / 0.53 / 0.72 / 0.93 / 0.96 | −0.00 | 0.150 | 0.85 / 0.93 / 0.83 | 0.150 / 0.151 | 0.548 | 0.003 / 0.077 / 0.109 / 0.001 | 0.39 / 0.05 / 0.39 | 0.009 | 0.999, 0.999 |
| G12-global | own young | 12 | global | 20/20 | 0.983 | 0.16 / 0.37 / 0.54 / 0.74 / 0.96 / 0.98 | −0.00 | 0.150 | 0.83 / 0.93 / 0.81 | 0.150 / 0.151 | 0.680 | 0.002 / 0.067 / 0.047 / 0.000 | 0.33 / 0.04 / 0.33 | 0.004 | 1.000, 0.999 |
| G6-local-lean | own young, γ 0.08 | 6 | local | 20/20 | 0.973 | 0.05 / 0.10 / 0.28 / 0.58 / 0.93 / 0.97 | 0.48 | 0.080 | 0.70 / 0.83 / 0.64 | 0.080 / 0.091 | 0.782 | 0.037 / 0.152 / 0.163 / 0.006 | 0.37 / 0.40 / 0.37 | 0.011 | 0.998, 0.998 |
| G6-global-lean | own young, γ 0.08 | 6 | global | 20/20 | 0.982 | 0.07 / 0.38 / 0.58 / 0.90 / 0.98 / 0.98 | −0.00 | 0.080 | 0.70 / 0.83 / 0.65 | 0.080 / 0.081 | 0.809 | – / 0.158 / 0.152 / 0.005 | 0.38 / – / 0.38 | 0.008 | 0.999, 0.999 |

Diagnostics are means over payoff states after 1000-5999 updates, then over runs, over occupied sites; `G` is the
income store at payoff time (after the harvest); resource is the site stock before the harvest; harvest and the added
starvation share are pooled over the window and seeds. "Recent parents" were charged for a birth in the previous
step. – where no site of that kind existed. G6-local final `h` ranged from 0.58 to 0.98; the one unsuccessful run ended at
0.58. No run went extinct; the lowest final occupancy in any arm was 0.991. Death probability (cared / uncared /
parents / mean) in G6-local was 0.02 / 0.11 / 0.09 / 0.09, and births per occupant per step 0.13 (0.47-0.50 in the
arms where helping stayed near 0).

**What this shows (at these settings).**

- **In the limited-income arms, care for own young still spread** (b/c 6, 12, 24; not 3), and help to young
  neighbours did not (0/20). As before, the contrast is the own-young-care package against help to young
  neighbours, not parentage alone. It also spread without local settlement (G6-global 20/20).
- **The resource was limiting throughout.** Occupied sites were harvested to the regrowth level every step (resource
  before harvest 0.150, capped in more than 99% of occupant-steps), and income stores were below the old baseline 1:
  about 0.85 in the helping arms and 0.70 in the lean arms, lowest among parents.
- **Added starvation deaths were a large share of deaths where helping spread:** 26% of deaths in G6-local (R3d's
  F6-local, a different batch: 1.3%), 49-68% in the other `γ` = 0.15 arms where helping spread, and about 80% in the
  lean arms. It was more common among high helpers and
  recent breeders than among low helpers and juveniles. In the arms where helping stayed near 0 it stayed at 0.4%.
- **Helping ended higher, not lower, than in R3d (descriptive, different batch).** The screen predicted that limited
  income would penalize high helping; final `h` was 0.90 at b/c 6 local (R3d: 0.65), 0.96 at b/c 6 global (R3d: 0.86),
  and 0.97-0.98 in the lean arms. In G6-local the mean `h` was similar to R3d's batch mean up to step 2000 (0.65 against 0.63) and kept
  rising afterwards. The batches are not paired and no mechanism was tested; the screen used steady states for
  occupants that receive no care, while helpers' own young do receive it.
- **Vacancies stayed rare even at `γ` = 0.08:** at most 1.4% of fills emptied in any arm (lean arms 1.1% and 0.8%), with
  occupancy at least 0.998 in the window. Vacant space remained rare at these settings; whether limited income
  changed the vacancy rate was not tested.

**Predictions made before the data.** Attempt 1 met: 30% (met). Income limitation active in G6-local: 90% (active,
0.150). GN6-local <= 3/20: 85% (0/20). H2 >= 15/20: 40% (met, 20/20). Fills left empty below 1% in the `γ` = 0.15
arms: 70% (not met: the test arm 0.9%, but G12-local 1.4% and G24-local 1.2%). Above 5% in at least one lean arm:
50% (not met: 1.1% and 0.8%).

**Next:** decided with the user. Candidates from the pre-registration: care that transfers income, a newborn endowment
taken from the parent, or foraging movement; substantial vacant space is still untested.

Data: `data/r4_runs.csv`, `data/r4_verdict.json`, `data/r4_log.txt`.

## Diagnostic DR4: why did helping rise under limited income? (run 2026-11-20, code 2a37902, pre-registration 51821a1, labels 1010b9d)

**Result: valid. Under the registered attribution rule, a uniform baseline of 0.75 accounted for most of the rise
and the rise persisted with a lower endowment; a baseline of 0.85 did not; the birth-cost reading is unclear.** The
readings are labels of a counterfactual decomposition, not direct causal proportions. Both references reproduced the stored runs exactly (D-F against
R3d's F6-local, D-G against R4's G6-local: per-seed final `h` and final occupancy, and the across-seed mean trajectory;
see the pre-run amendment in the README). The rise was `Δ` = 0.247 (95% seed-block bootstrap interval 0.198-0.288;
bar 0.10). The code was reviewed by Codex (gpt-6.2-sol, medium) before the run; the review found one output bug (the
CSV would have dropped the income columns of the R4 arms) and two edge cases, all fixed before the run, but the fixes
were not re-reviewed.

| Part | Arm (against) | Numerator | Share of `Δ` | `d` = numerator − 0.5`Δ` (95% interval) | Reading |
| --- | --- | --- | --- | --- | --- |
| Uniform cut to 0.85 | D-U85 (D-F) | −0.025 | −0.10 | −0.148 (−0.173, −0.120) | accounts for less than half |
| Uniform cut to 0.75 | D-U75 (D-F) | +0.284 | 1.15 | +0.161 (+0.136, +0.191) | **accounts for most of the rise** |
| Lower endowment (`G` start 0.75) | D-E (D-F) | +0.250 | 1.01 | +0.126 (+0.065, +0.179) | accounts for most (free endowment **not needed**) |
| No birth costs | D-Gcb0 (D-Fcb0) | +0.140 | 0.57 | +0.017 (−0.032, +0.064) | unclear |

**Overall (mechanical):** clear readings for the two uniform cuts and the endowment; the birth-cost pair is unclear.
Neither "inconclusive" nor "unexplained by these parts" applies.

| Arm | Model | Successes | Mean final `h` (sd) | Mean `h` at 2000 / 4000 / 6000 | Ineligible: all / `h` < 0.5 / `h` >= 0.5 / recent parents | Starvation rate: `h` < 0.5 / `h` >= 0.5 / recent parents | Added starvation share of deaths | Births per occupant-step: `h` < 0.5 / `h` >= 0.5 | `G` at payoff: all / juveniles / parents | `S`, `D` | Fills emptied |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D-F | R3d | 19/20 | 0.653 (0.028) | 0.63 / 0.64 / 0.65 | 0.04 / 0.01 / 0.04 / 0.13 | 0.001 / 0.002 / 0.021 | 0.013 | 0.147 / 0.117 | – | 0.55, 0.56 | 0.000 |
| D-G | R4 | 19/20 | 0.900 (0.117) | 0.65 / 0.80 / 0.90 | 0.31 / 0.08 / 0.31 / 0.27 | 0.006 / 0.038 / 0.096 | 0.256 | 0.155 / 0.124 | 0.85 / 0.93 / 0.82 | 0.67, 0.62 | 0.009 |
| D-U85 | R3d, baseline 0.85 | 17/20 | 0.628 (0.021) | 0.62 / 0.62 / 0.63 | 0.16 / 0.06 / 0.17 / 0.26 | 0.005 / 0.007 / 0.071 | 0.048 | 0.150 / 0.124 | – | 0.53, 0.54 | 0.001 |
| D-U75 | R3d, baseline 0.75 | 20/20 | 0.937 (0.062) | 0.63 / 0.83 / 0.94 | 0.35 / 0.13 / 0.36 / 0.37 | 0.012 / 0.049 / 0.135 | 0.326 | 0.159 / 0.131 | – | 0.69, 0.61 | 0.014 |
| D-E | R4, `G` start 0.75 | 18/20 | 0.902 (0.132) | 0.63 / 0.85 / 0.90 | 0.35 / 0.14 / 0.36 / 0.37 | 0.012 / 0.053 / 0.135 | 0.350 | 0.158 / 0.132 | 0.75 / 0.75 / 0.75 | 0.70, 0.61 | 0.014 |
| D-Fcb0 | R3d, `c_b` = 0 | 20/20 | 0.721 (0.048) | 0.67 / 0.71 / 0.72 | 0.01 / 0.00 / 0.01 / 0.00 | 0 / 0 / 0 | 0 | 0.141 / 0.108 | – | 0.58, 0.45 | 0.000 |
| D-Gcb0 | R4, `c_b` = 0 | 20/20 | 0.861 (0.105) | 0.67 / 0.83 / 0.86 | 0.19 / 0.00 / 0.19 / 0.01 | 0 / 0.016 / 0 | 0.113 | 0.141 / 0.107 | 0.84 / 0.93 / 0.82 | 0.65, 0.50 | 0.003 |

Seeds 0-19, 6000 steps, b/c 6, local settlement. Diagnostics are means over payoff states after 1000-5999 updates,
then over runs; births by class and the starvation share are pooled over the window and seeds. No run went extinct;
final occupancy was at least 0.996 in every arm. Occupants with `h` < 0.5 were 2-6% of occupant-steps.

**What this shows (at these settings).**

- **In this diagnostic, a uniform baseline of 0.75 was sufficient to meet the registered rise criterion, without site
  resources or an age gradient; a baseline of 0.85 was not.** The 0.75 baseline gave final `h` 0.94 (R4: 0.90); 0.85,
  approximately R4's mean `G` at payoff (0.845), gave 0.63, no higher than R3d. Because the lottery ignores a uniform
  shift, these two arms differ from R3d only through the absolute breeding and starvation cutoffs. The large
  difference between 0.85 and 0.75 suggests a sharp, threshold-like response over this interval; two levels cannot
  establish its shape.
- **R4's observed ineligibility and starvation rates were closer to the 0.75 arm's than to the 0.85 arm's.**
  Ineligibility (31%) and starvation of recent parents (9.6% per step) in D-G lay between the 0.85 arm (16%, 7.1%)
  and the 0.75 arm (35%, 13.5%), closer to the latter (these are outcome rates, not a direct measure of exposure). Adults' stores (parents 0.82) were below the overall mean, which includes juveniles (0.93).
  Which feature of R4's condition distribution sets its effective cut was not tested.
- **High helping persisted when founders and newborns started at `G` = 0.75** (so `G` about 0.75 for everyone; the
  registered label: free endowment "not needed" for most of the rise). R4 still ended at 0.90, close to the constant 0.75 baseline (0.94; descriptive). Whether R4's site resource dynamics
  add anything beyond the level cut is not separated by these arms.
- **Birth costs: unclear.** Without birth costs, R4 still ended above R3d (0.86 against 0.72; 57% of `Δ`), but the
  matched comparison does not resolve how much of the R4-R3d difference is attributable to birth costs. Removing birth costs also raised `h` in R3d itself
  (0.72 against 0.65).
- **The higher helping came with more starvation and ineligibility.** These rates were generally higher among high
  helpers than among low helpers and, in the arms with birth costs, among recent parents (rates, not shares of
  events). The pooled births per occupant-step were not higher for high helpers than for the rare low helpers in any
  arm; this is not a measure of lifetime reproduction and does not identify the pathway. How the harsher cutoffs
  favoured care was not tested (one candidate: received care, `0.5 S`, decides more often whether a young
  occupant clears the cutoffs).
- Mean `h` was similar in all arms at step 2000 (0.62-0.67); the arms separated between steps 2000 and 6000, and R4,
  the 0.75 arm and the lower-endowment arm were still rising at 6000.

**Predictions made before the data.** `s_U85` accounts for most: 35% (no: less than half). `s_U75` accounts for
most: 45% (yes). Free endowment needed: 30% (no: not needed). Birth costs needed: 40% (unclear). Unexplained by these
parts: 20% (no). Inconclusive: 15% (no).

**Limits.** One b/c level, local settlement; final `h` at 6000 steps is not an equilibrium; the 0.85 baseline was
chosen after seeing R4. The arms do not separate the eligibility pathway from the starvation pathway. DR4 does not
change R4's verdict and makes no kin-selection claim.

**For R5.** Read helping levels in R5 against this: at these settings, a uniform 0.75 baseline was sufficient to
raise final `h` without site resources, so a change in `h` under foraging or movement need not be attributable
solely to spatial resource differences.

**Next:** decided with the user. Pre-registered next: R5a's exposure pilot.

## Step R5a exposure pilot: foraging over the neighbourhood (run 2026-11-20, code 577c7ca, pre-registration 51821a1)

**Result: below the pilot exposure threshold; the R5a main run was not done, as pre-registered.** In seeds 0-1,
the harvest under neighbourhood foraging differed by more than 0.01 from R4's own-site rule (same state) in 0.78% of
occupant-steps in the test arm (`γ` = 0.15) and 0.06% in the lean arm (`γ` = 0.08); neither arm reached the 2%
threshold. The code was reviewed by Codex (gpt-6.2-sol, medium) before the run; the review found two issues (a second,
step-averaged exposure fraction in the output, and float rounding at the strict 0.01 cutoff), both fixed before the
run, but the fixes were not re-reviewed.

| Arm | Occupant-steps (window, 2 seeds) | Exposed (> 0.01) | Exposure (per seed) | Occupants next to an empty site | Harvest: next to / away from empty sites | Occupancy (window) | Fills emptied | Final `h` (seeds 0, 1) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A6-local (`γ` 0.15) | 5,754,307 | 44,630 | **0.78%** (0.79%, 0.76%) | 0.39% | 0.165 / 0.150 | 0.999 | 0.8% | 0.95, 0.96 |
| A6-local-lean (`γ` 0.08) | 5,748,620 | 3,366 | **0.06%** (0.06%, 0.06%) | 0.77% | 0.088 / 0.080 | 0.998 | 1.1% | 0.96, 0.97 |

Payoff states after 1000-5999 updates; counts pooled over both seeds.

**What this shows (at these settings).** Neighbourhood foraging differed from the own-site rule on very few
occupant-steps, as the screen predicted (upper bounds 1.3% and 2.4%): window occupancy remained at least 0.998, and
the higher mean harvest was concentrated among occupant-steps next to the rare empty sites (about 0.165 against
0.150 in the test arm); the pilot does not show that all differences were confined to those occupants. In the lean arm,
fewer occupants cleared the 0.01 cutoff although more of them were next to an empty site, a pattern consistent with
the screen's isolated-vacancy example (none clearing the cutoff at `γ` = 0.08). The pilot measures a one-step difference
on the same state; cumulative effects, and whether they fall mostly on juveniles or breeders, are not covered.

**Prediction made before the data.** R5a pilot inert: 75% (inert).

**Next:** the pre-registration said the R5b movement pilot runs even though R5a was below its threshold. By user
decision (2026-11-20) R5b was not run: with window occupancy at least 0.998, moves per occupant-step are bounded at
about 0.1-0.2% on these states (each empty site takes at most one mover), below R5b's 0.5% bar (recorded as "not
run: user decision, low expected exposure"; see the README). **Next registered step:** R6, in which the newborn's
endowment is partly or wholly paid by its parent.

## Step R6 pilot: the newborn's endowment paid by its parent (run 2026-11-20, code 14e3c62, pre-registration 8e056ea)

**Result: vacant space rare at both levels; no level chosen, so the R6 main run was not done, as pre-registered.**
Both levels were viable (no extinction, final occupancy at least 0.9965), but neither left at least 5% of needed fills
empty or brought window occupancy down to 0.97. The level choice was written before `h` was reported. The code was
reviewed by Codex (gpt-6.2-sol, medium) before the run; the review found two failure-path bugs in the pilot runner (a
failed rerun could leave an earlier passing selection; the selector did not check the level set), both fixed before
the run, but the fixes were not re-reviewed.

| Level | Effective birth cost | Window occupancy | Fills left empty / needed | Viable | Outcome |
| --- | --- | --- | --- | --- | --- |
| `q` = 1 (parent pays 0.75) | 1.25 | 0.999 | 0.28% (5,752 / 2,029,743) | yes | vacant space rare |
| `q` = 0.5 (parent pays 0.375) | 0.875 | 0.996 | 1.97% (23,022 / 1,168,008) | yes | vacant space rare |

Test arm only (b/c 6, local settlement), seeds 0-1, 6000 steps; counts pooled over payoff states after 1000-5999
updates and both seeds (bars: fill failure >= 5% or occupancy <= 0.97).

**Recorded after the selection (not used in it).**

| Level | Final `h` (seeds 0, 1) | Recent parents starving per step | Recent parents in overdraft | Births per occupant-step | Juvenile fraction | Mean age | `G` mean | `S` of juveniles | Added starvation share of deaths | Ineligible | Births by parents dying that step | Paid per birth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `q` = 1 | 0.97, 0.97 | 100% | 27% | 0.35 | 0.69 | 1.6 | 0.55 | 0.78 | 75% | 41% | 3.7% | 0.72 |
| `q` = 0.5 | 0.97, 0.98 | 51% | 2% | 0.20 | 0.39 | 2.8 | 0.64 | 1.02 | 70% | 45% | 4.8% | 0.36 |

For comparison, D-E (DR4, `q` = 0, 20 seeds): recent parents starving 13.5% per step, fills left empty 1.4%.

**What this shows (at these settings).**

- **Paying for the endowment imposed large costs on parents, especially at `q` = 1, but did not create enough vacant
  space.** At `q` = 1 the recorded starvation rate of recent parents was 100% per step; the population turned over
  fast (births 0.35 per occupant-step, mean age 1.6, 69% juveniles). Fewer fills failed than at `q` = 0.5 (0.28%
  against 1.97%). The population was mostly juvenile at `q` = 1, which is consistent with, but does not establish,
  the screen's second consequence: juvenile replacement candidates (starting at `G` = 0.75, able to breed) keeping
  pools eligible. That mechanism was not tested directly.
- Fills left empty rose from D-E's 1.4% (a separate batch) to about 2% at `q` = 0.5, still below the 5% bar.
- Final `h` was high in all four pilot runs (0.97-0.98). The pilot cannot assess whether care spreads because of
  kin, or whether it collapses when parents die soon after a birth: it ran only the test arm, on two seeds, and final
  `h` alone is not diagnostic of either question.

**Predictions made before the data.** `q` = 1 viable: 70% (viable). Vacant space at `q` = 1: 35% (no); at `q` =
0.5: 20% (no). Pilot passes at some level: 40% (no).

**Next:** decided with the user. Candidates named in the pre-registration: a lower endowment, or juveniles that cannot
breed (the pilot is consistent with breeding juveniles keeping pools eligible).

## Step R7 pilot: juveniles cannot breed (run 2026-11-20, code 58d5f68, pre-registration 20bbece)

**Result: no level chosen, so the R7 main run was not done, as pre-registered.** `a_b` = 2 was **not viable** (seed
1 went extinct); `a_b` = 1 was viable but left **vacant space rare** (fill failure 3.65%, bar 5%; occupancy 0.994).
The runner's overall label reads "vacant space rare at these levels"; the per-level reasons above are the precise
record. The level choice was written before `h` was reported. The code was reviewed by Codex (gpt-6.2-sol, medium)
before the run; the review found a test that did not force the pool it claimed to (global arm) and three
input-validation issues, all fixed before the run, but the fixes were not re-reviewed.

| Level | Seed | Final occupancy | Window occupancy | Fill failure | Failed fills age-blocked | Outcome (level) |
| --- | --- | --- | --- | --- | --- | --- |
| `a_b` = 2 | 0 | 0.962 | 0.961 | 19.1% | 98% (this seed) | not viable (pooled: occupancy 0.480, fill failure 86%) |
| `a_b` = 2 | 1 | 0 (extinct at step 171) | 0 | 100% | – | |
| `a_b` = 1 | 0 | 0.990 | 0.995 | 3.6% | 94% | vacant space rare (pooled: occupancy 0.994, fill failure 3.65%) |
| `a_b` = 1 | 1 | 0.993 | 0.994 | 3.7% | 94% | |

Test arm only (b/c 6, local settlement), 6000 steps, counts over payoff states after 1000-5999 updates. The per-seed
rows and the start-up trajectories below were looked at after the selection.

**Recorded after the selection (not used in it).** Final `h`: 0.59 (`a_b` = 2, seed 0), 0.55 and 0.55 (`a_b` = 1).
Births per occupant-step by age class at `a_b` = 1: adults 0.12, age-1 juveniles 0.23 (per juvenile-step; age-0
occupants cannot breed); mean parent age 2.6 (`a_b` = 1) and 3.0 (`a_b` = 2). Empty neighbours per empty site
(of 4): 0.11 at `a_b` = 1, 0.36 in the surviving `a_b` = 2 run (scattered rather than clustered vacancies).

**Start-up (descriptive, rerun of the same seeds after the selection; `data/r7_pilot_startup.txt`).** At `a_b` = 2
all founders start at age 0 and cannot breed in the first two updates, while the base death probability without care
is 0.5: occupancy fell to about 0.25-0.27 by step 2, oscillated, and reached about 0.06-0.10 by step 100 in both seeds. Seed 1 went
extinct at step 171; seed 0 recovered (0.84 by step 500, about 0.95-0.97 from step 1000 on) and then kept a fill
failure of 19%.

**What this shows (at these settings).**

- **The pre-registered pilot failed at both levels**, for different reasons: extinction at `a_b` = 2, too few
  vacancies at `a_b` = 1.
- **Exploratory (looked at after the selection, two seeds, not a test):** the `a_b` = 2 extinction came after an
  early low-occupancy phase that was observed when all founders started at age 0; this is consistent with, but does
  not establish, a start-up bottleneck. In the surviving `a_b` = 2 run (seed 0), 19% of fills failed and about 98% of
  those failed fills were age-blocked, more vacant space than in any earlier step. Whether `a_b` = 2 would be viable and leave vacant space with founders that can breed from the start was not
  tested.
- At `a_b` = 1, failed fills were about 3.7%, compared with 1.4% in the separate D-E batch (the screen's toy
  estimate was 2.7% under independence); this remained below the 5% bar.
- Final `h` in these test-arm runs (0.55-0.59) was lower than D-E's 0.90 (separate batch, 20 seeds); with two seeds and
  no control arm this is descriptive only.

**Predictions made before the data.** `a_b` = 2 viable: 85% (not viable). Vacant space at `a_b` = 2: 50% (yes, but
not viable); at `a_b` = 1: 15% (no). Pilot passes at some level: 52% (no).

**Next:** decided with the user. One candidate suggested by the exploratory start-up look: the same step with founders
that start as adults (age `a_b`), pre-registered as a new step.

## Step R7b pilot: juveniles cannot breed, with adult founders (run 2026-11-20, code 2c34727, pre-registration 6d79213)

**Result: not viable; the R7b main run was not done, as pre-registered.** Both pilot seeds (20 and 21, not looked
at before) went extinct, at updates 376 and 193. The decision was written before `h` was reported. The code was
reviewed by Codex (gpt-6.2-sol, medium) before the run; the review found a completeness gap (short-window runs
accepted) and that an incomplete pilot would still write `h`, both fixed before the run, but the fixes were not
re-reviewed.

| Seed | Occupancy after update 10 / 50 / 100 / 500 | First empty update | Outcome |
| --- | --- | --- | --- |
| 20 | 0.55 / 0.31 / 0.11 / 0 | 376 | extinct |
| 21 | 0.59 / 0.18 / 0.09 / 0 | 193 | extinct |

Test arm B6-local (b/c 6, local settlement, `a_b` = 2, founders at age 2), 6000 steps.

**What this shows (at these settings).**

- **In this two-seed pilot, adult founders did not meet the `a_b` = 2 viability criterion.** The pre-registered
  screen showed only that the first update's fills succeed (as tested); occupancy then declined across the sampled
  checkpoints through update 100, as in R7 (about 0.06-0.10 by update 100 there, 0.09-0.11 here), and both runs died out.
- **The exploratory reading of R7 is not supported:** sampled occupancy kept falling well beyond the first two
  updates, and under these settings removing the initial breeding pause did not prevent extinction in either pilot
  seed. R7's single surviving seed should therefore be treated cautiously, as one trajectory from a stochastic early
  decline. Why the population declines at `a_b` = 2 was not tested; one untested hypothesis is that, while helping is
  still rare, few occupants survive to age 2 (base death 0.5 per update without care).

**Predictions made before the data.** Pilot viable: 80% (no). Vacant space: 75% (vacant, but not viable). Pilot
passes: 65% (no).

**Next:** decided with the user. This was the fifth attempt at the empty-space rung (R5a, R5b skipped, R6, R7, R7b);
the proposal recorded before this run was to stop this route here and change the structure of replacement instead.

## Step R8 Stage S: demographic screen for parent-driven births (run 2026-11-20, code ad4005a, pre-registration 852cd06)

**Result: complete; point chosen, `d0` = 0.2, `g_rep` = 0.5** (the highest passing `d0`, then the lower `g_rep`, as
pre-registered). Two of six grid points passed: at both, populations with `h` fixed at 0 and at 0.6 persisted in both
seeds with window occupancy between 0.50 and 0.95. The code was reviewed by Codex (gpt-6.2-sol, medium) before the run;
the review found that truncated runs could pass the completeness check and that the choice was written before the run
record, both fixed before the run, but the fixes were not re-reviewed. Stage M has not been built or run.

| `d0` | `g_rep` | Window occupancy, `h` = 0 (seeds 50, 51) | Window occupancy, `h` = 0.6 (seeds 50, 51) | Point |
| --- | --- | --- | --- | --- |
| 0.1 | 0.5 | 0.989, 0.989 | 0.929, 0.929 | fails (`h` = 0 above 0.95) |
| 0.1 | 0.7 | 0.575, 0.578 | 0.729, 0.728 | passes |
| **0.2** | **0.5** | **0.769, 0.770** | **0.948, 0.948** | **passes, chosen** |
| 0.2 | 0.7 | extinct (updates 81, 74) | 0.699, 0.697 | fails |
| 0.3 | 0.5 | extinct (updates 133, 134) | 0.951, 0.951 | fails |
| 0.3 | 0.7 | extinct (updates 33, 23) | 0.662, 0.662 | fails |

Fixed traits, no mutation, local births, energy split, no birth cost, 3000 updates; window = states after 1000-2999
completed updates.

**At the chosen point (descriptive, both seeds alike).**

| `h` | Births per occupant-update | Vacancies left unfilled after births | Claims per targeted site | Mean death probability | Starvation share of deaths | Mean `G` at payoff | Occupancy after updates 10 / 50 / 100 / 500 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.20 | 60% | 1.2 | 0.20 | 0 | 0.47 | 0.91-0.95 / 0.73-0.81 / 0.75-0.77 / 0.73-0.79 |
| 0.6 | 0.07 | 44% | 1.4 | 0.07 | 5.5% | 0.58 | 1.00 / 0.93-0.95 / 0.93-0.95 / 0.93-0.95 |

**What this shows (at these settings).**

- **At the chosen point, the parent-driven birth rule left substantial vacant space**: 44-60% of sites vacant after the
  deaths stayed empty after the births, and window occupancy was 0.77 (`h` = 0) and 0.95 (`h` = 0.6), against at least
  0.996 in every earlier rung where the population persisted.
- **Care was associated with higher density here.** With `h` = 0.6, occupancy was about 0.18 higher than with
  `h` = 0, and the mean death probability lower (0.07 against 0.20; care lowers death by the model's rule). At the
  tested points one grid step higher (`d0` 0.3, or `g_rep` 0.7 at `d0` 0.2), populations without care went extinct
  while populations with care persisted; there, care was associated with persistence itself. The chosen point is next to that region (one step up in either parameter), so the Stage M result
  should be read with this in mind.
- `h` = 0.6 at the chosen point sits just below the upper occupancy bound (0.948 against 0.95); Stage M will show
  whether higher helping crosses it (the vacancy label also uses fill failure, which was 44% here).
- The screen covers two homogeneous populations; it does not show that rare helpers can invade, nor that the
  control, global or attempt-2 arms are viable.

**Prediction made before the data.** Stage S finds a passing point: 50% (yes).

**Next:** Stage M (care test, 8 arms × 20 seeds at `d0` = 0.2, `g_rep` = 0.5), pre-registered, to be built and run
after the user's go.

## Step R8 Stage M: the care test with parent-driven births (run 2026-11-20, code 5d3aa9c, pre-registration 852cd06)

**Verdict: neither attempt met; both local failure** (test arm 0/20 in each attempt). Per the hard stop agreed in
advance, the empty-site rung is closed and the next step is a write-up of R1-R4 and the empty-site attempts. The code
was reviewed by Codex (gpt-6.2-sol, medium) before the run; the review found that an all-extinct test arm would crash
the harvest label, plus three validation gaps, all fixed before the run, but the fixes were not re-reviewed. At the
Stage-S point `d0` = 0.2, `g_rep` = 0.5; 8 arms × 20 seeds per attempt, 6000 updates; both attempts complete.

| Attempt | Test U6-local | Control UN6-local | Below maintained | H2 (global dispersal) | Income activation | Vacancy label (test arm, pooled) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 (energy split, no birth cost) | 0/20 | 0/20 | 0/20 (all 20 extinct) | not met: 0/20, neighbour corr. 0.001 | active (0.151) | vacant space present (fill failure 7.4%, occupancy 0.993) |
| 2 (free endowment 0.75, `c_b` 0.5) | 0/20 | 0/20 | 0/20 (19 of 20 extinct) | **met: 20/20**, neighbour corr. −0.007 | active (0.150) | vacant space rare (fill failure 0.8%, occupancy 0.999) |

**Per arm (descriptive; means over 20 seeds).**

| Arm | Successes | Mean final `h` | Mean `h` at 2000 / 6000 | Window occupancy | Fill failure | Death prob. | Starvation share of deaths | Neighbour `h` corr. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| U6-local | 0 | 0.36 | 0.35 / 0.36 | 0.993 | 7.4% | 0.085 | 0.1% | 0.45 |
| UN6-local | 0 | 0.09 | 0.09 / 0.09 | 0.989 | 10% | 0.097 | 0 | 0.40 |
| U3 / U12 / U24-local | 0 / 0 / 0 | 0.35 / 0.35 / 0.38 | – | 0.973-0.999 | 1.4-19% | 0.05-0.11 | <0.1% | 0.46-0.47 |
| U6-global | 0 | 0.31 | 0.31 / 0.31 | 1.000 | 0.3% | 0.090 | 0 | 0.00 |
| U12-global | 0 | 0.45 | 0.44 / 0.45 | 1.000 | 0.0% | 0.061 | 0.5% | 0.00 |
| U2-6-local | 0 | 0.35 | 0.35 / 0.35 | 0.999 | 0.8% | 0.084 | 7.7% | 0.50 |
| U2-N6-local | 0 | 0.09 | 0.09 / 0.09 | 0.999 | 0.7% | 0.098 | 0.3% | 0.45 |
| U2-3 / U2-12 / U2-24-local | 0 / 0 / 4 | 0.32 / 0.42 / 0.60 | – | 0.997-1.000 | 0.3-2.3% | 0.05-0.12 | 6-12% | 0.48-0.56 |
| **U2-6-global** | **20** | **0.99** | 0.99 / 0.99 | 0.999 | 0.7% | 0.014 | 87% | −0.01 |
| U2-12-global | 20 | 0.99 | 0.99 / 0.99 | 1.000 | 0.1% | 0.007 | 92% | 0.00 |

Below arms (common start `h` 0.9, `B` 0.05): attempt 1 all 20 extinct, attempt 2 19 of 20 extinct.

**What this shows (at these settings).**

- **The primary U6-local care test did not reach the endpoint in either attempt.** Across the local own-young arms,
  mean `h` rose from the rare start (0.05) to about 0.32-0.42 by update 2000 and then stayed there, except U2-24-local
  (0.60; 4/20 successes); help to young neighbours stayed near 0.09. So own-young care was
  higher than the control, but at an intermediate level below the 0.60 endpoint.
- **In attempt 2, own-young care spread to near fixation under global dispersal (0.99, 20/20 at b/c 6 and 12) but not
  with local births (0.35).** This is the reverse of the earlier rungs' pattern of local ≥ global. The contrast is
  consistent with kin competition (Taylor 1992), but this was not measured: local parent-driven births may increase
  competition among nearby relatives for vacancies, potentially offsetting the benefit of helping. Other differences
  between local and global births remain possible explanations. In attempt 1 (energy split) the global arm stayed at
  0.31, so the pattern also differs with the birth economics.
- **Vacancies:** with the energy split, the test arm kept 7.4% of needed fills empty at occupancy 0.993 (lower density
  and more vacancies were seen at fixed traits in Stage S); with the free endowment they were rare again (0.8%).
- **Care and density (descriptive).** The control arms had low helping (`h` about 0.09), mean juvenile `S` about 0.43
  and a mean death probability of about 0.10, and kept about 0.99 occupancy, far above Stage S's 0.77 at fixed `h` = 0;
  this association does not establish that care caused the density difference. The below arms (high helping at a tiny
  benefit) went extinct.

**Predictions made before the data.** Met in attempt 1: 35% (no). H2 met: 40% (not met in attempt 1, met in attempt
2). Vacant space present in the test arm: 85% (yes in attempt 1, rare in attempt 2).

**Disposition (hard stop):** neither attempt met; the empty-site rung is closed. Next: a write-up of R1-R4 and the
empty-site attempts (R5a-R8), decided with the user, not another variant.
