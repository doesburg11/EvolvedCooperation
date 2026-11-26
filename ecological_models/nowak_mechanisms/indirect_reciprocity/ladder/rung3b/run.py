"""Registered rung-3b run (README.md, "Rung 3b") and verdict.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3b.run

Main test: q = 0.6, o = 0.5, e = 0.1, a = 0.02, start 90% DISC, 500 generations, seeds 0-19, test vs shuffled. Met
if test ends with DISC >= 0.8 in >= 16/20 seeds and shuffled in <= 4/20. Sanity: no violation in any test-arm run
(else INVALID pending inspection). Reported (test arm): a = 0, 0.05, 0.1, 0.2.
Writes data/rung3b_runs.csv, rung3b_traj.npz, rung3b_verdict.txt.
"""

import csv
import math
import time
from pathlib import Path

import numpy as np

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3b import model

GENS = 500
SEEDS = tuple(range(20))
ENDPOINT = 0.8
START, Q, O, E = 0.9, 0.6, 0.5, 0.1
ARMS = {"test": model.TEST, "shuffled": model.SHUFFLED}
CONDITIONS = {  # name: (a, arms)
    "main": (0.02, ("test", "shuffled")),
    "a000": (0.0, ("test",)),
    "a005": (0.05, ("test",)),
    "a010": (0.1, ("test",)),
    "a020": (0.2, ("test",)),
}
FIELDS = ("violations", "consult_alld", "consult_alld_good", "helps", "consult_disc", "consult_disc_good",
          "qual_fail_consult", "qual_fail_noconsult", "disc_bad", "flips_good", "flips_bad", "flips_alld")
DATA = Path(__file__).resolve().parent / "data"


def _row_ok(r):
    acts_run, acts_gen = 1000 * 10 * GENS, 1000 * 10
    for pre, cap in (("", acts_run), ("g1_", acts_gen)):
        for f in FIELDS:
            v = r[pre + f]
            if not (math.isfinite(v) and 0 <= v <= cap and v == int(v)):
                return False
        if r[pre + "consult_alld_good"] > r[pre + "consult_alld"] or r[pre + "consult_disc_good"] > r[pre + "consult_disc"]:
            return False
        if r[pre + "flips_alld"] > r[pre + "flips_good"] + r[pre + "flips_bad"]:
            return False
        if CONDITIONS[r["condition"]][0] == 0.0 and r[pre + "flips_good"] + r[pre + "flips_bad"] > 0:
            return False  # a = 0 makes no flip draw
    if any(r["g1_" + f] > r[f] for f in FIELDS):
        return False
    return math.isfinite(r["disc_gen100"]) and 0.0 <= r["disc_gen100"] <= 1.0


def verdict(rows):
    try:
        keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
        need = {(c, a, s) for c, (_, arms) in CONDITIONS.items() for a in arms for s in SEEDS}
        bad = (len(keys) != len(set(keys)) or set(keys) != need
               or any(r["gens"] != GENS or (r["q"], r["o"], r["e"], r["start_disc"]) != (Q, O, E, START)
                      or r["a"] != CONDITIONS[r["condition"]][0]
                      or not (math.isfinite(r["final_disc"]) and 0.0 <= r["final_disc"] <= 1.0)
                      or not _row_ok(r) for r in rows))
    except (KeyError, TypeError):
        bad = True
    if bad:
        return "NO VERDICT (data)", None, None
    if any(r["arm"] == "test" and (r["violations"] > 0 or r["g1_violations"] > 0) for r in rows):
        return "INVALID (sanity violation in the test arm; inspection pending)", None, None
    main = {(r["arm"], r["seed"]): r for r in rows if r["condition"] == "main"}
    t = sum(main[("test", s)]["final_disc"] >= ENDPOINT for s in SEEDS)
    sh = sum(main[("shuffled", s)]["final_disc"] >= ENDPOINT for s in SEEDS)
    return ("MET" if t >= 16 and sh <= 4 else "NOT MET"), t, sh


def main():
    DATA.mkdir(exist_ok=True)
    model.run(Q, O, E, 0.02, START, model.TEST, 0, gens=2)  # compile
    rows, trajs = [], {}
    t0 = time.time()
    for name, (a, arms) in CONDITIONS.items():
        for arm in arms:
            for seed in SEEDS:
                tr, st, g1 = model.run(Q, O, E, a, START, ARMS[arm], seed, gens=GENS)
                trajs[f"{name}_{arm}_{seed}"] = tr
                row = {"condition": name, "q": Q, "o": O, "e": E, "a": a, "start_disc": START, "arm": arm, "seed": seed,
                       "gens": len(tr) - 1, "final_disc": float(tr[-1]), "disc_gen100": float(tr[100])}
                for idx, f in enumerate(FIELDS):
                    row[f] = float(st[idx] + g1[idx])
                    row["g1_" + f] = float(g1[idx])
                rows.append(row)
    with open(DATA / "rung3b_runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(DATA / "rung3b_traj.npz", **trajs)
    v, t, sh = verdict(rows)

    def ratio(rs, x, y):
        d = sum(r[y] for r in rs)
        return sum(r[x] for r in rs) / d if d else float("nan")

    lines = [f"rung 3b registered run: {len(rows)} runs in {time.time() - t0:.1f} s",
             f"main (q=0.6, o=0.5, e=0.1, a=0.02, start 0.9): test {t}/20 and shuffled {sh}/20 with DISC >= {ENDPOINT} after generation {GENS}",
             f"sanity: violations in test-arm runs: {int(sum(r['violations'] for r in rows if r['arm'] == 'test'))}",
             f"VERDICT: {v}", "",
             "condition (seeds DISC >= 0.8 | mean final | mean gen 100 | gen-1 good share of consulted DISC | of consulted ALLD |",
             "pooled until fixation: DISC | ALLD | flips to good / to bad):"]
    for name, (a, arms) in CONDITIONS.items():
        for arm in arms:
            rs = [r for r in rows if r["condition"] == name and r["arm"] == arm]
            lines.append(f"  {name:5s} a={a} {arm:8s}: {sum(r['final_disc'] >= ENDPOINT for r in rs):2d}/20 | "
                         f"{np.mean([r['final_disc'] for r in rs]):.4f} | {np.mean([r['disc_gen100'] for r in rs]):.4f} | "
                         f"{ratio(rs, 'g1_consult_disc_good', 'g1_consult_disc'):.4f} | {ratio(rs, 'g1_consult_alld_good', 'g1_consult_alld'):.4f} | "
                         f"{ratio(rs, 'consult_disc_good', 'consult_disc'):.4f} | {ratio(rs, 'consult_alld_good', 'consult_alld'):.4f} | "
                         f"{int(sum(r['flips_good'] for r in rs))}/{int(sum(r['flips_bad'] for r in rs))}")
    text = "\n".join(lines)
    (DATA / "rung3b_verdict.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
