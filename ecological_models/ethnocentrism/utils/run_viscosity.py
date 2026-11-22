#!/usr/bin/env python3
"""Lower-viscosity experiment: Experiment 104 x offspring dispersal x colour rule (rules: README).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_viscosity
Writes data/viscosity/runs.csv, lineage.csv and summary.json.
"""
from __future__ import annotations

import csv
import json
import math
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy import stats

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_viscosity")

from ..config.ethnocentrism_config import (
    DATA_DIR, DISPERSAL_LEVELS, RANDOM_COLOUR_BASE, RANDOM_COLOUR_DIR, VISC_ALPHA, VISC_DIR, VISC_H1_MIN_DROP,
    VISC_H2_MIN_DIFF, VISC_MIN_FOUNDER_DROP, VISC_N_SEEDS, VISC_SEED_OFFSET, WORKERS, run_config,
)
from ..ethnocentrism_model import Ethnocentrism
from .run_random_colour import clean, stats_of

COOP = "last100coop-percent"
DESCRIBE_REPORTERS = ["cc-percent", "cd-percent", "dc-percent", "dd-percent", COOP, "last100meetown-percent"]
DESCRIBE_LINEAGE = ["population", "n_founders_alive", "frac_pairs_same_colour", "colour_fidelity",
                    "all_frac_same_founder", "all_tmrca_median", "all_r_reg_cs", "all_r_reg_cd",
                    "same_frac_same_founder", "diff_frac_same_founder"]
CONDITIONS = list(VISC_SEED_OFFSET)


def seeds(cond: str, level: int) -> list[int]:
    return [10000 * level + VISC_SEED_OFFSET[cond] + i for i in range(VISC_N_SEEDS)]


def one(job: tuple[str, int, int]) -> dict:
    cond, level, seed = job
    cfg = {**run_config(RANDOM_COLOUR_BASE), "colour_inheritance": cond, "dispersal": DISPERSAL_LEVELS[level]}
    return {"condition": cond, "level": level, "dispersal": DISPERSAL_LEVELS[level], "seed": seed,
            **Ethnocentrism(cfg, seed).run()}


def compare(a: np.ndarray, b: np.ndarray, min_diff: float, n: int) -> dict:
    """Observed mean(a) - mean(b) >= min_diff and two-sided Welch p < VISC_ALPHA. Undefined input -> valid False."""
    valid = a.size == n and b.size == n and bool(np.isfinite(a).all() and np.isfinite(b).all())
    se = math.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size) if valid and n > 1 else math.nan
    valid = valid and math.isfinite(se) and se > 1e-12                   # Welch needs a standard error above rounding (registered)
    diff = float(a.mean() - b.mean()) if valid else math.nan
    p = float(stats.ttest_ind(a, b, equal_var=False).pvalue) if valid else math.nan
    valid = valid and math.isfinite(p)
    return {"diff": diff, "p": p, "valid": valid,
            "criterion_met": bool(valid and diff >= min_diff - 1e-9 and p < VISC_ALPHA)}   # 1e-9: float tolerance


def founder_drop(a: np.ndarray, b: np.ndarray, n: int) -> dict:
    """Manipulation check (no test): n finite values per cell and mean(a) - mean(b) >= VISC_MIN_FOUNDER_DROP."""
    valid = a.size == n and b.size == n and bool(np.isfinite(a).all() and np.isfinite(b).all())
    drop = float(a.mean() - b.mean()) if valid else math.nan
    return {"drop": drop, "valid": valid, "ok": bool(valid and drop >= VISC_MIN_FOUNDER_DROP - 1e-9)}


def coop_of(r: dict) -> float:
    """Cooperation share; undefined (NaN) when there were no meetings in the last 100 ticks or the key is missing."""
    if r.get("last100_meetings", 0) <= 0:
        return math.nan
    return float(r.get("reporters", {}).get(COOP, math.nan))


def nan_if_none(v) -> float:
    return math.nan if v is None else float(v)


def founder_of(r: dict) -> float:
    lin = r.get("lineage") or [{}]
    v = lin[-1].get("all_frac_same_founder", math.nan)
    return math.nan if v is None else float(v)


def replays(runs: list[dict], ref_csv: Path, col: str, val: str) -> bool:
    """Runs reproduce the reference rows (ref_csv rows with col == val) exactly: same seeds, all reporters."""
    if not ref_csv.exists():
        return False
    rows = [r for r in csv.DictReader(open(ref_csv)) if r[col] == val]
    ref = {int(r["seed"]): r for r in rows}
    if len(ref) != len(rows) or sorted(ref) != sorted(r["seed"] for r in runs):
        return False
    for r in runs:
        row = ref[r["seed"]]
        if set(row) - {col, "seed", "population", "births_total"} != set(r["reporters"]):
            return False
        if int(row["population"]) != r["population"] or int(row["births_total"]) != r["births_total"]:
            return False
        if any(float(row[k]) != v for k, v in r["reporters"].items()):
            return False
    return True


