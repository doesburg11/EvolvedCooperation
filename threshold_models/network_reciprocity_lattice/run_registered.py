#!/usr/bin/env python3
"""Stage 0 and registered run for the lattice network-reciprocity threshold model (README.md).

Set MODE ("stage0": neutral check and benchmark; "run": registered run with RUNS per cell), then from repo root:
  ./.conda/bin/python -m threshold_models.network_reciprocity_lattice.run_registered
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
RUNS = 1_000_000  # set from the Stage 0 benchmark rule before the registered run
CORES = 2
BUDGET_HOURS = 5.0
SIDE = 10
N = SIDE * SIDE
C = 1.0
Z99 = 2.5758293035489
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 12345
DATA_DIR = Path("threshold_models/network_reciprocity_lattice/data")

GRAPHS = {"V": ("von_neumann", 4, 0.01, [2.0, 3.0, 4.0, 5.0, 6.0, 8.0]),
          "M": ("moore", 8, 0.0025, [4.0, 6.0, 8.0, 9.0, 11.0, 14.0])}
CELLS = [(g, hood, k, w, b) for g, (hood, k, w, bs) in GRAPHS.items() for b in bs]  # cell index = position


def _check_fitness_positive() -> None:
    for g, hood, k, w, b in CELLS:
        if 1 - w - w * C * k <= 0:
            raise ValueError(f"fitness can be non-positive in cell {g} b={b}")


def _cell_job(args):
    index, hood, b, w, seed0, runs = args
    nbr = lattice(SIDE, hood)
    t0 = time.process_time()
    fixed = run_cell(nbr, b, C, w, seed0, runs)
    return index, int(fixed), time.process_time() - t0


def _interval(fixed: int, runs: int) -> tuple[float, float, float]:
    p = fixed / runs
    half = Z99 * np.sqrt(p * (1 - p) / runs)
    return p * N, (p - half) * N, (p + half) * N


def stage0() -> None:
    _check_fitness_positive()
    run_cell(lattice(SIDE, "von_neumann"), 2.0, C, 0.0, 0, 10)  # compile
    print("Neutral check (w = 0, 200,000 runs per graph):")
    for g, (hood, k, _, _) in GRAPHS.items():
        fixed = run_cell(lattice(SIDE, hood), 5.0, C, 0.0, 900_000_000 + 1_000_000 * k, 200_000)
        est, lo, hi = _interval(fixed, 200_000)
        print(f"  {g}: rho*N = {est:.3f} [{lo:.3f}, {hi:.3f}] -> {'PASS' if lo <= 1 <= hi else 'FAIL'}")
    print("Benchmark (20,000 runs per cell, timing only; fixation counts discarded):")
    jobs = [(i, hood, b, w, 800_000_000 + 100_000 * i, 20_000) for i, (g, hood, k, w, b) in enumerate(CELLS)]
    with Pool(CORES) as pool:
        times = {i: t for i, _fixed, t in pool.map(_cell_job, jobs)}
    per_run = sum(times.values()) / 20_000  # CPU seconds for one run of every cell
    projected_h = per_run * 1_000_000 / CORES / 3600
    runs = 1_000_000 if projected_h <= BUDGET_HOURS else int(BUDGET_HOURS * 3600 * CORES / per_run // 100_000 * 100_000)
    for i, (g, hood, k, w, b) in enumerate(CELLS):
        print(f"  {g} b={b:g}: {times[i] / 20_000 * 1e6:.0f} us per run")
    print(f"Projected registered run at R = 1,000,000: {projected_h:.2f} h on {CORES} cores -> R = {runs:,}")


def _fit_crossing(bs: np.ndarray, y: np.ndarray, var: np.ndarray) -> tuple[float, float, float]:
    wts = 1 / var
    X = np.column_stack([np.ones_like(bs), bs])
    a, slope = np.linalg.solve(X.T @ (X * wts[:, None]), X.T @ (wts * y))
    return -a / slope, a, slope


def run() -> None:
    _check_fitness_positive()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    t0 = time.time()
    jobs = [(i, hood, b, w, 1_000_003 * i, RUNS) for i, (g, hood, k, w, b) in enumerate(CELLS)]
    with Pool(CORES) as pool:
        out = {i: (fixed, cpu) for i, fixed, cpu in pool.imap_unordered(_cell_job, jobs)}

    rows = []
    for i, (g, hood, k, w, b) in enumerate(CELLS):
        fixed, cpu = out[i]
        est, lo, hi = _interval(fixed, RUNS)
        bstar = threshold(N, k)
        rows.append({"cell": i, "graph": g, "k": k, "w": w, "b": b, "b_star": bstar, "runs": RUNS, "fixed": fixed,
                     "rhoN": est, "ci99_lo": lo, "ci99_hi": hi, "far": int(abs(b - bstar) >= 1),
                     "predicted": "above" if b > bstar else "below", "cpu_s": cpu})

    t1_ok = all((r["ci99_lo"] > 1) if r["predicted"] == "above" else (r["ci99_hi"] < 1) for r in rows if r["far"])
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    lines, t2_ok = [], True
    for g, (hood, k, w, bs) in GRAPHS.items():
        gr = [r for r in rows if r["graph"] == g]
        b_arr = np.array([r["b"] for r in gr])
        p = np.array([r["fixed"] / RUNS for r in gr])
        var = N * N * p * (1 - p) / RUNS
        bstar_hat, a, slope = _fit_crossing(b_arr, p * N - 1, var)
        boot = []
        for _ in range(BOOTSTRAP_DRAWS):
            pb = rng.binomial(RUNS, p) / RUNS
            boot.append(_fit_crossing(b_arr, pb * N - 1, N * N * pb * (1 - pb) / RUNS)[0])
        lo, hi = np.percentile(boot, [2.5, 97.5])
        target = threshold(N, k)
        ok = lo <= target <= hi
        t2_ok &= ok
        resid = (p * N - 1) - (a + slope * b_arr)
        for r, e in zip(gr, resid):
            r["fit_residual"] = e
        lines.append(f"T2 {g}: crossing {bstar_hat:.3f} [{lo:.3f}, {hi:.3f}] vs b* {target:.3f} -> {'ok' if ok else 'FAIL'}"
                     + (f"; H2 (interval above k = {k}): {'yes' if lo > k else 'no'}" if g == "M" else ""))

    verdict = "rule reproduced" if (t1_ok and t2_ok) else "not reproduced"
    near = [f"{r['graph']} b={r['b']:g}: {r['rhoN']:.3f} [{r['ci99_lo']:.3f}, {r['ci99_hi']:.3f}] (rule: {r['predicted']})"
            for r in rows if not r["far"]]
    report = [f"{r['graph']} b={r['b']:g}: rho*N {r['rhoN']:.3f} [{r['ci99_lo']:.3f}, {r['ci99_hi']:.3f}] "
              f"(far={r['far']}, predicted {r['predicted']}, {r['fixed']} fixations)" for r in rows]
    report += [f"T1 (far cells): {'holds' if t1_ok else 'fails'}", *lines, "H3 near cells: " + "; ".join(near),
               f"Verdict: {verdict}", f"R = {RUNS:,} per cell, wall time {time.time() - t0:.0f} s"]
    path = DATA_DIR / f"registered_{stamp}_summary.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (DATA_DIR / f"registered_{stamp}_verdict.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"wrote {path}")


if __name__ == "__main__":
    if MODE == "stage0":
        stage0()
    elif MODE == "run":
        run()
    else:
        raise ValueError(f"MODE must be 'stage0' or 'run', got {MODE!r}")
