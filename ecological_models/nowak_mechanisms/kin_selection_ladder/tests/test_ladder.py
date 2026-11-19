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
