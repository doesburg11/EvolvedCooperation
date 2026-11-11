"""README "Targeted sharing": classifies each s > 0 condition of
data/sweep_targeted.csv as helps / hurts / neither against s = 0 in the same
world, and prints the pre-registered predictions P1-P3. Refuses incomplete
or duplicated data."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..config.stag_hunt_sharing_config import RUN, SWEEP_TARGETED
from ..stag_hunt_sharing import conditions

THRESHOLD = 0.05
WORLD = ("stag_to_hare_ratio", "fitness_shape", "dispersal")


def key(setting: dict[str, Any]) -> tuple:
    return tuple(str(setting[k]) for k in SWEEP_TARGETED)


def effects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One record per s > 0 condition: mean, matched s = 0 mean, effect,
    class. Every condition of conditions(SWEEP_TARGETED) must have exactly
    the seeds in RUN, and no other rows may be present."""
    expected = {key(c): c for c in conditions(SWEEP_TARGETED)}
    seeds = defaultdict(list)
    values = defaultdict(list)
    for row in rows:
        k = key(row)
        if k not in expected:
            raise ValueError(f"row outside the sweep: {k}")
        seeds[k].append(int(row["seed"]))
        values[k].append(float(row["stag_fraction"]))
    for k in expected:
        if sorted(seeds.get(k, [])) != sorted(RUN["seeds"]):
            raise ValueError(f"condition {k} has seeds {sorted(seeds.get(k, []))}, not {RUN['seeds']}")
    mean = {k: float(np.mean(v)) for k, v in values.items()}
    baseline = {tuple(str(c[w]) for w in WORLD): mean[k] for k, c in expected.items() if c["share_fraction"] == 0}
    out = []
    for k, c in expected.items():
        if c["share_fraction"] == 0:
            continue
        base = baseline[tuple(str(c[w]) for w in WORLD)]
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


def main() -> None:
    with open(RUN["targeted_csv"]) as handle:
        rows = list(csv.DictReader(handle))
    records = effects(rows)
    lines = [f"{len(records)} conditions with s > 0 (threshold {THRESHOLD})"]
    for name, n, helps, hurts, met in predictions(records):
        lines.append(f"{name}: {n} conditions, helps {helps}, hurts {hurts} -> {'MET' if met else 'NOT MET'}")
    lines.append("")
    lines.append("conditions where sharing helps:")
    for r in sorted(records, key=lambda r: -r["effect"]):
        if r["class"] == "helps":
            lines.append(f"  target {r['share_target']}, s {r['share_fraction']}, radius {r['sharing_radius']}, ratio {r['stag_to_hare_ratio']}, {r['fitness_shape']}, dispersal {r['dispersal']}: {r['baseline']:.3f} -> {r['mean']:.3f} ({r['effect']:+.3f})")
    text = "\n".join(lines)
    print(text)
    path = Path(RUN["targeted_csv"]).with_name("judge_targeted.txt")
    path.write_text(text + "\n")


if __name__ == "__main__":
    main()
