#!/usr/bin/env python3
"""Step K0: costly-helping base (README pre-registration 9e81fb5).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_k0
"""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_k0")

from ..config.ladder_config import (
    DATA_DIR, K0_ALPHA, K0_DEATH, K0_STEPS, SEEDS, STEP1_MAX_GLOBAL_CORR, WORKERS, k0_arms, k0_roles,
)
from .analysis import check_seeds, classify_step1
from .run_step1 import run_one, summarize
from .run_steps01 import write_csv

ATTEMPT2_TRIGGERS = {"local failure", "comparison failed"}   # control invalid: stop and discuss instead


def main():
    out = Path(DATA_DIR)
    verdict, all_rows = {}, []
    with Pool(WORKERS) as pool:
        for attempt in (1, 2):
            arms_cfg = k0_arms(attempt)
            rows = pool.map(run_one, [(a, m, u, s, K0_STEPS) for a, (m, u) in arms_cfg.items() for s in SEEDS])
            all_rows += rows
            arms = {a: [r for r in rows if r["arm"] == a] for a in arms_cfg}
            for v in arms.values():
                check_seeds(v, SEEDS)
            test, glob, below = k0_roles(attempt)
            # manipulation check as in step 1: mean over runs of each run's mean correlation (steps 1000-6000);
            # any undefined sample makes it undefined and the control invalid
            gcorr = float(np.mean([np.mean(r["neighbour_h_corr"]) for r in arms[glob]]))
            res = classify_step1(arms[test], arms[glob], arms[below], gcorr, K0_ALPHA, STEP1_MAX_GLOBAL_CORR)
            res.update({"test_arm": test, "global_arm": glob, "below_arm": below, "death": K0_DEATH,
                        "steps": K0_STEPS, "exclude_focal": attempt == 2})
            res["descriptive"] = {a: summarize(v, K0_STEPS) for a, v in arms.items()}
            verdict[f"attempt{attempt}"] = res
            print(f"attempt {attempt}:", res["class"], flush=True)
            if res["class"] not in ATTEMPT2_TRIGGERS:
                break
    verdict["k0_met"] = any(v["met"] for v in verdict.values() if isinstance(v, dict))
    write_csv(out / "k0_runs.csv", all_rows)
    (out / "k0_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "descriptive"} if isinstance(v, dict) else v)
                      for k, v in verdict.items()}, indent=1))


if __name__ == "__main__":
    main()
