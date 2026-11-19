#!/usr/bin/env python3
"""Step R3a: care and its cost carry over as condition (README pre-registration 415b90c). Same runner as R1/R2.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r3a
"""
from __future__ import annotations

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r3a")

from ..config.ladder_config import r3a_arms, r3a_roles
from . import run_r1


def main():
    run_r1.main(arms_fn=r3a_arms, roles_fn=r3a_roles, name="r3a")


if __name__ == "__main__":
    main()
