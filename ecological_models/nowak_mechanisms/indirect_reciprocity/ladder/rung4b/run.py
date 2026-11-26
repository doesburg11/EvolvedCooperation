"""Registered rung-4b run (README.md, "Rung 4b: mutation, on the rebased setting q = 0.8") and verdict.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b.run

800 runs: main (mu 0.001, start 0.1/0.8/0.1; test and shuffled), mu002 / mu004 / mu005 (main start), all_disc and
all_alld (mu 0.001), image (main start); seeds 2000-2099; 2,000 generations; q 0.8, o 0.5, e 0.1, a 0.02.
Met if >= 80/100 test runs meet BOTH endpoints (cooperators >= 0.8 at generation 500, and mean cooperator share over
generations 1501-2000 >= 0.8) and the shuffled arm meets each endpoint in <= 20/100. Validation of all 800 runs;
sanity (test arms): rung 4a's rule. Outputs: data/ (runs CSV, counts NPZ, summary JSON). One attempt: an attempt
marker is claimed before running; a stage that was started cannot be started again.
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.stats import binom

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DATA = HERE / "data"
N, K, GENS = 1000, 10, 2000
B_, C_, S_ = 3.0, 1.0, 0.1
WORKERS = 16
Q, O, E, A = 0.8, 0.5, 0.1, 0.02
SEEDS = tuple(range(2000, 2100))
G_END, WIN = 500, (1501, 2000)
ENDPOINT, T_MIN, SH_MAX = 0.8, 80, 20
ARMS = {"test": 0, "shuffled": 1, "image": 2}      # rung 4a's TEST, SHUFFLED, IMAGE
MAIN = (0.1, 0.8, 0.1)
CONDITIONS = {  # name: (mu, start (ALLC, DISC, ALLD), arms)
    "main": (0.001, MAIN, ("test", "shuffled")),
    "mu002": (0.002, MAIN, ("test",)),
    "mu004": (0.004, MAIN, ("test",)),
    "mu005": (0.005, MAIN, ("test",)),
    "all_disc": (0.001, (0.0, 1.0, 0.0), ("test",)),
    "all_alld": (0.001, (0.0, 0.0, 1.0), ("test",)),
    "image": (0.001, MAIN, ("image",)),
}
FIELDS = ("violations", "consult_alld", "consult_alld_good", "helps", "consult_disc", "consult_disc_good",
          "qual_fail_consult", "qual_fail_noconsult", "disc_bad", "flips_good", "flips_bad", "flips_alld",
          "consult_allc", "consult_allc_good", "allc_qual_fail", "allc_bad", "encounters", "allc_intends")


def git_state():
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", str(HERE.parent.relative_to(ROOT))],
                           capture_output=True, text=True).stdout.strip()
    return commit, dirty == ""


def jobs():
    return [(c, arm, s) for c, (_, _, arms) in CONDITIONS.items() for arm in arms for s in SEEDS]


def endpoints(counts):
    coop = (N - counts[:, 0]) / N                      # ALLC + DISC = N - ALLD
    return float(coop[G_END]), float(coop[WIN[0]:WIN[1] + 1].mean()), coop


def run_one(job):
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b import model
    c, arm, seed = job
    mu, start, _ = CONDITIONS[c]
    counts, audit, st, g1 = model.run(Q, O, E, A, mu, start, ARMS[arm], seed, gens=GENS, n=N, k=K, b=B_, c=C_, s=S_)
    mutants = audit[:, 3:6].sum(1)
    g500, win, coop = endpoints(counts)
    below = np.nonzero(coop < 0.5)[0]
    row = {"condition": c, "arm": arm, "seed": seed, "q": Q, "o": O, "e": E, "a": A, "mu": mu,
           "n": N, "k": K, "b": B_, "c": C_, "s": S_,
           "start_allc": start[0], "start_disc": start[1], "start_alld": start[2], "gens": len(counts) - 1,
           "coop_g500": g500, "coop_window": win,
           "final_alld": counts[-1, 0] / N, "final_allc": counts[-1, 1] / N,
           "final_disc": (N - counts[-1, 0] - counts[-1, 1]) / N,
           "win_alld": float(counts[WIN[0]:WIN[1] + 1, 0].mean() / N),
           "win_allc": float(counts[WIN[0]:WIN[1] + 1, 1].mean() / N),
           "max_alld": float(counts[:, 0].max() / N),
           "first_below_05": int(below[0]) if len(below) else -1,
           "mutants_total": int(mutants.sum()), "mutants_max_gen": int(mutants.max())}
    for i, f in enumerate(FIELDS):
        row[f] = float(st[i] + g1[i])
        row["g1_" + f] = float(g1[i])
    return row, counts.astype(np.int16), audit.astype(np.int32)


def validate(rows, counts, audits):
    """Raise ValueError on any failure of the registered validity rules (all 800 runs)."""
    keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != set(jobs()):
        raise ValueError("run set incomplete or duplicated")
    for r in rows:
        key = (r["condition"], r["arm"], r["seed"])
        mu, start, _ = CONDITIONS[r["condition"]]
        if (r["n"], r["k"], r["b"], r["c"], r["s"]) != (N, K, B_, C_, S_):
            raise ValueError(f"{key}: frozen model constants differ")
        if (r["q"], r["o"], r["e"], r["a"], r["mu"]) != (Q, O, E, A, mu) or \
                (r["start_allc"], r["start_disc"], r["start_alld"]) != start or r["gens"] != GENS:
            raise ValueError(f"{key}: frozen settings differ")
        raw = np.asarray(counts[key])
        if raw.shape != (GENS + 1, 2) or not np.issubdtype(raw.dtype, np.integer):
            raise ValueError(f"{key}: trajectory shape or type")
        cnt = raw.astype(np.int64)
        if (cnt < 0).any() or (cnt.sum(1) > N).any():
            raise ValueError(f"{key}: bad trajectory")
        au = np.asarray(audits[key])
        if au.shape != (GENS, 10) or not np.issubdtype(au.dtype, np.integer):
            raise ValueError(f"{key}: audit shape or type")
        au = au.astype(np.int64)
        pre_c, pre_d, pre_a, m_c, m_d, m_a, c_d, d_c, a_c, enc = au.T
        if (au < 0).any() or (pre_c + pre_d + pre_a != N).any():
            raise ValueError(f"{key}: offspring accounting")
        if (m_c > pre_c).any() or (m_d > pre_d).any() or (m_a > pre_a).any() or \
                (c_d > m_c).any() or (d_c > m_d).any() or (a_c > m_a).any():
            raise ValueError(f"{key}: mutants exceed their source")
        post_c = pre_c - m_c + d_c + a_c
        post_a = pre_a - m_a + (m_c - c_d) + (m_d - d_c)
        if not (np.array_equal(post_a, cnt[1:, 0]) and np.array_equal(post_c, cnt[1:, 1])):
            raise ValueError(f"{key}: transfers do not balance with the trajectory")
        if mu == 0.0 and (m_c + m_d + m_a).any():
            raise ValueError(f"{key}: mutants with mu = 0")
        if not (enc == N * K).all():
            raise ValueError(f"{key}: a generation did not play all encounters")
        mtot = int((m_c + m_d + m_a).sum())
        if r["mutants_total"] != mtot or r["mutants_max_gen"] != int((m_c + m_d + m_a).max()):
            raise ValueError(f"{key}: mutant summaries do not match the audit")
        if cnt[0, 0] != round(start[2] * N) or cnt[0, 1] != round(start[0] * N):
            raise ValueError(f"{key}: start counts")
        g500, win, _ = endpoints(cnt)
        if g500 != r["coop_g500"] or win != r["coop_window"]:
            raise ValueError(f"{key}: endpoints do not match the trajectory")
        for pre, cap in (("", N * K * GENS), ("g1_", N * K)):
            for f in FIELDS:
                v = r[pre + f]
                if not (math.isfinite(v) and 0 <= v <= cap and v == int(v)):
                    raise ValueError(f"{key}: counter {pre}{f}")
            for num, den in (("consult_alld_good", "consult_alld"), ("consult_disc_good", "consult_disc"),
                             ("consult_allc_good", "consult_allc"), ("helps", "encounters"),
                             ("allc_intends", "encounters")):
                if r[pre + num] > r[pre + den]:
                    raise ValueError(f"{key}: {pre}{num} > {pre}{den}")
            if r[pre + "consult_alld"] + r[pre + "consult_disc"] + r[pre + "consult_allc"] + r[pre + "allc_intends"] \
                    > r[pre + "encounters"]:
                raise ValueError(f"{key}: {pre}encounter accounting")
        if r["encounters"] != N * K * GENS or r["g1_encounters"] != N * K:
            raise ValueError(f"{key}: not every generation played all encounters")
        if any(r["g1_" + f] > r[f] for f in FIELDS):
            raise ValueError(f"{key}: generation-1 counter above the run total")
        for pre in ("", "g1_"):
            if r[pre + "flips_alld"] > r[pre + "flips_good"] + r[pre + "flips_bad"]:
                raise ValueError(f"{key}: {pre}flips")
        if r["g1_allc_intends"] != round(start[0] * N) * K:
            raise ValueError(f"{key}: every ALLC intends to help in each of its donor turns in generation 1")


def verdict(rows):
    if any(r["arm"] == "test" and (r["violations"] > 0 or r["g1_violations"] > 0) for r in rows):
        return "INVALID (sanity violation in a test arm; inspection pending)", None, None, None
    main = {(r["arm"], r["seed"]): r for r in rows if r["condition"] == "main"}
    ok = lambda v: v >= ENDPOINT - 1e-12
    t_joint = sum(ok(main[("test", s)]["coop_g500"]) and ok(main[("test", s)]["coop_window"]) for s in SEEDS)
    sh_g500 = sum(ok(main[("shuffled", s)]["coop_g500"]) for s in SEEDS)
    sh_win = sum(ok(main[("shuffled", s)]["coop_window"]) for s in SEEDS)
    met = t_joint >= T_MIN and sh_g500 <= SH_MAX and sh_win <= SH_MAX
    return ("MET" if met else "NOT MET"), t_joint, sh_g500, sh_win


def describe(rows):
    ok = lambda v: v >= ENDPOINT - 1e-12
    out = {}
    for c, (mu, start, arms) in CONDITIONS.items():
        for arm in arms:
            rr = [r for r in rows if r["condition"] == c and r["arm"] == arm]

            def ratio(num, den):
                d = sum(r[den] for r in rr)
                return float(sum(r[num] for r in rr) / d) if d else None

            lo, hi = binom.ppf(0.0005, N * GENS, mu), binom.ppf(0.9995, N * GENS, mu)
            out[f"{c}_{arm}"] = dict(
                runs=len(rr), g500=int(sum(ok(r["coop_g500"]) for r in rr)),
                window=int(sum(ok(r["coop_window"]) for r in rr)),
                joint=int(sum(ok(r["coop_g500"]) and ok(r["coop_window"]) for r in rr)),
                mean_coop_g500=float(np.mean([r["coop_g500"] for r in rr])),
                mean_coop_window=float(np.mean([r["coop_window"] for r in rr])),
                mean_win_allc=float(np.mean([r["win_allc"] for r in rr])),
                mean_win_alld=float(np.mean([r["win_alld"] for r in rr])),
                mean_max_alld=float(np.mean([r["max_alld"] for r in rr])),
                ever_below_05=int(sum(r["first_below_05"] >= 0 for r in rr)),
                help_rate_g1=ratio("g1_helps", "g1_encounters"), help_rate_pooled=ratio("helps", "encounters"),
                g1_good_consulted_allc=ratio("g1_consult_allc_good", "g1_consult_allc"),
                g1_good_consulted_disc=ratio("g1_consult_disc_good", "g1_consult_disc"),
                g1_good_consulted_alld=ratio("g1_consult_alld_good", "g1_consult_alld"),
                mean_mutants=float(np.mean([r["mutants_total"] for r in rr])),
                mutant_range_999=[float(lo), float(hi)],
                mutants_outside_range=int(sum(not (lo <= r["mutants_total"] <= hi) for r in rr)))
    return out


def main(workers):
    summ = DATA / "rung4b_summary.json"
    commit, clean = git_state()
    if not clean:
        raise SystemExit("ladder tree not clean; commit first")
    DATA.mkdir(exist_ok=True)
    if summ.exists() or (DATA / "rung4b_runs.csv").exists():
        raise SystemExit("rung 4b was already started (outputs exist); a rerun needs a documented repair")
    try:
        with open(DATA / "rung4b.attempt", "x") as fh:
            fh.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
    except FileExistsError:
        raise SystemExit("rung 4b was already started (attempt marker exists)")
    t0 = time.time()
    res = {"commit": commit, "seeds": [SEEDS[0], SEEDS[-1]], "gens": GENS, "thresholds": [T_MIN, SH_MAX]}
    try:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            out = list(ex.map(run_one, jobs(), chunksize=4))
        rows = [o[0] for o in out]
        counts = {(r["condition"], r["arm"], r["seed"]): o[1] for r, o in zip(rows, out)}
        audits = {(r["condition"], r["arm"], r["seed"]): o[2] for r, o in zip(rows, out)}
        with open(DATA / "rung4b_runs.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        np.savez_compressed(DATA / "rung4b_counts.npz", **{f"{c}_{a}_{s}": v for (c, a, s), v in counts.items()},
                            **{f"audit_{r['condition']}_{r['arm']}_{r['seed']}": o[2] for r, o in zip(rows, out)})
        validate(rows, counts, audits)
        v, t, sh5, shw = verdict(rows)
        res.update(verdict=v, test_joint=t, shuffled_g500=sh5, shuffled_window=shw,
                   reported=describe(rows) if not v.startswith("INVALID") else None)
    except Exception as exc:
        res.update(verdict=f"NO VERDICT ({exc!r})", reported=None)
    res["seconds"] = time.time() - t0
    summ.write_text(json.dumps(res, indent=1))
    print(f"rung 4b: test (both endpoints) {res.get('test_joint')}/100, shuffled {res.get('shuffled_g500')}/100 "
          f"(gen 500) and {res.get('shuffled_window')}/100 (window) -> {res['verdict']} in {res['seconds']:.0f} s")
    return res


if __name__ == "__main__":
    main(WORKERS)
