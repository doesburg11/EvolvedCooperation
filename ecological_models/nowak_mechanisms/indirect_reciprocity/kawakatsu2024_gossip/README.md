# Kawakatsu, Kessinger and Plotkin (2024): gossip as an external check

**Status (2026-11-27): set up; no pre-registration yet, no run.**

**Why.** The indirect-reciprocity ladder (`../ladder/`) ended at rung 5a: under private, disagreeing views, simple
standing kept cooperation in 45/100 runs (bar 80). A separate follow-up added opinion-copying gossip to that model and
was not met (44/100; `../ladder/rung5b/`). Kawakatsu, Kessinger and Plotkin (2024) report that the same kind of
gossip (an individual adopts another's view of a third) can sustain cooperation under private assessment. This check
runs the authors' own code unchanged on their own settings, with criteria fixed in advance, to see whether their
result reproduces, and then, if it does, which differences from the ladder's model decide whether gossip helps.

**Authors' code.** <https://github.com/tkessinger/NeutralGossip>, commit `9d894a79a63f5276817ec2ca3c82a39d107fc376`
(2024-01-11). The repository has no license file, so the code is not copied here: it is cloned and run unchanged in
`~/simulation_results/kawakatsu2024_gossip/NeutralGossip/`. This directory holds only our pre-registration, analysis
and results. Julia 1.13.4 (juliaup, per-user).

**Paper.** Kawakatsu, M., Kessinger, T. A., and Plotkin, J. B. (2024). *A mechanistic model of gossip, reputations,
and cooperation*. PNAS. Preprint: <https://arxiv.org/abs/2312.10821>.

**Next.** Read the paper's main claims and figures, then draft a pre-registration (claims to check, settings,
criteria, hard stop) for agreement before any run.
