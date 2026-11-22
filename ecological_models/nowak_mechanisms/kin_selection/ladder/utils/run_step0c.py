#!/usr/bin/env python3
"""Ladder step 0c, the half-step (README pre-registration 1252e8f). Writes data/step0c_runs.csv, data/step0c_verdict.json.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_step0c
"""
from __future__ import annotations

import contextlib
import io
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_step0c")

from ..config.ladder_config import (
    DATA_DIR, FISHER_ALPHA_ATTEMPT2, SEEDS, STEP0C_ARMS, STEP0C_ATTEMPT2_ARMS, STEPS_0C, SUCCESS_FINAL_MEAN_TRAIT,
    WORKERS, run_config,
)
from ..ladder_model import make_engine
from .analysis import check_seeds, score_t0c, successes
from .run_steps01 import write_csv


def run_one(job):
    arm, mech, updates, seed = job
    eng = make_engine(run_config(seed, updates, STEPS_0C), **mech)
    with contextlib.redirect_stdout(io.StringIO()):
        payload = eng.run()
    final = float(payload["final_mean_trait"])
    traj = [payload["history"][t]["mean_trait"] for t in range(50, STEPS_0C, 50)] + [final]
    return {"arm": arm, "seed": seed, "final_mean_trait": final, "success": int(final >= SUCCESS_FINAL_MEAN_TRAIT),
            "final_identity_count": int(payload["final_identity_count"]), "traj_every_50": traj}


def grouped(rows, arms):
    out = {a: [r for r in rows if r["arm"] == a] for a in arms}
    for v in out.values():
        check_seeds(v, SEEDS)
    return out


def describe(v):
    return {"successes": successes(v), "mean_final_h": float(np.mean([r["final_mean_trait"] for r in v])),
            "mean_final_labels": float(np.mean([r["final_identity_count"] for r in v])),
            "mean_h_every_50": [float(np.mean([r["traj_every_50"][t] for r in v])) for t in range(len(v[0]["traj_every_50"]))]}


def main():
    out = Path(DATA_DIR)
    with Pool(WORKERS) as pool:
        rows = pool.map(run_one, [(a, m, u, s) for a, (m, u) in STEP0C_ARMS.items() for s in SEEDS])
        arms = grouped(rows, STEP0C_ARMS)
        verdict = {"attempt1": score_t0c(arms["H-kin"], arms["H-nobias"], arms["H-below"], 0.05)}
        print("T0c attempt 1:", verdict["attempt1"]["met"], flush=True)
        if not verdict["attempt1"]["met"]:
            rows2 = pool.map(run_one, [(a, m, u, s) for a, (m, u) in STEP0C_ATTEMPT2_ARMS.items() for s in SEEDS])
            rows += rows2
            arms.update(grouped(rows2, STEP0C_ATTEMPT2_ARMS))
            verdict["attempt2"] = score_t0c(arms["H2-kin"], arms["H-nobias"], arms["H2-below"], FISHER_ALPHA_ATTEMPT2)
            print("T0c attempt 2:", verdict["attempt2"]["met"], flush=True)
    verdict["T0c_met"] = bool(verdict["attempt1"]["met"] or verdict.get("attempt2", {}).get("met", False))
    verdict["descriptive"] = {a: describe(v) for a, v in arms.items()}
    write_csv(out / "step0c_runs.csv", rows)
    (out / "step0c_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: v for k, v in verdict.items() if k != "descriptive"}, indent=1))


if __name__ == "__main__":
    main()
