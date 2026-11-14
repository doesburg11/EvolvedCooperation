#!/usr/bin/env python3
"""
Step 0 verdict for selection between groups (PredPreyGrass
eco_evolutionary_deer_stag_hunt DESIGN_4.md and RESULTS.md section 4.2),
from data/sweep_groups.csv (groups.py).

A rule (R or F) passes if, at ratio 1.2 with diminishing fitness, for every
q in {0.3, 0.45, 0.6} and both starts (0.05, 0.5), it gives takeover (mean
stag share over the last 100 generations > 0.5) in at least 15 of 20 seeds
and in at least 10 more seeds than rule "none". Training goes ahead with F
if F passes, else R if R passes, else the line stops.

Also prints the full table: takeovers out of 20 per ratio, q, start and rule.
Writes data/judge_groups.txt.

    ./.conda/bin/python -m ecological_models.stag_hunt_sharing.utils.judge_groups
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

from ..config.stag_hunt_sharing_config import GROUPS

RATIO, QS, STARTS, SEEDS = 1.2, (0.3, 0.45, 0.6), (0.05, 0.5), 20
TAKEOVER, MIN_PASS, MIN_GAIN = 0.5, 15, 10


def load(path):
    with open(path) as handle:
        return list(csv.DictReader(handle))


def takeovers(rows):
    """{(ratio, q, start, rule): (takeovers, seeds)}, checking each cell
    has exactly the 20 seeds once."""
    seen = defaultdict(list)
    for row in rows:
        if row["fitness_shape"] != "diminishing":
            raise ValueError("only diminishing fitness is expected")
        key = (float(row["stag_to_hare_ratio"]), float(row["stag_success_probability"]), float(row["initial_stag_fraction"]), row["rule"])
        seen[key].append((int(row["seed"]), float(row["stag_fraction"]) > TAKEOVER))
    out = {}
    for key, values in seen.items():
        seeds = sorted(s for s, _ in values)
        if seeds != list(GROUPS["seeds"]) or len(seeds) != SEEDS:
            raise ValueError(f"cell {key}: seeds {seeds}")
        out[key] = (sum(t for _, t in values), len(values))
    return out


def verdict(table):
    """{rule: (passes, [per q/start detail])}."""
    result = {}
    for rule in ("R", "F"):
        details, ok = [], True
        for q in QS:
            for start in STARTS:
                got = table[(RATIO, q, start, rule)][0]
                base = table[(RATIO, q, start, "none")][0]
                cell = got >= MIN_PASS and got - base >= MIN_GAIN
                ok &= cell
                details.append(f"q {q}, start {start}: {rule} {got}/20, none {base}/20 -> {'pass' if cell else 'fail'}")
        result[rule] = (ok, details)
    return result


def main():
    if sys.argv[1:]:
        raise SystemExit("usage: ... utils.judge_groups")
    table = takeovers(load(GROUPS["results_csv"]))
    lines = []
    result = verdict(table)
    for rule in ("R", "F"):
        ok, details = result[rule]
        lines.append(f"rule {rule}: {'PASSES' if ok else 'fails'} at ratio {RATIO}")
        lines += [f"  {d}" for d in details]
    chosen = "F" if result["F"][0] else "R" if result["R"][0] else None
    lines.append(f"step 0: {'training goes ahead with rule ' + chosen if chosen else 'neither rule passes; the line stops'}")
    lines.append("")
    lines.append("takeovers of 20 (none / R / F), by ratio, q and start:")
    ratios = sorted({k[0] for k in table})
    for q in QS:
        for start in STARTS:
            cells = "; ".join(f"{r}: " + "/".join(str(table[(r, q, start, rule)][0]) for rule in ("none", "R", "F")) for r in ratios)
            lines.append(f"  q {q}, start {start}: {cells}")
    text = "\n".join(lines)
    print(text)
    out = Path(GROUPS["results_csv"]).with_name("judge_groups.txt")
    out.write_text(text + "\n")


if __name__ == "__main__":
    main()
