# Kawakatsu, Kessinger and Plotkin (2024): gossip as an external check

**Status (2026-11-27): done, hard stop reached.** The authors' code met the registered operational replication criteria for the headline setting (Stage 1 met: without gossip 300/300 runs fix ALLD under stern judging; with gossip τ = 0.4, 43-47/50 fix DISC from the three predicted starts; Stage 2 C3 held). Under simple standing without gossip, ALLD went extinct in 175/200 runs from the four predicted mixture-basin starts, and mean cooperation was 0.91-0.95 from starts 0.6/0.1/0.3, 0.4/0.2/0.4 and 0.2/0.3/0.5 (Stage 3). Details: `RESULTS.md`.

**Why.** The indirect-reciprocity ladder (`../ladder/`) ended at rung 5a: under private, disagreeing views, simple
standing met both registered maintenance endpoints in 45/100 runs (bar 80). A separate follow-up added opinion-copying gossip to that model and
was not met (both maintenance endpoints in 44/100 runs, registered comparison criterion failed; `../ladder/rung5b/`). Kawakatsu, Kessinger and Plotkin (2024) report that the same kind of
gossip (an individual adopts another's view of a third) can sustain cooperation under private assessment. This check
runs the authors' own code unchanged on their own settings, with criteria fixed in advance, to see whether their
result reproduces, and then, if it does, which differences from the ladder's model decide whether gossip helps.

**Authors' code.** <https://github.com/tkessinger/NeutralGossip>, commit `9d894a79a63f5276817ec2ca3c82a39d107fc376`
(2024-01-11). The repository has no license file, so the code is not copied here: it is cloned and run unchanged in
`~/simulation_results/kawakatsu2024_gossip/NeutralGossip/`. This directory holds only our pre-registration, analysis
and results. Julia 1.13.4 (juliaup, per-user).

**Paper.** Kawakatsu, M., Kessinger, T. A., and Plotkin, J. B. (2024). *A mechanistic model of gossip, reputations,
and cooperation*. PNAS. Preprint: <https://arxiv.org/abs/2312.10821>.

**Files.** `PREREGISTRATION.md`, `run_check.jl` (driver), `preflight.jl`, `run_stage1-3.jl`, `analyze.py`, `RESULTS.md`, `results_stage1-3.json`.
