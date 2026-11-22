#!/usr/bin/env python3
"""Step R2: care only for young offspring (README pre-registration aa957de). Same runner as R1.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r2
"""
from __future__ import annotations

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r2")

from ..config.ladder_config import r2_arms, r2_roles
from . import run_r1


def main():
    run_r1.main(arms_fn=r2_arms, roles_fn=r2_roles, name="r2")


if __name__ == "__main__":
    main()
