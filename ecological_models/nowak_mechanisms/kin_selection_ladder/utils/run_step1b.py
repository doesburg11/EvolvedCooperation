#!/usr/bin/env python3
"""Revised-ladder step 1b: selection on survival (README pre-registration a3a180e).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_step1b
"""
from __future__ import annotations

import contextlib
import io
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_step1b")

from ..config.ladder_config import (
    DATA_DIR, SEEDS, STEP1_ALPHA, STEP1_MAX_GLOBAL_CORR, STEP1_SUSTAINED_LAST, STEP1B_LAMBDA, STEP1B_STEPS,
    SUCCESS_FINAL_MEAN_TRAIT, WORKERS, run_config, step1b_arms,
)
from ..ladder_model import make_engine
from .analysis import check_seeds, classify_step1, neighbour_correlation
from .run_step1 import corr_steps, summarize
from .run_steps01 import edge_pairs, write_csv


def run_one(job):
    arm, mech, updates, seed, steps = job
    mech = dict(mech)
    eng = make_engine(run_config(seed, updates, steps), replacement=mech.pop("replacement"),
                      death=mech.pop("death"), lam=mech.pop("lam"), norm=mech.pop("norm", "local"), **mech)
    juv = []
    ei, ej = edge_pairs(eng)
    cs = corr_steps(steps)
    traj, corr, surv = [], [], []
    with contextlib.redirect_stdout(io.StringIO()):
        while eng.step_index < steps:
            eng.step()
            t = eng.step_index
            surv.append(float(eng.last_survivors.mean()))
            if hasattr(eng, "last_juvenile_fraction"):
                juv.append(eng.last_juvenile_fraction)
            if t % 50 == 0:
                traj.append(float(np.mean(eng.h)))
            if t in cs:
                corr.append(neighbour_correlation(eng.h, ei, ej))
    final = float(np.mean(eng.h))
    n_last = STEP1_SUSTAINED_LAST // 50 + 1
    return {"arm": arm, "seed": seed, "final_mean_trait": final, "success": int(final >= SUCCESS_FINAL_MEAN_TRAIT),
            "sustained_success": int(all(x >= SUCCESS_FINAL_MEAN_TRAIT for x in traj[-n_last:])),
            "survival_fraction": float(np.mean(surv)), "death_fraction": 1.0 - float(np.mean(surv)),
            **({"juvenile_fraction": float(np.mean(juv))} if juv else {}), "traj_every_50": traj, "neighbour_h_corr": corr}


def main(arms_fn=None, name="step1b"):
    arms_fn = arms_fn or step1b_arms
    out = Path(DATA_DIR)
    verdict, all_rows = {}, []
    with Pool(WORKERS) as pool:
        for attempt in (1, 2):
            arms_cfg = arms_fn(attempt)
            rows = pool.map(run_one, [(a, m, u, s, STEP1B_STEPS) for a, (m, u) in arms_cfg.items() for s in SEEDS])
            all_rows += rows
            arms = {a: [r for r in rows if r["arm"] == a] for a in arms_cfg}
            for v in arms.values():
                check_seeds(v, SEEDS)
            local, glob, below = list(arms_cfg)[:3]
            gcorr = float(np.mean([np.mean(r["neighbour_h_corr"]) for r in arms[glob]]))
            res = classify_step1(arms[local], arms[glob], arms[below], gcorr, STEP1_ALPHA, STEP1_MAX_GLOBAL_CORR)
            res["lam"] = arms_cfg[local][0]["lam"]                     # from the arm, not the 1b table
            res["descriptive"] = {a: {**summarize(v, STEP1B_STEPS),
                                      "death_fraction": float(np.mean([r["death_fraction"] for r in v])),
                                      **({"juvenile_fraction": float(np.mean([r["juvenile_fraction"] for r in v]))}
                                         if "juvenile_fraction" in v[0] else {})}
                                  for a, v in arms.items()}
            verdict[f"attempt{attempt}"] = res
            print(f"attempt {attempt}:", res["class"], flush=True)
            if res["met"]:
                break
    verdict[f"{name}_met"] = any(v["met"] for v in verdict.values() if isinstance(v, dict))
    write_csv(out / f"{name}_runs.csv", all_rows)
    (out / f"{name}_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "descriptive"} if isinstance(v, dict) else v)
                      for k, v in verdict.items()}, indent=1))


if __name__ == "__main__":
    main()
