"""Tests for the rung-6a runner: frozen design, validation on small real runs, verdict, one attempt."""

import time

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung6a_overlap import run as R


def test_frozen_design():
    assert len(R.jobs()) == 200 and R.SEEDS == tuple(range(3700, 3800)) and R.GENS == 4000
    assert (R.G_END, R.WIN) == (1000, (3001, 4000)) and (R.P_EMP, R.R_REP, R.STEP) == (0.75, 0.5, "6a")
    assert R.CONDITIONS == {"main": (0.001, (0.1, 0.8, 0.1), ("test", "shuffled"))}
    assert (R.N, R.K, R.B_, R.C_, R.S_) == (1000, 10, 3.0, 1.0, 0.1)
    assert (R.Q, R.O, R.E, R.A) == (0.8, 0.5, 0.1, 0.02) and (R.T_MIN, R.SH_MAX) == (80, 20)
    assert R.BENCH_SEED not in R.SEEDS and R.BUDGET_CPU_H == 80.0 and R.DATA == R.HERE / "data"
    import inspect
    assert "rung6a_overlap import model" in inspect.getsource(R.run_one)
    assert "r=R_REP" in inspect.getsource(R.run_one) and "r=R_REP" in inspect.getsource(R.benchmark)


def _small(monkeypatch, tmp_path):
    for k, v in dict(N=60, GENS=30, G_END=10, WIN=(11, 30), SEEDS=(3700, 3701), DATA=tmp_path).items():
        monkeypatch.setattr(R, k, v)
    (tmp_path / "heartbeats").mkdir()
    (tmp_path / "runs").mkdir()
    out = [R.run_one(j) for j in R.jobs()]
    rows = [o[0] for o in out]
    keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
    return rows, dict(zip(keys, [o[1] for o in out])), dict(zip(keys, [o[2] for o in out]))


def test_validate_and_corruption(monkeypatch, tmp_path):
    rows, counts, audits = _small(monkeypatch, tmp_path)
    R.validate(rows, counts, audits)
    assert all(r["check_mismatch"] == 0 for r in rows)
    assert all(r["sanity_violations"] == 0 for r in rows if r["arm"] == "test")

    def rejects(rows_=rows, counts_=counts, audits_=audits):
        with pytest.raises(ValueError):
            R.validate(rows_, counts_, audits_)

    for field, delta in (("coop_window", 0.01), ("observations", 1e12), ("flips", 1e12), ("encounters", -1),
                         ("consult_alld", 1), ("g1_allc_intends", -10), ("mutants_total", 1), ("final_allc", 7.0),
                         ("g1_goodview_disc", 1e15), ("goodview_disc", 1e15), ("intent_refusal_obs", 1e9),
                         ("disc_turns", 10), ("allc_intends", 10), ("first_below_05", 3)):
        bad = [dict(r) for r in rows]
        i = next(i for i, r in enumerate(bad) if r["condition"] == "main" and r["arm"] == "test")
        bad[i][field] += delta
        rejects(rows_=bad)
    rejects(rows_=rows[1:])
    k = next(iter(counts))
    c2 = dict(counts)
    c2[k] = c2[k].astype(float)
    rejects(counts_=c2)
    a2 = dict(audits)
    a2[k] = a2[k].copy()
    a2[k][3, 6] += 1
    rejects(audits_=a2)


def test_verdict_rules():
    def rows_for(test, sh, mismatch=0, sanity=0):
        rr = [dict(condition="main", arm="test", seed=s, coop_g500=a, coop_window=b, check_mismatch=mismatch,
                   sanity_violations=sanity) for s, (a, b) in zip(R.SEEDS, test)]
        rr += [dict(condition="main", arm="shuffled", seed=s, coop_g500=a, coop_window=b, check_mismatch=0,
                    sanity_violations=0) for s, (a, b) in zip(R.SEEDS, sh)]
        return rr
    good, bad = (0.9, 0.9), (0.01, 0.01)
    assert R.verdict(rows_for([good] * 80 + [bad] * 20, [bad] * 100))[0] == "MET"
    assert R.verdict(rows_for([good] * 79 + [bad] * 21, [bad] * 100))[0] == "NOT MET"
    assert R.verdict(rows_for([good] * 100, [good] * 21 + [bad] * 79))[0] == "NOT MET"
    assert R.verdict(rows_for([good] * 100, [bad] * 100, mismatch=1))[0].startswith("INVALID")
    assert R.verdict(rows_for([good] * 100, [bad] * 100, sanity=1))[0].startswith("INVALID")


