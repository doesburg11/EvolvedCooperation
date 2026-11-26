"""Tests for the rung-5a model: scripted comparison with an independent reference, corruption tests, sampling."""

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import model as M
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a.tests.reference import PrivateViews


def _vt_from(ref):
    n = ref.n
    VT = np.zeros((n, n), np.uint8)
    for (w, t), g in ref.views.items():
        VT[t, w] = 1 if g else 0
    return VT


def _masks(n, observers, flipped):
    obs = np.zeros(n, np.bool_)
    fl = np.zeros(n, np.bool_)
    for w in observers:
        obs[w] = True
    for w in flipped:
        fl[w] = True
    return obs, fl


def _act(VT, ref, d, r, helped, observers, flipped, image=False):
    obs, fl = _masks(VT.shape[0], observers, flipped)
    don_b, rec_b = VT[d].copy(), VT[r].copy()
    cnt = M.apply_act(VT, d, r, helped, obs, fl, image)
    assert cnt == len(observers)
    assert M.check_act(VT, d, r, helped, obs, fl, image, don_b, rec_b) == 0
    ref.assess(d, r, helped, observers, set(flipped), image)
    assert np.array_equal(VT, _vt_from(ref))


def test_scripted_acts_match_reference_including_disagreement_and_stale_recipient():
    n = 6
    ref = PrivateViews(n)
    VT = _vt_from(ref)
    # 0 = ALLD refuses 1; observers 2, 3 see it -> they mark 0 bad; 1 (recipient) keeps 0 good (stale)
    _act(VT, ref, 0, 1, False, [2, 3], [])
    assert VT[0, 2] == 0 and VT[0, 3] == 0 and VT[0, 1] == 1 and VT[0, 4] == 1
    # DISC 2 refuses 0 (2 sees 0 bad): observer 3 also sees 0 bad -> 2 stays good; observer 4 sees 0 good -> 2 bad
    intends, helped = ref.decide("DISC", 2, 0, consulted=True, failed=False)
    assert not intends and VT[0, 2] == 0
    _act(VT, ref, 2, 0, helped, [3, 4], [])
    assert VT[2, 3] == 1 and VT[2, 4] == 0
    # the stale recipient 1 (sees 0 good) would help 0, unlike a public record
    intends, _ = ref.decide("DISC", 1, 0, consulted=True, failed=False)
    assert intends and VT[0, 1] == 1
    # a flip turns a deserved good into bad for one observer only
    _act(VT, ref, 5, 3, True, [1, 2, 4], [2])
    assert VT[5, 2] == 0 and VT[5, 1] == 1 and VT[5, 4] == 1
    # image scoring: refusal is bad whatever the observer thinks of the recipient
    _act(VT, ref, 3, 0, False, [5], [], image=True)
    assert VT[3, 5] == 0


@pytest.mark.parametrize("corrupt", ["nonobserver", "recipient", "wrong_rule", "missing_write"])
def test_check_act_catches_corruption(corrupt):
    n = 8
    rng = np.random.default_rng(1)
    VT = rng.integers(0, 2, (n, n)).astype(np.uint8)
    d, r, helped = 2, 5, False
    obs, fl = _masks(n, [0, 1, 3, 6], [3])
    don_b, rec_b = VT[d].copy(), VT[r].copy()
    M.apply_act(VT, d, r, helped, obs, fl, False)
    if corrupt == "nonobserver":
        VT[d, 4] ^= 1
    elif corrupt == "recipient":
        VT[r, 0] ^= 1
    elif corrupt == "wrong_rule":
        VT[d, 0] ^= 1
    else:
        VT[d, 6] = don_b[6] if VT[d, 6] != don_b[6] else 1 - VT[d, 6]
    assert M.check_act(VT, d, r, helped, obs, fl, False, don_b, rec_b) > 0


def test_generation_reset_and_counters():
    cnt, au, st, g1 = M.run(0.8, 0.5, 0.1, 0.02, 0.001, (0.1, 0.8, 0.1), M.TEST, 5, gens=3, n=60)
    s = dict(zip(M.STATS, st + g1))
    assert s["check_mismatch"] == 0 and s["sanity_violations"] == 0
    assert s["encounters"] == 60 * 10 * 3 and (au[:, 9] == 600).all()
    assert s["flips"] <= s["observations"] <= s["encounters"] * 58
    assert s["consult_disc"] <= s["disc_turns"] and s["helps"] <= s["encounters"]
    # every generation starts from all-good views: generation-1 good shares are high
    assert g1[22] / g1[23] > 0.8 and g1[24] / g1[25] > 0.8


def test_observation_and_flip_rates():
    cnt, au, st, g1 = M.run(0.8, 0.5, 0.1, 0.02, 0.0, (0.0, 1.0, 0.0), M.TEST, 7, gens=2, n=300)
    s = dict(zip(M.STATS, st + g1))
    per_enc = s["observations"] / s["encounters"]
    assert abs(per_enc - 0.5 * 298) < 1.0                       # o (N - 2)
    assert abs(s["flips"] / s["observations"] - 0.02) < 0.001   # a per observation


