"""Registered rung-4a attempt-2 run (README.md, "Rung 4a, attempt 2") and verdict.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a.run_attempt2

Only change from attempt 1 (run.py): the start, 5% ALLC / 85% DISC / 10% ALLD, and no reported conditions beyond
the two arms. Model, parameters, endpoint, sanity rule, validation and verdict are run.py's. Writes separate files
data/rung4a_attempt2_runs.csv, _traj.npz, _verdict.txt (attempt 1's outputs are kept).
"""

import csv
import time

import numpy as np

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a import model, run

START = (0.05, 0.85, 0.1)
CONDITIONS = {"main": (START, ("test", "shuffled"))}
PREFIX = "rung4a_attempt2_"


def verdict(rows):
    """run.py's verdict and validation with attempt 2's condition list."""
    saved = run.CONDITIONS
    run.CONDITIONS = CONDITIONS
    try:
        return run.verdict(rows)
    finally:
        run.CONDITIONS = saved


def main():
    run.DATA.mkdir(exist_ok=True)
    model.run(run.Q, run.O, run.E, run.A, START, model.TEST, 0, gens=2)  # compile
    rows, trajs = [], {}
    t0 = time.time()
    for arm in ("test", "shuffled"):
        for seed in run.SEEDS:
            tr, st, g1 = model.run(run.Q, run.O, run.E, run.A, START, run.ARMS[arm], seed, gens=run.GENS)
            trajs[f"main_{arm}_{seed}"] = tr
            row = {"condition": "main", "q": run.Q, "o": run.O, "e": run.E, "a": run.A, "start_allc": START[0],
                   "start_disc": START[1], "start_alld": START[2], "arm": arm, "seed": seed, "gens": len(tr) - 1,
                   "final_alld": float(tr[-1, 0]), "final_allc": float(tr[-1, 1]), "final_disc": float(tr[-1, 2]),
                   "coop_gen100": float(tr[100, 1] + tr[100, 2]), "max_alld": float(tr[:, 0].max())}
            for idx, f in enumerate(run.FIELDS):
                row[f] = float(st[idx] + g1[idx])
                row["g1_" + f] = float(g1[idx])
            rows.append(row)
    with open(run.DATA / f"{PREFIX}runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(run.DATA / f"{PREFIX}traj.npz", **trajs)
    v, t, sh = verdict(rows)

    def ratio(rs, x, y):
        d = sum(r[y] for r in rs)
        return sum(r[x] for r in rs) / d if d else float("nan")

    lines = [f"rung 4a attempt 2 registered run: {len(rows)} runs in {time.time() - t0:.1f} s",
             f"main (ALLC 0.05 / DISC 0.85 / ALLD 0.1): test {t}/20 and shuffled {sh}/20 with cooperators >= {run.ENDPOINT} after generation {run.GENS}",
             f"sanity: violations in test-arm runs: {int(sum(r['violations'] for r in rows if r['arm'] == 'test'))}",
             f"VERDICT: {v}", "",
             "arm (seeds coop >= 0.8 | mean final ALLC / DISC / ALLD | mean coop gen 100 | mean max ALLD | help rate gen 1 / pooled |",
             "gen-1 good share of consulted ALLC / DISC / ALLD); per-seed final cooperators:"]
    for arm in ("test", "shuffled"):
        rs = [r for r in rows if r["arm"] == arm]
        lines.append(f"  {arm:8s}: {sum(r['final_allc'] + r['final_disc'] >= run.ENDPOINT - 1e-12 for r in rs):2d}/20 | "
                     f"{np.mean([r['final_allc'] for r in rs]):.3f} / {np.mean([r['final_disc'] for r in rs]):.3f} / {np.mean([r['final_alld'] for r in rs]):.3f} | "
                     f"{np.mean([r['coop_gen100'] for r in rs]):.3f} | {np.mean([r['max_alld'] for r in rs]):.3f} | "
                     f"{ratio(rs, 'g1_helps', 'g1_encounters'):.3f} / {ratio(rs, 'helps', 'encounters'):.3f} | "
                     f"{ratio(rs, 'g1_consult_allc_good', 'g1_consult_allc'):.3f} / {ratio(rs, 'g1_consult_disc_good', 'g1_consult_disc'):.3f} / "
                     f"{ratio(rs, 'g1_consult_alld_good', 'g1_consult_alld'):.3f}")
        lines.append("    " + " ".join(f"{r['seed']}:{r['final_allc'] + r['final_disc']:.2f}" for r in rs))
    text = "\n".join(lines)
    (run.DATA / f"{PREFIX}verdict.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
