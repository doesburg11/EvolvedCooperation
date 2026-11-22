#!/usr/bin/env python3
"""Random-colour experiment: Experiment 104 with the colour-descent link intact vs broken (rules: README).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_random_colour
Writes data/random_colour/runs.csv, lineage.csv and summary.json.
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
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_random_colour")

from ..config.ethnocentrism_config import (
    DATA_DIR, RANDOM_COLOUR_BASE, RANDOM_COLOUR_CONDITIONS, RANDOM_COLOUR_DIR, RANDOM_COLOUR_SEEDS, RC_ALPHA,
    RC_MANIP_MAX_MEAN_ABS_GAP, RC_MANIP_MAX_MEAN_GAP, RC_MIN_DROP, WORKERS, run_config,
)
from ..ethnocentrism_model import Ethnocentrism

ETHNO = "cd-percent"          # NetLogo reporter: cooperate with same colour, defect against different = ethnocentric
DESCRIBE_REPORTERS = ["cc-percent", "cd-percent", "dc-percent", "dd-percent", "last100coop-percent",
                      "last100meetown-percent"]
DESCRIBE_LINEAGE = ["population", "n_founders_alive", "frac_pairs_same_colour", "colour_fidelity",
                    *[f"{g}_{k}" for g in ("same", "diff", "all") for k in
                      ("n_pairs", "frac_same_founder", "gen_dist_median", "tmrca_median", "r_reg_cs", "r_reg_cd")]]


def one(job: tuple[str, int]) -> dict:
    cond, seed = job
    cfg = {**run_config(RANDOM_COLOUR_BASE), **RANDOM_COLOUR_CONDITIONS[cond]}
    return {"condition": cond, "seed": seed, **Ethnocentrism(cfg, seed).run()}


def clean(x):
    """JSON-safe: NaN/inf -> None, numpy scalars -> Python."""
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(x) else None
    if isinstance(x, np.integer):
        return int(x)
    return x


def stats_of(values: list[float]) -> dict[str, float]:
    a = np.array(values, dtype=float)
    ok = a[np.isfinite(a)]
    return {"mean": float(ok.mean()) if ok.size else math.nan, "min": float(ok.min()) if ok.size else math.nan,
            "max": float(ok.max()) if ok.size else math.nan, "n_nan": int(a.size - ok.size)}


def judge(ethno_inh: np.ndarray, ethno_rnd: np.ndarray, manip_gaps: np.ndarray, n_expected: int,
          baseline_ok: bool = True) -> dict:
    """Pre-registered verdict. Every undefined or unexpected input gives an 'invalid' verdict (fails closed)."""
    out: dict = {"n_inherited": int(ethno_inh.size), "n_random": int(ethno_rnd.size), "baseline_ok": baseline_ok}
    gap = float(np.mean(manip_gaps)) if manip_gaps.size else math.nan       # a NaN seed makes it NaN
    abs_gap = float(np.mean(np.abs(manip_gaps))) if manip_gaps.size else math.nan
    manip_ok = (manip_gaps.size == n_expected and math.isfinite(gap) and abs(gap) < RC_MANIP_MAX_MEAN_GAP
                and abs_gap < RC_MANIP_MAX_MEAN_ABS_GAP)
    out.update(manipulation_gap_mean=gap, manipulation_abs_gap_mean=abs_gap, manipulation_ok=manip_ok)
    data_ok = (ethno_inh.size == n_expected and ethno_rnd.size == n_expected
               and np.isfinite(ethno_inh).all() and np.isfinite(ethno_rnd).all()
               and (np.ptp(ethno_inh) > 0 or np.ptp(ethno_rnd) > 0))       # Welch needs a nonzero standard error
    drop = float(ethno_inh.mean() - ethno_rnd.mean()) if data_ok else math.nan
    p = float(stats.ttest_ind(ethno_inh, ethno_rnd, equal_var=False).pvalue) if data_ok else math.nan
    out.update(ethno_drop=drop, ethno_p=p)
    if not baseline_ok:
        verdict = "invalid: inherited arm does not replay the committed port run"
    elif not data_ok or not math.isfinite(p):
        verdict = "invalid: endpoint undefined or wrong number of runs"
    elif not manip_ok:
        verdict = "invalid: manipulation check failed"
    else:
        verdict = "H1 met" if (drop >= RC_MIN_DROP - 1e-9 and p < RC_ALPHA) else "H1 not met"   # 1e-9: float tolerance
    out.update(H1_met=verdict == "H1 met", verdict=verdict)
    return out


def baseline_matches(inherited: list[dict], port_csv: Path) -> bool:
    """The inherited arm must reproduce the committed Experiment-104 port run exactly (all reporters, all seeds)."""
    if not port_csv.exists():
        return False
    rows = [r for r in csv.DictReader(open(port_csv)) if r["experiment"] == RANDOM_COLOUR_BASE]
    ref = {int(r["seed"]): r for r in rows}
    if len(ref) != len(rows) or sorted(ref) != sorted(r["seed"] for r in inherited):   # duplicate or missing seeds
        return False
    for r in inherited:
        row = ref[r["seed"]]
        if int(row["population"]) != r["population"] or int(row["births_total"]) != r["births_total"]:
            return False
        ref_keys = set(row) - {"experiment", "seed", "population", "births_total"}
        if ref_keys != set(r["reporters"]):                                 # same reporter set, none omitted
            return False
        if any(float(row[k]) != v for k, v in r["reporters"].items()):     # CSV floats round-trip exactly
            return False
    return True


def main() -> None:
    out_dir = Path(RANDOM_COLOUR_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(c, s) for c in RANDOM_COLOUR_CONDITIONS for s in RANDOM_COLOUR_SEEDS[c]]
    with Pool(WORKERS) as pool:
        res = pool.map(one, jobs, chunksize=1)

    keys = list(res[0]["reporters"])
    with open(out_dir / "runs.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["condition", "seed", "population", "births_total", *keys])
        for r in res:
            w.writerow([r["condition"], r["seed"], r["population"], r["births_total"], *[r["reporters"][k] for k in keys]])
    lkeys = sorted({k for r in res for s in r["lineage"] for k in s})
    with open(out_dir / "lineage.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["condition", "seed", *lkeys])
        for r in res:
            for s in r["lineage"]:
                w.writerow([r["condition"], r["seed"], *[s.get(k, "") for k in lkeys]])

    by = {c: [r for r in res if r["condition"] == c] for c in RANDOM_COLOUR_CONDITIONS}
    fin = {c: [r["lineage"][-1] for r in rs] for c, rs in by.items()}
    ethno = {c: np.array([r["reporters"][ETHNO] for r in rs], dtype=float) for c, rs in by.items()}
    gaps = np.array([s["same_frac_same_founder"] - s["diff_frac_same_founder"] for s in fin["random"]], dtype=float)
    base_ok = baseline_matches(by["inherited"], Path(DATA_DIR) / "runs.csv")
    summary: dict = judge(ethno["inherited"], ethno["random"], gaps, len(RANDOM_COLOUR_SEEDS["random"]), base_ok)
    summary["manipulation_per_seed"] = [
        {"seed": r["seed"], "gap": g, "same_n_pairs": s["same_n_pairs"], "diff_n_pairs": s["diff_n_pairs"]}
        for r, s, g in zip(by["random"], fin["random"], gaps)]
    summary["describe"] = {c: {**{k: stats_of([r["reporters"][k] for r in by[c]]) for k in DESCRIBE_REPORTERS},
                               **{k: stats_of([s[k] for s in fin[c]]) for k in DESCRIBE_LINEAGE}}
                           for c in RANDOM_COLOUR_CONDITIONS}
    summary = clean(summary)
    json.dump(summary, open(out_dir / "summary.json", "w"), indent=1, allow_nan=False)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("describe", "manipulation_per_seed")}, indent=1))
    for c, d in summary["describe"].items():
        print(c)
        for k, v in d.items():
            fmt = lambda x: "  nan" if x is None else f"{x:.3f}"
            print(f"  {k:26} mean {fmt(v['mean']):>8}  range {fmt(v['min'])}..{fmt(v['max'])}  nan {v['n_nan']}")


if __name__ == "__main__":
    main()
