# Results: direct reciprocity threshold model (TFT against ALLD)

## Stage 0 (2026-11-26)

- Tests: 6 passed (`./.conda/bin/python -m pytest threshold_models/direct_reciprocity_tft`; run with system Python 3
  and numba 0.68.1 in a cloud session).
- Benchmark (500 one-generation runs per cell and start, 2 trajectory runs per cell; timing only, outcomes
  discarded): 135 ms of CPU per one-generation run of all 12 cells and both starts, 6.5 s per trajectory run of all
  cells; projected registered run 0.41 h on 2 cores, under the 5-hour budget → **20,000** one-generation runs per
  cell and start, as registered.
