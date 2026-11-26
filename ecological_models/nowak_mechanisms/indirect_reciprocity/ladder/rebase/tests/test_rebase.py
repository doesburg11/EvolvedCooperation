"""Tests for the rebase runner (README.md, "Rebase to q = 0.8 and rung 4a, attempt 3")."""

import csv
import importlib

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rebase import run as R

PKG = "ecological_models.nowak_mechanisms.indirect_reciprocity.ladder"


def _registered_rows(rung):
    mod = importlib.import_module(f"{PKG}.{rung}.run")
    return {(r["condition"], r["arm"], r["seed"]): r for r in R.read_rows(mod.DATA / f"{rung}_runs.csv")}


@pytest.mark.parametrize("rung,settings", [
    ("rung2", {"CONDITIONS": {"main": (0.6, 0.9, ("test", "shuffled"))}}),
    ("rung2b", {"CONDITIONS": {"main": (0.6, 0.5, ("test", "shuffled"))}}),
    ("rung3a", {"CONDITIONS": {"main": (0.1, ("test", "shuffled"))}}),
    ("rung3b", {"CONDITIONS": {"main": (0.02, ("test", "shuffled"))}}),
    ("rung4a", {"CONDITIONS": {"main": ((0.1, 0.8, 0.1), ("test", "shuffled"))}}),
])
def test_configured_runner_at_q06_reproduces_registered_rows(rung, settings, tmp_path):
    # the wrapper path, with the registered q = 0.6 settings, reproduces the registered CSV rows exactly
    v, t, sh, rows = R.run_rung(rung, settings, tmp_path, seeds=(0, 1, 2))
    reg = _registered_rows(rung)
    for r in rows:
        ref = reg[(r["condition"], r["arm"], r["seed"])]
        for k in r:
            assert r[k] == ref[k], (rung, r["seed"], k)
    assert not list(tmp_path.glob("*_verdict.txt"))


def test_settings_restored_after_call(tmp_path):
    mod = importlib.import_module(f"{PKG}.rung3b.run")
    before = (mod.Q, mod.SEEDS, dict(mod.CONDITIONS), mod.DATA)
    R.run_rung("rung3b", {"Q": 0.8, "CONDITIONS": {"main": (0.02, ("test", "shuffled"))}}, tmp_path, seeds=(5,))
    assert (mod.Q, mod.SEEDS, dict(mod.CONDITIONS), mod.DATA) == before
    with pytest.raises(RuntimeError):
        with R.configured("rung3b", {"Q": 0.8}, tmp_path):
            raise RuntimeError
    assert mod.Q == before[0]


def test_classify_thresholds():
    assert R.classify("MET", 80, 20) == "MET"
    assert R.classify("NOT MET", 80, 20) == "MET"          # the runner's 16/20 string is ignored; counts decide
    assert R.classify("MET", 79, 0) == "NOT MET"
    assert R.classify("MET", 100, 21) == "NOT MET"
    assert R.classify("NO VERDICT (data)", None, None).startswith("NO VERDICT")
    assert R.classify("INVALID (sanity)", None, None).startswith("INVALID")


def test_frozen_design():
    assert R.Q_NEW == 0.8 and R.SEEDS == tuple(range(1000, 1100)) and (R.T_MIN, R.SH_MAX) == (80, 20)
    assert set(R.STAGE_R) == {"rung2", "rung2b", "rung3a", "rung3b"}
    c = R.STAGE_4A["CONDITIONS"]
    assert c["main"] == ((0.1, 0.8, 0.1), ("test", "shuffled")) and c["allc5"][0] == (0.05, 0.85, 0.1)
    assert set(c) == {"main", "allc5", "no_allc", "more_allc", "no_alld", "image"}


