"""Analysis for PREREG_KIN_TEST.md.

Usage: python -m ecological_models.density_dependent_dispersal.analyze_test {V|M}

Measures (as in the authors' notebook): zbar = mean over the last 1000 generations of the per-generation population
mean of z; A = zbar / (1 - zbar); d = (sum over the last 1000 generations of per-patch attempts / survivors) /
(number of such patch-generation rows). Cost share = sum of z over juveniles helping at a net direct cost / sum of
z over all juveniles, pooled over generations 1..G and over the last 1000 generations.
Summaries are written to data/stage_{v,m}_summary.json (committed; KG_DATA overrides for smoke tests).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from ecological_models.density_dependent_dispersal.run_test import DATA, G, jobs, model_sha, stage_dir, validate

HERE = Path(__file__).resolve().parent
LAST = int(__import__("os").environ.get("KG_LAST", 1000))
ORIG_SUMMARY = Path.home() / "simulation_results/kanwal_gardner_viscosity/full_grid/analysis_summary.json"


def measure(job):
    path = stage_dir(job["stage"]) / f"{job['name']}.npz"
    meta = validate(path, job, model_sha())
    with np.load(path) as f:
        z = f["z"].astype(float)
        d_sum = f["d_sum"].astype(float)
        d_rows = f["d_rows"].astype(float)
        cost_z = f["cost_z"].astype(float)
        total_z = f["total_z"].astype(float)
        empty = f["empty"].astype(float)
    zbar = float(z[-LAST:].mean())
    return dict(commit=meta["commit"], name=job["name"], arm=job["arm"], n=job["n"], c=job["c"], seed=job["seed"], zbar=zbar,
                A=zbar / (1 - zbar), d=float(d_sum[-LAST:].sum() / d_rows[-LAST:].sum()),
                cost_share_all=float(cost_z[1:].sum() / total_z[1:].sum()),
                cost_share_last=float(cost_z[-LAST:].sum() / total_z[-LAST:].sum()),
                zbar_first_half=float(z[-LAST:-LAST // 2].mean()), zbar_second_half=float(z[-LAST // 2:].mean()),
                empty_refills=int(np.nansum(empty[1:])), wall_h=meta["wall_s"] / 3600,
                z_every_1000=[float(x) for x in z[::1000].round(4)])


def stage_v():
    rows = {(r["n"], r["c"]): r for r in (measure(j) for j in jobs("V"))}
    assert len(rows) == 25
    orig = {(r["n"], r["c"]): r for r in json.load(open(ORIG_SUMMARY))["runs"]}
    assert len(orig) == 25
    out = []
    for key in sorted(rows):
        r, o = rows[key], orig[key]
        out.append(dict(n=key[0], c=key[1], A_port=r["A"], A_orig=float(o["A"]), A_diff=r["A"] - float(o["A"]),
                        d_port=r["d"], d_orig=float(o["d"]), d_diff=r["d"] - float(o["d"]),
                        empty_refills=r["empty_refills"]))
    multi = [x for x in out if x["n"] > 1]
    above = int(sum(x["A_port"] > 1 / x["n"] for x in multi))
    import pandas as pd
    import statsmodels.formula.api as smf
    df = pd.DataFrame([dict(A=x["A_port"], d=x["d_port"], n=x["n"]) for x in multi])
    assert np.isfinite(df.to_numpy()).all()
    fit = smf.mixedlm("A ~ d", df, groups=df["n"]).fit()
    slope = float(fit.params["d"])
    a_within = int(sum(abs(x["A_diff"]) <= 0.03 for x in out))
    d_within = int(sum(abs(x["d_diff"]) <= 0.03 for x in out))
    a_max = float(max(abs(x["A_diff"]) for x in out))
    passes = bool(above == 20 and fit.converged and slope < 0 and a_within >= 23 and a_max <= 0.06
                  and d_within >= 23)
    commits = sorted({r["commit"] for r in rows.values()})
    res = dict(G=G, last=LAST, model_sha=model_sha(), commits=commits, cells=out, n_gt_1_above_1_over_n=above, slope=slope, fit_converged=bool(fit.converged),
               A_within_0_03=a_within, A_max_abs_diff=a_max, d_within_0_03=d_within, passes=passes)
    DATA.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(DATA / "stage_v_summary.json", "w"), indent=1)
    for x in out:
        print(f"n={x['n']:2} c={x['c']}: A port {x['A_port']:.3f} orig {x['A_orig']:.3f} ({x['A_diff']:+.3f})  "
              f"d port {x['d_port']:.3f} orig {x['d_orig']:.3f} ({x['d_diff']:+.3f})")
    print(f"above 1/n {above}/20, slope {slope:.4f} (converged {fit.converged}), A within 0.03 {a_within}/25, "
          f"max |A diff| {a_max:.3f}, d within 0.03 {d_within}/25 -> {'PASS' if passes else 'FAIL'}")


def classify_cell(T, X, cost_ok):
    if X["reached"] > 2:
        return "control did not separate"
    if T["reached"] >= 8:
        return "met" if cost_ok else "not met: help not at a net cost"
    return "not met"


def stage_m():
    rows = [measure(j) for j in jobs("M")]
    assert len(rows) == 60 and len({r["name"] for r in rows}) == 60
    res = {"G": G, "last": LAST, "model_sha": model_sha(), "commits": sorted({r["commit"] for r in rows}), "cells": {}}
    for n, c in ((2, 0.8), (5, 0.8)):
        cell = {}
        for arm in "TXF":
            rs = sorted([r for r in rows if (r["n"], r["c"], r["arm"]) == (n, c, arm)], key=lambda r: r["seed"])
            assert [r["seed"] for r in rs] == list(range(100, 110))
            cell[arm] = dict(runs=rs, A=[r["A"] for r in rs], reached=int(sum(r["A"] >= 1 / n for r in rs)),
                             mean_A=float(np.mean([r["A"] for r in rs])))
        T, X, F = cell["T"], cell["X"], cell["F"]
        cost_ok = bool(all(r["cost_share_all"] >= 0.95 and r["cost_share_last"] >= 0.95 for r in T["runs"]))
        paired = int(sum(t > f for t, f in zip(T["A"], F["A"])))
        h1 = bool(T["reached"] >= 8 and X["reached"] <= 2)
        cell.update(cost_ok=cost_ok, classification=classify_cell(T, X, cost_ok), H1_endpoint_counts=h1,
                    H2_T_gt_F_pairs=paired, H2=bool(paired >= 8),
                    empty_refills_total=int(sum(r["empty_refills"] for arm in "TXF" for r in cell[arm]["runs"])))
        res["cells"][f"n{n}_c{c}"] = cell
        print(f"n={n} c={c}: T {T['reached']}/10 at endpoint (mean A {T['mean_A']:.3f}), X {X['reached']}/10 "
              f"(mean A {X['mean_A']:.3f}), F mean A {F['mean_A']:.3f}; cost ok {cost_ok}; -> {cell['classification']}; "
              f"T > F in {paired}/10 pairs (H2 {cell['H2']})")
    cls = [x["classification"] for x in res["cells"].values()]
    met = sum(x == "met" for x in cls)
    if met == 2:
        verdict = "met"
    elif met == 1:
        verdict = "met at one setting only"
    elif any(x == "control did not separate" for x in cls):
        verdict = "not met: control did not separate"
    else:
        verdict = "not met"
    res.update(verdict=verdict, H2_both=bool(all(x["H2"] for x in res["cells"].values())))
    DATA.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(DATA / "stage_m_summary.json", "w"), indent=1)
    print("verdict:", verdict, "| H2 both cells:", res["H2_both"])


if __name__ == "__main__":
    {"V": stage_v, "M": stage_m}[sys.argv[1]]()
