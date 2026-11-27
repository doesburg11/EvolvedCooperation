"""Registered run of rung 5a′ (rung5a_nomut/PREREGISTRATION.md): private views before mutation (mu = 0).

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a_nomut.run

Reuses rung 5a's registered runner unchanged, as the bridge does: sets its frozen globals (CONDITIONS = main at
mu = 0, SEEDS 3300-3399, DATA = rung5a_nomut/data/; b, e, q stay rung 5a's) for the duration of the call, with forked
workers inheriting them. After the runner's own validation and verdict, it applies the registered mu = 0 validity check
(no mutants or transfers in any generation) and adds the reported ALLD-extinction and DISC summaries.
"""

from __future__ import annotations

import csv
import importlib
import json
import multiprocessing
from contextlib import contextmanager
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PKG = "ecological_models.nowak_mechanisms.indirect_reciprocity.ladder"
MAIN = (0.1, 0.8, 0.1)
SEEDS = tuple(range(3300, 3400))
DATA = HERE / "data"


def settings():
    return dict(CONDITIONS={"main": (0.0, MAIN, ("test", "shuffled"))}, SEEDS=SEEDS, DATA=DATA,
                B_=3.0, E=0.1, Q=0.8)


@contextmanager
def configured(extra=None):
    mod = importlib.import_module(f"{PKG}.rung5a.run")
    names = dict(settings(), **(extra or {}))
    saved = {k: getattr(mod, k) for k in names}
    try:
        for k, v in names.items():
            setattr(mod, k, v)
        yield mod
    finally:
        for k, v in saved.items():
            setattr(mod, k, v)


def load_runs(data):
    rows, counts, audits = [], {}, {}
    for p in sorted((data / "runs").glob("*.npz")):
        if p.name.endswith(".partial.npz"):
            continue
        z = np.load(p)
        r = json.loads(str(z["row"]))
        key = (r["condition"], r["arm"], r["seed"])
        rows.append(r)
        counts[key], audits[key] = z["counts"], z["audit"]
    return rows, counts, audits


def mutation_free(rows, audits):
    """Registered mu = 0 check: no mutants or transfers in any generation, zero mutant summaries."""
    for r in rows:
        au = np.asarray(audits[(r["condition"], r["arm"], r["seed"])])
        if (au[:, 3:9] != 0).any() or r["mutants_total"] != 0 or r["mutants_max_gen"] != 0:
            return False
    return True


def extinction_and_disc(rows, counts, n, g_end, win):
    w0, w1 = win
    out, per_run = {}, []
    for arm in ("test", "shuffled"):
        ext, g500, wmean, reappear = [], [], [], 0
        for r in rows:
            if r["arm"] != arm:
                continue
            c = np.asarray(counts[(r["condition"], arm, r["seed"])]).astype(np.int64)
            zero = np.nonzero(c[:, 0] == 0)[0]
            g = int(zero[0]) if len(zero) else None
            if g is not None and (c[g:, 0] != 0).any():
                reappear += 1
            disc = (n - c[:, 0] - c[:, 1]) / n
            ext.append(g)
            g500.append(float(disc[g_end]))
            wmean.append(float(disc[w0:w1 + 1].mean()))
            per_run.append({"arm": arm, "seed": r["seed"], "alld_extinct_gen": g, "DISC_g500": g500[-1],
                            "DISC_window": wmean[-1]})
        gs = [g for g in ext if g is not None]
        out[arm] = dict(runs=len(ext), alld_extinct_runs=len(gs),
                        alld_extinct_by_500=int(sum(g <= 500 for g in gs)),
                        alld_extinct_gen_median=float(np.median(gs)) if gs else None,
                        alld_reappeared_runs=reappear,
                        mean_disc_g500=float(np.mean(g500)), mean_disc_window=float(np.mean(wmean)),
                        runs_disc_g500_ge_05=int(sum(v >= 0.5 for v in g500)),
                        runs_disc_window_ge_05=int(sum(v >= 0.5 for v in wmean)))
    return out, per_run


def main():
    if multiprocessing.get_start_method() != "fork":
        raise SystemExit("workers must be forked so they inherit the settings")
    DATA.mkdir(exist_ok=True)
    with configured() as mod:
        res = mod.main()
        n, g_end, win = mod.N, mod.G_END, mod.WIN
    rep = {"seeds": [SEEDS[0], SEEDS[-1]], "runner_verdict": res.get("verdict"), "test_joint": res.get("test_joint"),
           "shuffled_g500": res.get("shuffled_g500"), "shuffled_window": res.get("shuffled_window")}
    verdict = res.get("verdict")
    if verdict in ("MET", "NOT MET"):
        rows, counts, audits = load_runs(DATA)
        if len(rows) != 200 or not mutation_free(rows, audits):
            verdict = "NO VERDICT (mutation-free check failed or run set incomplete)"
        else:
            rep["reported"], per_run = extinction_and_disc(rows, counts, n, g_end, win)
            with open(DATA / "per_run.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(per_run[0]))
                w.writeheader()
                w.writerows(per_run)
    rep["verdict"] = verdict
    (DATA / "rung5a_nomut_summary.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1), flush=True)
    return rep


if __name__ == "__main__":
    main()
