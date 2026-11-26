#!/usr/bin/env python3
"""Stage 0 and registered run for pre-registration 2 (weaker selection in groups of 10, README.md).

Set MODE ("stage0": benchmark; "run": registered run), then from repo root:
  ./.conda/bin/python -m threshold_models.group_selection_traulsen_nowak.run_weak_omega
"""

from __future__ import annotations

import csv
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from threshold_models.group_selection_traulsen_nowak.model import threshold
from threshold_models.group_selection_traulsen_nowak.run_registered import _d_and_var, _fit, _job

MODE = "run"
RUNS = 2_000_000  # set from the Stage 0 benchmark rule before the registered run
NEUTRAL_RUNS = 4_000_000
CORES = 2
BUDGET_HOURS = 5.0
C = 1.0
Z99 = 2.5758293035489
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 778
N, M = 10, 10
B_STAR = threshold(N, M)
OFFSETS = (-1.0, -0.5, -0.25, 0.25, 0.5, 1.0)
OMEGAS = (0.02, 0.01)
CELLS = [(w, round(B_STAR + d, 3), d) for w in OMEGAS for d in OFFSETS]
FIRST_RUN_W005 = (7.026, 6.662, 7.441)  # crossing [95% interval] at omega = 0.05, registered run of 2026-11-26
DATA_DIR = Path("threshold_models/group_selection_traulsen_nowak/data")


def _jobs(runs, neutral_runs, bench):
    base = 1_500_000_000 if bench else 0
    jobs = [(("cell", i), N, M, b, w, base + 340_000_000 + 2_000_003 * i, runs) for i, (w, b, d) in enumerate(CELLS)]
    jobs.append((("neutral", 0), N, M, B_STAR, 0.0, base + 370_000_000, neutral_runs))
    return jobs


def stage0() -> None:
    for w in OMEGAS:
        if 1 - w - w * C * (N - 1) <= 0:
            raise ValueError(f"fitness can be non-positive at omega = {w}")
    with Pool(CORES) as pool:
        res = pool.map(_job, _jobs(20_000, 20_000, bench=True))
    cell_t = sum(t for key, _, t in res if key[0] == "cell") / 20_000
    neut_t = sum(t for key, _, t in res if key[0] == "neutral") / 20_000
    projected_h = (cell_t * RUNS + neut_t * NEUTRAL_RUNS) / CORES / 3600
    factor = 1.0 if projected_h <= BUDGET_HOURS else BUDGET_HOURS / projected_h
    runs = int(RUNS * factor // 100_000 * 100_000)
    print(f"Benchmark: {cell_t / len(CELLS) * 1e3:.3f} ms per run per cell, {neut_t * 1e3:.3f} ms per neutral run; "
          f"projected {projected_h:.2f} h on {CORES} cores -> R = {runs:,}, R0 = {int(NEUTRAL_RUNS * runs / RUNS):,}")


def run() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    t0 = time.time()
    with Pool(CORES) as pool:
        out = {key: f for key, f, _ in pool.imap_unordered(_job, _jobs(RUNS, NEUTRAL_RUNS, bench=False))}
    neutral = out[("neutral", 0)]
    rows = []
    for i, (w, b, d) in enumerate(CELLS):
        fixed = out[("cell", i)]
        dd, var = _d_and_var(fixed, RUNS, neutral, NEUTRAL_RUNS)
        half = Z99 * np.sqrt(var)
        rows.append({"cell": i, "omega": w, "n": N, "m": M, "b": b, "offset": d, "b_star": B_STAR, "runs": RUNS,
                     "fixed": fixed, "neutral_runs": NEUTRAL_RUNS, "neutral_fixed": neutral, "D": dd,
                     "ci99_lo": dd - half, "ci99_hi": dd + half, "predicted": "above" if d > 0 else "below",
                     "outer": int(abs(d) == 1.0)})
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    crossing = {}
    for w in OMEGAS:
        inner = [r for r in rows if r["omega"] == w and not r["outer"]]
        bs = np.array([r["b"] for r in inner])
        fx = np.array([r["fixed"] for r in inner])
        est = _fit(bs, np.array([r["D"] for r in inner]),
                   np.array([_d_and_var(f, RUNS, neutral, NEUTRAL_RUNS)[1] for f in fx]))
        p_hat, p0_hat = fx / RUNS, neutral / NEUTRAL_RUNS
        boot = []
        for _ in range(BOOTSTRAP_DRAWS):
            fb = rng.binomial(RUNS, p_hat)
            f0 = rng.binomial(NEUTRAL_RUNS, p0_hat)
            dv = [_d_and_var(f, RUNS, f0, NEUTRAL_RUNS) for f in fb]
            boot.append(_fit(bs, np.array([x[0] for x in dv]), np.array([x[1] for x in dv])))
        lo, hi = np.percentile(boot, [2.5, 97.5])
        crossing[w] = (est, lo, hi)
    e01, lo01, hi01 = crossing[0.01]
    e02 = crossing[0.02][0]
    w1 = hi01 < FIRST_RUN_W005[1] and min(e01, FIRST_RUN_W005[0]) < e02 < max(e01, FIRST_RUN_W005[0])
    w2 = lo01 <= B_STAR <= hi01
    wd = all((r["ci99_lo"] > 0) if r["predicted"] == "above" else (r["ci99_hi"] < 0)
             for r in rows if r["outer"] and r["omega"] == 0.01)
    report = [f"omega={r['omega']:.2f} b={r['b']:.3f} (b*{r['offset']:+.2f}): D {r['D']:+.4f} [{r['ci99_lo']:+.4f}, "
              f"{r['ci99_hi']:+.4f}] predicted {r['predicted']}{' (outer)' if r['outer'] else ''}; {r['fixed']} fixations"
              for r in rows]
    for w in OMEGAS:
        e, lo, hi = crossing[w]
        report.append(f"crossing omega={w:.2f}: {e:.3f} [{lo:.3f}, {hi:.3f}]; contains b* {B_STAR}: "
                      f"{'yes' if lo <= B_STAR <= hi else 'no'}; excludes 2.0: {'yes' if not (lo <= 2.0 <= hi) else 'no'}")
    report.append(f"crossing omega=0.05 (first run): {FIRST_RUN_W005[0]:.3f} [{FIRST_RUN_W005[1]:.3f}, {FIRST_RUN_W005[2]:.3f}]")
    report.append(f"neutral rho0*m(n-1) = {neutral / NEUTRAL_RUNS * M * (N - 1):.4f}")
    report += [f"W-1 (crossing moves): {'holds' if w1 else 'fails'}", f"W-2 (rule reached): {'holds' if w2 else 'fails'}",
               f"W-D (outer cells at omega=0.01): {'holds' if wd else 'fails'}",
               f"Verdict: weak-selection explanation {'supported' if w1 else 'not supported'}; rule "
               f"{'reproduced' if (w2 and wd) else 'not reproduced'} for groups of 10 at omega = 0.01",
               f"R = {RUNS:,}, R0 = {NEUTRAL_RUNS:,}; wall time {time.time() - t0:.0f} s"]
    path = DATA_DIR / f"weak_omega_{stamp}_summary.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (DATA_DIR / f"weak_omega_{stamp}_verdict.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    if MODE == "stage0":
        stage0()
    elif MODE == "run":
        run()
    else:
        raise ValueError(f"MODE must be 'stage0' or 'run', got {MODE!r}")
