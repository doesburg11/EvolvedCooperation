import numpy as np
import pytest

from ecological_models.nowak_mechanisms.kin_selection_ladder.config.ladder_config import NEUTRAL, run_config
from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import make_engine
from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.analysis import (
    choose_mu, compare, score_t0a, score_t0b, score_t1,
)


def _eng(**kw):
    upd = kw.pop("updates", {})
    return make_engine(run_config(0, {"simulation_steps": 5, **upd}), **kw)


def _kernel(e):
    return e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)


def test_self_in_routing_share_matches_theory():
    e = _eng()
    e.lineage = np.arange(e.n_sites, dtype=np.int32)  # nobody shares a label: self-share 0.8 / 1.6
    K = _kernel(e)
    assert np.allclose(np.diag(K), 0.5)
    e.lineage[:] = 0                                   # everyone same label: 0.8 / 4.0
    assert np.allclose(np.diag(_kernel(e)), 0.2)


def test_self_out_of_routing_but_in_replacement():
    e = _eng(self_in_routing=False)
    K = _kernel(e)
    assert np.allclose(np.diag(K), 0.0) and np.allclose(K.sum(1), 1.0)
    assert ((K > 0).sum(1) == 4).all()
    assert all(i in nb for i, nb in enumerate(e.neighbor_indices))  # self still competes for its site


def test_uniform_and_genome_kernels():
    e = _eng(self_in_routing=False, kin="none")
    K = _kernel(e)
    assert np.allclose(K[K > 0], 0.25)
    g = _eng(self_in_routing=False, kin="genome")
    K = _kernel(g)                                     # founders unrelated: r = 0 -> equal weights
    assert np.allclose(K[K > 0], 0.25)
    nb = [j for j in g.neighbor_indices[0] if j != 0]
    g.extra_state["genome"][nb[0]] = g.extra_state["genome"][0]   # r = 1 with one neighbour
    K = _kernel(g)
    assert K[0, nb[0]] == pytest.approx(0.8 / (0.8 + 3 * 0.2))


def test_genome_mutation_uses_own_stream_and_unique_alleles():
    runs = {}
    for mu in (0.0, 0.03):
        e = make_engine(run_config(3, {**NEUTRAL, "simulation_steps": 60}), kin="label", track_genome=True, mu=mu)
        for _ in range(60):
            e.step()
        runs[mu] = e
    assert np.array_equal(runs[0.0].lineage, runs[0.03].lineage)       # genealogy independent of mu
    assert np.array_equal(runs[0.0].h, runs[0.03].h)
    g0, g1 = runs[0.0].extra_state["genome"], runs[0.03].extra_state["genome"]
    assert g0.max() < g0.size and g1.max() >= g1.size                 # new alleles beyond founder ids
    assert (g0 == g1).mean() == pytest.approx(0.97 ** 60, abs=0.02)  # every site is reborn every step
    assert np.allclose(runs[0.0].h, 0.0)                               # neutral calibration keeps h = 0


def test_genome_stream_does_not_touch_engine_rng():
    a = make_engine(run_config(5, {"simulation_steps": 30}), kin="label", track_genome=True, mu=0.5)
    b = make_engine(run_config(5, {"simulation_steps": 30}), kin="label", track_genome=False)
    for _ in range(30):
        a.step(); b.step()
    assert np.array_equal(a.h, b.h) and np.array_equal(a.lineage, b.lineage)


def _rows(n_success, n=20, h=0.9):
    return [{"seed": s, "success": int(s < n_success), "final_mean_trait": h if s < n_success else 0.1}
            for s in range(n)]


def test_score_t0a_t0b():
    arms = {"A-kin": _rows(18), "A-nobias": _rows(5), "A-below": _rows(1),
            "S-kin": _rows(16), "S-nobias": _rows(7), "S-below": _rows(0)}
    assert score_t0a(arms)["met"]
    t = score_t0b(arms, 8)
    assert t["met"] and t["scored_at_B"] == 1.0
    arms["S-kin"] = _rows(14)                         # below 15
    assert not score_t0b(arms, 8)["met"]
    arms["S-kin"], arms["S-nobias"] = _rows(20), _rows(9)  # nobias >= 8 -> scored at 0.6
    arms["S-kin-0.6"], arms["S-nobias-0.6"] = _rows(12), _rows(4)
    t = score_t0b(arms, 8)
    assert t["low_b_triggered"] and t["scored_at_B"] == 0.6 and t["met"]
    arms["S-below"] = _rows(3)
    assert not score_t0b(arms, 8)["met"]


def test_score_t1_and_diff_rule():
    arms = {"G-kin": _rows(15), "G-nobias": _rows(8), "G-below": _rows(0)}
    assert not score_t1(arms, 15)["met"]              # diff 7 < 8
    arms["G-nobias"] = _rows(7)
    assert score_t1(arms, 15)["met"]
    assert compare(_rows(15), _rows(7), 15, 8)["fisher_p"] < 0.05


def test_choose_mu_closest_ties_lower():
    rows = [{"mu": m, "seed": 0, "genome_contrast": c, "label_contrast": 0.2}
            for m, c in ((0.001, 0.4), (0.003, 0.25), (0.01, 0.15), (0.03, 0.05))]
    assert choose_mu(rows, [0.001, 0.003, 0.01, 0.03])["mu_star"] == 0.003
    tie = [{"mu": 0.01, "genome_contrast": 0.3, "label_contrast": 0.2},
           {"mu": 0.003, "genome_contrast": 0.1 + 1e-15, "label_contrast": 0.2}]
    assert choose_mu(tie, [0.003, 0.01])["mu_star"] == 0.003


