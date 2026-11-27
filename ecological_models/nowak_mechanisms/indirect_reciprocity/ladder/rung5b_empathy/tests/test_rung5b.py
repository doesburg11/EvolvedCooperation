"""Tests for the rung-5b model: independent reference (empathetic rule), corruption tests, shared rung-5a mechanics."""

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5b_empathy import model as M
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5b_empathy.tests.reference import EmpatheticViews


def _vt_from(ref):
    n = ref.n
    VT = np.zeros((n, n), np.uint8)
    for (w, t), g in ref.views.items():
        VT[t, w] = 1 if g else 0
    return VT


def _masks(n, observers, flipped):
    obs = np.zeros(n, np.bool_)
    fl = np.zeros(n, np.bool_)
    obs[list(observers)] = True
    fl[list(flipped)] = True
    return obs, fl


@pytest.mark.parametrize("donor_good", [True, False])
@pytest.mark.parametrize("observer_good", [True, False])
@pytest.mark.parametrize("helped", [True, False])
@pytest.mark.parametrize("flip", [True, False])
def test_truth_table(donor_good, observer_good, helped, flip):
    n = 5
    d, r, w = 0, 1, 2
    VT = np.ones((n, n), np.uint8)
    VT[r, d] = donor_good
    VT[r, w] = observer_good
    obs, fl = _masks(n, [w], [w] if flip else [])
    don_b, rec_b = VT[d].copy(), VT[r].copy()
    M.apply_act(VT, d, r, helped, obs, fl, False)
    expect = (helped or not donor_good) != flip
    assert VT[d, w] == expect
    assert M.check_act(VT, d, r, helped, obs, fl, False, don_b, rec_b) == 0


def test_scripted_acts_match_reference_including_stale_views():
    n = 6
    ref = EmpatheticViews(n)
    VT = _vt_from(ref)
    script = [(0, 1, False, [2, 3], []),          # ALLD-like refusal of 1 (donor 0 sees 1 good) -> 0 bad for 2, 3
              (2, 0, False, [3, 4], []),          # 2 refuses 0; 2 sees 0 bad -> justified: 2 good for 3 and 4
              (5, 3, True, [1, 2, 4], [2]),       # help, flip for observer 2
              (1, 0, False, [5], []),             # 1 did not observe 0's refusal (stale: sees 0 good) -> 1 bad
              ]
    for d, r, helped, obs, fl in script:
        o, f = _masks(n, obs, fl)
        don_b, rec_b = VT[d].copy(), VT[r].copy()
        M.apply_act(VT, d, r, helped, o, f, False)
        assert M.check_act(VT, d, r, helped, o, f, False, don_b, rec_b) == 0
        ref.assess(d, r, helped, obs, set(fl))
        assert np.array_equal(VT, _vt_from(ref)), (d, r)
    assert VT[2, 4] == 1                       # observer 4 saw 0 good, but judged by 2's view: justified refusal
    assert VT[1, 5] == 0 and VT[0, 1] == 1     # stale view of the donor 1 condemns its refusal


@pytest.mark.parametrize("corrupt", ["observer_rule", "wrong_index", "nonobserver", "recipient"])
def test_check_act_catches_corruption(corrupt):
    n = 8
    rng = np.random.default_rng(1)
    VT = rng.integers(0, 2, (n, n)).astype(np.uint8)
    d, r, helped = 2, 5, False
    VT[r, d] = 0                               # donor sees recipient bad
    obs_list = [0, 1, 3, 6]
    for w in obs_list:
        VT[r, w] = 1                           # observers see recipient good: the two rules disagree
    VT[d, r] = 1                               # the transposed entry differs from VT[r, d]
    obs, fl = _masks(n, obs_list, [])
    don_b, rec_b = VT[d].copy(), VT[r].copy()
    M.apply_act(VT, d, r, helped, obs, fl, False)
    if corrupt == "observer_rule":             # rung 5a's rule (observer's own view): all observers would say bad
        for w in obs_list:
            VT[d, w] = 0 if rec_b[w] == 1 else 1
    elif corrupt == "wrong_index":             # VT[d, r] (recipient's view of donor) instead of VT[r, d]
        for w in obs_list:
            VT[d, w] = 0 if VT[d, r] == 1 else 1
    elif corrupt == "nonobserver":
        VT[d, 4] ^= 1
    else:
        VT[r, 0] ^= 1
    assert M.check_act(VT, d, r, helped, obs, fl, False, don_b, rec_b) > 0


