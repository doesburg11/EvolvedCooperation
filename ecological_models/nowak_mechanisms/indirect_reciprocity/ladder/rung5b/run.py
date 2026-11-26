"""Registered runner for the proposed rung-5b gossip comparison (once frozen)."""

from __future__ import annotations

import csv
import json
import os
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5b import model

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
N, K, GENS = 1000, 10, 2000
Q, O, E, A, MU = 0.8, 0.5, 0.1, 0.02, 0.001
START = (0.1, 0.8, 0.1)
SEEDS = tuple(range(4000, 4100))
ARMS = (("target", model.TARGET_GOSSIP), ("none", model.NO_GOSSIP), ("sham", model.SHAM_GOSSIP))
ENDPOINT, MIN_SUCCESS, MIN_ADVANTAGE, BUDGET_CPU_H = 0.8, 80, 20, 45.0
WORKERS, BENCH_SEED, BENCH_GENS = 20, 9999, 100


def endpoint(counts):
    cooperative = N - counts[:, 0]
    return bool(cooperative[500] >= int(ENDPOINT * N) and cooperative[1501:2001].sum() >= int(ENDPOINT * N * 500))


def _heartbeat_path(job):
    name, _, seed = job
    return DATA / "heartbeats" / f"{name}_{seed}.txt"


def run_one(job):
    name, arm, seed = job
    t0 = time.process_time()

    def heartbeat(generation):
        path = _heartbeat_path(job)
        tmp = path.with_suffix(".partial")
        tmp.write_text(f"{generation} {time.process_time() - t0:.6f}\n")
        os.replace(tmp, path)

    heartbeat(0)
    counts, audit, stats, gen1 = model.run(Q, O, E, A, MU, START, arm, seed, gens=GENS, n=N, k=K, b=3.0, c=1.0,
                                            s=0.1, heartbeat=heartbeat)
    cooperative = (N - counts[:, 0]) / N
    row = dict(arm=name, seed=seed, coop_g500=float(cooperative[500]), coop_window=float(cooperative[1501:2001].mean()),
               passed=endpoint(counts), cpu_s=time.process_time() - t0,
               check_mismatch=float(stats[0] + gen1[0]), sanity_violations=float(stats[1] + gen1[1]),
               gossip_attempts=float(stats[28] + gen1[28]), gossip_changes=float(stats[29] + gen1[29]),
               gossip_noops=float(stats[30] + gen1[30]),
               refusal_obs_first=float(stats[31] + gen1[31]), refusal_recgood_first=float(stats[32] + gen1[32]),
               refusal_obs_second=float(stats[33] + gen1[33]), refusal_recgood_second=float(stats[34] + gen1[34]),
               agreement_before=float(stats[35] + gen1[35]), agreement_after=float(stats[36] + gen1[36]),
               encounters=float(stats[2] + gen1[2]), helps=float(stats[3] + gen1[3]),
               observations=float(stats[7] + gen1[7]), flips=float(stats[8] + gen1[8]),
               goodview_allc=float(stats[22] + gen1[22]), views_allc=float(stats[23] + gen1[23]),
               goodview_disc=float(stats[24] + gen1[24]), views_disc=float(stats[25] + gen1[25]),
               goodview_alld=float(stats[26] + gen1[26]), views_alld=float(stats[27] + gen1[27]))
    return row, counts.astype(np.int16), audit.astype(np.int32)


def validate_one(row, counts, audit):
    """Outcome-independent integrity checks required for every completed run."""
    if counts.shape != (GENS + 1, 2) or audit.shape != (GENS, 10):
        raise ValueError("bad stored array shape")
    if (counts < 0).any() or (counts.sum(axis=1) > N).any() or (audit < 0).any():
        raise ValueError("negative or impossible population count")
    if not (audit[:, 9] == N * K).all() or row["encounters"] != N * K * GENS:
        raise ValueError("missing encounter")
    pre_c, pre_d, pre_a, m_c, m_d, m_a, c_d, d_c, a_c = audit[:, :9].T
    if not (pre_c + pre_d + pre_a == N).all() or (m_c > pre_c).any() or (m_d > pre_d).any() or (m_a > pre_a).any():
        raise ValueError("invalid offspring or mutation audit")
    if row["check_mismatch"] or row["sanity_violations"]:
        raise ValueError("stored-view or standing audit failed")
    if row["gossip_changes"] + row["gossip_noops"] != row["gossip_attempts"]:
        raise ValueError("gossip accounting does not balance")
    if not (np.array_equal(pre_a - m_a + (m_c - c_d) + (m_d - d_c), counts[1:, 0]) and
            np.array_equal(pre_c - m_c + d_c + a_c, counts[1:, 1])):
        raise ValueError("mutation flows do not reconcile")
    if row["helps"] > row["encounters"] or row["flips"] > row["observations"]:
        raise ValueError("impossible encounter audit")


def persist_one(row, counts, audit):
    key = f"{row['arm']}_{row['seed']}"
    path = DATA / "runs" / f"{key}.npz"
    tmp = path.with_suffix(".partial.npz")
    np.savez_compressed(tmp, row=json.dumps(row), counts=counts, audit=audit)
    os.replace(tmp, path)


