"""Runner and analysis for STEP5_OWNOFFSPRING.md (rung 2 of the kin-ladder close-out).

Usage (from the repository root):
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_ownoffspring run 0        (checks, benchmarks)
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_ownoffspring run M [--workers N]
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_ownoffspring analyze M
  python -m ecological_models.nowak_mechanisms.kin_selection.ladder.run_ownoffspring interim M    (progress files only)

Raw output: ~/simulation_results/step5_ownoffspring/stage_m/ (one .npz per run, outside the repository).
Summaries: data/step5_ownoffspring/stage_{0,m}_summary.json (committed).
A crash or interruption leaves a .failed / .progress / .partial file and stops the stage; Stage M refuses a
relaunch once its launch record exists (one attempt, as registered).
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
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAW_REG = Path.home() / "simulation_results" / "step5_ownoffspring"
DATA_REG = HERE / "data" / "step5_ownoffspring"
RAW = Path(os.environ.get("OF_RAW", RAW_REG))
DATA = Path(os.environ.get("OF_DATA", DATA_REG))
SCALE = float(os.environ.get("OF_SCALE", 1.0))      # smoke tests only: shrink all run lengths
P, N_SITES, NB_PAIRS = 1000, 10, 100_000
C_TEST = 0.005
ARMS = {  # name: (mode, b, c)
    "N0": (0, 0.0, 0.0), "OF14": (5, 0.07, C_TEST), "XO14": (6, 0.07, C_TEST), "OF3.5": (5, 0.0175, C_TEST),
}
SEEDS = list(range(200, 220))
GIFT_MODES, POOL_MODE = (5, 6), 6
T_M, DT_M, T_BENCH = 100_000.0 * SCALE, 1_000.0 * SCALE, 5_000.0 * SCALE
END_WINDOW, ROUTE_FROM = 90_000.0 * SCALE, 50_000.0 * SCALE
G_MIN_OF14 = 0.00388
BUDGET_CPU_H, STALL_S = 8.0, 900.0


def require_registered(what):
    """Registered stages run only at full scale into the registered folders; smoke runs need OF_RAW and OF_DATA."""
    reg = {RAW_REG.resolve(), DATA_REG.resolve()}
    here = {RAW.resolve(), DATA.resolve()}
    if SCALE != 1.0 and (here & reg or any(str(x).startswith(str(r) + os.sep) or str(r).startswith(str(x) + os.sep)
                                          for x in here for r in reg)):
        raise SystemExit(f"{what}: OF_SCALE != 1 needs OF_RAW and OF_DATA outside the registered folders")
CODE_FILES = ("empty_sites_model.py", "empty_sites_model_step5.py", "empty_sites_model_rung1.py",
              "run_ownoffspring.py", "theory/no_offspring_screen.py", "theory/own_offspring_screen.py")
STEP5_SUMMARY = HERE / "data" / "step5_empty_sites" / "stage_0_summary.json"
TESTS = ("tests/test_empty_sites.py", "tests/test_nonoffspring.py", "tests/test_ownoffspring.py")


def git_state():
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", str(HERE.relative_to(ROOT))],
                           capture_output=True, text=True).stdout.strip()
    return commit, dirty == ""


def code_sha():
    h = hashlib.sha256()
    for f in CODE_FILES:
        h.update((HERE / f).read_bytes())
    return h.hexdigest()[:16]


def jobs():
    return [dict(stage="M", name=f"{a}_s{s}", arm=a, seed=s, mode=m, b=b, c=c, T=T_M, dt=DT_M)
            for a, (m, b, c) in ARMS.items() for s in SEEDS]


def stage_dir(stage):
    return RAW / ("stage_0" if stage == "0" else "stage_m")


def _atomic_text(path, text):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def check_equivalence(T=2_000.0):
    """Modes 0-3 must give byte-identical output to the step-5 code (columns 0-14) and modes 0-4 to the rung-1
    code (all columns, route statistics on), full size, two seeds."""
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model_step5 as O
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model_rung1 as R1
    for mode, b, c in ((0, 0.0, 0.0), (1, 0.07, C_TEST), (2, 0.07, C_TEST), (3, 0.07, C_TEST)):
        for seed in (0, 1):
            kw = dict(seed=seed, b=b, c=c, mode=mode, T=T * SCALE, sample_dt=DT_M, nb_pairs=NB_PAIRS)
            a, z = O.run(**kw), E.run(**kw)
            if a["events"] != z["events"] or a["samples"].tobytes() != \
                    np.ascontiguousarray(z["samples"][:, :15]).tobytes() or a["hists"].tobytes() != z["hists"].tobytes():
                raise SystemExit(f"mode {mode} seed {seed}: output differs from the step-5 code")
    for mode, b, c in ((0, 0.0, 0.0), (1, 0.07, C_TEST), (2, 0.14, C_TEST), (3, 0.07, C_TEST), (4, 0.14, C_TEST)):
        for seed in (0, 1):
            kw = dict(seed=seed, b=b, c=c, mode=mode, T=T * SCALE, sample_dt=DT_M, nb_pairs=NB_PAIRS, route=True)
            a, z = R1.run(**kw), E.run(**kw)
            if a["events"] != z["events"] or a["samples"].tobytes() != z["samples"].tobytes() or \
                    a["hists"].tobytes() != z["hists"].tobytes():
                raise SystemExit(f"mode {mode} seed {seed}: output differs from the rung-1 code")


def validate(path, job, sha, commit=None):
    from ecological_models.nowak_mechanisms.kin_selection.ladder.empty_sites_model import COLS
    with np.load(path) as f:
        meta = json.loads(str(f["meta"]))
        for key in ("stage", "name", "arm", "seed", "mode", "b", "c", "T", "dt"):
            if meta[key] != job[key]:
                raise ValueError(f"{path.name}: {key} {meta[key]!r} != {job[key]!r}")
        if meta["code_sha"] != sha or (commit is not None and meta["commit"] != commit):
            raise ValueError(f"{path.name}: code or commit does not match")
        s, hs = f["samples"], f["hists"]
        ns = int(round(job["T"] / job["dt"])) + 1                        # every sample time present
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
        if not np.isfinite(s[alive][:, [1, 2, 3, 4]]).all():
            raise ValueError(f"{path.name}: non-finite values while alive")
        if job["mode"] in GIFT_MODES:
            ce = s[alive, 22]
            if not np.isfinite(ce).all() or ce.max(initial=0.0) > 1e-9:
                raise ValueError(f"{path.name}: class-pool cache error missing or {np.nanmax(ce, initial=0.0)}")
        if job["mode"] in GIFT_MODES and not np.isfinite(s[alive][:, 15:18]).all():
            raise ValueError(f"{path.name}: gift-route statistics missing while alive")
    return meta


def run_one(job):
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
    d = stage_dir("M")
    final = d / f"{job['name']}.npz"
    prog = d / f"{job['name']}.progress"
    t0, c0 = time.time(), time.process_time()
    try:
        _atomic_text(prog, "0 -1 0.0 0.0\n")

        def progress(t_reached, N):
            _atomic_text(prog, f"{t_reached:.0f} {N} {time.time() - t0:.1f} {time.process_time() - c0:.1f}\n")

        o = E.run(seed=job["seed"], b=job["b"], c=job["c"], mode=job["mode"], T=job["T"], sample_dt=job["dt"],
                  nb_pairs=NB_PAIRS, chunk_T=10 * job["dt"], progress=progress, route=True)
        meta = dict(job, wall_s=time.time() - t0, cpu_s=time.process_time() - c0, events=o["events"],
                    births=o["births"])
        tmp = d / f"{job['name']}.{os.getpid()}.partial.npz"
        np.savez_compressed(tmp, samples=o["samples"], hists=o["hists"], meta=json.dumps(meta))
        validate(tmp, job, job["code_sha"], job["commit"])
        os.replace(tmp, final)
        prog.unlink(missing_ok=True)
    except Exception:
        _atomic_text(d / f"{job['name']}.failed", traceback.format_exc())
        raise
    return job["name"], f"done {meta['wall_s'] / 60:.1f} min"


def power_proxy():
    """t* from the stored step-5 Stage 0c variance series (every 1,000 time units), OF14's smallest gradient."""
    summ = json.loads(STEP5_SUMMARY.read_text())
    V = np.asarray(summ["V_every_1000"], float)
    tc = np.arange(len(V)) * 1_000.0
    integ = np.concatenate([[0.0], np.cumsum(0.5 * (V[1:] + V[:-1]) * np.diff(tc))]) * G_MIN_OF14
    hit = np.nonzero(integ >= 0.55)[0]
    return float(tc[hit[0]]) if len(hit) else None


