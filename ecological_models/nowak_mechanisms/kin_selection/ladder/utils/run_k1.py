#!/usr/bin/env python3
"""Step K1: parental care on the costly-helping base (README pre-registration 3615065).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_k1
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
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_k1")

from ..config.ladder_config import (
    DATA_DIR, K0_STEPS, K1_DIAG_FROM, K1_MIN_TEST, SEEDS, STEP1_MAX_GLOBAL_CORR, SUCCESS_FINAL_MEAN_TRAIT, WORKERS,
    k1_arms, k1_roles, run_config,
)
from ..ladder_model import make_engine
from .analysis import check_seeds, fisher_greater, neighbour_correlation, successes
from .run_step1 import STEP1_SUSTAINED_LAST, corr_steps, summarize
from .run_steps01 import edge_pairs, write_csv

DIAG_KEYS = ("offspring_mean", "frac_no_offspring", "benefit_lost", "parent_offspring_corr")


def run_one(job):
    arm, mech, updates, seed, steps = job
    mech = dict(mech)
    eng = make_engine(run_config(seed, updates, steps), replacement=mech.pop("replacement"),
                      death=mech.pop("death"), **mech)
    ei, ej = edge_pairs(eng)
    cs = corr_steps(steps)
    parental = hasattr(eng, "last_diag")
    traj, corr, surv, diag = [], [], [], {k: [] for k in DIAG_KEYS}
    with contextlib.redirect_stdout(io.StringIO()):
        while eng.step_index < steps:
            start = eng.step_index
            eng.step()
            t = eng.step_index
            surv.append(float(eng.last_survivors.mean()))
            if parental and start >= K1_DIAG_FROM:        # payoff states after 1000, ..., 5999 updates
                for k in DIAG_KEYS:
                    diag[k].append(eng.last_diag[k])
            if t % 50 == 0:
                traj.append(float(np.mean(eng.h)))
            if t in cs:
                corr.append(neighbour_correlation(eng.h, ei, ej))
    final = float(np.mean(eng.h))
    n_last = STEP1_SUSTAINED_LAST // 50 + 1
    row = {"arm": arm, "seed": seed, "final_mean_trait": final, "success": int(final >= SUCCESS_FINAL_MEAN_TRAIT),
           "sustained_success": int(all(x >= SUCCESS_FINAL_MEAN_TRAIT for x in traj[-n_last:])),
           "survival_fraction": float(np.mean(surv)), "traj_every_50": traj, "neighbour_h_corr": corr}
    for k in DIAG_KEYS:
        v = np.asarray(diag[k], dtype=float)
        row[k] = float(np.nanmean(v)) if v.size and np.isfinite(v).any() else float("nan")
    return row


def classify_k1(test_rows, below_rows):
    t, b = successes(test_rows), successes(below_rows)
    cls = "local failure" if (t < K1_MIN_TEST or b > 2) else "met"
    return {"test": t, "below_maintained": b, "class": cls, "met": cls == "met"}


def score_h2(global_rows):
    corr = float(np.mean([np.mean(r["neighbour_h_corr"]) for r in global_rows]))
    s = successes(global_rows)
    if not (corr <= STEP1_MAX_GLOBAL_CORR):
        res = "not interpretable"
    else:
        res = "met" if s >= K1_MIN_TEST else "not met"
    return {"successes": s, "neighbour_corr": corr, "result": res}


def check_n6(rows, k0_csv: Path):
    """N6-local must reproduce K0's K6-local exactly (final mean h per seed)."""
    cols = ("final_mean_trait", "success", "sustained_success", "survival_fraction")
    with open(k0_csv) as f:
        ref = {int(r["seed"]): r for r in csv.DictReader(f) if r["arm"] == "K6-local"}
    bad = [r["seed"] for r in rows if any(str(r[c]) != ref[r["seed"]][c] for c in cols)]
    if bad or len(ref) != len(rows):
        raise RuntimeError(f"N6-local does not reproduce K6-local (seeds {bad}): code error, step stopped")


def main():
    out = Path(DATA_DIR)
    verdict, all_rows = {}, []
    with Pool(WORKERS) as pool:
        for attempt in (1, 2):
            arms_cfg = k1_arms(attempt)
            rows = pool.map(run_one, [(a, m, u, s, K0_STEPS) for a, (m, u) in arms_cfg.items() for s in SEEDS])
            all_rows += rows
            arms = {a: [r for r in rows if r["arm"] == a] for a in arms_cfg}
            for v in arms.values():
                check_seeds(v, SEEDS)
            if attempt == 1:
                check_n6(arms["N6-local"], out / "k0_runs.csv")
            test, below, glob = k1_roles(attempt)
            res = classify_k1(arms[test], arms[below])
            res["h2"] = score_h2(arms[glob])
            n6 = verdict.get("attempt1", {}).get("n6_successes") if attempt == 2 else successes(arms["N6-local"])
            res["n6_successes"] = n6
            res["fisher_p_vs_n6"] = fisher_greater(res["test"], len(arms[test]), n6, len(SEEDS))
            res.update({"test_arm": test, "below_arm": below, "global_arm": glob, "care": arms_cfg[test][0]["care"]})
            desc = {}
            for a, v in arms.items():
                d = summarize(v, K0_STEPS)
                for k in DIAG_KEYS:
                    vals = np.asarray([r[k] for r in v], dtype=float)
                    # hybrid arms redirect (not lose) the benefit of helpers without offspring
                    key = "benefit_redirected" if (k == "benefit_lost" and attempt == 2) else k
                    d[key] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
                desc[a] = d
            res["descriptive"] = desc
            verdict[f"attempt{attempt}"] = res
            print(f"attempt {attempt}:", res["class"], "H2:", res["h2"]["result"], flush=True)
            if res["class"] != "local failure":
                break
    verdict["k1_met"] = any(v["met"] for v in verdict.values() if isinstance(v, dict))
    write_csv(out / "k1_runs.csv", all_rows)
    (out / "k1_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "descriptive"} if isinstance(v, dict) else v)
                      for k, v in verdict.items()}, indent=1))


if __name__ == "__main__":
    main()
