"""Registered rung-5a run (README.md, "Rung 5a: private assessment, on rung 4b's base") and verdict.

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a.run

Steps (parameters are constants here, per AGENTS.md):
  1. benchmark: the fixed performance case outside the registered runs (main start, test arm, seed 9999, 100
     generations) in process CPU time; only the time is kept. Launch only if it projects the 600 runs to <= 40 CPU-h.
  2. the 600 registered runs over WORKERS processes, each writing a heartbeat (generation, CPU seconds) every 100
     generations. The runner stops the stage (no verdict) if a run raises, if a started run writes no heartbeat for
     15 minutes, or if the stage passes 40 CPU-hours. A run that loses cooperation is a result and runs to the end.
  3. validation of all 600 runs and the verdict: met if >= 80/100 test runs meet both endpoints and the shuffled arm
     meets each endpoint in <= 20/100; any stored-view check mismatch in any run, or a sanity violation in a test
     arm, makes the result invalid.
One attempt: an attempt marker is claimed before step 2.
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

import numpy as np
from scipy.stats import binom

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DATA = HERE / "data"
N, K, GENS = 1000, 10, 2000
B_, C_, S_ = 3.0, 1.0, 0.1
Q, O, E, A = 0.8, 0.5, 0.1, 0.02
SEEDS = tuple(range(3000, 3100))
G_END, WIN = 500, (1501, 2000)
ENDPOINT, T_MIN, SH_MAX = 0.8, 80, 20
WORKERS = 28
BUDGET_CPU_H, STALL_S, BENCH_SEED, BENCH_GENS = 40.0, 900.0, 9999, 100
POLL_S = 60.0
ARMS = {"test": 0, "shuffled": 1, "image": 2}
MAIN = (0.1, 0.8, 0.1)
CONDITIONS = {  # name: (mu, start (ALLC, DISC, ALLD), arms)
    "main": (0.001, MAIN, ("test", "shuffled")),
    "mu002": (0.002, MAIN, ("test",)),
    "all_disc": (0.001, (0.0, 1.0, 0.0), ("test",)),
    "all_alld": (0.001, (0.0, 0.0, 1.0), ("test",)),
    "image": (0.001, MAIN, ("image",)),
}


def git_state():
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", str(HERE.parent.relative_to(ROOT))],
                           capture_output=True, text=True).stdout.strip()
    return commit, dirty == ""


def jobs():
    return [(c, arm, s) for c, (_, _, arms) in CONDITIONS.items() for arm in arms for s in SEEDS]


def endpoints(counts):
    coop = (N - counts[:, 0]) / N
    return float(coop[G_END]), float(coop[WIN[0]:WIN[1] + 1].mean()), coop


def _hb_path(job):
    c, arm, seed = job
    return DATA / "heartbeats" / f"{c}_{arm}_{seed}.hb"


def _key(job):
    return f"{job[0]}_{job[1]}_{job[2]}"


def run_one(job):
    hb = _hb_path(job)
    c0 = time.process_time()

    def heartbeat(g):
        tmp = hb.with_suffix(".tmp")
        tmp.write_text(f"{g} {time.process_time() - c0:.1f}\n")
        os.replace(tmp, hb)

    heartbeat(0)                                    # first thing: the run is visible to the watcher at once
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import model
    c, arm, seed = job
    mu, start, _ = CONDITIONS[c]
    counts, audit, st, g1 = model.run(Q, O, E, A, mu, start, ARMS[arm], seed, gens=GENS, n=N, k=K, b=B_, c=C_,
                                      s=S_, heartbeat=heartbeat)
    g500, win, coop = endpoints(counts)
    below = np.nonzero(coop < 0.5)[0]
    mutants = audit[:, 3:6].sum(1)
    row = {"condition": c, "arm": arm, "seed": seed, "q": Q, "o": O, "e": E, "a": A, "mu": mu,
           "n": N, "k": K, "b": B_, "c": C_, "s": S_,
           "start_allc": start[0], "start_disc": start[1], "start_alld": start[2], "gens": len(counts) - 1,
           "coop_g500": g500, "coop_window": win,
           "final_alld": counts[-1, 0] / N, "final_allc": counts[-1, 1] / N,
           "final_disc": (N - counts[-1, 0] - counts[-1, 1]) / N,
           "win_alld": float(counts[WIN[0]:WIN[1] + 1, 0].mean() / N),
           "win_allc": float(counts[WIN[0]:WIN[1] + 1, 1].mean() / N),
           "max_alld": float(counts[:, 0].max() / N), "first_below_05": int(below[0]) if len(below) else -1,
           "mutants_total": int(mutants.sum()), "mutants_max_gen": int(mutants.max()),
           "cpu_s": time.process_time() - c0}
    for i, f in enumerate(model.STATS):
        row[f] = float(st[i] + g1[i])
        row["g1_" + f] = float(g1[i])
    # saved at once, so that a stopped stage keeps its completed runs
    part = DATA / "runs" / f"{_key(job)}.npz"
    tmp = part.with_name(part.stem + ".partial.npz")
    np.savez_compressed(tmp, row=json.dumps(row), counts=counts.astype(np.int16), audit=audit.astype(np.int32))
    os.replace(tmp, part)
    return row, counts.astype(np.int16), audit.astype(np.int32)


def validate(rows, counts, audits):
    """Raise ValueError on any failure of the registered validity rules (all 600 runs)."""
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import model
    keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != set(jobs()):
        raise ValueError("run set incomplete or duplicated")
    enc_run, enc_gen = N * K * GENS, N * K
    for r in rows:
        key = (r["condition"], r["arm"], r["seed"])
        mu, start, _ = CONDITIONS[r["condition"]]
        if (r["n"], r["k"], r["b"], r["c"], r["s"]) != (N, K, B_, C_, S_) or \
                (r["q"], r["o"], r["e"], r["a"], r["mu"]) != (Q, O, E, A, mu) or \
                (r["start_allc"], r["start_disc"], r["start_alld"]) != start or r["gens"] != GENS:
            raise ValueError(f"{key}: frozen settings differ")
        raw = np.asarray(counts[key])
        if raw.shape != (GENS + 1, 2) or not np.issubdtype(raw.dtype, np.integer):
            raise ValueError(f"{key}: trajectory shape or type")
        cnt = raw.astype(np.int64)
        if (cnt < 0).any() or (cnt.sum(1) > N).any() or cnt[0, 0] != round(start[2] * N) or \
                cnt[0, 1] != round(start[0] * N):
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
        if not (np.array_equal(pre_a - m_a + (m_c - c_d) + (m_d - d_c), cnt[1:, 0])
                and np.array_equal(pre_c - m_c + d_c + a_c, cnt[1:, 1])):
            raise ValueError(f"{key}: transfers do not balance with the trajectory")
        if not (enc == enc_gen).all():
            raise ValueError(f"{key}: a generation did not play all encounters")
        if r["mutants_total"] != int((m_c + m_d + m_a).sum()) or r["mutants_max_gen"] != int((m_c + m_d + m_a).max()):
            raise ValueError(f"{key}: mutant summaries do not match the audit")
        g500, win, coop = endpoints(cnt)
        if g500 != r["coop_g500"] or win != r["coop_window"]:
            raise ValueError(f"{key}: endpoints do not match the trajectory")
        below = np.nonzero(coop < 0.5)[0]
        recomputed = {"final_alld": cnt[-1, 0] / N, "final_allc": cnt[-1, 1] / N,
                      "final_disc": (N - cnt[-1, 0] - cnt[-1, 1]) / N,
                      "win_alld": float(cnt[WIN[0]:WIN[1] + 1, 0].mean() / N),
                      "win_allc": float(cnt[WIN[0]:WIN[1] + 1, 1].mean() / N),
                      "max_alld": float(cnt[:, 0].max() / N),
                      "first_below_05": int(below[0]) if len(below) else -1}
        if any(r[f] != v for f, v in recomputed.items()):
            raise ValueError(f"{key}: strategy summaries do not match the trajectory")
        n_disc_g = N - cnt[:-1, 0] - cnt[:-1, 1]          # DISC at the start of each generation
        if r["disc_turns"] != K * int(n_disc_g.sum()) or r["g1_disc_turns"] != K * int(n_disc_g[0]):
            raise ValueError(f"{key}: DISC donor turns do not match the trajectory")
        if r["allc_intends"] != K * int(cnt[:-1, 1].sum()):
            raise ValueError(f"{key}: ALLC intentions do not match the trajectory")
        n0 = {"allc": int(cnt[0, 1]), "disc": int(N - cnt[0, 0] - cnt[0, 1]), "alld": int(cnt[0, 0])}
        for t, nt in n0.items():
            if r["g1_views_" + t] != (N - 1) * nt * N * K or r["views_" + t] != r["g1_views_" + t]:
                raise ValueError(f"{key}: generation-1 view denominators ({t})")
            if r["g1_goodview_" + t] > r["g1_views_" + t] or r["goodview_" + t] != r["g1_goodview_" + t]:
                raise ValueError(f"{key}: good views above views ({t})")
        for pre in ("", "g1_"):
            enc_cap = enc_run if pre == "" else enc_gen
            v = {f: r[pre + f] for f in model.STATS}
            if any(not (math.isfinite(x) and x >= 0 and x == int(x)) for x in v.values()):
                raise ValueError(f"{key}: {pre}counter not a non-negative integer")
            if v["encounters"] != enc_cap:
                raise ValueError(f"{key}: {pre}encounters")
            if not (v["disc_turns"] <= enc_cap and v["consult_disc"] <= v["disc_turns"]
                    and v["consult_good"] <= v["consult_disc"] and v["helps"] <= enc_cap
                    and v["allc_intends"] <= enc_cap and v["exec_fail"] <= enc_cap
                    and v["intent_refusals"] <= v["consult_disc"]
                    and v["observations"] <= (N - 2) * enc_cap and v["flips"] <= v["observations"]
                    and v["intent_refusal_obs_recgood"] <= v["intent_refusal_obs"] <= (N - 2) * v["intent_refusals"]
                    and v["shuffled_refusal_obs_recgood"] <= v["shuffled_refusal_obs"] <= (N - 2) * v["intent_refusals"]
                    and v["consult_alld"] + v["consult_disc_rec"] + v["consult_allc"] == v["consult_disc"]
                    and v["consult_alld_good"] <= v["consult_alld"]
                    and v["consult_disc_rec_good"] <= v["consult_disc_rec"]
                    and v["consult_allc_good"] <= v["consult_allc"]):
                raise ValueError(f"{key}: {pre}counter bounds")
        if any(r["g1_" + f] > r[f] for f in model.STATS):
            raise ValueError(f"{key}: generation-1 counter above the run total")
        if r["g1_allc_intends"] != round(start[0] * N) * K:
            raise ValueError(f"{key}: ALLC intentions in generation 1")
        if r["arm"] != "shuffled" and r["shuffled_refusal_obs"] > 0:
            raise ValueError(f"{key}: shuffled refusals outside the shuffled arm")


def verdict(rows):
    if any(r["check_mismatch"] > 0 for r in rows):
        return "INVALID (stored-view check mismatch; inspection pending)", None, None, None
    if any(r["arm"] == "test" and r["sanity_violations"] > 0 for r in rows):
        return "INVALID (sanity violation in a test arm; inspection pending)", None, None, None
    main = {(r["arm"], r["seed"]): r for r in rows if r["condition"] == "main"}
    ok = lambda v: v >= ENDPOINT - 1e-12
    t_joint = sum(ok(main[("test", s)]["coop_g500"]) and ok(main[("test", s)]["coop_window"]) for s in SEEDS)
    sh5 = sum(ok(main[("shuffled", s)]["coop_g500"]) for s in SEEDS)
    shw = sum(ok(main[("shuffled", s)]["coop_window"]) for s in SEEDS)
    return ("MET" if t_joint >= T_MIN and sh5 <= SH_MAX and shw <= SH_MAX else "NOT MET"), t_joint, sh5, shw


def describe(rows):
    ok = lambda v: v >= ENDPOINT - 1e-12
    out = {}
    for c, (mu, start, arms) in CONDITIONS.items():
        for arm in arms:
            rr = [r for r in rows if r["condition"] == c and r["arm"] == arm]

            def ratio(num, den, pre=""):
                d = sum(r[pre + den] for r in rr)
                return float(sum(r[pre + num] for r in rr) / d) if d else None

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
                help_rate_g1=ratio("helps", "encounters", "g1_"), help_rate_pooled=ratio("helps", "encounters"),
                disagreement_penalty=ratio("intent_refusal_obs_recgood", "intent_refusal_obs"),
                shuffled_refusal_recgood=ratio("shuffled_refusal_obs_recgood", "shuffled_refusal_obs"),
                g1_good_views_allc=ratio("goodview_allc", "views_allc", "g1_"),
                g1_good_views_disc=ratio("goodview_disc", "views_disc", "g1_"),
                g1_good_views_alld=ratio("goodview_alld", "views_alld", "g1_"),
                mean_mutants=float(np.mean([r["mutants_total"] for r in rr])), mutant_range_999=[float(lo), float(hi)],
                mutants_outside_range=int(sum(not (lo <= r["mutants_total"] <= hi) for r in rr)),
                mean_cpu_s=float(np.mean([r["cpu_s"] for r in rr])))
    return out


def benchmark():
    """The fixed performance case outside the registered runs; only its CPU time is kept."""
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import model
    mu, start, _ = CONDITIONS["main"]
    model.run(Q, O, E, A, mu, start, 0, 1, gens=2, n=50)       # compile
    c0 = time.process_time()
    model.run(Q, O, E, A, mu, start, ARMS["test"], BENCH_SEED, gens=BENCH_GENS, n=N, k=K, b=B_, c=C_, s=S_)
    cpu = time.process_time() - c0
    return cpu, cpu / BENCH_GENS * GENS * len(jobs()) / 3600


def main():
    summ = DATA / "rung5a_summary.json"
    commit, clean = git_state()
    if not clean:
        raise SystemExit("ladder tree not clean; commit first")
    DATA.mkdir(exist_ok=True)
    if summ.exists() or (DATA / "rung5a_runs.csv").exists() or (DATA / "rung5a.attempt").exists():
        raise SystemExit("rung 5a was already started; a rerun needs a documented repair")
    cpu, proj = benchmark()
    (DATA / "rung5a_benchmark.json").write_text(json.dumps({"cpu_s": cpu, "gens": BENCH_GENS, "seed": BENCH_SEED,
                                                            "projected_cpu_h": proj}))
    print(f"benchmark: {cpu:.1f} CPU-s for {BENCH_GENS} generations -> projected {proj:.1f} CPU-h", flush=True)
    if proj > BUDGET_CPU_H:
        raise SystemExit(f"projected {proj:.1f} CPU-h > {BUDGET_CPU_H}; not launched")
    with open(DATA / "rung5a.attempt", "x") as fh:
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
    (DATA / "heartbeats").mkdir(exist_ok=True)
    (DATA / "runs").mkdir(exist_ok=True)
    t0 = time.time()
    res = {"commit": commit, "seeds": [SEEDS[0], SEEDS[-1]], "gens": GENS, "thresholds": [T_MIN, SH_MAX],
           "benchmark_projected_cpu_h": proj}
    js = jobs()
    out = {}
    stop = None
    ex = ProcessPoolExecutor(max_workers=WORKERS)
    try:
        futs = {ex.submit(run_one, j): j for j in js}
        pending = set(futs)
        last_progress = time.time()
        while pending and stop is None:
            done, pending = wait(pending, timeout=POLL_S, return_when=FIRST_COMPLETED)
            for f in done:
                exc = f.exception()
                if exc is not None:
                    stop = f"run {futs[f]} raised {exc!r}"
                    break
                out[futs[f]] = f.result()
                last_progress = time.time()
            now = time.time()
            cpu_total = 0.0
            for j in js:
                hb = _hb_path(j)
                if j in out:
                    cpu_total += out[j][0]["cpu_s"]
                elif hb.exists():
                    g, c = hb.read_text().split()
                    cpu_total += float(c)        # CPU since the last heartbeat (<= 100 generations) not yet counted
                    mt = hb.stat().st_mtime
                    last_progress = max(last_progress, mt)
                    if now - mt > STALL_S:
                        stop = stop or f"run {j} wrote no heartbeat for {STALL_S:.0f} s"
            if now - last_progress > STALL_S:   # also catches a worker that hangs before its first heartbeat
                stop = stop or f"no progress anywhere for {STALL_S:.0f} s"
            if cpu_total / 3600 > BUDGET_CPU_H:
                stop = stop or f"stage passed {BUDGET_CPU_H} CPU-hours"
            print(time.strftime("%H:%M:%S"), f"{len(out)}/{len(js)} runs done, {cpu_total / 3600:.2f} CPU-h", flush=True)
    except BaseException as exc:                 # any watcher failure or interruption: stop, keep outputs
        stop = stop or f"watcher interrupted: {exc!r}"
    finally:
        if stop:
            for p in list(getattr(ex, "_processes", {}).values()):
                p.terminate()
            ex.shutdown(wait=True, cancel_futures=True)
            if "check failed" in stop or "sanity rule violated" in stop:
                res.update(verdict=f"INVALID (stopped: {stop}; inspection pending)", reported=None, runs_kept=len(out))
            else:
                res.update(verdict=f"NO VERDICT (stopped: {stop})", reported=None, runs_kept=len(out))
            res["seconds"] = time.time() - t0
            summ.write_text(json.dumps(res, indent=1))
        else:
            ex.shutdown(wait=True)
    if stop:
        print(f"rung 5a: {res['verdict']}", flush=True)
        return res
    rows = [out[j][0] for j in js]
    counts = {j: out[j][1] for j in js}
    audits = {j: out[j][2] for j in js}
    with open(DATA / "rung5a_runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(DATA / "rung5a_counts.npz", **{f"{c}_{a}_{s}": counts[(c, a, s)] for c, a, s in js},
                        **{f"audit_{c}_{a}_{s}": audits[(c, a, s)] for c, a, s in js})
    try:
        validate(rows, counts, audits)
        v, t, sh5, shw = verdict(rows)
        res.update(verdict=v, test_joint=t, shuffled_g500=sh5, shuffled_window=shw,
                   reported=describe(rows) if not v.startswith("INVALID") else None)
    except Exception as exc:
        res.update(verdict=f"NO VERDICT ({exc!r})", reported=None)
    res["seconds"] = time.time() - t0
    summ.write_text(json.dumps(res, indent=1))
    print(f"rung 5a: test (both endpoints) {res.get('test_joint')}/100, shuffled {res.get('shuffled_g500')}/100 "
          f"(gen 500) and {res.get('shuffled_window')}/100 (window) -> {res['verdict']}", flush=True)
    return res


if __name__ == "__main__":
    main()
