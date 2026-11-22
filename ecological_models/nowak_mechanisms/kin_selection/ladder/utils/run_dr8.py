#!/usr/bin/env python3
"""Diagnostic DR8 (README pre-registration): are high helpers blocked by a full neighbourhood in R8 attempt 2?

Wraps BuddingEngine.claims on each engine to record, per update in the window, would-be breeders (claimants before
the vacancy requirement) by helper class (h above vs at/below the occupied mean): blocked (no vacant grid neighbour),
births, and the own-offspring share of their occupied surviving grid neighbours. No random draws are added, so runs
reproduce r8_main_runs.csv exactly (checked). Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_dr8
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_dr8")

from ..config.ladder_config import DATA_DIR, R8_MAIN_SEEDS, R8_MAIN_STEPS, R8_WINDOW_FROM, WORKERS, r8_arms, run_config
from ..ladder_model import make_engine
from .run_r1 import json_safe

ARMS = ("U2-6-local", "U2-6-global")
KEYS = ("wb", "blocked", "births", "nb_occ", "nb_own")


def class_stats(eng, claimant, vacant, h_mean):
    """Per class (high, low): would-be breeders, blocked, occupied surviving neighbours, own offspring among them."""
    out = {}
    survive = ~vacant
    for cls, mask in (("high", claimant & (eng.h > h_mean)), ("low", claimant & (eng.h <= h_mean))):
        idx = np.nonzero(mask)[0]
        blocked = nb_occ = nb_own = 0
        for i in idx:
            nb = eng.grid_nb[i]
            if eng.dispersal == "global":
                blocked += int(not vacant.any())
            else:
                blocked += int(not vacant[nb].any())
            occ_nb = nb[survive[nb]]
            nb_occ += len(occ_nb)
            nb_own += int((eng.parent_ids[occ_nb] == eng.ids[i]).sum())
        out[cls] = {"wb": len(idx), "blocked": blocked, "nb_occ": nb_occ, "nb_own": nb_own, "mask": mask}
    return out


def run_one(job):
    arm, mech, updates, seed, steps, window_from = job
    mech = dict(mech)
    eng = make_engine(run_config(seed, updates, steps), replacement=mech.pop("replacement"),
                      death=mech.pop("death"), **mech)
    sums = {c: {k: 0 for k in KEYS} for c in ("high", "low")}
    rec = {}
    real_claims = eng.claims

    def claims(claimant, vacant):
        rec["stats"] = class_stats(eng, claimant, vacant, rec["h_mean"])
        return real_claims(claimant, vacant)
    eng.claims = claims
    with contextlib.redirect_stdout(io.StringIO()):
        while eng.step_index < steps:
            start = eng.step_index
            rec["h_mean"] = float(eng.h[eng.occ].mean()) if eng.occ.any() else 0.0
            rec.pop("stats", None)
            eng.step()
            if start >= window_from and "stats" in rec:
                parents = eng.last_birth_parents
                for c, st in rec["stats"].items():
                    for k in ("wb", "blocked", "nb_occ", "nb_own"):
                        sums[c][k] += st[k]
                    sums[c]["births"] += int(st["mask"][parents].sum()) if len(parents) else 0
    return {"arm": arm, "seed": seed, "final_mean_trait": eng.occupied_mean_h(),
            "final_occupancy": float(eng.occ.mean()), "steps_done": eng.step_index,
            **{f"{c}_{k}": v for c, d in sums.items() for k, v in d.items()}}


def rates(r, c):
    wb = r[f"{c}_wb"]
    return {"blocked": r[f"{c}_blocked"] / wb if wb else None, "births": r[f"{c}_births"] / wb if wb else None,
            "own_share": r[f"{c}_nb_own"] / r[f"{c}_nb_occ"] if r[f"{c}_nb_occ"] else None, "wb": wb}


def reading(rows):
    deltas, excluded = [], 0
    for r in rows:
        hi, lo = rates(r, "high"), rates(r, "low")
        if hi["blocked"] is None or lo["blocked"] is None:
            excluded += 1
            continue
        deltas.append(hi["blocked"] - lo["blocked"])
    pos = sum(d > 0 for d in deltas)
    label = ("high helpers more often blocked" if pos >= 15 else "not supported" if pos <= 5 else "unclear")
    return {"label": label, "seeds_delta_positive": pos, "seeds_used": len(deltas), "seeds_excluded": excluded,
            "deltas": deltas}


def paired_count(hi, lo, key, better):
    """Seeds where the high class compares as `better` on `key`, with the numbers used and excluded."""
    used = [(x[key], y[key]) for x, y in zip(hi, lo) if x[key] is not None and y[key] is not None]
    return {"count": sum(1 for a, b in used if better(a, b)), "used": len(used), "excluded": len(hi) - len(used)}


def summarize(rows) -> dict:
    out = {}
    for a in ARMS:
        v = [r for r in rows if r["arm"] == a]
        pooled = {c: rates({k: sum(r[k] for r in v) for k in v[0] if k.startswith(c + "_")}, c)
                  for c in ("high", "low")}
        hi = [rates(r, "high") for r in v]
        lo = [rates(r, "low") for r in v]
        out[a] = {"pooled": pooled,
                  "per_seed": {int(r["seed"]): {"high": x, "low": y} for r, x, y in zip(v, hi, lo)},
                  "births_lower_for_high": paired_count(hi, lo, "births", lambda p, q: p < q),
                  "own_share_higher_for_high": paired_count(hi, lo, "own_share", lambda p, q: p > q)}
        if a == "U2-6-local":
            out[a]["reading"] = reading(v)
    return out


def check_stored(rows, out: Path):
    with open(out / "r8_main_runs.csv") as f:
        stored = {(r["arm"], int(r["seed"])): r for r in csv.DictReader(f)}
    bad = []
    for r in rows:
        s = stored.get((r["arm"], int(r["seed"])))
        if s is None or float(s["final_mean_trait"]) != r["final_mean_trait"] \
                or float(s["final_occupancy"]) != r["final_occupancy"]:
            bad.append((r["arm"], r["seed"]))
    return bad


def main():
    out = Path(DATA_DIR)
    arms = r8_arms(2, 0.2, 0.5)
    jobs = [(a, *arms[a], s, R8_MAIN_STEPS, R8_WINDOW_FROM) for a in ARMS for s in R8_MAIN_SEEDS]
    with Pool(WORKERS) as pool:
        rows = pool.map(run_one, jobs)
    bad = check_stored(rows, out)
    valid = not bad and all(r["steps_done"] == R8_MAIN_STEPS for r in rows)
    verdict = {"valid": valid, "mismatches": bad}
    if valid:
        verdict.update(summarize(rows))
    (out / "dr8_verdict.json").write_text(json.dumps(json_safe(verdict), indent=1, allow_nan=False))
    print(json.dumps(json_safe({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items()
                                                                       if kk != "per_seed"})
                                for k, v in verdict.items()}), indent=1))


if __name__ == "__main__":
    main()
