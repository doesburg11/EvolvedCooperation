#!/usr/bin/env python3
"""Stage 0 and registered run for pre-registration 2 (location of the threshold), README.md.

Set MODE ("stage0": benchmark; "run": registered run with RUNS per cell), then from repo root:
  ./.conda/bin/python -m threshold_models.network_reciprocity_lattice.run_location
"""

from __future__ import annotations

import csv
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from threshold_models.network_reciprocity_lattice.model import lattice, run_cell, threshold

MODE = "stage0"
RUNS = 4_000_000  # set from the Stage 0 benchmark rule before the registered run
CORES = 2
BUDGET_HOURS = 5.0
SIDE = 10
N = SIDE * SIDE
C = 1.0
Z99 = 2.5758293035489
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 54321
SEED_BASE = 50_000_000
SEED_STRIDE = 4_000_037
DATA_DIR = Path("threshold_models/network_reciprocity_lattice/data")

GRAPHS = {"V": ("von_neumann", 4, 0.0025, (-0.5, -0.25, 0.25, 0.5)),
          "M": ("moore", 8, 0.0025, (-1.0, -0.5, 0.5, 1.0))}
CELLS = [(g, hood, k, w, round(threshold(N, k) + d, 3), d) for g, (hood, k, w, ds) in GRAPHS.items() for d in ds]
OUTER = {("V", -0.5), ("V", 0.5), ("M", -1.0), ("M", 1.0)}


def _job(args):
    index, hood, b, w, seed0, runs = args
    t0 = time.process_time()
    fixed = run_cell(lattice(SIDE, hood), b, C, w, seed0, runs)
    return index, int(fixed), time.process_time() - t0


def _interval(fixed: int, runs: int) -> tuple[float, float, float]:
    p = fixed / runs
    half = Z99 * np.sqrt(p * (1 - p) / runs)
    return p * N, (p - half) * N, (p + half) * N


def _fit(bs, y, var):
    wts = 1 / var
    X = np.column_stack([np.ones_like(bs), bs])
    a, slope = np.linalg.solve(X.T @ (X * wts[:, None]), X.T @ (wts * y))
    return -a / slope, a, slope


def stage0() -> None:
    for g, hood, k, w, b, d in CELLS:
        if 1 - w - w * C * k <= 0:
            raise ValueError(f"fitness can be non-positive in {g} b={b}")
    print("Cells:", [(g, b) for g, _, _, _, b, _ in CELLS])
    run_cell(lattice(SIDE, "von_neumann"), 2.0, C, 0.0, 0, 10)
    jobs = [(i, hood, b, w, 700_000_000 + 100_000 * i, 20_000) for i, (g, hood, k, w, b, d) in enumerate(CELLS)]
    with Pool(CORES) as pool:
        times = [t for _, _fixed, t in pool.map(_job, jobs)]
    per_run = sum(times) / 20_000
    projected_h = per_run * 4_000_000 / CORES / 3600
    runs = 4_000_000 if projected_h <= BUDGET_HOURS else int(BUDGET_HOURS * 3600 * CORES / per_run // 500_000 * 500_000)
    print(f"Benchmark: {per_run / len(CELLS) * 1e6:.0f} us per run on average; projected at R = 4,000,000: "
          f"{projected_h:.2f} h on {CORES} cores -> R = {runs:,}")


def run() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    t0 = time.time()
    jobs = [(i, hood, b, w, SEED_BASE + SEED_STRIDE * i, RUNS) for i, (g, hood, k, w, b, d) in enumerate(CELLS)]
    with Pool(CORES) as pool:
        out = {i: (f, t) for i, f, t in pool.imap_unordered(_job, jobs)}
    rows = []
    for i, (g, hood, k, w, b, d) in enumerate(CELLS):
        est, lo, hi = _interval(out[i][0], RUNS)
        rows.append({"cell": i, "graph": g, "k": k, "w": w, "b": b, "offset": d, "b_star": threshold(N, k),
                     "runs": RUNS, "fixed": out[i][0], "rhoN": est, "ci99_lo": lo, "ci99_hi": hi,
                     "outer": int((g, d) in OUTER), "predicted": "above" if d > 0 else "below", "cpu_s": out[i][1]})
    l1 = all((r["ci99_lo"] > 1) if r["predicted"] == "above" else (r["ci99_hi"] < 1) for r in rows if r["outer"])
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    lines, l2 = [], True
    for g, (hood, k, w, ds) in GRAPHS.items():
        gr = [r for r in rows if r["graph"] == g]
        bs = np.array([r["b"] for r in gr])
        p = np.array([r["fixed"] / RUNS for r in gr])
        est, a, slope = _fit(bs, p * N - 1, N * N * p * (1 - p) / RUNS)
        boot = [_fit(bs, pb * N - 1, N * N * pb * (1 - pb) / RUNS)[0]
                for pb in (rng.binomial(RUNS, p) / RUNS for _ in range(BOOTSTRAP_DRAWS))]
        lo, hi = np.percentile(boot, [2.5, 97.5])
        bstar = threshold(N, k)
        ok = lo <= bstar <= hi
        l2 &= ok
        quad = np.polyfit(bs, p * N - 1, 2, w=1 / np.sqrt(N * N * p * (1 - p) / RUNS))
        lines.append(f"L2 {g}: crossing {est:.3f} [{lo:.3f}, {hi:.3f}] vs b* {bstar:.3f} -> {'ok' if ok else 'FAIL'}; "
                     f"L3 excludes k = {k}: {'yes' if not (lo <= k <= hi) else 'no'}; "
                     f"L4 quadratic coefficient {quad[0]:+.4f}")
    verdict = "threshold location reproduced" if (l1 and l2) else "not reproduced"
    report = [f"{r['graph']} b={r['b']:.3f} (b*{r['offset']:+.2f}): rho*N {r['rhoN']:.4f} [{r['ci99_lo']:.4f}, "
              f"{r['ci99_hi']:.4f}] predicted {r['predicted']}{' (outer)' if r['outer'] else ''}" for r in rows]
    report += [f"L1 (outer cells): {'holds' if l1 else 'fails'}", *lines, f"Verdict: {verdict}",
               f"R = {RUNS:,} per cell, wall time {time.time() - t0:.0f} s"]
    path = DATA_DIR / f"location_{stamp}_summary.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (DATA_DIR / f"location_{stamp}_verdict.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    if MODE == "stage0":
        stage0()
    elif MODE == "run":
        run()
    else:
        raise ValueError(f"MODE must be 'stage0' or 'run', got {MODE!r}")
