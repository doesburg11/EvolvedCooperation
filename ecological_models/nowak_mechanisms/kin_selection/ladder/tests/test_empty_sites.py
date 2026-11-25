"""Tests for the empty-site island model (STEP5_EMPTY_SITES.md)."""

import numpy as np

from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E


def _patch_state(n=10):
    occ = np.zeros(n, bool); h = np.zeros(n); ident = np.arange(n, dtype=np.int64) + 100
    parent = np.full(n, -1, np.int64)
    return occ, h, ident, parent


def test_patch_gift_formula_in_sample():
    # one patch: breeders with h = 1, 0, 0 -> each of the two others gets b/2; the donor gets 0
    P, n = 1, 10
    occ, h, ident, parent = _patch_state(n)
    occ[:3] = True; h[0] = 1.0
    marker = np.arange(n, dtype=np.int64)
    cnt = np.array([3]); Hp = np.array([1.0]); gift = np.zeros(n)
    row = np.empty(len(E.COLS)); hist = np.empty(n + 1, np.int64)
    E._seed(0)
    E._sample(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, 0.2, 0.1, E.PATCH, 1.0, 3, 10, row, hist)
    # mean fecundity = [(1 - 0.1) + (1 + 0.1) + (1 + 0.1)] / 3
    assert abs(row[4] - (0.9 + 1.1 + 1.1) / 3) < 1e-12
    assert row[8] == 0.0 and hist[3] == 1


def test_nonoffspring_gift_excludes_own_offspring():
    n = 10
    occ, h, ident, parent = _patch_state(n)
    occ[:4] = True
    h[0] = 1.0                     # donor id 100
    parent[1] = 100                # breeder 1 is the donor's offspring
    gift = np.zeros(n)
    E._recompute_patch(0, n, occ, h, ident, parent, gift, 0.3, E.NONOFF)
    assert gift[1] == 0.0 and gift[0] == 0.0
    assert abs(gift[2] - 0.15) < 1e-12 and abs(gift[3] - 0.15) < 1e-12
    # only offspring present -> gift lost
    occ[2:] = False
    E._recompute_patch(0, n, occ, h, ident, parent, gift, 0.3, E.NONOFF)
    assert gift.sum() == 0.0


def test_lone_breeder_gift_lost_and_offspring_share():
    P, n = 2, 10
    occ = np.zeros(P * n, bool); h = np.zeros(P * n)
    ident = np.arange(P * n, dtype=np.int64) + 100; parent = np.full(P * n, -1, np.int64)
    marker = np.arange(P * n, dtype=np.int64)
    occ[0] = True; h[0] = 1.0                          # alone in patch 0 -> all its gift is lost
    occ[10:12] = True; h[10] = 1.0; parent[11] = ident[10]   # patch 1: donor and its own offspring
    cnt = np.array([1, 2]); Hp = np.array([1.0, 1.0]); gift = np.zeros(P * n)
    row = np.empty(len(E.COLS)); hist = np.empty(n + 1, np.int64)
    E._sample(P, n, occ, h, ident, parent, marker, gift, cnt, Hp, 0.1, 0.0, E.PATCH, 2.0, 3, 10, row, hist)
    assert abs(row[8] - 0.5) < 1e-12          # half of all gifts (the lone donor's) lost
    assert abs(row[7] - 0.5) < 1e-12          # the other half goes to own offspring


def test_neutral_occupancy_matches_theory():
    # theory (Alizon and Taylor 2008, n = 10, k = 0.5, stay if i <= 5): mean occupancy 0.535
    o = E.run(seed=3, b=0.0, c=0.0, mode=E.NONE, T=3000, sample_dt=100.0, mu=0.0, h_fixed=0.0, nb_pairs=1000)
    occ = o["samples"][10:, 3].mean()
    assert abs(occ - 0.535) < 0.01


def test_markers_unique_at_start_and_mutation_changes_h():
    o = E.run(seed=4, b=0.0, c=0.0, mode=E.NONE, T=500, sample_dt=100.0, mu=1.0, sd=0.1, nb_pairs=2000, P=200)
    s0 = o["samples"][0]
    assert s0[5] == 0.0 and s0[6] == 0.0      # all founder markers distinct
    assert o["samples"][-1, 2] > s0[2]        # h variance grows with mutation
    assert o["births"] > 0 and o["events"] > o["births"]