def paired(a, b):
    """One-sided paired McNemar details, with a/b maps keyed by seed."""
    wins = sum(a[s]["passed"] and not b[s]["passed"] for s in SEEDS)
    losses = sum(b[s]["passed"] and not a[s]["passed"] for s in SEEDS)
    p = float(binomtest(wins, wins + losses, 0.5, alternative="greater").pvalue) if wins + losses else 1.0
    return dict(wins=wins, losses=losses, advantage=wins - losses, p_one_sided=p,
                passes_a=sum(a[s]["passed"] for s in SEEDS), passes_b=sum(b[s]["passed"] for s in SEEDS))


def verdict(rows):
    if len(rows) != len(ARMS) * len(SEEDS) or any(r["check_mismatch"] or r["sanity_violations"] for r in rows):
        return {"verdict": "NO VERDICT"}
    by_arm = {name: {r["seed"]: r for r in rows if r["arm"] == name} for name, _ in ARMS}
    tn, ts = paired(by_arm["target"], by_arm["none"]), paired(by_arm["target"], by_arm["sham"])
    paired_pass = tn["advantage"] >= MIN_ADVANTAGE and tn["p_one_sided"] < 0.01
    restored = tn["passes_a"] >= MIN_SUCCESS and paired_pass
    outcome = "MET" if restored else ("INCONCLUSIVE ABOUT GOSSIP" if tn["passes_a"] >= MIN_SUCCESS else "NOT MET")
    return {"verdict": outcome, "target_vs_none": tn, "target_vs_sham": ts,
            "target_specific_support": ts["advantage"] >= MIN_ADVANTAGE and ts["p_one_sided"] < 0.01,
            "sham_reached_80": ts["passes_b"] >= MIN_SUCCESS}


def benchmark():
    for _, arm in ARMS:
        model.run(Q, O, E, A, MU, START, arm, 1, gens=2, n=50, k=10)  # compilation, discarded
    costs = []
    for _, arm in ARMS:
        t0 = time.process_time()
        model.run(Q, O, E, A, MU, START, arm, BENCH_SEED, gens=BENCH_GENS, n=N, k=K)
        costs.append(time.process_time() - t0)
    return costs, sum(costs) / BENCH_GENS * GENS * len(SEEDS) / 3600


def main():
    if DATA.exists():
        raise SystemExit("rung-5b data directory already exists; a rerun requires a documented repair")
    costs, projected = benchmark()
    DATA.mkdir()
    (DATA / "heartbeats").mkdir()
    (DATA / "runs").mkdir()
    (DATA / "benchmark.json").write_text(json.dumps(dict(cpu_s_by_arm=costs, projected_cpu_h=projected), indent=2))
    if projected > BUDGET_CPU_H:
        raise SystemExit(f"projected {projected:.2f} CPU-h exceeds {BUDGET_CPU_H}; not launched")
    jobs = [(name, arm, seed) for name, arm in ARMS for seed in SEEDS]
    rows, trajectories, audits, stop = [], {}, {}, None
    pool = ProcessPoolExecutor(max_workers=WORKERS)
    waiting = list(jobs)
    futures, submitted, finished = {}, {}, {}

    def submit_available():
        while waiting and len(futures) < WORKERS:
            job = waiting.pop(0)
            future = pool.submit(run_one, job)
            futures[future] = job
            submitted[job] = time.time()

    submit_available()
    try:
        while futures and stop is None:
            done, _ = wait(set(futures), timeout=60, return_when=FIRST_COMPLETED)
            for future in done:
                job = futures.pop(future)
                if future.exception() is not None:
                    stop = f"{job} raised {future.exception()!r}"
                    break
                try:
                    row, counts, audit = future.result()
                    validate_one(row, counts, audit)
                    persist_one(row, counts, audit)
                except Exception as exc:
                    stop = f"{job} failed validation: {exc!r}"
                    break
                finished[job] = row
                key = f"{row['arm']}_{row['seed']}"
                rows.append(row); trajectories[key], audits[key] = counts, audit
                print(f"{len(rows)}/{len(jobs)} {key}", flush=True)
            submit_available()
            cpu = sum(r["cpu_s"] for r in finished.values())
            now = time.time()
            for job in futures.values():
                if job in finished:
                    continue
                hb = _heartbeat_path(job)
                if not hb.exists():
                    if now - submitted[job] > 900:
                        stop = f"no first heartbeat for {job}"
                        break
                else:
                    if now - hb.stat().st_mtime > 900:
                        stop = f"stale heartbeat for {job}"
                        break
                    cpu += float(hb.read_text().split()[1])
            if cpu / 3600 > BUDGET_CPU_H:
                stop = f"stage passed {BUDGET_CPU_H} CPU-hours"
    finally:
        if stop:
            for process in pool._processes.values():
                process.terminate()
            pool.shutdown(wait=True, cancel_futures=True)
        else:
            pool.shutdown(wait=True)
    if stop:
        result = dict(verdict="NO VERDICT", reason=stop, completed=len(rows), projected_cpu_h=projected)
        (DATA / "verdict.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return result
    rows.sort(key=lambda r: (r["arm"], r["seed"]))
    with (DATA / "runs.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    np.savez_compressed(DATA / "trajectories.npz", **trajectories, **{f"audit_{k}": v for k, v in audits.items()})
    result = verdict(rows)
    result.update(projected_cpu_h=projected, completed=len(rows), settings=dict(n=N, gens=GENS, seeds=[SEEDS[0], SEEDS[-1]]))
    (DATA / "verdict.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
