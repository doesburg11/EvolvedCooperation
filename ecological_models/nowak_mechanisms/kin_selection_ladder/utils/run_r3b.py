#!/usr/bin/env python3
"""Step R3b: a realized birth costs the surviving parent condition (README pre-registration 4b81e7f). Same runner as R1/R2.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r3b
"""
from __future__ import annotations

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r3b")

from ..config.ladder_config import r3b_arms, r3b_roles
from . import run_r1


def main():
    run_r1.main(arms_fn=r3b_arms, roles_fn=r3b_roles, name="r3b")


if __name__ == "__main__":
    main()
