"""Tests for the rung-4b runner: frozen design, validation, joint verdict, one attempt."""

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b import run as R


def test_frozen_design():
    assert len(R.jobs()) == 800 and R.SEEDS == tuple(range(2000, 2100)) and R.GENS == 2000
    assert R.CONDITIONS["main"] == (0.001, (0.1, 0.8, 0.1), ("test", "shuffled"))
    assert (R.Q, R.O, R.E, R.A) == (0.8, 0.5, 0.1, 0.02) and (R.T_MIN, R.SH_MAX) == (80, 20)
    assert R.WIN == (1501, 2000) and R.G_END == 500


def _small(monkeypatch, gens=40):
    monkeypatch.setattr(R, "GENS", gens)
    monkeypatch.setattr(R, "G_END", 10)
    monkeypatch.setattr(R, "WIN", (21, gens))
    monkeypatch.setattr(R, "SEEDS", (2000, 2001))
    out = [R.run_one(j) for j in R.jobs()]
    rows = [o[0] for o in out]
    counts = {(r["condition"], r["arm"], r["seed"]): o[1] for r, o in zip(rows, out)}
    audits = {(r["condition"], r["arm"], r["seed"]): o[2] for r, o in zip(rows, out)}
    return rows, counts, audits


def test_validate_accepts_real_runs_and_rejects_corruption(monkeypatch):
    rows, counts, audits = _small(monkeypatch)
    R.validate(rows, counts, audits)

    def rejects(rows_=rows, counts_=counts, audits_=audits):
        with pytest.raises(ValueError):
            R.validate(rows_, counts_, audits_)

    bad = [dict(r) for r in rows]
    bad[0]["coop_window"] += 0.01
    rejects(rows_=bad)
    rejects(rows_=rows[1:])                                 # a missing run
    for field, delta in (("encounters", -1), ("g1_allc_intends", -10), ("mutants_total", 0.5)):
        bad = [dict(r) for r in rows]
        i = next(i for i, r in enumerate(bad) if r["condition"] == "main")
        bad[i][field] += delta
        rejects(rows_=bad)
    bad = [dict(r) for r in rows]
    bad[0]["g1_helps"] = bad[0]["helps"] + 1                  # generation 1 above the run total
    rejects(rows_=bad)
    k = next(iter(counts))
    c2 = dict(counts)
    c2[k] = c2[k].copy()
    c2[k][5, 0] = 1001
    rejects(counts_=c2)
    c3 = dict(counts)
    c3[k] = c3[k].astype(float) + 0.5                       # fractional counts
    rejects(counts_=c3)
    a2 = dict(audits)
    a2[k] = a2[k].copy()
    a2[k][3, 6] += 1                                        # transfers no longer balance
    rejects(audits_=a2)
    a3 = dict(audits)
    a3[k] = a3[k].copy()
    a3[k][2, 9] -= 1                                        # a generation short of encounters
    rejects(audits_=a3)


def test_joint_verdict():
    def rows_for(test_pairs, sh_pairs):
        rr = []
        for s, (a, b) in zip(R.SEEDS, test_pairs):
            rr.append(dict(condition="main", arm="test", seed=s, coop_g500=a, coop_window=b, violations=0,
                           g1_violations=0))
        for s, (a, b) in zip(R.SEEDS, sh_pairs):
            rr.append(dict(condition="main", arm="shuffled", seed=s, coop_g500=a, coop_window=b, violations=0,
                           g1_violations=0))
        return rr
    good, bad = (0.9, 0.9), (0.01, 0.01)
    v, t, s5, sw = R.verdict(rows_for([good] * 80 + [bad] * 20, [bad] * 100))
    assert v == "MET" and t == 80
    # 80 pass each endpoint but only 60 pass both -> not met
    mix = [good] * 60 + [(0.9, 0.1)] * 20 + [(0.1, 0.9)] * 20
    assert R.verdict(rows_for(mix, [bad] * 100))[0] == "NOT MET"
    assert R.verdict(rows_for([good] * 100, [good] * 21 + [bad] * 79))[0] == "NOT MET"
    rr = rows_for([good] * 100, [bad] * 100)
    rr[0]["violations"] = 1
    assert R.verdict(rr)[0].startswith("INVALID")


def test_one_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DATA", tmp_path)
    monkeypatch.setattr(R, "git_state", lambda: ("abc", True))
    (tmp_path / "rung4b.attempt").write_text("x")
    with pytest.raises(SystemExit):
        R.main(2)
