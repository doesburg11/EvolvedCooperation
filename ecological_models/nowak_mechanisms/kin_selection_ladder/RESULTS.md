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
