#!/usr/bin/env python3
"""Step R4: income from a limited, renewable site resource (README pre-registration b0104c2). Same runner as R1/R2.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r4
"""
from __future__ import annotations

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_r4")

from ..config.ladder_config import r4_arms, r4_roles
from . import run_r1


def main():
    run_r1.main(arms_fn=r4_arms, roles_fn=r4_roles, name="r4")


if __name__ == "__main__":
    main()
