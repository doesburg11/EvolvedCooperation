"""README "Targeted sharing" and "Riskier stags": classifies each s > 0
condition of a targeted sweep's CSV as helps / hurts / neither against s = 0
in the same world, and prints the pre-registered predictions (P1-P3, or
R1-R3 with the argument lowq). Refuses incomplete or duplicated data."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..config.stag_hunt_sharing_config import RUN, SWEEP_TARGETED, SWEEP_TARGETED_LOWQ
from ..stag_hunt_sharing import conditions

THRESHOLD = 0.05
SHARING = ("share_fraction", "share_target", "sharing_radius")


def world(sweep: dict[str, list[Any]]) -> tuple[str, ...]:
    """The keys that make a world: everything swept except how food is
    shared (at s = 0 target and radius play no part)."""
    return tuple(k for k in sweep if k not in SHARING)


def key(setting: dict[str, Any], sweep: dict[str, list[Any]] = SWEEP_TARGETED) -> tuple:
    return tuple(str(setting[k]) for k in sweep)


def effects(rows: list[dict[str, Any]], sweep: dict[str, list[Any]] = SWEEP_TARGETED) -> list[dict[str, Any]]:
    """One record per s > 0 condition: mean, matched s = 0 mean, effect,
    class. Every condition of conditions(SWEEP_TARGETED) must have exactly
    the seeds in RUN, and no other rows may be present."""
    expected = {key(c, sweep): c for c in conditions(sweep)}
    keys = world(sweep)
    seeds = defaultdict(list)
    values = defaultdict(list)
    for row in rows:
        k = key(row, sweep)
        if k not in expected:
            raise ValueError(f"row outside the sweep: {k}")
        seeds[k].append(int(row["seed"]))
        values[k].append(float(row["stag_fraction"]))
    for k in expected:
        if sorted(seeds.get(k, [])) != sorted(RUN["seeds"]):
            raise ValueError(f"condition {k} has seeds {sorted(seeds.get(k, []))}, not {RUN['seeds']}")
    mean = {k: float(np.mean(v)) for k, v in values.items()}
    baseline = {tuple(str(c[w]) for w in keys): mean[k] for k, c in expected.items() if c["share_fraction"] == 0}
    out = []
    for k, c in expected.items():
        if c["share_fraction"] == 0:
            continue
        base = baseline[tuple(str(c[w]) for w in keys)]
        effect = mean[k] - base
        label = "helps" if effect > THRESHOLD else "hurts" if effect < -THRESHOLD else "neither"
        out.append({**c, "mean": mean[k], "baseline": base, "effect": effect, "class": label})
    return out


def predictions(records: list[dict[str, Any]]) -> list[tuple[str, int, int, int, bool]]:
    """(name, conditions, helps, hurts, met) for P1-P3."""
    p1 = [r for r in records if r["share_target"] == "stag" and r["fitness_shape"] == "diminishing" and str(r["dispersal"]) == "1"]
    p2 = [r for r in records if r["share_target"] == "stag" and r["fitness_shape"] == "linear"]
    p3 = [r for r in records if r["share_target"] == "all"]
    out = []
    for name, group, met in (
        ("P1 stag, diminishing, dispersal 1: helps in >= 1", p1, lambda h, x: h >= 1),
        ("P2 stag, linear: hurts in none", p2, lambda h, x: x == 0),
        ("P3 all: helps in none", p3, lambda h, x: h == 0),
    ):
        helps = sum(r["class"] == "helps" for r in group)
        hurts = sum(r["class"] == "hurts" for r in group)
        out.append((name, len(group), helps, hurts, met(helps, hurts)))
    return out


def predictions_lowq(records: list[dict[str, Any]]) -> list[tuple[str, int, int, int, bool]]:
    """(name, conditions, helps, hurts, met) for R1-R3 (README, "Riskier stags")."""
    def q(r, value):
        return float(r["stag_success_probability"]) == value

    r1 = [r for r in records if r["share_target"] == "stag" and r["fitness_shape"] == "diminishing" and q(r, 0.5)]
    r2 = [r for r in records if r["share_target"] == "stag" and r["fitness_shape"] == "diminishing" and q(r, 0.2)]
    r3 = [r for r in records if r["share_target"] == "all"]
    out = []
    for name, group, met in (
        ("R1 stag, diminishing, q 0.5: helps in >= 1", r1, lambda h, x: h >= 1),
        ("R2 stag, diminishing, q 0.2: helps in >= 1", r2, lambda h, x: h >= 1),
        ("R3 all: helps in none", r3, lambda h, x: h == 0),
    ):
        helps = sum(r["class"] == "helps" for r in group)
        hurts = sum(r["class"] == "hurts" for r in group)
        out.append((name, len(group), helps, hurts, met(helps, hurts)))
    return out


def main() -> None:
    import sys

    lowq = sys.argv[1:] == ["lowq"]
    csv_path = RUN["targeted_lowq_csv"] if lowq else RUN["targeted_csv"]
    with open(csv_path) as handle:
        rows = list(csv.DictReader(handle))
    records = effects(rows, SWEEP_TARGETED_LOWQ if lowq else SWEEP_TARGETED)
    lines = [f"{len(records)} conditions with s > 0 (threshold {THRESHOLD})"]
    for name, n, helps, hurts, met in (predictions_lowq if lowq else predictions)(records):
        lines.append(f"{name}: {n} conditions, helps {helps}, hurts {hurts} -> {'MET' if met else 'NOT MET'}")
    lines.append("")
    lines.append("conditions where sharing helps:")
    for r in sorted(records, key=lambda r: -r["effect"]):
        if r["class"] == "helps":
            q = f"q {r['stag_success_probability']}, " if "stag_success_probability" in r else ""
            lines.append(f"  target {r['share_target']}, s {r['share_fraction']}, radius {r.get('sharing_radius', 1)}, {q}ratio {r['stag_to_hare_ratio']}, {r['fitness_shape']}, dispersal {r['dispersal']}: {r['baseline']:.3f} -> {r['mean']:.3f} ({r['effect']:+.3f})")
    text = "\n".join(lines)
    print(text)
    path = Path(csv_path).with_name("judge_targeted_lowq.txt" if lowq else "judge_targeted.txt")
    path.write_text(text + "\n")


if __name__ == "__main__":
    main()
