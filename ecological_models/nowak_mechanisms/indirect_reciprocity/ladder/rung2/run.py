"""Registered rung-2 run (README.md, "Rung 2") and verdict.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2.run

Main test: q = 0.6, start 90% DISC, 500 generations, seeds 0-19, test vs shuffled. Met if test ends with DISC >= 0.8
in >= 16/20 seeds and shuffled in <= 4/20. Sanity: no DISC ever assessed bad in any test-arm run (else INVALID
pending inspection). Reported, not tests: q = 0.45 and q = 0.2 (both arms), rare start 5% (both arms), and an
image-scoring arm at q = 0.6, start 90%. Writes data/rung2_runs.csv, rung2_traj.npz, rung2_verdict.txt.
"""

import csv
import math
import time
from pathlib import Path

import numpy as np

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2 import model

GENS = 500
SEEDS = tuple(range(20))
ENDPOINT = 0.8
ARMS = {"test": model.TEST, "shuffled": model.SHUFFLED, "image": model.IMAGE}
CONDITIONS = {  # name: (q, start_disc, arms)
    "main": (0.6, 0.9, ("test", "shuffled")),
    "q045": (0.45, 0.9, ("test", "shuffled")),
    "low_q": (0.2, 0.9, ("test", "shuffled")),
    "rare": (0.6, 0.05, ("test", "shuffled")),
    "image": (0.6, 0.9, ("image",)),
}
DATA = Path(__file__).resolve().parent / "data"


def verdict(rows):
    try:
        keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
        need = {(c, a, s) for c, (_, _, arms) in CONDITIONS.items() for a in arms for s in SEEDS}
        bad = (len(keys) != len(set(keys)) or set(keys) != need
               or any(r["gens"] != GENS or not (math.isfinite(r["final_disc"]) and 0.0 <= r["final_disc"] <= 1.0)
                      or (r["q"], r["start_disc"]) != CONDITIONS[r["condition"]][:2]
                      or not (math.isfinite(r["disc_bad"]) and r["disc_bad"] >= 0 and r["disc_bad"] == int(r["disc_bad"]))
                      for r in rows))
    except (KeyError, TypeError):
        bad = True
    if bad:
        return "NO VERDICT (data)", None, None
    if any(r["arm"] == "test" and r["disc_bad"] > 0 for r in rows):
        return "INVALID (sanity: a DISC was assessed bad in the test arm; inspection pending)", None, None
    main = {(r["arm"], r["seed"]): r for r in rows if r["condition"] == "main"}
    t = sum(main[("test", s)]["final_disc"] >= ENDPOINT for s in SEEDS)
    sh = sum(main[("shuffled", s)]["final_disc"] >= ENDPOINT for s in SEEDS)
    return ("MET" if t >= 16 and sh <= 4 else "NOT MET"), t, sh


def main():
    DATA.mkdir(exist_ok=True)
    model.run(0.6, 0.9, model.TEST, 0, gens=2)  # compile
    rows, trajs = [], {}
    t0 = time.time()
    for name, (q, start, arms) in CONDITIONS.items():
        for arm in arms:
            for seed in SEEDS:
                tr, st = model.run(q, start, ARMS[arm], seed, gens=GENS)
                trajs[f"{name}_{arm}_{seed}"] = tr
                rows.append({"condition": name, "q": q, "start_disc": start, "arm": arm, "seed": seed,
                             "gens": len(tr) - 1, "final_disc": float(tr[-1]), "disc_gen100": float(tr[100]),
                             "disc_bad": float(st[0]), "consult_alld": float(st[1]), "consult_alld_good": float(st[2]),
                             "helps": float(st[3])})
    with open(DATA / "rung2_runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(DATA / "rung2_traj.npz", **trajs)
    v, t, sh = verdict(rows)
    lines = [f"rung 2 registered run: {len(rows)} runs in {time.time() - t0:.1f} s",
             f"main (q=0.6, start 0.9): test {t}/20 and shuffled {sh}/20 with DISC >= {ENDPOINT} after generation {GENS}",
             f"sanity: DISC assessed bad in test-arm runs: {int(sum(r['disc_bad'] for r in rows if r['arm'] == 'test'))}",
             f"VERDICT: {v}", "",
             "all conditions (seeds DISC >= 0.8 | mean final | mean gen 100 | share of consulted ALLD with good record,",
             "pooled over the run; encounter counts stop when a strategy fixes):"]
    for name, (q, start, arms) in CONDITIONS.items():
        for arm in arms:
            rs = [r for r in rows if r["condition"] == name and r["arm"] == arm]
            ca = sum(r["consult_alld"] for r in rs)
            g = sum(r["consult_alld_good"] for r in rs) / ca if ca else float("nan")
            lines.append(f"  {name:6s} {arm:8s}: {sum(r['final_disc'] >= ENDPOINT for r in rs):2d}/20 | "
                         f"{np.mean([r['final_disc'] for r in rs]):.4f} | {np.mean([r['disc_gen100'] for r in rs]):.4f} | {g:.4f}")
    text = "\n".join(lines)
    (DATA / "rung2_verdict.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