def test_production_encounter_matches_reference_all_types_both_arms():
    n = 7
    is_disc = np.array([True, True, False, False, True, False, True])
    is_allc = np.array([False, False, True, False, False, True, False])
    strat = ["DISC" if is_disc[t] else ("ALLC" if is_allc[t] else "ALLD") for t in range(n)]
    for arm in (M.TEST, M.SHUFFLED):
        ref = EmpatheticViews(n)
        VT = _vt_from(ref)
        stats = np.zeros(M.NST)
        db, rb = np.empty(n, np.uint8), np.empty(n, np.uint8)
        script = [  # donor, recipient, consult_u, fail_u, z, observers, flipped
            (3, 0, 1.0, 1.0, -1, [1, 2, 4], []),       # ALLD refuses 0
            (1, 3, 0.1, 1.0, 2, [0, 2, 5], []),        # DISC 1 consults
            (0, 3, 0.1, 1.0, 4, [1, 5, 6], [5]),       # DISC 0 consults (stale view of 3), flip for 5
            (4, 1, 0.1, 1.0, 3, [0, 2, 5], []),        # DISC 4 consults; shuffled: reads its view of 3
            (6, 3, 0.9, 0.0, -1, [1, 2], []),          # DISC 6 does not consult, help fails
            (2, 1, 1.0, 0.05, -1, [0, 3, 6], []),      # ALLC 2 intends, fails
            (5, 0, 1.0, 1.0, -1, [1, 4], [4]),         # ALLC 5 helps, flip for 4
        ]
        # make some views bad first so refusals occur: 4 and 6 see 3 bad, 4 sees 1 bad
        for w, t in ((4, 3), (6, 3), (4, 1)):
            ref.views[(w, t)] = False
        VT = _vt_from(ref)
        for d, r, cu, fu, z, obs, fl in script:
            observed, flip = _masks(n, obs, fl)
            zz = z if (arm == M.SHUFFLED and is_disc[d] and cu < 0.8) else -1
            helped, _ = M.encounter(VT, d, r, is_disc, is_allc, cu, fu, zz, observed, flip, 0.8, 0.1, arm, stats, db, rb)
            consulted = bool(is_disc[d] and cu < 0.8)
            _, ref_helped = ref.decide(strat[d], d, r, consulted, failed=fu < 0.1,
                                       shuffled_target=zz if zz >= 0 else None)
            assert helped == ref_helped, (arm, d, r)
            ref.assess(d, r, ref_helped, obs, set(fl))
            assert np.array_equal(VT, _vt_from(ref)), (arm, d, r)
        assert stats[0] == 0 and stats[1] == 0
        st = dict(zip(M.STATS, stats))
        for name, v in ref.counts.items():
            assert st[name] == v, (arm, name, st[name], v)


def test_justified_refusal_judged_good_and_disagreement_counted():
    # a justified refusal is judged good even by observers who see the recipient as good; disagreement is counted
    n = 5
    is_disc = np.array([True, False, False, False, False])
    is_allc = np.zeros(n, np.bool_)
    VT = np.ones((n, n), np.uint8)
    VT[1, 0] = 0                               # DISC 0 sees recipient 1 bad: intentional, justified refusal
    obs, fl = _masks(n, [2, 3], [])
    stats = np.zeros(M.NST)
    db, rb = np.empty(n, np.uint8), np.empty(n, np.uint8)
    helped, _ = M.encounter(VT, 0, 1, is_disc, is_allc, 0.1, 1.0, -1, obs, fl, 0.8, 0.1, M.TEST, stats, db, rb)
    assert not helped and VT[0, 2] == 1 and VT[0, 3] == 1      # observers see 1 good, yet judge 0 good
    assert stats[9] == 2 and stats[10] == 2                     # residual disagreement still counted