def test_stage_4a_gate_refuses_without_stage_r(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DATA", tmp_path)
    with pytest.raises(SystemExit):
        R.stage_4a()
    (tmp_path / "stage_R_summary.json").write_text('{"passes": false, "rungs": {}}')
    with pytest.raises(SystemExit):
        R.stage_4a()


def test_replay_check_on_small_run(tmp_path, monkeypatch):
    # rung 4a without ALLC replays rung 3b exactly through the wrapper (q = 0.8, two seeds)
    monkeypatch.setattr(R, "DATA", tmp_path)
    R.run_rung("rung3b", {"Q": 0.8, "CONDITIONS": {"main": (0.02, ("test", "shuffled"))}},
               tmp_path / "stage_R" / "rung3b", seeds=(1000, 1001))
    _, _, _, rows = R.run_rung("rung4a", {"Q": 0.8, "CONDITIONS": {"main": ((0.1, 0.8, 0.1), ("test", "shuffled")),
                                                                   "no_allc": ((0.0, 0.9, 0.1), ("test",))}},
                               tmp_path / "stage_4a", seeds=(1000, 1001))
    assert R.replay_check(rows) == []


def _fake_git(monkeypatch):
    monkeypatch.setattr(R, "git_state", lambda: ("abc", True))


def test_stage_r_one_attempt_and_no_verdict_propagation(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DATA", tmp_path)
    _fake_git(monkeypatch)
    calls = []

    def fake(rung, settings, out_dir, seeds=R.SEEDS):
        calls.append(rung)
        out_dir.mkdir(parents=True, exist_ok=True)
        if rung == "rung3a":
            return "INVALID (sanity: two-way violation in the test arm; inspection pending)", None, None, []
        if rung == "rung2b":
            raise RuntimeError("boom")
        return "NOT MET", 95, 3, [{}] * 200

    monkeypatch.setattr(R, "run_rung", fake)
    res = R.stage_r()
    assert res["rungs"]["rung2"]["verdict"] == "MET" and res["rungs"]["rung3b"]["verdict"] == "MET"
    assert res["rungs"]["rung2b"]["verdict"].startswith("NO VERDICT")
    assert res["rungs"]["rung3a"]["verdict"].startswith("INVALID") and res["passes"] is False
    with pytest.raises(SystemExit):                    # completed attempt: refused
        R.stage_r()
    with pytest.raises(SystemExit):                    # Stage 4a gate: Stage R did not pass
        R.stage_4a()


def test_interrupted_attempt_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DATA", tmp_path)
    _fake_git(monkeypatch)
    (tmp_path / "stage_R").mkdir()                     # outputs of an interrupted attempt, no summary
    with pytest.raises(SystemExit):
        R.stage_r()
    (tmp_path / "stage_R").rmdir()
    (tmp_path / "stage_R.attempt").write_text("x")
    with pytest.raises(SystemExit):
        R.stage_r()


def test_stage_4a_records_no_verdict_and_replay_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DATA", tmp_path)
    _fake_git(monkeypatch)
    passed = {"passes": True, "rungs": {k: {"verdict": "MET"} for k in R.STAGE_R}}
    (tmp_path / "stage_R_summary.json").write_text(__import__("json").dumps(passed))
    monkeypatch.setattr(R, "run_rung", lambda *a, **k: ("NO VERDICT (data)", None, None, []))
    res = R.stage_4a()
    assert res["verdict"].startswith("NO VERDICT") and res["reported"] is None and res["replay_mismatch"] is None
    assert (tmp_path / "stage_4a_summary.json").exists()
    # a valid run whose replay fails becomes NO VERDICT
    for f in ("stage_4a_summary.json", "stage_4a.attempt"):
        (tmp_path / f).unlink()
    import shutil
    shutil.rmtree(tmp_path / "stage_4a", ignore_errors=True)
    monkeypatch.setattr(R, "run_rung", lambda *a, **k: ("MET", 90, 0, []))
    monkeypatch.setattr(R, "replay_check", lambda rows: [1003])
    monkeypatch.setattr(R, "descriptives", lambda rows: {})
    res = R.stage_4a()
    assert res["verdict"].startswith("NO VERDICT (no-ALLC runs do not replay")


def test_replay_check_detects_corruption(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DATA", tmp_path)
    R.run_rung("rung3b", {"Q": 0.8, "CONDITIONS": {"main": (0.02, ("test", "shuffled"))}},
               tmp_path / "stage_R" / "rung3b", seeds=(1000,))
    _, _, _, rows = R.run_rung("rung4a", {"Q": 0.8, "CONDITIONS": {"main": ((0.1, 0.8, 0.1), ("test", "shuffled")),
                                                                   "no_allc": ((0.0, 0.9, 0.1), ("test",))}},
                               tmp_path / "stage_4a", seeds=(1000,))
    assert R.replay_check(rows) == []
    rows = [dict(r, helps=r["helps"] + 1) if r["condition"] == "no_allc" else r for r in rows]
    assert R.replay_check(rows) == [1000]


def test_descriptives_include_good_record_shares():
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a import run as r4
    base = {f: 1.0 for f in r4.FIELDS}
    base.update({"g1_" + f: 1.0 for f in r4.FIELDS})
    base.update(final_allc=0.1, final_disc=0.8, final_alld=0.1, max_alld=0.2, g1_consult_allc=0.0)
    rows = [dict(base, condition=c, arm=a, seed=1000) for c, (_, arms) in R.STAGE_4A["CONDITIONS"].items() for a in arms]
    d = R.descriptives(rows)
    assert d["main_test"]["g1_good_share_consulted_disc"] == 1.0
    assert d["main_test"]["g1_good_share_consulted_allc"] is None      # zero denominator -> undefined
    assert d["main_test"]["at_endpoint"] == 1
