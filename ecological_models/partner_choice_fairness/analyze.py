"""Registered verdict of PREREG_SCREEN.md step 2 from data/screen_runs.csv and data/screen_status.json.

    ./.conda/bin/python -m ecological_models.partner_choice_fairness.analyze [--v1-final]

The data are first checked: the exact registered grid (arm x start x h x T, seeds 0-19 once each),
2,000 generations, finite partner shares in [0, 1]. A failed check gives NO VERDICT (data). If V1 fails,
the output is "V1 FAILED: inspection pending" (the registered one inspection and re-run come first);
--v1-final marks the re-run, after which a V1 failure is INVALID.
"""

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

FAIR = 0.4
EXPLOITED = 0.25
NEED = 16  # of 20 seeds
TS = (1, 5, 20, 50, 100)
HS = (0.0, 0.1, 0.3)
STARTS = ("exploiter", "fair", "random")
ARMS = ("choice", "no_choice")
SEEDS = tuple(range(20))
GENS = 2000
H = 100
DATA = Path(__file__).resolve().parent / "data"


def load(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["T"] = int(r["T"])
        r["h"] = float(r["h"])
        r["seed"] = int(r["seed"])
        r["gens"] = int(r["gens"])
        r["partner_share"] = float(r["partner_share"])
    return rows


def check(rows):
    """Problems with the dataset (empty list = the exact registered grid)."""
    problems = []
    seen = defaultdict(list)
    for r in rows:
        key = (r["arm"], r["start"], r["h"], r["T"])
        seen[key].append(r["seed"])
        if r["gens"] != GENS:
            problems.append(f"run {key} seed {r['seed']}: {r['gens']} generations")
        x = r["partner_share"]
        if not (math.isfinite(x) and 0.0 <= x <= 1.0):
            problems.append(f"run {key} seed {r['seed']}: partner share {x}")
    expected = {(a, s, h, T) for a in ARMS for s in STARTS for h in HS for T in TS}
    if set(seen) != expected:
        problems.append(f"cells: {len(set(seen) & expected)} of {len(expected)} expected, {len(set(seen) - expected)} unexpected")
    for key in expected & set(seen):
        if sorted(seen[key]) != list(SEEDS):
            problems.append(f"cell {key}: seeds {sorted(seen[key])}")
    return problems


def cells(rows):
    out = defaultdict(list)
    for r in rows:
        out[(r["arm"], r["start"], r["h"], r["T"])].append(r["partner_share"])
    return out


def _mean(v):
    return sum(v) / len(v)


def v1(c):
    """V1: every no-choice cell's mean partner share <= 0.25. Returns (holds, failing cells)."""
    bad = [(s, h, T, _mean(c[("no_choice", s, h, T)])) for s in STARTS for h in HS for T in TS
           if _mean(c[("no_choice", s, h, T)]) > EXPLOITED]
    return not bad, bad


def fair_counts(c, start, h):
    return [sum(x >= FAIR for x in c[("choice", start, h, T)]) for T in TS]


def x_star(c, start, h):
    """Largest T/H with >= 16/20 fair there and at every smaller T/H; None if the first fails."""
    best = None
    for T, n in zip(TS, fair_counts(c, start, h)):
        if n >= NEED:
            best = T / H
        else:
            break
    return best


def verdict(c, v1_final=False):
    """Registered verdict for a checked, complete dataset."""
    ok, _ = v1(c)
    if not ok:
        return "INVALID" if v1_final else "V1 FAILED: inspection pending"

    def all_h(start):
        return all((x_star(c, start, h) or 0) >= 0.05 for h in HS)

    if all_h("exploiter"):
        return "PASS"
    if all_h("random") or all_h("fair"):
        return "MARGINAL"
    return "KILL"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--runs", default=str(DATA / "screen_runs.csv"))
    p.add_argument("--status", default=str(DATA / "screen_status.json"))
    p.add_argument("--v1-final", action="store_true")
    args = p.parse_args(argv)
    try:
        status = json.loads(Path(args.status).read_text())
        if status.get("killed"):
            print("VERDICT: NO VERDICT (compute)")
            return
        rows = load(args.runs)
        problems = check(rows)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"VERDICT: NO VERDICT (data): {e!r}")
        return
    if problems or not status.get("complete"):
        print("VERDICT: NO VERDICT (data)")
        for pr in problems[:20]:
            print("  " + pr)
        return
    c = cells(rows)
    ok, bad = v1(c)
    print(f"{len(rows)} runs; V1 holds: {ok}" + ("" if ok else f"; failing: {bad}"))
    print("\nno-choice mean partner share (rows start, h; columns T = " + ", ".join(map(str, TS)) + ")")
    for start in STARTS:
        for h in HS:
            print(f"  {start:9s} h={h}: " + "  ".join(f"{_mean(c[('no_choice', start, h, T)]):.3f}" for T in TS))
    print("\nchoice arm: fair seeds of 20 | mean partner share, per T; x*")
    for start in STARTS:
        for h in HS:
            n = fair_counts(c, start, h)
            means = [_mean(c[("choice", start, h, T)]) for T in TS]
            print(f"  {start:9s} h={h}: " + "  ".join(f"{k:2d}|{m:.3f}" for k, m in zip(n, means))
                  + f"   x* = {x_star(c, start, h)}")
    print(f"\nVERDICT: {verdict(c, args.v1_final)}")


if __name__ == "__main__":
    main()
