# Rebase theory screen (2026-11-26)

After rung 4a's hard stop the user chose (2026-11-26) to rebase the ladder with more margin and retry rung 4a. This
screen (`theory.py`, output `theory_output.txt`; calculation only, no simulation) scans the two base parameters held
fixed so far, the probability q that a discriminator consults a reputation and the benefit b (c = 1), on the full
rung-3b stack (o = 0.5, e = 0.1, a = 0.02). It reuses the mean-field records of `rung3b/theory.py` and
`rung4a/theory.py` (records do not depend on b) and recomputes payoffs. The current-base row reproduces the
registered screens (boundary 0.824; at rung 4a's start ALLD out-earns DISC for 11 generations and grows for 25, peak
0.101; with 30% ALLC, ALLD takes over).

| Base | Rung-3b boundary | Rung 4a start (10/80/10): ALLD out-earns DISC / grows | 30% ALLC: ALLD out-earns DISC / grows, peak, final ALLD | Shuffled gen 100, ALLD |
| --- | --- | --- | --- | --- |
| q 0.6, b 3 (current) | 0.824 | 11 / 25 generations | 500 / 500, 1.00, 1.00 | 0.990 |
| q 0.7, b 3 | 0.707 | 0 / 0 | 92 / 107, 0.169, 0.000 | 0.986 |
| **q 0.8, b 3** | **0.608** | **0 / 0** | **0 / 6, 0.1004, 0.000** | 0.980 |
| q 0.6, b 4 | 0.647 | 0 / 0 | 4 / 19, 0.1024, 0.000 | 0.988 |
| q 0.9, b 3 | 0.523 | 0 / 0 | 0 / 0, 0.100, 0.000 | 0.972 |

Boundaries at q = 0.8 for each rung's stack (rung-3b theory with the other errors off): rung 2 0.481, rung 2b
0.526, rung 3a 0.585, rung 3b 0.608 (at q = 0.6: 0.66, 0.715, 0.794, 0.824). From a 90% start all reach DISC ≈ 1.0 by
generation 500 in the recursion; the shuffled control falls to DISC 0.01-0.02 by generation 100.

**Choice: q = 0.8, b/c = 3 kept.** A one-parameter change. It restores more two-strategy margin than rung 2 had on the
current base (0.608 against 0.66), removes the early phase in which defectors out-earn discriminators or grow at
rung 4a's start, and keeps the shuffled control failing. A Codex review (gpt-6.1-sol, medium) found the reuse of the
records and payoffs valid, confirmed the current-base row, and preferred q = 0.8 over b = 4: raising q strengthens
reputation-conditioned discrimination directly, while raising b also raises what unconditional cooperators give to
defectors (b = 4 lets ALLD grow for 19 generations from a 30% ALLC start, q = 0.8 for 6).

**Limits.** The recursion omits encounter noise and Wright-Fisher sampling; it gives no probability that a stochastic
run is lost. Rung 4a's attempt 2 (5% ALLC) had no deterministic defector-favoured phase and still kept cooperation in
only 11/20 runs. The two-strategy boundary is not the three-strategy basin boundary. The choice is outcome-informed
(made after rung 4a failed twice) and opens a new branch; the earlier rung results on q = 0.6 stand unchanged.
