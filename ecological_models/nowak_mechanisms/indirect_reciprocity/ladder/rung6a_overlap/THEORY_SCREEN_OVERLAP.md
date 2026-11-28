# Rung 6a theory screen: overlapping generations (2026-11-28, calculation only)

**The smallest ecological step.** On rung 5c's met setting (C2: private views, mutation 0.001, empathy p = 0.75),
only a share r of the population is replaced each generation; the rest survive with their strategy. Views still
reset every generation (memory across generations is a later, separate step). `theory.py`; check: r = 1 reproduces
rung 5c's mean-field dynamics exactly.

| Share replaced per generation r | Cooperators at gen 500 / gens 1,501-2,000 | Final ALLC / DISC / ALLD | Shuffled (late) | Finite-time cliff μ |
| --- | --- | --- | --- | --- |
| 1 (rung 5c C2) | 0.986 / 0.986 | 0.095 / 0.891 / 0.014 | 0.014 | 0.0039 |
| 0.5 | 0.986 / 0.986 | 0.095 / 0.891 / 0.014 | 0.014 | 0.0039 |
| 0.2 | 0.981 / 0.986 | 0.096 / 0.891 / 0.014 | 0.014 | 0.0040 |

**Reading.** In the mean field, partial replacement only rescales time: the equilibrium and the cliff are unchanged.
In a finite population it also changes drift and the number of births within a fixed horizon. **Design trap:** with r
= 0.5 and rung 5a's 2,000-generation horizon, each run would contain half the births, so there would be less time for
the late erosion that caused every earlier failure, and a pass could come from the shorter effective horizon alone.
A fair step keeps the number of births equal: r = 0.5 over 4,000 generations, endpoints at generation 1,000 and the
mean over generations 3,001-4,000 (the same births as rung 5c's generation 500 and window 1,501-2,000).

**Proposed rung 6a (not agreed):** rung 5c C2 exactly, plus r = 0.5, horizon and endpoints rescaled as above, fresh
seeds, rung 5a's pass rule, hard stop one step. As before, the screen does not predict the simulated pass rate.
