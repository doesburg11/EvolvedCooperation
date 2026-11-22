#!/usr/bin/env python3
"""Diagnostic DR4: why did helping rise under limited income? (README pre-registration 51821a1, labels 1010b9d).

Seven arms (D-F, D-G references; D-U85, D-U75 uniform cut; D-E lower endowment; D-Fcb0 / D-Gcb0 no birth costs),
seeds 0-19, 6000 steps. Decisions use d_X = numerator - 0.5 Delta with a seed-block bootstrap (same seeds in every
arm). Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_dr4
"""
from __future__ import annotations

import csv
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_dr4")

from ..config.ladder_config import (
    DATA_DIR, DR4_BOOT, DR4_BOOT_SEED, DR4_MIN_RISE, K0_STEPS, SEEDS, WORKERS, dr4_arms,
)
from . import run_r1
from .analysis import check_seeds

REFERENCES = {"D-F": ("r3d", "F6-local"), "D-G": ("r4", "G6-local")}
# share numerators: (arm, its reference); the rise is D-G minus D-F
PARTS = {"U85": ("D-U85", "D-F"), "U75": ("D-U75", "D-F"), "E": ("D-E", "D-F"), "cb0": ("D-Gcb0", "D-Fcb0")}
TRAJ_STEPS = (2000, 4000, 6000)
CLASS_KEYS = ("frac_ineligible", "frac_ineligible_low_h", "frac_ineligible_high_h", "frac_ineligible_recent_parents",
              "starve_rate_low_h", "starve_rate_high_h", "starve_rate_recent_parents", "starve_rate_juveniles",
              "starve_added_share", "S_mean", "D_mean", "G_mean", "G_juvenile", "G_parents", "occupancy",
              "frac_fill_emptied", "births_per_occupant", "mean_age")


def write_union_csv(path, rows):
    """Scalar columns of every row in first-seen order (Codex DR4 review: R3d and R4 rows have different fields)."""
    names = []
    for r in rows:
        names += [k for k, v in r.items() if not isinstance(v, list) and k not in names]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=names, restval="", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def same_float(a, b) -> bool:
    """Exact equality; two undefined values (NaN, or a JSON null) also match (a reproduced extinct run)."""
    a = float("nan") if a is None else float(a)
    b = float("nan") if b is None else float(b)
    return a == b or (np.isnan(a) and np.isnan(b))


def final_h(row) -> float:
    """Final mean h over occupied sites; an extinct run counts as 0 (pre-registered)."""
    return 0.0 if int(row["extinct"]) else float(row["final_mean_trait"])


def check_references(arms, data_dir) -> dict:
    """Validity: per seed, final_mean_trait and final_occupancy equal the stored rows exactly; the across-seed mean
    trajectory equals the stored mean_h_every_50 exactly (per-seed trajectories were not stored)."""
    out = {}
    for arm, (name, stored_arm) in REFERENCES.items():
        with open(Path(data_dir) / f"{name}_runs.csv") as f:
            stored = {int(r["seed"]): r for r in csv.DictReader(f) if r["arm"] == stored_arm}
        v = json.loads((Path(data_dir) / f"{name}_verdict.json").read_text())
        stored_traj = v["attempt1"]["descriptive"][stored_arm]["mean_h_every_50"]
        rows = sorted(arms[arm], key=lambda r: int(r["seed"]))
        mism = []
        for r in rows:
            s = stored.get(int(r["seed"]))
            if s is None:
                mism.append((int(r["seed"]), "missing"))
                continue
            for k in ("final_mean_trait", "final_occupancy"):
                if not same_float(s[k], r[k]):
                    mism.append((int(r["seed"]), k))
        traj = [float(np.mean([r["traj_every_50"][t] for r in rows])) for t in range(len(rows[0]["traj_every_50"]))]
        traj_ok = len(traj) == len(stored_traj) and all(same_float(a, b) for a, b in zip(traj, stored_traj))
        out[arm] = {"stored": f"{name}:{stored_arm}", "seeds_match": not mism and len(rows) == len(stored),
                    "mismatches": mism, "mean_traj_match": traj_ok}
    return out


def bootstrap(h: dict[str, np.ndarray], n_boot=DR4_BOOT, seed=DR4_BOOT_SEED) -> dict:
    """Seed-block bootstrap: one draw of seed indices per resample, used for every arm, numerator and Delta."""
    n = len(next(iter(h.values())))
    idx = np.random.default_rng(seed).integers(0, n, size=(n_boot, n))
    bm = {a: v[idx].mean(axis=1) for a, v in h.items()}
    pm = {a: float(v.mean()) for a, v in h.items()}
    delta, delta_b = pm["D-G"] - pm["D-F"], bm["D-G"] - bm["D-F"]
    res = {"delta": delta, "delta_ci": [float(x) for x in np.percentile(delta_b, [2.5, 97.5])], "parts": {}}
    for key, (arm, ref) in PARTS.items():
        num, num_b = pm[arm] - pm[ref], bm[arm] - bm[ref]
        d_b = num_b - 0.5 * delta_b
        lo, hi = (float(x) for x in np.percentile(d_b, [2.5, 97.5]))
        res["parts"][key] = {"arm": arm, "reference": ref, "numerator": num, "share": num / delta if delta else None,
                             "d": num - 0.5 * delta, "d_ci": [lo, hi], "reading": reading(key, lo, hi)}
    return res


