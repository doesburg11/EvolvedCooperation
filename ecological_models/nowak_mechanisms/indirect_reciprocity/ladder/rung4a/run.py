"""Registered rung-4a run (README.md, "Rung 4a") and verdict.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a.run

Main test: start ALLC 0.1 / DISC 0.8 / ALLD 0.1, q = 0.6, o = 0.5, e = 0.1, a = 0.02, 500 generations, seeds 0-19,
test vs shuffled. Met if cooperators (ALLC + DISC) >= 0.8 after generation 500 in >= 16/20 test seeds and <= 4/20
shuffled seeds. Sanity: no violation in any test-arm run (else INVALID pending inspection). Reported: no ALLC
(0/0.9/0.1, test), 0.3/0.6/0.1 (test), 0.2/0.8/0 (test), image scoring at the main start.
Writes data/rung4a_runs.csv, rung4a_traj.npz, rung4a_verdict.txt.
"""

import csv
import math
import time
from pathlib import Path

import numpy as np

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a import model

GENS = 500
SEEDS = tuple(range(20))
ENDPOINT = 0.8
Q, O, E, A = 0.6, 0.5, 0.1, 0.02
ARMS = {"test": model.TEST, "shuffled": model.SHUFFLED, "image": model.IMAGE}
CONDITIONS = {  # name: (start (ALLC, DISC, ALLD), arms)
    "main": ((0.1, 0.8, 0.1), ("test", "shuffled")),
    "no_allc": ((0.0, 0.9, 0.1), ("test",)),
    "more_allc": ((0.3, 0.6, 0.1), ("test",)),
    "no_alld": ((0.2, 0.8, 0.0), ("test",)),
    "image": ((0.1, 0.8, 0.1), ("image",)),
}
FIELDS = ("violations", "consult_alld", "consult_alld_good", "helps", "consult_disc", "consult_disc_good",
          "qual_fail_consult", "qual_fail_noconsult", "disc_bad", "flips_good", "flips_bad", "flips_alld",
          "consult_allc", "consult_allc_good", "allc_qual_fail", "allc_bad", "encounters", "allc_intends")
DATA = Path(__file__).resolve().parent / "data"


def _row_ok(r):
    for pre, cap in (("", 1000 * 10 * GENS), ("g1_", 1000 * 10)):
        for f in FIELDS:
            v = r[pre + f]
            if not (math.isfinite(v) and 0 <= v <= cap and v == int(v)):
                return False
        for num, den in (("consult_alld_good", "consult_alld"), ("consult_disc_good", "consult_disc"),
                         ("consult_allc_good", "consult_allc"), ("helps", "encounters"), ("allc_intends", "encounters")):
            if r[pre + num] > r[pre + den]:
                return False
        if r[pre + "flips_alld"] > r[pre + "flips_good"] + r[pre + "flips_bad"]:
            return False
    if any(r["g1_" + f] > r[f] for f in FIELDS):
        return False
    if r["g1_encounters"] != 1000 * 10 and r["start_allc"] * r["start_disc"] + r["start_alld"] * r["start_disc"] + r["start_alld"] * r["start_allc"] > 0:
        return False  # generation 1 always plays when two strategies are present
    if r["start_allc"] == 0 and (r["allc_intends"] > 0 or r["final_allc"] > 0):
        return False
    if r["start_alld"] == 0 and (r["final_alld"] > 0 or r["max_alld"] > 0):
        return False  # no mutation: an absent strategy cannot reappear
    if r["g1_allc_intends"] != round(r["start_allc"] * 1000) * 10:
        return False  # every ALLC intends to help in each of its 10 donor turns
    for pre in ("", "g1_"):
        if r[pre + "consult_alld"] + r[pre + "consult_disc"] + r[pre + "consult_allc"] + r[pre + "allc_intends"] > r[pre + "encounters"]:
            return False
    for f in ("final_alld", "final_allc", "final_disc", "coop_gen100"):
        if not (math.isfinite(r[f]) and 0.0 <= r[f] <= 1.0):
            return False
    return abs(r["final_alld"] + r["final_allc"] + r["final_disc"] - 1.0) < 1e-9


