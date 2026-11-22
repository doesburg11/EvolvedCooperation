#!/usr/bin/env python3
"""Revised-ladder step 2a: ages, adult-only helping (pre-registration 3db3b5e). Same runner as steps 1b/1c.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_step2a
"""
from __future__ import annotations

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_step2a")

from ..config.ladder_config import step2a_arms
from . import run_step1b

if __name__ == "__main__":
    run_step1b.main(step2a_arms, "step2a")
