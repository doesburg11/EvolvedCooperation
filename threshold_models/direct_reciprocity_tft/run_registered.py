#!/usr/bin/env python3
"""Stage 0 and registered run for the TFT-against-ALLD threshold model (README.md).

Set MODE ("stage0": benchmark; "run": registered run), then from repo root:
  ./.conda/bin/python -m threshold_models.direct_reciprocity_tft.run_registered
"""

from __future__ import annotations

import csv
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy import stats as sps

from threshold_models.direct_reciprocity_tft.model import (
    one_generation_changes,
    predicted_change,
    trajectory_finals,
    w_star,
)

MODE = "stage0"
ONE_GEN_RUNS = 20_000  # set from the Stage 0 benchmark rule before the registered run
TRAJ_RUNS = 40
TRAJ_GENERATIONS = 100
CORES = 2
BUDGET_HOURS = 5.0
N = 1000
N_RARE = 10
S = 0.1
DATA_DIR = Path("threshold_models/direct_reciprocity_tft/data")

CELLS = [("B3", 3.0, 1.0, w) for w in (0.15, 0.25, 0.30, 0.375, 0.45, 0.55)] + \
        [("B2", 2.0, 1.0, w) for w in (0.30, 0.40, 0.45, 0.55, 0.60, 0.70)]


def _jobs(runs: int, traj_runs: int, bench: bool):
    jobs = []
    for i, (series, b, c, w) in enumerate(CELLS):
        base = 900_000_000 if bench else 0
        jobs.append(("alld", i, b, c, w, base + 10_000_000 + 100_003 * i, runs))
        jobs.append(("tft", i, b, c, w, base + 30_000_000 + 100_003 * i, runs))
        if traj_runs:
            jobs.append(("traj", i, b, c, w, base + 50_000_000 + 1_009 * i, traj_runs))
    return jobs


def _work(job):
    kind, i, b, c, w, seed0, runs = job
    t0 = time.process_time()
    if kind == "alld":
        out = one_generation_changes(N_RARE, N, b, c, w, S, seed0, runs)
    elif kind == "tft":
        out = -one_generation_changes(N - N_RARE, N, b, c, w, S, seed0, runs)  # change in TFT frequency
    else:
        out = trajectory_finals(N_RARE, N, b, c, w, S, seed0, runs, TRAJ_GENERATIONS)
    return kind, i, out, time.process_time() - t0


def _t99(values: np.ndarray) -> tuple[float, float, float]:
    m = float(values.mean())
    half = float(sps.t.ppf(0.995, values.size - 1) * values.std(ddof=1) / np.sqrt(values.size))
    return m, m - half, m + half


def stage0() -> None:
    _work(("alld", 0, 3.0, 1.0, 0.3, 0, 2))  # compile
    with Pool(CORES) as pool:
        res = pool.map(_work, _jobs(500, 2, bench=True))
    one_gen = sum(t for kind, _, _, t in res if kind != "traj") / 500
    traj = sum(t for kind, _, _, t in res if kind == "traj") / 2
    projected_h = (one_gen * 20_000 + traj * TRAJ_RUNS) / CORES / 3600
    if projected_h <= BUDGET_HOURS:
        runs = 20_000
    else:
        runs = int((BUDGET_HOURS * 3600 * CORES - traj * TRAJ_RUNS) / one_gen // 5_000 * 5_000)
    print(f"Benchmark: one-generation runs {one_gen * 1e3:.1f} ms per run of all cells and starts; trajectories "
          f"{traj:.1f} s per run of all cells; projected {projected_h:.2f} h on {CORES} cores -> one-generation runs = {runs:,}")


def run() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    t0 = time.time()
    with Pool(CORES) as pool:
        res = pool.map(_work, _jobs(ONE_GEN_RUNS, TRAJ_RUNS, bench=False))
    out = {(kind, i): v for kind, i, v, _ in res}
    rows, d1, d2_count, d3 = [], True, 0, True
    for i, (series, b, c, w) in enumerate(CELLS):
        ws = w_star(N_RARE, N, b, c)
        far = abs(w - ws) >= 0.05
        m, lo, hi = _t99(out[("alld", i)])
        pred = predicted_change(N_RARE, N, b, c, w, S)
        side_ok = (lo > 0) if w < ws else (hi < 0)
        if far:
            d1 &= side_ok
        d2_ok = lo <= pred <= hi
        d2_count += d2_ok
        mt, lot, hit = _t99(out[("tft", i)])
        d3_ok = hit < 0
        d3 &= d3_ok
        finals = out[("traj", i)]
        rows.append({"cell": i, "series": series, "b": b, "c": c, "w": w, "w_star": ws, "c_over_b": c / b,
                     "far": int(far), "predicted_alld": "up" if w < ws else "down",
                     "alld_mean_dx": m, "alld_ci99_lo": lo, "alld_ci99_hi": hi, "alld_side_ok": int(side_ok),
                     "predicted_dx": pred, "d2_ok": int(d2_ok),
                     "tft_mean_dx": mt, "tft_ci99_lo": lot, "tft_ci99_hi": hit, "d3_ok": int(d3_ok),
                     "traj_alld_lost": int(np.sum(finals == 0)), "traj_alld_fixed": int(np.sum(finals == 1)),
                     "traj_mean_final": float(finals.mean())})
    d2 = d2_count >= 10
    verdict = "reproduced" if (d1 and d2 and d3) else "not reproduced"
    report = [f"{r['series']} w={r['w']:.3f} (w* {r['w_star']:.4f}, far={r['far']}): ALLD dx {r['alld_mean_dx']:+.6f} "
              f"[{r['alld_ci99_lo']:+.6f}, {r['alld_ci99_hi']:+.6f}] pred {r['predicted_dx']:+.6f} "
              f"(expected {r['predicted_alld']}); TFT dx {r['tft_mean_dx']:+.6f} [{r['tft_ci99_lo']:+.6f}, "
              f"{r['tft_ci99_hi']:+.6f}]; 100 gen: ALLD lost {r['traj_alld_lost']}/40, fixed {r['traj_alld_fixed']}/40, "
              f"mean final {r['traj_mean_final']:.3f}" for r in rows]
    report += [f"D1 (far cells, direction): {'holds' if d1 else 'fails'}",
               f"D2 (size): {d2_count}/12 -> {'holds' if d2 else 'fails'}",
               f"D3 (rare TFT declines): {'holds' if d3 else 'fails'}", f"Verdict: {verdict}",
               f"one-generation runs {ONE_GEN_RUNS:,} per cell and start; wall time {time.time() - t0:.0f} s"]
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
