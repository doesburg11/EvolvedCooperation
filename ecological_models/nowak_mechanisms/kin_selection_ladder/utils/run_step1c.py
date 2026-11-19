#!/usr/bin/env python3
"""Revised-ladder step 1c: survival selection with a globally normalized death lottery (pre-registration 5067eed).
Same runner as step 1b; only the arms (norm = "global") and the output names differ.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_step1c
"""
from __future__ import annotations

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_step1c")

from ..config.ladder_config import step1c_arms
from . import run_step1b

if __name__ == "__main__":
    run_step1b.main(step1c_arms, "step1c")
