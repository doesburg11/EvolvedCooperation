"""Runner and analysis for STEP5_EMPTY_SITES.md.

Usage (from the repository root):
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites run 0   [--workers N]
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites analyze 0
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites run M   (refuses unless Stage 0 passed)
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites analyze M
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites interim M   (progress files only)

Raw output: ~/simulation_results/step5_empty_sites/stage_{0,m}/ (one .npz per run, outside the repository).
Summaries: data/step5_empty_sites/stage_{0,m}_summary.json (committed).
A crashed or interrupted run leaves a .failed / .progress / .partial file; a relaunch then refuses to start (the
pre-registration says a crash stops the stage and is reported, not rerun).
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import time
import traceback
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAW = Path(os.environ.get("ES_RAW", Path.home() / "simulation_results" / "step5_empty_sites"))
DATA = Path(os.environ.get("ES_DATA", HERE / "data" / "step5_empty_sites"))
SCALE = float(os.environ.get("ES_SCALE", 1.0))      # smoke tests only: shrink all run lengths
P, N_SITES, NB_PAIRS = 1000, 10, 100_000
C_TEST = 0.005
ARMS = {  # name: (mode, b, c)
    "N0": (0, 0.0, 0.0), "T14": (1, 0.07, C_TEST), "NO14": (2, 0.07, C_TEST), "X14": (3, 0.07, C_TEST),
    "T3.5": (1, 0.0175, C_TEST),
}
T_M = 100_000.0 * SCALE
T_0A, T_0C, T_BENCH = 20_000.0 * SCALE, 30_000.0 * SCALE, 5_000.0 * SCALE
DT_0, DT_M = 100.0 * SCALE, 1_000.0 * SCALE          # sampling: every 100 in Stage 0, every 1,000 in Stage M
G_MIN_T14 = 0.00145
CODE_FILES = ("empty_sites_model.py", "run_empty_sites.py", "theory/at_breakeven.py")


def git_state():
    root = HERE.parents[3]
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", str(HERE.relative_to(root))],
                           capture_output=True, text=True).stdout.strip()
    return commit, dirty == ""


def code_sha():
    h = hashlib.sha256()
    for f in CODE_FILES:
        h.update((HERE / f).read_bytes())
    return h.hexdigest()[:16]


def theory():
    import contextlib
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location("atb", HERE / "theory" / "at_breakeven.py")
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    r = m.at(0.0, 0.0, 0.0)
    return np.asarray(r["p"]), float(r["occ"]), float(r["G_pair"]), r["G"]


def jobs(stage):
    if stage == "0":
        js = [dict(stage="0", name=f"0a_s{s}", kind="0a", seed=s, mode=0, b=0.0, c=0.0, T=T_0A, dt=DT_0, mu=0.0,
                   h_fixed=0.0) for s in range(900, 904)]
        js += [dict(stage="0", name=f"0c_s{s}", kind="0c", seed=s, mode=0, b=0.0, c=0.0, T=T_0C, dt=DT_0, mu=0.02,
                    h_fixed=None) for s in range(900, 904)]
        return js
    return [dict(stage="M", name=f"{a}_s{s}", kind="M", seed=s, mode=m, b=b, c=c, T=T_M, dt=DT_M, mu=0.02,
                 h_fixed=None, arm=a) for a, (m, b, c) in ARMS.items() for s in range(20)]


def bench_jobs():
    return [dict(stage="0", name=f"bench_{a}", kind="bench", seed=999, mode=m, b=b, c=c, T=T_BENCH, dt=DT_M, mu=0.02,
                 h_fixed=None, arm=a) for a, (m, b, c) in ARMS.items()]


def stage_dir(stage):
    return RAW / ("stage_0" if stage == "0" else "stage_m")


def _atomic_text(path, text):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def validate(path, job, sha, commit=None):
    from ecological_models.nowak_mechanisms.kin_selection.ladder.empty_sites_model import COLS
    with np.load(path) as f:
        meta = json.loads(str(f["meta"]))
        for key in ("stage", "name", "kind", "seed", "mode", "b", "c", "T", "dt", "mu", "h_fixed"):
            if meta[key] != job[key]:
                raise ValueError(f"{path.name}: {key} {meta[key]!r} != {job[key]!r}")
        if meta["code_sha"] != sha:
            raise ValueError(f"{path.name}: code_sha {meta['code_sha']} != {sha}")
        if commit is not None and meta["commit"] != commit:
            raise ValueError(f"{path.name}: commit {meta['commit']} != {commit}")
        s, hs = f["samples"], f["hists"]
        ns = int(round(job["T"] / job["dt"])) + 1
        if s.shape != (ns, len(COLS)) or hs.shape != (ns, N_SITES + 1):
            raise ValueError(f"{path.name}: shape {s.shape}")
        N = s[:, 0]
        if not np.isfinite(N).all() or (N < 0).any():
            raise ValueError(f"{path.name}: bad population counts")
        dead = np.nonzero(N == 0)[0]
        if len(dead) and (N[dead[0]:] != 0).any():
            raise ValueError(f"{path.name}: breeders reappear after extinction")
        if (hs.sum(1) != P).any():
            raise ValueError(f"{path.name}: patch histogram does not sum to P")
        alive = N > 0
        if not np.isfinite(s[alive][:, [1, 2, 3, 4, 5, 6]]).all():
            raise ValueError(f"{path.name}: non-finite values while alive")
    return meta


def run_one(job):
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
    d = stage_dir(job["stage"])
    final = d / f"{job['name']}.npz"
    if final.exists():
        validate(final, job, job["code_sha"], job["commit"])
        return job["name"], "skipped (valid)"
    prog = d / f"{job['name']}.progress"
    t0 = time.time()
    try:
        _atomic_text(prog, f"0 -1 0.0\n")

        def progress(t_reached, N):
            _atomic_text(prog, f"{t_reached:.0f} {N} {time.time() - t0:.1f}\n")

        o = E.run(seed=job["seed"], b=job["b"], c=job["c"], mode=job["mode"], T=job["T"], sample_dt=job["dt"],
                  mu=job["mu"], h_fixed=job["h_fixed"], nb_pairs=NB_PAIRS, chunk_T=10 * job["dt"] if job["kind"] == "M"
                  else 100 * job["dt"], progress=progress)
        meta = dict(job, wall_s=time.time() - t0, events=o["events"], births=o["births"])
        tmp = d / f"{job['name']}.{os.getpid()}.partial.npz"
        np.savez_compressed(tmp, samples=o["samples"], hists=o["hists"], meta=json.dumps(meta))
        validate(tmp, job, job["code_sha"], job["commit"])
        os.replace(tmp, final)
        prog.unlink(missing_ok=True)
    except Exception:
        _atomic_text(d / f"{job['name']}.failed", traceback.format_exc())
        raise
    return job["name"], f"done {meta['wall_s'] / 60:.1f} min"


def run_benchmarks(commit, sha):
    """Sequential, single process, after a warm-up compile: wall time here is CPU time of one run. Only the
    event count and wall time are kept."""
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
    d = stage_dir("0")
    for m in (0, 1, 2, 3):
        E.run(seed=1, b=0.07, c=0.005, mode=m, T=10.0, sample_dt=10.0, P=20, nb_pairs=10)
    for j in bench_jobs():
        t0 = time.time()
        o = E.run(seed=j["seed"], b=j["b"], c=j["c"], mode=j["mode"], T=j["T"], sample_dt=j["dt"], mu=j["mu"],
                  nb_pairs=NB_PAIRS)
        rec = dict(j, commit=commit, code_sha=sha, wall_s=time.time() - t0, events=o["events"])
        _atomic_text(d / f"{j['name']}.json", json.dumps(rec))
        print(time.strftime("%H:%M:%S"), j["name"], f"{rec['wall_s']:.1f} s, {rec['events']} events", flush=True)


def cmd_run(stage, workers):
    commit, clean = git_state()
    if not clean:
        raise SystemExit("ladder tree not clean; commit first")
    sha = code_sha()
    d = stage_dir(stage)
    d.mkdir(parents=True, exist_ok=True)
    leftovers = [p.name for p in d.iterdir() if p.suffix in (".failed", ".progress") or ".partial" in p.name]
    if leftovers:
        raise SystemExit(f"previous crash or interrupted run in {d}: {leftovers[:5]}; stop and report, not rerun")
    if stage == "M":
        s0 = DATA / "stage_0_summary.json"
        summ = json.loads(s0.read_text()) if s0.exists() else {}
        if summ.get("passes") is not True or summ.get("code_sha") != sha or summ.get("scale") != SCALE:
            raise SystemExit("Stage 0 has not passed for this code; Stage M not started")
        for j in jobs("0"):
            validate(stage_dir("0") / f"{j['name']}.npz", j, sha, summ["commit"])
    lock = open(d / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("another runner holds this stage")
    js = [dict(j, commit=commit, code_sha=sha) for j in jobs(stage)]
    _atomic_text(d / "launch.json", json.dumps(dict(stage=stage, commit=commit, code_sha=sha, runs=len(js),
                                                    start=time.time(), workers=workers, scale=SCALE)))
    print(f"stage {stage}: {len(js)} runs, commit {commit}", flush=True)
    with Pool(min(workers, len(js))) as p:
        for name, status in p.imap_unordered(run_one, js):
            print(time.strftime("%H:%M:%S"), name, status, flush=True)
    if stage == "0":
        run_benchmarks(commit, sha)
    print("stage complete", flush=True)


def _load(job, sha, commit):
    path = stage_dir(job["stage"]) / f"{job['name']}.npz"
    meta = validate(path, job, sha, commit)
    with np.load(path) as f:
        return meta, f["samples"].astype(float), f["hists"].astype(float)


def cmd_analyze_0():
    sha = code_sha()
    launch = json.loads((stage_dir("0") / "launch.json").read_text())
    commit = launch["commit"]
    p_th, occ_th, g_th, G_th = theory()
    res = dict(code_sha=sha, commit=commit, scale=SCALE,
               theory=dict(p=p_th.tolist(), occupancy=occ_th, G_pair=g_th, G6=float(G_th[6]), G7=float(G_th[7])),
               seeds={})
    times = np.arange(int(round(T_0A / DT_0)) + 1) * DT_0
    win = times > T_0A / 2
    ok_a = True
    num6 = den6 = num7 = den7 = qb_num = qb_den = 0.0
    short = 0
    for j in [j for j in jobs("0") if j["kind"] == "0a"]:
        meta, s, hs = _load(j, sha, commit)
        w = s[win]
        p_ibm = hs[win].mean(0) / P
        tv = 0.5 * np.abs(p_ibm - p_th).sum()
        occ = w[:, 3].mean()
        qw = (w[:, 5] * w[:, 14]).sum() / w[:, 14].sum()                 # pooled over ordered patch-mate pairs
        qb = (w[:, 6] * w[:, 11]).sum() / w[:, 11].sum()                 # pooled over between-patch pairs
        short += int((w[:, 11] < NB_PAIRS).sum())
        R = (qw - qb) / (1 - qb)
        ok = bool(tv <= 0.03 and abs(occ - occ_th) <= 0.02 and abs(R - g_th) <= 0.02)
        ok_a &= ok
        num6 += np.nansum(w[:, 9] * w[:, 12]); den6 += w[:, 12].sum()
        num7 += np.nansum(w[:, 10] * w[:, 13]); den7 += w[:, 13].sum()
        qb_num += (w[:, 6] * w[:, 11]).sum(); qb_den += w[:, 11].sum()
        res["seeds"][j["name"]] = dict(tv=float(tv), occupancy=float(occ), R=float(R), passes=ok,
                                       p=p_ibm.round(4).tolist(), wall_s=meta["wall_s"])
    qb_all = qb_num / qb_den
    R6 = (num6 / den6 - qb_all) / (1 - qb_all)
    R7 = (num7 / den7 - qb_all) / (1 - qb_all)
    drop_ok = bool(R6 - R7 >= 0.02)
    estimator_ok = short == 0
    tc = np.arange(int(round(T_0C / DT_0)) + 1) * DT_0
    V = np.mean([_load(j, sha, commit)[1][:, 2] for j in jobs("0") if j["kind"] == "0c"], axis=0)
    integ = np.concatenate([[0.0], np.cumsum(0.5 * (V[1:] + V[:-1]) * np.diff(tc))]) * G_MIN_T14
    hit = np.nonzero(integ >= 0.55)[0]
    t_star = float(tc[hit[0]]) if len(hit) else None
    power_ok = bool(t_star is not None and t_star <= 25_000 * SCALE)
    bench = {}
    for j in bench_jobs():
        rec = json.loads((stage_dir("0") / f"{j['name']}.json").read_text())
        if rec["code_sha"] != sha or rec["commit"] != commit or rec["T"] != j["T"]:
            raise ValueError(f"benchmark {j['name']} does not match this code or launch")
        bench[j["arm"]] = rec["wall_s"] / j["T"]
    cpu_h = sum(20 * w * T_M for w in bench.values()) / 3600
    runtime_ok = bool(cpu_h <= 8.0)
    passes = bool(ok_a and drop_ok and estimator_ok and power_ok and runtime_ok)
    res.update(R6=float(R6), R7=float(R7), drop_passes=drop_ok, Qb_samples_short=short,
               V_every_1000=V[::10].round(5).tolist(), t_star=t_star, power_passes=power_ok,
               bench_cpu_s_per_time_unit=bench, projected_cpu_h=cpu_h, runtime_passes=runtime_ok,
               demography_relatedness_passes=bool(ok_a), passes=passes)
    DATA.mkdir(parents=True, exist_ok=True)
    _atomic_text(DATA / "stage_0_summary.json", json.dumps(res, indent=1))
    for name, r in res["seeds"].items():
        print(f"{name}: TV {r['tv']:.4f}  occupancy {r['occupancy']:.4f} (theory {occ_th:.4f})  R {r['R']:.4f} "
              f"(theory {g_th:.4f}) -> {'ok' if r['passes'] else 'FAIL'}")
    print(f"R6 {R6:.3f} R7 {R7:.3f} (theory {G_th[6]:.3f}, {G_th[7]:.3f}): drop {'ok' if drop_ok else 'FAIL'}; "
          f"between-patch samples short of {NB_PAIRS}: {short}")
    print(f"power gate: t* = {t_star} (limit {25_000 * SCALE:.0f}) -> {'ok' if power_ok else 'FAIL'}")
    print(f"runtime: projected Stage M {cpu_h:.2f} CPU-h (limit 8) -> {'ok' if runtime_ok else 'FAIL'}")
    print("STAGE 0", "PASSES" if passes else "FAILS")


def classify(arm):
    """arm: {name: [20 run dicts with viable, final_h, reached]} -> (verdict, H2, details). As registered."""
    interp = {a: sum(r["viable"] for r in rs) >= 18 for a, rs in arm.items()}
    reached = {a: sum(r["reached"] for r in rs) for a, rs in arm.items()}

    def pairs(a, ref, sign):
        return sum(1 for x, y in zip(arm[a], arm[ref]) if x["viable"] and y["viable"]
                   and sign * (x["final_h"] - y["final_h"]) > 0)

    above = {a: pairs(a, "N0", +1) for a in ("T14", "NO14")}
    below = pairs("T3.5", "N0", -1)
    if not (interp["N0"] and interp["T14"] and interp["X14"]):
        verdict = "not interpretable"
    elif reached["X14"] > 2:
        verdict = "not met: the control did not separate"
    elif reached["T14"] >= 15 and above["T14"] >= 16:
        if interp["NO14"] and reached["NO14"] >= 15 and above["NO14"] >= 16:
            verdict = "met: among non-offspring relatives"
        else:
            verdict = "met: help to patch-mates, own offspring not excluded"
    else:
        verdict = "not met"
    if not (interp["T3.5"] and interp["N0"]):
        h2 = "not interpretable"
    else:
        h2 = "supported" if below >= 16 else "not supported"
    return verdict, h2, dict(interpretable=interp, reached=reached, T14_above_N0_pairs=above["T14"],
                             NO14_above_N0_pairs=above["NO14"], T35_below_N0_pairs=below)


def cmd_analyze_m():
    sha = code_sha()
    commit = json.loads((stage_dir("M") / "launch.json").read_text())["commit"]
    times = np.arange(int(round(T_M / DT_M)) + 1) * DT_M
    win = times > T_M - 10_000 * SCALE
    runs = {}
    for j in jobs("M"):
        meta, s, _ = _load(j, sha, commit)
        viable = bool(s[-1, 0] > 0)
        final_h = float(s[win, 1].mean()) if viable else None
        runs[j["name"]] = dict(arm=j["arm"], seed=j["seed"], viable=viable, final_h=final_h,
                               reached=bool(viable and final_h >= 0.60),
                               gift_own_offspring=float(np.nanmean(s[win, 7])) if viable else None,
                               gift_lost=float(np.nanmean(s[win, 8])) if viable else None,
                               occupancy=float(s[win, 3].mean()) if viable else None,
                               h_every_10000=[None if not np.isfinite(x) else float(x) for x in s[::10, 1]])
    arm = {a: [runs[f"{a}_s{s}"] for s in range(20)] for a in ARMS}
    verdict, h2, det = classify(arm)
    res = dict(code_sha=sha, commit=commit, scale=SCALE, verdict=verdict, H2=h2, **det,
               mean_final_h={a: float(np.mean([r["final_h"] for r in rs if r["viable"]]))
                             if any(r["viable"] for r in rs) else None for a, rs in arm.items()},
               runs=runs)
    DATA.mkdir(parents=True, exist_ok=True)
    _atomic_text(DATA / "stage_m_summary.json", json.dumps(res, indent=1))
    for a in ARMS:
        print(f"{a:5}: viable {sum(r['viable'] for r in arm[a])}/20, at endpoint {det['reached'][a]}/20, "
              f"mean final h {res['mean_final_h'][a]}")
    print(f"T14 > N0 in {det['T14_above_N0_pairs']}/20 pairs, NO14 > N0 in {det['NO14_above_N0_pairs']}/20, "
          f"T3.5 < N0 in {det['T35_below_N0_pairs']}/20")
    print("verdict:", verdict, "| H2:", h2)


def cmd_interim(stage):
    """Progress files only (time reached, breeders alive, elapsed): never trait values."""
    d = stage_dir(stage)
    launch = json.loads((d / "launch.json").read_text())
    now = time.time()
    done = waiting = 0
    rows = []
    failed = [p.name for p in d.glob("*.failed")]
    for j in jobs(stage):
        if (d / f"{j['name']}.npz").exists():
            done += 1
            continue
        pf = d / f"{j['name']}.progress"
        if not pf.exists():
            waiting += 1
            continue
        t_r, N, el = pf.read_text().split()
        rows.append((float(t_r), int(N), float(el), now - pf.stat().st_mtime, j["T"]))
    print(time.strftime("%H:%M"), f"stage {stage}: {done} done, {len(rows)} running, {waiting} not started, "
          f"{len(failed)} failed {failed[:3]}")
    started = [r for r in rows if r[0] > 0]
    if started:
        per_run = float(np.median([el / tr * T for tr, _, el, _, T in started]))     # projected wall time per run
        remaining_running = max(per_run - (el + age) for _, _, el, age, _ in started)
        waves_left = int(np.ceil(waiting / max(1, launch["workers"])))
        finish = now + max(0.0, remaining_running) + waves_left * per_run
        print(f"  time reached {min(r[0] for r in rows):.0f}..{max(r[0] for r in rows):.0f}; oldest progress update "
              f"{max(r[3] for r in rows):.0f} s ago; projected stage end {time.strftime('%H:%M', time.localtime(finish))} "
              f"({(finish - launch['start']) / 3600:.2f} h after launch)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "analyze", "interim"])
    ap.add_argument("stage", choices=["0", "M"])
    ap.add_argument("--workers", type=int, default=7)
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run(a.stage, a.workers)
    elif a.cmd == "analyze":
        cmd_analyze_0() if a.stage == "0" else cmd_analyze_m()
    else:
        cmd_interim(a.stage)


if __name__ == "__main__":
    main()
