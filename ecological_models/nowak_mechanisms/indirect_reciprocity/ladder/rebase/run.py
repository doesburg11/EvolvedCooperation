"""Registered rebase run (README.md, "Rebase to q = 0.8 and rung 4a, attempt 3"): Stage R, then Stage 4a.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rebase.run R
    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rebase.run 4a

Each stage reuses the registered runner of its rung unchanged: this script sets that runner's frozen settings
(q = 0.8, seeds 1000-1099, the registered conditions of this pre-registration) and its output folder for the duration
of the call, runs the runner's own run loop, validation and sanity verdict, restores the settings, and then applies
this pre-registration's thresholds (test >= 80/100, shuffled <= 20/100) to the counts the runner's verdict returns.
The runners' own verdict-text files (which name the old 16/20 thresholds) are not kept.

Outputs go to rebase/data/ only. Stage 4a refuses to start unless rebase/data/stage_R_summary.json shows all four rungs
met with valid data. A stage refuses to run again once its summary exists (one scientific attempt; a documented
technical repair is a separate, recorded step).
"""

from __future__ import annotations

import csv
import importlib
import json
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DATA = HERE / "data"
PKG = "ecological_models.nowak_mechanisms.indirect_reciprocity.ladder"
Q_NEW = 0.8
SEEDS = tuple(range(1000, 1100))
T_MIN, SH_MAX = 80, 20
ARMS2 = ("test", "shuffled")

# rung: (settings to set on its runner module, as {name: value})
STAGE_R = {
    "rung2": {"CONDITIONS": {"main": (Q_NEW, 0.9, ARMS2)}},
    "rung2b": {"CONDITIONS": {"main": (Q_NEW, 0.5, ARMS2)}},
    "rung3a": {"Q": Q_NEW, "CONDITIONS": {"main": (0.1, ARMS2)}},
    "rung3b": {"Q": Q_NEW, "CONDITIONS": {"main": (0.02, ARMS2)}},
}
STAGE_4A = {"Q": Q_NEW, "CONDITIONS": {
    "main": ((0.1, 0.8, 0.1), ARMS2),
    "allc5": ((0.05, 0.85, 0.1), ("test",)),
    "no_allc": ((0.0, 0.9, 0.1), ("test",)),
    "more_allc": ((0.3, 0.6, 0.1), ("test",)),
    "no_alld": ((0.2, 0.8, 0.0), ("test",)),
    "image": ((0.1, 0.8, 0.1), ("image",)),
}}
RUNG3B_FIELDS_SHARED = 12        # rung 4a's first 12 counters are rung 3b's (with no ALLC present)


def git_state():
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", str(HERE.parent.relative_to(ROOT))],
                           capture_output=True, text=True).stdout.strip()
    return commit, dirty == ""


@contextmanager
def configured(rung, settings, out_dir, seeds=SEEDS):
    """Set a registered runner's frozen settings and output folder; always restore them."""
    mod = importlib.import_module(f"{PKG}.{rung}.run")
    names = dict(settings, SEEDS=seeds, DATA=out_dir)
    saved = {k: getattr(mod, k) for k in names}
    try:
        for k, v in names.items():
            setattr(mod, k, v)
        yield mod
    finally:
        for k, v in saved.items():
            setattr(mod, k, v)


def run_rung(rung, settings, out_dir, seeds=SEEDS):
    """Run a registered runner under the given settings; return (verdict string, test count, shuffled count, rows)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with configured(rung, settings, out_dir, seeds) as mod:
        mod.main()
        rows = read_rows(out_dir / f"{rung}_runs.csv")
        v, t, sh = mod.verdict(rows)
    for txt in out_dir.glob("*_verdict.txt"):
        txt.unlink()          # names the old 16/20 thresholds; this script writes its own summary
    return v, t, sh, rows


def read_rows(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        d = {}
        for k, v in r.items():
            if k in ("condition", "arm"):
                d[k] = v
            elif k == "seed":
                d[k] = int(v)
            else:
                d[k] = float(v)
        out.append(d)
    return out


def claim_attempt(stage):
    """One scientific attempt per stage: refuse if this stage was ever started (marker or outputs present)."""
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / ("stage_R" if stage == "R" else "stage_4a")
    if out.exists() or (DATA / f"stage_{stage}_summary.json").exists():
        raise SystemExit(f"Stage {stage} was already started (outputs exist); a rerun needs a documented repair")
    try:
        with open(DATA / f"stage_{stage}.attempt", "x") as fh:
            fh.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
    except FileExistsError:
        raise SystemExit(f"Stage {stage} was already started (attempt marker exists)")


def classify(v, t, sh):
    if v.startswith("NO VERDICT") or v.startswith("INVALID"):
        return v
    return "MET" if t >= T_MIN and sh <= SH_MAX else "NOT MET"


def stage_r():
    summ_path = DATA / "stage_R_summary.json"
    commit, clean = git_state()
    if not clean:
        raise SystemExit("ladder tree not clean; commit first")
    claim_attempt("R")
    t0 = time.time()
    res = {"commit": commit, "q": Q_NEW, "seeds": [SEEDS[0], SEEDS[-1]], "thresholds": [T_MIN, SH_MAX], "rungs": {}}
    for rung, settings in STAGE_R.items():
        try:
            v, t, sh, rows = run_rung(rung, settings, DATA / "stage_R" / rung)
        except Exception as exc:                       # recorded, not hidden: the stage has no verdict
            v, t, sh, rows = f"NO VERDICT (exception: {exc!r})", None, None, []
        res["rungs"][rung] = {"runner_verdict": v, "test": t, "shuffled": sh, "verdict": classify(v, t, sh),
                              "runs": len(rows)}
        print(f"{rung}: test {t}/100, shuffled {sh}/100 -> {res['rungs'][rung]['verdict']} ({v})", flush=True)
    res["passes"] = all(x["verdict"] == "MET" for x in res["rungs"].values())
    res["seconds"] = time.time() - t0
    summ_path.write_text(json.dumps(res, indent=1))
    print("STAGE R", "PASSES" if res["passes"] else "DOES NOT PASS")
    return res


def replay_check(rows4a):
    """The no-ALLC condition must replay Stage R's rung-3b test runs exactly (trajectories and shared counters)."""
    traj4 = np.load(DATA / "stage_4a" / "rung4a_traj.npz")
    traj3 = np.load(DATA / "stage_R" / "rung3b" / "rung3b_traj.npz")
    rows3 = {r["seed"]: r for r in read_rows(DATA / "stage_R" / "rung3b" / "rung3b_runs.csv")
             if r["condition"] == "main" and r["arm"] == "test"}
    m3 = importlib.import_module(f"{PKG}.rung3b.run")
    m4 = importlib.import_module(f"{PKG}.rung4a.run")
    shared = m3.FIELDS[:RUNG3B_FIELDS_SHARED]
    assert tuple(m4.FIELDS[:RUNG3B_FIELDS_SHARED]) == tuple(shared)
    bad = []
    for r in rows4a:
        if r["condition"] != "no_allc":
            continue
        s = r["seed"]
        a4 = traj4[f"no_allc_test_{s}"]             # shares per generation [ALLD, ALLC, DISC]
        a3 = traj3[f"main_test_{s}"]                # DISC share per generation (rung 3b)
        # exact in integer counts (N = 1000): ALLD, ALLC (none) and DISC in every generation
        same = (a4.shape[0] == a3.shape[0]
                and np.array_equal(np.round(a4[:, 0] * 1000), np.round((1.0 - a3) * 1000))
                and np.array_equal(np.round(a4[:, 2] * 1000), np.round(a3 * 1000))
                and bool((a4[:, 1] == 0).all()))
        same = same and all(r[f] == rows3[s][f] and r["g1_" + f] == rows3[s]["g1_" + f] for f in shared)
        if not same:
            bad.append(s)
    return bad


