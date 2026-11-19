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
    assert all(k in row for k in r.EXTRA_KEYS) and 0 < row["juvenile_fraction"] < 1
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
