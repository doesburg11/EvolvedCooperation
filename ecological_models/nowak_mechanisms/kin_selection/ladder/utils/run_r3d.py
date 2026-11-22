#!/usr/bin/env python3
"""Step R3d: starvation, occupants with W below sigma die (README pre-registration 1a5830a). Same runner as R1/R2.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r3d
"""
from __future__ import annotations

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r3d")

from ..config.ladder_config import r3d_arms, r3d_roles
from . import run_r1


def main():
    run_r1.main(arms_fn=r3d_arms, roles_fn=r3d_roles, name="r3d")


if __name__ == "__main__":
    main()
