#!/usr/bin/env python3
"""Shuffle experiment: Experiment 104 x shuffle_fraction x colour rule (rules: README, pre-registered in 9343482).

Run from the repo root:
  ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_shuffle
Writes data/shuffle/runs.csv, lineage.csv, interaction.csv and summary.json.
"""
from __future__ import annotations

import csv
import json
import math
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy import stats

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.ethnocentrism.utils.run_shuffle")

from ..config.ethnocentrism_config import (
    DATA_DIR, RANDOM_COLOUR_BASE, RANDOM_COLOUR_DIR, SHUF_ALPHA, SHUF_H1_MIN_DROP, SHUF_H2_MIN_RISE,
    SHUF_MIN_EXCESS_DROP, SHUF_N, SHUFFLE_CELLS, SHUFFLE_DIR, WORKERS, run_config,
)
from ..ethnocentrism_model import CODE_CC, CODE_CD, CODE_DC, CODE_DD, Ethnocentrism
from .run_random_colour import clean, stats_of
from .run_viscosity import nan_if_none, replays

COOP, EGOIST = "last100coop-percent", "dd-percent"
DESCRIBE_REPORTERS = ["cc-percent", "cd-percent", "dc-percent", "dd-percent", COOP, "last100meetown-percent"]
DESCRIBE_LINEAGE = ["population", "n_founders_alive", "all_frac_same_founder", "same_frac_same_founder",
                    "diff_frac_same_founder", "all_frac_gen_le2", "all_tmrca_median", "all_r_reg_cs", "all_r_reg_cd"]
CODES = {"altruist": CODE_CC, "ethnocentric": CODE_CD, "cosmopolitan": CODE_DC, "egoist": CODE_DD}
TICKS = run_config(RANDOM_COLOUR_BASE)["ticks"]


def one(job: tuple[str, int]) -> dict:
    """One run; any failure is returned as an error record (the batch is then invalid), never raised."""
    cell, seed = job
    colour, f, _ = SHUFFLE_CELLS[cell]
    try:
        cfg = {**run_config(RANDOM_COLOUR_BASE), "colour_inheritance": colour, "shuffle_fraction": f}
        return {"cell": cell, "colour": colour, "shuffle_fraction": f, "seed": seed, **Ethnocentrism(cfg, seed).run()}
    except Exception as e:                                   # noqa: BLE001 - recorded, makes the batch invalid
        return {"cell": cell, "seed": seed, "error": repr(e)}


KIN_KEYS = ("pairs", "same_founder", "expected_weighted", "ticks_with_pairs", "ticks")
INT_KEYS = ("population", "births_total", "offspring_total", "dispersed_total", "last100_meetings",
            "last100_agent_ticks", "last100_egoist_ticks")


def _is_int(x) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, bool)


def well_formed(r: dict, reporter_keys: set[str]) -> bool:
    """A complete, internally consistent run record (finiteness of endpoints is judged per hypothesis)."""
    try:
        if "error" in r or r["cell"] not in SHUFFLE_CELLS:
            return False
        colour, f, seeds = SHUFFLE_CELLS[r["cell"]]
        if r["colour"] != colour or r["shuffle_fraction"] != f or r["seed"] not in seeds:
            return False
        if set(r["reporters"]) != reporter_keys or not all(isinstance(v, (float, int)) for v in r["reporters"].values()):
            return False
        if not all(_is_int(r[x]) and r[x] >= 0 for x in INT_KEYS):
            return False
        every = run_config(RANDOM_COLOUR_BASE)["lineage_sample_every"]
        lin = r["lineage"]
        if [s["tick"] for s in lin] != list(range(every, TICKS + 1, every)):
            return False
        if any(set(s) != set(lin[0]) for s in lin) or not set(DESCRIBE_LINEAGE) <= set(lin[0]):
            return False
        if not all(isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)
                   for smp in lin for v in smp.values()):
            return False
        k = r["interaction_kinship"]
        if set(k) != set(KIN_KEYS) or k["ticks"] != 100 or not 0 <= k["ticks_with_pairs"] <= 100:
            return False
        if not (_is_int(k["pairs"]) and _is_int(k["same_founder"]) and _is_int(k["ticks_with_pairs"])
                and 0 <= k["same_founder"] <= k["pairs"] and k["ticks_with_pairs"] <= k["pairs"]
                and math.isfinite(k["expected_weighted"]) and 0 <= k["expected_weighted"] <= k["pairs"]
                and r["last100_meetings"] == 2 * k["pairs"]):      # every unordered pair meets in both directions
            return False
        by = np.asarray(r["last100_meetings_by_code"])
        if by.shape != (4, 2) or not np.issubdtype(by.dtype, np.integer) or (by < 0).any() \
                or (by[:, 1] > by[:, 0]).any() or int(by[:, 0].sum()) != r["last100_meetings"]:
            return False
        return r["last100_egoist_ticks"] <= r["last100_agent_ticks"]
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return False


