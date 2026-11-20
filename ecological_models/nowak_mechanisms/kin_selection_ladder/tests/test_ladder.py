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


def test_global_replacement_candidates_and_local_routing():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import GlobalReplacementEngine
    e = make_engine(run_config(2, {"simulation_steps": 3}), replacement="global", kin="label")
    assert isinstance(e, GlobalReplacementEngine)
    grid_mask = e.neighbor_mask.copy()
    c = e.draw_candidates()
    assert len(c) == e.n_sites and all(len(x) == 5 and len(set(x.tolist())) == 5 for x in c)
    own = np.mean([i in x for i, x in enumerate(c)])
    assert own < 0.05                                       # focal included only by chance (5/576)
    e.step()
    assert np.array_equal(e.neighbor_mask, grid_mask)       # routing still on the grid
    # candidates spread over the grid, not local
    far = np.mean([not grid_mask[i, x].any() for i, x in enumerate(c)])
    assert far > 0.9
    with pytest.raises(ValueError):
        make_engine(run_config(2, {}), replacement="weird")


def test_global_stream_separate_and_local_unchanged():
    a = make_engine(run_config(4, {"simulation_steps": 20}), kin="label")
    b = make_engine(run_config(4, {"simulation_steps": 20}), replacement="local", kin="label")
    for _ in range(20):
        a.step(); b.step()
    assert np.array_equal(a.h, b.h)


def test_score_t0d_branches_and_corr():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.analysis import neighbour_correlation, score_t0d
    assert score_t0d(_rows(20), _rows(2), _rows(0))["branch"] == "met"
    assert score_t0d(_rows(20), _rows(13), _rows(0))["branch"] == "comparison failed"
    assert score_t0d(_rows(14), _rows(0), _rows(0))["branch"] == "base replication failure"
    assert score_t0d(_rows(20), _rows(0), _rows(3))["branch"] == "base replication failure"
    h = np.array([0.0, 0.0, 1.0, 1.0])
    assert neighbour_correlation(h, np.array([0, 2]), np.array([1, 3])) == pytest.approx(1.0)
    assert neighbour_correlation(h, np.array([0, 3]), np.array([2, 1])) == pytest.approx(-1.0)
    assert np.isnan(neighbour_correlation(h, np.array([0, 1]), np.array([2, 3])))
    out = score_t0d(_rows(15), _rows(7), _rows(2))
    assert out["met"] and out["local"] == 15 and out["global"] == 7 and "kin" not in out
    assert score_t0d(_rows(15), _rows(8), _rows(2))["branch"] == "comparison failed"


def test_step0d_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a = c.STEP0D_ARMS
    assert a["V-local"] == c.STEP0C_ARMS["H-nobias"]          # the H-nobias configuration, rerun
    assert a["V-global"][0]["replacement"] == "global" and a["V-global"][1] == a["V-local"][1]
    assert a["V-below"][1]["B_plus_scale"] == 0.05 and a["V-below"][1]["initial_trait_mean"] == 0.9
    assert a["V-null"][1]["B_plus_scale"] == 0.0 and a["V-null"][1]["C_scale"] == 0.0
    assert a["V-null"][0]["replacement"] == "global"


def test_global_candidates_are_the_replacement_pool(monkeypatch):
    from moran_models.interaction_kernel.core import engine as eng_mod
    e = make_engine(run_config(1, {"simulation_steps": 2}), replacement="global", kin="label")
    seen = {}
    real = eng_mod.local_replacement_step

    def spy(trait, lineage, fitness, neighbor_indices, *args):
        seen["pool"] = neighbor_indices
        out = real(trait, lineage, fitness, neighbor_indices, *args)
        seen["parents"] = out[2]
        return out

    monkeypatch.setattr(eng_mod, "local_replacement_step", spy)
    e.step()
    pools = seen["pool"]
    assert all(len(p) == 5 for p in pools) and pools is e.neighbor_indices
    assert all(seen["parents"][i] in pools[i] for i in range(e.n_sites))


def test_overlapping_death1_equals_base_local_and_global():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    for repl in ("local", "global"):
        base = make_engine(run_config(6, {**c.RARE, **c.UNIFORM, "simulation_steps": 40}), replacement=repl, kin="label")
        ov = make_engine(run_config(6, {**c.RARE, **c.UNIFORM, "simulation_steps": 40}), replacement=repl, death=1.0,
                         kin="label")
        for _ in range(40):
            base.step(); ov.step()
        assert np.array_equal(base.h, ov.h) and np.array_equal(base.lineage, ov.lineage)


def test_overlapping_survivors_keep_site_and_death_rate():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    e = make_engine(run_config(7, {**c.RARE, **c.UNIFORM, "simulation_steps": 5}), death=0.5, kin="label")
    before_h, before_l = e.h.copy(), e.lineage.copy()
    e.step()
    s = e.last_survivors
    assert np.array_equal(e.h[s], before_h[s]) and np.array_equal(e.lineage[s], before_l[s])
    assert 0.44 < s.mean() < 0.56
    # death draws use their own stream: the engine stream (and so dead sites' offspring) match the base step
    b = make_engine(run_config(7, {**c.RARE, **c.UNIFORM, "simulation_steps": 5}), kin="label")
    b.step()
    assert np.array_equal(e.h[~s], b.h[~s])
    with pytest.raises(ValueError):
        make_engine(run_config(7, {}), death=0.0, kin="label")


def test_classify_step1_order():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.analysis import classify_step1
    f = lambda l, g, b, corr: classify_step1(_rows(l), _rows(g), _rows(b), corr, 0.025, 0.10)["class"]
    assert f(20, 2, 0, 0.05) == "met"
    assert f(20, 2, 0, 0.11) == "control invalid"
    assert f(20, 2, 0, float("nan")) == "control invalid"
    assert f(14, 0, 0, 0.0) == "local failure"
    assert f(20, 0, 3, 0.0) == "local failure"
    assert f(20, 13, 0, 0.0) == "comparison failed"
    assert f(15, 7, 0, 0.0) == "met"            # p ~ 0.01 < 0.025


def test_step1_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.step1_arms(1), c.step1_arms(2)
    assert list(a1) == ["O-local", "O-global", "O-below", "O-null"] and list(a2)[0] == "O2-local"
    assert all(m["death"] == 0.5 for m, _ in a1.values()) and all(m["death"] == 0.8 for m, _ in a2.values())
    assert c.STEP1_ATTEMPTS[1]["steps"] == 6000 and c.STEP1_ATTEMPTS[2]["steps"] == 3750
    assert a1["O-global"][0]["replacement"] == "global" and a1["O-local"][1] == a1["O-global"][1]
    assert a1["O-below"][1]["B_plus_scale"] == 0.05 and a1["O-null"][1]["C_scale"] == 0.0


