"""Tests for the rung-5c model: independent reference with mixed empathy masks, p = 0 / p = 1 equivalence on scripted
acts, corruption tests, frozen sampling test of the empathy mask, shared mechanics."""

import numpy as np
import pytest
from numba import njit

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import model as M5a
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5b_empathy import model as M5b
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5c_partial_empathy import model as M
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5c_partial_empathy.tests.reference import \
    PartialEmpathyViews


def _vt(ref):
    VT = np.zeros((ref.n, ref.n), np.uint8)
    for (w, t), g in ref.views.items():
        VT[t, w] = 1 if g else 0
    return VT


def _m(n, idx):
    m = np.zeros(n, np.bool_)
    m[list(idx)] = True
    return m


SCRIPT = [  # donor, recipient, helped, observers, flipped, empathetic
    (0, 1, False, [2, 3, 4], [], [3]),
    (2, 0, False, [1, 3, 4, 5], [5], [1, 4]),
    (5, 3, True, [1, 2, 4], [2], [1, 2, 4]),
    (1, 0, False, [3, 5], [], []),
    (4, 2, False, [0, 1, 3, 5], [0], [0, 1, 3, 5]),
]


def test_scripted_acts_with_mixed_masks_match_reference():
    n = 6
    ref = PartialEmpathyViews(n)
    for (w, t) in ((2, 0), (4, 2), (3, 1)):
        ref.views[(w, t)] = False
    VT = _vt(ref)
    for d, r, helped, obs, fl, emp in SCRIPT:
        o, f, e = _m(n, obs), _m(n, fl), _m(n, emp)
        db, rb = VT[d].copy(), VT[r].copy()
        M.apply_act(VT, d, r, helped, o, f, False, e)
        assert M.check_act(VT, d, r, helped, o, f, False, db, rb, e) == 0
        ref.assess(d, r, helped, obs, set(fl), set(emp))
        assert np.array_equal(VT, _vt(ref)), (d, r)


@pytest.mark.parametrize("all_emp, other", [(True, M5b), (False, M5a)])
def test_endpoints_equal_earlier_rungs_on_scripted_acts(all_emp, other):
    n = 6
    rng = np.random.default_rng(4)
    VT = rng.integers(0, 2, (n, n)).astype(np.uint8)
    VT2 = VT.copy()
    for d, r, helped, obs, fl, _ in SCRIPT:
        o, f = _m(n, obs), _m(n, fl)
        e = o.copy() if all_emp else np.zeros(n, np.bool_)
        M.apply_act(VT, d, r, helped, o, f, False, e)
        other.apply_act(VT2, d, r, helped, o, f, False)
        assert np.array_equal(VT, VT2)


@pytest.mark.parametrize("corrupt", ["always_emp", "never_emp", "emp_nonobserver", "nonobserver_write"])
def test_check_act_catches_corruption(corrupt):
    n = 8
    rng = np.random.default_rng(1)
    VT = rng.integers(0, 2, (n, n)).astype(np.uint8)
    d, r, helped = 2, 5, False
    VT[r, d] = 0
    obs_l, emp_l = [0, 1, 3, 6], [0, 3]
    for w in obs_l:
        VT[r, w] = 1                              # donor and observers disagree: the two rules differ
    o, f, e = _m(n, obs_l), _m(n, []), _m(n, emp_l)
    db, rb = VT[d].copy(), VT[r].copy()
    if corrupt == "always_emp":
        M.apply_act(VT, d, r, helped, o, f, False, o.copy())
    elif corrupt == "never_emp":
        M.apply_act(VT, d, r, helped, o, f, False, np.zeros(n, np.bool_))
    else:
        M.apply_act(VT, d, r, helped, o, f, False, e)
        if corrupt == "emp_nonobserver":
            e = e.copy()
            e[4] = True
        else:
            VT[d, 4] ^= 1
    assert M.check_act(VT, d, r, helped, o, f, False, db, rb, e) > 0