def test_below_and_low_b_boundaries():
    base = {"S-kin": _rows(20), "S-nobias": _rows(9), "S-kin-0.6": _rows(12), "S-nobias-0.6": _rows(4)}
    assert score_t0b({**base, "S-below": _rows(2)}, 8)["met"]
    assert not score_t0b({**base, "S-below": _rows(3)}, 8)["met"]
    assert not score_t0b({**base, "S-below": _rows(0), "S-kin-0.6": _rows(11), "S-nobias-0.6": _rows(3)}, 8)["met"]
    g = {"G-kin": _rows(12), "G-nobias": _rows(4), "G-below": _rows(2)}
    assert score_t1(g, 12)["met"] and not score_t1(g, 15)["met"]
    assert not score_t1({**g, "G-below": _rows(3)}, 12)["met"]


def test_calibration_pairs_and_genealogy():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_steps01 import random_pairs, run_cal_one
    e = _eng()
    i, j = random_pairs(e, 2000, 12345)
    assert len(set(zip(i, j))) == 2000 and (i < j).all() and not e.neighbor_mask[i, j].any()
    i2, j2 = random_pairs(e, 2000, 12345)
    assert (i == i2).all() and (j == j2).all()
    a, b = run_cal_one((0.001, 1)), run_cal_one((0.03, 1))
    assert a["final_lineage"] == b["final_lineage"] and a["label_contrast"] == b["label_contrast"]


def test_self_weight_half_step_shares():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.analysis import score_t0c
    e = _eng(self_weight=0.2)
    e.lineage = np.arange(e.n_sites, dtype=np.int32)          # m = 0: share 0.2 / 1.0
    assert np.allclose(np.diag(_kernel(e)), 0.2)
    e.lineage[:] = 0                                           # m = 4: 0.2 / 3.4
    K = _kernel(e)
    assert np.allclose(np.diag(K), 0.2 / 3.4) and np.allclose(K.sum(1), 1.0)
    nb = [j for j in e.neighbor_indices[0] if j != 0]
    assert K[0, nb[0]] == pytest.approx(0.8 / 3.4)
    e2 = _eng(self_weight=0.5)
    e2.lineage = np.arange(e2.n_sites, dtype=np.int32)
    assert np.allclose(np.diag(_kernel(e2)), 0.5 / 1.3)
    e2.lineage[:] = 0
    assert np.allclose(np.diag(_kernel(e2)), 0.5 / 3.7)
    with pytest.raises(ValueError):
        _eng(self_in_routing=False, self_weight=0.2)
    # default (no self_weight) still matches the Moran kernel
    a, b = _eng(), _eng()
    assert np.allclose(_kernel(a), b.mechanism.build_positive_kernel(b.neighbor_mask, b.lineage, {}, b.cfg))
    # T0c with the Bonferroni alpha: 15 vs 7 gives p ~ 0.01 (passes 0.025); 15 vs 7 with below 3 fails
    assert score_t0c(_rows(15), _rows(7), _rows(2), 0.025)["met"]
    assert not score_t0c(_rows(15), _rows(7), _rows(3), 0.025)["met"]
    assert not score_t0c(_rows(14), _rows(5), _rows(0), 0.05)["met"]


def test_step0c_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    assert c.STEPS_0C == 3000 and c.STEP0C_ARMS["H-kin"][0]["self_weight"] == 0.2
    assert c.STEP0C_ATTEMPT2_ARMS["H2-kin"][0]["self_weight"] == 0.5
    assert c.STEP0C_ARMS["H-nobias"][1]["kin_weight_same_lineage"] == 0.5
    assert c.STEP0C_ARMS["H-below"][1]["B_plus_scale"] == 0.05 and c.STEP0C_ARMS["H-below"][1]["initial_trait_mean"] == 0.9
    assert run_config(0, {}, c.STEPS_0C)["simulation_steps"] == 3000
    with pytest.raises(ValueError):
        _eng(self_weight=float("nan"))
    full = {**c.STEP0C_ARMS, **c.STEP0C_ATTEMPT2_ARMS}
    assert c.SEEDS == list(range(20))
    for arm, (mech, upd) in full.items():
        cfg = run_config(0, upd, c.STEPS_0C)
        assert cfg["C_scale"] == 0.2 and mech["self_in_routing"] and mech["kin"] == "label"
        rare = arm in ("H-kin", "H-nobias", "A-kin-3k", "H2-kin")
        assert (cfg["initial_trait_mean"], cfg["initial_trait_stddev"]) == ((0.05, 0.02) if rare else (0.9, 0.05))
        assert cfg["B_plus_scale"] == (1.0 if rare else 0.05)
        if arm != "H-nobias":
            assert (cfg["kin_weight_same_lineage"], cfg["kin_weight_other_lineage"]) == (0.8, 0.2)
    assert "self_weight" not in full["A-kin-3k"][0]


def test_step0c_attempt2_only_after_failure(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_step0c as r
    calls = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            return [{"arm": a, "seed": s, "final_mean_trait": 0.1, "success": 0, "final_identity_count": 1,
                     "traj_every_50": [0.1]} for a, _, _, s in jobs]

    def fake_score(kin, nobias, below, alpha):
        calls.append((kin[0]["arm"], nobias[0]["arm"], below[0]["arm"], alpha))
        return {"met": False}

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "score_t0c", fake_score)
    monkeypatch.setattr(r, "DATA_DIR", str(__import__("tempfile").mkdtemp()))
    r.main()
    assert calls == [("H-kin", "H-nobias", "H-below", 0.05), ("H2-kin", "H-nobias", "H2-below", 0.025)]