def batch_ok(res: list[dict], reporter_keys: set[str]) -> bool:
    """Exactly one well-formed result for every registered (cell, seed), nothing else."""
    want = sorted((c, s) for c, (_, _, seeds) in SHUFFLE_CELLS.items() for s in seeds)
    try:
        got = sorted((str(r.get("cell")), int(r.get("seed", -1))) for r in res)
    except (TypeError, ValueError, AttributeError):
        return False
    return bool(reporter_keys) and got == want and all(well_formed(r, reporter_keys) for r in res)


def validate(res: list[dict], random_csv: Path, port_csv: Path) -> tuple[bool, bool]:
    """(batch_ok, replay_ok); any problem reading the replay files counts as not ok (fails closed)."""
    try:
        headers = []
        for path in (random_csv, port_csv):
            with open(path) as fh:
                headers.append(next(csv.reader(fh)))
        if any(len(h) != len(set(h)) for h in headers):      # duplicate columns would hide values in DictReader
            return False, False
        reporter_keys = set(headers[0]) - {"condition", "seed", "population", "births_total"}
        if reporter_keys != set(headers[1]) - {"experiment", "seed", "population", "births_total"}:
            return False, False
    except (OSError, StopIteration, csv.Error, UnicodeDecodeError):
        return False, False                                   # a missing or unreadable replay file: batch invalid
    valid = batch_ok(res, reporter_keys)
    if not valid:
        return False, False
    cells = {c: [r for r in res if r["cell"] == c] for c in SHUFFLE_CELLS}
    try:
        replay = (replays(cells["R0"], random_csv, "condition", "random")
                  and replays(cells["I0"], port_csv, "experiment", RANDOM_COLOUR_BASE))
    except (OSError, KeyError, ValueError, TypeError, csv.Error, UnicodeDecodeError):
        replay = False
    return True, bool(replay)


def excess_of(r: dict) -> float:
    """Pooled (pair-weighted) observed minus random-mixing founder sharing among interacting pairs, last 100 ticks."""
    k = r.get("interaction_kinship") or {}
    if k.get("ticks_with_pairs", 0) < 100 or k.get("pairs", 0) <= 0:
        return math.nan
    return k["same_founder"] / k["pairs"] - k["expected_weighted"] / k["pairs"]


def coop_of(r: dict) -> float:
    return float(r["reporters"][COOP]) if r.get("last100_meetings", 0) > 0 else math.nan


def egoist_of(r: dict) -> float:
    """Registered H2 ratio from raw counts: egoist agent-ticks / all agent-ticks, last 100 ticks (NetLogo's
    dd-percent floors its denominator at 1 and is kept unchanged only for the replay)."""
    n = r.get("last100_agent_ticks", 0)
    return r["last100_egoist_ticks"] / n if n > 0 else math.nan


def compare(a: np.ndarray, b: np.ndarray, min_diff: float, n: int = SHUF_N) -> dict:
    """mean(a) - mean(b) >= min_diff and two-sided Welch p < SHUF_ALPHA. Undefined input -> valid False."""
    valid = a.size == n and b.size == n and n > 1 and bool(np.isfinite(a).all() and np.isfinite(b).all())
    se = math.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size) if valid else math.nan
    valid = valid and math.isfinite(se) and se > 1e-12
    diff = float(a.mean() - b.mean()) if valid else math.nan
    p = float(stats.ttest_ind(a, b, equal_var=False).pvalue) if valid else math.nan
    valid = valid and math.isfinite(p)
    return {"diff": diff, "p": p, "valid": valid,
            "criterion_met": bool(valid and diff >= min_diff - 1e-9 and p < SHUF_ALPHA)}