def judge(cell: dict, replay_ok: bool) -> dict:
    """Pre-registered verdicts from cell[(cond, level)] -> list of run dicts (level 0 = d 0, last = d 1)."""
    lo, hi = 0, len(DISPERSAL_LEVELS) - 1
    arr = lambda cond, lev, f: np.array([f(r) for r in cell.get((cond, lev), [])], dtype=float)
    out: dict = {"replay_ok": replay_ok}
    manip = {c: founder_drop(arr(c, lo, founder_of), arr(c, hi, founder_of), VISC_N_SEEDS) for c in CONDITIONS}
    manip_ok = all(m["ok"] for m in manip.values())
    out.update(manipulation=manip, manipulation_ok=manip_ok)
    h1 = compare(arr("random", lo, coop_of), arr("random", hi, coop_of), VISC_H1_MIN_DROP, VISC_N_SEEDS)
    h2 = compare(arr("inherited", hi, coop_of), arr("random", hi, coop_of), VISC_H2_MIN_DIFF, VISC_N_SEEDS)
    for name, h in (("H1", h1), ("H2", h2)):
        if not replay_ok:
            v = "invalid: d=0 runs do not replay the committed runs"
        elif not manip_ok:
            v = "invalid: manipulation check failed"
        elif not h["valid"]:
            v = "invalid: endpoint undefined or wrong number of runs"
        else:
            v = f"{name} met" if h["criterion_met"] else f"{name} not met"
        out[name] = {**h, "verdict": v, "met": v == f"{name} met"}
    return out


def main() -> None:
    out_dir = Path(VISC_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(c, k, s) for c in CONDITIONS for k in range(len(DISPERSAL_LEVELS)) for s in seeds(c, k)]
    with Pool(WORKERS) as pool:
        res = pool.map(one, jobs, chunksize=1)

    keys = list(res[0]["reporters"])
    with open(out_dir / "runs.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["condition", "dispersal", "seed", "population", "births_total", *keys])
        for r in res:
            w.writerow([r["condition"], r["dispersal"], r["seed"], r["population"], r["births_total"],
                        *[r["reporters"][k] for k in keys]])
    lkeys = sorted({k for r in res for s in r["lineage"] for k in s})
    with open(out_dir / "lineage.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["condition", "dispersal", "seed", *lkeys])
        for r in res:
            for s in r["lineage"]:
                w.writerow([r["condition"], r["dispersal"], r["seed"], *[s.get(k, "") for k in lkeys]])

    cell = {(c, k): [r for r in res if r["condition"] == c and r["level"] == k]
            for c in CONDITIONS for k in range(len(DISPERSAL_LEVELS))}
    replay_ok = (replays(cell[("inherited", 0)], Path(DATA_DIR) / "runs.csv", "experiment", RANDOM_COLOUR_BASE)
                 and replays(cell[("random", 0)], Path(RANDOM_COLOUR_DIR) / "runs.csv", "condition", "random"))
    summary = judge(cell, replay_ok)
    summary["describe"] = {
        f"{c} d={DISPERSAL_LEVELS[k]}": {
            **{m: stats_of([coop_of(r) if m == COOP else r.get("reporters", {}).get(m, math.nan) for r in rs])
               for m in DESCRIBE_REPORTERS},                                   # same missing-data rule as the verdict
            **{m: stats_of([nan_if_none((r.get("lineage") or [{}])[-1].get(m)) for r in rs]) for m in DESCRIBE_LINEAGE},
            "offspring_per_tick": stats_of([r["offspring_total"] / run_config(RANDOM_COLOUR_BASE)["ticks"] for r in rs]),
            "share_offspring_dispersed": stats_of([r["dispersed_total"] / max(r["offspring_total"], 1) for r in rs])}
        for (c, k), rs in cell.items()}
    summary = clean(summary)
    json.dump(summary, open(out_dir / "summary.json", "w"), indent=1, allow_nan=False)
    print(json.dumps({k: v for k, v in summary.items() if k != "describe"}, indent=1))
    show = ["cd-percent", "cc-percent", "dc-percent", "dd-percent", COOP, "population", "offspring_per_tick",
            "share_offspring_dispersed",
            "all_frac_same_founder", "all_r_reg_cs", "same_frac_same_founder", "diff_frac_same_founder"]
    print(f"{'cell':18}" + "".join(f"{m[:12]:>13}" for m in show))
    for name, d in summary["describe"].items():
        print(f"{name:18}" + "".join(f"{(d[m]['mean'] if d[m]['mean'] is not None else float('nan')):13.3f}"
                                     for m in show))


if __name__ == "__main__":
    main()
