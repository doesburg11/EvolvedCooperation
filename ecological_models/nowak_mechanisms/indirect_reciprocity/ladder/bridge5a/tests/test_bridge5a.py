import json

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.bridge5a import run as br
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import run as r5


def test_settings_applied_and_restored(tmp_path):
    before = (r5.B_, r5.E, r5.Q, r5.SEEDS, r5.CONDITIONS, r5.DATA)
    for step, (b, e, q, s0) in {"B1": (5.0, 0.1, 0.8, 3100), "B2": (5.0, 0.02, 1.0, 3200)}.items():
        with br.configured(step) as mod:
            assert (mod.B_, mod.E, mod.Q) == (b, e, q)
            js = mod.jobs()
            assert len(js) == 200 and {j[0] for j in js} == {"main"} and {j[1] for j in js} == {"test", "shuffled"}
            assert sorted({j[2] for j in js}) == list(range(s0, s0 + 100))
            assert mod.DATA == br.out_dir(step) and mod.DATA != before[5]
            assert (mod.O, mod.A, mod.N, mod.K, mod.GENS, mod.C_, mod.S_) == (0.5, 0.02, 1000, 10, 2000, 1.0, 0.1)
    assert (r5.B_, r5.E, r5.Q, r5.SEEDS, r5.CONDITIONS, r5.DATA) == before


def test_seed_blocks_disjoint_from_earlier_rungs():
    s1, s2 = set(br.STEPS["B1"]["SEEDS"]), set(br.STEPS["B2"]["SEEDS"])
    earlier = set(range(0, 20)) | set(range(1000, 1100)) | set(range(2000, 2100)) | set(range(3000, 3100))
    assert not (s1 & s2) and not (s1 & earlier) and not (s2 & earlier)


def test_run_one_records_step_parameters(tmp_path):
    # short run (GENS 5, N 50) into a temporary folder: the stored row carries the step's b, e, q and seed
    extra = dict(DATA=tmp_path, GENS=5, N=50, G_END=2, WIN=(3, 5))
    (tmp_path / "heartbeats").mkdir()
    (tmp_path / "runs").mkdir()
    with br.configured("B2", extra) as mod:
        row, counts, audit = mod.run_one(("main", "test", 3200))
    assert (row["b"], row["e"], row["q"], row["seed"], row["gens"]) == (5.0, 0.02, 1.0, 3200, 5)
    assert counts.shape == (6, 2)


def test_b2_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(br, "HERE", tmp_path)
    with pytest.raises(SystemExit, match="B2 needs"):
        br.main("B2")
    d = br.out_dir("B1")
    d.mkdir(parents=True)
    for v in ("MET", "NO VERDICT (x)", "INVALID (x)"):
        (d / "rung5a_summary.json").write_text(json.dumps({"verdict": v}))
        assert not br.b1_not_met()
    # a NOT MET string without a complete, valid B1 run set does not open B2
    (d / "rung5a_summary.json").write_text(json.dumps({"verdict": "NOT MET"}))
    (d / "runs").mkdir()
    assert not br.b1_not_met()
    with pytest.raises(SystemExit, match="B2 needs"):
        br.main("B2")


def test_disc_summaries(tmp_path, monkeypatch):
    monkeypatch.setattr(br, "HERE", tmp_path)
    d = br.out_dir("B1")
    d.mkdir(parents=True)
    rows, arrays = [], {}
    for arm in ("test", "shuffled"):
        for seed, disc in ((1, 600), (2, 400)):
            c = np.zeros((2001, 2), dtype=np.int16)
            c[:, 0] = 100                      # ALLD
            c[:, 1] = 1000 - 100 - disc        # ALLC
            arrays[f"main_{arm}_{seed}"] = c
            rows.append({"arm": arm, "seed": seed})
    with open(d / "rung5a_runs.csv", "w") as fh:
        fh.write("arm,seed\n" + "".join(f"{r['arm']},{r['seed']}\n" for r in rows))
    np.savez(d / "rung5a_counts.npz", **arrays)
    out = br.disc_summaries("B1")
    per = (d / "disc_per_run.csv").read_text().splitlines()
    assert per[0] == "arm,seed,DISC_g500,DISC_window" and len(per) == 5
    vals = {(l.split(",")[0], l.split(",")[1]): tuple(float(x) for x in l.split(",")[2:]) for l in per[1:]}
    assert vals[("test", "1")] == pytest.approx((0.6, 0.6)) and vals[("shuffled", "2")] == pytest.approx((0.4, 0.4))
    t = out["test"]
    assert (t["runs"], t["runs_disc_g500_ge_05"], t["runs_disc_window_ge_05"]) == (2, 1, 1)
    assert t["mean_disc_g500"] == pytest.approx(0.5) and t["mean_disc_window"] == pytest.approx(0.5)


def test_restored_after_exception():
    before = r5.B_
    with pytest.raises(RuntimeError):
        with br.configured("B1"):
            raise RuntimeError
    assert r5.B_ == before


def test_refuses_non_fork(monkeypatch):
    monkeypatch.setattr(br.multiprocessing, "get_start_method", lambda: "spawn")
    with pytest.raises(SystemExit, match="forked"):
        br.main("B1")
