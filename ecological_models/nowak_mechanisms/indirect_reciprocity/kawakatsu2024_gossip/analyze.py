"""Registered analysis for PREREGISTRATION.md (Kawakatsu, Kessinger and Plotkin 2024 external check).

Reads the per-run JSON records of one stage attempt from ~/simulation_results/kawakatsu2024_gossip/runs/, checks the
record set against the frozen seed manifest, and applies the registered criteria with censoring bounds:
a share has bounds [observed / total, (observed + censored) / total]; a single-share criterion holds if the lower bound
reaches the bar, fails if the upper bound does not, and is otherwise unresolved at the cap; a difference A - B has
bounds [L_A - U_B, U_A - L_B] and is judged the same way. Writes summary.json (and verdict.json for Stage 1) next to
the records. Constants in the script (per AGENTS.md); STAGE selects the stage.

Run: python3 analyze.py   (after setting STAGE)
"""

import json
import math
import sys
from pathlib import Path

STAGE = 1
ATTEMPT = {1: 1, 2: 1, 3: 1}
RUNS = Path.home() / "simulation_results" / "kawakatsu2024_gossip" / "runs"
REPS = 50
STARTS = ["0.6/0.3/0.1", "0.4/0.4/0.2", "0.2/0.5/0.3", "0.6/0.1/0.3", "0.4/0.2/0.4", "0.2/0.3/0.5"]
STAGES = {
    1: {"norm": "SJ", "starts": [1, 2, 3, 4, 5, 6], "taus": [0.0, 0.4]},
    2: {"norm": "SJ", "starts": [6], "taus": [0.05, 0.10, 0.15, 0.20, 0.30]},
    3: {"norm": "SS", "starts": [1, 2, 3, 4, 5, 6], "taus": [0.0, 0.4]},
}
DISC_BASIN = [4, 5, 6]
OUTCOMES = ["ALLC", "ALLD", "DISC", "censored"]


def manifest(stage):
    st = STAGES[stage]
    return {100_000 * stage + 1_000 * s + 100 * ti + r: (s, t, r)
            for s in st["starts"] for ti, t in enumerate(st["taus"]) for r in range(1, REPS + 1)}


def load(stage, attempt):
    d = RUNS / f"stage{stage}" / f"attempt{attempt}"
    if not (d / "complete.txt").is_file():
        raise SystemExit(f"{d} has no complete.txt: the stage did not finish")
    want = manifest(stage)
    recs = {}
    for f in d.glob("*.json"):
        if f.name in ("summary.json", "verdict.json"):
            continue
        r = json.loads(f.read_text())
        recs[r["seed"]] = r
    if set(recs) != set(want):
        raise SystemExit(f"record set does not match the manifest: missing {len(set(want) - set(recs))}, "
                         f"extra {len(set(recs) - set(want))}")
    for seed, (s, t, rep) in want.items():
        r = recs[seed]
        assert (r["start"], r["tau"], r["rep"], r["norm"]) == (s, t, rep, STAGES[stage]["norm"]), seed
        assert r["outcome"] in OUTCOMES, seed
        assert sum(r["final_ALLC_ALLD_DISC"]) == 100, seed
    return d, list(recs.values())


def wilson(k, n, z=1.959964):
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(mid - half, 4), round(mid + half, 4)]


def cell(recs, start, tau):
    return [r for r in recs if r["start"] == start and math.isclose(r["tau"], tau)]


def bounds(rs, outcome):
    n = len(rs)
    k = sum(r["outcome"] == outcome for r in rs)
    cens = sum(r["outcome"] == "censored" for r in rs)
    return k / n, (k + cens) / n


def judge(lo, hi, bar):
    # holds if the lower bound reaches the bar; fails if the upper bound does not; otherwise unresolved
    if lo >= bar - 1e-12:
        return "holds"
    if hi < bar - 1e-12:
        return "fails"
    return "unresolved at the cap"


def describe(recs, stage):
    out = []
    for s in STAGES[stage]["starts"]:
        for t in STAGES[stage]["taus"]:
            rs = cell(recs, s, t)
            n = len(rs)
            row = {"start": STARTS[s - 1], "start_index": s, "tau": t, "n": n}
            for o in OUTCOMES:
                k = sum(r["outcome"] == o for r in rs)
                row[o] = k
                row[o + "_wilson95"] = wilson(k, n)
            fix = sorted(r["generations"] for r in rs if r["outcome"] != "censored")
            row["fixation_generation_median"] = fix[len(fix) // 2] if fix else None
            row["coop_rate_mean"] = round(sum(r["coop_rate_mean"] for r in rs) / n, 4)
            ext = [r for r in rs if r["alld_extinct_generation"] >= 0]
            row["ALLD_extinct"] = len(ext)
            row["final_mean_ALLC_ALLD_DISC"] = [round(sum(r["final_ALLC_ALLD_DISC"][i] for r in rs) / n, 2)
                                                for i in range(3)]
            out.append(row)
    return out


def criteria(recs, stage):
    res = {}
    if stage == 1:
        rs0 = [r for r in recs if math.isclose(r["tau"], 0.0)]
        lo, hi = bounds(rs0, "ALLD")
        res["C1"] = {"bounds": [lo, hi], "bar": 0.9, "result": judge(lo, hi, 0.9)}
        parts = []
        for s in DISC_BASIN:
            a, b = cell(recs, s, 0.4), cell(recs, s, 0.0)
            la, ua = bounds(a, "DISC")
            lb, ub = bounds(b, "DISC")
            maj = judge(la, ua, 26 / 50)
            diff = judge(la - ub, ua - lb, 20 / 50)
            res[f"C2_start{s}"] = {"DISC_tau0.4_bounds": [la, ua], "majority": maj,
                                   "diff_bounds": [round(la - ub, 4), round(ua - lb, 4)], "diff_vs_tau0": diff}
            parts += [maj, diff]
        res["C2"] = ("holds" if all(p == "holds" for p in parts)
                     else "fails" if any(p == "fails" for p in parts) else "unresolved at the cap")
        res["stage1_met"] = res["C1"]["result"] == "holds" and res["C2"] == "holds"
    elif stage == 2:
        la, ua = bounds(cell(recs, 6, 0.30), "DISC")
        lb, ub = bounds(cell(recs, 6, 0.05), "DISC")
        res["C3"] = {"diff_bounds": [round(la - ub, 4), round(ua - lb, 4)], "bar": 0.30,
                     "result": judge(la - ub, ua - lb, 0.30)}
    return res


def main():
    stage = STAGE
    d, recs = load(stage, ATTEMPT[stage])
    summary = {"stage": stage, "attempt": ATTEMPT[stage], "cells": describe(recs, stage),
               "criteria": criteria(recs, stage)}
    (d / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    if stage == 1:
        (d / "verdict.json").write_text(json.dumps({"stage1_met": summary["criteria"]["stage1_met"]}) + "\n")
    json.dump(summary, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