def verdict(rows):
    try:
        keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
        need = {(c, a, s) for c, (_, arms) in CONDITIONS.items() for a in arms for s in SEEDS}
        bad = (len(keys) != len(set(keys)) or set(keys) != need
               or any(r["gens"] != GENS or (r["q"], r["o"], r["e"], r["a"]) != (Q, O, E, A)
                      or (r["start_allc"], r["start_disc"], r["start_alld"]) != CONDITIONS[r["condition"]][0]
                      or not _row_ok(r) for r in rows))
    except (KeyError, TypeError):
        bad = True
    if bad:
        return "NO VERDICT (data)", None, None
    if any(r["arm"] == "test" and (r["violations"] > 0 or r["g1_violations"] > 0) for r in rows):
        return "INVALID (sanity violation in the test arm; inspection pending)", None, None
    main = {(r["arm"], r["seed"]): r for r in rows if r["condition"] == "main"}
    coop = lambda r: r["final_allc"] + r["final_disc"]
    t = sum(coop(main[("test", s)]) >= ENDPOINT - 1e-12 for s in SEEDS)
    sh = sum(coop(main[("shuffled", s)]) >= ENDPOINT - 1e-12 for s in SEEDS)
    return ("MET" if t >= 16 and sh <= 4 else "NOT MET"), t, sh


def main():
    DATA.mkdir(exist_ok=True)
    model.run(Q, O, E, A, (0.1, 0.8, 0.1), model.TEST, 0, gens=2)  # compile
    rows, trajs = [], {}
    t0 = time.time()
    for name, (start, arms) in CONDITIONS.items():
        for arm in arms:
            for seed in SEEDS:
                tr, st, g1 = model.run(Q, O, E, A, start, ARMS[arm], seed, gens=GENS)
                trajs[f"{name}_{arm}_{seed}"] = tr
                row = {"condition": name, "q": Q, "o": O, "e": E, "a": A, "start_allc": start[0],
                       "start_disc": start[1], "start_alld": start[2], "arm": arm, "seed": seed, "gens": len(tr) - 1,
                       "final_alld": float(tr[-1, 0]), "final_allc": float(tr[-1, 1]), "final_disc": float(tr[-1, 2]),
                       "coop_gen100": float(tr[100, 1] + tr[100, 2]), "max_alld": float(tr[:, 0].max())}
                for idx, f in enumerate(FIELDS):
                    row[f] = float(st[idx] + g1[idx])
                    row["g1_" + f] = float(g1[idx])
                rows.append(row)
    with open(DATA / "rung4a_runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(DATA / "rung4a_traj.npz", **trajs)
    v, t, sh = verdict(rows)

    def ratio(rs, x, y):
        d = sum(r[y] for r in rs)
        return sum(r[x] for r in rs) / d if d else float("nan")

    lines = [f"rung 4a registered run: {len(rows)} runs in {time.time() - t0:.1f} s",
             f"main (ALLC 0.1 / DISC 0.8 / ALLD 0.1): test {t}/20 and shuffled {sh}/20 with cooperators >= {ENDPOINT} after generation {GENS}",
             f"sanity: violations in test-arm runs: {int(sum(r['violations'] for r in rows if r['arm'] == 'test'))}",
             f"VERDICT: {v}", "",
             "condition (seeds coop >= 0.8 | mean final ALLC / DISC / ALLD | mean coop gen 100 | mean max ALLD |",
             "help rate gen 1 / pooled | gen-1 good share of consulted ALLC / DISC / ALLD):"]
    for name, (start, arms) in CONDITIONS.items():
        for arm in arms:
            rs = [r for r in rows if r["condition"] == name and r["arm"] == arm]
            lines.append(f"  {name:9s} {arm:8s}: {sum(r['final_allc'] + r['final_disc'] >= ENDPOINT - 1e-12 for r in rs):2d}/20 | "
                         f"{np.mean([r['final_allc'] for r in rs]):.3f} / {np.mean([r['final_disc'] for r in rs]):.3f} / {np.mean([r['final_alld'] for r in rs]):.3f} | "
                         f"{np.mean([r['coop_gen100'] for r in rs]):.3f} | {np.mean([r['max_alld'] for r in rs]):.3f} | "
                         f"{ratio(rs, 'g1_helps', 'g1_encounters'):.3f} / {ratio(rs, 'helps', 'encounters'):.3f} | "
                         f"{ratio(rs, 'g1_consult_allc_good', 'g1_consult_allc'):.3f} / {ratio(rs, 'g1_consult_disc_good', 'g1_consult_disc'):.3f} / "
                         f"{ratio(rs, 'g1_consult_alld_good', 'g1_consult_alld'):.3f}")
    text = "\n".join(lines)
    (DATA / "rung4a_verdict.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