def cmd_run_0():
    from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
    require_registered("Stage 0")
    commit, clean = git_state()
    if not clean:
        raise SystemExit("ladder tree not clean; commit first")
    sha = code_sha()
    res = dict(code_sha=sha, commit=commit, scale=SCALE)
    env = {k: v for k, v in os.environ.items() if not k.startswith("OF_")}   # tests see the registered settings
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", *[str(HERE / x) for x in TESTS]], cwd=ROOT,
                       capture_output=True, text=True, env=env)
    res["tests_passed"] = t.returncode == 0
    res["tests_tail"] = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else ""
    print("unit tests:", res["tests_tail"], flush=True)

    def fail(reason):
        res.update(passes=False, failed_at=reason)
        DATA.mkdir(parents=True, exist_ok=True)
        _atomic_text(DATA / "stage_0_summary.json", json.dumps(res, indent=1))
        print("STAGE 0 FAILS:", reason)
        raise SystemExit(1)

    if not res["tests_passed"]:
        fail("unit tests")
    check_equivalence()
    res["equivalence_passed"] = True
    print("existing modes byte-identical to the step-5 and rung-1 code", flush=True)
    t_star = power_proxy()
    res["t_star"] = t_star
    res["power_passes"] = bool(t_star is not None and t_star <= 25_000)     # stored full-length series: unscaled
    print(f"power proxy: t* = {t_star} (limit 25000)", flush=True)
    if not res["power_passes"]:
        fail("power proxy")
    for m in ARMS.values():                                              # warm-up compile
        E.run(seed=1, b=m[1], c=m[2], mode=m[0], T=10.0, sample_dt=10.0, P=20, nb_pairs=10, route=True)
    bench = {}
    for a, (m, b, c) in ARMS.items():
        t0, c0 = time.time(), time.process_time()
        o = E.run(seed=999, b=b, c=c, mode=m, T=T_BENCH, sample_dt=DT_M, nb_pairs=NB_PAIRS, route=True)
        bench[a] = dict(cpu_s=time.process_time() - c0, wall_s=time.time() - t0, events=o["events"])
        print(time.strftime("%H:%M:%S"), a, f"{bench[a]['cpu_s']:.1f} CPU-s for {T_BENCH:.0f} time units", flush=True)
    cpu_h = sum(len(SEEDS) * v["cpu_s"] / T_BENCH * T_M for v in bench.values()) / 3600
    res.update(bench=bench, projected_cpu_h=cpu_h, runtime_passes=bool(cpu_h <= 8.0))
    res["passes"] = bool(res["tests_passed"] and res["equivalence_passed"] and res["power_passes"]
                         and res["runtime_passes"])
    DATA.mkdir(parents=True, exist_ok=True)
    _atomic_text(DATA / "stage_0_summary.json", json.dumps(res, indent=1))
    print(f"runtime: projected Stage M {cpu_h:.2f} CPU-h (limit 8)")
    print("STAGE 0", "PASSES" if res["passes"] else "FAILS")