@pytest.mark.parametrize("pe", [0.5, 0.25])
def test_empathy_mask_sampling_frozen(pe):
    M._seed(11)
    n, reps = 64, 20000
    obs, fl, emp = np.zeros(n, np.bool_), np.zeros(n, np.bool_), np.zeros(n, np.bool_)
    gap = M._geom(0.1)
    E, F = [], []
    for _ in range(reps):
        gap = M.draw_masks(n, 3, 40, 0.5, 0.1, gap, obs, fl, pe, emp)
        assert not (emp & ~obs).any()
        E.extend(emp[obs].tolist())
        F.extend(fl[obs].tolist())
    E, F = np.array(E, float), np.array(F, float)
    assert abs(E.mean() - pe) < 0.01
    assert abs(np.corrcoef(E, F)[0, 1]) < 0.02
    assert abs(np.corrcoef(E[:-1], E[1:])[0, 1]) < 0.02


def test_production_encounter_sanity_and_counter():
    for pe in (0.0, 0.5, 1.0):
        for arm in (M.TEST, M.SHUFFLED):
            cnt, au, st, g1 = M.run(0.8, 0.5, 0.1, 0.02, 0.001, (0.1, 0.8, 0.1), arm, 5, gens=3, n=60, pe=pe)
            s = dict(zip(M.STATS, st + g1))
            assert s["check_mismatch"] == 0 and s["sanity_violations"] == 0
            share = s["empathetic_obs"] / s["observations"]
            assert abs(share - pe) < 0.02


def test_intentional_refusal_judged_by_used_view():
    n = 5
    is_disc = np.array([True, False, False, False, False])
    is_allc = np.zeros(n, np.bool_)
    VT = np.ones((n, n), np.uint8)
    VT[1, 0] = 0                                   # DISC 0 sees recipient 1 bad; observers 2, 3 see 1 good
    obs, fl, emp = _m(n, [2, 3]), _m(n, []), _m(n, [2])
    stats = np.zeros(M.NST)
    db, rb = np.empty(n, np.uint8), np.empty(n, np.uint8)
    helped, _ = M.encounter(VT, 0, 1, is_disc, is_allc, 0.1, 1.0, -1, obs, fl, 0.8, 0.1, M.TEST, stats, db, rb, emp)
    assert not helped and VT[0, 2] == 1 and VT[0, 3] == 0   # empathetic 2 excuses, own-view 3 condemns
    assert stats[28] == 1 and stats[0] == 0 and stats[1] == 0


def test_shared_mechanics():
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b import model as m4b
    assert M.mutate_detail is m4b.mutate_detail
    M._seed(3)
    seen = np.zeros(10, int)
    for _ in range(20000):
        seen[M._other(10, 2, 7)] += 1
    assert seen[2] == 0 and seen[7] == 0
    n = 20
    VT = np.zeros((n, n), np.uint8)
    M.play(np.ones(n, np.bool_), np.zeros(n, np.bool_), 0, 3.0, 1.0, 0.8, 0.5, 0.1, 0.02, M.TEST,
           np.zeros(M.NST), VT, False, 0.5)
    assert (VT + np.eye(n, dtype=np.uint8) == 1).all()


