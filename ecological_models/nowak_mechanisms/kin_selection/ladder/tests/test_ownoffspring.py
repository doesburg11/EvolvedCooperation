"""Tests for the ownoff test mode and the offpool control (STEP5_OWNOFFSPRING.md)."""

import numpy as np

from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model_rung1 as R1


def _blank(P, n=10):
    S = P * n
    return (np.zeros(S, bool), np.zeros(S), np.arange(S, dtype=np.int64) + 1, np.full(S, -1, np.int64))


def test_modes_0_to_4_byte_identical_to_rung1_code():
    for mode, b in ((0, 0.0), (1, 0.07), (2, 0.14), (3, 0.07), (4, 0.14)):
        for route in (False, True):
            kw = dict(seed=41, b=b, c=0.005 if b else 0.0, mode=mode, T=500, sample_dt=100.0, P=200, nb_pairs=2000,
                      route=route, h0_mean=0.4, h0_sd=0.2)
            a, z = R1.run(**kw), E.run(**kw)
            assert a["events"] == z["events"]
            assert a["samples"].tobytes() == z["samples"].tobytes() and a["hists"].tobytes() == z["hists"].tobytes()


def test_ownoff_delivers_only_to_own_offspring_at_home():
    P, n, b = 2, 10, 0.3
    occ, h, ident, parent = _blank(P)
    occ[[0, 1, 2, 3, 10]] = True
    h[0] = 1.0
    parent[1] = parent[2] = ident[0]          # two offspring at home
    parent[10] = ident[0]                      # one dispersed to patch 1: gets nothing
    gift = np.zeros(P * n)
    for p in range(P):
        E._recompute_patch(p, n, occ, h, ident, parent, gift, b, E.OWNOFF)
    assert abs(gift[1] - b / 2) < 1e-12 and abs(gift[2] - b / 2) < 1e-12
    assert gift[0] == 0.0 and gift[3] == 0.0 and gift[10] == 0.0
    assert gift.max() <= b + 1e-12                                     # one parent: at most b per recipient
    # the parent dies: its gifts stop at once
    occ[0] = False
    E._recompute_patch(0, n, occ, h, ident, parent, gift, b, E.OWNOFF)
    assert gift[:n].sum() == 0.0
    # a newcomer settles on the dead parent's site with a new identity: it is not the offspring's parent
    occ[0] = True
    ident[0] = 999
    E._recompute_patch(0, n, occ, h, ident, parent, gift, b, E.OWNOFF)
    assert gift[:n].sum() == 0.0
    # no offspring at home: the gift is lost
    occ2, h2, id2, par2 = _blank(1)
    occ2[[0, 1]] = True
    h2[0] = 1.0
    g2 = np.zeros(n)
    E._recompute_patch(0, n, occ2, h2, id2, par2, g2, b, E.OWNOFF)
    assert g2.sum() == 0.0