def cmd_run_m(workers):
    require_registered("Stage M")
    commit, clean = git_state()
    if not clean:
        raise SystemExit("ladder tree not clean; commit first")
    sha = code_sha()
    s0 = DATA / "stage_0_summary.json"
    summ = json.loads(s0.read_text()) if s0.exists() else {}
    if summ.get("passes") is not True or summ.get("code_sha") != sha or summ.get("scale") != SCALE:
        raise SystemExit("Stage 0 has not passed for this code; Stage M not started")
    d = stage_dir("M")
    d.mkdir(parents=True, exist_ok=True)
    lock = open(d / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("another runner holds this stage")
    if (d / "launch.json").exists():
        raise SystemExit("Stage M was already launched once (launch.json exists); one attempt, no relaunch")
    leftovers = [p.name for p in d.iterdir() if p.suffix in (".failed", ".progress", ".npz") or ".partial" in p.name]
    if leftovers:
        raise SystemExit(f"files from an earlier attempt in {d}: {leftovers[:5]}")
    check_equivalence()
    print("existing modes byte-identical to the step-5 and rung-1 code", flush=True)
    js = [dict(j, commit=commit, code_sha=sha) for j in jobs()]
    _atomic_text(d / "launch.json", json.dumps(dict(stage="M", commit=commit, code_sha=sha, runs=len(js),
                                                    start=time.time(), workers=workers, scale=SCALE)))
    print(f"stage M: {len(js)} runs, commit {commit}", flush=True)
    with ProcessPoolExecutor(max_workers=min(workers, len(js))) as ex:
        futs = [ex.submit(run_one, j) for j in js]
        try:
            for fut in as_completed(futs):
                name, status = fut.result()
                print(time.strftime("%H:%M:%S"), name, status, flush=True)
        except BaseException as e:
            for f in futs:
                f.cancel()
            print(time.strftime("%H:%M:%S"), "STAGE FAILED:", repr(e), flush=True)
            for proc in list(getattr(ex, "_processes", {}).values()):
                proc.terminate()
            raise SystemExit(1)
    print("stage complete", flush=True)


def classify(arm, contrast):
    """arm: {name: [20 run dicts]}; contrast: R_route(OF14) - R_route(XO14). As registered."""
    interp = {a: sum(r["viable"] for r in rs) >= 18 for a, rs in arm.items()}
    reached = {a: sum(r["reached"] for r in rs) for a, rs in arm.items()}

    def pairs(a, ref, sign):
        return sum(1 for x, y in zip(arm[a], arm[ref]) if x["viable"] and y["viable"]
                   and sign * (x["final_h"] - y["final_h"]) > 0)

    above = pairs("OF14", "N0", +1)
    below5 = pairs("OF3.5", "N0", -1)
    belowx = pairs("XO14", "N0", -1)
    if not (interp["N0"] and interp["OF14"] and interp["XO14"]):
        verdict = "not interpretable"
    elif contrast is None or not np.isfinite(contrast) or contrast < 0.02:
        verdict = "not interpretable: no relatedness contrast between the arms' gift routes"
    elif reached["XO14"] > 2:
        verdict = "not met: the control did not separate"
    elif reached["OF14"] >= 15 and above >= 16:
        verdict = "met: through parental care (help to own offspring after they settle)"
    else:
        verdict = "not met"

    def h(a, n_pairs):
        if not (interp[a] and interp["N0"]):
            return "not interpretable"
        return "supported" if n_pairs >= 16 else "not supported"

    return verdict, h("OF3.5", below5), h("XO14", belowx), dict(
        interpretable=interp, reached=reached, OF14_above_N0_pairs=above, OF35_below_N0_pairs=below5,
        XO14_below_N0_pairs=belowx)


def cmd_analyze_m():
    require_registered("analysis")
    sha = code_sha()
    commit = json.loads((stage_dir("M") / "launch.json").read_text())["commit"]
    times = np.arange(int(round(T_M / DT_M)) + 1) * DT_M
    win = times > END_WINDOW
    rwin = times > ROUTE_FROM
    runs = {}
    route = {a: np.zeros(3) for a in ARMS}
    for j in jobs():
        path = stage_dir("M") / f"{j['name']}.npz"
        validate(path, j, sha, commit)
        with np.load(path) as f:
            s = f["samples"].astype(float)
        viable = bool(s[-1, 0] > 0)
        final_h = float(s[win, 1].mean()) if viable else None
        if viable and not np.isfinite(final_h):
            raise ValueError(f"{j['name']}: non-finite final mean h")
        if j["mode"] in GIFT_MODES:                    # validated: finite whenever alive; extinct rows are NaN
            r = s[rwin & (s[:, 0] > 0)][:, 15:18]
            route[j["arm"]] += r.sum(0)
        runs[j["name"]] = dict(arm=j["arm"], seed=j["seed"], viable=viable, final_h=final_h,
                               reached=bool(viable and final_h >= 0.60),
                               occupancy=float(s[win, 3].mean()) if viable else None,
                               lost_local=float(np.nanmean(s[win, 18])) if viable else None,
                               lost_single=float(np.nanmean(s[win, 19])) if viable else None,
                               own_mate_share=float(np.nanmean(s[win, 20])) if viable and j["mode"] in GIFT_MODES else None,
                               with_off_share=float(np.nanmean(s[win, 21])) if viable and j["mode"] in GIFT_MODES else None,
                               h_every_10000=[None if not np.isfinite(x) else float(x) for x in s[::10, 1]])
    R = {}
    for a, (w, wq, wref) in route.items():
        if w > 0:
            q, qr = wq / w, wref / w
            R[a] = float((q - qr) / (1 - qr))
        else:
            R[a] = None
    contrast = R["OF14"] - R["XO14"] if R["OF14"] is not None and R["XO14"] is not None else None
    arm = {a: [runs[f"{a}_s{s}"] for s in SEEDS] for a in ARMS}
    verdict, h2, h3, det = classify(arm, contrast)
    res = dict(code_sha=sha, commit=commit, scale=SCALE, verdict=verdict, H2=h2, H3=h3, R_route=R,
               route_contrast=contrast, **det,
               mean_final_h={a: float(np.mean([r["final_h"] for r in rs if r["viable"]]))
                             if any(r["viable"] for r in rs) else None for a, rs in arm.items()},
               runs=runs)
    DATA.mkdir(parents=True, exist_ok=True)
    _atomic_text(DATA / "stage_m_summary.json", json.dumps(res, indent=1))
    if SCALE != 1.0:                       # smoke runs stay blind: validation status only, no trait values
        print(f"smoke analysis: {len(runs)} runs validated; summary written to {DATA} (not printed)")
        return
    for a in ARMS:
        print(f"{a:5}: viable {sum(r['viable'] for r in arm[a])}/20, at endpoint {det['reached'][a]}/20, "
              f"mean final h {res['mean_final_h'][a]}, R_route {R[a]}")
    print(f"route contrast {contrast}; OF14 > N0 in {det['OF14_above_N0_pairs']}/20 pairs, OF3.5 < N0 in "
          f"{det['OF35_below_N0_pairs']}/20, XO14 < N0 in {det['XO14_below_N0_pairs']}/20")
    print("verdict:", verdict, "| H2:", h2, "| H3:", h3)


def interim_verdict(rows, done, waiting, failed, now, start):
    """Registered interim rule (progress files only): STOP if any run failed or stalled, or the projected total CPU
    time of the stage exceeds the budget (each run's elapsed time projected to its full length; runs not started
    take the median projection of their arm, else the largest; finished runs count with their recorded CPU time).
    rows carry the run's process CPU seconds ("cpu"). Returns (verdict, reasons, projected CPU-h)."""
    reasons = []
    if failed:
        reasons.append(f"failed runs: {failed[:3]}")
    stalled = [r["name"] for r in rows if r["age"] > STALL_S]
    if stalled:
        reasons.append(f"no progress for > {STALL_S:.0f} s: {stalled[:3]}")
    started = [r for r in rows if r["t"] > 0]
    total = float(sum(done.values()))                    # CPU seconds of finished runs always count
    if started:
        by_arm = {}
        for r in started:
            by_arm.setdefault(r["arm"], []).append(r["cpu"] / r["t"] * T_M)
        med = {a: float(np.median(v)) for a, v in by_arm.items()}
        fallback = max(med.values())
        total += sum(r["cpu"] / r["t"] * T_M if r["t"] > 0 else med.get(r["arm"], fallback) for r in rows)
        total += sum(med.get(a, fallback) for a in waiting)
    else:
        total += sum(r["cpu"] for r in rows)
    cpu_h = total / 3600
    if cpu_h > BUDGET_CPU_H:
        reasons.append(f"projected {cpu_h:.2f} CPU-h > {BUDGET_CPU_H:.0f}")
    return ("STOP" if reasons else "ok"), reasons, cpu_h


def cmd_interim():
    """Progress files only (time reached, breeders alive, elapsed): never trait values. Prints one verdict."""
    d = stage_dir("M")
    launch = json.loads((d / "launch.json").read_text())
    now = time.time()
    done, waiting, rows = {}, [], []
    failed = [p.name for p in d.glob("*.failed")]
    for j in jobs():
        fin = d / f"{j['name']}.npz"
        if fin.exists():
            with np.load(fin) as f:
                done[j["name"]] = json.loads(str(f["meta"]))["cpu_s"]
            continue
        pf = d / f"{j['name']}.progress"
        try:
            fd = os.open(pf, os.O_RDONLY)
            try:
                mt = os.fstat(fd).st_mtime
                t_r, N, el, cpu = os.read(fd, 256).decode().split()
            finally:
                os.close(fd)
        except FileNotFoundError:
            if fin.exists():
                with np.load(fin) as f:
                    done[j["name"]] = json.loads(str(f["meta"]))["cpu_s"]
            else:
                waiting.append(j["arm"])
            continue
        rows.append(dict(name=j["name"], arm=j["arm"], t=float(t_r), el=float(el), cpu=float(cpu), age=now - mt))
    verdict, reasons, cpu_h = interim_verdict(rows, done, waiting, failed, now, launch["start"])
    print(time.strftime("%H:%M"), f"stage M: {len(done)} done, {len(rows)} running, {len(waiting)} not started, "
          f"{len(failed)} failed; {(now - launch['start']) / 3600:.2f} h since launch; projected "
          f"{cpu_h:.2f} CPU-h")
    print("  VERDICT:", verdict + (" (" + "; ".join(reasons) + ")" if reasons else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "analyze", "interim"])
    ap.add_argument("stage", choices=["0", "M"])
    ap.add_argument("--workers", type=int, default=20)
    a = ap.parse_args()
    if a.cmd == "run":
        cmd_run_0() if a.stage == "0" else cmd_run_m(a.workers)
    elif a.cmd == "analyze":
        if a.stage != "M":
            raise SystemExit("Stage 0 is summarised by 'run 0'")
        cmd_analyze_m()
    else:
        cmd_interim()


if __name__ == "__main__":
    main()