def test_shuffled_target_excludes_donor_and_recipient():
    M._seed(3)
    seen = np.zeros(10, int)
    for _ in range(20000):
        seen[M._other(10, 2, 7)] += 1
    assert seen[2] == 0 and seen[7] == 0
    others = seen[[0, 1, 3, 4, 5, 6, 8, 9]]
    assert others.min() > 2200 and others.max() < 2800


def test_reproduction_and_mutation_shared_with_rung4b():
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b import model as m4b
    assert M.mutate_detail is m4b.mutate_detail
    cnt, au, _, _ = M.run(0.8, 0.5, 0.1, 0.02, 0.01, (0.0, 1.0, 0.0), M.TEST, 2, gens=5, n=80)
    pre_c, pre_d, pre_a, m_c, m_d, m_a, c_d, d_c, a_c, _ = au.T
    assert (pre_c + pre_d + pre_a == 80).all()
    assert np.array_equal(pre_a - m_a + (m_c - c_d) + (m_d - d_c), cnt[1:, 0])
    assert np.array_equal(pre_c - m_c + d_c + a_c, cnt[1:, 1])


def test_production_encounter_matches_reference():
    # drive the production encounter with scripted draws and compare decisions and views with the reference
    n = 7
    is_disc = np.array([True, True, False, False, True, False, True])
    is_allc = np.array([False, False, True, False, False, False, False])
    strat = ["DISC" if is_disc[t] else ("ALLC" if is_allc[t] else "ALLD") for t in range(n)]
    ref = PrivateViews(n)
    VT = _vt_from(ref)
    stats = np.zeros(M.NST)
    db, rb = np.empty(n, np.uint8), np.empty(n, np.uint8)
    script = [  # donor, recipient, consult_u, fail_u, observers, flipped
        (3, 0, 1.0, 1.0, [1, 2, 4], []),       # ALLD refuses 0
        (1, 3, 0.1, 1.0, [0, 2, 5], []),       # DISC 1 consults its good view of 3: helps
        (4, 3, 0.1, 1.0, [0, 1, 2], [2]),      # DISC 4 sees 3 good: helps; observer 2 flipped
        (0, 3, 0.1, 1.0, [1, 5, 6], []),       # DISC 0: its view of 3 is good (it did not observe 3's refusal)
        (6, 3, 0.9, 0.0, [1, 2], []),          # DISC 6 does not consult, help fails
        (2, 1, 1.0, 0.05, [0, 3, 6], []),      # ALLC 2 intends, fails (e = 0.1)
    ]
    for d, r, cu, fu, obs, fl in script:
        observed, flip = _masks(n, obs, fl)
        helped, _ = M.encounter(VT, d, r, is_disc, is_allc, cu, fu, -1, observed, flip, 0.8, 0.1, M.TEST, stats, db, rb)
        consulted = bool(is_disc[d] and cu < 0.8)
        intends, ref_helped = ref.decide(strat[d], d, r, consulted, failed=fu < 0.1)
        assert helped == ref_helped, (d, r)
        ref.assess(d, r, ref_helped, obs, set(fl))
        assert np.array_equal(VT, _vt_from(ref)), (d, r)
    assert stats[0] == 0 and stats[1] == 0
    st = dict(zip(M.STATS, stats))
    for name, v in ref.counts.items():                     # counters computed independently by the reference
        assert st[name] == v, (name, st[name], v)


def test_reset_at_generation_start():
    n = 20
    VT = np.zeros((n, n), np.uint8)
    is_disc = np.ones(n, np.bool_)
    is_allc = np.zeros(n, np.bool_)
    M.play(is_disc, is_allc, 0, 3.0, 1.0, 0.8, 0.5, 0.1, 0.02, M.TEST, np.zeros(M.NST), VT, False)
    assert (VT + np.eye(n, dtype=np.uint8) == 1).all()            # off-diagonal all good, diagonal 0


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


def test_observation_and_flip_independence():
    # observation masks: neighbouring observers uncorrelated; flips: no autocorrelation along observations
    M._seed(21)
    n = 400
    cnt, au, st, g1 = M.run(0.8, 0.5, 0.1, 0.2, 0.0, (0.0, 1.0, 0.0), M.TEST, 8, gens=1, n=n)
    s = dict(zip(M.STATS, st + g1))
    assert abs(s["flips"] / s["observations"] - 0.2) < 0.005
    rng_masks = []
    M._seed(5)
    for _ in range(3000):
        bits = [M._geom(0.2) for _ in range(1)]
        rng_masks.append(bits[0])
    gaps = np.array(rng_masks)
    assert abs(gaps.mean() - 0.8 / 0.2) < 0.2                    # geometric gaps: mean (1 - a) / a
    assert abs(np.corrcoef(gaps[:-1], gaps[1:])[0, 1]) < 0.06     # successive gaps independent
