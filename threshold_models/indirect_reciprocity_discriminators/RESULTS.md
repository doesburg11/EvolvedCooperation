# Results: indirect reciprocity threshold model (discriminators against ALLD)

## Stage 0 (2026-11-26)

- Tests: 5 passed (`./.conda/bin/python -m pytest threshold_models/indirect_reciprocity_discriminators`; system
  Python 3 and numba 0.68.1 in a cloud session), including encounter-by-encounter play on a small population
  against the closed-form payoffs.
- Benchmark (500 one-generation runs per cell and start, 2 trajectory runs per cell; timing only, outcomes
  discarded): projected registered run 0.02 h on 2 cores → **20,000** one-generation runs per cell and start, as
  registered.
