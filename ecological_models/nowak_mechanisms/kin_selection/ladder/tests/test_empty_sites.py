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
    o = E.run(seed=3, b=0.0, c=0.0, mode=E.NONE, T=3000, mu=0.0, h_fixed=0.0, nb_pairs=1000)
    occ = o["samples"][10:, 3].mean()
    assert abs(occ - 0.535) < 0.01


def test_markers_unique_at_start_and_mutation_changes_h():
    o = E.run(seed=4, b=0.0, c=0.0, mode=E.NONE, T=500, mu=1.0, sd=0.1, nb_pairs=2000, P=200)
    s0 = o["samples"][0]
    assert s0[5] == 0.0 and s0[6] == 0.0      # all founder markers distinct
    assert o["samples"][-1, 2] > s0[2]        # h variance grows with mutation
    assert o["births"] > 0 and o["events"] > o["births"]


def test_stay_rule_keeps_offspring_home_in_sparse_patches():
    # no deaths; one patch starts with 2 breeders, the rest empty. Offspring stay while the patch has <= 5
    # breeders, so no other patch can be colonised before the first one holds 6.
    P, n = 30, 10
    occ = np.zeros(P * n, bool); occ[:2] = True
    h = np.zeros(P * n); ident = np.arange(P * n, dtype=np.int64); parent = np.full(P * n, -1, np.int64)
    marker = np.arange(P * n, dtype=np.int64)
    out = np.empty((3, len(E.COLS))); hists = np.empty((3, n + 1), np.int64)
    counters = np.array([0.0, 0.0, float(P * n), float(P * n), 0.0])
    E._seed(5)
    E.simulate(P, n, 0.0, 0.0, 0.0, E.NONE, 5, 0.0, 0.0, 0.0, 0.2, 0.1, occ, h, ident, parent, marker, 10, out,
               hists, counters)
    first = occ[:n].sum()
    others = occ[n:].sum()
    assert others == 0 or first >= 6


def test_global_mode_fecundity_and_extinction_safe():
    o = E.run(seed=6, b=0.07, c=0.005, mode=E.GLOBAL, T=300, nb_pairs=1000, P=100, h_fixed=1.0, mu=0.0)
    # all h = 1: f = 1 - c + b * (N - 1)/(N - 1) = 1.065 for everyone
    assert abs(o["samples"][-1, 4] - 1.065) < 1e-9
    o = E.run(seed=7, b=0.0, c=0.0, mode=E.NONE, T=50, sample_dt=1.0, k=50.0, nb_pairs=100, P=20)   # dies out
    assert o["samples"][-1, 0] == 0 and np.isnan(o["samples"][-1, 1])
    assert len(o["samples"]) == 51
