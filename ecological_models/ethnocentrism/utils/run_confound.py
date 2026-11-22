#!/usr/bin/env python3
"""Confound-separating experiment: inherited vs uniform random vs skewed random colour (rules: README).

The skewed arm draws each child's colour independently of its parent, but from weights chosen so that about 80% of
meetings are with the own colour, as in the inherited arm. Run from the repo root:
  ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_confound
Writes data/confound/runs.csv, lineage.csv and summary.json.
"""
from __future__ import annotations

import csv
import json
import math
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_confound")

from ..config.ethnocentrism_config import (
    CF_ALPHA, CF_MEETOWN_RANGE, CF_MIN_DIFF, CONFOUND_ARMS, CONFOUND_DIR, CONFOUND_SEEDS, DATA_DIR,
    RANDOM_COLOUR_BASE, RANDOM_COLOUR_DIR, RC_MANIP_MAX_MEAN_ABS_GAP, RC_MANIP_MAX_MEAN_GAP, run_config, WORKERS,
)
from ..ethnocentrism_model import EMPTY, Ethnocentrism
from .run_random_colour import clean, stats_of
from .run_viscosity import compare as _compare, nan_if_none, replays

ETHNO, MEETOWN, COOP = "cd-percent", "last100meetown-percent", "last100coop-percent"
DESCRIBE_REPORTERS = ["cc-percent", "cd-percent", "dc-percent", "dd-percent", COOP, MEETOWN]
DESCRIBE_LINEAGE = ["population", "n_founders_alive", "frac_pairs_same_colour", "colour_fidelity",
                    *[f"{g}_{k}" for g in ("same", "diff", "all") for k in
                      ("n_pairs", "frac_same_founder", "frac_gen_le2", "tmrca_median", "r_reg_cs", "r_reg_cd")]]
EXPOSURE = ["exp_ethno_own", "exp_top_colour_own", "exp_other_colours_own", "top_colour_share"]
N = len(CONFOUND_SEEDS["inherited"])


def exposure(m: Ethnocentrism) -> dict[str, float]:
    """Final tick: share of occupied neighbours with the own colour, for ethnocentrics and by colour group."""
    occ = m.agent != EMPTY
    nb_occ = occ[m.nbr] & occ[:, None]
    same = nb_occ & (m.color[m.nbr] == m.color[:, None])
    def share(mask: np.ndarray) -> float:
        n = nb_occ[mask].sum()
        return float(same[mask].sum() / n) if n else math.nan
    counts = np.bincount(m.color[occ], minlength=m.cfg["n_colors"])
    top = int(np.argmax(counts))
    return {"exp_ethno_own": share(occ & m.cs & ~m.cd), "exp_top_colour_own": share(occ & (m.color == top)),
            "exp_other_colours_own": share(occ & (m.color != top)),
            "top_colour_share": float(counts[top] / counts.sum()) if counts.sum() else math.nan}


def one(job: tuple[str, int]) -> dict:
    arm, seed = job
    m = Ethnocentrism({**run_config(RANDOM_COLOUR_BASE), **CONFOUND_ARMS[arm]}, seed)
    return {"arm": arm, "seed": seed, **m.run(), "exposure": exposure(m)}


def compare(a: np.ndarray, b: np.ndarray) -> dict:
    """Same rule as the viscosity experiment, with this experiment's thresholds."""
    out = _compare(a, b, CF_MIN_DIFF, N)
    out["criterion_met"] = bool(out["valid"] and out["diff"] >= CF_MIN_DIFF - 1e-9 and out["p"] < CF_ALPHA)
    return out


MEETING_BASED = {MEETOWN, COOP}       # reporters whose denominator is the meeting count


def reporter(r: dict, key: str) -> float:
    """Reporter value; NaN if missing. Meeting-based reporters are NaN without a positive, finite meeting count."""
    if key in MEETING_BASED:
        n = r.get("last100_meetings")
        if n is None or not math.isfinite(n) or n <= 0:
            return math.nan
    return nan_if_none(r.get("reporters", {}).get(key))


