"""Analysis for PREREG_KIN_TEST.md. Usage: python -m ecological_models.density_dependent_dispersal.analyze_test {V|M}

Measures (as in the authors' notebook): A = zbar / (1 - zbar), zbar = mean over the last 1000 generations of the
per-generation population mean of z; d = mean over the last 1000 generations of the per-generation mean (over
patches with survivors) of dispersal attempts / survivors.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LAST = 1000
# authors' code, full grid 2026-11-21..25 (~/simulation_results/kanwal_gardner_viscosity/full_grid/analysis_summary.json)
ORIG_SUMMARY = Path.home() / "simulation_results/kanwal_gardner_viscosity/full_grid/analysis_summary.json"


def load(path):
    f = np.load(path)
    meta = json.loads(str(f["meta"]))
    z = f["z"].astype(float)
    zbar = z[-LAST:].mean()
    d = np.nanmean(f["d_mean"].astype(float)[-LAST:])
    return dict(meta=meta, n=meta["n"], c=meta["c"], zbar=zbar, A=zbar / (1 - zbar), d=d,
                zbar_first_half=z[-LAST:-LAST // 2].mean(), zbar_second_half=z[-LAST // 2:].mean(),
                empty_frac=float(np.nansum(f["empty"][1:]) / ((len(z) - 1) * (50000 / meta["n"]))),
                z_traj=z[::500].round(4).tolist())


def stage_v():
    rows = {(r["n"], r["c"]): r for r in map(load, sorted((HERE / "data/stage_v").glob("*.npz")))}
    orig = {(r["n"], r["c"]): r for r in json.load(open(ORIG_SUMMARY))["runs"]}
    assert len(rows) == 25, len(rows)
    diffs = []
    out = []
    for key in sorted(rows):
        r, o = rows[key], orig[key]
        diff = r["A"] - o["A"]
        diffs.append(abs(diff))
        out.append(dict(n=key[0], c=key[1], A_port=r["A"], A_orig=o["A"], diff=diff, d_port=r["d"], d_orig=o["d"]))
    multi = [x for x in out if x["n"] > 1]
    above = sum(x["A_port"] > 1 / x["n"] for x in multi)
    # mixed model as in the authors' notebook
    import pandas as pd
    import statsmodels.formula.api as smf
    df = pd.DataFrame([dict(A=x["A_port"], d=x["d_port"], n=x["n"]) for x in multi])
    fit = smf.mixedlm("A ~ d", df, groups=df["n"]).fit()
    slope = float(fit.params["d"])
    within = sum(d <= 0.03 for d in diffs)
    passes = above == 20 and slope < 0 and within >= 23 and max(diffs) <= 0.06
    res = dict(cells=out, n_gt_1_above_1_over_n=above, slope=slope, cells_within_0_03=within,
               max_abs_diff=max(diffs), passes=passes)
    json.dump(res, open(HERE / "data/stage_v_summary.json", "w"), indent=1)
    for x in out:
        print(f"n={x['n']:2} c={x['c']}: A port {x['A_port']:.3f} orig {x['A_orig']:.3f} diff {x['diff']:+.3f}"
              f"  d port {x['d_port']:.3f} orig {x['d_orig']:.3f}")
    print(f"above 1/n {above}/20, slope {slope:.4f}, within 0.03: {within}/25, max diff {max(diffs):.3f} -> "
          f"{'PASS' if passes else 'FAIL'}")


def stage_m():
    rows = [load(p) for p in sorted((HERE / "data/stage_m").glob("*.npz"))]
    assert len(rows) == 60, len(rows)
    res = {"cells": {}}
    for n, c in ((2, 0.8), (5, 0.8)):
        cell = {}
        for arm in "TXF":
            rs = sorted([r for r in rows if r["n"] == n and r["c"] == c and r["meta"]["arm"] == arm],
                        key=lambda r: r["meta"]["seed"])
            assert len(rs) == 10
            cell[arm] = dict(A=[r["A"] for r in rs], d=[r["d"] for r in rs], seeds=[r["meta"]["seed"] for r in rs],
                             reached=sum(r["A"] >= 1 / n for r in rs),
                             halves=[(r["zbar_first_half"], r["zbar_second_half"]) for r in rs],
                             empty_frac_max=max(r["empty_frac"] for r in rs),
                             z_traj_seed0=rs[0]["z_traj"])
        # net direct cost at the endpoint: dS_i/dz_i = 0.5 * (-zbar + (1 - z_i) / (n k)) < 0 iff zbar > (1 - z_i)/(n k)
        zbar_T = np.mean([A / (1 + A) for A in cell["T"]["A"]])
        cost = zbar_T > 1 / (n * 100)
        h1 = cell["T"]["reached"] >= 8 and cell["X"]["reached"] <= 2
        paired = sum(t > f for t, f in zip(cell["T"]["A"], cell["F"]["A"]))
        h2 = paired >= 8
        cell.update(net_cost_at_endpoint=bool(cost), H1=bool(h1), H2_paired_T_gt_F=paired, H2=bool(h2))
        res["cells"][f"n{n}_c{c}"] = cell
        print(f"n={n} c={c}: T reached {cell['T']['reached']}/10 (A {np.mean(cell['T']['A']):.3f}), "
              f"X reached {cell['X']['reached']}/10 (A {np.mean(cell['X']['A']):.3f}), "
              f"F A {np.mean(cell['F']['A']):.3f}; H1 {h1}; T>F paired {paired}/10, H2 {h2}")
    cells = res["cells"].values()
    res["H1_both"] = all(x["H1"] for x in cells)
    res["H2_both"] = all(x["H2"] for x in cells)
    json.dump(res, open(HERE / "data/stage_m_summary.json", "w"), indent=1)
    print("H1 both cells:", res["H1_both"], " H2 both cells:", res["H2_both"])


if __name__ == "__main__":
    {"V": stage_v, "M": stage_m}[sys.argv[1]]()