def descriptives(rows):
    coop = lambda r: r["final_allc"] + r["final_disc"]

    def ratio(rr, num, den):
        d = sum(r[den] for r in rr)
        return float(sum(r[num] for r in rr) / d) if d else None

    out = {}
    for c, (start, arms) in STAGE_4A["CONDITIONS"].items():
        for arm in arms:
            rr = [r for r in rows if r["condition"] == c and r["arm"] == arm]
            out[f"{c}_{arm}"] = dict(
                at_endpoint=int(sum(coop(r) >= 0.8 - 1e-12 for r in rr)), runs=len(rr),
                mean_final_allc=float(np.mean([r["final_allc"] for r in rr])),
                mean_final_disc=float(np.mean([r["final_disc"] for r in rr])),
                mean_final_alld=float(np.mean([r["final_alld"] for r in rr])),
                mean_max_alld=float(np.mean([r["max_alld"] for r in rr])),
                help_rate_g1=ratio(rr, "g1_helps", "g1_encounters"),
                help_rate_pooled=ratio(rr, "helps", "encounters"),
                g1_good_share_consulted_allc=ratio(rr, "g1_consult_allc_good", "g1_consult_allc"),
                g1_good_share_consulted_disc=ratio(rr, "g1_consult_disc_good", "g1_consult_disc"),
                g1_good_share_consulted_alld=ratio(rr, "g1_consult_alld_good", "g1_consult_alld"))
    return out


def stage_4a():
    summ_path = DATA / "stage_4a_summary.json"
    r_path = DATA / "stage_R_summary.json"
    rs = json.loads(r_path.read_text()) if r_path.exists() else {}
    if rs.get("passes") is not True or set(rs.get("rungs", {})) != set(STAGE_R) or \
            any(x.get("verdict") != "MET" for x in rs["rungs"].values()):
        raise SystemExit("Stage R has not passed with valid data; Stage 4a not started")
    commit, clean = git_state()
    if not clean:
        raise SystemExit("ladder tree not clean; commit first")
    claim_attempt("4a")
    t0 = time.time()
    res = {"commit": commit, "q": Q_NEW, "seeds": [SEEDS[0], SEEDS[-1]], "thresholds": [T_MIN, SH_MAX]}
    try:
        v, t, sh, rows = run_rung("rung4a", STAGE_4A, DATA / "stage_4a")
    except Exception as exc:
        v, t, sh, rows = f"NO VERDICT (exception: {exc!r})", None, None, []
    verdict = classify(v, t, sh)
    bad_replay = None
    if not verdict.startswith(("NO VERDICT", "INVALID")):       # inherited verdict first; replay only on valid data
        try:
            bad_replay = replay_check(rows)
        except Exception as exc:
            bad_replay = [f"replay check failed: {exc!r}"]
        if bad_replay:
            verdict = f"NO VERDICT (no-ALLC runs do not replay Stage R rung 3b: {bad_replay[:5]})"
    res.update(runner_verdict=v, test=t, shuffled=sh, replay_mismatch=bad_replay, verdict=verdict, runs=len(rows),
               seconds=time.time() - t0,
               reported=descriptives(rows) if not verdict.startswith(("NO VERDICT", "INVALID")) else None)
    summ_path.write_text(json.dumps(res, indent=1))
    print(f"rung 4a attempt 3: test {t}/100, shuffled {sh}/100 -> {verdict} ({v})")
    return res


if __name__ == "__main__":
    {"R": stage_r, "4a": stage_4a}[sys.argv[1]]()
