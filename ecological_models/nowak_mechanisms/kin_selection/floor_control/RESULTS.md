# Results: kin selection with a survival floor

## Step 0 (2026-11-19): registered stop, no main test

No-helper control (every `h` = 0, no mutation, no rare founders), seeds 0-19, 220 steps (`data/step0_runs.csv`,
`data/step0_result.json`). Runs persisting (population >= 100 at every step 181-220), of 20:

| Floor `f` | 0.05 | 0.1 | 0.15 | 0.2 | 0.3 | 0.4 |
| --- | --- | --- | --- | --- | --- | --- |
| K (kin rearing) | 0 | 0 | 0 | 0 | 0 | 0 |
| U (unrelated rearing) | 0 | 0 | 0 | 0 | 0 | 0 |

No floor qualified, so by the registered rule the test stops and the main test was not run.

**Diagnostic after the stop (not a registered test; K only, seeds 0-4, `f` beyond the registered grid).** Run
length (steps before extinction, of 220), final population, and mean juvenile survival per step:

| `f` | Steps survived | Final population | Juvenile survival |
| --- | --- | --- | --- |
| 0 | 86-100 | 0 in all 5 | 0.28-0.44 |
| 0.4 | 127-158 | 0 in all 5 | 0.60-0.67 |
| 0.6 | 220 | 6-34 | 0.79-0.82 |
| 0.8 | 220 | 43-265 | 0.94-0.96 |
| 0.9 | 220 | 7-299 | 1.0 |

The floor raises juvenile survival as designed (the code checks out). In this small diagnostic, no-helper
populations needed very high juvenile survival: at `f` = 0.8 (survival 0.94-0.96), two of five seeds ended below 100
(43 and 69). A floor that high would leave helper care little headroom (saturation is 0.9). The registered grid
found no qualifying floor up to 0.4, and the diagnostic suggests that higher floors would not give a useful
separation either; it does not rule out a different control design.

**What this means for "is kin selection established in the ecological model?"** Not established. The tested
controls do not separate the spread of the helping trait from care-dependent persistence: without helpers, the
tested floors did not keep populations alive, while small tested care efforts (0.07-0.15 per carer in
`../learning/`) did. The Moran kin-selection model, where the controls are clean, remains the
established result.

Not tested: why a fixed floor of 0.9 (juvenile survival 1.0) still let one seed crash, while a constant helper
effort of 0.07 persisted 40/40 in `../learning/`. Helper care differs from the floor in who receives
it and when (only juveniles with an able carer nearby), which may smooth the boom-and-crash at the population cap.