def test_one_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DATA", tmp_path)
    monkeypatch.setattr(R, "git_state", lambda: ("abc", True))
    (tmp_path / "rung6a.attempt").write_text("x")
    with pytest.raises(SystemExit):
        R.main()


_REAL_RUN_ONE = R.run_one


def _flaky(job):
    if job[2] == 3701 and job[1] == "shuffled":
        raise RuntimeError("boom")
    return _REAL_RUN_ONE(job)


def _bad(job):
    raise ValueError("stored-view check failed")


def _sleep_after_heartbeat(job):
    hb = R._hb_path(job)
    hb.write_text("0 0.0\n")
    time.sleep(30)
    return _REAL_RUN_ONE(job)


def _sleep_without_heartbeat(job):
    time.sleep(30)
    return _REAL_RUN_ONE(job)


def _stage(monkeypatch, tmp_path, run_one=None, budget=None, stall=None):
    if stall is not None:
        monkeypatch.setattr(R, "STALL_S", stall)
    monkeypatch.setattr(R, "POLL_S", 0.5)
    for k, v in dict(N=40, GENS=20, G_END=5, WIN=(11, 20), SEEDS=(3700, 3701), DATA=tmp_path, WORKERS=2).items():
        monkeypatch.setattr(R, k, v)
    monkeypatch.setattr(R, "git_state", lambda: ("abc", True))
    monkeypatch.setattr(R, "benchmark", lambda: (1.0, 0.0))
    if run_one is not None:
        monkeypatch.setattr(R, "run_one", run_one)
    if budget is not None:
        monkeypatch.setattr(R, "BUDGET_CPU_H", budget)
    return R.main()


def test_stage_completes_and_keeps_per_run_files(monkeypatch, tmp_path):
    res = _stage(monkeypatch, tmp_path)
    assert res["verdict"] in ("MET", "NOT MET") and len(list((tmp_path / "runs").glob("*.npz"))) == 4


def test_failing_run_stops_with_no_verdict_and_keeps_outputs(monkeypatch, tmp_path):
    res = _stage(monkeypatch, tmp_path, run_one=_flaky)
    assert res["verdict"].startswith("NO VERDICT (stopped") and "boom" in res["verdict"]
    assert (tmp_path / "rung6a_summary.json").exists() and len(list((tmp_path / "runs").glob("*.npz"))) >= 1


def test_check_failure_is_invalid(monkeypatch, tmp_path):
    res = _stage(monkeypatch, tmp_path, run_one=_bad)
    assert res["verdict"].startswith("INVALID") and "check failed" in res["verdict"]


def test_budget_stop(monkeypatch, tmp_path):
    res = _stage(monkeypatch, tmp_path, budget=1e-9)
    assert res["verdict"].startswith("NO VERDICT (stopped: stage passed")


def test_stale_heartbeat_stops(monkeypatch, tmp_path):
    t0 = time.time()
    res = _stage(monkeypatch, tmp_path, run_one=_sleep_after_heartbeat, stall=2.0)
    assert res["verdict"].startswith("NO VERDICT (stopped") and "heartbeat" in res["verdict"]
    assert time.time() - t0 < 25 and (tmp_path / "rung6a_summary.json").exists()


def test_no_first_heartbeat_stops(monkeypatch, tmp_path):
    t0 = time.time()
    res = _stage(monkeypatch, tmp_path, run_one=_sleep_without_heartbeat, stall=2.0)
    assert res["verdict"].startswith("NO VERDICT (stopped") and "no progress" in res["verdict"]
    assert time.time() - t0 < 25


def test_watcher_exception_stops_and_writes_summary(monkeypatch, tmp_path):
    calls = {"n": 0}
    real_wait = R.wait

    def bad_wait(*a, **k):
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("watcher broke")
        return real_wait(*a, **k)

    monkeypatch.setattr(R, "wait", bad_wait)
    res = _stage(monkeypatch, tmp_path)
    assert res["verdict"].startswith("NO VERDICT (stopped: watcher interrupted")
    assert (tmp_path / "rung6a_summary.json").exists()


