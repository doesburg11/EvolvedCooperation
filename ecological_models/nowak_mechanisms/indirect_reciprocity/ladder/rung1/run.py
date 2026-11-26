"""Registered rung-1 run (README.md, "Rung 1") and verdict.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung1.run

Main test: q = 0.6, start 90% DISC, 500 generations, seeds 0-19, test vs shuffled. Met if the test arm ends with
DISC >= 0.8 in >= 16/20 seeds and the shuffled arm in <= 4/20. Reported, not tests: q = 0.2 (start 90%) and a rare
start (5% DISC, q = 0.6), both arms. Writes data/rung1_runs.csv, data/rung1_traj.npz, data/rung1_verdict.txt.
"""

import csv
import itertools
import math
import time
from pathlib import Path

import numpy as np

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung1 import model

GENS = 500
SEEDS = tuple(range(20))
ENDPOINT = 0.8
CONDITIONS = {  # name: (q, start_disc, registered test?)
    "main": (0.6, 0.9, True),
    "low_q": (0.2, 0.9, False),
    "rare": (0.6, 0.05, False),
}
DATA = Path(__file__).resolve().parent / "data"


def verdict(rows):
    """Registered verdict from the main condition's rows."""
    try:
        keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
        need = {(c, a, s) for c in CONDITIONS for a in ("test", "shuffled") for s in SEEDS}
        bad = (len(keys) != len(set(keys)) or set(keys) != need
               or any(r["gens"] != GENS or not (math.isfinite(r["final_disc"]) and 0.0 <= r["final_disc"] <= 1.0)
                      or (r["q"], r["start_disc"]) != CONDITIONS[r["condition"]][:2] for r in rows))
    except (KeyError, TypeError):
        bad = True
    if bad:
        return "NO VERDICT (data)", None, None
    main = [r for r in rows if r["condition"] == "main"]
    by = {(r["arm"], r["seed"]): r for r in main}
    t = sum(by[("test", s)]["final_disc"] >= ENDPOINT for s in SEEDS)
    sh = sum(by[("shuffled", s)]["final_disc"] >= ENDPOINT for s in SEEDS)
    return ("MET" if t >= 16 and sh <= 4 else "NOT MET"), t, sh


def main():
    DATA.mkdir(exist_ok=True)
    model.run(0.6, 0.9, False, 0, gens=2)  # compile
    rows, trajs = [], {}
    t0 = time.time()
    for (name, (q, start, _)), arm, seed in itertools.product(CONDITIONS.items(), ("test", "shuffled"), SEEDS):
        tr = model.run(q, start, arm == "shuffled", seed, gens=GENS)
        trajs[f"{name}_{arm}_{seed}"] = tr
        rows.append({"condition": name, "q": q, "start_disc": start, "arm": arm, "seed": seed, "gens": len(tr) - 1,
                     "final_disc": float(tr[-1]), "disc_gen100": float(tr[100])})
    with open(DATA / "rung1_runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(DATA / "rung1_traj.npz", **trajs)
    v, t, sh = verdict(rows)
    lines = [f"rung 1 registered run: {len(rows)} runs in {time.time() - t0:.1f} s",
             f"main (q=0.6, start 0.9): test {t}/20 and shuffled {sh}/20 with DISC >= {ENDPOINT} after generation {GENS}",
             f"VERDICT: {v}", "", "reported, not tests (seeds with DISC >= 0.8 | mean final DISC | mean DISC at gen 100):"]
    for name in CONDITIONS:
        for arm in ("test", "shuffled"):
            rs = [r for r in rows if r["condition"] == name and r["arm"] == arm]
            lines.append(f"  {name:6s} {arm:8s}: {sum(r['final_disc'] >= ENDPOINT for r in rs):2d}/20 | "
                         f"{np.mean([r['final_disc'] for r in rs]):.4f} | {np.mean([r['disc_gen100'] for r in rs]):.4f}")
    text = "\n".join(lines)
    (DATA / "rung1_verdict.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