def judge(cells: dict[str, list[dict]], batch_valid: bool, replay_ok: bool) -> dict:
    """Pre-registered verdicts; every undefined or unexpected input gives 'invalid' (fails closed)."""
    if not batch_valid:                                       # nothing is extracted from an invalid batch
        v = "invalid: missing, duplicate, failed or malformed results"
        return {"batch_ok": False, "replay_ok": replay_ok, "manipulation": {"valid": False, "ok": False},
                **{n: {"valid": False, "criterion_met": False, "verdict": v, "met": False} for n in ("H1", "H2")}}
    def arr(c, f):
        try:
            return np.array([f(r) for r in cells.get(c, [])], dtype=float)
        except (KeyError, TypeError, ValueError, ZeroDivisionError, AttributeError):
            return np.array([math.nan])                       # wrong size and non-finite: invalid downstream
    e0, e1 = arr("R0", excess_of), arr("R1", excess_of)
    m_valid = e0.size == SHUF_N and e1.size == SHUF_N and bool(np.isfinite(e0).all() and np.isfinite(e1).all())
    drop = float(e0.mean() - e1.mean()) if m_valid else math.nan
    manip = {"excess_R0": float(e0.mean()) if m_valid else math.nan,
             "excess_R1": float(e1.mean()) if m_valid else math.nan,
             "drop": drop, "valid": m_valid, "ok": bool(m_valid and drop >= SHUF_MIN_EXCESS_DROP - 1e-9)}
    out: dict = {"batch_ok": batch_valid, "replay_ok": replay_ok, "manipulation": manip}
    tests = {"H1": compare(arr("R0", coop_of), arr("R1", coop_of), SHUF_H1_MIN_DROP),      # R0 - R1
             "H2": compare(arr("R1", egoist_of), arr("R0", egoist_of), SHUF_H2_MIN_RISE)}  # R1 - R0
    for name, h in tests.items():
        if not batch_valid:
            v = "invalid: missing, duplicate, failed or malformed results"
        elif not replay_ok:
            v = "invalid: f = 0 cells do not replay the committed runs"
        elif not manip["valid"]:
            v = "invalid: manipulation check undefined"
        elif not manip["ok"]:
            v = "invalid: manipulation check failed"
        elif not h["valid"]:
            v = "invalid: endpoint undefined, wrong number of runs or no standard error"
        else:
            v = f"{name} met" if h["criterion_met"] else f"{name} not met"
        out[name] = {**h, "verdict": v, "met": v == f"{name} met"}
    return out


def meeting_mix(rs: list[dict]) -> dict:
    """Last 100 ticks: donor strategy shares among meetings, own-colour share within each, and the help rates."""
    by = np.array([r["last100_meetings_by_code"] for r in rs], dtype=float)       # run x code x (meet, own)
    out = {}
    tot = by[:, :, 0].sum(axis=1)
    share = {n: np.where(tot > 0, by[:, c, 0] / np.maximum(tot, 1), np.nan) for n, c in CODES.items()}
    own = {n: np.where(by[:, c, 0] > 0, by[:, c, 1] / np.maximum(by[:, c, 0], 1), np.nan) for n, c in CODES.items()}
    for n in CODES:
        out[f"meeting_share_{n}"] = stats_of(share[n].tolist())
        out[f"own_colour_within_{n}"] = stats_of(own[n].tolist())
    helped = by[:, CODE_CC, 0] + by[:, CODE_CD, 1] + (by[:, CODE_DC, 0] - by[:, CODE_DC, 1])
    implied = np.where(tot > 0, helped / np.maximum(tot, 1), np.nan)
    reference = share["altruist"] + 0.25 * share["ethnocentric"] + 0.75 * share["cosmopolitan"]
    out["help_rate_implied"] = stats_of(implied.tolist())               # equals the cooperation reporter
    out["help_rate_reference_25pct"] = stats_of(reference.tolist())     # if 25% of each strategy's meetings were own colour
    return out