def test_offpool_eligibility_class_totals_and_own_patch_exclusion():
    rng = np.random.default_rng(3)
    P, n, b = 300, 10, 0.2
    occ = rng.random(P * n) < 0.5
    h = np.where(occ, rng.random(P * n), 0.0)
    ident = np.arange(P * n, dtype=np.int64) + 1
    parent = np.full(P * n, -1, np.int64)
    for j in np.flatnonzero(occ):
        mates = [m for m in range((j // n) * n, (j // n + 1) * n) if occ[m] and m != j]
        if mates and rng.random() < 0.4:
            parent[j] = ident[rng.choice(mates)]
    cnt = occ.reshape(P, n).sum(1).astype(np.int64)
    gift = np.zeros(P * n)
    for p in range(P):
        E._recompute_patch(p, n, occ, h, ident, parent, gift, b, E.OWNOFF)
    Dp = np.array([E._eligible_sum(p, n, occ, h, ident, parent, b, True) for p in range(P)])
    for p in range(P):                                                  # eligible sum = ownoff delivery
        assert abs(gift[p * n:(p + 1) * n].sum() - Dp[p]) < 1e-12
    Dcls = np.zeros(n + 1)
    PC = np.zeros(n + 1, np.int64)
    for p in range(P):
        Dcls[cnt[p]] += Dp[p]
        PC[cnt[p]] += 1
    pool = np.zeros(P * n)
    for p in range(P):
        for q in range(n):
            if occ[p * n + q]:
                pool[p * n + q] = E._pool_gift(p, cnt[p], Dp, Dcls, PC)
    pcls = np.repeat(cnt, n)
    for i in range(1, n + 1):
        sel = occ & (pcls == i)
        if PC[i] >= 2:
            assert abs(pool[sel].sum() - gift[sel].sum()) < 1e-9
        elif PC[i] == 1:
            assert pool[sel].sum() == 0.0
    assert pool.max() <= b + 1e-12
    # a lone donor patch with its offspring: none of its own patch's gift comes back
    occ3, h3, id3, par3 = _blank(3)
    occ3[[0, 1, 10, 11, 20, 21, 22]] = True
    h3[0] = 1.0
    par3[1] = id3[0]
    D3 = np.array([E._eligible_sum(p, 10, occ3, h3, id3, par3, 0.3, True) for p in range(3)])
    c3 = np.array([2, 2, 3])
    Dc3 = np.zeros(11); PC3 = np.zeros(11, np.int64)
    for p in range(3):
        Dc3[c3[p]] += D3[p]; PC3[c3[p]] += 1
    assert E._pool_gift(0, 2, D3, Dc3, PC3) == 0.0 and abs(E._pool_gift(1, 2, D3, Dc3, PC3) - 0.15) < 1e-12
    assert E._pool_gift(2, 3, D3, Dc3, PC3) == 0.0


def _final_state_fecundity(mode, seed):
    """Run simulate directly, then compare the last sample's mean fecundity with a from-scratch recomputation."""
    P, n, b, c = 60, 10, 0.3, 0.005
    S = P * n
    rng = np.random.default_rng(seed)
    occ = rng.random(S) < 0.5
    h = np.where(occ, rng.random(S), 0.0)
    ident = np.arange(S, dtype=np.int64)
    parent = np.full(S, -1, np.int64)
    marker = np.arange(S, dtype=np.int64)
    counters = np.array([0.0, 0.0, float(S), float(S), 0.0])
    E._seed(seed)
    out = np.empty((21, len(E.COLS)))
    hs = np.empty((21, n + 1), np.int64)
    E.simulate(P, n, 0.5, b, c, mode, 5, 0.02, 0.04, 0.001, 2000.0, 100.0, occ, h, ident, parent, marker, 500, out, hs,
               counters, True, np.array([5], np.uint64))
    cnt = occ.reshape(P, n).sum(1).astype(np.int64)
    if mode == E.OWNOFF:
        g = np.zeros(S)
        for p in range(P):
            E._recompute_patch(p, n, occ, h, ident, parent, g, b, E.OWNOFF)
    else:
        Dp = np.array([E._eligible_sum(p, n, occ, h, ident, parent, b, True) for p in range(P)])
        Dc = np.zeros(n + 1); PC = np.zeros(n + 1, np.int64)
        for p in range(P):
            Dc[cnt[p]] += Dp[p]; PC[cnt[p]] += 1
        g = np.array([E._pool_gift(j // n, cnt[j // n], Dp, Dc, PC) for j in range(S)])
    f = (1 - c * h + g)[occ]
    return out, f.mean(), counters[0]


def test_dynamic_caches_match_full_recomputation():
    for mode in (E.OWNOFF, E.OFFPOOL):
        out, fmean, events = _final_state_fecundity(mode, 7)
        assert events > 20_000
        assert abs(out[-1, 4] - fmean) < 1e-12
        if mode == E.OFFPOOL:
            assert np.nanmax(out[:, 22]) < 1e-9
    o = E.run(seed=43, b=0.3, c=0.005, mode=E.OFFPOOL, T=3000, sample_dt=50.0, P=30, nb_pairs=200, chunk_T=50.0,
              h0_mean=0.6, h0_sd=0.3, route=True)
    assert np.nanmax(o["samples"][:, 22]) < 1e-9
    assert {0, 1, 5, 6} <= set(np.flatnonzero(o["hists"].sum(0) > 0))


def test_route_contrast_and_with_offspring_share():
    kw = dict(b=0.07, c=0.005, T=3000, sample_dt=100.0, P=600, nb_pairs=5000, h0_mean=0.5, h0_sd=0.2, route=True)

    def R(o):
        s = o["samples"][10:]
        w = s[:, 15].sum()
        q, qr = s[:, 16].sum() / w, s[:, 17].sum() / w
        return (q - qr) / (1 - qr)

    of = E.run(seed=44, mode=E.OWNOFF, **kw)
    xo = E.run(seed=44, mode=E.OFFPOOL, **kw)
    assert R(of) > 0.95 and abs(R(xo)) < 0.02
    for o in (of, xo):
        s = o["samples"][1:]
        assert np.all((s[:, 21] > 0.1) & (s[:, 21] < 0.35))           # share of donors with an offspring at home
        assert np.allclose(s[:, 18] + s[:, 19], s[:, 8])
    assert np.all(of["samples"][1:, 19] == 0.0)
    no = E.run(seed=44, mode=E.NONOFF, **kw)
    assert np.isnan(no["samples"][:, 21]).all()                         # column 21 only for the own-offspring modes


def test_rung2_classification_and_registered_settings():
    from ecological_models.nowak_mechanisms.kin_selection.ladder import run_ownoffspring as R

    def arm(hs, viable=20):
        return [dict(viable=i < viable, final_h=x if i < viable else None, reached=i < viable and x >= 0.6)
                for i, x in enumerate(hs)]

    base = {"N0": arm([0.3] * 20), "XO14": arm([0.02] * 20), "OF3.5": arm([0.02] * 20)}
    v, h2, h3, d = R.classify(dict(base, OF14=arm([0.7] * 20)), 0.9)
    assert v.startswith("met: through parental care") and h2 == h3 == "supported"
    assert R.classify(dict(base, OF14=arm([0.7] * 20)), float("nan"))[0].startswith("not interpretable: no relatedness")
    assert R.classify(dict(base, OF14=arm([0.7] * 20)), None)[0].startswith("not interpretable: no relatedness")
    assert R.classify(dict(base, OF14=arm([0.7] * 14 + [0.5] * 6)), 0.9)[0] == "not met"
    assert R.classify(dict(base, OF14=arm([0.7] * 20), XO14=arm([0.7] * 3 + [0.0] * 17)), 0.9)[0] == \
        "not met: the control did not separate"
    assert R.SEEDS == list(range(200, 220)) and R.ARMS["OF14"] == (5, 0.07, 0.005) and R.ARMS["XO14"][0] == 6
    assert R.ARMS["OF3.5"] == (5, 0.0175, 0.005) and R.T_M == 100_000.0 and R.power_proxy() == 8000.0


def test_ownoff_per_breeder_cache_check_through_events():
    # many events in a small population, chunk restarts: the cached per-breeder gifts equal a full recomputation
    o = E.run(seed=45, b=0.3, c=0.005, mode=E.OWNOFF, T=3000, sample_dt=50.0, P=30, nb_pairs=200, chunk_T=50.0,
              h0_mean=0.6, h0_sd=0.3, route=True)
    err = o["samples"][:, 22]
    assert np.isfinite(err[o["samples"][:, 0] > 0]).all() and np.nanmax(err) == 0.0 and o["events"] > 50_000


def test_rung2_validation_and_blind_smoke(tmp_path, monkeypatch, capsys):
    import json
    import pytest
    from ecological_models.nowak_mechanisms.kin_selection.ladder import run_ownoffspring as R
    o = E.run(seed=46, b=0.07, c=0.005, mode=E.OWNOFF, T=2000, sample_dt=1000.0, P=1000, nb_pairs=100, route=True)
    job = dict(stage="M", name="OF14_s0", arm="OF14", seed=46, mode=5, b=0.07, c=0.005, T=2000.0, dt=1000.0)
    meta = json.dumps(dict(job, code_sha="x", commit="y"))
    good = tmp_path / "good.npz"
    np.savez_compressed(good, samples=o["samples"], hists=o["hists"], meta=meta)
    R.validate(good, job, "x", "y")
    for cols in ((15, 18), (22, 23)):
        s = o["samples"].copy(); s[1:, cols[0]:cols[1]] = np.nan
        bad = tmp_path / "bad.npz"
        np.savez_compressed(bad, samples=s, hists=o["hists"], meta=meta)
        with pytest.raises(ValueError):
            R.validate(bad, job, "x", "y")
