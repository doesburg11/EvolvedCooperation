# Kawakatsu, Kessinger and Plotkin (2024) external check: results (2026-11-27)

Pre-registration: `PREREGISTRATION.md` (agreed 2026-11-27 before the driver was written). Driver commit `d177167`,
authors' code `9d894a7` run unchanged, Julia 1.13.4, N = 100, b/c = 5, u_a = u_e = 0.02, ω = 1, no mutation,
50 runs per cell, cap 200,000 generations. **No run in any stage was censored**, so every censoring bound collapses to
the observed share. Each stage ran once (attempt 1), with no repair. Summaries: `results_stage1.json` to
`results_stage3.json`; raw records in `~/simulation_results/kawakatsu2024_gossip/runs/`.

## Stage 1, stern judging (600 runs): meets the registered replication criteria

| Start (ALLC/ALLD/DISC) | τ = 0 | τ = 0.4 | Predicted at τ = 0.4 |
| --- | --- | --- | --- |
| 0.6/0.3/0.1 | ALLD 50 | ALLD 50 | ALLD |
| 0.4/0.4/0.2 | ALLD 50 | ALLD 47, DISC 3 | ALLD |
| 0.2/0.5/0.3 | ALLD 50 | ALLD 48, DISC 2 | ALLD |
| 0.6/0.1/0.3 | ALLD 50 | **DISC 47**, ALLD 3 | DISC |
| 0.4/0.2/0.4 | ALLD 50 | **DISC 43**, ALLD 7 | DISC |
| 0.2/0.3/0.5 | ALLD 50 | **DISC 44**, ALLD 6 | DISC |

- **C1 holds:** 300/300 runs fix ALLD without gossip (bar 90%).
- **C2 holds** for each DISC-basin start: 47, 43, 44 of 50 fix DISC (bar 26), against 0 at τ = 0 (bar: 20 more).
- Mean realised cooperation rate in the three DISC-basin cells: 0.52-0.63 with gossip, 0.13-0.24 without.
- Every one of the twelve cells went to its predicted majority outcome.

## Stage 2, start 0.2/0.3/0.5, stern judging (250 runs): C3 holds

| τ | 0.05 | 0.10 | 0.15 | 0.20 | 0.30 |
| --- | --- | --- | --- | --- | --- |
| DISC fixed / 50 | 0 | 0 | 1 | 7 | 35 |
| Predicted | ALLD | ALLD | ALLD | ALLD | DISC |

C3: the DISC share rises by 0.70 from τ = 0.05 to τ = 0.30 (bar 0.30). The response is graded rather than a step between the
deterministic predictions at τ = 0.28 (ALLD) and τ = 0.30 (DISC): 14% of runs reach DISC at τ = 0.20, 70% at τ = 0.30.

## Stage 3, simple standing (600 runs): descriptive bridge

| Start | τ | ALLC | ALLD | DISC | ALLD extinct | Mean cooperation |
| --- | --- | --- | --- | --- | --- | --- |
| 0.6/0.3/0.1 | 0 | 0 | 50 | 0 | 0 | 0.22 |
| | 0.4 | 1 | 49 | 0 | 1 | 0.24 |
| 0.4/0.4/0.2 | 0 | 10 | 40 | 0 | 10 | 0.34 |
| | 0.4 | 19 | 25 | 6 | 25 | 0.55 |
| 0.2/0.5/0.3 | 0 | 29 | 20 | 1 | 30 | 0.62 |
| | 0.4 | 16 | 13 | 21 | 37 | 0.68 |
| 0.6/0.1/0.3 | 0 | 45 | 5 | 0 | 45 | 0.91 |
| | 0.4 | 40 | 1 | 9 | 49 | 0.94 |
| 0.4/0.2/0.4 | 0 | 50 | 0 | 0 | 50 | 0.95 |
| | 0.4 | 39 | 0 | 11 | 50 | 0.95 |
| 0.2/0.3/0.5 | 0 | 50 | 0 | 0 | 50 | 0.95 |
| | 0.4 | 34 | 0 | 16 | 50 | 0.93 |

- Against the recorded predictions: start 0.6/0.3/0.1 goes to ALLD as predicted. Start 0.4/0.4/0.2, predicted ALLD,
  goes to ALLD in 40/50 without gossip and in 25/50 with it. The four starts predicted to reach an ALLC-DISC mixture
  lose ALLD in 175/200 runs without gossip (30, 45, 50, 50) and 186/200 with it. The mixture then drifts to fixation
  (no mutation), mostly to ALLC.
- Without gossip, simple standing with private views produced mean cooperation of 0.91-0.95 from the three
  mixture-basin starts 0.6/0.1/0.3, 0.4/0.2/0.4 and 0.2/0.3/0.5. In these samples, gossip was associated with more
  DISC endpoints from the four mixture-basin starts (57/200 vs 1/200), while ALLD extinction rose from 175/200 to 186/200.
- My registered prediction for Stage 3 (ALLD goes extinct in most runs from the four mixture starts without gossip)
  was supported: ALLD went extinct in 175/200 runs.

## Interpretation (hedged)

- The authors' code met the registered operational replication criteria for the headline setting. Under stern
  judging with private views, all 300 runs without gossip fixed ALLD; with gossip at τ = 0.4, the three
  preregistered DISC-basin starts mostly fixed DISC (43-47/50). This reproduces the tested headline operational
  result. It says nothing about whether the model describes real gossip.
- The bridge comparison does not explain the ladder's rung-5a null by private views alone. In the authors' model,
  under simple standing with private views and no gossip, ALLD went extinct in 175/200 runs from the four
  mixture-basin starts. At rung 5a, the same norm with private views met both registered maintenance endpoints in
  45/100 runs. The two models differ in several ways
  at once: population updating (Wright-Fisher vs one Fermi pair), mutation (0.001 vs none), observation rate,
  starting conditions, and the success measure (fixation here, a cooperation threshold there). This check cannot say
  which difference matters. The ladder's own pre-registration measured a different quantity, so the numbers are not
  directly comparable.
- Hard stop reached: each stage ran once, and Stage 3 was the last registered step. No further settings were run.
