"""README "Targeted sharing" and "Riskier stags": classifies each s > 0
condition of a targeted sweep's CSV as helps / hurts / neither against s = 0
in the same world, and prints the pre-registered predictions (P1-P3, or
R1-R3 with the argument lowq, or T1-T3 and the threshold ratios with the
argument threshold). Refuses incomplete or duplicated data."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..config.stag_hunt_sharing_config import RUN, SWEEP_TARGETED, SWEEP_TARGETED_LOWQ, SWEEP_THRESHOLD
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


def thresholds(records: list[dict[str, Any]], ratios: list[float]) -> dict[tuple[float, str], float | None]:
    """Per (q, fitness shape): the smallest ratio r in the sweep such that
    sharing helps in at least one condition (s, dispersal) at r and at every
    larger swept ratio; None if it does not help at the largest ratio."""
    out = {}
    for q in sorted({float(r["stag_success_probability"]) for r in records}):
        for shape in sorted({r["fitness_shape"] for r in records}):
            helped = {
                ratio: any(
                    r["class"] == "helps"
                    for r in records
                    if float(r["stag_success_probability"]) == q
                    and r["fitness_shape"] == shape
                    and float(r["stag_to_hare_ratio"]) == ratio
                )
                for ratio in ratios
            }
            threshold = None
            for ratio in sorted(ratios, reverse=True):
                if not helped[ratio]:
                    break
                threshold = ratio
            out[(q, shape)] = threshold
    return out


def predictions_threshold(records: list[dict[str, Any]], ratios: list[float]) -> list[tuple[str, int, int, int, bool]]:
    """(name, conditions, helps, hurts, met) for T1-T3 (README, "Payoff
    threshold"); for T3 the counts are over the 3 diminishing thresholds."""
    dim = [r for r in records if r["fitness_shape"] == "diminishing"]
    t1 = [r for r in dim if float(r["stag_to_hare_ratio"]) == 1.0]
    t2 = [r for r in dim if float(r["stag_to_hare_ratio"]) == 1.5]
    out = []
    for name, group, met in (
        ("T1 diminishing, ratio 1: helps in none", t1, lambda h, x: h == 0),
        ("T2 diminishing, ratio 1.5: helps at every q", t2, None),
    ):
        helps = sum(r["class"] == "helps" for r in group)
        hurts = sum(r["class"] == "hurts" for r in group)
        if met is None:
            qs = {float(r["stag_success_probability"]) for r in group}
            ok = all(any(r["class"] == "helps" for r in group if float(r["stag_success_probability"]) == q) for q in qs)
        else:
            ok = met(helps, hurts)
        out.append((name, len(group), helps, hurts, ok))
    found = {k: v for k, v in thresholds(records, ratios).items() if k[1] == "diminishing"}
    inside = sum(v is not None and 1.1 <= v <= 1.5 for v in found.values())
    out.append(("T3 diminishing: threshold in [1.1, 1.5] at every q", len(found), inside, len(found) - inside, inside == len(found)))
    return out


def main() -> None:
    import sys

    if len(sys.argv) > 2:
        raise SystemExit("usage: ... judge_targeted [lowq | threshold]")
    mode = sys.argv[1] if sys.argv[1:] else ""
    if mode not in ("", "lowq", "threshold"):
        raise SystemExit("usage: ... judge_targeted [lowq | threshold]")
    sweep, csv_path, name = {
        "": (SWEEP_TARGETED, RUN["targeted_csv"], "judge_targeted.txt"),
        "lowq": (SWEEP_TARGETED_LOWQ, RUN["targeted_lowq_csv"], "judge_targeted_lowq.txt"),
        "threshold": (SWEEP_THRESHOLD, RUN["threshold_csv"], "judge_threshold.txt"),
    }[mode]
    with open(csv_path) as handle:
        rows = list(csv.DictReader(handle))
    records = effects(rows, sweep)
    ratios = [float(r) for r in sweep["stag_to_hare_ratio"]]
    judged = {"": predictions, "lowq": predictions_lowq}.get(mode) or (lambda rs: predictions_threshold(rs, ratios))
    lines = [f"{len(records)} conditions with s > 0 (threshold {THRESHOLD})"]
    for name_, n, helps, hurts, met in judged(records):
        lines.append(f"{name_}: {n} conditions, helps {helps}, hurts {hurts} -> {'MET' if met else 'NOT MET'}")
    if mode == "threshold":
        lines.append("")
        lines.append("threshold ratio (smallest swept ratio from which sharing helps at it and every larger one):")
        for (q, shape), value in thresholds(records, ratios).items():
            lines.append(f"  q {q}, {shape}: {value if value is not None else 'none in the sweep'}")
    lines.append("")
    lines.append("conditions where sharing helps:")
    for r in sorted(records, key=lambda r: -r["effect"]):
        if r["class"] == "helps":
            q = f"q {r['stag_success_probability']}, " if "stag_success_probability" in r else ""
            lines.append(f"  target {r['share_target']}, s {r['share_fraction']}, radius {r.get('sharing_radius', 1)}, {q}ratio {r['stag_to_hare_ratio']}, {r['fitness_shape']}, dispersal {r['dispersal']}: {r['baseline']:.3f} -> {r['mean']:.3f} ({r['effect']:+.3f})")
    text = "\n".join(lines)
    print(text)
    path = Path(csv_path).with_name(name)
    path.write_text(text + "\n")


if __name__ == "__main__":
    main()
