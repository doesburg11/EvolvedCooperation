"""Registered bridge run (bridge5a/PREREGISTRATION.md): step B1 (b/c 5) or, only after a valid B1 NOT MET, step B2
(b/c 5, e 0.02, q 1).

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.bridge5a.run

STEP below selects the step (no CLI parameters, per AGENTS.md; switching to B2 is a commit). The script reuses rung
5a's registered runner unchanged: it sets that runner's frozen settings (B_, E, Q, SEEDS, CONDITIONS = main only,
DATA) for the duration of the call, runs its benchmark gate, watcher, validation and verdict, restores the settings,
and then adds the registered DISC summaries from the saved trajectories. Workers are forked (they inherit the set
values); the script refuses any other start method. Outputs go to bridge5a/data/b1/ or b2/ only; rung 5a's outputs
are untouched. A step refuses to run again once its attempt marker exists (rung 5a's runner enforces this).
"""

from __future__ import annotations

import csv
import importlib
import json
import multiprocessing
from contextlib import contextmanager
from pathlib import Path

import numpy as np

STEP = "B1"
HERE = Path(__file__).resolve().parent
PKG = "ecological_models.nowak_mechanisms.indirect_reciprocity.ladder"
MAIN = (0.1, 0.8, 0.1)
STEPS = {
    "B1": dict(B_=5.0, E=0.1, Q=0.8, SEEDS=tuple(range(3100, 3200))),
    "B2": dict(B_=5.0, E=0.02, Q=1.0, SEEDS=tuple(range(3200, 3300))),
}


def out_dir(step):
    return HERE / "data" / step.lower()


def settings(step):
    return dict(STEPS[step], CONDITIONS={"main": (0.001, MAIN, ("test", "shuffled"))}, DATA=out_dir(step))


@contextmanager
def configured(step, extra=None):
    """Set rung 5a's runner to this step's frozen settings; always restore them."""
    mod = importlib.import_module(f"{PKG}.rung5a.run")
    names = dict(settings(step), **(extra or {}))
    saved = {k: getattr(mod, k) for k in names}
    try:
        for k, v in names.items():
            setattr(mod, k, v)
        yield mod
    finally:
        for k, v in saved.items():
            setattr(mod, k, v)


def b1_not_met():
    """True only if B1's saved per-run records re-validate at B1's settings and re-give NOT MET."""
    d = out_dir("B1")
    f = d / "rung5a_summary.json"
    if not f.is_file() or json.loads(f.read_text()).get("verdict") != "NOT MET":
        return False
    with configured("B1") as mod:
        rows, counts, audits = [], {}, {}
        for p in sorted((d / "runs").glob("*.npz")):
            if p.name.endswith(".partial.npz"):
                continue
            z = np.load(p)
            r = json.loads(str(z["row"]))
            key = (r["condition"], r["arm"], r["seed"])
            rows.append(r)
            counts[key], audits[key] = z["counts"], z["audit"]
        try:
            mod.validate(rows, counts, audits)
        except ValueError:
            return False
        return mod.verdict(rows)[0] == "NOT MET"


def disc_summaries(step):
    d = out_dir(step)
    with open(d / "rung5a_runs.csv") as fh:
        rows = list(csv.DictReader(fh))
    cnt = np.load(d / "rung5a_counts.npz")
    with configured(step) as mod:
        n, g_end, (w0, w1) = mod.N, mod.G_END, mod.WIN
    out, per_run = {}, []
    for arm in ("test", "shuffled"):
        g500, win = [], []
        for r in rows:
            if r["arm"] != arm:
                continue
            c = cnt[f"main_{arm}_{r['seed']}"].astype(np.int64)
            disc = (n - c[:, 0] - c[:, 1]) / n
            g500.append(float(disc[g_end]))
            win.append(float(disc[w0:w1 + 1].mean()))
            per_run.append({"arm": arm, "seed": int(r["seed"]), "DISC_g500": g500[-1], "DISC_window": win[-1]})
        out[arm] = dict(runs=len(g500), mean_disc_g500=float(np.mean(g500)), mean_disc_window=float(np.mean(win)),
                        runs_disc_g500_ge_05=int(sum(v >= 0.5 for v in g500)),
                        runs_disc_window_ge_05=int(sum(v >= 0.5 for v in win)))
    with open(d / "disc_per_run.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["arm", "seed", "DISC_g500", "DISC_window"])
        w.writeheader()
        w.writerows(per_run)
    return out


def main(step=STEP):
    if multiprocessing.get_start_method() != "fork":
        raise SystemExit("workers must be forked so they inherit the step's settings")
    if step == "B2" and not b1_not_met():
        raise SystemExit("B2 needs a valid B1 NOT MET (bridge5a/data/b1/rung5a_summary.json)")
    out_dir(step).mkdir(parents=True, exist_ok=True)
    with configured(step) as mod:
        res = mod.main()
    summ = out_dir(step) / "bridge_summary.json"
    rep = {"step": step, "settings": {k: v for k, v in STEPS[step].items() if k != "SEEDS"},
           "seeds": [STEPS[step]["SEEDS"][0], STEPS[step]["SEEDS"][-1]], "verdict": res.get("verdict"),
           "test_joint": res.get("test_joint"), "shuffled_g500": res.get("shuffled_g500"),
           "shuffled_window": res.get("shuffled_window")}
    if res.get("verdict") in ("MET", "NOT MET"):
        rep["disc"] = disc_summaries(step)
    summ.write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1), flush=True)
    return rep


if __name__ == "__main__":
    main()