def test_extra_summaries_boundaries(monkeypatch):
    monkeypatch.setattr(R, "N", 100)
    monkeypatch.setattr(R, "G_END", 5)
    monkeypatch.setattr(R, "WIN", (8, 10))
    rows = [{"condition": "main", "arm": a, "seed": s, "observations": 10.0, "empathetic_obs": 4.0}
            for a in ("test", "shuffled") for s in (1, 2)]
    counts = {}
    for a in ("test", "shuffled"):
        c1 = np.zeros((11, 2), dtype=np.int16); c1[:, 1] = 50               # DISC 0.5 throughout, coop 1.0
        c2 = np.zeros((11, 2), dtype=np.int16); c2[:, 1] = 60; c2[7:, 0] = 21  # coop 0.79 from generation 7
        c2[6, 0] = 20                                                          # coop exactly 0.80 at 6: not a drop
        counts[("main", a, 1)], counts[("main", a, 2)] = c1, c2
    out = R.extra_summaries(rows, counts)
    t = out["test"]
    assert t["realised_empathetic_share"] == pytest.approx(0.4)
    assert t["runs_disc_g500_ge_05"] == 1 and t["runs_disc_window_ge_05"] == 1      # exactly 0.5 counts
    assert t["runs_drop_below_08_after_500"] == 1 and t["median_first_drop_after_500"] == 7.0
    per = {(p["arm"], p["seed"]): p for p in out["per_run"]}
    assert per[("test", 1)]["first_drop_below_08_after_500"] is None
    assert per[("test", 2)]["first_drop_below_08_after_500"] == 7
    assert per[("test", 1)]["DISC_g500"] == pytest.approx(0.5)
    assert per[("test", 2)]["DISC_window"] == pytest.approx((100 - 21 - 60) / 100)


def test_rows_record_step_and_p_and_validation_rejects_wrong_p(monkeypatch, tmp_path):
    rows, counts, audits = _small(monkeypatch, tmp_path)
    assert all(r["step"] == "6a" and r["p"] == 0.75 and r["r"] == 0.5 for r in rows)
    for field, val in (("p", 0.5), ("step", "C2"), ("seed", 3600), ("r", 1.0), ("n_rep", 1000)):
        bad = [dict(r) for r in rows]
        bad[0][field] = val
        with pytest.raises(ValueError):
            R.validate(bad, counts, audits)
    bad = [dict(r) for r in rows]
    bad[0]["empathetic_obs"] = bad[0]["observations"] + 1
    with pytest.raises(ValueError):
        R.validate(bad, counts, audits)


def test_refuses_non_fork(monkeypatch):
    import multiprocessing
    monkeypatch.setattr(multiprocessing, "get_start_method", lambda: "spawn")
    with pytest.raises(SystemExit, match="forked"):
        R.main()


def test_validator_rejects_survivor_corruption(monkeypatch, tmp_path):
    rows, counts, audits = _small(monkeypatch, tmp_path)
    k = next(iter(audits))
    for col, delta in ((10, 1), (12, 1)):              # survivor total off by one
        a2 = dict(audits)
        a2[k] = a2[k].copy()
        a2[k][2, col] += delta
        with pytest.raises(ValueError, match="survivor accounting"):
            R.validate(rows, counts, a2)
    a2 = dict(audits)
    a2[k] = a2[k].copy()
    a2[k][2, 0] += 1                                    # offspring total off by one
    with pytest.raises(ValueError, match="offspring accounting"):
        R.validate(rows, counts, a2)
    # survivors of a strategy above its previous count, totals and signs intact: isolated bound
    cnt = np.asarray(counts[k]).astype(np.int64)
    au = np.asarray(audits[k]).astype(np.int64)
    g = next(g for g in range(au.shape[0]) if au[g, 11] > cnt[g, 0] - au[g, 12] + 1)
    over = int(cnt[g, 0]) + 1 - int(au[g, 12])
    a2 = dict(audits)
    a2[k] = au.copy()
    a2[k][g, 12] += over
    a2[k][g, 11] -= over
    assert (a2[k] >= 0).all() and a2[k][g, 10:13].sum() == au[g, 10:13].sum()
    with pytest.raises(ValueError, match="survivor accounting"):
        R.validate(rows, counts, a2)
