"""Runner and analysis for STEP5_EMPTY_SITES.md.

Usage (from the repository root):
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites run 0   [--workers N]
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites analyze 0
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites run M   (refuses unless Stage 0 passed)
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites analyze M
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites interim M   (progress files only)

Raw output: ~/simulation_results/step5_empty_sites/stage_{0,m}/ (one .npz per run, outside the repository).
Summaries: data/step5_empty_sites/stage_{0,m}_summary.json (committed).
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAW = Path(os.environ.get("ES_RAW", Path.home() / "simulation_results" / "step5_empty_sites"))
DATA = Path(os.environ.get("ES_DATA", HERE / "data" / "step5_empty_sites"))
SCALE = float(os.environ.get("ES_SCALE", 1.0))      # smoke tests only: shrink all run lengths
P, N_SITES = 1000, 10
C_TEST = 0.005
ARMS = {  # name: (mode, b, c)
    "N0": (0, 0.0, 0.0), "T14": (1, 0.07, C_TEST), "NO14": (2, 0.07, C_TEST), "X14": (3, 0.07, C_TEST),
    "T3.5": (1, 0.0175, C_TEST),
}
T_M = 100_000.0 * SCALE
T_0A, T_0C, T_BENCH = 20_000.0 * SCALE, 30_000.0 * SCALE, 5_000.0 * SCALE
# theory (theory/at_breakeven.py, neutral, n = 10, k = 0.5, stay if i <= 5)
TH_P = [0.001, 0.006, 0.023, 0.065, 0.143, 0.25, 0.345, 0.129, 0.032, 0.005, 0.0]
TH_OCC, TH_GPAIR, G_MIN_T14 = 0.535, 0.1466, 0.00145


def git_state():
    root = HERE.parents[3]
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", str(HERE.relative_to(root))],
                           capture_output=True, text=True).stdout.strip()
    return commit, dirty == ""


def model_sha():
    return hashlib.sha256((HERE / "empty_sites_model.py").read_bytes()).hexdigest()[:16]


def theory_p():
    """Exact theory patch-type distribution (recomputed, not the rounded TH_P)."""
    sys.path.insert(0, str(HERE / "theory"))
    import importlib.util, io, contextlib
    spec = importlib.util.spec_from_file_location("atb", HERE / "theory" / "at_breakeven.py")
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    r = m.at(0.0, 0.0, 0.0)
    return np.asarray(r["p"]), float(r["occ"]), float(r["G_pair"]), r["G"]


def jobs(stage):
    if stage == "0":
        js = [dict(stage="0", name=f"0a_s{s}", kind="0a", seed=s, mode=0, b=0.0, c=0.0, T=T_0A, mu=0.0, h_fixed=0.0)
              for s in range(900, 904)]
        js += [dict(stage="0", name=f"0c_s{s}", kind="0c", seed=s, mode=0, b=0.0, c=0.0, T=T_0C, mu=0.02, h_fixed=None)
               for s in range(900, 904)]
        js += [dict(stage="0", name=f"bench_{a}", kind="bench", seed=999, mode=m, b=b, c=c, T=T_BENCH, mu=0.02,
                    h_fixed=None, arm=a) for a, (m, b, c) in ARMS.items()]
        return js
    return [dict(stage="M", name=f"{a}_s{s}", kind="M", seed=s, mode=m, b=b, c=c, T=T_M, mu=0.02, h_fixed=None, arm=a)
            for a, (m, b, c) in ARMS.items() for s in range(20)]


def stage_dir(stage):
    return RAW / ("stage_0" if stage == "0" else "stage_m")


def _atomic_text(path, text):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def validate(path, job, sha):
    with np.load(path) as f:
        meta = json.loads(str(f["meta"]))
        for key in ("stage", "name", "kind", "seed", "mode", "b", "c", "T", "mu"):
            if meta[key] != job[key]:
                raise ValueError(f"{path.name}: {key} {meta[key]!r} != {job[key]!r}")
        if meta["model_sha"] != sha:
            raise ValueError(f"{path.name}: model_sha {meta['model_sha']} != {sha}")
        ns = int(round(job["T"] / 100.0)) + 1
        if f["samples"].shape != (ns, 11) or f["hists"].shape != (ns, N_SITES + 1):
            raise ValueError(f"{path.name}: shape {f['samples'].shape}")
        alive = f["samples"][:, 0] > 0
        if not np.isfinite(f["samples"][alive][:, [0, 1, 2, 3, 4]]).all():
            raise ValueError(f"{path.name}: non-finite values while alive")
    return meta


def run_one(job):
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
    d = stage_dir(job["stage"])
    final = d / f"{job['name']}.npz"
    if final.exists():
        validate(final, job, job["model_sha"])
        return job["name"], "skipped (valid)"
    prog = d / f"{job['name']}.progress"
    t0 = time.time()

    def progress(t_reached, N):
        _atomic_text(prog, f"{t_reached:.0f} {N} {time.time() - t0:.1f}\n")

    o = E.run(seed=job["seed"], b=job["b"], c=job["c"], mode=job["mode"], T=job["T"], mu=job["mu"],
              h_fixed=job["h_fixed"], progress=progress)
    meta = dict(job, wall_s=time.time() - t0, events=o["events"], births=o["births"])
    tmp = d / f"{job['name']}.{os.getpid()}.partial.npz"
    np.savez_compressed(tmp, samples=o["samples"], hists=o["hists"], meta=json.dumps(meta))
    validate(tmp, job, job["model_sha"])
    os.replace(tmp, final)
    prog.unlink(missing_ok=True)
    return job["name"], f"done {meta['wall_s'] / 60:.1f} min"


def cmd_run(stage, workers):
    commit, clean = git_state()
    if not clean:
        raise SystemExit("ladder tree not clean; commit first")
    sha = model_sha()
    if stage == "M":
        s0 = DATA / "stage_0_summary.json"
        summ = json.loads(s0.read_text()) if s0.exists() else {}
        if summ.get("passes") is not True or summ.get("model_sha") != sha or summ.get("scale") != SCALE:
            raise SystemExit("Stage 0 has not passed for this model code; Stage M not started")
        for j in jobs("0"):
            validate(stage_dir("0") / f"{j['name']}.npz", j, sha)
    d = stage_dir(stage)
    d.mkdir(parents=True, exist_ok=True)
    lock = open(d / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("another runner holds this stage")
    js = [dict(j, commit=commit, model_sha=sha) for j in jobs(stage)]
    _atomic_text(d / "launch.json", json.dumps(dict(stage=stage, commit=commit, model_sha=sha, runs=len(js),
                                                    start=time.time(), workers=workers, scale=SCALE)))
    print(f"stage {stage}: {len(js)} runs, commit {commit}", flush=True)
    with Pool(min(workers, len(js))) as p:
        for name, status in p.imap_unordered(run_one, js):
            print(time.strftime("%H:%M:%S"), name, status, flush=True)
    print("stage complete", flush=True)


def _load(job, sha):
    path = stage_dir(job["stage"]) / f"{job['name']}.npz"
    meta = validate(path, job, sha)
    with np.load(path) as f:
        return meta, f["samples"].astype(float), f["hists"].astype(float)


def cmd_analyze_0():
    sha = model_sha()
    p_th, occ_th, g_th, G_th = theory_p()
    res = dict(model_sha=sha, scale=SCALE, theory=dict(p=p_th.tolist(), occupancy=occ_th, G_pair=g_th,
                                                        G6=float(G_th[6]), G7=float(G_th[7])), seeds={})
    times = np.arange(int(round(T_0A / 100)) + 1) * 100.0
    win = times > T_0A / 2
    ok_a = True
    q6 = q7 = qb_all = 0.0
    n_s = 0
    for j in [j for j in jobs("0") if j["kind"] == "0a"]:
        meta, s, hs = _load(j, sha)
        p_ibm = hs[win].mean(0) / P
        tv = 0.5 * np.abs(p_ibm - p_th).sum()
        occ = s[win, 3].mean()
        qw, qb = s[win, 5].mean(), s[win, 6].mean()
        R = (qw - qb) / (1 - qb)
        ok = bool(tv <= 0.03 and abs(occ - occ_th) <= 0.02 and abs(R - g_th) <= 0.02)
        ok_a &= ok
        q6 += np.nanmean(s[win, 9]); q7 += np.nanmean(s[win, 10]); qb_all += qb; n_s += 1
        res["seeds"][j["name"]] = dict(tv=float(tv), occupancy=float(occ), R=float(R), passes=ok,
                                       p=p_ibm.round(4).tolist(), wall_s=meta["wall_s"])
    qb_m = qb_all / n_s
    R6 = (q6 / n_s - qb_m) / (1 - qb_m)
    R7 = (q7 / n_s - qb_m) / (1 - qb_m)
    drop_ok = bool(R6 - R7 >= 0.02)
    # 0c power gate
    tc = np.arange(int(round(T_0C / 100)) + 1) * 100.0
    V = np.mean([_load(j, sha)[1][:, 2] for j in jobs("0") if j["kind"] == "0c"], axis=0)
    integ = np.concatenate([[0.0], np.cumsum(0.5 * (V[1:] + V[:-1]) * np.diff(tc))]) * G_MIN_T14
    hit = np.nonzero(integ >= 0.55)[0]
    t_star = float(tc[hit[0]]) if len(hit) else None
    power_ok = bool(t_star is not None and t_star <= 25_000 * SCALE)
    # runtime
    bench = {}
    for j in [j for j in jobs("0") if j["kind"] == "bench"]:
        meta, _, _ = _load(j, sha)
        bench[j["arm"]] = meta["wall_s"] / j["T"]          # wall seconds per time unit
    cpu_h = sum(20 * w * T_M for w in bench.values()) / 3600
    runtime_ok = bool(cpu_h <= 8.0)
    passes = bool(ok_a and drop_ok and power_ok and runtime_ok)
    res.update(R6=float(R6), R7=float(R7), drop_passes=drop_ok, V_every_1000=V[::10].round(5).tolist(),
               t_star=t_star, power_passes=power_ok, bench_wall_s_per_time_unit=bench, projected_cpu_h=cpu_h,
               runtime_passes=runtime_ok, demography_relatedness_passes=bool(ok_a), passes=passes)
    DATA.mkdir(parents=True, exist_ok=True)
    _atomic_text(DATA / "stage_0_summary.json", json.dumps(res, indent=1))
    for name, r in res["seeds"].items():
        print(f"{name}: TV {r['tv']:.4f}  occupancy {r['occupancy']:.4f} (theory {occ_th:.4f})  R {r['R']:.4f} "
              f"(theory {g_th:.4f}) -> {'ok' if r['passes'] else 'FAIL'}")
    print(f"R6 {R6:.3f} R7 {R7:.3f} (theory {G_th[6]:.3f}, {G_th[7]:.3f}): drop {'ok' if drop_ok else 'FAIL'}")
    print(f"power gate: t* = {t_star} (limit {25_000 * SCALE:.0f}) -> {'ok' if power_ok else 'FAIL'}")
    print(f"runtime: projected Stage M {cpu_h:.2f} CPU-h (limit 8) -> {'ok' if runtime_ok else 'FAIL'}")
    print("STAGE 0", "PASSES" if passes else "FAILS")


def cmd_analyze_m():
    sha = model_sha()
    times = np.arange(int(round(T_M / 100)) + 1) * 100.0
    win = times > T_M - 10_000 * SCALE
    runs = {}
    for j in jobs("M"):
        meta, s, _ = _load(j, sha)
        viable = bool(s[-1, 0] > 0)
        final_h = float(s[win, 1].mean()) if viable else None
        runs[j["name"]] = dict(arm=j["arm"], seed=j["seed"], viable=viable, final_h=final_h,
                               reached=bool(viable and final_h >= 0.60),
                               gift_own_offspring=float(np.nanmean(s[win, 7])) if viable else None,
                               gift_lost=float(np.nanmean(s[win, 8])) if viable else None,
                               occupancy=float(s[win, 3].mean()) if viable else None,
                               h_every_10000=[None if not np.isfinite(x) else float(x) for x in s[::100, 1]])
    arm = {a: [runs[f"{a}_s{s}"] for s in range(20)] for a in ARMS}
    interp = {a: sum(r["viable"] for r in rs) >= 18 for a, rs in arm.items()}
    reached = {a: sum(r["reached"] for r in rs) for a, rs in arm.items()}

    def pairs(a, ref, sign):
        return sum(1 for x, y in zip(arm[a], arm[ref]) if x["viable"] and y["viable"]
                   and sign * (x["final_h"] - y["final_h"]) > 0)

    above = {a: pairs(a, "N0", +1) for a in ("T14", "NO14")}
    below_35 = pairs("T3.5", "N0", -1)
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
        h2 = "supported" if below_35 >= 16 else "not supported"
    res = dict(model_sha=sha, scale=SCALE, verdict=verdict, H2=h2, interpretable=interp, reached=reached,
               T14_above_N0_pairs=above["T14"], NO14_above_N0_pairs=above["NO14"], T35_below_N0_pairs=below_35,
               mean_final_h={a: float(np.mean([r["final_h"] for r in rs if r["viable"]])) if any(r["viable"] for r in rs)
                             else None for a, rs in arm.items()},
               runs=runs)
    DATA.mkdir(parents=True, exist_ok=True)
    _atomic_text(DATA / "stage_m_summary.json", json.dumps(res, indent=1))
    for a in ARMS:
        print(f"{a:5}: viable {sum(r['viable'] for r in arm[a])}/20, at endpoint {reached[a]}/20, "
              f"mean final h {res['mean_final_h'][a]}")
    print(f"T14 > N0 in {above['T14']}/20 pairs, NO14 > N0 in {above['NO14']}/20, T3.5 < N0 in {below_35}/20")
    print("verdict:", verdict, "| H2:", h2)


def cmd_interim(stage):
    d = stage_dir(stage)
    launch = json.loads((d / "launch.json").read_text())
    now = time.time()
    done = waiting = 0
    rows = []
    for j in jobs(stage):
        if (d / f"{j['name']}.npz").exists():
            done += 1
            continue
        pf = d / f"{j['name']}.progress"
        if not pf.exists():
            waiting += 1
            continue
        t_r, N, el = pf.read_text().split()
        rows.append((j["name"], float(t_r), int(N), float(el), now - pf.stat().st_mtime, j["T"]))
    print(time.strftime("%H:%M"), f"stage {stage}: {done} done, {len(rows)} running, {waiting} not started")
    if rows:
        proj = [now - age + el / tr * (T - tr) for _, tr, _, el, age, T in rows if tr > 0]
        print(f"  time reached {min(r[1] for r in rows):.0f}..{max(r[1] for r in rows):.0f}; "
              f"oldest update {max(r[4] for r in rows):.0f} s ago; "
              f"running wave projected to end {time.strftime('%H:%M', time.localtime(max(proj)))}" if proj else "")
        print(f"  elapsed since launch {(now - launch['start']) / 3600:.2f} h")


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