def test_generation_reset_counters_and_rates():
    cnt, au, st, g1 = M.run(0.8, 0.5, 0.1, 0.02, 0.001, (0.1, 0.8, 0.1), M.TEST, 5, gens=3, n=60)
    s = dict(zip(M.STATS, st + g1))
    assert s["check_mismatch"] == 0 and s["sanity_violations"] == 0
    assert s["encounters"] == 60 * 10 * 3 and (au[:, 9] == 600).all()
    cnt, au, st, g1 = M.run(0.8, 0.5, 0.1, 0.02, 0.0, (0.0, 1.0, 0.0), M.SHUFFLED, 7, gens=2, n=300)
    s = dict(zip(M.STATS, st + g1))
    assert abs(s["observations"] / s["encounters"] - 0.5 * 298) < 1.0
    assert abs(s["flips"] / s["observations"] - 0.02) < 0.001


def test_reset_and_shared_mutation():
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b import model as m4b
    assert M.mutate_detail is m4b.mutate_detail
    n = 20
    VT = np.zeros((n, n), np.uint8)
    M.play(np.ones(n, np.bool_), np.zeros(n, np.bool_), 0, 3.0, 1.0, 0.8, 0.5, 0.1, 0.02, M.TEST,
           np.zeros(M.NST), VT, False)
    assert (VT + np.eye(n, dtype=np.uint8) == 1).all()


def test_differs_from_rung5a_only_in_judging():
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import model as m5a
    # with every observer agreeing with the donor, the two models give identical runs
    a = m5a.run(0.8, 1.0, 0.0, 0.0, 0.0, (0.0, 1.0, 0.0), m5a.TEST, 3, gens=3, n=40)
    b = M.run(0.8, 1.0, 0.0, 0.0, 0.0, (0.0, 1.0, 0.0), M.TEST, 3, gens=3, n=40)
    assert np.array_equal(a[0], b[0])


# copied from rung 5a's tests (shared mechanics)
def test_shuffled_target_excludes_donor_and_recipient():
    M._seed(3)
    seen = np.zeros(10, int)
    for _ in range(20000):
        seen[M._other(10, 2, 7)] += 1
    assert seen[2] == 0 and seen[7] == 0
    others = seen[[0, 1, 3, 4, 5, 6, 8, 9]]
    assert others.min() > 2200 and others.max() < 2800


def test_production_masks_independent():
    M._seed(31)
    n, reps = 64, 20000
    obs = np.zeros(n, np.bool_)
    fl = np.zeros(n, np.bool_)
    O = np.zeros((reps, n), np.bool_)
    F = []
    gap = M._geom(0.1)
    for t in range(reps):
        gap = M.draw_masks(n, 3, 40, 0.5, 0.1, gap, obs, fl)
        O[t] = obs
        F.extend(fl[obs].tolist())
    assert not O[:, 3].any() and not O[:, 40].any()
    cols = [w for w in range(n) if w not in (3, 40)]
    m = O[:, cols].mean(0)
    assert np.abs(m - 0.5).max() < 0.02
    cc = np.corrcoef(O[:, cols].T.astype(float))
    off = cc[~np.eye(len(cols), dtype=bool)]
    assert np.abs(off).max() < 0.04                          # observers independent of each other
    F = np.array(F, float)
    assert abs(F.mean() - 0.1) < 0.005
    assert abs(np.corrcoef(F[:-1], F[1:])[0, 1]) < 0.02      # flips independent along successive observations
    # flips only fall on observers
    gap = M.draw_masks(n, 3, 40, 0.5, 0.9, 0, obs, fl)
    assert not (fl & ~obs).any()
