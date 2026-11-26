"""Registered rung-2b run (README.md, "Rung 2b") and verdict.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2b.run

Main test: q = 0.6, o = 0.5, start 90% DISC, 500 generations, seeds 0-19, test vs shuffled. Met if test ends with
DISC >= 0.8 in >= 16/20 seeds and shuffled in <= 4/20. Sanity: no DISC assessed bad in any test-arm run (else
INVALID pending inspection). Reported (test arm only): (q, o) = (0.6, 0.25), (0.6, 0.1), (1.0, 0.1), (0.45, 0.5),
(0.6, 1.0). Writes data/rung2b_runs.csv, rung2b_traj.npz, rung2b_verdict.txt.
"""

import csv
import math
import time
from pathlib import Path

import numpy as np

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2b import model

GENS = 500
SEEDS = tuple(range(20))
ENDPOINT = 0.8
START = 0.9
ARMS = {"test": model.TEST, "shuffled": model.SHUFFLED}
CONDITIONS = {  # name: (q, o, arms)
    "main": (0.6, 0.5, ("test", "shuffled")),
    "o025": (0.6, 0.25, ("test",)),
    "o010": (0.6, 0.1, ("test",)),
    "o010_q1": (1.0, 0.1, ("test",)),
    "q045": (0.45, 0.5, ("test",)),
    "o100": (0.6, 1.0, ("test",)),
}
DATA = Path(__file__).resolve().parent / "data"
COUNTERS = ("disc_bad", "disc_bad_g1", "g1_consult_alld", "g1_consult_alld_good", "g1_alld_unobserved", "g1_alld",
            "consult_alld", "consult_alld_good")


def _row_ok(r):
    if any(not (math.isfinite(r[c]) and r[c] >= 0 and r[c] == int(r[c])) for c in COUNTERS):
        return False
    if not (math.isfinite(r["disc_gen100"]) and 0.0 <= r["disc_gen100"] <= 1.0):
        return False
    return (r["g1_consult_alld_good"] <= r["g1_consult_alld"] and r["consult_alld_good"] <= r["consult_alld"]
            and r["g1_consult_alld"] <= r["consult_alld"] and r["g1_alld"] == round((1 - START) * 1000)
            and r["g1_alld_unobserved"] <= r["g1_alld"])


def verdict(rows):
    try:
        keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
        need = {(c, a, s) for c, (_, _, arms) in CONDITIONS.items() for a in arms for s in SEEDS}
        bad = (len(keys) != len(set(keys)) or set(keys) != need
               or any(r["gens"] != GENS or r["start_disc"] != START
                      or not (math.isfinite(r["final_disc"]) and 0.0 <= r["final_disc"] <= 1.0)
                      or (r["q"], r["o"]) != CONDITIONS[r["condition"]][:2]
                      or not _row_ok(r)
                      for r in rows))
    except (KeyError, TypeError):
        bad = True
    if bad:
        return "NO VERDICT (data)", None, None
    if any(r["arm"] == "test" and (r["disc_bad"] > 0 or r["disc_bad_g1"] > 0) for r in rows):
        return "INVALID (sanity: a DISC was assessed bad in the test arm; inspection pending)", None, None
    main = {(r["arm"], r["seed"]): r for r in rows if r["condition"] == "main"}
    t = sum(main[("test", s)]["final_disc"] >= ENDPOINT for s in SEEDS)
    sh = sum(main[("shuffled", s)]["final_disc"] >= ENDPOINT for s in SEEDS)
    return ("MET" if t >= 16 and sh <= 4 else "NOT MET"), t, sh


def main():
    DATA.mkdir(exist_ok=True)
    model.run(0.6, 0.5, START, model.TEST, 0, gens=2)  # compile
    rows, trajs = [], {}
    t0 = time.time()
    for name, (q, o, arms) in CONDITIONS.items():
        for arm in arms:
            for seed in SEEDS:
                tr, st, g1 = model.run(q, o, START, ARMS[arm], seed, gens=GENS)
                trajs[f"{name}_{arm}_{seed}"] = tr
                rows.append({"condition": name, "q": q, "o": o, "start_disc": START, "arm": arm, "seed": seed,
                             "gens": len(tr) - 1, "final_disc": float(tr[-1]), "disc_gen100": float(tr[100]),
                             "disc_bad": float(st[0]), "disc_bad_g1": float(g1[0]),
                             "g1_consult_alld": float(g1[1]), "g1_consult_alld_good": float(g1[2]),
                             "g1_alld_unobserved": float(g1[4]), "g1_alld": float(g1[5]),
                             "consult_alld": float(st[1] + g1[1]), "consult_alld_good": float(st[2] + g1[2])})
    with open(DATA / "rung2b_runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(DATA / "rung2b_traj.npz", **trajs)
    v, t, sh = verdict(rows)

    def ratio(rs, a, b):
        d = sum(r[b] for r in rs)
        return sum(r[a] for r in rs) / d if d else float("nan")

    lines = [f"rung 2b registered run: {len(rows)} runs in {time.time() - t0:.1f} s",
             f"main (q=0.6, o=0.5, start 0.9): test {t}/20 and shuffled {sh}/20 with DISC >= {ENDPOINT} after generation {GENS}",
             f"sanity: DISC assessed bad in test-arm runs: {int(sum(r['disc_bad'] + r['disc_bad_g1'] for r in rows if r['arm'] == 'test'))}",
             f"VERDICT: {v}", "",
             "condition (seeds DISC >= 0.8 | mean final | mean gen 100 | gen-1 share of consulted ALLD with good record |",
             "pooled share until fixation | gen-1 share of ALLD with no observed act):"]
    for name, (q, o, arms) in CONDITIONS.items():
        for arm in arms:
            rs = [r for r in rows if r["condition"] == name and r["arm"] == arm]
            lines.append(f"  {name:8s} q={q} o={o} {arm:8s}: {sum(r['final_disc'] >= ENDPOINT for r in rs):2d}/20 | "
                         f"{np.mean([r['final_disc'] for r in rs]):.4f} | {np.mean([r['disc_gen100'] for r in rs]):.4f} | "
                         f"{ratio(rs, 'g1_consult_alld_good', 'g1_consult_alld'):.4f} | {ratio(rs, 'consult_alld_good', 'consult_alld'):.4f} | "
                         f"{ratio(rs, 'g1_alld_unobserved', 'g1_alld'):.4f}")
    text = "\n".join(lines)
    (DATA / "rung2b_verdict.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