def reading(key, lo, hi) -> str:
    base = ("accounts for most of the rise" if lo > 0 else "accounts for less than half" if hi < 0 else "unclear")
    if key in ("E", "cb0") and base != "unclear":
        base += " (not needed)" if lo > 0 else " (needed)"
    return base


def overall(parts) -> str:
    r = {k: v["reading"] for k, v in parts.items()}
    if all(x == "unclear" for x in r.values()):
        return "inconclusive"
    if (all(x != "unclear" for x in r.values())
            and all(r[k].startswith("accounts for less than half") for k in ("U85", "U75"))
            and all(r[k].startswith("accounts for most") for k in ("E", "cb0"))):
        return "unexplained by these parts"
    return "clear readings: " + "; ".join(f"{k}: {v}" for k, v in r.items() if v != "unclear")


def describe(rows) -> dict:
    hs = np.array([final_h(r) for r in rows])
    d = {"mean_final_h": float(hs.mean()), "sd_final_h": float(hs.std(ddof=1)), "final_h_per_seed": hs.tolist(),
         "successes": int(sum(r["success"] for r in rows)), "extinctions": int(sum(r["extinct"] for r in rows)),
         "final_occupancy": float(np.mean([r["final_occupancy"] for r in rows]))}
    for t in TRAJ_STEPS:
        i = t // 50 - 1
        d[f"mean_h_{t}"] = float(np.mean([0.0 if not np.isfinite(r["traj_every_50"][i]) else r["traj_every_50"][i]
                                          for r in rows]))
    for cls in ("low", "high"):
        b, n = sum(r[f"births_{cls}_h_sum"] for r in rows), sum(r[f"n_{cls}_h"] for r in rows)
        d[f"births_per_occ_step_{cls}_h"] = b / n if n else None
        d[f"occ_steps_{cls}_h"] = int(n)
    for k in CLASS_KEYS:
        vals = np.asarray([r.get(k, np.nan) for r in rows], dtype=float)
        d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
    dt, st = sum(r["deaths_total"] for r in rows), sum(r["starve_added_total"] for r in rows)
    d["starvation_activation"] = st / dt if dt else None
    return d


def main():
    out = Path(DATA_DIR)
    cfg = dr4_arms()
    with Pool(WORKERS) as pool:
        rows = pool.map(run_r1.run_one, [(a, m, u, s, K0_STEPS) for a, (m, u) in cfg.items() for s in SEEDS])
    arms = {a: [r for r in rows if r["arm"] == a] for a in cfg}
    for v in arms.values():
        check_seeds(v, SEEDS)
    write_union_csv(out / "dr4_runs.csv", rows)
    (out / "dr4_trajectories.json").write_text(json.dumps(run_r1.json_safe(
        {a: {int(r["seed"]): {"traj_every_50": r["traj_every_50"], "occ_every_50": r["occ_every_50"]} for r in v}
         for a, v in arms.items()})))
    refs = check_references(arms, out)
    h = {a: np.array([final_h(r) for r in sorted(v, key=lambda r: int(r["seed"]))]) for a, v in arms.items()}
    boot = bootstrap(h)
    # inclusive cutoff with a float tolerance (Codex DR4 review: 0.6 - 0.5 over 20 seeds is 0.0999...87)
    rise_ok = boot["delta"] >= DR4_MIN_RISE - 1e-12
    valid = all(x["seeds_match"] and x["mean_traj_match"] for x in refs.values()) and rise_ok
    verdict = {"references": refs, "delta": boot["delta"], "delta_ci": boot["delta_ci"], "min_rise": DR4_MIN_RISE,
               "rise_ok": rise_ok, "valid": valid, "parts": boot["parts"],
               "overall": overall(boot["parts"]) if valid else "void",
               "bootstrap": {"resamples": DR4_BOOT, "seed": DR4_BOOT_SEED, "percentile": [2.5, 97.5]},
               "descriptive": {a: describe(v) for a, v in arms.items()}}
    (out / "dr4_verdict.json").write_text(json.dumps(run_r1.json_safe(verdict), indent=1, allow_nan=False))
    print(json.dumps(run_r1.json_safe({k: v for k, v in verdict.items() if k != "descriptive"}), indent=1))


if __name__ == "__main__":
    main()
