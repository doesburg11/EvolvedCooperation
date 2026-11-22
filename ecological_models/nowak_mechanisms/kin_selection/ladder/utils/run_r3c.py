#!/usr/bin/env python3
"""Step R3c: births need a minimum condition; sites can stay empty (README pre-registration da353fd). Same runner as R1/R2.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r3c
"""
from __future__ import annotations

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r3c")

from ..config.ladder_config import r3c_arms, r3c_roles
from . import run_r1


def main():
    run_r1.main(arms_fn=r3c_arms, roles_fn=r3c_roles, name="r3c")


if __name__ == "__main__":
    main()
