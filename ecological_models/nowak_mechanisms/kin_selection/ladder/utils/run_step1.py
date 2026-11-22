#!/usr/bin/env python3
"""Revised-ladder step 1: overlapping generations (README pre-registration ad9c75c).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_step1
"""
from __future__ import annotations

import contextlib
import io
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_step1")

from ..config.ladder_config import (
    DATA_DIR, SEEDS, STEP1_ALPHA, STEP1_ATTEMPTS, STEP1_MAX_GLOBAL_CORR, STEP1_SUSTAINED_LAST,
    SUCCESS_FINAL_MEAN_TRAIT, WORKERS, run_config, step1_arms,
)
from ..ladder_model import make_engine
from .analysis import check_seeds, classify_step1, neighbour_correlation, successes
from .run_steps01 import edge_pairs, write_csv


def corr_steps(steps):
    return list(range(1000, steps + 1, 1000))       # registered: every 1000 steps


def run_one(job):
    arm, mech, updates, seed, steps = job
    mech = dict(mech)
    eng = make_engine(run_config(seed, updates, steps), replacement=mech.pop("replacement"),
                      death=mech.pop("death"), **mech)
    ei, ej = edge_pairs(eng)
    cs = corr_steps(steps)
    traj, corr, surv = [], [], []
    with contextlib.redirect_stdout(io.StringIO()):
        while eng.step_index < steps:
            eng.step()
            t = eng.step_index
            surv.append(float(eng.last_survivors.mean()))
            if t % 50 == 0:
                traj.append(float(np.mean(eng.h)))
            if t in cs:
                corr.append(neighbour_correlation(eng.h, ei, ej))
    final = float(np.mean(eng.h))
    n_last = STEP1_SUSTAINED_LAST // 50 + 1          # samples at steps-1000, ..., steps inclusive
    return {"arm": arm, "seed": seed, "final_mean_trait": final, "success": int(final >= SUCCESS_FINAL_MEAN_TRAIT),
            "sustained_success": int(all(x >= SUCCESS_FINAL_MEAN_TRAIT for x in traj[-n_last:])),
            "survival_fraction": float(np.mean(surv)), "traj_every_50": traj, "neighbour_h_corr": corr}


def summarize(v, steps):
    return {"successes": successes(v), "sustained_successes": int(sum(r["sustained_success"] for r in v)),
            "mean_final_h": float(np.mean([r["final_mean_trait"] for r in v])),
            "survival_fraction": float(np.mean([r["survival_fraction"] for r in v])),
            "mean_h_every_50": [float(np.mean([r["traj_every_50"][t] for r in v])) for t in range(len(v[0]["traj_every_50"]))],
            "corr_steps": corr_steps(steps),
            "neighbour_h_corr": [float(np.nanmean([r["neighbour_h_corr"][t] for r in v])) for t in range(len(corr_steps(steps)))]}


def main():
    out = Path(DATA_DIR)
    verdict, all_rows = {}, []
    with Pool(WORKERS) as pool:
        for attempt in (1, 2):
            steps = STEP1_ATTEMPTS[attempt]["steps"]
            arms_cfg = step1_arms(attempt)
            rows = pool.map(run_one, [(a, m, u, s, steps) for a, (m, u) in arms_cfg.items() for s in SEEDS])
            all_rows += rows
            arms = {a: [r for r in rows if r["arm"] == a] for a in arms_cfg}
            for v in arms.values():
                check_seeds(v, SEEDS)
            names = list(arms_cfg)
            local, glob, below = names[0], names[1], names[2]
            # manipulation check: global arm's neighbour-h correlation over samples at steps >= 1000, mean over runs
            # any undefined sample correlation makes the mean undefined, and the control then counts as invalid
            gcorr = float(np.mean([np.mean(r["neighbour_h_corr"]) for r in arms[glob]]))
            res = classify_step1(arms[local], arms[glob], arms[below], gcorr, STEP1_ALPHA, STEP1_MAX_GLOBAL_CORR)
            res.update(STEP1_ATTEMPTS[attempt])
            res["descriptive"] = {a: summarize(v, steps) for a, v in arms.items()}
            verdict[f"attempt{attempt}"] = res
            print(f"attempt {attempt}:", res["class"], flush=True)
            if res["met"]:
                break
    verdict["step1_met"] = any(v["met"] for v in verdict.values() if isinstance(v, dict))
    write_csv(out / "step1_runs.csv", all_rows)
    (out / "step1_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "descriptive"} if isinstance(v, dict) else v)
                      for k, v in verdict.items()}, indent=1))


if __name__ == "__main__":
    main()
