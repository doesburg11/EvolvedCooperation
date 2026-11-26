#!/usr/bin/env python3
"""Stage 0 and registered run for the multilevel-selection threshold model (README.md).

Set MODE ("stage0": benchmark; "run": registered run), then from repo root:
  ./.conda/bin/python -m threshold_models.group_selection_traulsen_nowak.run_registered
"""

from __future__ import annotations

import csv
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from threshold_models.group_selection_traulsen_nowak.model import run_cell, threshold

MODE = "stage0"
RUNS = 1_000_000  # set from the Stage 0 benchmark rule before the registered run
NEUTRAL_RUNS = 2_000_000
CORES = 2
BUDGET_HOURS = 5.0
C = 1.0
W = 0.05
P = 0.001
Z99 = 2.5758293035489
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 777
OFFSETS = (-1.0, -0.5, -0.25, 0.25, 0.5, 1.0)
SETTINGS = {"G1": (10, 10), "G2": (5, 10)}
CELLS = [(g, n, m, round(threshold(n, m) + d, 3), d) for g, (n, m) in SETTINGS.items() for d in OFFSETS]
DATA_DIR = Path("threshold_models/group_selection_traulsen_nowak/data")


def _job(args):
    key, n, m, b, w, seed0, runs = args
    t0 = time.process_time()
    fixed = run_cell(n, m, b, C, w, P, seed0, runs)
    return key, int(fixed), time.process_time() - t0


def _jobs(runs, neutral_runs, bench):
    base = 1_500_000_000 if bench else 0
    jobs = [(("cell", i), n, m, b, W, base + 300_000_000 + 1_000_003 * i, runs) for i, (g, n, m, b, d) in enumerate(CELLS)]
    jobs += [(("neutral", k), n, m, threshold(n, m), 0.0, base + 320_000_000 + 2_000_003 * k, neutral_runs)
             for k, (g, (n, m)) in enumerate(SETTINGS.items())]
    return jobs


def stage0() -> None:
    for g, (n, m) in SETTINGS.items():
        if 1 - W - W * C * (n - 1) <= 0:
            raise ValueError(f"fitness can be non-positive in {g}")
    run_cell(5, 10, 2.0, C, W, P, 0, 3)
    with Pool(CORES) as pool:
        res = pool.map(_job, _jobs(20_000, 20_000, bench=True))
    cell_t = sum(t for key, _, t in res if key[0] == "cell") / 20_000
    neut_t = sum(t for key, _, t in res if key[0] == "neutral") / 20_000
    projected_h = (cell_t * RUNS + neut_t * NEUTRAL_RUNS) / CORES / 3600
    factor = 1.0 if projected_h <= BUDGET_HOURS else BUDGET_HOURS / projected_h
    runs = int(RUNS * factor // 100_000 * 100_000)
    print(f"Benchmark: {cell_t / len(CELLS) * 1e3:.3f} ms per run per cell, {neut_t / 2 * 1e3:.3f} ms per neutral run; "
          f"projected {projected_h:.2f} h on {CORES} cores -> R = {runs:,}, R0 = {int(NEUTRAL_RUNS * runs / RUNS):,}")


def _d_and_var(fixed, runs, fixed0, runs0):
    p, p0 = fixed / runs, fixed0 / runs0
    var = (p * (1 - p) / runs) / p0 ** 2 + (p / p0 ** 2) ** 2 * (p0 * (1 - p0) / runs0)
    return p / p0 - 1, var


def _fit(bs, d, var):
    wts = 1 / var
    X = np.column_stack([np.ones_like(bs), bs])
    a, slope = np.linalg.solve(X.T @ (X * wts[:, None]), X.T @ (wts * d))
    return -a / slope


def run() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    t0 = time.time()
    with Pool(CORES) as pool:
        out = {key: (f, t) for key, f, t in pool.imap_unordered(_job, _jobs(RUNS, NEUTRAL_RUNS, bench=False))}
    rows, neutral = [], {}
    for k, (g, (n, m)) in enumerate(SETTINGS.items()):
        neutral[g] = out[("neutral", k)][0]
    for i, (g, n, m, b, d) in enumerate(CELLS):
        fixed = out[("cell", i)][0]
        dd, var = _d_and_var(fixed, RUNS, neutral[g], NEUTRAL_RUNS)
        half = Z99 * np.sqrt(var)
        rows.append({"cell": i, "setting": g, "n": n, "m": m, "b": b, "offset": d, "b_star": threshold(n, m),
                     "large_m": 1 + n / m, "runs": RUNS, "fixed": fixed, "neutral_runs": NEUTRAL_RUNS,
                     "neutral_fixed": neutral[g], "D": dd, "ci99_lo": dd - half, "ci99_hi": dd + half,
                     "predicted": "above" if d > 0 else "below", "outer": int(abs(d) == 1.0)})
    gd = all((r["ci99_lo"] > 0) if r["predicted"] == "above" else (r["ci99_hi"] < 0) for r in rows if r["outer"])
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    lines, gl = [], True
    for g, (n, m) in SETTINGS.items():
        inner = [r for r in rows if r["setting"] == g and not r["outer"]]
        bs = np.array([r["b"] for r in inner])
        fx = np.array([r["fixed"] for r in inner])
        est_d = np.array([r["D"] for r in inner])
        est_v = np.array([_d_and_var(f, RUNS, neutral[g], NEUTRAL_RUNS)[1] for f in fx])
        est = _fit(bs, est_d, est_v)
        p_hat, p0_hat = fx / RUNS, neutral[g] / NEUTRAL_RUNS
        boot = []
        for _ in range(BOOTSTRAP_DRAWS):
            fb = rng.binomial(RUNS, p_hat)
            f0 = rng.binomial(NEUTRAL_RUNS, p0_hat)
            dv = [_d_and_var(f, RUNS, f0, NEUTRAL_RUNS) for f in fb]
            boot.append(_fit(bs, np.array([x[0] for x in dv]), np.array([x[1] for x in dv])))
        lo, hi = np.percentile(boot, [2.5, 97.5])
        bstar, large = threshold(n, m), 1 + n / m
        ok = lo <= bstar <= hi
        gl &= ok
        lines.append(f"G-L {g}: crossing {est:.3f} [{lo:.3f}, {hi:.3f}] vs b* {bstar:.3f} -> {'ok' if ok else 'FAIL'}; "
                     f"excludes 1 + n/m = {large:.3f}: {'yes' if not (lo <= large <= hi) else 'no'}; "
                     f"neutral rho0*m(n-1) = {neutral[g] / NEUTRAL_RUNS * m * (n - 1):.4f}")
    verdict = "rule reproduced" if (gd and gl) else "not reproduced"
    report = [f"{r['setting']} b={r['b']:.3f} (b*{r['offset']:+.2f}): D {r['D']:+.4f} [{r['ci99_lo']:+.4f}, "
              f"{r['ci99_hi']:+.4f}] predicted {r['predicted']}{' (outer)' if r['outer'] else ''}; {r['fixed']} fixations"
              for r in rows]
    report += [f"G-D (outer cells): {'holds' if gd else 'fails'}", *lines, f"Verdict: {verdict}",
               f"R = {RUNS:,}, R0 = {NEUTRAL_RUNS:,}; wall time {time.time() - t0:.0f} s"]
    path = DATA_DIR / f"registered_{stamp}_summary.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (DATA_DIR / f"registered_{stamp}_verdict.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    if MODE == "stage0":
        stage0()
    elif MODE == "run":
        run()
    else:
        raise ValueError(f"MODE must be 'stage0' or 'run', got {MODE!r}")