def judge(arms: dict[str, list[dict]], replay_ok: bool) -> dict:
    get = lambda arm, f: np.array([f(r) for r in arms.get(arm, [])], dtype=float)
    out: dict = {"replay_ok": replay_ok}
    meetown = get("random_skewed", lambda r: reporter(r, MEETOWN))
    m1_val = float(meetown.mean()) if meetown.size == N and np.isfinite(meetown).all() else math.nan
    m1 = math.isfinite(m1_val) and CF_MEETOWN_RANGE[0] <= m1_val <= CF_MEETOWN_RANGE[1]
    gaps = get("random_skewed", lambda r: nan_if_none((r.get("lineage") or [{}])[-1].get("same_frac_same_founder"))
               - nan_if_none((r.get("lineage") or [{}])[-1].get("diff_frac_same_founder")))
    gap = float(gaps.mean()) if gaps.size == N else math.nan
    abs_gap = float(np.abs(gaps).mean()) if gaps.size == N else math.nan
    m2 = (math.isfinite(gap) and math.isfinite(abs_gap) and abs(gap) < RC_MANIP_MAX_MEAN_GAP
          and abs_gap < RC_MANIP_MAX_MEAN_ABS_GAP)
    out["manipulation"] = {"meetown_mean": m1_val, "meetown_ok": m1, "founder_gap_mean": gap,
                           "founder_abs_gap_mean": abs_gap, "founder_ok": m2}
    out["manipulation_ok"] = bool(m1 and m2)
    eth = lambda arm: get(arm, lambda r: reporter(r, ETHNO))
    tests = {"H1": compare(eth("inherited"), eth("random_skewed")),        # cue loss at matched meeting share
             "H2": compare(eth("random_skewed"), eth("random_uniform"))}   # meeting share, both without the cue
    for name, h in tests.items():
        if not replay_ok:
            v = "invalid: replay of committed runs failed"
        elif not out["manipulation_ok"]:
            v = "invalid: manipulation check failed"
        elif not h["valid"]:
            v = "invalid: endpoint undefined or wrong number of runs"
        else:
            v = f"{name} met" if h["criterion_met"] else f"{name} not met"
        out[name] = {**h, "verdict": v, "met": v == f"{name} met"}
    return out


def main() -> None:
    out_dir = Path(CONFOUND_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(a, s) for a in CONFOUND_ARMS for s in CONFOUND_SEEDS[a]]
    with Pool(WORKERS) as pool:
        res = pool.map(one, jobs, chunksize=1)

    keys = list(res[0]["reporters"])
    with open(out_dir / "runs.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["arm", "seed", "population", "births_total", *keys])
        for r in res:
            w.writerow([r["arm"], r["seed"], r["population"], r["births_total"], *[r["reporters"][k] for k in keys]])
    lkeys = sorted({k for r in res for s in r["lineage"] for k in s})
    with open(out_dir / "lineage.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["arm", "seed", *lkeys])
        for r in res:
            for s in r["lineage"]:
                w.writerow([r["arm"], r["seed"], *[s.get(k, "") for k in lkeys]])

    arms = {a: [r for r in res if r["arm"] == a] for a in CONFOUND_ARMS}
    replay_ok = (replays(arms["inherited"], Path(DATA_DIR) / "runs.csv", "experiment", RANDOM_COLOUR_BASE)
                 and replays(arms["random_uniform"], Path(RANDOM_COLOUR_DIR) / "runs.csv", "condition", "random"))
    summary = judge(arms, replay_ok)
    summary["describe"] = {a: {**{m: stats_of([reporter(r, m) for r in rs]) for m in DESCRIBE_REPORTERS},
                               **{m: stats_of([nan_if_none((r.get("lineage") or [{}])[-1].get(m)) for r in rs])
                                  for m in DESCRIBE_LINEAGE},
                               **{m: stats_of([nan_if_none(r.get("exposure", {}).get(m)) for r in rs]) for m in EXPOSURE}}
                           for a, rs in arms.items()}
    summary = clean(summary)
    json.dump(summary, open(out_dir / "summary.json", "w"), indent=1, allow_nan=False)
    print(json.dumps({k: v for k, v in summary.items() if k != "describe"}, indent=1))
    for a, d in summary["describe"].items():
        print(a)
        for k, v in d.items():
            f = lambda x: "  nan" if x is None else f"{x:.3f}"
            print(f"  {k:26} mean {f(v['mean']):>8}  range {f(v['min'])}..{f(v['max'])}  nan {v['n_nan']}")


if __name__ == "__main__":
    main()