def main() -> None:
    out_dir = Path(SHUFFLE_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(c, s) for c, (_, _, seeds) in SHUFFLE_CELLS.items() for s in seeds]
    with Pool(WORKERS) as pool:
        res = pool.map(one, jobs, chunksize=1)

    valid, replay_ok = validate(res, Path(RANDOM_COLOUR_DIR) / "runs.csv", Path(DATA_DIR) / "runs.csv")
    cells = {c: [r for r in res if r.get("cell") == c] for c in SHUFFLE_CELLS}
    summary = judge(cells, valid, replay_ok)
    summary["errors"] = [r for r in res if "error" in r]
    json.dump(clean(summary), open(out_dir / "summary.json", "w"), indent=1, allow_nan=False)   # verdicts first
    if not valid:
        print(json.dumps(clean(summary), indent=1))
        return                                                # no descriptive output from an invalid batch

    good = res
    if good:
        keys = list(good[0]["reporters"])
        with open(out_dir / "runs.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["cell", "colour", "shuffle_fraction", "seed", "population", "births_total", *keys])
            for r in good:
                w.writerow([r["cell"], r["colour"], r["shuffle_fraction"], r["seed"], r["population"], r["births_total"],
                            *[r["reporters"].get(k, "") for k in keys]])
        lkeys = sorted({k for r in good for s in r["lineage"] for k in s})
        with open(out_dir / "lineage.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["cell", "seed", *lkeys])
            for r in good:
                for s in r["lineage"]:
                    w.writerow([r["cell"], r["seed"], *[s.get(k, "") for k in lkeys]])
        with open(out_dir / "interaction.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["cell", "seed", "pairs", "same_founder", "expected_weighted", "ticks_with_pairs", "excess",
                        "last100_meetings", "last100_agent_ticks",
                        *[f"{n}_{x}" for n in CODES for x in ("meetings", "own_colour")]])
            for r in good:
                k = r["interaction_kinship"]
                w.writerow([r["cell"], r["seed"], k["pairs"], k["same_founder"], k["expected_weighted"],
                            k["ticks_with_pairs"], excess_of(r), r["last100_meetings"], r["last100_agent_ticks"],
                            *[r["last100_meetings_by_code"][c][i] for c in CODES.values() for i in (0, 1)]])
        summary["describe"] = {}
        for c, rs in cells.items():
            k = [r["interaction_kinship"] for r in rs]
            summary["describe"][c] = {
                **{m: stats_of([coop_of(r) if m == COOP else egoist_of(r) if m == EGOIST else r["reporters"][m]
                                for r in rs]) for m in DESCRIBE_REPORTERS},
                **{m: stats_of([nan_if_none(r["lineage"][-1].get(m)) for r in rs]) for m in DESCRIBE_LINEAGE},
                "offspring_per_tick": stats_of([r["offspring_total"] / TICKS for r in rs]),
                "interacting_same_founder": stats_of([x["same_founder"] / x["pairs"] if x["pairs"] else math.nan
                                                      for x in k]),
                "interacting_expected_random_mixing": stats_of([x["expected_weighted"] / x["pairs"] if x["pairs"]
                                                                else math.nan for x in k]),
                "interacting_excess": stats_of([excess_of(r) for r in rs]),
                **meeting_mix(rs)}
    summary = clean(summary)
    json.dump(summary, open(out_dir / "summary.json", "w"), indent=1, allow_nan=False)
    print(json.dumps({k: v for k, v in summary.items() if k != "describe"}, indent=1))
    show = ["cd-percent", "cc-percent", "dc-percent", "dd-percent", COOP, "population", "interacting_excess",
            "all_frac_same_founder", "all_r_reg_cs", "help_rate_reference_25pct"]
    print(f"{'cell':8}" + "".join(f"{m[:12]:>13}" for m in show))
    for name, d in summary.get("describe", {}).items():
        print(f"{name:8}" + "".join(f"{(d[m]['mean'] if d[m]['mean'] is not None else float('nan')):13.3f}"
                                    for m in show))


if __name__ == "__main__":
    main()
