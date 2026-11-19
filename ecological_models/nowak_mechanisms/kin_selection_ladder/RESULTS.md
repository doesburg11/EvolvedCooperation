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
