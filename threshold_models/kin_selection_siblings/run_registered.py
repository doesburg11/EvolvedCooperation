#!/usr/bin/env python3
"""Registered run for the sibling alarm-call threshold model (README.md, amendment A1).

Run from repo root:
  ./.conda/bin/python -m threshold_models.kin_selection_siblings.run_registered
"""

from __future__ import annotations

import csv
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import stats as sps

from threshold_models.kin_selection_siblings.model import Params, hamilton, naive, predicted_change, run_one_generation, run_trajectory

F0 = 0.5
Q1_SEEDS = list(range(40))
Q1_GENERATIONS = 200
Q2_SEEDS = list(range(100_000, 104_000))
Q1_LEVEL = 0.95
Q2_LEVEL = 0.99
Q3_R_TOL = 0.02
Q3_RREG_TOL = 0.03
Q3_P_TOL = 0.03
DATA_DIR = Path("threshold_models/kin_selection_siblings/data")


def _sexual(n: int, c: float) -> Params:
    return Params(sexual=True, n=n, c=c, homes=250, puddles_per_home=2)


def _asexual(n: int, c: float) -> Params:
    return Params(sexual=False, n=n, c=c, homes=500, puddles_per_home=1)


CELLS: dict[str, Params] = {
    "S3-0.80": _sexual(3, 0.80),
    "S3-0.90": _sexual(3, 0.90),
    "S3-1.00": _sexual(3, 1.00),
    "S2-0.30": _sexual(2, 0.30),
    "S2-0.40": _sexual(2, 0.40),
    "S2-0.50": _sexual(2, 0.50),
    "S2-0.60": _sexual(2, 0.60),
    "S2-0.70": _sexual(2, 0.70),
    "A2-0.80": _asexual(2, 0.80),
    "A2-1.00": _asexual(2, 1.00),
}


def t_interval(values: np.ndarray, level: float) -> tuple[float, float, float]:
    mean = float(values.mean())
    half = float(sps.t.ppf(0.5 + level / 2, values.size - 1) * values.std(ddof=1) / np.sqrt(values.size))
    return mean, mean - half, mean + half


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    t0 = time.time()
    rows, trajectories, verdict_lines = [], [], []
    q1_ok_nonneutral = q1_ok_neutral = q2_ok = 0
    q3_ok = True

    for name, p in CELLS.items():
        hr = round(hamilton(p), 10)

        # Q1: direction over 200 generations.
        finals = []
        for seed in Q1_SEEDS:
            traj = run_trajectory(p, F0, Q1_GENERATIONS, seed)
            trajectories.append([name, seed, *[f"{x:.6f}" for x in traj[::10]]])
            finals.append(traj[-1] - F0)
        finals = np.array(finals)
        q1_mean, q1_lo, q1_hi = t_interval(finals, Q1_LEVEL)
        if hr > 0:
            q1_pass = q1_lo > 0
        elif hr < 0:
            q1_pass = q1_hi < 0
        else:
            q1_pass = q1_lo <= 0 <= q1_hi
        if hr == 0:
            q1_ok_neutral += q1_pass
        else:
            q1_ok_nonneutral += q1_pass

        # Q2 and Q3: one generation from fresh founders.
        stats = {"pairs": 0, "ibd": 0, "sib_altruist": 0}
        changes, f_before_all, preds = [], [], []
        for seed in Q2_SEEDS:
            f_before, f_after = run_one_generation(p, F0, seed, stats)
            changes.append(f_after - f_before)
            f_before_all.append(f_before)
            preds.append(predicted_change(p, f_before))
        changes = np.array(changes)
        pred = float(np.mean(preds))
        q2_mean, q2_lo, q2_hi = t_interval(changes, Q2_LEVEL)
        q2_pass = q2_lo <= pred <= q2_hi
        q2_ok += q2_pass

        f_bar = float(np.mean(f_before_all))
        r_hat = stats["ibd"] / stats["pairs"]
        p_hat = stats["sib_altruist"] / stats["pairs"]
        r_reg = (p_hat - f_bar) / (1 - f_bar)
        if p.sexual:
            q3_cell = abs(r_hat - 0.5) <= Q3_R_TOL and abs(r_reg - 0.5) <= Q3_RREG_TOL and abs(p_hat - 0.75) <= Q3_P_TOL
            q3_ok &= q3_cell
        else:
            q3_cell = None

        rows.append({
            "cell": name, "sexual": int(p.sexual), "n": p.n, "b": p.b, "r": p.r, "c": p.c,
            "hamilton_br_minus_c": hr, "naive_bp_minus_c_at_0.5": round(naive(p, 0.5), 10),
            "q1_mean_delta200": q1_mean, "q1_ci95_lo": q1_lo, "q1_ci95_hi": q1_hi,
            "q1_runs_up": int(np.sum(finals > 0)), "q1_runs_down": int(np.sum(finals < 0)), "q1_pass": int(q1_pass),
            "q2_predicted": pred, "q2_mean_change": q2_mean, "q2_ci99_lo": q2_lo, "q2_ci99_hi": q2_hi,
            "q2_pass": int(q2_pass), "q3_pairs": stats["pairs"], "q3_r_hat": r_hat, "q3_p_hat": p_hat,
            "q3_r_reg": r_reg, "q3_f_bar": f_bar, "q3_pass": "" if q3_cell is None else int(q3_cell),
        })
        print(f"{name}: b·r−c {hr:+.2f} | Q1 {q1_mean:+.3f} [{q1_lo:+.3f}, {q1_hi:+.3f}] {'ok' if q1_pass else 'FAIL'}"
              f" | Q2 pred {pred:+.5f} mean {q2_mean:+.5f} [{q2_lo:+.5f}, {q2_hi:+.5f}] {'ok' if q2_pass else 'FAIL'}"
              f" | r̂ {r_hat:.3f} p̂ {p_hat:.3f} r_reg {r_reg:.3f}  ({time.time() - t0:.0f} s)", flush=True)

    q1 = q1_ok_nonneutral == 7 and q1_ok_neutral >= 2
    q2 = q2_ok >= 9
    verdict = "Hamilton's rule reproduced" if (q1 and q2 and q3_ok) else "not reproduced"
    verdict_lines = [
        f"Q1 (direction): non-neutral {q1_ok_nonneutral}/7, neutral {q1_ok_neutral}/3 -> {'holds' if q1 else 'fails'}",
        f"Q2 (size): {q2_ok}/10 cells -> {'holds' if q2 else 'fails'}",
        f"Q3 (r vs p): {'holds' if q3_ok else 'fails'}",
        f"Verdict: {verdict}",
        f"wall time {time.time() - t0:.0f} s",
    ]

    summary_path = DATA_DIR / f"registered_{stamp}_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    traj_path = DATA_DIR / f"registered_{stamp}_q1_trajectories_every10.csv"
    with traj_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["cell", "seed", *[f"g{g}" for g in range(0, Q1_GENERATIONS + 1, 10)]])
        writer.writerows(trajectories)
    (DATA_DIR / f"registered_{stamp}_verdict.txt").write_text("\n".join(verdict_lines) + "\n", encoding="utf-8")
    print("\n".join(verdict_lines))
    print(f"wrote {summary_path}, {traj_path}")


if __name__ == "__main__":
    main()
