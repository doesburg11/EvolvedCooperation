#!/usr/bin/env python3
"""Hamilton's-rule prediction test (rules: README, pre-registered in f26de37).

Stage 0 (neutral runs, r(f) and the stage-1 manifest), then stage 1 (the test). Run from the repo root:
  ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_hamilton stage0
  ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_hamilton stage1
Writes data/hamilton/stage0_*.{csv,json}, manifest.json, stage1_*.{csv,json}.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from fractions import Fraction
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy import stats

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_hamilton stage0|stage1")

from ..config.ethnocentrism_config import (
    DATA_DIR, HAM_ALPHA, HAM_B_CAP, HAM_C, HAM_DIR, HAM_K, HAM_LEVELS, HAM_MIN_LEVELS, HAM_N, HAM_R_WINDOW,
    RANDOM_COLOUR_BASE, WORKERS, ham_seeds, run_config,
)
from ..ethnocentrism_model import Ethnocentrism
from .run_random_colour import clean, stats_of
from .run_viscosity import replays

PORT_EXPERIMENT = RANDOM_COLOUR_BASE                     # "104"
R_KEYS = ("pairs", "sum_ncov", "sum_nvar", "ticks_with_pairs", "ticks")
INT_KEYS = ("population", "births_total", "offspring_total", "last100_agent_ticks", "last100_helper_ticks")


# ---------------------------------------------------------------- runs
def settings(level: int, b: float, c: float) -> dict:
    return {"n_colors": 1, "colour_inheritance": "random", "shuffle_fraction": HAM_LEVELS[level],
            "cost_of_giving": c, "gain_of_receiving": b}


def one(job: tuple) -> dict:
    """job = (stage, level, k_index or None, seed, b, c). Failures are returned as error records, never raised."""
    stage, level, k, seed, b, c = job
    rec = {"stage": stage, "level": level, "k": k, "seed": seed}
    try:
        st = settings(level, b, c)
        cfg = {**run_config(PORT_EXPERIMENT), **st, "relatedness_window": HAM_R_WINDOW}
        return {**rec, "settings": st, **Ethnocentrism(cfg, seed).run()}
    except Exception as e:                                  # noqa: BLE001 - recorded; makes the stage invalid
        return {**rec, "error": repr(e)}


def port_replay_job(seed: int) -> dict:
    try:
        return {"seed": seed, **Ethnocentrism(run_config(PORT_EXPERIMENT), seed).run()}
    except Exception as e:                                  # noqa: BLE001
        return {"seed": seed, "error": repr(e)}


def port_reporter_keys(port_csv: Path) -> set[str]:
    """Reporter names from the committed port CSV header; empty set if unreadable or duplicated columns."""
    try:
        with open(port_csv) as fh:
            header = next(csv.reader(fh))
    except (OSError, StopIteration, csv.Error, UnicodeDecodeError):
        return set()
    if len(header) != len(set(header)):
        return set()
    return set(header) - {"experiment", "seed", "population", "births_total"}


def replay_ok(port_runs: list[dict], port_csv: Path) -> bool:
    if any("error" in r for r in port_runs) or sorted(r["seed"] for r in port_runs) != list(range(30)):
        return False
    if not port_reporter_keys(port_csv):
        return False
    try:
        return bool(replays(port_runs, port_csv, "experiment", PORT_EXPERIMENT))
    except (OSError, KeyError, ValueError, TypeError, csv.Error, UnicodeDecodeError):
        return False


# ---------------------------------------------------------------- per-run values
def _is_int(x) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, bool)


def well_formed(r: dict, expected: dict, reporter_keys: set[str]) -> bool:
    """Complete and consistent record whose settings match the manifest exactly (expected = settings dict)."""
    try:
        if "error" in r or r["settings"] != expected:
            return False
        if not reporter_keys or set(r["reporters"]) != reporter_keys:
            return False
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                   for v in r["reporters"].values()):
            return False
        if not all(_is_int(r[x]) and r[x] >= 0 for x in INT_KEYS):
            return False
        if r["last100_helper_ticks"] > r["last100_agent_ticks"] or r["offspring_total"] > r["births_total"]:
            return False
        k = r["relatedness_cs"]
        if set(k) != set(R_KEYS) or k["ticks"] != HAM_R_WINDOW[1] - HAM_R_WINDOW[0]:
            return False
        if not (_is_int(k["pairs"]) and _is_int(k["ticks_with_pairs"]) and 0 <= k["ticks_with_pairs"] <= k["ticks"]
                and k["pairs"] % 2 == 0 and 2 * k["ticks_with_pairs"] <= k["pairs"]   # directed pairs come in twos
                and (k["pairs"] > 0) == (k["ticks_with_pairs"] > 0)
                and math.isfinite(k["sum_ncov"]) and math.isfinite(k["sum_nvar"]) and k["sum_nvar"] >= -1e-9
                and abs(k["sum_ncov"]) <= k["sum_nvar"] + 1e-9):   # symmetric pairs: |cov| <= var within each tick
            return False
        if k["pairs"] == 0 and (k["sum_ncov"] != 0 or k["sum_nvar"] != 0):
            return False
        if k["sum_nvar"] > k["pairs"] / 4 + 1e-9:                # 0/1 trait: n * var(x) <= n / 4 in every tick
            return False
        if r["last100_agent_ticks"] >= 100:                       # NetLogo shares are unfloored here: must agree
            share = r["last100_helper_ticks"] / r["last100_agent_ticks"]
            if abs(r["reporters"]["cc-percent"] + r["reporters"]["cd-percent"] - share) > 1e-9:
                return False
        return True
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def r_of(r: dict) -> float:
    k = r["relatedness_cs"]
    return k["sum_ncov"] / k["sum_nvar"] if k["sum_nvar"] > 0 else math.nan


def r_exact(r: dict) -> Fraction | None:
    """The run's r as the exact ratio of its stored sums (None if undefined), for the feasibility rule."""
    k = r["relatedness_cs"]
    return Fraction(k["sum_ncov"]) / Fraction(k["sum_nvar"]) if k["sum_nvar"] > 0 else None