def test_step1_runner_windows_and_gating(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_step1 as r
    assert r.corr_steps(6000) == [1000, 2000, 3000, 4000, 5000, 6000]
    assert r.corr_steps(3750) == [1000, 2000, 3000]
    row = r.run_one(("O-local", {"self_in_routing": True, "kin": "label", "death": 0.5, "replacement": "local"},
                     {"initial_trait_mean": 0.9, "initial_trait_stddev": 0.0, "mutation_rate": 0.0,
                      "kin_weight_same_lineage": 0.5, "kin_weight_other_lineage": 0.5}, 0, 1000))
    assert len(row["traj_every_50"]) == 20 and len(row["neighbour_h_corr"]) == 1
    calls = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            calls.append(jobs[0][4])
            return [{"arm": a, "seed": s, "final_mean_trait": 0.9, "success": 1, "sustained_success": 1,
                     "survival_fraction": 0.5, "traj_every_50": [0.9], "neighbour_h_corr": [0.0] * len(r.corr_steps(n))}
                    for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(r, "classify_step1", lambda *a: {"met": True, "class": "met"})
    r.main()
    assert calls == [6000]                                  # attempt 1 met: no attempt 2
    calls.clear()
    monkeypatch.setattr(r, "classify_step1", lambda *a: {"met": False, "class": "comparison failed"})
    r.main()
    assert calls == [6000, 3750]


def _traj(e, n):
    hs, ls = [], []
    for _ in range(n):
        e.step()
        hs.append(e.h.copy()); ls.append(e.lineage.copy())
    return hs, ls


def test_survival_lambda0_equals_step1_and_null_equals_onull():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    for repl in ("local", "global"):
        cfg = lambda: run_config(8, {**c.RARE, **c.UNIFORM, "simulation_steps": 60})
        a = _traj(make_engine(cfg(), replacement=repl, death=0.5, kin="label"), 60)
        b = _traj(make_engine(cfg(), replacement=repl, death=0.5, lam=0.0, kin="label"), 60)
        assert all(np.array_equal(x, y) for x, y in zip(a[0], b[0])) and all(np.array_equal(x, y) for x, y in zip(a[1], b[1]))
    for lam in (0.5, 1.0):
        cfg = lambda: run_config(9, {**c.RARE, **c.UNIFORM, "B_plus_scale": 0.0, "C_scale": 0.0, "simulation_steps": 60})
        a = _traj(make_engine(cfg(), replacement="local", death=0.5, kin="label"), 60)
        b = _traj(make_engine(cfg(), replacement="local", death=0.5, lam=lam, kin="label"), 60)
        assert all(np.array_equal(x, y) for x, y in zip(a[0], b[0]))
        assert all(np.array_equal(x, y) for x, y in zip(a[1], b[1]))


def test_death_lottery_values_and_uniform_births():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    e = make_engine(run_config(3, {**c.RARE, **c.UNIFORM, "simulation_steps": 5}), death=0.5, lam=1.0, kin="label")
    x = np.zeros(e.n_sites)
    assert np.allclose(e.death_probabilities(x), 0.5)
    x[0] = 0.12                                     # one site 0.12 better than its four neighbours
    d = e.death_probabilities(x)
    w0 = np.exp(-1.0)
    assert d[0] == pytest.approx(0.5 * w0 / ((w0 + 4) / 5))
    nb = [j for j in e.neighbor_indices[0] if j != 0][0]
    assert d[nb] > 0.5                              # neighbours of a high-payoff site die more often
    assert (e.death_probabilities(np.linspace(-5, 5, e.n_sites)) <= 1.0).all()
    # lam = 1: births uniform -> (1 - lam) * W is all zeros
    e2 = make_engine(run_config(3, {**c.RARE, **c.UNIFORM, "simulation_steps": 5}), replacement="global", death=0.5,
                     lam=1.0, kin="label")
    grid = e2.grid_mask.copy()
    e2.step()
    assert np.array_equal(e2.grid_mask, grid) and all(len(x) == 5 for x in e2.neighbor_indices)
    with pytest.raises(ValueError):
        make_engine(run_config(3, {}), death=0.5, lam=1.5, kin="label")


def test_step1b_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.step1b_arms(1), c.step1b_arms(2)
    assert list(a1) == ["S-local", "S-global", "S-below", "S-null"] and list(a2)[0] == "S2-local"
    assert all(m["lam"] == 1.0 and m["death"] == 0.5 for m, _ in a1.values())
    assert all(m["lam"] == 0.5 for m, _ in a2.values())
    assert a1["S-global"][0]["replacement"] == "global" and a1["S-below"][1]["B_plus_scale"] == 0.05
    assert c.STEP1B_STEPS == 6000


def test_birth_fitness_is_scaled_by_one_minus_lambda(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder import ladder_model as lm
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    seen = {}
    real = lm.local_replacement_step

    def spy(trait, lineage, fitness, *args):
        seen["fit"] = np.array(fitness)
        return real(trait, lineage, fitness, *args)

    monkeypatch.setattr(lm, "local_replacement_step", spy)
    for lam in (1.0, 0.5):
        e = make_engine(run_config(3, {**c.RARE, **c.UNIFORM, "simulation_steps": 3}), death=0.5, lam=lam, kin="label")
        e.h = np.linspace(0, 1, e.n_sites)
        K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
        W = 1.0 + K.T @ (1.0 * e.h) - 0.2 * e.h
        e.step()
        assert np.allclose(seen["fit"], (1.0 - lam) * W)


def test_step1b_runner_gating(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_step1b as r
    seen = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            seen.append(jobs[0][1]["lam"])
            return [{"arm": a, "seed": s, "final_mean_trait": 0.9, "success": 1, "sustained_success": 1,
                     "survival_fraction": 0.5, "death_fraction": 0.5, "traj_every_50": [0.9],
                     "neighbour_h_corr": [0.0] * len(r.corr_steps(n))} for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(r, "classify_step1", lambda *a: {"met": False, "class": "local failure"})
    r.main()
    assert seen == [1.0, 0.5]
    import json
    v = json.loads((tmp_path / "step1b_verdict.json").read_text())
    assert "step1b_met" in v and (tmp_path / "step1b_runs.csv").exists()
    seen.clear()
    monkeypatch.setattr(r, "classify_step1", lambda *a: {"met": True, "class": "met"})
    r.main()
    assert seen == [1.0]


def test_global_death_normalization():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    e = make_engine(run_config(3, {**c.RARE, **c.UNIFORM, "simulation_steps": 5}), death=0.5, lam=1.0,
                    norm="global", kin="label")
    x = np.zeros(e.n_sites)
    assert np.allclose(e.death_probabilities(x), 0.5)
    x[0] = 0.12
    d = e.death_probabilities(x)
    w0 = np.exp(-1.0)
    mean = (w0 + e.n_sites - 1) / e.n_sites
    assert d[0] == pytest.approx(0.5 * w0 / mean)
    nb = [j for j in e.neighbor_indices[0] if j != 0][0]
    far = e.n_sites // 2
    assert d[nb] == pytest.approx(d[far])                                # neighbours no different from far sites
    assert d[far] == pytest.approx(0.5 / mean)
    with pytest.raises(ValueError):
        make_engine(run_config(3, {}), death=0.5, lam=1.0, norm="weird", kin="label")


def test_step1c_reductions_and_arms():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    for repl in ("local", "global"):
        cfg = lambda: run_config(8, {**c.RARE, **c.UNIFORM, "simulation_steps": 60})
        a = _traj(make_engine(cfg(), replacement=repl, death=0.5, kin="label"), 60)
        b = _traj(make_engine(cfg(), replacement=repl, death=0.5, lam=0.0, norm="global", kin="label"), 60)
        assert all(np.array_equal(x, y) for x, y in zip(a[0], b[0])) and all(np.array_equal(x, y) for x, y in zip(a[1], b[1]))
    for lam in (0.5, 1.0):
        cfg = lambda: run_config(9, {**c.RARE, **c.UNIFORM, "B_plus_scale": 0.0, "C_scale": 0.0, "simulation_steps": 60})
        a = _traj(make_engine(cfg(), replacement="local", death=0.5, kin="label"), 60)
        b = _traj(make_engine(cfg(), replacement="local", death=0.5, lam=lam, norm="global", kin="label"), 60)
        assert all(np.array_equal(x, y) for x, y in zip(a[0], b[0])) and all(np.array_equal(x, y) for x, y in zip(a[1], b[1]))
    a1, a2 = c.step1c_arms(1), c.step1c_arms(2)
    assert list(a1) == ["L-local", "L-global", "L-below", "L-null"] and list(a2)[0] == "L2-local"
    assert all(m["norm"] == "global" and m["lam"] == 1.0 for m, _ in a1.values())
    assert all(m["lam"] == 0.5 for m, _ in a2.values())
    b1 = c.step1b_arms(1)
    for (k, (m, u)), (k2, (m2, u2)) in zip(a1.items(), b1.items()):
        assert u == u2 and {kk: vv for kk, vv in m.items() if kk != "norm"} == m2


def test_step1c_runner_uses_names(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_step1b as r
    seen = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            seen.append((jobs[0][0], jobs[0][1]["norm"]))
            return [{"arm": a, "seed": s, "final_mean_trait": 0.9, "success": 1, "sustained_success": 1,
                     "survival_fraction": 0.5, "death_fraction": 0.5, "traj_every_50": [0.9],
                     "neighbour_h_corr": [0.0] * len(r.corr_steps(n))} for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(r, "classify_step1", lambda *a: {"met": False, "class": "local failure"})
    r.main(c.step1c_arms, "step1c")
    assert seen == [("L-local", "global"), ("L2-local", "global")]
    assert (tmp_path / "step1c_verdict.json").exists()


def test_age_engine_period0_equals_base_and_timing():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import AgeEngine
    for repl in ("local", "global"):
        cfg = lambda: run_config(8, {**c.RARE, **c.UNIFORM, "simulation_steps": 60})
        a = _traj(make_engine(cfg(), replacement=repl, death=0.5, lam=0.5, norm="global", kin="label"), 60)
        b = _traj(make_engine(cfg(), replacement=repl, death=0.5, lam=0.5, norm="global", juvenile_period=0,
                              kin="label"), 60)
        assert all(np.array_equal(x, y) for x, y in zip(a[0], b[0])) and all(np.array_equal(x, y) for x, y in zip(a[1], b[1]))
    e = make_engine(run_config(8, {**c.RARE, **c.UNIFORM, "simulation_steps": 5}), death=0.5, lam=0.5, norm="global",
                    juvenile_period=1, juvenile_strength=0.0, kin="label")
    assert isinstance(e, AgeEngine) and 0.4 < (e.age == 0).mean() < 0.6 and set(np.unique(e.age)) <= {0, 1}
    age0 = e.age.copy()
    e.step()
    s = e.last_survivors
    assert np.array_equal(e.age[s], age0[s] + 1) and (e.age[~s] == 0).all()
    with pytest.raises(ValueError):
        make_engine(run_config(8, {}), death=0.5, lam=0.5, juvenile_period=-1, kin="label")


def test_age_expression_payoffs():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    for strength in (0.0, 0.5):
        e = make_engine(run_config(2, {**c.RARE, **c.UNIFORM, "simulation_steps": 5}), death=0.5, lam=0.5,
                        norm="global", juvenile_period=1, juvenile_strength=strength, kin="label")
        e.h = np.full(e.n_sites, 0.6)
        expr = e.expressed_trait()
        juv = e.age < 1
        assert np.allclose(expr[juv], strength * 0.6) and np.allclose(expr[~juv], 0.6)


def test_step2a_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.step2a_arms(1), c.step2a_arms(2)
    assert list(a1) == ["A-local", "A-global", "A-below", "A-null"] and list(a2)[0] == "A2-local"
    assert all(m["juvenile_period"] == 1 and m["juvenile_strength"] == 0.0 for m, _ in a1.values())
    assert all(m["juvenile_strength"] == 0.5 for m, _ in a2.values())
    assert all(m["lam"] == 0.5 and m["norm"] == "global" and m["death"] == 0.5 for m, _ in a1.values())
    base = c.step1c_arms(2)
    for (m, u), (mb, ub) in zip(a1.values(), base.values()):
        assert u == ub and {k: v for k, v in m.items() if not k.startswith("juvenile")} == mb


def test_age_step_uses_expressed_trait_in_payoffs(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder import ladder_model as lm
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    seen = {}
    real = lm.local_replacement_step

    def spy(trait, lineage, fitness, *args):
        seen["fit"] = np.array(fitness)
        return real(trait, lineage, fitness, *args)

    monkeypatch.setattr(lm, "local_replacement_step", spy)
    e = make_engine(run_config(4, {**c.RARE, **c.UNIFORM, "simulation_steps": 3}), death=0.5, lam=0.5, norm="global",
                    juvenile_period=1, juvenile_strength=0.0, kin="label")
    e.h = np.linspace(0, 1, e.n_sites)
    juv = e.age < 1
    expr = np.where(juv, 0.0, e.h)
    K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
    W = 1.0 + K.T @ expr - 0.2 * expr
    e.step()
    assert np.allclose(seen["fit"], 0.5 * W)
    assert e.last_juvenile_fraction == pytest.approx(juv.mean())


def test_step2a_runner_metadata(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_step1b as r

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            return [{"arm": a, "seed": s, "final_mean_trait": 0.9, "success": 1, "sustained_success": 1,
                     "survival_fraction": 0.5, "death_fraction": 0.5, "juvenile_fraction": 0.5, "traj_every_50": [0.9],
                     "neighbour_h_corr": [0.0] * len(r.corr_steps(n))} for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(r, "classify_step1", lambda *a: {"met": False, "class": "local failure"})
    r.main(c.step2a_arms, "step2a")
    v = json.loads((tmp_path / "step2a_verdict.json").read_text())
    assert v["attempt1"]["lam"] == 0.5 and v["attempt2"]["lam"] == 0.5
    assert v["attempt1"]["descriptive"]["A-local"]["juvenile_fraction"] == 0.5


def test_d2a_expected_fitness_identity_and_probs():
    from moran_models.interaction_kernel.core.selection import _local_softmax_probabilities
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_d2a as r
    vals = np.array([0.1, 0.3, 0.0, 0.2, 0.25])
    assert np.allclose(r.birth_probs(vals, 0.12), _local_softmax_probabilities(vals, 0.12))
    arms = r.d2a_arms()
    for arm in ("A-global", "A-local", "L2-global"):
        m, u = arms[arm]
        m = dict(m)
        from ecological_models.nowak_mechanisms.kin_selection_ladder import ladder_model as lm
        e = lm.make_engine(run_config(1, u, 50), replacement=m.pop("replacement"), death=m.pop("death"),
                           lam=m.pop("lam"), norm=m.pop("norm"), **m)
        e.h = np.random.default_rng(0).random(e.n_sites)
        x, W = r.payoff(e)
        d = e.death_probabilities(x)
        cands = e.draw_candidates() if e.global_candidates else e.neighbor_indices
        surv, off = r.expected_fitness(d, W, cands, e.lam, e.temperature, e.n_sites)
        assert (surv + off).sum() == pytest.approx(e.n_sites)          # each site holds one occupant next step
        juv = (e.age < e.juvenile_period) if hasattr(e, "age") else np.zeros(e.n_sites, bool)
        tot = r.cov_contrib(e.h, surv + off)
        assert r.cov_contrib(e.h, surv, juv) + r.cov_contrib(e.h, surv, ~juv) == pytest.approx(r.cov_contrib(e.h, surv))
        assert r.cov_contrib(e.h, surv) + r.cov_contrib(e.h, off) == pytest.approx(tot)
        # recomputed payoff/death equal the engine's
        e.step()
        assert np.allclose(e.last_death_prob, d)


def test_d2a_run_one_smoke_and_accounting(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_d2a as r
    monkeypatch.setattr(r, "D2A_STEPS", 30)
    monkeypatch.setattr(r, "D2A_SAMPLES", [10, 20, 30])
    a, (m, u) = "A-global", r.d2a_arms()["A-global"]
    row = r.run_one((a, m, u, 0))
    assert row["max_death_prob_error"] < 1e-12
    assert row["real_survivor"] + row["real_parent"] + row["real_mutation"] == pytest.approx(row["real_total"], abs=1e-9)
    assert np.isfinite(row["spearman_all"])


def test_d2a_measurement_leaves_trajectory_unchanged(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder import ladder_model as lm
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_d2a as r
    monkeypatch.setattr(r, "D2A_STEPS", 40)
    monkeypatch.setattr(r, "D2A_SAMPLES", [20, 40])
    for arm in ("A-global", "A-local"):
        m, u = r.d2a_arms()[arm]
        row = r.run_one((arm, m, u, 2))
        mm = dict(m)
        e = lm.make_engine(run_config(2, u, 40), replacement=mm.pop("replacement"), death=mm.pop("death"),
                           lam=mm.pop("lam"), norm=mm.pop("norm"), **mm)
        for _ in range(40):
            e.step()
        assert row["final_mean_h"] == float(e.h.mean())


def test_d2a_classify_rules():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_d2a as r

    def rows(tot, surv, birth, sp_all, sp_ad=0.0, sp_j=0.0):
        return [{"expected_total": tot, "surv_part": surv, "birth_part": birth, "spearman_all": sp_all,
                 "spearman_adult": sp_ad, "spearman_juv": sp_j} for _ in range(5)]

    ref = rows(1.0, 0.6, 0.4, 0.3)
    near0 = rows(0.05, 0.0, 0.05, 0.0)
    near0[0] = {**near0[0], "expected_total": -0.05}           # not positive in all runs, all below 10% of A-local
    c, reading = r.classify({"A-local": ref, "L2-global": near0,
                             "A-global": rows(0.5, 0.4, 0.1, 0.05)})
    assert c["A-global"] == {"expected_selection": "positive", "part": "survival", "association": "present"}
    assert c["L2-global"]["expected_selection"] == "absent" and c["L2-global"]["association"] == "absent"
    assert reading.startswith("selection through an association")
    c, reading = r.classify({"A-local": ref, "L2-global": ref, "A-global": rows(0.5, 0.1, 0.4, 0.0)})
    assert c["A-global"]["part"] == "birth" and c["A-global"]["association"] == "absent"
    assert reading.startswith("a path these measures do not capture")
    nan = float("nan")
    c, _ = r.classify({"A-local": ref, "L2-global": ref, "A-global": rows(0.5, 0.1, 0.4, 0.0, 0.0, nan)})
    assert c["A-global"]["association"] == "mixed"                      # undefined is not "absent"
    c, reading = r.classify({"A-local": ref, "L2-global": ref, "A-global": rows(0.2, 0.1, 0.1, 0.0)})
    assert c["A-global"]["part"] == "both"
    mixed = rows(0.5, 0.4, 0.1, 0.05)
    mixed[0] = {**mixed[0], "expected_total": -0.5}
    c, reading = r.classify({"A-local": ref, "L2-global": ref, "A-global": mixed})
    assert c["A-global"]["expected_selection"] == "mixed" and reading.startswith("step-2a spread may be")


# ---- Step K0: costly-helping base ----

def test_k0_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.k0_arms(1), c.k0_arms(2)
    assert list(a1) == ["K3-local", "K6-local", "K12-local", "K24-local", "K12-global", "K-below", "K-null"]
    assert list(a2) == ["K3-DB", "K6-DB", "K12-DB", "K24-DB", "K12-DB-global", "K-below-DB", "K-null-DB"]
    for arms, ex in ((a1, False), (a2, True)):
        for name, (m, u) in arms.items():
            assert m["self_in_routing"] is False and m["death"] == 0.5 and m["exclude_focal"] is ex
            assert u["kin_weight_same_lineage"] == u["kin_weight_other_lineage"] == 0.5
            if "null" in name:
                assert u["B_plus_scale"] == 0.0 and u["C_scale"] == 0.0
            else:
                assert u["C_scale"] == 0.2
        for bc in (3, 6, 12, 24):
            nm = f"K{bc}-local" if not ex else f"K{bc}-DB"
            assert arms[nm][1]["B_plus_scale"] / 0.2 == pytest.approx(bc)
            assert arms[nm][0]["replacement"] == "local" and arms[nm][1]["initial_trait_mean"] == 0.05
    assert a1["K12-global"][0]["replacement"] == "global" and a1["K12-global"][1]["B_plus_scale"] == 2.4
    assert a1["K-below"][1]["initial_trait_mean"] == 0.9 and a1["K-below"][1]["B_plus_scale"] == 0.05
    g2, b2 = a2["K12-DB-global"], a2["K-below-DB"]
    assert g2[0]["replacement"] == "global" and g2[1]["B_plus_scale"] == 2.4 and g2[1]["initial_trait_mean"] == 0.05
    assert b2[0]["replacement"] == "local" and b2[1]["initial_trait_mean"] == 0.9 and b2[1]["B_plus_scale"] == 0.05
    assert a1["K12-global"][1]["initial_trait_mean"] == 0.05
    assert c.k0_roles(1) == ("K12-local", "K12-global", "K-below")
    assert c.k0_roles(2) == ("K12-DB", "K12-DB-global", "K-below-DB")


def test_k0_self_in_routing_reproduces_o_local():
    # registered check: K0 attempt-1 code with self in routing and B = 1.0 equals step 1's O-local runs
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.step1_arms(1)["O-local"]
    km, ku = c.k0_arms(1)["K12-local"]
    km = {**km, "self_in_routing": True}
    ku = {**ku, "B_plus_scale": 1.0}
    e1 = make_engine(run_config(3, u, 60), **{**m})
    e2 = make_engine(run_config(3, ku, 60), **km)
    for _ in range(60):
        e1.step(); e2.step()
    assert np.array_equal(e1.h, e2.h) and np.array_equal(e1.lineage, e2.lineage)


def test_k0_own_receipt_independent_of_own_h():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K12-local"]
    e = make_engine(run_config(4, u, 5), **m)
    K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
    assert np.allclose(np.diag(K), 0.0) and np.allclose(K.sum(axis=1), 1.0)
    assert np.allclose(K[K > 0], 0.25)
    # raising one site's h changes others' receipts but not its own
    B = e.mechanism.compute_positive_output(e.h, e.extra_state, e.cfg)
    h2 = e.h.copy(); h2[10] = min(1.0, h2[10] + 0.5)
    B2 = e.mechanism.compute_positive_output(h2, e.extra_state, e.cfg)
    R, R2 = K.T @ B, K.T @ B2
    assert R2[10] == pytest.approx(R[10]) and (R2 - R).sum() == pytest.approx(2.4 * (h2[10] - e.h[10]))


def test_k0_db_excludes_focal_local_and_global():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder import ladder_model as lm
    m, u = c.k0_arms(2)["K12-DB"]
    e = make_engine(run_config(5, u, 5), **m)
    assert isinstance(e, lm.DeathBirthEngine)
    assert all(len(n) == 4 and i not in n for i, n in enumerate(e.neighbor_indices))
    # routing still the grid neighbours without self
    K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
    assert np.allclose(np.diag(K), 0.0) and np.allclose(K[K > 0], 0.25)
    mg, ug = c.k0_arms(2)["K12-DB-global"]
    g = make_engine(run_config(5, ug, 5), **mg)
    cand = g.draw_candidates()
    assert all(len(n) == 4 and len(set(n.tolist())) == 4 and i not in n for i, n in enumerate(cand))
    # a dead site's parent is never its own occupant: track parents through the lottery
    import moran_models.interaction_kernel.core.engine as eng_mod
    seen = []
    orig = eng_mod.local_replacement_step

    def spy(trait, lineage, fitness, neighbor_indices, *a):
        out = orig(trait, lineage, fitness, neighbor_indices, *a)
        seen.append(out[2].copy())
        return out
    eng_mod.local_replacement_step = spy
    try:
        for _ in range(5):
            e.step(); g.step()
    finally:
        eng_mod.local_replacement_step = orig
    assert all((p != np.arange(len(p))).all() for p in seen)
    with pytest.raises(ValueError):
        make_engine(run_config(5, u, 5), exclude_focal=True, self_in_routing=False, kin="label")


def test_k0_engines_death_and_survivors():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder import ladder_model as lm
    m, u = c.k0_arms(1)["K12-local"]
    e = make_engine(run_config(5, u, 5), **m)
    assert type(e) is lm.OverlappingEngine and all(len(n) == 5 for n in e.neighbor_indices)
    for name in ("K12-local", "K12-DB", "K12-DB-global"):
        m, u = {**c.k0_arms(1), **c.k0_arms(2)}[name]
        e = make_engine(run_config(5, u, 5), **m)
        expected = np.random.default_rng(lm.DEATH_STREAM_OFFSET + 5).random(e.n_sites) >= 0.5
        h0, l0 = e.h.copy(), e.lineage.copy()
        e.step()
        assert np.array_equal(e.last_survivors, expected), name
        assert np.array_equal(e.h[expected], h0[expected]) and np.array_equal(e.lineage[expected], l0[expected])


def test_k0_runner_manipulation_check(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_k0 as r
    seen = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            out = []
            for a, _, _, s, n in jobs:
                corr = [0.0] * 6
                if a.endswith("global"):
                    corr = [float("nan")] + [0.0] * 5 if s == 0 else [0.06 if s % 2 else 0.0] * 6
                out.append({"arm": a, "seed": s, "final_mean_trait": 0.9, "success": 1, "sustained_success": 1,
                            "survival_fraction": 0.5, "traj_every_50": [0.9], "neighbour_h_corr": corr})
            return out

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    real = r.classify_step1
    monkeypatch.setattr(r, "classify_step1", lambda *a: (seen.append(a[3]), real(*a))[1])
    r.main()
    assert np.isnan(seen[0])                                 # one undefined sample: control invalid, no attempt 2
    import json
    v = json.loads((tmp_path / "k0_verdict.json").read_text())
    assert v["attempt1"]["class"] == "control invalid" and "attempt2" not in v


def test_k0_runner_gating(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_k0 as r
    calls = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            calls.append(sorted({j[0] for j in jobs})[0])
            return [{"arm": a, "seed": s, "final_mean_trait": 0.9, "success": 1, "sustained_success": 1,
                     "survival_fraction": 0.5, "traj_every_50": [0.9], "neighbour_h_corr": [0.0] * 6}
                    for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    for cls, n in (("met", 1), ("control invalid", 1), ("local failure", 2), ("comparison failed", 2)):
        calls.clear()
        monkeypatch.setattr(r, "classify_step1", lambda *a, _c=cls: {"met": _c == "met", "class": _c})
        r.main()
        assert len(calls) == n, cls


# ---- Step K1: parental care ----

def _k1(name, seed=8, steps=5, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.k1_arms(1), **c.k1_arms(2)}[name]
    m = dict(m)
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_k1_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.k1_arms(1), c.k1_arms(2)
    assert sorted(a1) == sorted(["P6-local", "P1.5-local", "P3-local", "P12-local", "N6-local", "P-below",
                                 "P3-global", "P6-global", "P12-global"])
    assert sorted(a2) == sorted(["H6-local", "H1.5-local", "H3-local", "H12-local", "H-below",
                                 "H3-global", "H6-global", "H12-global"])
    for arms in (a1, a2):
        for name, (m, u) in arms.items():
            assert m["self_in_routing"] is False and m["death"] == 0.5 and u["C_scale"] == 0.2
            assert m["replacement"] == ("global" if name.endswith("global") else "local")
            assert u["initial_trait_mean"] == (0.9 if "below" in name else 0.05)
            if name != "N6-local":
                assert m["care"] == ("offspring" if name[0] == "P" else "hybrid")
            bc = name[1:].split("-")[0]
            if bc:
                assert u["B_plus_scale"] / 0.2 == pytest.approx(float(bc))
            else:
                assert u["B_plus_scale"] == 0.05
    assert "care" not in a1["N6-local"][0] and a1["N6-local"][0] == {**c.k0_arms(1)["K6-local"][0]}
    assert a1["N6-local"][1] == c.k0_arms(1)["K6-local"][1]
    assert c.k1_roles(1) == ("P6-local", "P-below", "P6-global")
    assert c.k1_roles(2) == ("H6-local", "H-below", "H6-global")


def test_k1_ids_parents_and_locality():
    import moran_models.interaction_kernel.core.engine as eng_mod
    for name in ("P6-local", "P6-global"):
        e = _k1(name, steps=40)
        assert (e.parent_ids == -1).all()
        for _ in range(40):
            ids0, h0, lab0, pid0 = e.ids.copy(), e.h.copy(), e.lineage.copy(), e.parent_ids.copy()
            e.step()
            s, dead = e.last_survivors, ~e.last_survivors
            assert np.array_equal(e.ids[s], ids0[s]) and np.array_equal(e.parent_ids[s], pid0[s])
            assert np.array_equal(e.h[s], h0[s]) and np.array_equal(e.lineage[s], lab0[s])
            assert np.array_equal(e.parent_ids[dead], ids0[e.mechanism.last_parents[dead]])
            assert len(set(e.ids.tolist())) == e.n_sites and not set(e.ids[dead].tolist()) & set(ids0.tolist())
            ps = e.parent_sites()
            js = np.nonzero(ps >= 0)[0]
            assert (e.ids[ps[js]] == e.parent_ids[js]).all() and (ps[js] != js).all()
            if name == "P6-local":
                assert all(e.neighbor_mask[ps[j], j] for j in js)          # offspring of living parents are neighbours
        assert len(js) > 0


def test_k1_kernel_offspring_only_and_hybrid():
    for name in ("P6-local", "H6-local"):
        e = _k1(name, steps=30)
        for _ in range(30):
            e.step()
        ps = e.parent_sites()
        e.mechanism.parent_site = ps
        K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
        counts = np.bincount(ps[ps >= 0], minlength=e.n_sites)
        assert np.allclose(np.diag(K), 0.0)
        for i in range(e.n_sites):
            kids = np.nonzero(ps == i)[0]
            if len(kids):
                assert np.allclose(K[i, kids], 1 / len(kids)) and np.isclose(K[i].sum(), 1.0)
            elif name == "P6-local":
                assert np.allclose(K[i], 0.0)
            else:
                assert np.allclose(K[i][e.neighbor_mask[i] & (np.arange(e.n_sites) != i)], 0.25)
        assert (counts == 0).any() and (counts > 0).any()


def test_k1_null_equals_k_null_and_no_extra_draws():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K-null"]
    m = dict(m); m.pop("exclude_focal")
    ref = make_engine(run_config(9, u, 60), **m)
    e = _k1("P6-local", seed=9, steps=60, B_plus_scale=0.0, C_scale=0.0)
    for _ in range(60):
        ref.step(); e.step()
    assert np.array_equal(ref.h, e.h) and np.array_equal(ref.lineage, e.lineage)


def test_k1_diag_values():
    e = _k1("P6-local", steps=20)
    for _ in range(20):
        e.step()
    ps = e.parent_sites()
    counts = np.bincount(ps[ps >= 0], minlength=e.n_sites)
    h = e.h.copy()
    e.step()
    d = e.last_diag
    assert d["offspring_mean"] == pytest.approx(counts.mean())
    assert d["frac_no_offspring"] == pytest.approx((counts == 0).mean())
    assert d["benefit_lost"] == pytest.approx(h[counts == 0].sum() / h.sum())


def test_k1_runner_gating_and_n6_check(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_k1 as r
    import shutil
    shutil.copy("ecological_models/nowak_mechanisms/kin_selection_ladder/data/k0_runs.csv", tmp_path / "k0_runs.csv")
    import csv as _csv
    refrow = {int(x["seed"]): x for x in _csv.DictReader(open(tmp_path / "k0_runs.csv")) if x["arm"] == "K6-local"}
    ref = {k: float(v["final_mean_trait"]) for k, v in refrow.items()}
    calls, test_succ = [], {"v": 20}

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            calls.append(len(jobs))
            out = []
            for a, _, _, s, n in jobs:
                fm = ref[s] if a == "N6-local" else 0.9
                succ = int(fm >= 0.6)
                if a in ("P6-local", "H6-local"):
                    succ = int(s < test_succ["v"]); fm = 0.9 if succ else 0.1
                if "below" in a:
                    succ, fm = 0, 0.01
                row = {"arm": a, "seed": s, "final_mean_trait": fm, "success": succ, "sustained_success": succ,
                       "survival_fraction": 0.5, "traj_every_50": [fm], "neighbour_h_corr": [0.0] * 6,
                       **{k: 0.5 for k in r.DIAG_KEYS}}
                if a == "N6-local":
                    rr = refrow[s]
                    row.update(success=int(rr["success"]), sustained_success=int(rr["sustained_success"]),
                               survival_fraction=float(rr["survival_fraction"]))
                out.append(row)
            return out

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    r.main()
    assert calls == [180]                                         # met: no attempt 2
    calls.clear(); test_succ["v"] = 14
    r.main()
    assert calls == [180, 160]                                    # local failure: hybrid attempt 2
    import json
    v = json.loads((tmp_path / "k1_verdict.json").read_text())
    assert v["attempt1"]["class"] == "local failure" and v["attempt2"]["n6_successes"] == 0
    assert r.classify_k1([{"success": 1}] * 15, [{"success": 1}] * 3)["class"] == "local failure"
    assert r.score_h2([{"success": 1, "neighbour_h_corr": [0.2]}] * 20)["result"] == "not interpretable"
    bad = [{"seed": s, "final_mean_trait": ref[s], "success": 0, "sustained_success": 0, "survival_fraction": 0.4}
           for s in range(20)]                                      # final h matches, survival does not
    with pytest.raises(RuntimeError):
        r.check_n6(bad, tmp_path / "k0_runs.csv")


def test_k1_global_care_reaches_distant_offspring_and_po_corr():
    e = _k1("P6-global", steps=30)
    far = 0
    for _ in range(30):
        ps = e.parent_sites()
        js = np.nonzero(ps >= 0)[0]
        h = e.h.copy()
        e.step()
        if len(js) >= 2:
            assert e.last_diag["parent_offspring_corr"] == pytest.approx(np.corrcoef(h[ps[js]], h[js])[0, 1])
        e.mechanism.parent_site = ps
        K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
        for j in js:
            assert K[ps[j], j] > 0
            far += int(not e.neighbor_mask[ps[j], j])
    assert far > 0                                                  # some cared-for offspring are not neighbours
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    with pytest.raises(ValueError):
        c.k1_arms(3)


def test_k1_diag_window_and_hybrid_label(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_k1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    monkeypatch.setattr(r, "K1_DIAG_FROM", 3)
    m, u = c.k1_arms(1)["P6-local"]
    seen = []
    import ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model as lm
    orig = lm.ParentalEngine.step

    def spy(self):
        out = orig(self)
        seen.append((self.step_index - 1, self.last_diag["offspring_mean"]))
        return out
    monkeypatch.setattr(lm.ParentalEngine, "step", spy)
    row = r.run_one(("P6-local", m, u, 0, 8))
    expected = [v for t, v in seen if t >= 3]
    assert len(expected) == 5 and row["offspring_mean"] == pytest.approx(np.mean(expected))


# ---- Step R1: care on survival ----

def _r1(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.r1_arms(1), **c.r1_arms(2)}[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r1_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.r1_arms(1), c.r1_arms(2)
    assert sorted(a1) == sorted(["R6-local", "R3-local", "R12-local", "R24-local", "RN6-local", "R-below",
                                 "R6-global", "R12-global"])
    assert sorted(a2) == sorted(["R2-6-local", "R2-3-local", "R2-12-local", "R2-24-local", "R2-N6-local",
                                 "R2-below", "R2-6-global", "R2-12-global"])
    for arms, lam in ((a1, 1.0), (a2, 0.5)):
        for name, (m, u) in arms.items():
            assert m["care_lam"] == lam and m["self_in_routing"] is False and m["death"] == 0.5
            assert u["C_scale"] == 0.2 and u["kin_weight_same_lineage"] == u["kin_weight_other_lineage"]
            assert m["care"] == ("neighbours" if "N6" in name else "offspring")
            assert m["replacement"] == ("global" if name.endswith("global") else "local")
            assert u["initial_trait_mean"] == (0.9 if "below" in name else 0.05)
            if "below" in name:
                assert u["B_plus_scale"] == 0.05
            else:
                bc = name.replace("R2-", "R").replace("RN", "R")[1:].split("-")[0]
                assert u["B_plus_scale"] / 0.2 == pytest.approx(float(bc))
    assert c.r1_roles(1) == ("R6-local", "RN6-local", "R-below", "R6-global")
    assert c.r1_roles(2) == ("R2-6-local", "R2-N6-local", "R2-below", "R2-6-global")
    with pytest.raises(ValueError):
        c.r1_arms(0)


def test_r1_lam0_equals_k1():
    for r1name, k1name in (("R6-local", "P6-local"), ("R6-global", "P6-global")):
        e = _r1(r1name, seed=11, steps=60, mech_over={"care_lam": 0.0})
        k = _k1(k1name, seed=11, steps=60)
        for _ in range(60):
            e.step(); k.step()
            assert np.array_equal(e.h, k.h) and np.array_equal(e.lineage, k.lineage)
            assert np.array_equal(e.ids, k.ids) and np.array_equal(e.parent_ids, k.parent_ids)


def test_r1_null_equals_k_null():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K-null"]
    m = dict(m); m.pop("exclude_focal")
    for lam in (1.0, 0.5):
        ref = make_engine(run_config(9, u, 60), **m)
        e = _r1("R6-local", seed=9, steps=60, mech_over={"care_lam": lam}, B_plus_scale=0.0, C_scale=0.0)
        for _ in range(60):
            ref.step(); e.step()
        assert np.array_equal(ref.h, e.h) and np.array_equal(ref.lineage, e.lineage)


def test_r1_death_and_birth_rules(monkeypatch):
    import moran_models.interaction_kernel.core.engine as eng_mod
    for name, lam in (("R6-local", 1.0), ("R2-6-local", 0.5), ("RN6-local", 1.0)):
        e = _r1(name, steps=40)
        for _ in range(30):
            e.step()
        ps = e.parent_sites()
        e.mechanism.parent_site = ps
        K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
        assert np.allclose(np.diag(K), 0.0)
        if name.startswith("RN"):
            assert np.allclose(K[K > 0], 0.25) and np.allclose(K.sum(axis=1), 1.0)
        R = K.T @ (1.2 * e.h)
        d = e.death_probabilities(R)
        assert np.allclose(d, 0.5 * np.exp(-lam * R / 0.12)) and (d <= 0.5).all()
        assert np.allclose(d[R == 0], 0.5)
        seen = {}
        orig = eng_mod.local_replacement_step

        def spy(trait, lineage, fitness, *a):
            seen["W"] = fitness.copy()
            return orig(trait, lineage, fitness, *a)
        monkeypatch.setattr(eng_mod, "local_replacement_step", spy)
        h0 = e.h.copy()
        e.step()
        assert np.allclose(seen["W"], 1 + (1 - lam) * R - 0.2 * h0)
        assert e.last_diag["death_mean"] == pytest.approx(d.mean())
        monkeypatch.setattr(eng_mod, "local_replacement_step", orig)


def test_r1_survivor_and_id_bookkeeping():
    e = _r1("R6-local", steps=30)
    for _ in range(30):
        ids0, h0, pid0 = e.ids.copy(), e.h.copy(), e.parent_ids.copy()
        e.step()
        s, dead = e.last_survivors, ~e.last_survivors
        assert np.array_equal(e.ids[s], ids0[s]) and np.array_equal(e.h[s], h0[s])
        assert np.array_equal(e.parent_ids[s], pid0[s])
        assert np.array_equal(e.parent_ids[dead], ids0[e.mechanism.last_parents[dead]])
        ps = e.parent_sites(); js = np.nonzero(ps >= 0)[0]
        assert all(e.neighbor_mask[ps[j], j] for j in js)
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care="neighbours", self_in_routing=False, kin="label")
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care_lam=1.0, self_in_routing=False, kin="label")


def test_r1_classify_and_gating(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    one = lambda n, k: [{"success": int(i < k)} for i in range(n)]
    assert r.classify_r1(one(20, 14), one(20, 0), one(20, 0))["class"] == "local failure"
    assert r.classify_r1(one(20, 20), one(20, 0), one(20, 3))["class"] == "local failure"
    assert r.classify_r1(one(20, 16), one(20, 9), one(20, 0))["class"] == "comparison failed"
    assert r.classify_r1(one(20, 18), one(20, 2), one(20, 0))["class"] == "met"
    calls = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            calls.append(len(jobs))
            return [{"arm": a, "seed": s, "final_mean_trait": 0.5, "success": 0, "sustained_success": 0,
                     "survival_fraction": 0.5, "traj_every_50": [0.5], "neighbour_h_corr": [0.0] * 6,
                     **{k: 0.5 for k in r.DIAG_KEYS}} for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    for cls, n in (("met", 1), ("local failure", 2), ("comparison failed", 2)):
        calls.clear()
        monkeypatch.setattr(r, "classify_r1", lambda *a, _c=cls: {"met": _c == "met", "class": _c})
        r.main()
        assert calls == [160] * n, cls


def test_r1_diag_masks_and_h2():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    for name in ("R6-local", "RN6-local"):
        e = _r1(name, steps=40)
        for _ in range(30):
            e.step()
        ps = e.parent_sites()
        e.mechanism.parent_site = ps
        R = e.received_care()
        d = e.death_probabilities(R)
        counts = np.bincount(ps[ps >= 0], minlength=e.n_sites)
        h = e.h.copy()
        e.step()
        g = e.last_diag
        m = lambda x: float(x.mean()) if x.size else float("nan")   # empty class (e.g. all cared in RN6): nan
        assert g["death_cared"] == pytest.approx(m(d[R > 0]), nan_ok=True)
        assert g["death_uncared"] == pytest.approx(m(d[R == 0]), nan_ok=True)
        assert g["death_parents"] == pytest.approx(m(d[counts > 0]), nan_ok=True)
        assert g["frac_cared"] == pytest.approx((R > 0).mean())
        if name == "RN6-local":
            assert g["benefit_lost"] == 0.0
        else:
            assert g["benefit_lost"] == pytest.approx(h[counts == 0].sum() / h.sum())
    rows = lambda k, corr: [{"success": int(i < k), "neighbour_h_corr": [corr]} for i in range(20)]
    assert r.score_h2(rows(15, 0.05))["result"] == "met"
    assert r.score_h2(rows(14, 0.05))["result"] == "not met"
    assert r.score_h2(rows(20, 0.11))["result"] == "not interpretable"
    assert r.score_h2(rows(20, float("nan")))["result"] == "not interpretable"
    with pytest.raises(ValueError):
        c.r1_roles(3)


# ---- Diagnostic DR1 ----

def test_dr1_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a = c.dr1_arms()
    assert sorted(a) == sorted(["D12-local-high", "D24-local-high", "D48-local-high", "D6-global-high",
                                "D12-global-high", "D48-local", "D-null-local-high", "D-null-global-high"])
    r1 = c.r1_arms(1)
    for name, (m, u) in a.items():
        assert m["care_lam"] == 1.0 and m["care"] == "offspring" and m["self_in_routing"] is False
        assert m["replacement"] == ("global" if "global" in name else "local")
        assert u["initial_trait_mean"] == (0.05 if name == "D48-local" else 0.9)
        if "null" in name:
            assert u["B_plus_scale"] == 0.0 and u["C_scale"] == 0.0
        else:
            assert u["C_scale"] == 0.2
            assert u["B_plus_scale"] / 0.2 == pytest.approx(float(name[1:].split("-")[0]))
    # high-start arms differ from their R1 counterparts only in the start
    for high, rare in c.DR1_PAIRS.items():
        mh, uh = a[high]; mr, ur = r1[rare]
        assert mh == mr and {k: v for k, v in uh.items() if not k.startswith("initial")} == \
            {k: v for k, v in ur.items() if not k.startswith("initial")}


def test_dr1_scoring(tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    import shutil
    shutil.copy("ecological_models/nowak_mechanisms/kin_selection_ladder/data/r1_runs.csv", tmp_path / "r1_runs.csv")
    assert r.settled_range([0.9] * 99 + [0.1] * 21) == pytest.approx(0.0)        # samples from step 5000 = index 99
    assert r.settled_range([0.0] * 98 + [0.5] + [0.1] * 21) == pytest.approx(0.0)
    assert r.first_below([0.9, 0.5, 0.2], 0.3) == 150 and r.first_below([0.9], 0.3) == "never"

    def arm(final, traj_level=None, death=0.05):
        t = [traj_level if traj_level is not None else final] * 120
        return [{"seed": s, "arm": "x", "final_mean_trait": final, "success": 0, "sustained_success": 0,
                 "survival_fraction": 0.7, "traj_every_50": t, "neighbour_h_corr": [0.0] * 6,
                 **{k: death for k in r.DIAG_KEYS}} for s in c.SEEDS]
    base = {h: arm(c.DR1_RARE_REF[p] + 0.01) for h, p in c.DR1_PAIRS.items()}
    arms = {**base, "D48-local-high": arm(0.05, death=0.02), "D48-local": arm(0.05),
            "D-null-local-high": arm(0.9), "D-null-global-high": arm(0.9)}
    v = r.score(arms, tmp_path / "r1_runs.csv")
    assert v["T1"]["result"] == "supported" and v["T1"]["n_met"] == 4 and v["T2"]["result"] == "supported"
    arms["D-null-global-high"] = arm(0.4)                                        # global null fails: 2 pairs
    assert r.score(arms, tmp_path / "r1_runs.csv")["T1"]["result"] == "not supported"
    arms["D-null-global-high"] = arm(0.9)
    arms["D12-local-high"] = arm(c.DR1_RARE_REF["R12-local"] + 0.031)            # one pair outside tolerance
    v = r.score(arms, tmp_path / "r1_runs.csv")
    assert v["T1"]["n_met"] == 3 and v["T1"]["result"] == "supported"
    unsettled = arm(0.05, death=0.02)
    for row in unsettled:
        row["traj_every_50"] = [0.05] * 110 + [0.08] * 10                        # range 0.03 > 0.02 in window
    arms["D48-local-high"] = unsettled
    assert r.score(arms, tmp_path / "r1_runs.csv")["T2"]["result"] == "not settled"
    arms["D48-local-high"] = arm(0.2, death=0.02)                                 # higher h at 48: not supported
    assert r.score(arms, tmp_path / "r1_runs.csv")["T2"]["result"] == "not supported"


def test_dr1_scoring_edges(tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    import csv as _csv
    src = "ecological_models/nowak_mechanisms/kin_selection_ladder/data/r1_runs.csv"
    # settled window: step 5000 (index 99) and step 6000 (index 119) are each inside it
    t = [0.1] * 120; t[99] = 0.13
    assert r.settled_range(t) == pytest.approx(0.03)
    t = [0.1] * 120; t[98] = 0.5; t[119] = 0.13
    assert r.settled_range(t) == pytest.approx(0.03)
    assert r.first_below([0.3, 0.3, 0.29], 0.3) == 150
    # archive check: duplicate seed, non-finite value, changed mean
    rows = list(_csv.DictReader(open(src)))
    for mutate in ("dup", "nan", "shift"):
        rr = [dict(x) for x in rows]
        target = [x for x in rr if x["arm"] == "R12-local"]
        if mutate == "dup":
            target[1]["seed"] = target[0]["seed"]
        elif mutate == "nan":
            target[0]["final_mean_trait"] = "nan"
        else:
            target[0]["final_mean_trait"] = str(float(target[0]["final_mean_trait"]) + 1e-6)
        p = tmp_path / f"r1_{mutate}.csv"
        with open(p, "w", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rr)
        with pytest.raises(RuntimeError):
            r.load_r1_reference(p)
    ref = r.load_r1_reference(src)
    # paired: per-seed differences aligned by seed regardless of row order
    a_rows = [{"seed": s, "final_mean_trait": ref["R12-local"][s] + 0.01 * s} for s in reversed(c.SEEDS)]
    pr = r.paired(a_rows, ref["R12-local"])
    assert pr["per_seed_diff"] == pytest.approx([0.01 * s for s in c.SEEDS])


# ---- Step R2: care only for juvenile offspring ----

def _r2(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.r2_arms(1), **c.r2_arms(2)}[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r2_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.r2_arms(1), c.r2_arms(2)
    assert sorted(a1) == sorted(["Y6-local", "Y3-local", "Y12-local", "Y24-local", "YN6-local", "Y-below",
                                 "Y6-global", "Y12-global"])
    assert sorted(a2) == sorted(["Y2-6-local", "Y2-3-local", "Y2-12-local", "Y2-24-local", "Y2-N6-local",
                                 "Y2-below", "Y2-6-global", "Y2-12-global"])
    r1 = c.r1_arms(2)
    for arms, J, pre in ((a1, 2, "Y"), (a2, 5, "Y2-")):
        for name, (m, u) in arms.items():
            assert m["care_juvenile"] == J and m["care_lam"] == 0.5
            assert m["care"] == ("young_neighbours" if "N6" in name else "offspring")
            r1name = "R2-below" if name.endswith("below") else "R2-" + name[len(pre):]
            mr, ur = r1[r1name]
            assert u == ur                                         # same B, C, start as the R1 base arm
            assert {k: v for k, v in m.items() if k not in ("care_juvenile", "care")} == \
                {k: v for k, v in mr.items() if k != "care"}
    assert c.r2_roles(1) == ("Y6-local", "YN6-local", "Y-below", "Y6-global")
    assert c.r2_roles(2) == ("Y2-6-local", "Y2-N6-local", "Y2-below", "Y2-6-global")


def test_r2_large_j_equals_r1():
    for r2name, r1name in (("Y6-local", "R2-6-local"), ("Y6-global", "R2-6-global")):
        e = _r2(r2name, seed=12, steps=60, mech_over={"care_juvenile": 10**9})
        k = _r1(r1name, seed=12, steps=60)
        for _ in range(60):
            e.step(); k.step()
            assert np.array_equal(e.h, k.h) and np.array_equal(e.lineage, k.lineage)
            assert np.array_equal(e.ids, k.ids) and np.array_equal(e.parent_ids, k.parent_ids)


def test_r2_null_equals_k_null():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K-null"]
    m = dict(m); m.pop("exclude_focal")
    ref = make_engine(run_config(9, u, 60), **m)
    e = _r2("Y6-local", seed=9, steps=60, B_plus_scale=0.0, C_scale=0.0)
    for _ in range(60):
        ref.step(); e.step()
    assert np.array_equal(ref.h, e.h) and np.array_equal(ref.lineage, e.lineage)


def test_r2_ages_and_kernels():
    for name in ("Y6-local", "YN6-local"):
        e = _r2(name, steps=60)
        assert (e.ages == 0).all()
        for t in range(40):
            a0 = e.ages.copy()
            juv = e.ages < 2
            ps = e.parent_sites()
            e.mechanism.parent_site = ps; e.mechanism.juvenile = juv
            K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
            assert np.allclose(np.diag(K), 0.0)
            recv = K.sum(axis=0) > 0
            assert not (recv & ~juv).any()                         # only juveniles receive
            for i in range(0, e.n_sites, 7):
                if name == "Y6-local":
                    kids = np.nonzero((ps == i) & juv)[0]
                else:
                    kids = np.nonzero(e.neighbor_mask[i] & juv & (np.arange(e.n_sites) != i))[0]
                if len(kids):
                    assert np.allclose(K[i, kids], 1 / len(kids)) and np.isclose(K[i].sum(), 1.0)
                else:
                    assert np.allclose(K[i], 0.0)
            h0 = e.h.copy()
            e.step()
            s = e.last_survivors
            assert np.array_equal(e.ages[s], a0[s] + 1) and (e.ages[~s] == 0).all()
            # parents are adults (age >= 1) at the payoff computation
            assert (a0[ps[ps >= 0]] >= 1).all()
            lost = K.sum(axis=1) == 0
            assert e.last_diag["benefit_lost"] == pytest.approx(h0[lost].sum() / h0.sum())
            assert e.last_diag["juvenile_fraction"] == pytest.approx(juv.mean())
            assert e.last_diag["mean_age"] == pytest.approx(a0.mean())
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care="young_neighbours", care_lam=0.5,
                    self_in_routing=False, kin="label")
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care="neighbours", care_lam=0.5, care_juvenile=2,
                    self_in_routing=False, kin="label")


def test_r2_runner_names_and_extra_keys(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r, run_r2
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r2_arms(1)["Y6-local"]
    row = r.run_one(("Y6-local", m, u, 0, 1010))
    r2_keys = ("juvenile_offspring_mean", "juvenile_fraction", "mean_age")
    assert all(k in row for k in r2_keys) and 0 < row["juvenile_fraction"] < 1 and "S_mean" not in row
    calls = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            calls.append(sorted({j[0] for j in jobs}))
            return [{"arm": a, "seed": s, "final_mean_trait": 0.5, "success": 0, "sustained_success": 0,
                     "survival_fraction": 0.5, "traj_every_50": [0.5], "neighbour_h_corr": [0.0] * 6,
                     **{k: 0.5 for k in (*r.DIAG_KEYS, *r.EXTRA_KEYS)}} for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    run_r2.main()
    assert calls[0] == sorted(c.r2_arms(1)) and calls[1] == sorted(c.r2_arms(2))      # local failure -> attempt 2
    import json
    v = json.loads((tmp_path / "r2_verdict.json").read_text())
    assert v["attempt1"]["care_juvenile"] == 2 and v["attempt2"]["care_juvenile"] == 5 and "r2_met" in v
    assert "juvenile_fraction" in v["attempt1"]["descriptive"]["Y6-local"]


# ---- Step R3a: carry-over condition stores ----

def _r3a(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.r3a_arms(1), **c.r3a_arms(2)}[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r3a_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.r3a_arms(1), c.r3a_arms(2)
    assert sorted(a1) == sorted(["E6-local", "E3-local", "E12-local", "E24-local", "EN6-local", "E-below",
                                 "E6-global", "E12-global"])
    assert sorted(a2) == sorted(["E2-6-local", "E2-3-local", "E2-12-local", "E2-24-local", "E2-N6-local",
                                 "E2-below", "E2-6-global", "E2-12-global"])
    r2 = c.r2_arms(1)
    for arms, rho, pre in ((a1, 0.8, "E"), (a2, 0.4, "E2-")):
        for name, (m, u) in arms.items():
            r2name = "Y-below" if name.endswith("below") else "Y" + name[len(pre):]
            mr, ur = r2[r2name]
            assert u == ur and m == {**mr, "care_rho": rho}
    assert c.r3a_roles(1) == ("E6-local", "EN6-local", "E-below", "E6-global")
    assert c.r3a_roles(2) == ("E2-6-local", "E2-N6-local", "E2-below", "E2-6-global")


def test_r3a_rho0_equals_r2():
    for e_name, y_name in (("E6-local", "Y6-local"), ("E6-global", "Y6-global"), ("EN6-local", "YN6-local")):
        e = _r3a(e_name, seed=13, steps=60, mech_over={"care_rho": 0.0})
        y = _r2(y_name, seed=13, steps=60)
        for _ in range(60):
            e.step(); y.step()
            assert np.array_equal(e.h, y.h) and np.array_equal(e.lineage, y.lineage)
            assert np.array_equal(e.ids, y.ids) and np.array_equal(e.ages, y.ages)


def test_r3a_null_equals_k_null():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K-null"]
    m = dict(m); m.pop("exclude_focal")
    ref = make_engine(run_config(9, u, 60), **m)
    e = _r3a("E6-local", seed=9, steps=60, B_plus_scale=0.0, C_scale=0.0)
    for _ in range(60):
        ref.step(); e.step()
    assert np.array_equal(ref.h, e.h) and np.array_equal(ref.lineage, e.lineage)


def test_r3a_stores_death_and_births(monkeypatch):
    import moran_models.interaction_kernel.core.engine as eng_mod
    e = _r3a("E6-local", steps=60)
    for _ in range(30):
        e.step()
    for _ in range(5):
        S0, D0, h0 = e.S.copy(), e.D.copy(), e.h.copy()
        juv = e.ages < 2
        ps = e.parent_sites()
        e.mechanism.parent_site = ps; e.mechanism.juvenile = juv
        K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
        R = K.T @ (1.2 * h0)
        S1, D1 = 0.8 * S0 + R, 0.8 * D0 + 0.2 * h0
        seen = {}
        orig = eng_mod.local_replacement_step

        def spy(trait, lineage, fitness, *a):
            seen["W"] = fitness.copy()
            return orig(trait, lineage, fitness, *a)
        monkeypatch.setattr(eng_mod, "local_replacement_step", spy)
        e.step()
        monkeypatch.setattr(eng_mod, "local_replacement_step", orig)
        assert np.allclose(seen["W"], 1 + 0.5 * S1 - D1)
        assert e.mechanism.birth_override is None
        s = e.last_survivors
        assert np.allclose(e.S[s], S1[s]) and np.allclose(e.D[s], D1[s])
        assert (e.S[~s] == 0).all() and (e.D[~s] == 0).all()
        assert e.last_diag["death_mean"] == pytest.approx((0.5 * np.exp(-0.5 * S1 / 0.12)).mean())
        assert e.last_diag["S_mean"] == pytest.approx(S1.mean()) and e.last_diag["D_mean"] == pytest.approx(D1.mean())
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care="offspring", care_lam=0.5, care_rho=0.5,
                    self_in_routing=False, kin="label")


def test_r3a_runner(monkeypatch, tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r, run_r3a
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r3a_arms(1)["E6-local"]
    row = r.run_one(("E6-local", m, u, 0, 1010))
    r3a_keys = r.EXTRA_KEYS[:r.EXTRA_KEYS.index("births_per_occupant")]
    assert all(k in row for k in r3a_keys) and "births_per_occupant" not in row
    calls = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            calls.append(sorted({j[0] for j in jobs}))
            return [{"arm": a, "seed": s, "final_mean_trait": 0.9, "success": 1, "sustained_success": 1,
                     "survival_fraction": 0.5, "traj_every_50": [0.9], "neighbour_h_corr": [0.0] * 6,
                     **{k: 0.5 for k in (*r.DIAG_KEYS, *r.EXTRA_KEYS)}} for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(r, "classify_r1", lambda *a: {"met": True, "class": "met"})
    run_r3a.main()
    assert calls == [sorted(c.r3a_arms(1))]
    assert (tmp_path / "r3a_verdict.json").exists()


# ---- Step R3b: a realized birth costs the surviving parent condition ----

def _r3b(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.r3b_arms(1), **c.r3b_arms(2)}[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r3b_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.r3b_arms(1), c.r3b_arms(2)
    assert sorted(a1) == sorted(["Q6-local", "Q3-local", "Q12-local", "Q24-local", "QN6-local", "Q-below",
                                 "Q6-global", "Q12-global"])
    assert sorted(a2) == sorted(["Q2-6-local", "Q2-3-local", "Q2-12-local", "Q2-24-local", "Q2-N6-local",
                                 "Q2-below", "Q2-6-global", "Q2-12-global"])
    e = c.r3a_arms(1)
    for arms, cb, pre in ((a1, 0.5, "Q"), (a2, 0.2, "Q2-")):
        for name, (m, u) in arms.items():
            ename = "E-below" if name.endswith("below") else "E" + name[len(pre):]
            me, ue = e[ename]
            assert u == ue and m == {**me, "care_birth_cost": cb} and m["care_rho"] == 0.8
    assert c.r3b_roles(1) == ("Q6-local", "QN6-local", "Q-below", "Q6-global")
    assert c.r3b_roles(2) == ("Q2-6-local", "Q2-N6-local", "Q2-below", "Q2-6-global")
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care="offspring", care_lam=0.5, care_juvenile=2,
                    care_birth_cost=0.5, self_in_routing=False, kin="label")      # needs care_rho
    with pytest.raises(ValueError):
        _r3b("Q6-local", mech_over={"care_birth_cost": -0.1})


def test_r3b_cb0_equals_r3a():
    for q_name, e_name in (("Q6-local", "E6-local"), ("Q6-global", "E6-global"), ("QN6-local", "EN6-local")):
        q = _r3b(q_name, seed=13, steps=80, mech_over={"care_birth_cost": 0.0})
        e = _r3a(e_name, seed=13, steps=80)
        for _ in range(80):
            q.step(); e.step()
            for f in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D"):
                assert np.array_equal(getattr(q, f), getattr(e, f)), f


def test_r3b_null_equals_k_null():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K-null"]
    m = dict(m); m.pop("exclude_focal")
    ref = make_engine(run_config(9, u, 60), **m)
    e = _r3b("Q6-local", seed=9, steps=60, mech_over={"care_birth_cost": 0.0}, B_plus_scale=0.0, C_scale=0.0)
    for _ in range(60):
        ref.step(); e.step()
    assert np.array_equal(ref.h, e.h) and np.array_equal(ref.lineage, e.lineage)


def test_r3b_charge_forced_outcomes():
    e = _r3b("Q6-local")
    n = e.n_sites
    survive = np.ones(n, dtype=bool)
    survive[[10, 11, 20, 21]] = False                 # dead (newborn) sites
    survive[5] = False                                # parent 5 dies this step
    lp = np.arange(n)                                 # default: each site's winner is itself
    lp[[10, 11]] = 3                                  # surviving parent 3: two realized births
    lp[[20, 21]] = 5                                  # dead parent 5 wins another site...
    lp[5] = 5                                         # ...and its own site
    lp[7] = 3                                         # a win at a surviving site: discarded
    e.D[:] = 0.1; e.Db[:] = 0.0
    k = e.charge_births(survive, lp)
    assert k[3] == 2 and k[5] == 0 and k.sum() == 2
    assert e.D[3] == pytest.approx(0.1 + 2 * 0.5) and np.allclose(np.delete(e.D, 3), 0.1)
    assert e.Db[3] == pytest.approx(1.0) and np.allclose(np.delete(e.Db, 3), 0.0)


def test_r3b_step_charges_and_next_lottery(monkeypatch):
    import moran_models.interaction_kernel.core.engine as eng_mod
    import copy
    q = _r3b("Q6-local", seed=4, steps=60)
    for _ in range(25):
        q.step()
    z = copy.deepcopy(q)                       # identical state and RNG streams, then compare with and without cost
    z.birth_cost = 0.0
    seen = {}
    orig = eng_mod.local_replacement_step

    def spy(trait, lineage, fitness, *a):
        seen.setdefault("W", []).append(fitness.copy())
        return orig(trait, lineage, fitness, *a)
    monkeypatch.setattr(eng_mod, "local_replacement_step", spy)
    q.step(); z.step()
    assert np.array_equal(seen["W"][0], seen["W"][1])            # this step's lottery unchanged by the charge
    assert np.array_equal(q.h, z.h) and np.array_equal(q.parent_ids, z.parent_ids)
    s = q.last_survivors
    dead = ~s
    k = np.where(s, np.bincount(q.mechanism.last_parents[dead], minlength=q.n_sites), 0)
    assert np.allclose(q.D, z.D + 0.5 * k) and k.sum() > 0
    assert (q.D[dead] == 0).all() and (q.S[dead] == 0).all()   # newborns start at 0
    assert q.last_diag["births_per_occupant"] == pytest.approx(dead.mean())
    assert q.last_diag["frac_births_charged"] == pytest.approx(k.sum() / dead.sum())
    charged = k > 0
    seen.clear()
    Dq, Dz = q.D.copy(), z.D.copy()
    q.step(); z.step()
    # next lottery: depletion differs by exactly rho * k * c_b
    Wq, Wz = seen["W"]
    assert np.allclose(Wz - Wq, 0.8 * 0.5 * k)
    assert q.last_diag["D_recent_parents"] == pytest.approx(q.last_payoff_D[charged].mean())
    monkeypatch.setattr(eng_mod, "local_replacement_step", orig)


def test_r3b_death_site_by_site(monkeypatch):
    e = _r3b("Q6-local", seed=2, steps=10, B_plus_scale=0.0, C_scale=0.0)
    rng = np.random.default_rng(0)
    e.S = rng.uniform(0, 1, e.n_sites)
    u = rng.uniform(0, 1, e.n_sites)
    S1 = 0.8 * e.S                                                # R = 0 with B = 0
    d = 0.5 * np.exp(-0.5 * S1 / 0.12)
    class FixedDraws:
        def random(self, n):
            return u.copy()
    e.death_rng = FixedDraws()
    e.step()
    assert np.array_equal(e.last_survivors, u >= d)


def test_r2_finite_j_step_donor_age_and_founders():
    # R2 review gap: call step() without pre-setting the juvenile mask; rho = 0 so S after the step is R exactly.
    for name in ("E6-local", "EN6-local"):
        e = _r3a(name, seed=3, steps=60, mech_over={"care_rho": 0.0})
        saw_age1_donor = saw_age2_kid = False
        for t in range(40):
            ages, h, ids, pids = e.ages.copy(), e.h.copy(), e.ids.copy(), e.parent_ids.copy()
            juv = ages < 2
            n = e.n_sites
            site_of = {int(i): s for s, i in enumerate(ids)}
            R = np.zeros(n)
            for i in range(n):
                if name == "E6-local":
                    kids = [j for j in range(n) if pids[j] == ids[i] and juv[j]]
                else:
                    kids = [j for j in np.nonzero(e.neighbor_mask[i])[0] if j != i and juv[j]]
                for j in kids:
                    R[j] += 1.2 * h[i] / len(kids)
                if name == "E6-local" and kids and ages[i] == 1:
                    saw_age1_donor = True
            if name == "E6-local":
                old = [j for j in range(n) if pids[j] in site_of and ages[j] == 2]
                if old:
                    saw_age2_kid = True
                    assert np.allclose(R[old], 0.0)
            if name == "EN6-local" and t == 0:
                assert juv.all() and (pids < 0).all()        # founders count as juvenile neighbours
                assert (R > 0).sum() > 0.9 * n
            e.step()
            s = e.last_survivors
            assert np.allclose(e.S[s], R[s])
        if name == "E6-local":
            assert saw_age1_donor and saw_age2_kid


def test_h2_uniform_field_is_undefined_and_json_null(tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.analysis import neighbour_correlation
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_steps01 import edge_pairs
    e = _r3b("Q6-global")
    ei, ej = edge_pairs(e)
    assert np.isnan(neighbour_correlation(np.full(e.n_sites, 0.7), ei, ej))
    assert np.isnan(neighbour_correlation(np.full(e.n_sites, 0.1), ei, ej))
    assert np.isfinite(neighbour_correlation(np.random.default_rng(0).uniform(0, 1, e.n_sites), ei, ej))
    rows = [{"seed": s, "success": 1, "final_mean_trait": 0.9, "neighbour_h_corr": [0.0] * 6} for s in range(20)]
    rows[3]["neighbour_h_corr"][2] = float("nan")              # one undefined sample among 119 near-zero ones
    h2 = r.score_h2(rows)
    assert h2["result"] == "not interpretable"
    out = json.loads(json.dumps(r.json_safe(h2), allow_nan=False))
    assert out["per_seed_corr"]["3"][2] is None and out["neighbour_corr"] is None


def test_r3b_global_step_charges_and_db_timing():
    import copy
    q = _r3b("Q6-global", seed=6, steps=60)
    for _ in range(25):
        q.step()
    z = copy.deepcopy(q); z.birth_cost = 0.0
    old_ids = q.ids.copy()
    db0 = q.Db.copy()
    q.step(); z.step()
    assert np.array_equal(q.h, z.h) and np.array_equal(q.parent_ids, z.parent_ids)
    s = q.last_survivors; dead = ~s
    lp = q.mechanism.last_parents
    assert np.array_equal(q.parent_ids[dead], old_ids[lp[dead]])     # parent ids are the winners' old ids
    k = np.where(s, np.bincount(lp[dead], minlength=q.n_sites), 0)
    assert k.sum() > 0 and np.allclose(q.D, z.D + 0.5 * k)
    assert (q.D[dead] == 0).all() and (q.S[dead] == 0).all()
    assert q.last_diag["Db_mean"] == pytest.approx((0.8 * db0).mean())  # decayed, before this step's charges
    expect = np.where(dead, 0.0, 0.8 * db0) + 0.5 * k
    assert np.allclose(q.Db, expect)


# ---- Step R3c: breeding threshold, sites can stay empty ----

def _r3c(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.r3c_arms(1), **c.r3c_arms(2)}[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


class _Draws:
    def __init__(self, u):
        self.u = np.asarray(u, dtype=float)

    def random(self, n):
        return self.u.copy()


def test_r3c_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.r3c_arms(1), c.r3c_arms(2)
    assert sorted(a1) == sorted(["V6-local", "V3-local", "V12-local", "V24-local", "VN6-local", "V-below",
                                 "V6-global", "V12-global"])
    assert sorted(a2) == sorted(["V2-6-local", "V2-3-local", "V2-12-local", "V2-24-local", "V2-N6-local",
                                 "V2-below", "V2-6-global", "V2-12-global"])
    q = c.r3b_arms(1)
    for arms, th, pre in ((a1, 0.25, "V"), (a2, 0.0, "V2-")):
        for name, (m, u) in arms.items():
            qname = "Q-below" if name.endswith("below") else "Q" + name[len(pre):]
            mq, uq = q[qname]
            assert u == uq and m == {**mq, "care_theta": th} and m["care_birth_cost"] == 0.5
    assert c.r3c_roles(1) == ("V6-local", "VN6-local", "V-below", "V6-global")
    assert c.r3c_roles(2) == ("V2-6-local", "V2-N6-local", "V2-below", "V2-6-global")
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care="offspring", care_lam=0.5, care_juvenile=2,
                    care_rho=0.8, care_theta=0.25, self_in_routing=False, kin="label")   # needs care_birth_cost


def test_r3c_theta_minus_inf_equals_r3b():
    for v_name, q_name in (("V6-local", "Q6-local"), ("V6-global", "Q6-global"), ("VN6-local", "QN6-local")):
        v = _r3c(v_name, seed=13, steps=80, mech_over={"care_theta": -np.inf})
        q = _r3b(q_name, seed=13, steps=80)
        for _ in range(80):
            v.step(); q.step()
            for f in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D", "Db"):
                assert np.array_equal(getattr(v, f), getattr(q, f)), f
            assert v.occ.all()
            for k in ("death_mean", "benefit_lost", "S_mean", "D_parents", "births_per_occupant", "Db_mean"):
                assert v.last_diag[k] == pytest.approx(q.last_diag[k], nan_ok=True), k
        assert v.rng.bit_generator.state == q.rng.bit_generator.state
        assert v.death_rng.bit_generator.state == q.death_rng.bit_generator.state


def test_r3c_null_equals_k_null():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K-null"]
    m = dict(m); m.pop("exclude_focal")
    ref = make_engine(run_config(9, u, 60), **m)
    e = _r3c("V6-local", seed=9, steps=60, mech_over={"care_theta": -np.inf, "care_birth_cost": 0.0},
             B_plus_scale=0.0, C_scale=0.0)
    for _ in range(60):
        ref.step(); e.step()
    assert np.array_equal(ref.h, e.h) and np.array_equal(ref.lineage, e.lineage)


def test_r3c_eligibility_and_restricted_softmax():
    e = _r3c("V6-local")
    W = np.full(e.n_sites, 0.25)
    W[3] = 0.25 - 1e-12
    el = e.eligible_mask(W)
    assert el[0] and not el[3]                                   # W exactly theta is eligible
    e.occ[5] = False
    assert not e.eligible_mask(W)[5]                             # empty sites are never eligible
    w = np.array([1.0, 0.4, 0.9, 0.2, 0.7])
    m = np.array([True, False, True, False, True])
    p = e.pool_probs(w, m, 0.12)
    ex = np.exp(w[m] / 0.12); ex /= ex.sum()
    assert np.allclose(p[m], ex) and (p[~m] == 0).all()
    from moran_models.interaction_kernel.core.selection import _local_softmax_probabilities as sm
    assert np.array_equal(e.pool_probs(w, np.ones(5, bool), 0.12), sm(w, 0.12))
    assert np.array_equal(e.pool_probs(w, np.zeros(5, bool), 0.12), sm(w, 0.12))


def _forced(seed=5, warm=30):
    e = _r3c("V6-local", seed=seed, steps=200)
    for _ in range(warm):
        e.step()
    return e


def _pool(e, i):
    return [int(j) for j in e.neighbor_indices[i]]


def test_r3c_forced_vacancy_ineligible_helpers_and_streams():
    import copy
    e = _forced()
    n = e.n_sites
    i = 40
    pool = _pool(e, i)
    e.D[pool] = 5.0                                              # everyone in site i's pool ineligible
    u = np.ones(n); u[i] = 0.0                                   # only site i's occupant dies
    e.death_rng = _Draws(u)
    ref = copy.deepcopy(e); ref.theta = -np.inf
    juv = (e.ages < 2) & e.occ
    ps = e.parent_sites()
    e.mechanism.juvenile = juv; e.mechanism.parent_site = ps
    K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
    R = K.T @ (1.2 * e.h)
    S0, D0, h0 = e.S.copy(), e.D.copy(), e.h.copy()
    e.step(); ref.step()
    assert not e.occ[i] and e.h[i] == 0 and e.ids[i] == -1 and e.parent_ids[i] == -1
    assert e.S[i] == 0 and e.D[i] == 0 and e.Db[i] == 0 and e.ages[i] == 0
    others = [j for j in pool if j != i]
    # ineligible survivors still helped (their care is in R) and paid
    assert np.allclose(e.S[others], 0.8 * S0[others] + R[others])
    assert np.allclose(e.D[others], 0.8 * D0[others] + 0.2 * h0[others])
    assert e.last_diag["frac_fill_emptied"] == 1.0 and e.last_diag["frac_fill_trimmed"] == 1.0
    # random streams identical to the same step at theta = -inf
    assert e.rng.bit_generator.state == ref.rng.bit_generator.state
    # the empty site: next step it does not help, receive, breed or die; it refills when eligible
    e.death_rng = _Draws(np.ones(n))
    e.D[pool] = 5.0
    e.mechanism.juvenile = (e.ages < 2) & e.occ; e.mechanism.parent_site = e.parent_sites()
    K2 = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
    assert (K2[:, i] == 0).all()                                 # receives no care
    e.step()
    assert not e.occ[i] and e.S[i] == 0
    q = others[0]                                                # a survivor becomes eligible: it fills the vacancy
    e.D[others] = 5.0
    e.D[q] = 0.0
    e.S[q] = 0.0
    hq = e.h[q]
    e.death_rng = _Draws(np.ones(n))
    need_before = ~e.occ
    e.step()
    assert e.occ[i] and e.parent_ids[i] == e.ids[q] and e.ages[i] == 0 and e.S[i] == 0 and e.D[i] == 0
    k = int(sum(1 for j in np.nonzero(need_before)[0] if e.occ[j] and e.parent_ids[j] == e.ids[q]))
    assert k >= 1 and e.D[q] == pytest.approx(0.2 * hq + 0.5 * k)  # pays only for realized births


def test_r3c_dying_parent_wins_two_sites():
    e = _forced(seed=6)
    n = e.n_sites
    p = 60
    j = [x for x in _pool(e, p) if x != p][0]
    sites = set(_pool(e, p)) | set(_pool(e, j))
    for x in sites:
        e.D[x] = 5.0
    e.D[p] = 0.0; e.S[p] = 1.0
    u = np.ones(n); u[[p, j]] = 0.0                              # p and j die; p is the only eligible candidate
    e.death_rng = _Draws(u)
    pid = e.ids[p]
    e.step()
    for x in (p, j):
        assert e.occ[x] and e.parent_ids[x] == pid and e.S[x] == 0 and e.D[x] == 0
    assert e.last_diag["frac_births_charged"] == 0.0              # the parent died: nobody paid


def test_r3c_random_steps_invariants():
    e = _r3c("V6-local", seed=3, steps=400, mech_over={"care_theta": 0.6})   # a strong threshold: many vacancies
    saw_vac = False
    for _ in range(300):
        occ0 = e.occ.copy()
        ids0 = e.ids.copy()
        e.step()
        saw_vac |= not e.occ.all()
        assert (e.h[~e.occ] == 0).all() and (e.ids[~e.occ] == -1).all() and (e.S[~e.occ] == 0).all()
        new = e.occ & ~np.isin(e.ids, ids0)
        # newborns' parents were start-of-step occupants (a newborn cannot breed in its birth step)
        assert np.isin(e.parent_ids[new], ids0[occ0]).all()
    assert saw_vac
    assert e.occupied_mean_h() == pytest.approx(e.h[e.occ].mean())


def test_r3c_global_excludes_empty_candidates():
    e = _r3c("V6-global", seed=4, steps=100, mech_over={"care_theta": 0.6})
    for _ in range(60):
        occ0 = e.occ.copy()
        ids0 = e.ids.copy()
        e.step()
        new = e.occ & ~np.isin(e.ids, ids0)
        assert np.isin(e.parent_ids[new], ids0[occ0]).all()


def test_r3c_extinction_and_joint_success():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    e = _r3c("V6-local")
    e.occ[:] = False; e.h[:] = 0; e.ids[:] = -1; e.parent_ids[:] = -1
    e.step()
    assert not e.occ.any() and np.isnan(e.occupied_mean_h())
    assert not r.joint_success(float("nan"), 0.0)
    assert not r.joint_success(0.9, 0.49) and r.joint_success(0.9, 0.5) and not r.joint_success(0.59, 1.0)
    assert r.joint_success(0.6) and not r.joint_success(float("nan"))


def test_r3c_runner(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r, run_r3c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r3c_arms(1)["V6-local"]
    row = r.run_one(("V6-local", m, u, 0, 1010))
    r3c_keys = r.EXTRA_KEYS[:r.EXTRA_KEYS.index("starve_added_per_occ")]
    assert all(k in row for k in r3c_keys) and 0 < row["final_occupancy"] <= 1 and row["extinct"] == 0
    assert "starve_added_total" not in row
    calls = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            calls.append(sorted({j[0] for j in jobs}))
            return [{"arm": a, "seed": s, "final_mean_trait": 0.5, "success": 0, "sustained_success": 0,
                     "survival_fraction": 0.5, "traj_every_50": [0.5], "neighbour_h_corr": [0.0] * 6,
                     "final_occupancy": 0.9, "extinct": 0, "occupancy_last1000": 0.9, "occ_every_50": [0.9],
                     **{k: 0.5 for k in (*r.DIAG_KEYS, *r.EXTRA_KEYS)}} for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    run_r3c.main()
    assert calls == [sorted(c.r3c_arms(1)), sorted(c.r3c_arms(2))]          # local failure -> attempt 2
    v = json.loads((tmp_path / "r3c_verdict.json").read_text())
    assert v["attempt1"]["care_theta"] == 0.25 and v["attempt2"]["care_theta"] == 0.0
    assert v["attempt1"]["descriptive"]["V6-local"]["extinctions"] == 0


def test_r3c_streams_all_masked_and_single_eligible():
    import copy
    for th in (10.0, None):                                       # 10: every pool all-masked; None: one eligible
        e = _forced(seed=7)
        if th is None:
            i = 33
            pool = _pool(e, i)
            e.D[:] = 0.0
            e.D[pool] = 5.0
            e.D[pool[0]] = 0.0; e.S[pool[0]] = 0.0               # a single eligible candidate in site i's pool
            e.theta = 0.25
        else:
            e.theta = th
        ref = copy.deepcopy(e); ref.theta = -np.inf
        e.step(); ref.step()
        for g in ("rng", "death_rng"):
            assert getattr(e, g).bit_generator.state == getattr(ref, g).bit_generator.state, g
        assert np.array_equal(e.last_survivors, ref.last_survivors)
        if th is not None:
            assert e.last_diag["frac_fill_emptied"] == 1.0
        else:
            assert e.last_diag["frac_fill_trimmed"] > 0


def test_r3c_global_mixed_pools_and_streams():
    import copy
    e = _r3c("V6-global", seed=4, steps=200, mech_over={"care_theta": 0.6})
    mixed = False
    for t in range(80):
        ref = copy.deepcopy(e); ref.theta = -np.inf
        occ0, ids0 = e.occ.copy(), e.ids.copy()
        e.step(); ref.step()
        for g in ("rng", "death_rng", "global_rng"):
            assert getattr(e, g).bit_generator.state == getattr(ref, g).bit_generator.state, g
        new = e.occ & ~np.isin(e.ids, ids0)
        lp = e.mechanism.last_parents
        filled = np.nonzero(new)[0]
        assert e.last_eligible[lp[filled]].all() and occ0[lp[filled]].all()
        if 0 < e.last_diag["frac_fill_trimmed"] and len(filled):
            mixed = True
    assert mixed


def test_r3c_young_neighbour_care_around_vacancy():
    e = _r3c("VN6-local", seed=2, steps=60)
    for _ in range(5):
        e.step()
    i = 50
    e.occ[i] = False; e.h[i] = 0; e.ids[i] = -1; e.parent_ids[i] = -1; e.ages[i] = 0
    juv = (e.ages < 2) & e.occ
    e.mechanism.juvenile = juv
    K = e.mechanism.build_positive_kernel(e.neighbor_mask, e.lineage, e.extra_state, e.cfg)
    assert (K[:, i] == 0).all()
    for d in [j for j in _pool(e, i) if j != i]:
        kids = [j for j in np.nonzero(e.neighbor_mask[d])[0] if j != d and juv[j]]
        if kids:
            assert np.allclose(K[d, kids], 1 / len(kids)) and np.isclose(K[d].sum(), 1.0)


def test_r3c_occupied_edge_correlation():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.analysis import neighbour_correlation
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_steps01 import edge_pairs
    e = _r3c("V6-local")
    ei, ej = edge_pairs(e)
    e.h = np.random.default_rng(1).uniform(0, 1, e.n_sites)
    e.occ[::3] = False
    both = e.occ[ei] & e.occ[ej]
    assert r.occupied_corr(e, ei, ej) == pytest.approx(neighbour_correlation(e.h, ei[both], ej[both]))
    assert r.occupied_corr(e, ei, ej) != pytest.approx(neighbour_correlation(e.h, ei, ej))
    e.occ[:] = False
    assert np.isnan(r.occupied_corr(e, ei, ej))



# ---- Step R3d: starvation below sigma ----

def _r3d(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.r3d_arms(1), **c.r3d_arms(2)}[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r3d_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.r3d_arms(1), c.r3d_arms(2)
    assert sorted(a1) == sorted(["F6-local", "F3-local", "F12-local", "F24-local", "FN6-local", "F-below",
                                 "F6-global", "F12-global"])
    assert sorted(a2) == sorted(["F2-6-local", "F2-3-local", "F2-12-local", "F2-24-local", "F2-N6-local",
                                 "F2-below", "F2-6-global", "F2-12-global"])
    v = c.r3c_arms(1)
    for arms, sg, pre in ((a1, 0.0, "F"), (a2, -0.1, "F2-")):
        for name, (m, u) in arms.items():
            vname = "V-below" if name.endswith("below") else "V" + name[len(pre):]
            mv, uv = v[vname]
            assert u == uv and m == {**mv, "care_sigma": sg} and m["care_theta"] == 0.25
    assert c.r3d_roles(1) == ("F6-local", "FN6-local", "F-below", "F6-global")
    assert c.r3d_roles(2) == ("F2-6-local", "F2-N6-local", "F2-below", "F2-6-global")
    with pytest.raises(ValueError):
        _r3d("F6-local", mech_over={"care_sigma": 0.5})                       # sigma must be <= theta
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care="offspring", care_lam=0.5, care_juvenile=2,
                    care_rho=0.8, care_birth_cost=0.5, care_sigma=0.0, self_in_routing=False, kin="label")


def test_r3d_sigma_minus_inf_equals_r3c():
    for f_name, v_name in (("F6-local", "V6-local"), ("F6-global", "V6-global"), ("FN6-local", "VN6-local")):
        f = _r3d(f_name, seed=13, steps=80, mech_over={"care_sigma": -np.inf})
        v = _r3c(v_name, seed=13, steps=80)
        for _ in range(80):
            f.step(); v.step()
            for x in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D", "Db", "occ"):
                assert np.array_equal(getattr(f, x), getattr(v, x)), x
            assert f.last_diag["n_starve_added"] == 0
        for g in ("rng", "death_rng", "global_rng"):
            assert getattr(f, g).bit_generator.state == getattr(v, g).bit_generator.state, g


def test_r3d_null_equals_k_null():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K-null"]
    m = dict(m); m.pop("exclude_focal")
    ref = make_engine(run_config(9, u, 60), **m)
    e = _r3d("F6-local", seed=9, steps=60, mech_over={"care_sigma": -np.inf, "care_theta": -np.inf,
                                                       "care_birth_cost": 0.0}, B_plus_scale=0.0, C_scale=0.0)
    for _ in range(60):
        ref.step(); e.step()
    assert np.array_equal(ref.h, e.h) and np.array_equal(ref.lineage, e.lineage)


def test_r3d_survival_mask_cutoff():
    e = _r3d("F6-local")
    n = e.n_sites
    W = np.full(n, 0.5); W[0] = -1e-12; W[1] = 0.0; W[2] = -2.0
    u = np.ones(n); u[3] = 0.0
    d = np.full(n, 0.5)
    occ = np.ones(n, bool); occ[2] = False
    s = e.survival_mask(u, d, W, occ)
    assert not s[0] and s[1] and not s[2] and not s[3] and s[4:].all()   # W < sigma starves; W == sigma does not
    starve, added, base_dead = e._starve
    assert starve[0] and not starve[1] and not starve[2] and added[0] and added.sum() == 1


def test_r3d_forced_starving_never_parent_and_streams():
    import copy
    e = _r3d("F6-local", seed=5, steps=200)
    for _ in range(30):
        e.step()
    n = e.n_sites
    i = 40
    pool = [int(j) for j in e.neighbor_indices[i]]
    a, b = [j for j in pool if j != i][:2]
    W = np.full(n, 0.5)
    W[pool] = 0.1                                             # ineligible, not starving
    W[a] = -1.0                                               # starving
    W[b] = 1.0                                                # eligible, dies by its base draw
    u = np.ones(n); u[[i, b]] = 0.0
    e.death_rng = _Draws(u)
    e.condition_score = lambda: W.copy()
    ref = copy.deepcopy(e); ref.sigma = -np.inf
    ida, idb = e.ids[a], e.ids[b]
    e.step(); ref.step()
    assert not e.last_survivors[a] and not e.last_survivors[b] and not e.last_survivors[i]
    assert e.occ[i] and e.parent_ids[i] == idb                  # the base-dead eligible occupant bred
    new = e.occ & (e.ages == 0)
    assert not (e.parent_ids[new] == ida).any()                 # the starving occupant parented nothing
    assert e.last_diag["n_starve_added"] == 1 and e.last_starved[a] and e.last_starved.sum() == 1
    assert e.rng.bit_generator.state == ref.rng.bit_generator.state
    assert ref.last_survivors[a]                                # without starvation it would have survived


def test_r3d_natural_starvation_needs_a_birth():
    # screen: from W >= 0, at sigma = 0 an occupant can starve only if it was charged for a birth the step before
    e = _r3d("F6-local", seed=3, steps=3000)
    starved_total = 0
    W_prev = None
    for t in range(2500):
        charged_prev = e.last_charged.copy()
        occ0 = e.occ.copy()
        e.step()
        st = e.last_starved
        assert (e.last_W[st] < 0).all()
        if W_prev is not None:
            ok = occ0 & (W_prev >= 0) & st
            assert charged_prev[ok].all()
        starved_total += int(st.sum())
        W_prev = e.last_W.copy()
        W_prev[~e.occ] = np.nan
        # survivors keep their W only if they stay on their site; newborns have no previous W
        W_prev = np.where(e.ages == 0, np.nan, W_prev)
    assert starved_total > 0
    if e.last_diag["n_deaths"]:
        assert e.last_diag["starve_added_share"] == pytest.approx(e.last_diag["n_starve_added"] / e.last_diag["n_deaths"])


def test_r3d_runner(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r, run_r3d
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r3d_arms(1)["F6-local"]
    row = r.run_one(("F6-local", m, u, 0, 1010))
    r3d_keys = r.EXTRA_KEYS[:r.EXTRA_KEYS.index("harvest_mean")]
    assert all(k in row for k in r3d_keys) and row["deaths_total"] > 0 and row["starve_added_total"] >= 0
    calls = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            calls.append(sorted({j[0] for j in jobs}))
            return [{"arm": a, "seed": s, "final_mean_trait": 0.5, "success": 0, "sustained_success": 0,
                     "survival_fraction": 0.5, "traj_every_50": [0.5], "neighbour_h_corr": [0.0] * 6,
                     "final_occupancy": 0.9, "extinct": 0, "occupancy_last1000": 0.9, "occ_every_50": [0.9],
                     "starve_added_total": 1, "deaths_total": 200,
                     **{k: 0.5 for k in (*r.DIAG_KEYS, *r.EXTRA_KEYS)}} for a, _, _, s, n in jobs]

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    run_r3d.main()
    assert calls == [sorted(c.r3d_arms(1)), sorted(c.r3d_arms(2))]
    v = json.loads((tmp_path / "r3d_verdict.json").read_text())
    assert v["attempt1"]["care_sigma"] == 0.0 and v["attempt2"]["care_sigma"] == -0.1
    assert v["attempt1"]["starvation_activation"] == pytest.approx(0.005)
    assert v["attempt1"]["starvation_active"] is False


def test_r3d_forced_counts_rates_refill_and_vacancy():
    e = _r3d("F6-local", seed=11, steps=200)
    for _ in range(30):
        e.step()
    n = e.n_sites
    v = 70
    e.occ[v] = False; e.h[v] = 0; e.ids[v] = -1; e.parent_ids[v] = -1; e.ages[v] = 0
    e.S[v] = e.D[v] = e.Db[v] = 0
    pool_x = [int(j) for j in e.neighbor_indices[10]]
    pool_y = [int(j) for j in e.neighbor_indices[200]]
    assert not set(pool_x) & set(pool_y) and v not in pool_x + pool_y
    x, y = 10, 200
    e.h[x], e.h[y] = 0.8, 0.2                                    # one starver on each side of h = 0.5
    W = np.full(n, 0.5)
    W[v] = 0.0
    W[[j for j in pool_y if j != y]] = 0.1                       # y's pool has no eligible candidate
    W[x] = -1.0                                                  # added starvation death (draw says survive)
    W[y] = -1.0                                                  # below cutoff and dies by its draw anyway
    u = np.ones(n); u[y] = 0.0
    e.death_rng = _Draws(u)
    e.condition_score = lambda: W.copy()
    occ0, h0 = e.occ.copy(), e.h.copy()
    e.step()
    nocc = int(occ0.sum())
    dg = e.last_diag
    assert dg["n_starve_added"] == 1 and dg["n_deaths"] == 2
    assert dg["starve_added_share"] == pytest.approx(0.5)
    assert dg["starve_all_per_occ"] == pytest.approx(2 / nocc) and dg["starve_added_per_occ"] == pytest.approx(1 / nocc)
    assert e.occ[x] and not e.occ[y]                             # x refilled by an eligible neighbour; y stays empty
    assert dg["starve_rate_high_h"] == pytest.approx(1 / int((occ0 & (h0 >= 0.5)).sum()))
    assert dg["starve_rate_low_h"] == pytest.approx(1 / int((occ0 & (h0 < 0.5)).sum()))


def test_r3d_birth_charge_crosses_cutoff_next_step():
    e = _r3d("F6-local", seed=12, steps=200)
    for _ in range(30):
        e.step()
    n = e.n_sites
    adults = np.nonzero(e.occ & (e.ages >= 3))[0]
    p = None
    for cand in adults:
        if not (e.parent_ids == e.ids[cand]).any():              # no living offspring: no care to give or get
            j = [int(x) for x in e.neighbor_indices[cand] if x != cand][0]
            if e.occ[j] and not ((e.parent_ids == e.ids[j]) & (e.ages < 3)).any():
                p = int(cand); break
    assert p is not None
    e.h[p] = 0.9; e.S[p] = 0.0
    e.D[p] = (0.7 - 0.2 * 0.9) / 0.8                             # real W_p at payoff = 0.3 (eligible, not starving)
    real = e.condition_score
    pool_j = [int(x) for x in e.neighbor_indices[j]]

    def stub():
        W = real()
        others = [x for x in pool_j if x != p]
        W[others] = 0.1                                          # p is the only eligible candidate for site j
        return W
    e.condition_score = stub
    u = np.ones(n); u[j] = 0.0
    e.death_rng = _Draws(u)
    e.step()
    assert e.last_W[p] == pytest.approx(0.3) and e.last_survivors[p] and e.last_charged[p]
    assert e.parent_ids[j] == e.ids[p]
    k = int(((e.parent_ids == e.ids[p]) & (e.ages == 0)).sum())
    assert k == 1
    e.condition_score = real
    e.death_rng = _Draws(np.ones(n))
    e.step()
    # W_next = 0.2 + 0.8 * 0.3 - 0.2 * 0.9 - 0.4 * 1 = -0.14 (no care received): starves although its draw survives
    assert e.last_W[p] == pytest.approx(-0.14) and e.last_starved[p] and e.last_diag["n_starve_added"] >= 1


def test_r3d_global_active_starvation_streams():
    import copy
    e = _r3d("F6-global", seed=5, steps=3000)
    hits = 0
    for t in range(2500):
        ref = copy.deepcopy(e); ref.sigma = -np.inf
        e.step(); ref.step()
        for g in ("rng", "death_rng", "global_rng"):
            assert getattr(e, g).bit_generator.state == getattr(ref, g).bit_generator.state, g
        if e.last_starved.any():
            hits += 1
            if hits >= 3:
                break
    assert hits >= 3


def test_r3d_runner_window_sums_and_activation(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r, run_r3d
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r3d_arms(1)["F6-local"]
    row = r.run_one(("F6-local", m, u, 0, 1030))
    mm = dict(m)
    eng = make_engine(run_config(0, u, 1030), replacement=mm.pop("replacement"), death=mm.pop("death"), **mm)
    add = dead = 0
    while eng.step_index < 1030:
        start = eng.step_index
        eng.step()
        if start >= c.K1_DIAG_FROM:
            add += eng.last_diag["n_starve_added"]; dead += eng.last_diag["n_deaths"]
    assert row["starve_added_total"] == add and row["deaths_total"] == dead

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            out = []
            for a, _, _, s, n in jobs:
                tot = 100 + 50 * s                                # unequal denominators per seed
                out.append({"arm": a, "seed": s, "final_mean_trait": 0.9, "success": 1, "sustained_success": 1,
                            "survival_fraction": 0.5, "traj_every_50": [0.9], "neighbour_h_corr": [0.0] * 6,
                            "final_occupancy": 1.0, "extinct": 0, "occupancy_last1000": 1.0, "occ_every_50": [1.0],
                            "starve_added_total": 0, "deaths_total": tot,
                            **{k: 0.5 for k in (*r.DIAG_KEYS, *r.EXTRA_KEYS)}})
            seeds = [o for o in out if o["arm"] == "F6-local"]
            total = sum(o["deaths_total"] for o in seeds)
            seeds[0]["starve_added_total"] = total // 100           # exactly 1% pooled (total is a multiple of 100)
            return out

    monkeypatch.setattr(r, "Pool", FakePool)
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(r, "classify_r1", lambda *a: {"met": True, "class": "met"})
    run_r3d.main()
    v = json.loads((tmp_path / "r3d_verdict.json").read_text())
    assert v["attempt1"]["starvation_activation"] == pytest.approx(0.01)
    assert v["attempt1"]["starvation_active"] is True             # pooled ratio, not a mean of seed ratios


# ---- Step R4: income from a limited, renewable site resource ----

def _r4(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.r4_arms(1), **c.r4_arms(2)}[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r4_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import IncomeEngine
    a1, a2 = c.r4_arms(1), c.r4_arms(2)
    assert sorted(a1) == sorted(["G6-local", "G3-local", "G12-local", "G24-local", "GN6-local", "G-below",
                                 "G6-global", "G12-global", "G6-local-lean", "G6-global-lean"])
    assert sorted(a2) == sorted(["G2-6-local", "G2-3-local", "G2-12-local", "G2-24-local", "G2-N6-local",
                                 "G2-below", "G2-6-global", "G2-12-global"])
    f = c.r3d_arms(1)
    for arms, gm, pre in ((a1, 0.15, "G"), (a2, 0.18, "G2-")):
        for name, (m, u) in arms.items():
            if name.endswith("-lean"):
                mf, uf = f["F" + name[len(pre):-len("-lean")]]
                assert u == uf and m == {**mf, "care_gamma": 0.08}
                continue
            fname = "F-below" if name.endswith("below") else "F" + name[len(pre):]
            mf, uf = f[fname]
            assert u == uf and m == {**mf, "care_gamma": gm} and m["care_sigma"] == 0.0
    assert c.r4_roles(1) == ("G6-local", "GN6-local", "G-below", "G6-global")
    assert c.r4_roles(2) == ("G2-6-local", "G2-N6-local", "G2-below", "G2-6-global")
    assert isinstance(_r4("G6-local"), IncomeEngine)
    for bad in (0.0, 1.5, np.nan):
        with pytest.raises(ValueError):
            _r4("G6-local", mech_over={"care_gamma": bad})
    with pytest.raises(ValueError):
        _r4("G6-local", mech_over={"care_rho": 0.7})                       # cap 0.2 must equal 1 - rho
    with pytest.raises(ValueError):
        make_engine(run_config(1, {}, 5), death=0.5, care="offspring", care_lam=0.5, care_juvenile=2,
                    care_rho=0.8, care_birth_cost=0.5, care_theta=0.25, care_gamma=0.15,
                    self_in_routing=False, kin="label")


def test_r4_gamma_one_equals_r3d():
    for g_name, f_name in (("G6-local", "F6-local"), ("G6-global", "F6-global"), ("GN6-local", "FN6-local")):
        g = _r4(g_name, seed=13, steps=300, mech_over={"care_gamma": 1.0})
        f = _r3d(f_name, seed=13, steps=300)
        for _ in range(300):
            occ0 = g.occ.copy()
            g.step(); f.step()
            for x in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D", "Db", "occ", "last_W"):
                assert np.array_equal(getattr(g, x), getattr(f, x)), x
            assert (g.G == 1.0).all() and (g.r == 1.0).all()
            assert (g.last_harvest[occ0] == 0.2).all() and (g.last_harvest[~occ0] == 0.0).all()
        for k in ("rng", "death_rng", "global_rng"):
            assert getattr(g, k).bit_generator.state == getattr(f, k).bit_generator.state, k
        for k in ("rng", "genome_rng"):
            if hasattr(f.mechanism, k):
                assert getattr(g.mechanism, k).bit_generator.state == getattr(f.mechanism, k).bit_generator.state


def test_r4_gamma_one_equals_r3d_with_vacancies():
    # force vacancies (low W pools) identically in both, then compare last_W and state after the stub is removed
    g = _r4("G6-local", seed=4, steps=200, mech_over={"care_gamma": 1.0})
    f = _r3d("F6-local", seed=4, steps=200)
    for _ in range(20):
        g.step(); f.step()
    for e in (g, f):
        for v in (30, 31, 100):
            e.occ[v] = False; e.h[v] = 0; e.ids[v] = -1; e.parent_ids[v] = -1; e.ages[v] = 0
            e.lineage[v] = -1; e.S[v] = e.D[v] = e.Db[v] = 0
    g.r[[30, 31, 100]] = 1.0; g.G[[30, 31, 100]] = 1.0
    for _ in range(100):
        g.step(); f.step()
        assert np.array_equal(g.last_W, f.last_W)
        for x in ("h", "occ", "S", "D", "ids"):
            assert np.array_equal(getattr(g, x), getattr(f, x)), x
    for k in ("rng", "death_rng", "global_rng"):
        assert getattr(g, k).bit_generator.state == getattr(f, k).bit_generator.state, k


def test_r4_harvest_and_regrow_rules():
    e = _r4("G6-local", seed=6, steps=200)
    for _ in range(25):
        e.step()
    n = e.n_sites
    rng = np.random.default_rng(0)
    e.r = rng.uniform(0, 1, n)
    v = 50
    e.occ[v] = False; e.h[v] = 0; e.ids[v] = -1; e.parent_ids[v] = -1; e.ages[v] = 0; e.lineage[v] = -1
    e.S[v] = e.D[v] = e.Db[v] = 0; e.G[v] = 1.0
    occ0, r0, G0, S0, D0 = e.occ.copy(), e.r.copy(), e.G.copy(), e.S.copy(), e.D.copy()
    e.step()
    g = e.last_harvest
    assert np.array_equal(g, np.where(occ0, np.minimum(r0, 0.2), 0.0))      # dying occupants harvest too
    assert g[v] == 0.0
    post = r0 - g
    assert np.allclose(e.r, post + 0.15 * (1 - post))                         # regrowth from post-harvest stock
    surv = e.last_survivors
    assert np.allclose(e.G[surv], (0.8 * G0 + g)[surv])
    assert (e.G[~surv] == 1.0).all()                                          # newborns and empty sites
    # W at payoff used G after the harvest: recompute for survivors (S, D unchanged for them except birth charges)
    W_exp = 0.8 * G0 + g + 0.5 * e.S - e.D
    assert np.allclose(e.last_W[surv & ~e.last_charged], W_exp[surv & ~e.last_charged])
    assert e.last_diag["n_occ_start"] == int(occ0.sum())
    assert e.last_diag["harvest_total"] == pytest.approx(g[occ0].sum())
    assert e.last_diag["frac_harvest_capped"] == pytest.approx(float((r0[occ0] < 0.2).mean()))
    assert e.last_diag["r_empty"] == pytest.approx(r0[~occ0].mean())


def test_r4_steady_state_single_site():
    e = _r4("G6-local", seed=1, steps=10)
    gamma = 0.15
    G, r = 1.0, 1.0
    for _ in range(300):
        h = min(r, 0.2); r -= h; G = 0.8 * G + h; r = r + gamma * (1 - r)
    assert h == pytest.approx(gamma) and G == pytest.approx(5 * gamma)
    # the engine's own update on a continuously occupied site
    occ = np.zeros(e.n_sites, bool); occ[0] = True
    for _ in range(300):
        g = e.harvest(occ); e.regrow()
    assert g[0] == pytest.approx(gamma) and e.G[0] == pytest.approx(5 * gamma)
    assert (e.G[1:] == 1.0).all() and (e.r[1:] == 1.0).all()


def test_r4_newborn_g_and_site_resource_kept_two_step_vacancy():
    e = _r4("G6-local-lean", seed=11, steps=200)
    for _ in range(30):
        e.step()
    n = e.n_sites
    v = 70
    pool = [int(j) for j in e.neighbor_indices[v]]
    nb = [j for j in pool if j != v]
    assert e.occ[v]
    e.r[v] = 0.1
    real = e.condition_score

    def low():                                                # step 1: v dies, no eligible candidate: stays empty
        W = real(); W[pool] = 0.1
        return W
    e.condition_score = low
    u = np.ones(n); u[v] = 0.0
    e.death_rng = _Draws(u)
    e.step()
    assert not e.occ[v] and e.last_harvest[v] == pytest.approx(0.1)   # the dying occupant harvested its site
    assert e.r[v] == pytest.approx(0.08) and e.G[v] == 1.0          # regrown from 0 at gamma 0.08
    r_pre = e.r.copy(); occ_pre = e.occ.copy()

    def high():                                               # step 2: neighbours eligible, v refilled
        W = real(); W[nb] = 1.0
        return W
    e.condition_score = high
    e.death_rng = _Draws(np.ones(n))
    e.step()
    assert e.last_harvest[v] == 0.0 and e.occ[v] and e.ages[v] == 0 and e.G[v] == 1.0
    assert e.r[v] == pytest.approx(0.08 + 0.08 * 0.92)            # empty site regrew, not reset
    assert e.last_diag["r_occupied"] == pytest.approx(r_pre[occ_pre].mean())
    assert e.last_diag["r_empty"] == pytest.approx(r_pre[~occ_pre].mean())
    e.condition_score = real
    e.step()                                                  # step 3: the newborn harvests the regrown stock
    assert e.last_harvest[v] == pytest.approx(0.1536)
    assert e.last_survivors[v] and e.G[v] == pytest.approx(0.8 + 0.1536)


def test_r4_diag_cohort_g_means():
    e = _r4("G6-local", seed=2, steps=200)
    for _ in range(40):
        e.step()
    occ0 = e.occ.copy(); juv0 = (e.ages < e.care_juvenile) & occ0
    ps = e.parent_sites()
    kids0 = (np.bincount(ps[ps >= 0], minlength=e.n_sites) > 0) & occ0
    G_exp = np.where(occ0, 0.8 * e.G + np.minimum(e.r, 0.2), e.G)
    e.step()
    d = e.last_diag
    assert d["G_mean"] == pytest.approx(G_exp[occ0].mean())
    assert d["G_juvenile"] == pytest.approx(G_exp[juv0].mean()) and d["G_parents"] == pytest.approx(G_exp[kids0].mean())


def test_r4_lottery_uses_g_once_with_unequal_eligible():
    e = _r4("G6-local", seed=5, steps=200, B_plus_scale=0.0, C_scale=0.0)
    for _ in range(30):
        e.step()
    i = 40
    pool = [int(j) for j in e.neighbor_indices[i]]
    a, b = [j for j in pool if j != i][:2]
    e.S[:] = 0.0; e.D[:] = 0.0; e.r[:] = 0.0; e.G[:] = 0.2 / 0.8      # all W = 0.2: ineligible
    e.G[a] = 0.5 / 0.8; e.G[b] = 1.0 / 0.8                            # W 0.5 and 1.0: the two eligible
    calls = {"cs": 0, "lot": []}
    real_cs, real_lot = e.condition_score, e.lottery

    def cs():
        calls["cs"] += 1
        return real_cs()

    def lot(W, eligible):
        calls["lot"].append(W.copy())
        return real_lot(W, eligible)
    e.condition_score = cs; e.lottery = lot
    e.step()
    assert calls["cs"] == 1 and len(calls["lot"]) == 1
    W = calls["lot"][0]
    assert W[a] == pytest.approx(0.5) and W[b] == pytest.approx(1.0)
    p = e.pool_probs(W[pool], e.last_eligible[pool], float(e.cfg["selection_temperature"]))
    pa, pb = p[pool.index(a)], p[pool.index(b)]
    assert pa + pb == pytest.approx(1.0) and pb / pa == pytest.approx(np.exp(0.5 / 0.12))


def test_r4_unequal_g_drives_eligibility_starvation_and_lottery():
    e = _r4("G6-local", seed=5, steps=200, B_plus_scale=0.0, C_scale=0.0)   # no care: W depends on G only
    for _ in range(30):
        e.step()
    n = e.n_sites
    i = 40
    pool = [int(j) for j in e.neighbor_indices[i]]
    others = [j for j in pool if j != i]
    a, b = others[0], others[1]
    e.S[:] = 0.0; e.D[:] = 0.0
    e.r[:] = 0.0                                          # no harvest: G <- 0.8 G
    e.G[:] = 1.0
    e.G[a] = -0.1 / 0.8                                    # W = -0.1: starves
    e.G[b] = 0.2 / 0.8                                     # W = 0.2: ineligible but alive
    e.G[[j for j in others if j not in (a, b)]] = 0.2 / 0.8
    e.G[i] = 1.0                                            # W = 0.8 for the dying focal: the only eligible
    u = np.ones(n); u[i] = 0.0
    e.death_rng = _Draws(u)
    ida = e.ids[a]; idi = e.ids[i]
    e.step()
    assert e.last_W[a] == pytest.approx(-0.1) and e.last_starved[a]
    assert e.last_W[b] == pytest.approx(0.2) and not e.last_eligible[b] and e.last_survivors[b]
    assert e.occ[i] and e.parent_ids[i] == idi              # the only eligible candidate in i's pool bred
    assert not (e.parent_ids[e.occ & (e.ages == 0)] == ida).any()


def test_r4_null_equals_k_null():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.k0_arms(1)["K-null"]
    m = dict(m); m.pop("exclude_focal")
    ref = make_engine(run_config(9, u, 60), **m)
    e = _r4("G6-local", seed=9, steps=60, mech_over={"care_sigma": -np.inf, "care_theta": -np.inf,
                                                      "care_birth_cost": 0.0, "care_gamma": 1.0},
            B_plus_scale=0.0, C_scale=0.0)
    for _ in range(60):
        ref.step(); e.step()
    assert np.array_equal(ref.h, e.h) and np.array_equal(ref.lineage, e.lineage)


def test_r4_runner_window_and_activation(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r, run_r4
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r4_arms(1)["G6-local"]
    row = r.run_one(("G6-local", m, u, 0, 1030))
    assert all(k in row for k in r.EXTRA_KEYS[:r.EXTRA_KEYS.index("frac_exposed")])
    assert "frac_exposed" not in row and "n_exposed" not in row
    mm = dict(m)
    eng = make_engine(run_config(0, u, 1030), replacement=mm.pop("replacement"), death=mm.pop("death"), **mm)
    hv = 0.0; no = 0
    while eng.step_index < 1030:
        start = eng.step_index
        eng.step()
        if start >= c.K1_DIAG_FROM:
            hv += eng.last_diag["harvest_total"]; no += eng.last_diag["n_occ_start"]
    assert row["harvest_total"] == pytest.approx(hv) and row["n_occ_start"] == no and no > 0
    calls = []

    def fake(windows):
        """windows: arm -> list of (occupant-steps, harvest) per seed (other arms 0.2 per occupant-step)."""
        class FakePool:
            def __init__(self, *_): pass
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def map(self, f, jobs):
                calls.append(sorted({j[0] for j in jobs}))
                out = []
                for a, _, _, s, n in jobs:
                    no, hv = windows.get(a, [(50 + s, 0.2 * (50 + s))] * 20)[s]
                    out.append({"arm": a, "seed": s, "final_mean_trait": 0.5, "success": 0, "sustained_success": 0,
                                "survival_fraction": 0.5, "traj_every_50": [0.5], "neighbour_h_corr": [0.0] * 6,
                                "final_occupancy": 0.9, "extinct": 0, "occupancy_last1000": 0.9,
                                "occ_every_50": [0.9], "starve_added_total": 1, "deaths_total": 200,
                                "harvest_total": hv, "n_occ_start": no,
                                **{k: 0.5 for k in (*r.DIAG_KEYS, *r.EXTRA_KEYS)}})
                return out
        return FakePool

    mix = float(np.tile([0.18, 0.20], 6).sum())                   # decimal mean 0.19, float 0.19000000000000003
    w_exact = [(12, mix), (0, 0.0)] + [(0, 0.0)] * 18                # one empty window ignored
    w_above = [(100, 19.0), (1, 0.6)] + [(0, 0.0)] * 18             # (19.6) / 101 > 0.19
    monkeypatch.setattr(r, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(r, "Pool", fake({"G6-local": w_above, "G2-6-local": w_exact}))
    run_r4.main()
    assert calls == [sorted(c.r4_arms(1)), sorted(c.r4_arms(2))]
    v = json.loads((tmp_path / "r4_verdict.json").read_text())
    assert v["attempt1"]["care_gamma"] == 0.15 and v["attempt2"]["care_gamma"] == 0.18
    assert v["attempt1"]["pooled_harvest"] == pytest.approx(19.6 / 101)
    assert v["attempt1"]["income_limitation_active"] is False
    assert v["attempt1"]["income_limitation_label"] == "income limitation inactive"
    assert v["attempt2"]["test_arm"] == "G2-6-local" and v["attempt2"]["income_limitation_active"] is True
    assert v["attempt2"]["income_limitation_label"] == "income limitation active"
    assert v["attempt1"]["descriptive"]["GN6-local"]["pooled_harvest"] == pytest.approx(0.2)


# ---------------------------------------------------------------- Diagnostic DR4
def _dr4(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.dr4_arms()[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_dr4_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import IncomeEngine, StarvationEngine
    a = c.dr4_arms()
    assert list(a) == ["D-F", "D-G", "D-U85", "D-U75", "D-E", "D-Fcb0", "D-Gcb0"]
    mf, uf = c.r3d_arms(1)["F6-local"]
    mg, ug = c.r4_arms(1)["G6-local"]
    assert a["D-F"] == (mf, uf) and a["D-G"] == (mg, ug)
    assert a["D-U85"] == (mf, {**uf, "base_fitness": 0.85}) and a["D-U75"] == (mf, {**uf, "base_fitness": 0.75})
    assert a["D-E"] == ({**mg, "care_g_start": 0.75}, ug)
    assert a["D-Fcb0"] == ({**mf, "care_birth_cost": 0.0}, uf) and a["D-Gcb0"] == ({**mg, "care_birth_cost": 0.0}, ug)
    assert mf["care_birth_cost"] == 0.5 and mg["care_gamma"] == 0.15 and mf["replacement"] == "local"
    for n in a:
        e = _dr4(n)
        assert isinstance(e, IncomeEngine) == (n in ("D-G", "D-E", "D-Gcb0")) and isinstance(e, StarvationEngine)
    assert _dr4("D-E").g_start == 0.75 and _dr4("D-G").g_start == 1.0
    with pytest.raises(ValueError):
        _r3d("F6-local", mech_over={"care_g_start": 0.75})          # needs care_gamma
    with pytest.raises(ValueError):
        _dr4("D-E", mech_over={"care_g_start": float("nan")})


def test_dr4_g_start_one_equals_r4():
    g = _dr4("D-E", seed=5, steps=300, mech_over={"care_g_start": 1.0})
    f = _r4("G6-local", seed=5, steps=300)
    for _ in range(300):
        g.step(); f.step()
        for x in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D", "Db", "occ", "last_W", "G", "r"):
            assert np.array_equal(getattr(g, x), getattr(f, x)), x
    for k in ("rng", "death_rng", "global_rng"):
        assert getattr(g, k).bit_generator.state == getattr(f, k).bit_generator.state, k


def test_dr4_g_start_founders_and_newborns():
    e = _dr4("D-E", seed=3, steps=100)
    assert (e.G == 0.75).all()
    e.step()                                                       # founders on full stock: 0.8 * 0.75 + 0.2
    s = e.last_survivors
    assert np.allclose(e.G[s], 0.8 * 0.75 + 0.2) and (e.G[~s] == 0.75).all() and (~s).any()
    for _ in range(20):
        G0, occ0 = e.G.copy(), e.occ.copy()
        e.step()
        s = e.last_survivors
        assert (e.G[~s] == 0.75).all()
        assert np.allclose(e.G[s], 0.8 * G0[s] + e.last_harvest[s]) and (occ0[s]).all()


def test_dr4_uniform_cut_is_a_cutoff_shift():
    """base_fitness 1 - x with (theta, sigma) is base 1 with (theta + x, sigma + x): same lottery probabilities
    (1e-12) on a fixed state, same eligibility and starvation away from the cutoffs."""
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import ThresholdEngine
    for x, arm in ((0.15, "D-U85"), (0.25, "D-U75")):
        cut = _dr4(arm, seed=4, steps=200)
        for _ in range(60):
            cut.step()
        W_cut = cut.condition_score()
        W_one = W_cut + x                                            # the same state at base 1
        assert np.allclose(W_one, 1.0 + 0.5 * cut.S - cut.D, atol=1e-12)
        temp = float(cut.cfg["selection_temperature"])
        th, sg = cut.theta, cut.sigma
        e_cut, e_one = cut.occ & (W_cut >= th), cut.occ & (W_one >= th + x)
        away = np.abs(W_cut - th) > 1e-9
        assert np.array_equal(e_cut[away], e_one[away])
        away_s = np.abs(W_cut - sg) > 1e-9
        assert np.array_equal((W_cut < sg)[away_s], (W_one < sg + x)[away_s])
        assert (~e_cut & cut.occ).any() and e_cut.any()             # both sides of the cutoff present
        for pool in cut.neighbor_indices:
            p1 = ThresholdEngine.pool_probs(W_cut[pool], e_cut[pool], temp)
            p2 = ThresholdEngine.pool_probs(W_one[pool], e_cut[pool], temp)
            assert np.max(np.abs(p1 - p2)) < 1e-12


def test_dr4_uniform_cut_trajectory_matches_shifted_cutoffs():
    """Dynamics: R3d at base 0.85 matches R3d at base 1 with theta, sigma raised by 0.15 (this seed has no
    exact-cutoff flip; equality of h, occupancy and draws over 400 steps)."""
    cut = _dr4("D-U85", seed=6, steps=400)
    one = _dr4("D-F", seed=6, steps=400)
    one.theta += 0.15
    one.sigma += 0.15
    for _ in range(400):
        cut.step(); one.step()
        assert np.array_equal(cut.h, one.h) and np.array_equal(cut.occ, one.occ)
        assert np.allclose(cut.last_W + 0.15, one.last_W, atol=1e-12)
    for k in ("rng", "death_rng"):
        assert getattr(cut, k).bit_generator.state == getattr(one, k).bit_generator.state


def test_dr4_births_by_class_forced():
    """A parent that dies in the same step still counts its realized births; classes use start-of-step h."""
    e = _dr4("D-F", seed=9, steps=100)
    for _ in range(20):
        e.step()
    n = e.n_sites
    v = 50
    pool_v = [int(j) for j in e.neighbor_indices[v]]
    j = [p for p in pool_v if p != v][0]
    pool_j = [int(k) for k in e.neighbor_indices[j]]
    assert e.occ[v] and e.occ[j]
    e.h[j] = 0.7
    e.h[v] = 0.2
    real = e.condition_score

    def forced():
        W = real()
        W[:] = 1.0
        W[pool_v + pool_j] = 0.2                                    # ineligible (theta 0.25), not starving (sigma 0)
        W[j] = 1.0
        return W
    e.condition_score = forced
    u = np.ones(n); u[[v, j]] = 0.0                                  # v and its only eligible neighbour j die
    e.death_rng = _Draws(u)
    h0, occ0 = e.h.copy(), e.occ.copy()
    e.step()
    kb = e.last_births_by_parent
    assert kb[j] == 2 and kb.sum() == 2                             # fills v and its own site
    assert e.parent_ids[v] == e.parent_ids[j] and e.occ[v] and e.occ[j]
    d = e.last_diag
    assert d["births_high_h_sum"] == 2 and d["births_low_h_sum"] == 0
    assert d["n_high_h"] == int((occ0 & (h0 >= 0.5)).sum()) and d["n_low_h"] == int((occ0 & (h0 < 0.5)).sum())
    assert d["frac_births_charged"] == 0.0                           # the dead parent is not charged


def test_dr4_recent_parent_ineligibility():
    e = _dr4("D-G", seed=2, steps=200)
    for _ in range(40):
        e.step()
    prev = e.last_charged.copy()
    occ0 = e.occ.copy()
    e.step()
    exp = (~e.last_eligible[occ0 & prev]).mean() if (occ0 & prev).any() else float("nan")
    assert e.last_diag["frac_ineligible_recent_parents"] == pytest.approx(exp, nan_ok=True)


def _dr4_fake_rows(h_by_arm, extinct=()):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    rows = []
    income = r.EXTRA_KEYS[r.EXTRA_KEYS.index("harvest_mean"):r.EXTRA_KEYS.index("frac_harvest_capped") + 1]
    for a, hs in h_by_arm.items():
        for s, h in enumerate(hs):
            ext = (a, s) in extinct
            rows.append({"arm": a, "seed": s, "final_mean_trait": float("nan") if ext else h, "success": int(h >= 0.6),
                         "sustained_success": 0, "survival_fraction": 0.5, "traj_every_50": [h] * 120,
                         "neighbour_h_corr": [0.0] * 6, "final_occupancy": 0.0 if ext else 0.99,
                         "extinct": int(ext), "occupancy_last1000": 0.99, "occ_every_50": [0.99] * 120,
                         "starve_added_total": 1, "deaths_total": 100, "births_low_h_sum": 3 if s else 9,
                         "n_low_h": 30 if s else 10, "births_high_h_sum": 5, "n_high_h": 100,
                         **{k: 0.5 for k in (*r.DIAG_KEYS, *r.EXTRA_KEYS)
                            if a in ("D-G", "D-E", "D-Gcb0") or k not in income}})
    return rows


def _dr4_store(tmp_path, rows):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_steps01 import write_csv
    for name, arm, src in (("r3d", "F6-local", "D-F"), ("r4", "G6-local", "D-G")):
        st = [{**r, "arm": arm} for r in rows if r["arm"] == src]
        write_csv(tmp_path / f"{name}_runs.csv", st)
        traj = [float(np.mean([r["traj_every_50"][t] for r in st])) for t in range(120)]
        (tmp_path / f"{name}_verdict.json").write_text(json.dumps(
            {"attempt1": {"descriptive": {arm: {"mean_h_every_50": traj}}}}))


def test_dr4_runner_readings(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr4 as d
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    noise = np.linspace(-0.02, 0.02, 20)
    h = {"D-F": 0.6 + noise, "D-G": 0.9 + noise, "D-U85": 0.86 + noise, "D-U75": 0.62 + noise,
         "D-E": 0.75 + np.where(np.arange(20) % 2, 0.1, -0.1), "D-Fcb0": 0.5 + noise, "D-Gcb0": 0.85 + noise}
    rows = _dr4_fake_rows(h, extinct={("D-U75", 3)})
    _dr4_store(tmp_path, rows)
    jobs_seen = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            jobs_seen.extend(jobs)
            return rows

    monkeypatch.setattr(d, "Pool", FakePool)
    monkeypatch.setattr(d, "DATA_DIR", str(tmp_path))
    d.main()
    assert sorted({j[0] for j in jobs_seen}) == sorted(c.dr4_arms()) and len(jobs_seen) == 140
    assert all(j[4] == 6000 for j in jobs_seen)
    v = json.loads((tmp_path / "dr4_verdict.json").read_text())
    assert v["valid"] and v["delta"] == pytest.approx(0.3)
    p = v["parts"]
    assert p["U85"]["reading"] == "accounts for most of the rise" and p["U85"]["share"] == pytest.approx(0.26 / 0.3)
    # extinct seed 3 counts as h = 0
    exp75 = (np.sum(0.62 + noise) - (0.62 + noise[3])) / 20 - 0.6
    assert p["U75"]["numerator"] == pytest.approx(exp75) and p["U75"]["reading"] == "accounts for less than half"
    assert p["E"]["reading"] == "unclear"
    assert p["cb0"]["reading"] == "accounts for most of the rise (not needed)"
    assert p["cb0"]["numerator"] == pytest.approx(0.35)            # against D-Fcb0, not D-F
    assert v["overall"].startswith("clear readings:") and "E:" not in v["overall"]
    assert v["descriptive"]["D-U75"]["extinctions"] == 1
    assert v["descriptive"]["D-F"]["births_per_occ_step_low_h"] == pytest.approx((9 + 19 * 3) / (10 + 19 * 30))
    import csv
    with open(tmp_path / "dr4_runs.csv") as f:
        out = list(csv.DictReader(f))
    assert len(out) == 140 and "G_mean" in out[0] and "births_low_h_sum" in out[0]
    assert {x["arm"] for x in out if x["G_mean"] != ""} == {"D-G", "D-E", "D-Gcb0"}
    assert v["descriptive"]["D-F"]["mean_h_2000"] == pytest.approx(0.6)
    t = json.loads((tmp_path / "dr4_trajectories.json").read_text())
    assert len(t["D-G"]["0"]["traj_every_50"]) == 120


def test_dr4_runner_void_on_reference_mismatch(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr4 as d
    noise = np.linspace(-0.02, 0.02, 20)
    h = {a: 0.6 + noise for a in ("D-F", "D-U85", "D-U75", "D-E", "D-Fcb0", "D-Gcb0")}
    h["D-G"] = 0.9 + noise
    rows = _dr4_fake_rows(h)
    _dr4_store(tmp_path, rows)
    i = next(k for k, r in enumerate(rows) if r["arm"] == "D-G" and r["seed"] == 5)
    rows[i] = {**rows[i], "final_mean_trait": rows[i]["final_mean_trait"] + 1e-15}     # tiny change

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs): return rows

    monkeypatch.setattr(d, "Pool", FakePool)
    monkeypatch.setattr(d, "DATA_DIR", str(tmp_path))
    d.main()
    v = json.loads((tmp_path / "dr4_verdict.json").read_text())
    assert v["references"]["D-G"]["mismatches"] == [[5, "final_mean_trait"]]
    assert v["references"]["D-F"]["seeds_match"] and not v["valid"] and v["overall"] == "void"


def test_dr4_overall_and_small_rise():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr4 as d
    P = lambda **r: {k: {"reading": x} for k, x in r.items()}
    assert d.overall(P(U85="unclear", U75="unclear", E="unclear", cb0="unclear")) == "inconclusive"
    assert d.overall(P(U85="accounts for less than half", U75="accounts for less than half",
                       E="accounts for most of the rise (not needed)",
                       cb0="accounts for most of the rise (not needed)")) == "unexplained by these parts"
    assert d.overall(P(U85="accounts for less than half", U75="unclear",
                       E="accounts for most of the rise (not needed)",
                       cb0="accounts for most of the rise (not needed)")).startswith("clear readings:")
    assert d.reading("E", -0.2, -0.1) == "accounts for less than half (needed)"
    assert d.reading("U85", -0.1, 0.1) == "unclear"
    # bootstrap uses the same resampled seeds in every arm: identical arms give d = -0.5 Delta exactly
    h = {"D-F": np.linspace(0, 1, 20), "D-G": np.linspace(0, 1, 20) + 0.2}
    for a in ("D-U85", "D-U75", "D-E", "D-Fcb0", "D-Gcb0"):
        h[a] = h["D-F"].copy()
    b = d.bootstrap(h)
    assert b["delta_ci"][0] == pytest.approx(0.2) and b["delta_ci"][1] == pytest.approx(0.2)
    assert b["parts"]["U85"]["d_ci"] == pytest.approx([-0.1, -0.1])


def test_dr4_reference_reruns_reproduce_stored_seed0():
    """Pre-run check: seed 0 of the references reproduces r3d_runs.csv (F6-local) and r4_runs.csv (G6-local)."""
    import csv
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    for arm, name, stored_arm in (("D-F", "r3d", "F6-local"), ("D-G", "r4", "G6-local")):
        m, u = c.dr4_arms()[arm]
        row = r.run_one((arm, m, u, 0, 6000))
        with open(f"{c.DATA_DIR}/{name}_runs.csv") as f:
            s = [x for x in csv.DictReader(f) if x["arm"] == stored_arm and x["seed"] == "0"][0]
        assert float(s["final_mean_trait"]) == row["final_mean_trait"]
        assert float(s["final_occupancy"]) == row["final_occupancy"]


def _dr4_run_fake(monkeypatch, tmp_path, rows):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr4 as d

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs): return rows

    monkeypatch.setattr(d, "Pool", FakePool)
    monkeypatch.setattr(d, "DATA_DIR", str(tmp_path))
    d.main()
    return json.loads((tmp_path / "dr4_verdict.json").read_text())


@pytest.mark.parametrize("kind", ["occupancy", "trajectory"])
def test_dr4_runner_void_on_occupancy_or_trajectory_mismatch(monkeypatch, tmp_path, kind):
    noise = np.linspace(-0.02, 0.02, 20)
    h = {a: 0.6 + noise for a in ("D-F", "D-U85", "D-U75", "D-E", "D-Fcb0", "D-Gcb0")}
    h["D-G"] = 0.9 + noise
    rows = _dr4_fake_rows(h)
    _dr4_store(tmp_path, rows)
    i = next(k for k, r in enumerate(rows) if r["arm"] == "D-F" and r["seed"] == 7)
    if kind == "occupancy":
        rows[i] = {**rows[i], "final_occupancy": 0.98}
    else:
        t = list(rows[i]["traj_every_50"]); t[40] += 1e-9
        rows[i] = {**rows[i], "traj_every_50": t}
    v = _dr4_run_fake(monkeypatch, tmp_path, rows)
    ref = v["references"]["D-F"]
    if kind == "occupancy":
        assert ref["mismatches"] == [[7, "final_occupancy"]] and ref["mean_traj_match"]
    else:
        assert ref["seeds_match"] and not ref["mean_traj_match"]
    assert v["references"]["D-G"]["seeds_match"] and not v["valid"] and v["overall"] == "void"


def test_dr4_runner_rise_at_and_below_cutoff(monkeypatch, tmp_path):
    for dg, ok in ((0.6, True), (0.59, False)):
        h = {a: np.full(20, 0.5) for a in ("D-F", "D-U85", "D-U75", "D-E", "D-Fcb0", "D-Gcb0")}
        h["D-G"] = np.full(20, dg)
        rows = _dr4_fake_rows(h)
        _dr4_store(tmp_path, rows)
        v = _dr4_run_fake(monkeypatch, tmp_path, rows)
        assert v["delta"] < 0.1 if ok else True                     # 0.0999...87 in floating point
        assert v["rise_ok"] is ok and v["valid"] is ok and (v["overall"] == "void") is (not ok)


def test_dr4_runner_extinct_reference_reproduced_is_valid(monkeypatch, tmp_path):
    noise = np.linspace(-0.02, 0.02, 20)
    h = {a: 0.6 + noise for a in ("D-F", "D-U85", "D-U75", "D-E", "D-Fcb0", "D-Gcb0")}
    h["D-G"] = 0.9 + noise
    rows = _dr4_fake_rows(h, extinct={("D-F", 2)})
    i = next(k for k, r in enumerate(rows) if r["arm"] == "D-F" and r["seed"] == 2)
    rows[i] = {**rows[i], "traj_every_50": [float("nan")] * 120}
    _dr4_store(tmp_path, rows)
    import json
    for name in ("r3d",):                                          # the stored mean trajectory has nulls, as json_safe writes
        p = tmp_path / f"{name}_verdict.json"
        v = json.loads(p.read_text())
        v["attempt1"]["descriptive"]["F6-local"]["mean_h_every_50"] = [None] * 120
        p.write_text(json.dumps(v))
    v = _dr4_run_fake(monkeypatch, tmp_path, rows)
    assert v["references"]["D-F"]["seeds_match"] and v["references"]["D-F"]["mean_traj_match"] and v["valid"]
    assert v["descriptive"]["D-F"]["final_h_per_seed"][2] == 0.0


def test_dr4_bootstrap_paired_draws():
    """With D-U85 = D-F + 0.5 (D-G - D-F) seed by seed, d is 0 in every resample only if numerator and Delta use
    the same draw and all arms the same seeds; independent draws would give a wide interval."""
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr4 as d
    rng = np.random.default_rng(1)
    f = rng.uniform(0.4, 0.8, 20)
    g = f + rng.uniform(0.0, 0.6, 20)
    h = {"D-F": f, "D-G": g, "D-U85": f + 0.5 * (g - f), "D-U75": f, "D-E": g, "D-Fcb0": f, "D-Gcb0": f}
    b = d.bootstrap(h)
    lo, hi = b["parts"]["U85"]["d_ci"]
    assert abs(lo) < 1e-12 and abs(hi) < 1e-12 and b["parts"]["U85"]["share"] == pytest.approx(0.5)
    assert b["delta_ci"][1] - b["delta_ci"][0] > 0.05                # Delta itself varies across resamples
    assert b["parts"]["E"]["reading"] == "accounts for most of the rise (not needed)"
    assert b["parts"]["U75"]["reading"] == "accounts for less than half"


# ---------------------------------------------------------------- Step R5a (foraging over the neighbourhood)
def _r5a(name, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = {**c.r5a_arms(1), **c.r5a_arms(2)}[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def _forage_reference(occ, r, grid, w_own):
    """Loop implementation of the pre-registered R5a rule."""
    n = len(r)
    w = lambda i, s: w_own if i == s else (1 - w_own) / 4
    nb = [np.nonzero(grid[i])[0] for i in range(n)]
    Q = np.zeros(n)
    for i in range(n):
        if occ[i]:
            for s in nb[i]:
                Q[s] += 0.2 * w(i, s)
    a = np.array([min(1.0, r[s] / Q[s]) if Q[s] > 0 else 1.0 for s in range(n)])
    g = np.zeros(n)
    for i in range(n):
        if occ[i]:
            g[i] = 0.2 if all(a[s] == 1.0 for s in nb[i]) else sum(0.2 * w(i, s) * a[s] for s in nb[i])
    r_new = np.array([r[s] - min(r[s], Q[s]) if Q[s] > 0 else r[s] for s in range(n)])
    return g, r_new


def test_r5a_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import ForagingEngine
    a1, a2 = c.r5a_arms(1), c.r5a_arms(2)
    assert sorted(a1) == sorted(["A3-local", "A6-local", "A12-local", "A24-local", "AN6-local", "A-below",
                                 "A6-global", "A12-global", "A6-local-lean", "A6-global-lean"])
    assert sorted(a2) == sorted(["A2-3-local", "A2-6-local", "A2-12-local", "A2-24-local", "A2-N6-local",
                                 "A2-below", "A2-6-global", "A2-12-global"])
    r4 = c.r4_arms(1)
    for name, (m, u) in a1.items():
        src = "G-below" if name == "A-below" else "G" + name[1:]
        assert m == {**r4[src][0], "care_forage_own": 0.2} and u == r4[src][1]
    for name, (m, u) in a2.items():
        src = "G-below" if name == "A2-below" else "G" + name[3:]
        assert m == {**r4[src][0], "care_forage_own": 0.5} and u == r4[src][1]
    assert a1["A6-local-lean"][0]["care_gamma"] == 0.08 and a1["A6-local"][0]["care_gamma"] == 0.15
    for roles, arms in ((c.r5a_roles(1), a1), (c.r5a_roles(2), a2)):
        assert all(x in arms for x in roles)
    e = _r5a("A6-local")
    assert isinstance(e, ForagingEngine) and e.w_nb == pytest.approx(0.2) and _r5a("A2-6-local").w_nb == 0.125
    assert c.R5A_PILOT_ARMS == ("A6-local", "A6-local-lean") and c.R5A_PILOT_SEEDS == [0, 1]
    with pytest.raises(ValueError):
        _r5a("A6-local", mech_over={"care_g_start": 0.75})
    with pytest.raises(ValueError):
        _r5a("A6-local", mech_over={"care_forage_own": 0.0})
    with pytest.raises(ValueError):
        _r3d("F6-local", mech_over={"care_forage_own": 0.2})          # needs care_gamma


@pytest.mark.parametrize("pair", [("A6-local", "F6-local"), ("A6-global", "F6-global"), ("AN6-local", "FN6-local"),
                                  ("A2-6-local", "F6-local")])
def test_r5a_gamma_one_equals_r3d(pair):
    a_name, f_name = pair
    a = _r5a(a_name, seed=13, steps=300, mech_over={"care_gamma": 1.0})
    f = _r3d(f_name, seed=13, steps=300)
    for _ in range(300):
        occ0 = a.occ.copy()
        a.step(); f.step()
        for x in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D", "Db", "occ", "last_W"):
            assert np.array_equal(getattr(a, x), getattr(f, x)), x
        assert (a.G == 1.0).all() and (a.r == 1.0).all()
        assert (a.last_harvest[occ0] == 0.2).all() and (a.last_harvest[~occ0] == 0.0).all()
        assert a.last_diag["n_exposed"] == 0
    for k in ("rng", "death_rng", "global_rng"):
        assert getattr(a, k).bit_generator.state == getattr(f, k).bit_generator.state, k
    for k in ("rng", "genome_rng"):
        if hasattr(f.mechanism, k):
            assert getattr(a.mechanism, k).bit_generator.state == getattr(f.mechanism, k).bit_generator.state


def test_r5a_gamma_one_equals_r3d_with_vacancies_and_refills():
    a = _r5a("A6-local", seed=4, steps=200, mech_over={"care_gamma": 1.0})
    f = _r3d("F6-local", seed=4, steps=200)
    for _ in range(20):
        a.step(); f.step()
    for e in (a, f):
        for v in (30, 31, 100):
            e.occ[v] = False; e.h[v] = 0; e.ids[v] = -1; e.parent_ids[v] = -1; e.ages[v] = 0
            e.lineage[v] = -1; e.S[v] = e.D[v] = e.Db[v] = 0
    a.G[[30, 31, 100]] = 1.0
    refilled = False
    for _ in range(100):
        occ0 = a.occ.copy()
        a.step(); f.step()
        refilled |= bool(a.occ[[30, 31, 100]].any() and not occ0[[30, 31, 100]].all())
        assert np.array_equal(a.last_W, f.last_W)
        for x in ("h", "occ", "S", "D", "Db", "ids", "ages", "parent_ids", "lineage"):
            assert np.array_equal(getattr(a, x), getattr(f, x)), x
        assert (a.last_harvest[occ0] == 0.2).all() and (a.G == 1.0).all() and (a.r == 1.0).all()
    assert refilled
    for k in ("rng", "death_rng", "global_rng"):
        assert getattr(a, k).bit_generator.state == getattr(f, k).bit_generator.state, k
    for k in ("rng", "genome_rng"):
        if hasattr(f.mechanism, k):
            assert getattr(a.mechanism, k).bit_generator.state == getattr(f.mechanism, k).bit_generator.state


@pytest.mark.parametrize("w_own", [0.2, 0.5])
def test_r5a_harvest_matches_loop_reference_on_random_states(w_own):
    name = "A6-local" if w_own == 0.2 else "A2-6-local"
    rng = np.random.default_rng(7)
    for trial in range(6):
        e = _r5a(name, seed=trial)
        occ = rng.random(e.n_sites) < (0.6 if trial % 2 else 0.95)
        r = rng.uniform(0.0, 0.4, e.n_sites)
        r[rng.random(e.n_sites) < 0.2] = 1.0
        e.r = r.copy()
        G0 = rng.uniform(0.5, 1.0, e.n_sites)
        e.G = G0.copy()
        g = e.harvest(occ)
        g_ref, r_ref = _forage_reference(occ, r, e.forage_grid, w_own)
        assert np.allclose(g, g_ref, atol=1e-14) and np.allclose(e.r, r_ref, atol=1e-14)
        assert (e.r >= 0).all() and (g[~occ] == 0).all()
        assert g.sum() == pytest.approx((r - e.r).sum(), abs=1e-12)         # food is conserved
        assert np.allclose(e.G, np.where(occ, 0.8 * G0 + g, G0))


def test_r5a_uniform_full_lattice_equals_own_site_rule():
    e = _r5a("A6-local")
    occ = np.ones(e.n_sites, dtype=bool)
    for stock in (0.15, 0.08, 0.3, 1.0):
        e.r = np.full(e.n_sites, stock)
        g = e.harvest(occ)
        assert np.allclose(g, min(stock, 0.2), atol=1e-15)
        assert not e.exposure_mask(g, np.full(e.n_sites, stock), occ).any()
    e.r = np.full(e.n_sites, 0.3)
    assert (e.harvest(occ) == 0.2).all()                                   # literal 0.2, not a float sum


def test_r5a_isolated_vacancy_hand_computed():
    """One empty site v on uniform stock 0.15: its 4 neighbours and 4 diagonal sites get 0.165 (exposed), sites two
    steps out in a straight line 0.1575 (not exposed): 8 exposed occupants, as in the screen."""
    e = _r5a("A6-local")
    v = 5 * e.width + 5
    occ = np.ones(e.n_sites, dtype=bool); occ[v] = False
    r = np.full(e.n_sites, 0.15)
    e.r = r.copy()
    g = e.harvest(occ)
    W = e.width
    nbrs = [v - 1, v + 1, v - W, v + W]
    diag = [v - W - 1, v - W + 1, v + W - 1, v + W + 1]
    straight = [v - 2, v + 2, v - 2 * W, v + 2 * W]
    assert np.allclose(g[nbrs], 0.04 * (2 * 0.9375 + 3 * 0.75))
    assert np.allclose(g[diag], 0.04 * (2 * 0.9375 + 3 * 0.75))
    assert np.allclose(g[straight], 0.04 * (0.9375 + 4 * 0.75))
    assert g[v] == 0.0 and e.r[v] == 0.0                                    # the empty site is foraged out
    ex = e.exposure_mask(g, r, occ)
    assert set(np.nonzero(ex)[0]) == set(nbrs + diag)


@pytest.mark.parametrize("name,own_take,nb_take", [("A6-local", 0.01, 0.01), ("A2-6-local", 0.04, 0.01)])
def test_r5a_two_foragers_split_a_short_stock(name, own_take, nb_take):
    e = _r5a(name)
    i = 3 * e.width + 3
    j = i + 1
    occ = np.zeros(e.n_sites, dtype=bool); occ[[i, j]] = True
    e.r = np.ones(e.n_sites)
    e.r[i] = 0.02 if name == "A6-local" else 0.05
    g = e.harvest(occ)
    # i's site: demand 0.04 + 0.04 (attempt 1) or 0.1 + 0.025 (attempt 2); split proportionally, stock to 0
    assert e.r[i] == 0.0
    w_own, w_nb = e.w_own, e.w_nb
    rest = 0.2 * (1 - w_own)                                           # i's other four sites are full
    assert g[i] == pytest.approx(own_take + rest)                     # own-site share + four full sites
    assert g[j] == pytest.approx(nb_take + 0.2 * (1 - w_nb))
    assert e.r[j] == pytest.approx(1 - 0.2 * w_own - 0.2 * w_nb)


def test_r5a_step_exposure_diagnostics():
    e = _r5a("A6-local-lean", seed=3, steps=300)
    seen = 0
    for t in range(300):
        if t in (50, 150):                                          # forced vacancies (rare otherwise)
            for v in (30, 31, 100, 200):
                e.occ[v] = False; e.h[v] = 0; e.ids[v] = -1; e.parent_ids[v] = -1; e.ages[v] = 0
                e.lineage[v] = -1; e.S[v] = e.D[v] = e.Db[v] = 0
        occ0 = e.occ.copy()
        e.step()
        ex = e.exposure_mask(e.last_harvest, e._r_pre_forage, occ0)
        d = e.last_diag
        assert d["n_exposed"] == int(ex.sum()) and d["frac_exposed"] == pytest.approx(ex.sum() / occ0.sum())
        near = occ0 & (e.forage_grid & ~occ0[None, :]).any(axis=1)
        assert d["n_near_empty"] == int(near.sum())
        seen += d["n_near_empty"]
        assert (e.r >= 0).all()
    assert seen > 0


def test_r5a_runner_pools_exposure(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import ForagingEngine
    m, u = c.r5a_arms(1)["A6-local-lean"]
    monkeypatch.setattr(r, "K1_DIAG_FROM", 100)
    # every occupant exposed in every step: the pooled numerator must equal the window's occupant-steps exactly
    monkeypatch.setattr(ForagingEngine, "exposure_mask", staticmethod(lambda g, r_pre, occ: occ.copy()))
    row_all = r.run_one(("A6-local-lean", m, u, 0, 400))
    assert row_all["n_exposed"] == row_all["n_occ_start"] > 0
    monkeypatch.undo()
    monkeypatch.setattr(r, "K1_DIAG_FROM", 100)
    row = r.run_one(("A6-local-lean", m, u, 0, 400))
    eng = _r5a("A6-local-lean", seed=0, steps=400)
    ne = nn = no = 0
    for t in range(400):
        eng.step()
        if t >= 100:
            ne += eng.last_diag["n_exposed"]; nn += eng.last_diag["n_near_empty"]; no += eng.last_diag["n_occ_start"]
    assert row["n_exposed"] == ne and row["n_near_empty"] == nn and row["n_occ_start"] == no


def test_r5a_pilot_decision_rule():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r5a_pilot as p
    E = lambda n_occ, n_exp: p.exposure([{"n_occ_start": n_occ, "n_exposed": n_exp, "n_near_empty": 0}])
    assert p.decide({"a": E(1000, 19), "b": E(1000, 5)})["decision"] == "below the pilot exposure threshold"
    assert p.decide({"a": E(1000, 19), "b": E(1000, 21)})["decision"] == "pilot passed"
    assert p.decide({"a": E(1000, 20), "b": E(1000, 0)})["main_run"] is True           # exactly at the bar passes
    assert p.decide({"a": E(0, 0), "b": E(1000, 50)})["decision"] == "void arm: decided with the user"
    pooled = p.exposure([{"n_occ_start": 100, "n_exposed": 10, "n_near_empty": 1},
                         {"n_occ_start": 900, "n_exposed": 0, "n_near_empty": 2}])
    assert pooled["exposure"] == 0.01 and pooled["near_empty"] == 3                   # pooled, not mean of rates


def test_r5a_pilot_runner(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r5a_pilot as p
    seen = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            seen.extend(jobs)
            return [{"arm": a, "seed": s, "final_mean_trait": 0.8, "final_occupancy": 0.99,
                     "n_occ_start": 1000, "n_exposed": 15 if a == "A6-local-lean" else 1, "n_near_empty": 4,
                     "occupancy": 0.99} for a, _, _, s, n in jobs]

    monkeypatch.setattr(p, "Pool", FakePool)
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    p.main()
    assert [(j[0], j[3], j[4]) for j in seen] == [("A6-local", 0, 6000), ("A6-local", 1, 6000),
                                                  ("A6-local-lean", 0, 6000), ("A6-local-lean", 1, 6000)]
    v = json.loads((tmp_path / "r5a_pilot_verdict.json").read_text())
    assert v["exposure"]["A6-local-lean"]["exposure"] == 0.015 and v["exposure"]["A6-local"]["exposure"] == 0.001
    assert v["decision"] == "below the pilot exposure threshold" and v["main_run"] is False and v["w_own"] == 0.2


def test_r5a_exposure_cutoff_is_strict_with_tolerance():
    """Full lattice on stock 0.15, one neighbour at 0.10 / 0.09 / 0.11: the focal harvest is 0.14 (difference exactly
    0.01: not exposed), 0.138 (exposed), 0.142 (not exposed)."""
    e = _r5a("A6-local")
    i = 4 * e.width + 4
    occ = np.ones(e.n_sites, dtype=bool)
    for nb_stock, g_exp, exposed in ((0.10, 0.14, False), (0.09, 0.138, True), (0.11, 0.142, False)):
        r = np.full(e.n_sites, 0.15); r[i + 1] = nb_stock
        e.r = r.copy()
        g = e.harvest(occ)
        assert g[i] == pytest.approx(g_exp)
        assert bool(e.exposure_mask(g, r, occ)[i]) is exposed


def test_r5a_global_arm_forages_on_the_grid():
    """Global settlement redraws the lottery pools; foraging still uses the fixed torus grid."""
    e = _r5a("A6-global", seed=2, steps=50)
    for _ in range(5):
        e.step()
    W, H = e.width, e.height
    grid = np.zeros((e.n_sites, e.n_sites), dtype=bool)
    for y in range(H):
        for x in range(W):
            i = y * W + x
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                grid[i, ((y + dy) % H) * W + (x + dx) % W] = True
    assert np.array_equal(e.forage_grid, grid)
    rng = np.random.default_rng(3)
    occ = rng.random(e.n_sites) < 0.8
    r = rng.uniform(0.0, 0.3, e.n_sites)
    e.r = r.copy()
    g1 = e.harvest(occ)
    e.neighbor_indices = e.draw_candidates()                          # new random pools: no effect on foraging
    e.r = r.copy()
    g2 = e.harvest(occ)
    g_ref, _ = _forage_reference(occ, r, grid, 0.2)
    assert np.array_equal(g1, g2) and np.allclose(g1, g_ref, atol=1e-14)


# ---------------------------------------------------------------- Step R6 (parent-paid endowment)
def _r6(name, q=1.0, attempt=1, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r6_arms(q, attempt)[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r6_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import ParentPaidEngine
    a1, a2 = c.r6_arms(1.0, 1), c.r6_arms(0.5, 2)
    assert sorted(a1) == sorted(["T3-local", "T6-local", "T12-local", "T24-local", "TN6-local", "T-below",
                                 "T6-global", "T12-global", "T6-local-lean", "T6-global-lean"])
    assert sorted(a2) == sorted(["T2-3-local", "T2-6-local", "T2-12-local", "T2-24-local", "T2-N6-local",
                                 "T2-below", "T2-6-global", "T2-12-global"])
    r4 = c.r4_arms(1)
    for name, (m, u) in a1.items():
        src = "G-below" if name == "T-below" else "G" + name[1:]
        assert m == {**r4[src][0], "care_g_start": 0.75, "care_parent_pay": 1.0} and u == r4[src][1]
    for name, (m, u) in a2.items():
        assert m["care_gamma"] == 0.15 and m["care_parent_pay"] == 0.5 and m["care_g_start"] == 0.75
    p = c.r6_pilot_arms()
    assert list(p) == ["T6-local-q1", "T6-local-q0.5"]
    assert p["T6-local-q1"] == a1["T6-local"] and p["T6-local-q0.5"] == c.r6_arms(0.5, 1)["T6-local"]
    mde = c.dr4_arms()["D-E"]
    assert {k: v for k, v in p["T6-local-q1"][0].items() if k != "care_parent_pay"} == mde[0]
    assert p["T6-local-q1"][1] == mde[1]
    e = _r6("T6-local")
    assert isinstance(e, ParentPaidEngine) and e.parent_pay == 1.0 and e.g_start == 0.75 and (e.G == 0.75).all()
    with pytest.raises(ValueError):
        _r4("G6-local", mech_over={"care_parent_pay": 1.0})            # needs care_g_start
    with pytest.raises(ValueError):
        _r6("T6-local", mech_over={"care_parent_pay": 1.5})


def test_r6_q_zero_equals_d_e():
    t = _r6("T6-local", seed=5, steps=300, mech_over={"care_parent_pay": 0.0})
    d = _dr4("D-E", seed=5, steps=300)
    for _ in range(300):
        t.step(); d.step()
        for x in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D", "Db", "occ", "last_W", "G", "r"):
            assert np.array_equal(getattr(t, x), getattr(d, x)), x
    for k in ("rng", "death_rng", "global_rng"):
        assert getattr(t, k).bit_generator.state == getattr(d, k).bit_generator.state, k


@pytest.mark.parametrize("q", [1.0, 0.5])
def test_r6_payment_equals_higher_birth_cost(q):
    """Paying q E from G gives the same dynamics as birth cost 0.5 + q E in D (W within 1e-12; this seed has no
    decision flip at a cutoff or lottery boundary)."""
    t = _r6("T6-local", q=q, seed=6, steps=400)
    d = _dr4("D-E", seed=6, steps=400, mech_over={"care_birth_cost": 0.5 + q * 0.75})
    for _ in range(400):
        t.step(); d.step()
        assert np.array_equal(t.h, d.h) and np.array_equal(t.occ, d.occ) and np.array_equal(t.ids, d.ids)
        assert np.allclose(t.last_W, d.last_W, rtol=0, atol=1e-12)
        assert np.allclose(t.G - t.D, d.G - d.D, rtol=0, atol=1e-12)
    for k in ("rng", "death_rng"):
        assert getattr(t, k).bit_generator.state == getattr(d, k).bit_generator.state


def _r6_forced_birth(e, parent_dies):
    n = e.n_sites
    v = 50
    pool_v = [int(j) for j in e.neighbor_indices[v]]
    j = [p for p in pool_v if p != v][0]
    pool_j = [int(k) for k in e.neighbor_indices[j]]
    real = e.condition_score

    def forced():
        W = real()
        W[:] = 1.0
        W[pool_v + pool_j] = 0.2                                    # ineligible (theta 0.25), not starving
        W[j] = 1.0
        return W
    e.condition_score = forced
    u = np.ones(n); u[v] = 0.0
    if parent_dies:
        u[j] = 0.0
    e.death_rng = _Draws(u)
    return v, j


def test_r6_forced_surviving_parent_pays_and_can_overdraw():
    e = _r6("T6-local", q=1.0, seed=9, steps=100)
    for _ in range(20):
        e.step()
    v, j = _r6_forced_birth(e, parent_dies=False)
    e.G[j] = 0.1
    r_j = e.r[j]
    e.step()
    assert e.last_births_by_parent[j] == 1 and e.last_survivors[j]
    g = min(r_j, 0.2)
    assert e.G[j] == pytest.approx(0.8 * 0.1 + g - 0.75) and e.G[j] < 0     # overdraft allowed
    assert e.G[v] == 0.75 and e.parent_ids[v] == e.ids[j]
    assert e.last_paid[j] == 0.75 and e.last_paid.sum() == 0.75
    assert e.last_diag["paid_total"] == 0.75 and e.last_diag["births_by_dying_parents"] == 0
    e.condition_score = type(e).condition_score.__get__(e)
    e.death_rng = np.random.default_rng(1)
    prev = e.last_charged.copy()
    assert prev[j]
    occ0 = e.occ.copy()
    G_after = e.G[j]
    e.step()                                                         # the overdraft shows at the next payoff
    assert occ0[j] and e.last_G_payoff[j] == pytest.approx(0.8 * G_after + e.last_harvest[j])
    assert e.last_G_payoff[j] < 0                                    # -0.47 * 0.8 + at most 0.2
    rp = occ0 & prev
    assert e.last_diag["frac_overdraft_recent_parents"] == pytest.approx((e.last_G_payoff[rp] < 0).mean())
    assert e.last_diag["frac_overdraft_recent_parents"] > 0 and e.last_diag["n_overdraft"] >= 1


def test_r6_forced_two_births_and_dying_parent():
    for dies in (False, True):
        e = _r6("T6-local", q=0.5, seed=9, steps=100)
        for _ in range(20):
            e.step()
        v, j = _r6_forced_birth(e, parent_dies=dies)
        G_before = e.G[j]
        r_j = e.r[j]
        e.step()
        kb = e.last_births_by_parent
        if dies:
            assert kb[j] == 2 and e.last_paid.sum() == 0.0              # fills v and its own site, pays nothing
            assert e.G[j] == 0.75 and e.G[v] == 0.75                   # both newborns at E
            assert e.last_diag["births_by_dying_parents"] == 2
        else:
            assert kb[j] == 1 and e.last_paid[j] == pytest.approx(0.375)
            assert e.G[j] == pytest.approx(0.8 * G_before + min(r_j, 0.2) - 0.375)


def test_r6_overdraft_diagnostic():
    e = _r6("T6-local", q=1.0, seed=2, steps=300)
    for _ in range(60):
        prev = e.last_charged.copy()
        occ0 = e.occ.copy()
        e.step()
        rp = occ0 & prev
        exp = (e.last_G_payoff[rp] < 0).mean() if rp.any() else float("nan")
        assert e.last_diag["frac_overdraft_recent_parents"] == pytest.approx(exp, nan_ok=True)
        assert e.last_diag["n_overdraft"] == int((occ0 & (e.last_G_payoff < 0)).sum())
        assert e.last_diag["n_fill_emptied"] <= e.last_diag["n_fill_needed"]


def test_r6_runner_pools_counts(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r6_arms(1.0, 1)["T6-local"]
    monkeypatch.setattr(r, "K1_DIAG_FROM", 100)
    row = r.run_one(("T6-local", m, u, 0, 300))
    eng = _r6("T6-local", seed=0, steps=300)
    sums = {k: 0 for k in ("n_fill_needed", "n_fill_emptied", "n_births", "births_by_dying_parents", "occ")}
    paid = 0.0
    for t in range(300):
        occ0 = eng.occ.copy()
        eng.step()
        if t >= 100:
            for k in ("n_fill_needed", "n_fill_emptied", "n_births", "births_by_dying_parents"):
                sums[k] += eng.last_diag[k]
            sums["occ"] += int(occ0.sum())
            paid += eng.last_diag["paid_total"]
    for k in ("n_fill_needed", "n_fill_emptied", "n_births", "births_by_dying_parents"):
        assert row[k] == sums[k], k
    assert row["occ_site_steps"] == sums["occ"] and row["site_steps"] == 200 * eng.n_sites
    assert row["paid_total"] == pytest.approx(paid) and row["n_births"] > 0 and paid > 0
    g = _r4("G6-local", seed=0, steps=20)
    m4, u4 = c.r4_arms(1)["G6-local"]
    row4 = r.run_one(("G6-local", m4, u4, 0, 20))
    assert "n_fill_needed" not in row4 and "paid_total" not in row4


def _r6_rows(q, need, emptied, occ_steps, site_steps, final_occ=(0.99, 0.99), extinct=(0, 0), seeds=(0, 1)):
    return [{"arm": f"T6-local-q{q:g}", "seed": s, "n_fill_needed": need, "n_fill_emptied": emptied,
             "occ_site_steps": occ_steps, "site_steps": site_steps, "final_occupancy": fo, "extinct": ex}
            for s, fo, ex in zip(seeds, final_occ, extinct)]


def test_r6_pilot_selection_rule():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r6_pilot as p
    # q = 1 passes on fill failure (exactly 5%): chosen
    s = p.select({1.0: _r6_rows(1, 100, 5, 990, 1000), 0.5: _r6_rows(0.5, 100, 0, 1000, 1000)})
    assert s["chosen_q"] == 1.0 and s["levels"]["1"]["reason"] == "passed"
    assert s["levels"]["0.5"]["reason"] == "vacant space rare"
    # q = 1 not viable (one extinct seed), q = 0.5 passes on occupancy only (exactly 0.97)
    s = p.select({1.0: _r6_rows(1, 100, 50, 500, 1000, final_occ=(0.0, 0.6), extinct=(1, 0)),
                  0.5: _r6_rows(0.5, 100, 1, 970, 1000)})
    assert s["chosen_q"] == 0.5 and s["levels"]["1"]["reason"] == "not viable"
    assert s["levels"]["0.5"]["fill_failure"] == 0.01 and s["levels"]["0.5"]["window_occupancy"] == 0.97
    # final occupancy below 0.5 in one seed: not viable
    s = p.select({1.0: _r6_rows(1, 100, 50, 900, 1000, final_occ=(0.49, 0.9)), 0.5: _r6_rows(0.5, 100, 0, 999, 1000)})
    assert s["chosen_q"] is None and s["decision"] == "vacant space rare at these levels"
    # no fills needed: occupancy decides
    s = p.select({1.0: _r6_rows(1, 0, 0, 960, 1000), 0.5: _r6_rows(0.5, 0, 0, 1000, 1000)})
    assert s["levels"]["1"]["fill_failure"] is None and s["chosen_q"] == 1.0
    assert s["levels"]["0.5"]["reason"] == "vacant space rare"
    # neither viable
    s = p.select({q: _r6_rows(q, 10, 10, 10, 1000, final_occ=(0.0, 0.0), extinct=(1, 1)) for q in (1.0, 0.5)})
    assert s["chosen_q"] is None and s["decision"] == "not viable"
    # missing or duplicated seed: incomplete
    s = p.select({1.0: _r6_rows(1, 1, 1, 1, 1, final_occ=(0.9,), extinct=(0,), seeds=(0,)),
                  0.5: _r6_rows(0.5, 1, 1, 1, 1)})
    assert s["complete"] is False and s["chosen_q"] is None
    s = p.select({1.0: _r6_rows(1, 1, 1, 1, 1, seeds=(0, 0)), 0.5: _r6_rows(0.5, 1, 1, 1, 1)})
    assert s["complete"] is False


def test_r6_pilot_runner_writes_selection_without_h(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r6_pilot as p
    seen = []

    class FakePool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            seen.extend(jobs)
            out = []
            for a, _, _, s, n in jobs:
                q1 = a.endswith("q1")
                out.append({"arm": a, "seed": s, "final_mean_trait": 0.77, "n_fill_needed": 1000,
                            "n_fill_emptied": 80 if q1 else 10, "occ_site_steps": 980, "site_steps": 1000,
                            "final_occupancy": 0.98, "extinct": 0, "n_births": 100, "births_by_dying_parents": 10,
                            "paid_total": 67.5, "births_per_occupant": 0.1})
            return out

    monkeypatch.setattr(p, "Pool", FakePool)
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    p.main()
    assert sorted((j[0], j[3], j[4]) for j in seen) == sorted(
        [(f"T6-local-q{q}", s, 6000) for q in ("1", "0.5") for s in (0, 1)])
    sel = json.loads((tmp_path / "r6_pilot_selection.json").read_text())
    assert sel["chosen_q"] == 1.0 and "0.77" not in json.dumps(sel) and "final_h" not in json.dumps(sel)
    v = json.loads((tmp_path / "r6_pilot_verdict.json").read_text())
    assert v["chosen_q"] == 1.0 and v["after_selection_descriptive"]["1"]["final_h_per_seed"] == [0.77, 0.77]
    assert v["after_selection_descriptive"]["1"]["paid_per_birth"] == pytest.approx(0.675)


def test_r6_surviving_parent_two_births_pays_twice():
    e = _r6("T6-local", q=0.5, seed=9, steps=100)
    for _ in range(20):
        e.step()
    n = e.n_sites
    j = 50
    nb = [int(x) for x in e.neighbor_indices[j] if x != j]
    v, w = nb[0], nb[1]                                              # two neighbours of j die; only j eligible
    pools = [int(x) for site in (v, w) for x in e.neighbor_indices[site]]
    real = e.condition_score

    def forced():
        W = real()
        W[:] = 1.0
        W[pools] = 0.2
        W[j] = 1.0
        return W
    e.condition_score = forced
    u = np.ones(n); u[[v, w]] = 0.0
    e.death_rng = _Draws(u)
    G0, r0 = e.G[j], e.r[j]
    e.step()
    assert e.last_births_by_parent[j] == 2 and e.last_survivors[j]
    assert e.last_paid[j] == pytest.approx(2 * 0.375) and e.last_diag["paid_total"] == pytest.approx(0.75)
    assert e.G[j] == pytest.approx(0.8 * G0 + min(r0, 0.2) - 0.75)
    assert e.G[v] == 0.75 and e.G[w] == 0.75


def test_r6_fill_counts_include_already_empty_sites():
    e = _r6("T6-local", seed=4, steps=100)
    for _ in range(10):
        e.step()
    v = 70
    pool = [int(x) for x in e.neighbor_indices[v]]
    e.occ[v] = False; e.h[v] = 0; e.ids[v] = -1; e.parent_ids[v] = -1; e.ages[v] = 0
    e.lineage[v] = -1; e.S[v] = e.D[v] = e.Db[v] = 0
    real = e.condition_score

    def low():
        W = real(); W[pool] = 0.1                                    # nobody in v's pool eligible
        return W
    e.condition_score = low
    u = np.ones(e.n_sites)
    e.death_rng = _Draws(u)
    e.step()
    d = e.last_diag
    assert d["n_fill_needed"] >= 1 and d["n_fill_emptied"] >= 1 and not e.occ[v]
    starving = int(e.last_starved.sum())
    assert d["n_fill_needed"] == 1 + starving                         # the already-empty site counts as needed


def test_r6_pilot_unequal_denominators_pool_counts():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r6_pilot as p
    rows = [{"arm": "T6-local-q1", "seed": 0, "n_fill_needed": 10, "n_fill_emptied": 5, "occ_site_steps": 100,
             "site_steps": 100, "final_occupancy": 0.99, "extinct": 0},
            {"arm": "T6-local-q1", "seed": 1, "n_fill_needed": 990, "n_fill_emptied": 0, "occ_site_steps": 900,
             "site_steps": 900, "final_occupancy": 0.99, "extinct": 0}]
    o = p.level_outcome(rows)
    assert o["fill_failure"] == 5 / 1000 and o["reason"] == "vacant space rare"     # mean of rates would be 25%
    s = p.select({1.0: rows})                                        # a level missing: incomplete
    assert s["complete"] is False and s["chosen_q"] is None
    s = p.select({1.0: rows, 0.5: rows, 2.0: rows})                  # an unexpected level: incomplete
    assert s["complete"] is False


def test_r6_pilot_fails_closed_and_writes_selection_before_h(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r6_pilot as p
    (tmp_path / "r6_pilot_selection.json").write_text(json.dumps({"complete": True, "chosen_q": 1.0}))
    (tmp_path / "r6_pilot_verdict.json").write_text("{}")

    class FailPool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs): raise RuntimeError("worker failed")

    monkeypatch.setattr(p, "Pool", FailPool)
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    with pytest.raises(RuntimeError):
        p.main()
    sel = json.loads((tmp_path / "r6_pilot_selection.json").read_text())
    assert sel["complete"] is False and sel["chosen_q"] is None and not (tmp_path / "r6_pilot_verdict.json").exists()

    class OkPool(FailPool):
        def map(self, f, jobs):
            return [{"arm": a, "seed": s, "final_mean_trait": 0.77, "n_fill_needed": 1000, "n_fill_emptied": 80,
                     "occ_site_steps": 980, "site_steps": 1000, "final_occupancy": 0.98, "extinct": 0,
                     "n_births": 100, "births_by_dying_parents": 10, "paid_total": 67.5}
                    for a, _, _, s, n in jobs]

    order = []
    real_csv = p.write_union_csv

    def csv_spy(path, rows):
        sel_now = json.loads((tmp_path / "r6_pilot_selection.json").read_text())
        order.append(("csv", sel_now["complete"], (tmp_path / "r6_pilot_verdict.json").exists()))
        real_csv(path, rows)

    monkeypatch.setattr(p, "Pool", OkPool)
    monkeypatch.setattr(p, "write_union_csv", csv_spy)
    p.main()
    assert order == [("csv", True, False)]                           # selection final before h is written anywhere


# ---------------------------------------------------------------- Step R7 (juveniles cannot breed)
def _r7(name, a_b=2, attempt=1, seed=8, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r7_arms(a_b, attempt)[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def _income_g075(r4_name, seed, steps):
    return _r4(r4_name, seed=seed, steps=steps, mech_over={"care_g_start": 0.75})


def test_r7_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import BreedingAgeEngine
    a1, a2 = c.r7_arms(2, 1), c.r7_arms(1, 2)
    assert sorted(a1) == sorted(["J3-local", "J6-local", "J12-local", "J24-local", "JN6-local", "J-below",
                                 "J6-global", "J12-global", "J6-local-lean", "J6-global-lean"])
    assert sorted(a2) == sorted(["J2-3-local", "J2-6-local", "J2-12-local", "J2-24-local", "J2-N6-local",
                                 "J2-below", "J2-6-global", "J2-12-global"])
    r4 = c.r4_arms(1)
    for name, (m, u) in a1.items():
        src = "G-below" if name == "J-below" else "G" + name[1:]
        assert m == {**r4[src][0], "care_g_start": 0.75, "care_breed_age": 2} and u == r4[src][1]
    assert all(m["care_breed_age"] == 1 and m["care_gamma"] == 0.15 for m, _ in a2.values())
    p = c.r7_pilot_arms()
    assert list(p) == ["J6-local-a2", "J6-local-a1"] and p["J6-local-a2"] == a1["J6-local"]
    mde = c.dr4_arms()["D-E"]
    assert {k: v for k, v in p["J6-local-a2"][0].items() if k != "care_breed_age"} == mde[0]
    e = _r7("J6-local")
    assert isinstance(e, BreedingAgeEngine) and e.breed_age == 2 and (e.G == 0.75).all()
    for args in ((1.9, 1), (2, 2), (3, 1), (True, 1)):
        with pytest.raises(ValueError):
            c.r7_arms(*args)
    for bad in ({"care_breed_age": -1}, {"care_breed_age": 1.5}, {"care_parent_pay": 0.5}):
        with pytest.raises(ValueError):
            _r7("J6-local", mech_over=bad)
    with pytest.raises(ValueError):
        _r4("G6-local", mech_over={"care_breed_age": 2})               # needs care_g_start


@pytest.mark.parametrize("pair", [("J6-local", "G6-local"), ("J6-global", "G6-global"), ("JN6-local", "GN6-local")])
def test_r7_breed_age_zero_reproduces_matched_income_arm(pair):
    j_name, g_name = pair
    j = _r7(j_name, seed=5, steps=300, mech_over={"care_breed_age": 0})
    g = _income_g075(g_name, seed=5, steps=300)
    for _ in range(300):
        j.step(); g.step()
        for x in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D", "Db", "occ", "last_W", "G", "r"):
            assert np.array_equal(getattr(j, x), getattr(g, x)), x
    for k in ("rng", "death_rng", "global_rng"):
        assert getattr(j, k).bit_generator.state == getattr(g, k).bit_generator.state, k
    if j_name == "J6-local":
        d = _dr4("D-E", seed=5, steps=300)
        for _ in range(300):
            d.step()
        assert np.array_equal(d.h, j.h) and np.array_equal(d.occ, j.occ)


@pytest.mark.parametrize("a_b", [2, 1])
def test_r7_no_birth_by_a_too_young_parent(a_b):
    e = _r7("J6-local", a_b=a_b, seed=3, steps=400)
    births = 0
    for _ in range(400):
        age0 = e.ages.copy()
        e.step()
        kb = e.last_births_by_parent
        assert (kb[age0 < a_b] == 0).all()
        births += int(kb.sum())
    assert births > 0


def _r7_forced_pool(e, cand_age, cand_dies=False):
    """Site v dies; its only candidate with W >= theta is neighbour j, of age cand_age."""
    n = e.n_sites
    v = next(i for i in range(n) if e.occ[e.neighbor_indices[i]].all())   # a fully occupied pool
    pool_v = [int(x) for x in e.neighbor_indices[v]]
    j = [x for x in pool_v if x != v][0]
    if e.global_candidates:                    # global pools are redrawn in the step: keep the draw, force v's pool
        orig = type(e).draw_candidates.__get__(e)

        def draw():
            pools = orig()
            pools[v] = np.array(pool_v, dtype=np.int32)
            return pools
        e.draw_candidates = draw
    real = e.condition_score

    def forced():
        W = real()
        W[:] = 1.0
        W[pool_v] = 0.1                                                # ineligible by W, not starving
        W[j] = 1.0
        return W
    e.condition_score = forced
    e.ages[j] = cand_age
    for x in pool_v:
        if x != j:
            e.ages[x] = 5
    u = np.ones(n); u[v] = 0.0
    if cand_dies:
        u[j] = 0.0
    e.death_rng = _Draws(u)
    return v, j


@pytest.mark.parametrize("a_b,age,fills", [(1, 1, True), (1, 0, False), (2, 1, False), (2, 2, True), (0, 0, True)])
def test_r7_age_boundary_and_age_blocked(a_b, age, fills):
    e = _r7("J6-local", a_b=2, seed=9, steps=200, mech_over={"care_breed_age": a_b})
    for _ in range(80):
        e.step()
    v, j = _r7_forced_pool(e, age)
    e.step()
    assert bool(e.occ[v]) is fills
    if fills:
        assert e.last_births_by_parent[j] >= 1 and e.parent_ids[v] != -1
    else:
        assert e.last_vac[v] and e.last_diag["n_fill_age_blocked"] >= 1


def test_r7_dying_adult_can_parent():
    e = _r7("J6-local", a_b=2, seed=9, steps=200)
    for _ in range(80):
        e.step()
    v, j = _r7_forced_pool(e, 4, cand_dies=True)
    old_id = e.ids[j]
    e.step()
    assert e.occ[v] and e.parent_ids[v] == old_id and not e.last_survivors[j]


@pytest.mark.parametrize("name", ["J6-local", "J6-global"])
def test_r7_age_blocked_pool_keeps_streams(name):
    """A fill that fails because the candidate is too young makes the same draws as one that fails by W."""
    a = _r7(name, a_b=2, seed=9, steps=200)
    b = _r7(name, a_b=2, seed=9, steps=200)
    c = _r7(name, a_b=2, seed=9, steps=200)                              # unforced reference for the draw count
    for _ in range(80):
        a.step(); b.step(); c.step()
    assert np.array_equal(a.occ, b.occ)
    va, ja = _r7_forced_pool(a, 0)                                       # j blocked by age (W high)
    vb, jb = _r7_forced_pool(b, 5)                                       # j old enough, blocked by W
    assert (va, ja) == (vb, jb)
    real_b = b.condition_score

    def by_w():
        W = real_b(); W[jb] = 0.1
        return W
    b.condition_score = by_w
    a.step(); b.step(); c.step()
    assert list(a.neighbor_indices[va]) == list(b.neighbor_indices[vb])   # the forced pool was the one used
    assert ja in list(a.neighbor_indices[va])
    assert not a.occ[va] and not b.occ[vb] and a.last_vac[va] and a.last_diag["n_fill_age_blocked"] >= 1
    # every site made its lottery draw (same rng advance as an unforced step), the failed fill included
    assert a.rng.bit_generator.state == c.rng.bit_generator.state
    assert np.array_equal(a.occ, b.occ) and np.array_equal(a.h, b.h)
    for k in ("rng", "global_rng"):                                      # death draws are forced in both
        assert getattr(a, k).bit_generator.state == getattr(b, k).bit_generator.state, k
    for k in ("rng", "genome_rng"):
        if hasattr(a.mechanism, k):
            assert getattr(a.mechanism, k).bit_generator.state == getattr(b.mechanism, k).bit_generator.state


def test_r7_diagnostics_and_runner_export(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    e = _r7("J6-local", seed=1, steps=200)
    for _ in range(60):
        occ0, age0 = e.occ.copy(), e.ages.copy()
        e.step()
        d = e.last_diag
        kb = e.last_births_by_parent
        assert d["births_adult_sum"] + d["births_juvenile_sum"] == kb.sum() == d["n_births_age"]
        assert d["births_juvenile_sum"] == 0                            # a_b = 2 = care-juvenile period
        assert d["n_adult"] == int((occ0 & (age0 >= 2)).sum())
        assert d["parent_age_sum"] == int((kb * age0).sum())
        assert d["n_fill_age_blocked"] <= d["n_fill_emptied"]
        empty = ~e.occ
        assert d["n_empty_end"] == int(empty.sum())
    m, u = c.r7_arms(2, 1)["J6-local"]
    monkeypatch.setattr(r, "K1_DIAG_FROM", 50)
    row = r.run_one(("J6-local", m, u, 0, 150))
    for k in (*r.FILL_KEYS, *r.AGE_KEYS, "occ_site_steps", "site_steps"):
        assert k in row, k
    assert row["site_steps"] == 100 * 576 and "paid_total" not in row


def _r7_rows(a_b, need, emptied, occ_steps, site_steps, final_occ=(0.99, 0.99), extinct=(0, 0), seeds=(0, 1)):
    return [{"arm": f"J6-local-a{a_b}", "seed": s, "n_fill_needed": need, "n_fill_emptied": emptied,
             "occ_site_steps": occ_steps, "site_steps": site_steps, "final_occupancy": fo, "extinct": ex}
            for s, fo, ex in zip(seeds, final_occ, extinct)]


def test_r7_pilot_selection_rule():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r7_pilot as p
    s = p.select(_r7_rows(2, 100, 5, 990, 1000) + _r7_rows(1, 100, 0, 1000, 1000))
    assert s["chosen_a_b"] == 2 and s["levels"]["1"]["reason"] == "vacant space rare"
    s = p.select(_r7_rows(2, 100, 50, 500, 1000, final_occ=(0.0, 0.6), extinct=(1, 0))
                 + _r7_rows(1, 100, 1, 970, 1000))
    assert s["chosen_a_b"] == 1 and s["levels"]["2"]["reason"] == "not viable"
    s = p.select(_r7_rows(2, 0, 0, 960, 1000) + _r7_rows(1, 100, 0, 999, 1000))
    assert s["chosen_a_b"] == 2 and s["levels"]["2"]["fill_failure"] is None
    s = p.select(_r7_rows(2, 100, 1, 999, 1000) + _r7_rows(1, 100, 1, 999, 1000))
    assert s["chosen_a_b"] is None and s["decision"] == "vacant space rare at these levels"
    s = p.select(_r7_rows(2, 1, 1, 1, 1000, final_occ=(0, 0), extinct=(1, 1))
                 + _r7_rows(1, 1, 1, 1, 1000, final_occ=(0, 0), extinct=(1, 1)))
    assert s["decision"] == "not viable"
    for rows in (_r7_rows(2, 1, 1, 1, 1, seeds=(0,), final_occ=(0.9,), extinct=(0,)) + _r7_rows(1, 1, 1, 1, 1),
                 _r7_rows(2, 1, 1, 1, 1) + _r7_rows(1, 1, 1, 1, 1) + _r7_rows(3, 1, 1, 1, 1),
                 _r7_rows(2, 1, 1, 1, 1, seeds=(0, 0)) + _r7_rows(1, 1, 1, 1, 1)):
        s = p.select(rows)
        assert s["complete"] is False and s["chosen_a_b"] is None


def test_r7_pilot_fails_closed_and_writes_selection_before_h(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r7_pilot as p
    (tmp_path / "r7_pilot_selection.json").write_text(json.dumps({"complete": True, "chosen_a_b": 2}))
    (tmp_path / "r7_pilot_verdict.json").write_text("{}")
    (tmp_path / "r7_pilot_runs.csv").write_text("arm,seed,final_mean_trait\nx,0,0.9\n")

    class FailPool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs): raise RuntimeError("worker failed")

    monkeypatch.setattr(p, "Pool", FailPool)
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    with pytest.raises(RuntimeError):
        p.main()
    sel = json.loads((tmp_path / "r7_pilot_selection.json").read_text())
    assert sel["complete"] is False and sel["chosen_a_b"] is None and not (tmp_path / "r7_pilot_verdict.json").exists()
    assert not (tmp_path / "r7_pilot_runs.csv").exists()
    seen = []

    class OkPool(FailPool):
        def map(self, f, jobs):
            seen.extend(jobs)
            return [{"arm": a, "seed": s, "final_mean_trait": 0.77, "n_fill_needed": 1000,
                     "n_fill_emptied": 80 if a.endswith("a2") else 10, "occ_site_steps": 980, "site_steps": 1000,
                     "final_occupancy": 0.98, "extinct": 0, "n_fill_age_blocked": 40, "births_adult_sum": 50,
                     "n_adult": 500, "births_juvenile_sum": 0, "n_juvenile": 200, "parent_age_sum": 300,
                     "n_births_age": 50, "empty_nb_sum": 30, "n_empty_end": 20} for a, _, _, s, n in jobs]

    order = []
    real_csv = p.write_union_csv

    def csv_spy(path, rows):
        sel_now = json.loads((tmp_path / "r7_pilot_selection.json").read_text())
        order.append((sel_now["complete"], (tmp_path / "r7_pilot_verdict.json").exists()))
        real_csv(path, rows)

    monkeypatch.setattr(p, "Pool", OkPool)
    monkeypatch.setattr(p, "write_union_csv", csv_spy)
    p.main()
    assert order == [(True, False)]
    assert sorted((j[0], j[3], j[4]) for j in seen) == sorted(
        [(f"J6-local-a{a}", s, 6000) for a in (2, 1) for s in (0, 1)])
    sel = json.loads((tmp_path / "r7_pilot_selection.json").read_text())
    assert sel["chosen_a_b"] == 2 and "0.77" not in json.dumps(sel)
    v = json.loads((tmp_path / "r7_pilot_verdict.json").read_text())
    assert v["after_selection_descriptive"]["2"]["age_blocked_share_of_failed_fills"] == 0.5
    assert v["after_selection_descriptive"]["2"]["mean_parent_age"] == 6.0


def test_r7_pilot_more_cases():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r7_pilot as p
    s = p.select(_r7_rows(2, 100, 10, 900, 1000) + _r7_rows(1, 100, 10, 900, 1000))     # both pass: 2 chosen
    assert s["chosen_a_b"] == 2 and s["levels"]["1"]["reason"] == "passed"
    s = p.select(_r7_rows(2, 100, 10, 900, 1000, final_occ=(0.5, 0.9)) + _r7_rows(1, 100, 0, 1000, 1000))
    assert s["levels"]["2"]["viable"] and s["chosen_a_b"] == 2                         # 0.50 is viable
    rows = [{"arm": "J6-local-a2", "seed": 0, "n_fill_needed": 10, "n_fill_emptied": 5, "occ_site_steps": 100,
             "site_steps": 100, "final_occupancy": 0.99, "extinct": 0},
            {"arm": "J6-local-a2", "seed": 1, "n_fill_needed": 990, "n_fill_emptied": 0, "occ_site_steps": 990,
             "site_steps": 1000, "final_occupancy": 0.99, "extinct": 0}]
    s = p.select(rows + _r7_rows(1, 100, 0, 1000, 1000))
    assert s["levels"]["2"]["fill_failure"] == 0.005 and s["levels"]["2"]["window_occupancy"] == 1090 / 1100
    bad = _r7_rows(2, 1, 1, 1, 1) + _r7_rows(1, 1, 1, 1, 1)
    bad[1] = {**bad[1], "seed": 0.9}
    assert p.select(bad)["complete"] is False


# ---------------------------------------------------------------- Step R7b (adult founders)
def _r7b(name, attempt=1, seed=20, steps=5, mech_over=None, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r7b_arms(attempt)[name]
    m = {**m, **(mech_over or {})}
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r7b_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    a1, a2 = c.r7b_arms(1), c.r7b_arms(2)
    assert sorted(a1) == sorted(["B3-local", "B6-local", "B12-local", "B24-local", "BN6-local", "B-below",
                                 "B6-global", "B12-global", "B6-local-lean", "B6-global-lean"])
    assert sorted(a2) == sorted(["B2-3-local", "B2-6-local", "B2-12-local", "B2-24-local", "B2-N6-local",
                                 "B2-below", "B2-6-global", "B2-12-global"])
    j1, j2 = c.r7_arms(2, 1), c.r7_arms(1, 2)
    for name, (m, u) in a1.items():
        assert m == {**j1["J" + name[1:]][0], "care_founder_age": 2} and u == j1["J" + name[1:]][1]
    for name, (m, u) in a2.items():
        assert m == {**j2["J2-" + name[3:]][0], "care_founder_age": 2} and m["care_breed_age"] == 1
    assert c.r7b_pilot_arms() == {"B6-local": a1["B6-local"]}
    assert c.R7B_PILOT_SEEDS == [20, 21] and c.R7B_MAIN_SEEDS == list(range(22, 42))
    e = _r7b("B6-local")
    assert (e.ages == 2).all() and e.founder_age == 2 and (e.parent_ids == -1).all()
    with pytest.raises(ValueError):
        _r6("T6-local", mech_over={"care_founder_age": 2})            # needs care_breed_age
    with pytest.raises(ValueError):
        _r7b("B6-local", mech_over={"care_founder_age": -1})


@pytest.mark.parametrize("pair", [("B6-local", "J6-local"), ("B6-global", "J6-global"), ("BN6-local", "JN6-local")])
def test_r7b_founder_age_zero_is_r7(pair):
    b_name, j_name = pair
    b = _r7b(b_name, seed=5, steps=300, mech_over={"care_founder_age": 0})
    j = _r7(j_name, a_b=2, seed=5, steps=300)
    for _ in range(300):
        b.step(); j.step()
        for x in ("h", "lineage", "ids", "parent_ids", "ages", "S", "D", "Db", "occ", "last_W", "G", "r"):
            assert np.array_equal(getattr(b, x), getattr(j, x)), x
    for k in ("rng", "death_rng", "global_rng"):
        assert getattr(b, k).bit_generator.state == getattr(j, k).bit_generator.state, k


@pytest.mark.parametrize("name", ["B6-local", "B6-global", "BN6-local", "B6-local-lean"])
def test_r7b_first_update_all_founders_eligible_every_fill_succeeds(name):
    e = _r7b(name, seed=21, steps=10)
    e.step()
    assert np.array_equal(e.last_eligible, np.ones(e.n_sites, dtype=bool))
    assert e.last_diag["n_fill_emptied"] == 0 and e.last_diag["n_fill_needed"] > 0 and e.occ.all()
    assert e.last_W.min() >= 0.6 - 1e-12 and e.last_W.max() <= 0.8 + 1e-12
    z = _r7(name.replace("B", "J", 1), a_b=2, seed=21, steps=10)       # R7: founders age 0 cannot breed
    z.step()
    assert not z.last_eligible.any() and z.last_diag["n_fill_emptied"] == z.last_diag["n_fill_needed"]


def test_r7b_control_founder_care_differs_by_founder_age():
    adult = _r7b("BN6-local", seed=3, steps=10)
    young = _r7b("BN6-local", seed=3, steps=10, mech_over={"care_founder_age": 0})
    adult.step(); young.step()
    s_a, s_y = adult.last_survivors, young.last_survivors
    assert (adult.S[s_a] == 0).all()                                  # age-2 founders are not young neighbours
    assert (young.S[s_y] > 0).any()                                   # age-0 founders receive first-payoff care
    own = _r7b("B6-local", seed=3, steps=10)
    own.step()
    assert (own.S[own.last_survivors] == 0).all()                     # founders have no living parent


def test_r7b_newborn_breeding_ages_both_attempts():
    e = _r7b("B6-local", seed=20, steps=300)
    for _ in range(300):
        age0 = e.ages.copy()
        e.step()
        assert (e.last_births_by_parent[age0 < 2] == 0).all()
    f = _r7b("B2-6-local", attempt=2, seed=20, steps=300)
    juv_births = 0
    for _ in range(300):
        age0, occ0 = f.ages.copy(), f.occ.copy()
        f.step()
        kb = f.last_births_by_parent
        assert (kb[age0 < 1] == 0).all()
        juv_births += int(kb[occ0 & (age0 == 1)].sum())               # age-1 juveniles breed
    assert juv_births > 0
    g = _r7b("B2-6-local", attempt=2, seed=9, steps=200)
    for _ in range(80):
        g.step()
    v, j = _r7_forced_pool(g, 1)
    g.step()
    assert g.occ[v] and g.last_births_by_parent[j] >= 1               # an age-1 candidate fills at a_b = 1


def test_r7b_runner_startup_and_first_empty(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import BreedingAgeEngine
    m, u = c.r7b_arms(1)["B6-local"]
    row = r.run_one(("B6-local", m, u, 20, 120))
    e = _r7b("B6-local", seed=20, steps=120)
    occ = {}
    for t in range(1, 121):
        e.step()
        if t in (10, 50, 100):
            occ[t] = float(e.occ.mean())
    for t in (10, 50, 100):
        assert row[f"occ_after_{t}"] == occ[t]
    assert np.isnan(row["occ_after_500"]) and row["first_empty_update"] == -1
    real = BreedingAgeEngine.step

    def emptying(self):
        out = real(self)
        if self.step_index == 7:
            self.occ[:] = False
        return out
    monkeypatch.setattr(BreedingAgeEngine, "step", emptying)
    row = r.run_one(("B6-local", m, u, 20, 20))
    assert row["first_empty_update"] == 7 and row["extinct"] == 1


def _r7b_rows(need, emptied, occ_steps, site_steps, final_occ=(0.99, 0.99), extinct=(0, 0), seeds=(20, 21)):
    return [{"arm": "B6-local", "seed": s, "n_fill_needed": need, "n_fill_emptied": emptied,
             "occ_site_steps": occ_steps, "site_steps": site_steps, "final_occupancy": fo, "extinct": ex}
            for s, fo, ex in zip(seeds, final_occ, extinct)]


def test_r7b_pilot_rule():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r7b_pilot as p
    s = p.select(_r7b_rows(100, 5, 990, 1000), 1000)
    assert s["passed"] is True and s["decision"] == "pilot passed: main run"
    s = p.select(_r7b_rows(100, 1, 970, 1000), 1000)
    assert s["passed"] is True                                         # occupancy path, inclusive
    s = p.select(_r7b_rows(100, 1, 999, 1000), 1000)
    assert s["passed"] is False and s["decision"] == "vacant space rare"
    s = p.select(_r7b_rows(100, 50, 500, 1000, final_occ=(0.0, 0.9), extinct=(1, 0)), 1000)
    assert s["passed"] is False and s["decision"] == "not viable"
    for rows in (_r7b_rows(1, 1, 1, 1, seeds=(20,), final_occ=(0.9,), extinct=(0,)),
                 _r7b_rows(1, 1, 1, 1, seeds=(0, 1)), _r7b_rows(1, 1, 1, 1, seeds=(20, 20)),
                 _r7b_rows(1, 1, 1, 1) + _r7b_rows(1, 1, 1, 1, seeds=(22,), final_occ=(0.9,), extinct=(0,)),
                 [{**x, "seed": 20.5} if i == 0 else x for i, x in enumerate(_r7b_rows(1, 1, 1, 1))]):
        s = p.select(rows, 1)
        assert s["complete"] is False and s["passed"] is None
    assert p.select(_r7b_rows(100, 5, 990, 1000), 5000 * 576)["complete"] is False      # short window
    assert p.EXPECTED_SITE_STEPS == 5000 * 576


def test_r7b_pilot_fails_closed_and_decides_before_h(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r7b_pilot as p
    (tmp_path / "r7b_pilot_selection.json").write_text(json.dumps({"complete": True, "passed": True}))
    (tmp_path / "r7b_pilot_verdict.json").write_text("{}")
    (tmp_path / "r7b_pilot_runs.csv").write_text("arm,seed\\nx,0\\n")

    class FailPool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs): raise RuntimeError("worker failed")

    monkeypatch.setattr(p, "Pool", FailPool)
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    with pytest.raises(RuntimeError):
        p.main()
    sel = json.loads((tmp_path / "r7b_pilot_selection.json").read_text())
    assert sel["complete"] is False and sel["passed"] is None
    assert not (tmp_path / "r7b_pilot_verdict.json").exists() and not (tmp_path / "r7b_pilot_runs.csv").exists()
    seen = []

    class OkPool(FailPool):
        def map(self, f, jobs):
            seen.extend(jobs)
            return [{"arm": a, "seed": s, "final_mean_trait": 0.77, "n_fill_needed": 1000, "n_fill_emptied": 150,
                     "occ_site_steps": 960, "site_steps": 5000 * 576, "final_occupancy": 0.96, "extinct": 0,
                     "n_fill_age_blocked": 140, "births_adult_sum": 50, "n_adult": 500, "parent_age_sum": 200,
                     "n_births_age": 50, "empty_nb_sum": 10, "n_empty_end": 20, "first_empty_update": -1,
                     **{f"occ_after_{t}": 0.9 for t in (10, 50, 100, 500)}} for a, _, _, s, n in jobs]

    order = []
    real_csv = p.write_union_csv

    def spy(path, rows):
        sel_now = json.loads((tmp_path / "r7b_pilot_selection.json").read_text())
        order.append((sel_now["complete"], (tmp_path / "r7b_pilot_verdict.json").exists()))
        real_csv(path, rows)

    monkeypatch.setattr(p, "Pool", OkPool)
    monkeypatch.setattr(p, "write_union_csv", spy)
    p.main()
    assert order == [(True, False)]
    assert [(j[0], j[3], j[4]) for j in seen] == [("B6-local", 20, 6000), ("B6-local", 21, 6000)]
    sel = json.loads((tmp_path / "r7b_pilot_selection.json").read_text())
    assert sel["passed"] is True and "0.77" not in json.dumps(sel)
    v = json.loads((tmp_path / "r7b_pilot_verdict.json").read_text())
    assert v["after_selection_descriptive"]["per_seed_fill_failure"] == [0.15, 0.15]

    class ShortPool(FailPool):                                        # one row missing: incomplete, no h written
        def map(self, f, jobs):
            return OkPool.map(self, f, jobs)[:1]
    monkeypatch.setattr(p, "Pool", ShortPool)
    p.main()
    sel = json.loads((tmp_path / "r7b_pilot_selection.json").read_text())
    assert sel["complete"] is False
    assert not (tmp_path / "r7b_pilot_verdict.json").exists() and not (tmp_path / "r7b_pilot_runs.csv").exists()
    assert v["after_selection_descriptive"]["startup_occupancy_per_seed"]["20"] == [0.9] * 4


def test_r7b_founder_and_breed_age_zero_is_income_arm():
    b = _r7b("B6-local", seed=5, steps=200, mech_over={"care_founder_age": 0, "care_breed_age": 0})
    g = _income_g075("G6-local", seed=5, steps=200)                     # a different engine class
    for _ in range(200):
        b.step(); g.step()
        for x in ("h", "ids", "ages", "S", "D", "occ", "last_W", "G", "r"):
            assert np.array_equal(getattr(b, x), getattr(g, x)), x
    for k in ("rng", "death_rng", "global_rng"):
        assert getattr(b, k).bit_generator.state == getattr(g, k).bit_generator.state, k


def test_r7b_newborns_age_zero_and_age_one_breeders_receive_care():
    f = _r7b("B2-6-local", attempt=2, seed=20, steps=300)
    cared_breeders = 0
    for _ in range(300):
        age0, occ0 = f.ages.copy(), f.occ.copy()
        f.step()
        new = f.occ & ~f.last_survivors
        assert (f.ages[new] == 0).all() and (f.parent_ids[new] >= 0).all()
        kb = f.last_births_by_parent
        bred1 = occ0 & (age0 == 1) & (kb > 0) & f.last_survivors
        cared_breeders += int((bred1 & (f.S > 0)).sum())               # payoff S kept by survivors
    assert cared_breeders > 0


def test_r7b_runner_startup_after_500():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r1 as r
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r7b_arms(1)["B6-local"]
    row = r.run_one(("B6-local", m, u, 21, 510))
    e = _r7b("B6-local", seed=21, steps=510)
    for _ in range(500):
        e.step()
    assert row["occ_after_500"] == float(e.occ.mean())


# ---------------------------------------------------------------- Step R8 (parent-driven births)
def _r8(d0=0.2, g_rep=0.5, attempt=1, dispersal="local", src="G6-local", seed=50, steps=50, **upd):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r8_base(d0, g_rep, attempt, dispersal, src)
    m = dict(m)
    return make_engine(run_config(seed, {**u, **upd}, steps), replacement=m.pop("replacement"),
                       death=m.pop("death"), **m)


def test_r8_config_and_validation():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import BuddingEngine
    m, u = c.r8_base(0.2, 0.5)
    assert m["death"] == 0.2 and m["care_g_rep"] == 0.5 and m["care_split"] is True and m["care_birth_cost"] == 0.0
    assert m["care_g_start"] == 0.75 and m["care_gamma"] == 0.15 and m["care"] == "offspring"
    m2, _ = c.r8_base(0.2, 0.5, attempt=2)
    assert m2["care_split"] is False and m2["care_birth_cost"] == 0.5
    jobs = c.r8_screen_jobs()
    assert len(jobs) == 12 and len({j[0] for j in jobs}) == 12
    for a, mm, uu, d, g, h in jobs:
        assert uu["initial_trait_mean"] == h and uu["initial_trait_stddev"] == 0.0 and uu["mutation_rate"] == 0.0
        assert mm["death"] == d and mm["care_g_rep"] == g and uu["B_plus_scale"] == 1.2
    e = _r8()
    assert isinstance(e, BuddingEngine) and (e.G == 0.75).all() and e.occ.all()
    assert e.birth_rng.bit_generator.state == np.random.default_rng(15_000_000 + 50).bit_generator.state
    with pytest.raises(ValueError):                                    # split needs birth_cost 0
        mm = {**m, "care_birth_cost": 0.5}
        make_engine(run_config(1, u, 5), replacement=mm.pop("replacement"), death=mm.pop("death"), **mm)
    with pytest.raises(ValueError):
        mm = {**m, "replacement": "global"}
        make_engine(run_config(1, u, 5), replacement=mm.pop("replacement"), death=mm.pop("death"), **mm)


def _r8_force(e, dead_sites, W=None, G=None):
    """Next step: exactly dead_sites die by the draw; optional W override and pre-harvest G values."""
    u = np.ones(e.n_sites); u[list(dead_sites)] = 0.0
    e.death_rng = _Draws(u)
    if W is not None:
        real = e.condition_score

        def forced():
            out = real(); out[:] = W(out) if callable(W) else W
            return out
        e.condition_score = forced
    if G is not None:
        e.G = G.copy()


def test_r8_two_claimants_softmax_split_and_losers():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import _local_softmax_probabilities
    e = _r8()
    v = 5 * e.width + 5
    nb = [int(x) for x in e.grid_nb[v]]
    G = np.zeros(e.n_sites); G[nb[0]] = G[nb[1]] = 1.0                 # after harvest 0.8 G + 0.2: 1.0 vs 0.2
    _r8_force(e, [v], G=G)
    D0, h0 = e.D.copy(), e.h.copy()
    rb = np.random.default_rng(); rb.bit_generator.state = e.rng.bit_generator.state
    e.step()
    assert e.last_diag["n_claimants"] == 2 and e.last_diag["n_births"] == 1 and e.occ[v]
    win = int(e.last_birth_parents[0])
    lose = nb[1] if win == nb[0] else nb[0]
    assert e.parent_ids[v] == e.ids[win] and e.ages[v] == 0 and e.S[v] == 0 and e.D[v] == 0
    assert e.lineage[v] == e.lineage[win]
    assert e.G[win] == pytest.approx(0.5) and e.G[v] == pytest.approx(0.5) and e.G[lose] == pytest.approx(1.0)
    assert e.G[win] + e.G[v] == 1.0                                    # split conserves the store exactly
    assert e.D[win] == pytest.approx(0.8 * D0[win] + 0.2 * h0[win])    # no birth cost with the split
    # replay the lottery stream: one softmax choice among the two claimants, then the mutation draws for one birth
    probs = _local_softmax_probabilities(e.last_W[np.array(sorted(nb[:2]))], 0.12)
    k = int(rb.choice(2, p=probs))
    assert sorted(nb[:2])[k] == win
    if rb.random(1)[0] < 0.02:
        rb.normal(0.0, 0.04, size=1)
    assert rb.bit_generator.state == e.rng.bit_generator.state


def test_r8_claims_rules_and_streams():
    e = _r8(seed=51)
    for _ in range(30):
        occ0, ids0 = e.occ.copy(), e.ids.copy()
        bstate = e.birth_rng.bit_generator.state
        e.step()
        W, G = e.last_W, e.last_G_payoff
        s = e.last_survivors
        vac = ~s
        claim = s & (W >= 0.25) & (G >= 0.5)
        assert np.array_equal(e.last_eligible, claim)
        has_nb = np.array([vac[e.grid_nb[i]].any() for i in range(e.n_sites)])
        assert e.last_diag["n_claims"] == int((claim & has_nb).sum())
        sites, parents = e.last_birth_sites, e.last_birth_parents
        assert len(set(parents.tolist())) == len(parents)              # at most one birth per parent
        assert vac[sites].all() and s[parents].all() and claim[parents].all()
        for t, p in zip(sites, parents):
            assert t in e.grid_nb[p]                                    # local: a grid neighbour
            assert e.parent_ids[t] == ids0[p] and e.ages[t] == 0
        unfilled = vac & ~np.isin(np.arange(e.n_sites), sites)
        assert not e.occ[unfilled].any()
        if e.last_diag["n_claims"] == 0:
            assert e.birth_rng.bit_generator.state == bstate
        # replay of the birth stream: one integers draw per claimant with a vacant neighbour, increasing index
        rb = np.random.default_rng(); rb.bit_generator.state = bstate
        for i in np.nonzero(claim & has_nb)[0]:
            opts = e.grid_nb[i][vac[e.grid_nb[i]]]
            rb.integers(len(opts))
        assert rb.bit_generator.state == e.birth_rng.bit_generator.state


def test_r8_dying_and_starving_never_parent_and_no_births_without_vacancy():
    e = _r8()
    _r8_force(e, [])                                                   # nobody dies: full lattice, no births
    bstate = e.birth_rng.bit_generator.state
    rstate = e.rng.bit_generator.state
    e.step()
    assert e.last_diag["n_births"] == 0 and e.occ.all()
    assert e.birth_rng.bit_generator.state == bstate and e.rng.bit_generator.state == rstate
    v = 3 * e.width + 3
    nb = list(e.grid_nb[v])
    G = np.full(e.n_sites, 1.0)
    _r8_force(e, [v] + nb[:2], G=G,                                     # v and two neighbours die by the draw
              W=lambda w: np.where(np.isin(np.arange(len(w)), nb[2:3]), -1.0, w))   # a third starves
    e.step()
    parents = set(e.last_birth_parents.tolist())
    assert not (parents & set(nb[:3]))
    assert e.last_starved[nb[2]] and not e.last_survivors[nb[2]]


def test_r8_global_dispersal_targets_outside_the_neighbourhood():
    e = _r8(dispersal="global", seed=52)
    far = 12 * e.width + 12
    G = np.zeros(e.n_sites); G[0] = 1.0                                # only site 0 can claim
    _r8_force(e, [far], G=G)
    e.step()
    assert e.last_diag["n_births"] == 1 and e.last_birth_sites[0] == far and e.last_birth_parents[0] == 0
    assert far not in e.grid_nb[0]
    e2 = _r8(dispersal="local", seed=52)
    _r8_force(e2, [far], G=G)
    e2.step()
    assert e2.last_diag["n_births"] == 0 and not e2.occ[far]           # local: no vacant neighbour, no claim


def test_r8_attempt2_free_endowment_and_birth_cost():
    e = _r8(attempt=2)
    v = 5 * e.width + 5
    nb = list(e.grid_nb[v])
    G = np.zeros(e.n_sites); G[nb[0]] = 1.0
    _r8_force(e, [v], G=G)
    D0 = e.D.copy()
    e.step()
    p = nb[0]
    assert e.last_birth_parents.tolist() == [p] and e.G[v] == 0.75 and e.G[p] == pytest.approx(1.0)
    cost = 0.2 * e.h[p]
    assert e.D[p] == pytest.approx(0.8 * D0[p] + cost + 0.5)


def test_r8_resource_kept_regrows_once_and_newborn_care_next_payoff():
    e = _r8(seed=53, initial_trait_mean=0.6, initial_trait_stddev=0.0, mutation_rate=0.0)
    v = 6 * e.width + 6
    nb = list(e.grid_nb[v])
    G = np.zeros(e.n_sites); G[nb[0]] = 1.0
    e.r[v] = 0.5
    _r8_force(e, [v], G=G)
    e.step()                                                           # v's occupant harvests 0.2 then dies
    assert e.occ[v] and e.r[v] == pytest.approx(0.3 + 0.15 * 0.7)
    p = nb[0]
    _r8_force(e, [])
    e.step()                                                           # parent alive: newborn gets care
    assert e.S[v] == pytest.approx(1.2 * 0.6) and e.ages[v] == 1


def test_r8_founder_hand_computed_case():
    """h 0.6 founder breeding at update 1: G 0.40 after the split, D 0.12; update 2: G 0.52, D 0.216, W 0.304 with
    c_b 0; with an extra 0.5 in D (c_b 0.5 on top of the split) W = -0.096 and it starves."""
    for extra, survives in ((0.0, True), (0.5, False)):
        e = _r8(seed=54, initial_trait_mean=0.6, initial_trait_stddev=0.0, mutation_rate=0.0)
        v = 4 * e.width + 4
        p = int(e.grid_nb[v][0])
        G = np.full(e.n_sites, 0.75); others = [int(x) for x in e.grid_nb[v][1:]]
        G[others] = 0.0
        _r8_force(e, [v], G=G)
        e.step()
        assert e.last_birth_parents.tolist() == [p]
        assert e.G[p] == pytest.approx(0.40) and e.D[p] == pytest.approx(0.12)
        e.D[p] += extra
        e.r[p] = 1.0
        _r8_force(e, [])
        e.step()
        assert e.last_G_payoff[p] == pytest.approx(0.52)
        assert e.last_W[p] == pytest.approx(0.304 if extra == 0 else -0.096)
        assert bool(e.last_survivors[p]) is survives


def test_r8_run_one_window_and_counts():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    m, u = c.r8_base(0.2, 0.5)
    row = run_r8.run_one(("x", m, u, 50, 120, 20))
    e = _r8(seed=50, steps=120)
    occ = nb = 0
    occ_at = {}
    for t in range(120):
        e.step()
        if t >= 20:
            occ += e.last_diag["n_occ_start"]; nb += e.last_diag["n_births"]
        if t + 1 in (10, 50, 100):
            occ_at[t + 1] = float(e.occ.mean())
    assert row["window_states"] == 100 and row["site_steps"] == 100 * 576
    assert row["occ_site_steps"] == occ and row["n_births"] == nb
    assert all(row[f"occ_after_{t}"] == occ_at[t] for t in (10, 50, 100)) and np.isnan(row["occ_after_500"])
    assert row["steps_done"] == 120 and len(row["traj_every_50"]) == 2


def _r8_rows(occ=0.8, final=0.8, extinct=0, override=None, site_steps=2000 * 576):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    rows = []
    for d in c.R8_D0:
        for g in c.R8_G_REP:
            for h in c.R8_SCREEN_H:
                for s in c.R8_SCREEN_SEEDS:
                    o, f, x = occ, final, extinct
                    if override and (d, g, h, s) in override:
                        o, f, x = override[(d, g, h, s)]
                    rows.append({"d0": d, "g_rep": g, "h": h, "seed": s, "occ_site_steps": o * site_steps,
                                 "site_steps": site_steps, "final_occupancy": f, "extinct": x,
                                 "first_empty_update": -1, "steps_done": 3000,
                                 "window_states": site_steps // 576})
    return rows


def test_r8_screen_selection_rule():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8_screen as p
    s = p.select(_r8_rows())
    assert s["complete"] and s["chosen"] == {"d0": 0.3, "g_rep": 0.5}
    # d0 0.3 fails (one seed at h 0.6 above 0.95; per seed, not pooled); d0 0.2 g 0.5 fails (extinct); -> 0.2 / 0.7
    ov = {(0.3, 0.5, 0.6, 51): (0.96, 0.96, 0), (0.3, 0.7, 0.0, 50): (0.49, 0.8, 0),
          (0.2, 0.5, 0.0, 50): (0.0, 0.0, 1)}
    s = p.select(_r8_rows(override=ov))
    assert s["chosen"] == {"d0": 0.2, "g_rep": 0.7}
    assert not s["points"]["d0.3-g0.5"]["passes"] and not s["points"]["d0.3-g0.7"]["passes"]
    ov = {(0.1, 0.5, 0.0, 50): (0.95, 0.5, 0)}                         # bounds inclusive, final 0.5 ok
    s = p.select(_r8_rows(occ=0.99, override=ov))
    assert s["chosen"] is None and s["decision"] == "no setting passed the registered R8 screen"
    s = p.select(_r8_rows(occ=0.5, final=0.5))
    assert s["chosen"] == {"d0": 0.3, "g_rep": 0.5}
    s = p.select(_r8_rows(occ=0.8, final=0.49))
    assert s["chosen"] is None
    rows = _r8_rows()
    for bad in (rows[:-1], rows + rows[:1], [{**rows[0], "seed": 50.5}] + rows[1:],
                [{**rows[0], "steps_done": 2999}] + rows[1:], [{**rows[0], "window_states": 1999}] + rows[1:],
                [{**rows[0], "site_steps": 2000 * 576 + 0.5}] + rows[1:], [{**rows[0], "site_steps": 1000}] + rows[1:]):
        assert p.select(bad)["complete"] is False
    s = p.select(_r8_rows(occ=0.95))                                    # exactly 0.95 passes
    assert s["chosen"] == {"d0": 0.3, "g_rep": 0.5}
    assert p.EXPECTED_SITE_STEPS == 2000 * 576


def test_r8_screen_fails_closed(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8_screen as p
    (tmp_path / "r8_screen_selection.json").write_text(json.dumps({"complete": True, "chosen": {"d0": 0.3}}))
    (tmp_path / "r8_screen_runs.csv").write_text("x\n1\n")

    class FailPool:
        def __init__(self, *_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs): raise RuntimeError("worker failed")

    monkeypatch.setattr(p, "Pool", FailPool)
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    with pytest.raises(RuntimeError):
        p.main()
    sel = json.loads((tmp_path / "r8_screen_selection.json").read_text())
    assert sel["complete"] is False and sel["chosen"] is None and not (tmp_path / "r8_screen_runs.csv").exists()
    seen = []

    class OkPool(FailPool):
        def map(self, f, jobs):
            seen.extend(jobs)
            return [{"arm": a, "seed": s, "occ_site_steps": int(0.8 * 2000 * 576), "site_steps": 2000 * 576,
                     "final_occupancy": 0.8, "extinct": 0, "first_empty_update": -1, "steps_done": 3000,
                     "window_states": 2000} for a, m, u, s, n, w in jobs]

    monkeypatch.setattr(p, "Pool", OkPool)
    p.main()
    assert len(seen) == 24 and all(j[4] == 3000 and j[5] == 1000 for j in seen)
    assert sorted({j[3] for j in seen}) == [50, 51]
    sel = json.loads((tmp_path / "r8_screen_selection.json").read_text())
    assert sel["chosen"] == {"d0": 0.3, "g_rep": 0.5} and (tmp_path / "r8_screen_runs.csv").exists()
    (tmp_path / "r8_screen_runs.csv").unlink()

    def broken_csv(path, rows):
        raise OSError("disk full")
    monkeypatch.setattr(p, "write_union_csv", broken_csv)             # CSV failure: no choice published
    with pytest.raises(OSError):
        p.main()
    sel = json.loads((tmp_path / "r8_screen_selection.json").read_text())
    assert sel["complete"] is False and sel["chosen"] is None


def test_r8_multi_birth_draw_order_and_mutation_batch():
    """Two vacancies, three claimants: targets replay from the birth stream in increasing claimant index; conflicts in
    increasing target index from the lottery stream; then one mutation batch for all births."""
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import _local_softmax_probabilities
    e = _r8(seed=55)
    W_ = e.width
    v1, v2 = 5 * W_ + 5, 5 * W_ + 7                                  # share neighbour 5*W+6
    shared = 5 * W_ + 6
    a, b = 5 * W_ + 4, 4 * W_ + 7                                    # a: only v1; b: only v2
    G = np.zeros(e.n_sites); G[[a, b, shared]] = 1.0
    _r8_force(e, [v1, v2], G=G)
    bs = np.random.default_rng(); bs.bit_generator.state = e.birth_rng.bit_generator.state
    ls = np.random.default_rng(); ls.bit_generator.state = e.rng.bit_generator.state
    h0 = e.h.copy()
    e.step()
    vac = np.zeros(e.n_sites, dtype=bool); vac[[v1, v2]] = True
    targets = {}
    for i in sorted([a, b, shared]):
        opts = e.grid_nb[i][vac[e.grid_nb[i]]]
        targets.setdefault(int(opts[int(bs.integers(len(opts)))]), []).append(i)
    assert bs.bit_generator.state == e.birth_rng.bit_generator.state
    sites, parents = [], []
    for tsite in sorted(targets):
        cl = targets[tsite]
        win = cl[0] if len(cl) == 1 else cl[int(ls.choice(len(cl), p=_local_softmax_probabilities(e.last_W[cl], 0.12)))]
        sites.append(tsite); parents.append(win)
    assert e.last_birth_sites.tolist() == sites and e.last_birth_parents.tolist() == parents
    mut = ls.random(len(sites)) < 0.02
    if mut.any():
        ls.normal(0.0, 0.04, size=int(mut.sum()))
    assert ls.bit_generator.state == e.rng.bit_generator.state
    for tsite, p_, mu in zip(sites, parents, mut):
        if not mu:
            assert e.h[tsite] == h0[p_]                               # unmutated newborns copy the parent
    assert len(sites) == 2


def test_r8_global_newborn_receives_care_by_parent_id():
    e = _r8(dispersal="global", seed=56, initial_trait_mean=0.6, initial_trait_stddev=0.0, mutation_rate=0.0)
    far = 12 * e.width + 12
    G = np.zeros(e.n_sites); G[0] = 1.0
    _r8_force(e, [far], G=G)
    e.step()
    assert e.last_birth_parents.tolist() == [0] and e.parent_ids[far] == e.ids[0]
    _r8_force(e, [])
    e.step()
    assert e.S[far] == pytest.approx(1.2 * 0.6)                       # own-young care at any distance


def test_r8_diagnostics_use_payoff_snapshots():
    e = _r8(seed=57, initial_trait_mean=0.5, initial_trait_stddev=0.1)
    seen_dead = False
    for _ in range(15):
        occ0 = e.occ.copy()
        juv0 = (e.ages < 2) & occ0
        e.step()
        d = e.last_diag
        m = lambda x, mask: float(x[mask].mean()) if mask.any() else float("nan")
        assert d["D_mean"] == m(e.last_D_payoff, occ0) and d["S_mean"] == m(e.last_S_payoff, occ0)
        assert d["S_juvenile"] == pytest.approx(m(e.last_S_payoff, juv0), nan_ok=True)
        np.testing.assert_allclose(e.last_W[occ0], (e.last_G_payoff + 0.5 * e.last_S_payoff - e.last_D_payoff)[occ0],
                                   rtol=0, atol=1e-12)
        dead = occ0 & ~e.last_survivors
        if dead.any():
            seen_dead = True
            assert (e.last_D_payoff[dead] > 0).any()                  # snapshot taken before dead sites are cleared
        assert d["n_fill_needed"] == int((~e.last_survivors).sum())
        assert d["n_fill_emptied"] == d["n_fill_needed"] - d["n_births"]
    assert seen_dead


# ---------------------------------------------------------------- Step R8 Stage M
def test_r8_main_arms_registered():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    from ecological_models.nowak_mechanisms.kin_selection_ladder.ladder_model import BuddingEngine
    a1, a2 = c.r8_arms(1, 0.2, 0.5), c.r8_arms(2, 0.2, 0.5)
    assert sorted(a1) == sorted(["U6-local", "UN6-local", "U-below", "U3-local", "U12-local", "U24-local",
                                 "U6-global", "U12-global"])
    assert sorted(a2) == sorted(["U2-6-local", "U2-N6-local", "U2-below", "U2-3-local", "U2-12-local",
                                 "U2-24-local", "U2-6-global", "U2-12-global"])
    r4 = c.r4_arms(1)
    for arms, att in ((a1, 1), (a2, 2)):
        for name, (m, u) in arms.items():
            assert m["replacement"] == "local" and m["death"] == 0.2 and m["care_g_rep"] == 0.5
            assert m["care_split"] is (att == 1) and m["care_birth_cost"] == (0.0 if att == 1 else 0.5)
            assert m["care_dispersal"] == ("global" if "global" in name else "local")
    assert a1["UN6-local"][0]["care"] == "young_neighbours" and a1["U6-local"][0]["care"] == "offspring"
    assert a1["U-below"][1] == r4["G-below"][1] and a1["U-below"][1]["B_plus_scale"] == 0.05
    assert a1["U6-local"][1] == r4["G6-local"][1] and a1["U24-local"][1]["B_plus_scale"] == r4["G24-local"][1]["B_plus_scale"]
    assert c.r8_roles(1) == ("U6-local", "UN6-local", "U-below", "U6-global")
    assert c.r8_roles(2) == ("U2-6-local", "U2-N6-local", "U2-below", "U2-6-global")
    for name in ("U6-global", "UN6-local", "U-below"):
        m, u = a1[name]; m = dict(m)
        e = make_engine(run_config(0, u, 5), replacement=m.pop("replacement"), death=m.pop("death"), **m)
        assert isinstance(e, BuddingEngine) and e.dispersal == ("global" if "global" in name else "local")


def _r8m_row(arm, seed, success, extinct=0, ff=(100, 1000), occ=0.8, harvest=0.15, corr=0.0, attempt=1):
    states = 5000
    return {"arm": arm, "seed": seed, "steps_done": 6000, "window_states": states, "site_steps": states * 576,
            "occ_site_steps": int(occ * states * 576), "n_occ_start": int(occ * states * 576),
            "harvest_total": harvest * int(occ * states * 576), "n_fill_emptied": ff[0], "n_fill_needed": ff[1],
            "final_mean_trait": 0.8 if success else 0.1, "final_occupancy": 0.0 if extinct else 0.9,
            "extinct": extinct, "first_empty_update": 300 if extinct else -1, "traj_every_50": [0.5] * 120,
            "neighbour_h_corr": [corr] * 6, **{f"occ_after_{t}": 0.9 for t in (10, 50, 100, 500)},
            **{k: 1 for k in ("n_births", "n_claims", "n_targets", "n_deaths", "n_starve_added", "n_draw_deaths",
                              "births_low_h_sum", "n_low_h", "births_high_h_sum", "n_high_h", "n_claimants")},
            **{k: 0.5 for k in ("G_mean", "G_juvenile", "G_parents", "S_mean", "D_mean", "S_juvenile", "D_juvenile",
                                "S_parents", "D_parents", "death_mean", "frac_claimant",
                                "starve_rate_recent_parents")}}


def _r8m_pool(rows_by_attempt, seen):
    class P:
        def __init__(self, *_): self.calls = 0
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def map(self, f, jobs):
            seen.append(sorted({j[0] for j in jobs}))
            arms = sorted({j[0] for j in jobs})
            att = 2 if arms[0].startswith("U2-") else 1
            return [dict(r) for r in rows_by_attempt[att](jobs)]
    return P


def _r8m_setup(tmp_path, chosen=True):
    import json
    sel = {"complete": True, "chosen": {"d0": 0.2, "g_rep": 0.5}} if chosen else {"complete": True, "chosen": None}
    (tmp_path / "r8_screen_selection.json").write_text(json.dumps(sel))


def test_r8_main_met_attempt1_and_labels(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8_main as p
    _r8m_setup(tmp_path)

    def rows1(jobs):
        out = []
        for a, m, u, s, n, w in jobs:
            assert n == 6000 and w == 1000 and m["death"] == 0.2 and m["care_g_rep"] == 0.5
            ok = a in ("U6-local", "U6-global") or (a == "U-below" and s < 1)
            ext = int(a == "U6-local" and s == 19)
            out.append(_r8m_row(a, s, ok and not ext, extinct=ext,
                                ff=(30, 1000) if (a == "U6-local" and s < 12) else (10, 1000),
                                occ=0.96 if a == "U6-local" else 0.8))
        return out
    seen = []
    monkeypatch.setattr(p, "Pool", _r8m_pool({1: rows1}, seen))
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    p.main()
    v = json.loads((tmp_path / "r8_main_verdict.json").read_text())
    a = v["attempt1"]
    assert v["complete"] and a["class"] == "met" and a["test"] == 19 and a["control"] == 0 and v["r8_met"] is True
    assert "attempt2" not in v and len(seen) == 1
    assert a["h2"]["result"] == "met" and a["income_activation"]["active"]
    vac = a["vacancy"]
    assert vac["extinct_seeds"] == 1 and vac["pooled"]["window_occupancy"] == pytest.approx(0.96, abs=1e-6)
    assert vac["label"] == "vacant space present"                     # occupancy 0.96 <= 0.97
    assert vac["successes_with_vacant_space"] == 19 and vac["non_extinct_seeds_with_vacant_space"] == 19
    assert "reopen_r5_proposable" not in vac and v["disposition"].startswith("met with vacant space")
    assert (tmp_path / "r8_main_runs.csv").exists()


def test_r8_main_attempt2_after_comparison_failure_and_vacancy_rare(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8_main as p
    _r8m_setup(tmp_path)

    def rows(jobs):
        return [_r8m_row(a, s, a.endswith("6-local") or a.endswith("N6-local") or a.endswith("6-global"),
                         ff=(1, 1000), occ=0.99) for a, m, u, s, n, w in jobs]
    seen = []
    monkeypatch.setattr(p, "Pool", _r8m_pool({1: rows, 2: rows}, seen))
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    p.main()
    v = json.loads((tmp_path / "r8_main_verdict.json").read_text())
    assert v["attempt1"]["class"] == "comparison failed" and v["attempt2"]["class"] == "comparison failed"
    assert len(seen) == 2 and seen[1][0].startswith("U2-")
    assert v["attempt1"]["vacancy"]["label"] == "vacant space rare" and v["r8_met"] is False
    assert v["disposition"].startswith("neither attempt met")


def test_r8_main_all_extinct_undefined_and_h2_not_interpretable():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8_main as p
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_r1 import score_h2
    rows = [{**_r8m_row("U6-local", s, False, extinct=1), "success": 0} for s in range(20)]
    lab = p.vacancy_label(rows)
    assert lab["label"] == "undefined"
    g = [{**_r8m_row("U6-global", s, True, corr=float("nan") if s == 3 else 0.0), "success": 1} for s in range(20)]
    assert score_h2(g)["result"] == "not interpretable"
    g = [{**_r8m_row("U6-global", s, True, corr=0.2), "success": 1} for s in range(20)]
    assert score_h2(g)["result"] == "not interpretable"
    assert p.joint_success({"final_mean_trait": 0.6, "final_occupancy": 0.5}) == 1
    assert p.joint_success({"final_mean_trait": float("nan"), "final_occupancy": 0.0}) == 0


def test_r8_main_incomplete_and_needs_screen(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8_main as p
    _r8m_setup(tmp_path)

    def short(jobs):
        rows = [_r8m_row(a, s, True) for a, m, u, s, n, w in jobs]
        rows[5] = {**rows[5], "steps_done": 5999}
        return rows
    seen = []
    monkeypatch.setattr(p, "Pool", _r8m_pool({1: short}, seen))
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    p.main()
    v = json.loads((tmp_path / "r8_main_verdict.json").read_text())
    assert v["complete"] is False and v["attempt1"]["class"] is None and v["r8_met"] is None and len(seen) == 1
    _r8m_setup(tmp_path, chosen=False)                                  # complete screen, no point: terminal
    p.main()
    v = json.loads((tmp_path / "r8_main_verdict.json").read_text())
    assert v["complete"] is True and v["chosen_point"] is None and v["r8_met"] is False


def test_r8_main_real_run_one_smoke():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    for name in ("U6-local", "UN6-local", "U6-global", "U2-6-local"):
        att = 2 if name.startswith("U2-") else 1
        m, u = c.r8_arms(att, 0.2, 0.5)[name]
        row = run_r8.run_one((name, m, u, 0, 1200, 1000))
        assert row["window_states"] == 200 and row["steps_done"] == 1200 and len(row["neighbour_h_corr"]) == 1


def test_r8_main_early_extinction_classified_and_triggers_attempt2(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8_main as p
    _r8m_setup(tmp_path)

    def dead(jobs):                                                   # every run extinct before the window
        out = []
        for a, m, u, s, n, w in jobs:
            r = _r8m_row(a, s, False, extinct=1, occ=0.0, harvest=0.0, ff=(5000 * 576, 5000 * 576),
                         corr=float("nan"))
            r["final_mean_trait"] = float("nan")
            out.append(r)
        return out
    seen = []
    monkeypatch.setattr(p, "Pool", _r8m_pool({1: dead, 2: dead}, seen))
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    p.main()
    v = json.loads((tmp_path / "r8_main_verdict.json").read_text())
    assert v["attempt1"]["class"] == "local failure" and v["attempt2"]["class"] == "local failure"
    assert v["attempt1"]["income_activation"]["pooled_harvest"] is None
    assert v["attempt1"]["vacancy"]["label"] == "undefined" and v["attempt1"]["h2"]["result"] == "not interpretable"
    assert len(seen) == 2 and v["r8_met"] is False


def test_r8_main_choice_validation_and_missing_h2_sample(monkeypatch, tmp_path):
    import json
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_r8_main as p
    monkeypatch.setattr(p, "DATA_DIR", str(tmp_path))
    for sel in ({"complete": "false", "chosen": {"d0": 0.2, "g_rep": 0.5}},
                {"complete": True, "chosen": {"d0": 0.25, "g_rep": 0.5}}):
        (tmp_path / "r8_screen_selection.json").write_text(json.dumps(sel))
        with pytest.raises(SystemExit):
            p.main()
    (tmp_path / "r8_screen_selection.json").write_text(json.dumps({"complete": True, "chosen": None}))
    p.main()
    v = json.loads((tmp_path / "r8_main_verdict.json").read_text())
    assert v["complete"] is True and v["r8_met"] is False and v["disposition"].startswith("no setting passed")
    r = _r8m_row("U6-global", 0, True)
    assert p.finished(r) and not p.finished({**r, "neighbour_h_corr": [0.0] * 5})


# ---------------------------------------------------------------- Diagnostic DR8
def test_dr8_wrapper_keeps_trajectory_and_counts():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr8 as d, run_r8
    from ecological_models.nowak_mechanisms.kin_selection_ladder.config import ladder_config as c
    for arm in d.ARMS:
        m, u = c.r8_arms(2, 0.2, 0.5)[arm]
        a = d.run_one((arm, m, u, 3, 300, 100))
        b = run_r8.run_one((arm, m, u, 3, 300, 100))
        assert a["final_mean_trait"] == b["final_mean_trait"] and a["final_occupancy"] == b["final_occupancy"]
        assert a["high_wb"] + a["low_wb"] > 0
        assert a["high_blocked"] <= a["high_wb"] and a["low_blocked"] <= a["low_wb"]
        tot_births = a["high_births"] + a["low_births"]
        assert tot_births == b["n_births"]                             # every window birth is by a would-be breeder


def test_dr8_class_stats_forced():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr8 as d
    e = _r8(attempt=2)
    n = e.n_sites
    i = 5 * e.width + 5
    nb = e.grid_nb[i]
    claimant = np.zeros(n, dtype=bool); claimant[i] = True
    vacant = np.zeros(n, dtype=bool)
    e.h[:] = 0.1; e.h[i] = 0.9
    e.parent_ids[nb[:2]] = e.ids[i]                                    # two neighbours are its own offspring
    st = d.class_stats(e, claimant, vacant, 0.5)
    assert st["high"]["wb"] == 1 and st["high"]["blocked"] == 1 and st["low"]["wb"] == 0
    assert st["high"]["nb_occ"] == 4 and st["high"]["nb_own"] == 2
    vacant[nb[3]] = True
    st = d.class_stats(e, claimant, vacant, 0.5)
    assert st["high"]["blocked"] == 0 and st["high"]["nb_occ"] == 3


def test_dr8_reading_rule():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr8 as d
    def row(hb, lb, hw=10, lw=10):
        return {"high_wb": hw, "high_blocked": hb, "high_births": 0, "high_nb_occ": 1, "high_nb_own": 0,
                "low_wb": lw, "low_blocked": lb, "low_births": 0, "low_nb_occ": 1, "low_nb_own": 0}
    assert d.reading([row(5, 1)] * 15 + [row(1, 5)] * 5)["label"] == "high helpers more often blocked"
    assert d.reading([row(5, 1)] * 5 + [row(1, 5)] * 15)["label"] == "not supported"
    r = d.reading([row(5, 1)] * 10 + [row(1, 5)] * 9 + [row(1, 1, hw=0)])
    assert r["label"] == "unclear" and r["seeds_excluded"] == 1 and r["seeds_used"] == 19


def test_dr8_global_blocking_and_mean_tie():
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr8 as d
    e = _r8(attempt=2, dispersal="global")
    n = e.n_sites
    i = 5 * e.width + 5
    claimant = np.zeros(n, dtype=bool); claimant[i] = True
    vacant = np.zeros(n, dtype=bool)
    e.h[:] = 0.5
    st = d.class_stats(e, claimant, vacant, 0.5)                     # h equal to the mean: low class
    assert st["low"]["wb"] == 1 and st["high"]["wb"] == 0 and st["low"]["blocked"] == 1   # full grid: blocked
    vacant[12 * e.width + 12] = True                                  # a vacancy far away unblocks globally
    assert d.class_stats(e, claimant, vacant, 0.5)["low"]["blocked"] == 0
    e2 = _r8(attempt=2)
    e2.h[:] = 0.5
    assert d.class_stats(e2, claimant, vacant, 0.5)["low"]["blocked"] == 1   # but not locally


def test_dr8_validity_void_and_match(tmp_path):
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils import run_dr8 as d
    from ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_dr4 import write_union_csv
    stored = [{"arm": "U2-6-local", "seed": 0, "final_mean_trait": 0.35, "final_occupancy": 0.99}]
    write_union_csv(tmp_path / "r8_main_runs.csv", stored)
    assert d.check_stored([dict(stored[0])], tmp_path) == []
    assert d.check_stored([{**stored[0], "final_mean_trait": 0.35 + 1e-15}], tmp_path) == [("U2-6-local", 0)]
    assert d.check_stored([{**stored[0], "seed": 1}], tmp_path) == [("U2-6-local", 1)]
    def row(seed, arm, hb, lb):
        return {"arm": arm, "seed": seed, "high_wb": 10, "high_blocked": hb, "high_births": 2, "high_nb_occ": 0,
                "high_nb_own": 0, "low_wb": 10, "low_blocked": lb, "low_births": 3, "low_nb_occ": 4, "low_nb_own": 1}
    rows = [row(s, a, 5, 1) for a in d.ARMS for s in range(20)]
    sm = d.summarize(rows)
    assert sm["U2-6-local"]["reading"]["label"] == "high helpers more often blocked"
    assert sm["U2-6-local"]["births_lower_for_high"] == {"count": 20, "used": 20, "excluded": 0}
    assert sm["U2-6-local"]["own_share_higher_for_high"] == {"count": 0, "used": 0, "excluded": 20}
