#!/usr/bin/env python3
"""Ladder step 0d: local versus global-competitor replacement (README pre-registration 697928d).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_step0d
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_step0d")

from ..config.ladder_config import (
    CAL_PAIR_SEED, CAL_RANDOM_PAIRS, DATA_DIR, SAMPLE_STEPS_0D, SEEDS, STEP0D_ARMS, STEPS_0C,
    SUCCESS_FINAL_MEAN_TRAIT, SUSTAINED_FROM, WORKERS, run_config,
)
from ..ladder_model import make_engine
from .analysis import check_seeds, neighbour_correlation, score_t0d, successes
from .run_steps01 import edge_pairs, random_pairs, write_csv


def run_one(job):
    arm, mech, updates, seed = job
    mech = dict(mech)
    replacement = mech.pop("replacement", "local")
    eng = make_engine(run_config(seed, updates, STEPS_0C), replacement=replacement, **mech)
    ei, ej = edge_pairs(eng)
    ri, rj = random_pairs(eng, CAL_RANDOM_PAIRS, CAL_PAIR_SEED)
    traj, corr, label_c = [], [], []
    with contextlib.redirect_stdout(io.StringIO()):
        while eng.step_index < STEPS_0C:
            eng.step()
            t = eng.step_index
            if t % 50 == 0:
                traj.append(float(np.mean(eng.h)))
            if t in SAMPLE_STEPS_0D:
                corr.append(neighbour_correlation(eng.h, ei, ej))
                lab = eng.lineage
                label_c.append(float((lab[ei] == lab[ej]).mean() - (lab[ri] == lab[rj]).mean()))
    final = float(np.mean(eng.h))
    sustained_idx = [i for i, t in enumerate(range(50, STEPS_0C + 1, 50)) if t >= SUSTAINED_FROM]
    return {"arm": arm, "seed": seed, "final_mean_trait": final, "success": int(final >= SUCCESS_FINAL_MEAN_TRAIT),
            "sustained_success": int(all(traj[i] >= SUCCESS_FINAL_MEAN_TRAIT for i in sustained_idx)),
            "final_identity_count": int(np.unique(eng.lineage).size), "traj_every_50": traj,
            "neighbour_h_corr": corr, "label_contrast": label_c}


def main():
    out = Path(DATA_DIR)
    with Pool(WORKERS) as pool:
        rows = pool.map(run_one, [(a, m, u, s) for a, (m, u) in STEP0D_ARMS.items() for s in SEEDS])
    arms = {a: [r for r in rows if r["arm"] == a] for a in STEP0D_ARMS}
    for v in arms.values():
        check_seeds(v, SEEDS)
    # pre-registered: V-local must equal the step-0c H-nobias runs
    with open(out / "step0c_runs.csv") as f:
        ref = {int(r["seed"]): float(r["final_mean_trait"]) for r in csv.DictReader(f) if r["arm"] == "H-nobias"}
    mism = [r["seed"] for r in arms["V-local"] if ref.get(r["seed"]) != r["final_mean_trait"]]
    if mism:
        raise SystemExit(f"V-local differs from step-0c H-nobias for seeds {mism}: code error, step stops")
    verdict = {"T0d": score_t0d(arms["V-local"], arms["V-global"], arms["V-below"]), "V_local_matches_H_nobias": True}
    verdict["descriptive"] = {a: {
        "successes": successes(v), "sustained_successes": int(sum(r["sustained_success"] for r in v)),
        "mean_final_h": float(np.mean([r["final_mean_trait"] for r in v])),
        "final_h_by_seed": [round(r["final_mean_trait"], 3) for r in sorted(v, key=lambda r: r["seed"])],
        "mean_h_every_50": [float(np.mean([r["traj_every_50"][t] for r in v])) for t in range(len(v[0]["traj_every_50"]))],
        "neighbour_h_corr_at_500s": [float(np.nanmean([r["neighbour_h_corr"][t] for r in v])) for t in range(len(SAMPLE_STEPS_0D))],
        "label_contrast_at_500s": [float(np.mean([r["label_contrast"][t] for r in v])) for t in range(len(SAMPLE_STEPS_0D))],
    } for a, v in arms.items()}
    write_csv(out / "step0d_runs.csv", rows)
    (out / "step0d_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps(verdict["T0d"], indent=1))


if __name__ == "__main__":
    main()