def helper_share(r: dict) -> float:
    n = r["last100_agent_ticks"]
    return r["last100_helper_ticks"] / n if n > 0 else math.nan


def batch_ok(res: list[dict], expected: dict[tuple, dict], reporter_keys: set[str]) -> bool:
    """Exactly one well-formed result per expected (stage, level, k, seed) key, nothing else."""
    try:
        got = [(r["stage"], r["level"], r["k"], r["seed"]) for r in res]
        for st, lev, k, sd in got:
            if not (_is_int(st) and _is_int(lev) and _is_int(sd) and (k is None or _is_int(k))):
                return False
        if len(got) != len(expected) or len(set(got)) != len(got) or set(got) != set(expected):
            return False
    except (KeyError, TypeError):
        return False
    return all(well_formed(r, expected[key], reporter_keys) for r, key in zip(res, got))


# ---------------------------------------------------------------- stage 0
C_EXACT, CAP_EXACT = Fraction(str(HAM_C)), Fraction(str(HAM_B_CAP))   # the registered decimal values


def feasibility(r_values: dict[int, list], h_values: dict[int, list[float]]) -> dict:
    """Mechanical rule: keep a level if all r defined, all neutral helper shares defined, r(f) > 0, 2c/r(f) <= cap.
    r values may be exact Fractions (from the stored sums) or floats; the mean and comparison are exact."""
    levels, kept, exact = {}, [], {}
    for lev in range(len(HAM_LEVELS)):
        rv = list(r_values.get(lev, []))
        hv = np.array(h_values.get(lev, []), dtype=float)
        ok_r = len(rv) == HAM_N and all(v is not None and (isinstance(v, Fraction) or math.isfinite(v)) for v in rv)
        ok_vals = ok_r and hv.size == HAM_N and bool(np.isfinite(hv).all())
        mean = sum(Fraction(v) for v in rv) / len(rv) if ok_vals else None        # exact mean, no rounding
        r_f = float(mean) if ok_vals else math.nan
        keep = bool(ok_vals and mean > 0 and 2 * C_EXACT <= CAP_EXACT * mean)
        levels[lev] = {"f": HAM_LEVELS[lev], "r": r_f, "keep": keep}
        if keep:
            kept.append(lev)
            exact[lev] = mean
    return {"levels": levels, "kept": kept, "feasible": len(kept) >= HAM_MIN_LEVELS, "exact": exact}


def manifest_from(feas: dict) -> dict:
    cells = []
    for lev in feas["kept"]:
        for ki, k in enumerate(HAM_K):
            b = float(Fraction(str(k)) * C_EXACT / feas["exact"][lev])     # exact, rounded once
            cells.append({"level": lev, "k": ki, "b": b, "seeds": ham_seeds(1, lev, ki)})
    return {"c": HAM_C, "kept_levels": feas["kept"], "r": {str(l): feas["levels"][l]["r"] for l in feas["kept"]},
            "cells": cells}


