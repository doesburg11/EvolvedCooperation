# Results: group selection threshold model (Traulsen and Nowak multilevel selection)

## Stage 0 (2026-11-26)

- Tests: 6 passed (`./.conda/bin/python -m pytest threshold_models/group_selection_traulsen_nowak`; system Python 3
  and numba 0.68.1 in a cloud session).
- Benchmark (20,000 runs of each cell and 20,000 neutral runs per setting, timing only, outcomes discarded):
  0.39 ms per run per cell, 0.69 ms per neutral run; projected registered run 1.03 h on 2 cores, under the 5-hour
  budget → **`R` = 1,000,000, `R₀` = 2,000,000**, as registered.
