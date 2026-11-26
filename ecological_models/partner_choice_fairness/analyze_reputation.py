"""Registered verdict of PREREG_REPUTATION.md from data/reputation_* and the earlier screen's data (V2).

    ./.conda/bin/python -m ecological_models.partner_choice_fairness.analyze_reputation [--final]

Checks the data (exact grid, 2,000 generations, finite shares), V1 (no-choice <= 0.25), V2 (q = 0 choice runs
reproduce the earlier screen's trajectories and summaries exactly), then the mechanism verdict and the PPG module
gate. A V1 or V2 failure gives "inspection pending"; --final marks the re-run, after which it is INVALID.
"""

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

FAIR = 0.4
EXPLOITED = 0.25
NEED = 16
QS = (0.0, 0.25, 0.5, 0.75, 1.0)
TS = (1, 5, 20)
HS = (0.0, 0.1)
STARTS = ("exploiter", "fair", "random")
SEEDS = tuple(range(20))
GENS = 2000
DATA = Path(__file__).resolve().parent / "data"
V2_COLS = ("partner_share", "mean_a", "catch_weighted_share", "frac_paired", "breakups_per_gen")


def _f(x):
    return float(x) if x not in ("", None) else float("nan")


def load(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["T"] = int(r["T"])
        r["h"] = float(r["h"])
        r["seed"] = int(r["seed"])
        r["gens"] = int(r["gens"])
        if "q" in r:
            r["q"] = float(r["q"])
        for c in V2_COLS + ("refusals_per_gen",):
            if c in r:
                r[c] = _f(r[c])
    return rows


def expected_keys():
    ch = {("choice", q, st, h, T) for q in QS for st in STARTS for h in HS for T in TS}
    nc = {("no_choice", 0.0, st, h, T) for st in STARTS for h in HS for T in TS}
    return ch | nc


def check(rows):
    problems = []
    seen = defaultdict(list)
    for r in rows:
        k = (r["arm"], r["q"], r["start"], r["h"], r["T"])
        seen[k].append(r["seed"])
        if r["gens"] != GENS:
            problems.append(f"{k} seed {r['seed']}: {r['gens']} generations")
        for col, lo, hi, nan_ok in (("partner_share", 0, 1, False), ("mean_a", 0, 1, False),
                                    ("catch_weighted_share", 0, 1, True), ("frac_paired", 0, 1, False),
                                    ("breakups_per_gen", 0, math.inf, False), ("refusals_per_gen", 0, math.inf, False)):
            x = r.get(col, float("nan"))
            if math.isnan(x) and nan_ok:
                continue
            if not (math.isfinite(x) and lo <= x <= hi):
                problems.append(f"{k} seed {r['seed']}: {col} {x}")
    exp = expected_keys()
    if set(seen) != exp:
        problems.append(f"cells: {len(set(seen) & exp)} of {len(exp)} expected, {len(set(seen) - exp)} unexpected")
    for k in exp & set(seen):
        if sorted(seen[k]) != list(SEEDS):
            problems.append(f"cell {k}: seeds {sorted(seen[k])}")
    return problems


def check_traj(rows, traj):
    problems = []
    for r in rows:
        for suf in ("_s", "_a"):
            k = f"{r['q']}_{r['T']}_{r['h']}_{r['start']}_{r['arm']}_{r['seed']}{suf}"
            if k not in traj.files:
                problems.append(f"trajectory missing: {k}")
            elif traj[k].shape != (GENS,):
                problems.append(f"trajectory {k}: shape {traj[k].shape}")
    return problems


def cells(rows):
    out = defaultdict(list)
    for r in rows:
        out[(r["arm"], r["q"], r["start"], r["h"], r["T"])].append(r)
    return out


def _mean(v):
    return sum(v) / len(v)


def v1(c):
    bad = [(st, h, T) for st in STARTS for h in HS for T in TS
           if _mean([r["partner_share"] for r in c[("no_choice", 0.0, st, h, T)]]) > EXPLOITED]
    return not bad, bad


def v2(rows, traj, old_rows, old_traj):
    """q = 0 choice runs vs the earlier screen. Returns list of mismatches."""
    old = {(r["T"], r["h"], r["start"], r["seed"]): r for r in old_rows if r["arm"] == "choice"}
    bad = []
    for r in rows:
        if r["arm"] != "choice" or r["q"] != 0.0:
            continue
        o = old.get((r["T"], r["h"], r["start"], r["seed"]))
        if o is None:
            bad.append(("missing baseline", r["T"], r["h"], r["start"], r["seed"]))
            continue
        for c in V2_COLS:
            x, y = r[c], o[c]
            if not ((math.isnan(x) and math.isnan(y)) or abs(x - y) <= 1e-12):
                bad.append((c, r["T"], r["h"], r["start"], r["seed"], x, y))
        nk = f"0.0_{r['T']}_{r['h']}_{r['start']}_choice_{r['seed']}"
        ok = f"{o['T']}_{o['h']}_{o['start']}_choice_{o['seed']}"
        for suf in ("_s", "_a"):
            if nk + suf not in traj.files or ok + suf not in old_traj.files:
                bad.append(("trajectory key missing" + suf, r["T"], r["h"], r["start"], r["seed"]))
            elif not np.array_equal(traj[nk + suf], old_traj[ok + suf]):
                bad.append(("trajectory" + suf, r["T"], r["h"], r["start"], r["seed"]))
    return bad


def fair_count(c, q, st, h, T):
    return sum(r["partner_share"] >= FAIR for r in c[("choice", q, st, h, T)])


def q_star(c, st, h, T):
    best = None
    for q in reversed(QS):
        if fair_count(c, q, st, h, T) >= NEED:
            best = q
        else:
            break
    return best


def verdict(c, valid=True, final=False):
    if not valid:
        return "INVALID" if final else "V1/V2 FAILED: inspection pending"

    def some_T(st):
        return [T for T in TS if all(q_star(c, st, h, T) is not None for h in HS)]

    em = some_T("exploiter")
    if em:
        mech = f"EMERGES (T = {em})"
        gate = "module gate MET" if any(T in (5, 20) for T in em) else "module gate not met (T = 1 only)"
        return f"{mech}; {gate}"
    mt = sorted(set(some_T("fair")) | set(some_T("random")))
    if mt:
        return f"MAINTAINED ONLY (T = {mt}); module gate not met"
    return "KILL; module gate not met"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--prefix", default="reputation_")
    p.add_argument("--final", action="store_true")
    args = p.parse_args(argv)
    try:
        status = json.loads((DATA / f"{args.prefix}status.json").read_text())
        if status.get("killed"):
            print("VERDICT: NO VERDICT (compute)")
            return
        rows = load(DATA / f"{args.prefix}runs.csv")
        problems = check(rows)
        traj = np.load(DATA / f"{args.prefix}traj.npz")
        problems += check_traj(rows, traj)
        old_rows = load(DATA / "screen_runs.csv")
        old_traj = np.load(DATA / "screen_traj.npz")
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"VERDICT: NO VERDICT (data): {e!r}")
        return
    if problems or not status.get("complete"):
        print("VERDICT: NO VERDICT (data)")
        for pr in problems[:20]:
            print("  " + pr)
        return
    c = cells(rows)
    ok1, bad1 = v1(c)
    bad2 = v2(rows, traj, old_rows, old_traj)
    print(f"{len(rows)} runs; V1 holds: {ok1}" + ("" if ok1 else f" {bad1}"))
    print(f"V2 holds: {not bad2}" + ("" if not bad2 else f" ({len(bad2)} mismatches, first: {bad2[:3]})"))
    print("\nno-choice mean partner share (start, h; T = 1, 5, 20)")
    for st in STARTS:
        for h in HS:
            print(f"  {st:9s} h={h}: " + "  ".join(f"{_mean([r['partner_share'] for r in c[('no_choice', 0.0, st, h, T)]]):.3f}" for T in TS))
    print("\nchoice arm: fair seeds of 20 | mean s | catch-weighted share | refusals/gen, per q; q*")
    for st in STARTS:
        for h in HS:
            for T in TS:
                parts = []
                for q in QS:
                    rs = c[("choice", q, st, h, T)]
                    parts.append(f"{fair_count(c, q, st, h, T):2d}|{_mean([r['partner_share'] for r in rs]):.3f}|"
                                 f"{np.nanmean([r['catch_weighted_share'] for r in rs]):.3f}|{_mean([r['refusals_per_gen'] for r in rs]):.0f}")
                subset = [q for q in QS
                          if np.nanmean([r["catch_weighted_share"] for r in c[("choice", q, st, h, T)]]) >= FAIR
                          and _mean([r["partner_share"] for r in c[("choice", q, st, h, T)]]) < FAIR]
                print(f"  {st:9s} h={h} T={T:2d}: " + "  ".join(parts) + f"   q* = {q_star(c, st, h, T)}"
                      + (f"   fair exchanges among a subset at q = {subset}" if subset else ""))
    print(f"\nVERDICT: {verdict(c, ok1 and not bad2, args.final)}")


if __name__ == "__main__":
    main()