def test_production_encounter_matches_reference_all_types_both_arms():
    n = 7
    is_disc = np.array([True, True, False, False, True, False, True])
    is_allc = np.array([False, False, True, False, False, True, False])
    strat = ["DISC" if is_disc[t] else ("ALLC" if is_allc[t] else "ALLD") for t in range(n)]
    script = [  # donor, recipient, consult_u, fail_u, z, observers, flipped, empathetic
        (3, 0, 1.0, 1.0, -1, [1, 2, 4], [], [2]),
        (1, 3, 0.1, 1.0, 2, [0, 2, 5], [], [0, 5]),
        (0, 3, 0.1, 1.0, 4, [1, 5, 6], [5], [6]),
        (4, 1, 0.1, 1.0, 3, [0, 2, 5], [], [0, 2, 5]),
        (6, 3, 0.9, 0.0, -1, [1, 2], [], []),
        (2, 1, 1.0, 0.05, -1, [0, 3, 6], [], [3]),
        (5, 0, 1.0, 1.0, -1, [1, 4], [4], [1]),
    ]
    for arm in (M.TEST, M.SHUFFLED):
        ref = PartialEmpathyViews(n)
        for w, t in ((4, 3), (6, 3), (4, 1), (0, 3)):
            ref.views[(w, t)] = False
        VT = _vt(ref)
        stats = np.zeros(M.NST)
        db, rb = np.empty(n, np.uint8), np.empty(n, np.uint8)
        for d, r, cu, fu, z, obs, fl, emp in script:
            zz = z if (arm == M.SHUFFLED and is_disc[d] and cu < 0.8) else -1
            helped, _ = M.encounter(VT, d, r, is_disc, is_allc, cu, fu, zz, _m(n, obs), _m(n, fl), 0.8, 0.1, arm,
                                    stats, db, rb, _m(n, emp))
            _, ref_helped = ref.decide(strat[d], d, r, bool(is_disc[d] and cu < 0.8), fu < 0.1,
                                       zz if zz >= 0 else None)
            assert helped == ref_helped, (arm, d, r)
            ref.assess(d, r, ref_helped, obs, set(fl), set(emp))
            assert np.array_equal(VT, _vt(ref)), (arm, d, r)
        assert stats[0] == 0 and stats[1] == 0
        st = dict(zip(M.STATS, stats))
        for name, v in ref.counts.items():
            assert st[name] == v, (arm, name, st[name], v)


def test_check_act_catches_recipient_change():
    n = 6
    VT = np.ones((n, n), np.uint8)
    o, f, e = _m(n, [0, 3]), _m(n, []), _m(n, [0])
    db, rb = VT[2].copy(), VT[4].copy()
    M.apply_act(VT, 2, 4, False, o, f, False, e)
    VT[4, 1] ^= 1
    assert M.check_act(VT, 2, 4, False, o, f, False, db, rb, e) > 0


def test_observation_and_flip_masks_independent():
    M._seed(31)
    n, reps = 64, 20000
    obs, fl, emp = np.zeros(n, np.bool_), np.zeros(n, np.bool_), np.zeros(n, np.bool_)
    O = np.zeros((reps, n), np.bool_)
    F = []
    gap = M._geom(0.1)
    for t in range(reps):
        gap = M.draw_masks(n, 3, 40, 0.5, 0.1, gap, obs, fl, 0.5, emp)
        O[t] = obs
        F.extend(fl[obs].tolist())
    cols = [w for w in range(n) if w not in (3, 40)]
    assert not O[:, 3].any() and not O[:, 40].any()
    assert np.abs(O[:, cols].mean(0) - 0.5).max() < 0.02
    cc = np.corrcoef(O[:, cols].T.astype(float))
    assert np.abs(cc[~np.eye(len(cols), dtype=bool)]).max() < 0.04
    F = np.array(F, float)
    assert abs(F.mean() - 0.1) < 0.005 and abs(np.corrcoef(F[:-1], F[1:])[0, 1]) < 0.02


@njit
def _numba_uniforms(k):
    return np.random.random(k)              # the same numba stream the model draws from


def test_empathy_draws_after_flips_in_ascending_order():
    # o = 1 and a = 0 draw nothing for observation and flips, so the empathy bits are the first uniforms of the stream,
    # assigned to observers in ascending index order (donor 0 and recipient 1 excluded)
    n = 16
    obs, fl, emp = np.zeros(n, np.bool_), np.zeros(n, np.bool_), np.zeros(n, np.bool_)
    M._seed(5)
    M.draw_masks(n, 0, 1, 1.0, 0.0, -1, obs, fl, 0.5, emp)
    M._seed(5)
    u = _numba_uniforms(n - 2)
    assert [bool(emp[w]) for w in range(2, n)] == [bool(x < 0.5) for x in u]
    assert not emp[0] and not emp[1] and 0 < emp.sum() < n - 2
