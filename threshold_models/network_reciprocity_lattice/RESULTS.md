# Results: network reciprocity threshold model (lattice, death-birth)

## Stage 0 (2026-11-26, code at the commit that adds this section)

- Tests: 8 passed (`./.conda/bin/python -m pytest threshold_models/network_reciprocity_lattice`; run with system
  Python 3 and numba 0.68.1 in a cloud session). One test was corrected before Stage 0: its own choice of `w` = 0.5
  made fitness negative; the runner now refuses any cell where `1 − w − w·c·k` ≤ 0 (all registered cells pass).
- Neutral check (`w` = 0, 200,000 runs per graph): graph V `ρ̂·N` = 1.004 [0.947, 1.062], graph M 1.006
  [0.949, 1.064]; both contain 1 → pass.
- Benchmark (20,000 runs per cell, timing only, counts discarded): 48-84 µs per run; projected registered run at
  `R` = 1,000,000: 0.10 h on 2 cores, under the 5-hour budget → **`R` = 1,000,000** as registered.
