#!/usr/bin/env python3
"""Step 5 restart: births into free space on the K1 base (pre-registration ../STEP5_RESTART.md).

Stage S (demographic screen) -> point written -> Stage M (care test) -> mechanical classification; attempt 2 only
after attempt 1 is 'local failure' or 'comparison failed' (hard stop after attempt 2).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_step5
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"

import json  # noqa: E402
import math  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_step5")

from ..step5_model import Params, Step5Model  # noqa: E402
from .analysis import fisher_greater  # noqa: E402
from .run_steps01 import write_csv  # noqa: E402

DATA_DIR = Path("ecological_models/nowak_mechanisms/kin_selection/ladder/data/step5")
UPDATES = 6000
WINDOW = (1000, 5999)          # start-of-update states after 1000..5999 completed updates
LATE = (4000, 5999)
CORR_AT = (1000, 2000, 3000, 4000, 5000)   # end states within the window, K1 cadence (amendment A1)
SUCCESS_H = 0.60
VIABLE_OCC = 0.50
OCC_MAX = 0.90
EXPOSURE_MIN = 0.10
MIN_TEST = 15
MIN_LEAD = 8
ALPHA = 0.025
MIN_VIABLE = 18
MAX_CORR_H2 = 0.10
C = 0.2
LOW = {"initial_mean": 0.05, "initial_sd": 0.02}
COMMON = {"initial_mean": 0.9, "initial_sd": 0.05}
FIXED = {"mutation_rate": 0.0, "initial_sd": 0.0}
S_P0 = [0.2, 0.3, 0.45]
S_D = [0.05, 0.1, 0.2]
S_SEEDS = [50, 51, 52, 53]
M_SEEDS = list(range(20))
WORKERS = int(os.environ.get("STEP5_WORKERS", "6"))
NICE = 10


def m_arms(p0: float, d: float, attempt: int) -> dict[str, dict]:
    base = {"p0": p0, "d": d, "attempt": attempt}
    pre = "F" if attempt == 1 else "F2-"
    def a(B_ratio, **kw):
        return {**base, "B": B_ratio * C, **LOW, **kw}
    return {
        f"{pre}6-local": a(6),
        f"{pre}N6-local": a(6, care="neighbours"),
        f"{pre}R6-local": a(6, care="matched"),
        f"{pre}6-refill": a(6, births="refill"),
        f"{pre}below": {**base, "B": 0.05, **COMMON},
        f"{pre}3-local": a(3),
        f"{pre}12-local": a(12),
        f"{pre}24-local": a(24),
        f"{pre}6-global": a(6, births="global"),
        f"{pre}6-dd": a(6, births="dd"),
        f"{pre}null": {**base, "B": 0.0, "C": 0.0, "care": "none", **LOW},
    }


def run_one(job: tuple) -> dict:
    arm, kw, seed, stage = job
    m = Step5Model(Params(**kw), seed)
    win = {k: [] for k in ("occupancy_start", "births_per_occupant", "failed_per_attempt", "failed_per_occupant",
                           "clipped_fraction", "offspring_mean", "frac_no_offspring", "benefit_lost",
                           "shortfall_lost", "own_offspring_share")}
    exp_w = [0, 0]      # pooled exposed survivors, survivors (window); amendment A1
    exp_l = [0, 0]      # same, late window
    late_occ, traj, corr, pocorr = [], [], [], []
    n_win = n_late = 0
    extinct_at = None
    while m.s.step_index < UPDATES:
        t0 = m.s.step_index
        last = m.step()
        if WINDOW[0] <= t0 <= WINDOW[1]:
            n_win += 1
            for k in win:
                win[k].append(last[k])
            exp_w[0] += last["exposed_survivors"]
            exp_w[1] += last["survivors"]
        if LATE[0] <= t0 <= LATE[1]:
            n_late += 1
            late_occ.append(last["occupancy_start"])
            exp_l[0] += last["exposed_survivors"]
            exp_l[1] += last["survivors"]
        t = m.s.step_index
        if t % 50 == 0:
            traj.append(m.mean_h())
        if t in CORR_AT:
            corr.append(m.neighbour_corr())
            pocorr.append(m.parent_offspring_corr())
        if m.extinct():
            extinct_at = t
            break
    def mean(v):
        v = np.asarray(v, dtype=float)
        return float(np.nanmean(v)) if v.size and np.isfinite(v).any() else float("nan")
    final_occ = m.occupancy()
    final_h = m.mean_h()
    full = extinct_at is None
    viable = full and final_occ >= VIABLE_OCC
    row = {"stage": stage, "arm": arm, "seed": seed, **{k: v for k, v in kw.items()},
           "completed_updates": m.s.step_index, "extinct": int(not full), "extinct_at": extinct_at,
           "final_occupancy": final_occ, "final_mean_h": final_h, "viable": int(viable),
           "success": int(viable and final_h >= SUCCESS_H),
           "late_occupancy": mean(late_occ), "late_exposure": exp_l[0] / exp_l[1] if exp_l[1] else float("nan"),
           "window_exposure": exp_w[0] / exp_w[1] if exp_w[1] else float("nan"),
           "neighbour_h_corr": mean(corr), "neighbour_h_corr_defined": int(np.isfinite(corr).sum()) if corr else 0,
           "parent_offspring_corr": mean(pocorr), "traj_every_50": traj, "n_window": n_win, "n_late": n_late}
    # an extinct run is never vacancy-exposed (amendment A1)
    row["vacancy_exposed"] = int(full and row["late_occupancy"] <= OCC_MAX and row["late_exposure"] >= EXPOSURE_MIN)
    for k, v in win.items():
        row[f"window_{k}"] = mean(v)
    return row


def complete(rows: list[dict], jobs: list[tuple]) -> bool:
    want = sorted((j[0], j[2]) for j in jobs)
    got = sorted((r["arm"], r["seed"]) for r in rows)
    if want != got:
        return False
    for r in rows:   # a full run with full windows, or an extinction (a valid result) at its recorded update
        if r["extinct"] == 1:
            if not (r["extinct_at"] == r["completed_updates"] and r["completed_updates"] <= UPDATES):
                return False
        elif r["extinct"] == 0:
            if not (r["completed_updates"] == UPDATES and r["n_window"] == WINDOW[1] - WINDOW[0] + 1
                    and r["n_late"] == LATE[1] - LATE[0] + 1):
                return False
        else:
            return False
    return True


def stage_s(pool, attempt: int) -> dict:
    jobs = []
    for p0 in S_P0:
        for d in S_D:
            for hv in (0.0, 0.6):
                for births in ("local", "refill"):
                    kw = {"p0": p0, "d": d, "attempt": attempt, "B": 1.2, "births": births,
                          "initial_mean": hv, **FIXED}
                    for s in S_SEEDS:
                        jobs.append((f"S{attempt}_p{p0}_d{d}_h{hv}_{births}", kw, s, f"S{attempt}"))
    rows = pool.map(run_one, jobs)
    if not complete(rows, jobs):
        raise RuntimeError("Stage S incomplete: rerun the same jobs")
    points = []
    for p0 in S_P0:
        for d in S_D:
            loc = [r for r in rows if r["p0"] == p0 and r["d"] == d and r["births"] == "local"]
            ok = all((not r["extinct"]) and OCC_MAX >= r["window_occupancy_start"] >= VIABLE_OCC
                     and r["window_exposure"] >= EXPOSURE_MIN for r in loc)
            points.append({"p0": p0, "d": d, "passes": ok,
                           "per_run": [{k: r[k] for k in ("initial_mean", "seed", "extinct", "window_occupancy_start",
                                                          "window_exposure")} for r in loc]})
    passing = [q for q in points if q["passes"]]
    chosen = sorted(passing, key=lambda q: (-q["d"], q["p0"]))[0] if passing else None
    return {"rows": rows, "points": points, "chosen": chosen}


def counts(rows, key):
    return int(sum(r[key] for r in rows))


def classify(arms: dict[str, list[dict]], pre: str) -> dict:
    t, n6, r6 = arms[f"{pre}6-local"], arms[f"{pre}N6-local"], arms[f"{pre}R6-local"]
    below, glob, refill = arms[f"{pre}below"], arms[f"{pre}6-global"], arms[f"{pre}6-refill"]
    viab = {a: counts(arms[a], "viable") for a in (f"{pre}6-local", f"{pre}N6-local", f"{pre}below")}
    succ = {a: counts(v, "success") for a, v in arms.items()}
    exposed = counts(t, "vacancy_exposed")
    ts, ns = succ[f"{pre}6-local"], succ[f"{pre}N6-local"]
    p_n6 = fisher_greater(ts, 20, ns, 20)
    if min(viab.values()) < MIN_VIABLE:
        cls = "not interpretable"
    elif exposed < MIN_TEST:
        cls = "not a step-5 test"
    elif ts < MIN_TEST or succ[f"{pre}below"] > 2:
        cls = "local failure"
    elif ts - ns < MIN_LEAD or not p_n6 < ALPHA:
        cls = "comparison failed"
    else:
        cls = "met"
    gs = succ[f"{pre}6-global"]
    # H2 (amendment A1): any F6-global run without a defined correlation sample makes H2 not interpretable
    if any(r["neighbour_h_corr_defined"] == 0 for r in glob):
        corr, h2 = float("nan"), "not interpretable (undefined correlation)"
    else:
        corr = float(np.mean([r["neighbour_h_corr"] for r in glob]))
        h2 = "not interpretable" if not corr <= MAX_CORR_H2 else ("met" if gs >= MIN_TEST else "not met")
    rs = succ[f"{pre}R6-local"]
    p_r6 = fisher_greater(ts, 20, rs, 20)
    if cls != "met":
        h3 = "not scored (primary not met)"
    elif counts(r6, "viable") < MIN_VIABLE:
        h3 = "not interpretable (FR6-local viability)"
    else:
        h3 = "met" if (ts - rs >= MIN_LEAD and p_r6 < ALPHA) else "not met"
    fs = succ[f"{pre}6-refill"]
    # failure reading (amendment A1): only when the local test arm itself missed its endpoint
    if cls == "met":
        reading = "met"
    elif cls in ("local failure", "comparison failed") and ts < MIN_TEST:
        reading = ("free space blocks care on this base (against the refill benchmark)" if fs >= MIN_TEST
                   else "missed endpoint for this birth-rule package")
    elif cls in ("local failure", "comparison failed"):
        reading = "care reached the endpoint locally; the failure is in the below-rule control or the comparison"
    else:
        reading = cls
    dd = succ[f"{pre}6-dd"]
    paired = {}
    for ctrl in (f"{pre}N6-local", f"{pre}R6-local", f"{pre}6-refill"):
        diffs = [a["final_mean_h"] - b["final_mean_h"] for a, b in zip(t, arms[ctrl])
                 if a["seed"] == b["seed"]]
        paired[ctrl] = {"mean_seed_paired_diff_final_h": float(np.nanmean(diffs)),
                        "test_higher_in": int(sum(x > 0 for x in diffs if np.isfinite(x)))}
    return {"class": cls, "viable": viab, "successes": succ, "test_vacancy_exposed": exposed,
            "seed_paired_vs_test": paired,
            "fisher_p_vs_N6": p_n6, "h2": {"result": h2, "successes": gs, "neighbour_corr": corr},
            "h3": {"result": h3, "matched_successes": rs, "fisher_p_vs_R6": p_r6},
            "refill_successes": fs, "failure_reading": reading,
            "dd_exploratory": {"dd_successes": dd, "fisher_p_dd_vs_local": fisher_greater(dd, 20, ts, 20),
                               "dd_mean_final_h": float(np.nanmean([r["final_mean_h"] for r in arms[f"{pre}6-dd"]])),
                               "local_mean_final_h": float(np.nanmean([r["final_mean_h"] for r in t]))}}


def describe(arms: dict[str, list[dict]]) -> dict:
    keys = ["final_mean_h", "final_occupancy", "late_occupancy", "late_exposure", "neighbour_h_corr",
            "parent_offspring_corr"] + [k for k in arms[next(iter(arms))][0] if k.startswith("window_")]
    out = {}
    for a, v in arms.items():
        d = {"successes": counts(v, "success"), "viable": counts(v, "viable"), "extinct": counts(v, "extinct"),
             "vacancy_exposed": counts(v, "vacancy_exposed")}
        for k in keys:
            vals = np.asarray([r[k] for r in v], dtype=float)
            d[k] = float(np.nanmean(vals)) if np.isfinite(vals).any() else None
        traj = [r["traj_every_50"] for r in v if len(r["traj_every_50"]) == UPDATES // 50]
        if traj:
            mt = np.nanmean(np.array(traj, dtype=float), axis=0)
            d["mean_h_at_1000_2000_4000_6000"] = [float(mt[i // 50 - 1]) for i in (1000, 2000, 4000, 6000)]
        out[a] = d
    return out


def _clean(x):
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    return x


def main() -> None:
    if os.nice(0) < NICE:
        os.nice(NICE - os.nice(0))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if any(DATA_DIR.iterdir()):
        raise SystemExit(f"{DATA_DIR} is not empty; refusing to overwrite a registered run. The run is deterministic: "
                         "after an interrupted run, move the partial output aside by hand and rerun from the start.")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "ecological_models/nowak_mechanisms/kin_selection/ladder",
                            ":(exclude)ecological_models/nowak_mechanisms/kin_selection/ladder/data"],
                           capture_output=True, text=True).stdout.strip()
    verdict = {"git_commit": commit, "tree_clean": dirty == "", "workers": WORKERS}
    t0 = time.time()
    with Pool(WORKERS) as pool:
        for attempt in (1, 2):
            s = stage_s(pool, attempt)
            write_csv(DATA_DIR / f"stage_s{attempt}_runs.csv", s["rows"])
            (DATA_DIR / f"stage_s{attempt}_choice.json").write_text(json.dumps(_clean(
                {"points": s["points"], "chosen": s["chosen"]}), indent=1))
            print(f"attempt {attempt} Stage S chosen:", s["chosen"] and {k: s["chosen"][k] for k in ("p0", "d")},
                  f"({(time.time() - t0) / 60:.1f} min)", flush=True)
            res = {"stage_s_chosen": s["chosen"] and {k: s["chosen"][k] for k in ("p0", "d")}}
            if s["chosen"] is None:
                res["class"] = "stopped: no Stage S point passes"
                verdict[f"attempt{attempt}"] = res
                break
            arms_cfg = m_arms(s["chosen"]["p0"], s["chosen"]["d"], attempt)
            jobs = [(a, kw, sd, f"M{attempt}") for a, kw in arms_cfg.items() for sd in M_SEEDS]
            rows = pool.map(run_one, jobs)
            if not complete(rows, jobs):
                raise RuntimeError(f"Stage M attempt {attempt} incomplete: rerun the same jobs")
            write_csv(DATA_DIR / f"stage_m{attempt}_runs.csv", rows)
            with open(DATA_DIR / f"stage_m{attempt}_traj.json", "w") as f:
                json.dump(_clean([{"arm": r["arm"], "seed": r["seed"], "traj": r["traj_every_50"]} for r in rows]), f)
            arms = {a: sorted([r for r in rows if r["arm"] == a], key=lambda r: r["seed"]) for a in arms_cfg}
            res.update(classify(arms, "F" if attempt == 1 else "F2-"))
            res["descriptive"] = describe(arms)
            verdict[f"attempt{attempt}"] = res
            print(f"attempt {attempt}: {res['class']}; H2 {res['h2']['result']}; H3 {res['h3']['result']} "
                  f"({(time.time() - t0) / 60:.1f} min)", flush=True)
            if res["class"] not in ("local failure", "comparison failed"):
                break
    verdict["wall_minutes"] = round((time.time() - t0) / 60, 1)
    (DATA_DIR / "verdict.json").write_text(json.dumps(_clean(verdict), indent=1))
    print(json.dumps(_clean({k: ({kk: vv for kk, vv in v.items() if kk != "descriptive"} if isinstance(v, dict) else v)
                             for k, v in verdict.items()}), indent=1))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