def stage0_expected() -> dict:
    return {(0, lev, None, s): settings(lev, 0.0, 0.0) for lev in range(len(HAM_LEVELS)) for s in ham_seeds(0, lev)}


def neutral_values(res: list[dict]) -> tuple[dict, dict, dict]:
    by = {lev: sorted((r for r in res if r["level"] == lev), key=lambda r: r["seed"]) for lev in range(len(HAM_LEVELS))}
    return by, {lev: [r_exact(r) for r in rs] for lev, rs in by.items()}, \
        {lev: [helper_share(r) for r in rs] for lev, rs in by.items()}


def refuse_if_done(path: Path) -> None:
    marker = path.with_suffix(".started")
    if path.exists() or marker.exists():                      # registered hard stop: one batch per stage
        raise SystemExit(f"{path} or its .started marker exists: this stage has already been run; not re-running")


def reserve(path: Path) -> None:
    """Atomically reserve the stage before any registered run is dispatched; the marker is never removed."""
    try:
        os.close(os.open(path.with_suffix(".started"), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        raise SystemExit(f"{path.with_suffix('.started')} exists: stage already started; not re-running")


def run_replay_first(pool, port_csv: Path) -> bool:
    return replay_ok(pool.map(port_replay_job, range(30), chunksize=1), port_csv)


def stage0(out_dir: Path, workers: int) -> dict:
    refuse_if_done(out_dir / "stage0_summary.json")
    reserve(out_dir / "stage0_summary.json")                  # before the replay: any outcome is final
    port_csv = Path(DATA_DIR) / "runs.csv"
    keys = port_reporter_keys(port_csv)
    expected = stage0_expected()
    with Pool(workers) as pool:
        rep_ok = run_replay_first(pool, port_csv)
        if not rep_ok:                                        # no registered run is made after a failed replay
            summary = {"replay_ok": False, "batch_ok": False, "status": "invalid", "errors": []}
            json.dump(summary, open(out_dir / "stage0_summary.json", "w"), indent=1)
            return summary
        res = pool.map(one, [(0, lev, None, s, 0.0, 0.0) for (_, lev, _, s) in expected], chunksize=1)
    valid = batch_ok(res, expected, keys)
    summary: dict = {"replay_ok": True, "batch_ok": valid, "errors": [r for r in res if "error" in r]}
    record_keys = ("stage", "level", "k", "seed", "settings", "reporters", "relatedness_cs", "error", *INT_KEYS)
    json.dump(clean([{k: r[k] for k in record_keys if k in r} for r in res]),
              open(out_dir / "stage0_records.json", "w"), allow_nan=False)                # raw, re-checked by stage 1
    if not valid:
        summary["status"] = "invalid"
        json.dump(clean(summary), open(out_dir / "stage0_summary.json", "w"), indent=1, allow_nan=False)
        return summary
    by, r_values, h_values = neutral_values(res)
    feas = feasibility(r_values, h_values)
    summary.update(status="valid" if feas["feasible"] else "not run: infeasible",
                   feasibility={k: v for k, v in feas.items() if k != "exact"},
                   neutral={str(lev): {"seeds": [r["seed"] for r in rs], "r": [math.nan if v is None else float(v) for v in r_values[lev]],
                                       "helper_share": h_values[lev]} for lev, rs in by.items()},
                   describe={str(lev): {"r": stats_of([math.nan if v is None else float(v) for v in r_values[lev]]), "helper_share": stats_of(h_values[lev]),
                                        "population": stats_of([r["population"] for r in rs])}
                             for lev, rs in by.items()})
    write_runs(out_dir / "stage0_runs.csv", res)
    if feas["feasible"]:
        json.dump(manifest_from(feas), open(out_dir / "manifest.json", "w"), indent=1, allow_nan=False)
    json.dump(clean(summary), open(out_dir / "stage0_summary.json", "w"), indent=1, allow_nan=False)
    return summary


# ---------------------------------------------------------------- stage 1
def stage0_from_records(out_dir: Path, reporter_keys: set[str]) -> tuple[dict, dict] | None:
    """Re-validate the committed raw stage-0 records and re-derive (manifest, neutral helper shares) from them;
    None if anything is missing, malformed, or the summary does not report a valid stage with a passed replay."""
    try:
        s0 = json.load(open(out_dir / "stage0_summary.json"))
        records = json.load(open(out_dir / "stage0_records.json"))
        if s0.get("status") != "valid" or s0.get("replay_ok") is not True or s0.get("batch_ok") is not True:
            return None
        if not batch_ok(records, stage0_expected(), reporter_keys):
            return None
        _, r_values, h_values = neutral_values(records)
        feas = feasibility(r_values, h_values)
        if not feas["feasible"]:
            return None
        return json.loads(json.dumps(manifest_from(feas))), {lev: np.array(v, dtype=float) for lev, v in h_values.items()}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def classify(cell: np.ndarray, neutral: np.ndarray, k: float) -> dict:
    """Welch two-sided test, cell vs neutral at the same f. correct / wrong / unclear, or invalid."""
    valid = cell.size == HAM_N and neutral.size == HAM_N and bool(np.isfinite(cell).all() and np.isfinite(neutral).all())
    se = math.sqrt(cell.var(ddof=1) / cell.size + neutral.var(ddof=1) / neutral.size) if valid else math.nan
    valid = valid and math.isfinite(se) and se > 1e-12
    diff = float(cell.mean() - neutral.mean()) if valid else math.nan
    p = float(stats.ttest_ind(cell, neutral, equal_var=False).pvalue) if valid else math.nan
    valid = valid and math.isfinite(p)
    if not valid:
        return {"diff": diff, "p": p, "class": "invalid"}
    predicted = 1 if k > 1 else -1
    sign = (diff > 0) - (diff < 0)
    cls = "correct" if sign == predicted and p < HAM_ALPHA else "wrong" if sign == -predicted and p < HAM_ALPHA \
        else "unclear"
    return {"diff": diff, "p": p, "class": cls}


def hypothesis(classes: list[str], stage_valid: bool) -> str:
    if not stage_valid or not classes or "invalid" in classes:
        return "invalid"
    if "wrong" in classes:
        return "not met: reversal"
    return "met" if all(c == "correct" for c in classes) else "inconclusive"


def k_star(diffs: list[float]) -> float:
    """Registered rule: signs (zeros included) non-decreasing across k, at least one negative and one positive,
    at most one zero, not at k = 0.5 or 2; then the zero's k, or log-k interpolation at the single crossing."""
    d = np.array(diffs, dtype=float)
    if d.size != len(HAM_K) or not np.isfinite(d).all():
        return math.nan
    s = np.sign(d)
    zeros = np.flatnonzero(s == 0)
    if (np.diff(s) < 0).any() or not (s < 0).any() or not (s > 0).any() or zeros.size > 1 \
            or (zeros.size and zeros[0] in (0, len(HAM_K) - 1)):
        return math.nan
    if zeros.size:
        return float(HAM_K[zeros[0]])
    i = int(np.flatnonzero(s < 0)[-1])
    lk = np.log(HAM_K)
    return float(math.exp(lk[i] + (0 - d[i]) * (lk[i + 1] - lk[i]) / (d[i + 1] - d[i])))


def mean_diff(cell: np.ndarray, neutral: np.ndarray) -> float:
    """Descriptive mean difference (for k*), independent of the Welch verdict."""
    ok = cell.size == HAM_N and neutral.size == HAM_N and bool(np.isfinite(cell).all() and np.isfinite(neutral).all())
    return float(cell.mean() - neutral.mean()) if ok else math.nan


def judge(cells: dict[tuple[int, int], np.ndarray], neutral: dict[int, np.ndarray], kept: list[int],
          stage_valid: bool) -> dict:
    out: dict = {"stage_valid": stage_valid, "cells": {}}
    for lev in kept:
        for ki, k in enumerate(HAM_K):
            out["cells"][f"{lev},{ki}"] = {"f": HAM_LEVELS[lev], "k": k,
                                           **classify(cells.get((lev, ki), np.array([])),
                                                      neutral.get(lev, np.array([])), k)}
    groups = {"H1": [0, 3], "H2": [1, 2]}
    for name, kis in groups.items():
        classes = [out["cells"][f"{lev},{ki}"]["class"] for lev in kept for ki in kis]
        v = hypothesis(classes, stage_valid)
        out[name] = {"verdict": v, "met": v == "met", "n_correct": classes.count("correct"),
                     "n_wrong": classes.count("wrong"), "n_unclear": classes.count("unclear"),
                     "n_invalid": classes.count("invalid")}
    out["k_star"] = {str(lev): k_star([mean_diff(cells.get((lev, ki), np.array([])), neutral.get(lev, np.array([])))
                                       for ki in range(len(HAM_K))]) for lev in kept}
    return out


def stage1(out_dir: Path, workers: int) -> dict:
    refuse_if_done(out_dir / "stage1_summary.json")
    port_csv = Path(DATA_DIR) / "runs.csv"
    keys = port_reporter_keys(port_csv)
    derived = stage0_from_records(out_dir, keys)
    try:
        manifest = json.load(open(out_dir / "manifest.json"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"manifest missing or unreadable: {e!r}")
    if derived is None or manifest != derived[0]:
        raise SystemExit("manifest does not follow from valid committed stage-0 records: stage 1 not run")
    neutral = derived[1]
    reserve(out_dir / "stage1_summary.json")                  # before the replay: any outcome is final
    expected = {(1, c["level"], c["k"], s): settings(c["level"], c["b"], HAM_C) for c in manifest["cells"]
                for s in c["seeds"]}
    jobs = [(1, c["level"], c["k"], s, c["b"], HAM_C) for c in manifest["cells"] for s in c["seeds"]]
    kept = manifest["kept_levels"]
    with Pool(workers) as pool:
        if not run_replay_first(pool, port_csv):
            summary = judge({}, neutral, kept, False)
            summary.update(replay_ok=False, batch_ok=False, errors=[])
            json.dump(clean(summary), open(out_dir / "stage1_summary.json", "w"), indent=1, allow_nan=False)
            return summary
        res = pool.map(one, jobs, chunksize=1)
    valid = batch_ok(res, expected, keys)
    cells = {(c["level"], c["k"]): np.array([helper_share(r) for r in sorted(
        (r for r in res if r["level"] == c["level"] and r["k"] == c["k"]), key=lambda r: r["seed"])])
             for c in manifest["cells"]} if valid else {}
    summary = judge(cells, neutral, kept, valid)
    summary.update(replay_ok=True, batch_ok=valid, errors=[r for r in res if "error" in r])
    json.dump(clean(summary), open(out_dir / "stage1_summary.json", "w"), indent=1, allow_nan=False)  # verdicts first
    if not valid:
        return summary
    write_runs(out_dir / "stage1_runs.csv", res)
    summary["describe"] = {}
    for c in manifest["cells"]:
        rs = [r for r in res if r["level"] == c["level"] and r["k"] == c["k"]]
        summary["describe"][f"{c['level']},{c['k']}"] = {
            "f": HAM_LEVELS[c["level"]], "k": HAM_K[c["k"]], "b": c["b"],
            "helper_share": stats_of([helper_share(r) for r in rs]), "r_under_selection": stats_of([r_of(r) for r in rs]),
            "population": stats_of([r["population"] for r in rs]),
            "offspring_per_tick": stats_of([r["offspring_total"] / run_config(PORT_EXPERIMENT)["ticks"] for r in rs])}
    json.dump(clean(summary), open(out_dir / "stage1_summary.json", "w"), indent=1, allow_nan=False)
    return summary


def write_runs(path: Path, res: list[dict]) -> None:
    keys = list(res[0]["reporters"])
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stage", "level", "f", "k_index", "seed", "cost", "benefit", "population", "births_total",
                    "offspring_total", "last100_agent_ticks", "last100_helper_ticks", "helper_share", "r",
                    *[f"r_{k}" for k in R_KEYS], *keys])
        for r in res:
            st = r["settings"]
            w.writerow([r["stage"], r["level"], st["shuffle_fraction"], "" if r["k"] is None else r["k"], r["seed"],
                        st["cost_of_giving"], st["gain_of_receiving"], r["population"], r["births_total"],
                        r["offspring_total"], r["last100_agent_ticks"], r["last100_helper_ticks"], helper_share(r),
                        r_of(r), *[r["relatedness_cs"][k] for k in R_KEYS], *[r["reporters"][k] for k in keys]])


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("stage0", "stage1"):
        raise SystemExit("usage: run_hamilton stage0|stage1")
    out_dir = Path(HAM_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    s = stage0(out_dir, WORKERS) if sys.argv[1] == "stage0" else stage1(out_dir, WORKERS)
    print(json.dumps(clean({k: v for k, v in s.items() if k not in ("neutral", "describe")}), indent=1))


if __name__ == "__main__":
    main()