def test_stay_switch_at_five_and_six():
    E._seed(5)
    assert all(E._target(5, 5, 3, 1000) == 3 for _ in range(200))          # 5 breeders: stay home
    dest = [E._target(6, 5, 3, 1000) for _ in range(2000)]                  # 6 breeders: random patch
    assert np.mean(np.array(dest) == 3) < 0.01 and len(set(dest)) > 800


def test_nonoffspring_cache_unaffected_by_offspring_elsewhere():
    # the donor's offspring living in another patch does not change the donor's local recipients
    P, n = 2, 10
    occ = np.zeros(P * n, bool); h = np.zeros(P * n)
    ident = np.arange(P * n, dtype=np.int64) + 100; parent = np.full(P * n, -1, np.int64)
    occ[[0, 1, 10]] = True; h[0] = 1.0; parent[10] = ident[0]
    gift = np.zeros(P * n)
    E._recompute_patch(0, n, occ, h, ident, parent, gift, 0.2, E.NONOFF)
    assert abs(gift[1] - 0.2) < 1e-12 and gift[10] == 0.0


def test_off_grid_lengths_rejected():
    import pytest
    with pytest.raises(ValueError):
        E.run(seed=1, b=0.0, c=0.0, mode=E.NONE, T=150.0, sample_dt=100.0, P=10, nb_pairs=10)


def test_classification_thresholds():
    from ecological_models.nowak_mechanisms.kin_selection.ladder.run_empty_sites import classify

    def arm(hs, viable=20):
        return [dict(viable=i < viable, final_h=h if i < viable else None, reached=i < viable and h >= 0.6)
                for i, h in enumerate(hs)]
    base = {"N0": arm([0.3] * 20), "X14": arm([0.05] * 20), "T3.5": arm([0.02] * 20)}
    v, h2, d = classify(dict(base, T14=arm([0.7] * 15 + [0.4] * 5), NO14=arm([0.7] * 20)))
    assert v == "met: among non-offspring relatives" and h2 == "supported" and d["T14_above_N0_pairs"] == 20
    v, _, _ = classify(dict(base, T14=arm([0.7] * 14 + [0.4] * 6), NO14=arm([0.7] * 20)))
    assert v == "not met"
    v, _, _ = classify(dict(base, T14=arm([0.7] * 20), NO14=arm([0.7] * 14 + [0.1] * 6)))
    assert v == "met: help to patch-mates, own offspring not excluded"
    v, _, _ = classify(dict(base, X14=arm([0.7] * 3 + [0.0] * 17), T14=arm([0.7] * 20), NO14=arm([0.7] * 20)))
    assert v == "not met: the control did not separate"
    v, _, _ = classify(dict(base, T14=arm([0.7] * 20, viable=17), NO14=arm([0.7] * 20)))
    assert v == "not interpretable"
    v, h2, _ = classify(dict(base, **{"T3.5": arm([0.5] * 20)}, T14=arm([0.7] * 20), NO14=arm([0.7] * 20)))
    assert h2 == "not supported"


def test_global_mode_fecundity_and_extinction_safe():
    o = E.run(seed=6, b=0.07, c=0.005, mode=E.GLOBAL, T=300, sample_dt=100.0, nb_pairs=1000, P=100, h_fixed=1.0, mu=0.0)
    # all h = 1: f = 1 - c + b * (N - 1)/(N - 1) = 1.065 for everyone
    assert abs(o["samples"][-1, 4] - 1.065) < 1e-9
    o = E.run(seed=7, b=0.0, c=0.0, mode=E.NONE, T=50, sample_dt=1.0, k=50.0, nb_pairs=100, P=20)   # dies out
    assert o["samples"][-1, 0] == 0 and np.isnan(o["samples"][-1, 1])
    assert o["samples"][-1, 3] == 0.0 and o["hists"][-1, 0] == 20
    assert len(o["samples"]) == 51
