"""Tests for the class-pool control and gift-route statistics (STEP5_NONOFFSPRING.md)."""

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model as E
from ecological_models.nowak_mechanisms.kin_selection.ladder import empty_sites_model_step5 as OLD


def _state(P, n, rng, p_occ=0.5, off_frac=0.3):
    S = P * n
    occ = rng.random(S) < p_occ
    h = np.where(occ, rng.random(S), 0.0)
    ident = np.arange(S, dtype=np.int64) + 1000
    parent = np.full(S, -1, np.int64)
    for j in np.flatnonzero(occ):          # some breeders are the offspring of a patch-mate
        mates = [m for m in range((j // n) * n, (j // n + 1) * n) if occ[m] and m != j]
        if mates and rng.random() < off_frac:
            parent[j] = ident[rng.choice(mates)]
    return occ, h, ident, parent


def _caches(P, n, occ, h, ident, parent, b):
    cnt = occ.reshape(P, n).sum(1).astype(np.int64)
    Dp = np.array([E._eligible_sum(p, n, occ, h, ident, parent, b) for p in range(P)])
    Dcls = np.zeros(n + 1)
    PC = np.zeros(n + 1, np.int64)
    for p in range(P):
        Dcls[cnt[p]] += Dp[p]
        PC[cnt[p]] += 1
    return cnt, Dp, Dcls, PC


def test_existing_modes_byte_identical_to_step5_code():
    for mode, b, c in ((E.NONE, 0.0, 0.0), (E.PATCH, 0.07, 0.005), (E.NONOFF, 0.07, 0.005), (E.GLOBAL, 0.07, 0.005)):
        kw = dict(seed=21, b=b, c=c, mode=mode, T=500, sample_dt=100.0, P=200, nb_pairs=2000)
        a, z = OLD.run(**kw), E.run(**kw)
        assert a["events"] == z["events"] and a["births"] == z["births"]
        assert a["samples"].tobytes() == np.ascontiguousarray(z["samples"][:, :15]).tobytes()
        assert a["hists"].tobytes() == z["hists"].tobytes()


def test_route_statistics_do_not_change_the_run():
    for mode in (E.NONOFF, E.CLASSPOOL):
        kw = dict(seed=22, b=0.14, c=0.005, mode=mode, T=500, sample_dt=100.0, P=200, nb_pairs=2000)
        a, z = E.run(**kw), E.run(route=True, **kw)
        assert a["events"] == z["events"]
        assert np.array_equal(a["samples"][:, :15], z["samples"][:, :15], equal_nan=True)
        assert np.isnan(a["samples"][:, 15:22]).all() and np.isfinite(z["samples"][1:, 15]).all()


def test_classpool_preserves_class_totals_and_handles_singletons():
    rng = np.random.default_rng(1)
    P, n, b = 400, 10, 0.14
    occ, h, ident, parent = _state(P, n, rng)
    cnt, Dp, Dcls, PC = _caches(P, n, occ, h, ident, parent, b)
    gift_no = np.zeros(P * n)
    for p in range(P):
        E._recompute_patch(p, n, occ, h, ident, parent, gift_no, b, E.NONOFF)
    pool = np.zeros(P * n)
    for p in range(P):
        for q in range(n):
            if occ[p * n + q]:
                pool[p * n + q] = E._pool_gift(p, cnt[p], Dp, Dcls, PC)
    pcls = np.repeat(cnt, n)
    for i in range(1, n + 1):
        sel = occ & (pcls == i)
        if PC[i] >= 2:
            assert abs(pool[sel].sum() - gift_no[sel].sum()) < 1e-9          # class total and class mean preserved
            assert abs(pool[sel].sum() - Dcls[i]) < 1e-9
        elif PC[i] == 1:
            assert pool[sel].sum() == 0.0                                    # singleton class: nothing delivered
    assert pool.max() <= b + 1e-12                                           # fecundity bound 1 + b


def test_classpool_never_returns_a_gift_to_the_donors_patch():
    # two class-3 patches and one class-2 patch; only patch 0 has a donor
    P, n, b = 3, 10, 0.3
    occ = np.zeros(P * n, bool); h = np.zeros(P * n)
    ident = np.arange(P * n, dtype=np.int64) + 1; parent = np.full(P * n, -1, np.int64)
    occ[[0, 1, 2, 10, 11, 12, 20, 21]] = True
    h[0] = 1.0
    cnt, Dp, Dcls, PC = _caches(P, n, occ, h, ident, parent, b)
    assert E._pool_gift(0, 3, Dp, Dcls, PC) == 0.0                          # donor's own patch gets nothing
    assert abs(E._pool_gift(1, 3, Dp, Dcls, PC) - b / 3) < 1e-12           # the other class-3 patch gets it all
    assert E._pool_gift(2, 2, Dp, Dcls, PC) == 0.0                          # other classes get nothing
    # the donor's only patch-mates are its own offspring -> locally ineligible, nothing in the pool
    parent[1] = parent[2] = ident[0]
    cnt, Dp, Dcls, PC = _caches(P, n, occ, h, ident, parent, b)
    assert Dp[0] == 0.0 and E._pool_gift(1, 3, Dp, Dcls, PC) == 0.0
    # a singleton class: the donor's patch is the only class-3 patch -> lost
    parent[:] = -1
    occ[12] = False                                                          # patch 1 becomes class 2
    cnt, Dp, Dcls, PC = _caches(P, n, occ, h, ident, parent, b)
    assert PC[3] == 1 and Dp[0] > 0 and all(E._pool_gift(p, cnt[p], Dp, Dcls, PC) == 0.0 for p in range(P))


def test_classpool_cache_stays_exact_through_many_events_and_chunks():
    # small population with many class transitions (0<->1, 5<->6), restarts every 50 time units
    o = E.run(seed=23, b=0.14, c=0.005, mode=E.CLASSPOOL, T=3000, sample_dt=50.0, P=30, nb_pairs=200,
              chunk_T=50.0, h0_mean=0.6, h0_sd=0.3, route=True)
    err = o["samples"][:, 22]
    assert np.nanmax(err) < 1e-9 and o["events"] > 50_000
    seen = set(np.flatnonzero(o["hists"].sum(0) > 0))
    assert {0, 1, 5, 6} <= seen
    o = E.run(seed=24, b=0.14, c=0.005, mode=E.CLASSPOOL, T=2000, sample_dt=100.0, P=500, nb_pairs=1000,
              h0_mean=0.5, h0_sd=0.3)
    assert np.nanmax(o["samples"][:, 22]) < 1e-9


def test_route_relatedness_contrast_and_loss_split():
    kw = dict(b=0.14, c=0.005, T=3000, sample_dt=100.0, P=600, nb_pairs=5000, h0_mean=0.5, h0_sd=0.2, route=True)

    def R(o):
        s = o["samples"][10:]
        w = s[:, 15].sum()
        q, qr = s[:, 16].sum() / w, s[:, 17].sum() / w
        return (q - qr) / (1 - qr)

    no = E.run(seed=25, mode=E.NONOFF, **kw)
    xc = E.run(seed=25, mode=E.CLASSPOOL, **kw)
    assert R(no) > 0.03 and abs(R(xc)) < 0.02
    s = no["samples"][1:]
    assert np.all(s[:, 19] == 0.0)                                          # no singleton loss outside classpool
    assert np.allclose(s[:, 18], s[:, 8], equal_nan=True)                   # nonoff: all loss is local
    s = xc["samples"][1:]
    assert np.allclose(s[:, 18] + s[:, 19], s[:, 8])                        # classpool: the two kinds add up
    assert (s[:, 20] > 0).all() and (s[:, 20] < 0.2).all()                 # own-offspring share of patch-mates


def test_eligible_sum_matches_nonoff_delivery():
    rng = np.random.default_rng(2)
    P, n, b = 200, 10, 0.2
    occ, h, ident, parent = _state(P, n, rng, off_frac=0.6)
    gift = np.zeros(P * n)
    for p in range(P):
        E._recompute_patch(p, n, occ, h, ident, parent, gift, b, E.NONOFF)
        assert abs(gift[p * n:(p + 1) * n].sum() - E._eligible_sum(p, n, occ, h, ident, parent, b)) < 1e-12


def test_extinction_and_empty_rows_with_classpool():
    o = E.run(seed=26, b=0.14, c=0.005, mode=E.CLASSPOOL, T=50, sample_dt=1.0, k=50.0, nb_pairs=100, P=20,
              route=True)
    assert o["samples"][-1, 0] == 0 and np.isnan(o["samples"][-1, 15:22]).all()


def test_off_grid_still_rejected():
    with pytest.raises(ValueError):
        E.run(seed=1, b=0.0, c=0.0, mode=E.CLASSPOOL, T=150.0, sample_dt=100.0, P=10, nb_pairs=10)


def test_route_does_not_hang_when_all_breeders_share_one_patch():
    P, n = 3, 10
    occ = np.zeros(P * n, bool); h = np.zeros(P * n)
    ident = np.arange(P * n, dtype=np.int64) + 1; parent = np.full(P * n, -1, np.int64)
    marker = np.arange(P * n, dtype=np.int64)
    occ[[0, 1]] = True; h[[0, 1]] = 0.5
    cnt = occ.reshape(P, n).sum(1).astype(np.int64)
    olist = np.flatnonzero(occ).astype(np.int64)
    PC = np.bincount(cnt, minlength=n + 1).astype(np.int64)
    row = np.full(len(E.COLS), -1.0)
    E._route(P, n, occ, h, ident, parent, marker, cnt, 0.14, E.NONOFF, olist, 2, PC, np.array([7], np.uint64), row, 15)
    assert row[15] == 0.0 and row[16] == 0.0 and row[17] == 0.0      # donors skipped: no reference population


def _arm(hs, viable=20):
    return [dict(viable=i < viable, final_h=x if i < viable else None, reached=i < viable and x >= 0.6)
            for i, x in enumerate(hs)]


def test_classification_boundaries():
    from ecological_models.nowak_mechanisms.kin_selection.ladder.run_nonoffspring import classify
    base = dict(N0=_arm([0.3] * 20), XC28=_arm([0.02] * 20), NO5=_arm([0.02] * 20))
    v, h2, h3, d = classify(dict(base, NO28=_arm([0.7] * 15 + [0.31] * 1 + [0.2] * 4)), 0.05)
    assert v == "met: among non-offspring relatives" and d["NO28_above_N0_pairs"] == 16 and h2 == h3 == "supported"
    v, *_ = classify(dict(base, NO28=_arm([0.7] * 14 + [0.4] * 6)), 0.05)
    assert v == "not met"                                            # 14 at the endpoint
    v, *_ = classify(dict(base, NO28=_arm([0.7] * 15 + [0.2] * 5)), 0.05)
    assert v == "not met"                                            # 15 at the endpoint but only 15 pairs above
    v, *_ = classify(dict(base, NO28=_arm([0.7] * 20)), 0.0199)
    assert v.startswith("not interpretable: no relatedness contrast")
    v, *_ = classify(dict(base, NO28=_arm([0.7] * 20), XC28=_arm([0.7] * 3 + [0.0] * 17)), 0.05)
    assert v == "not met: the control did not separate"
    v, h2, h3, _ = classify(dict(base, NO28=_arm([0.7] * 20), XC28=_arm([0.02] * 20, viable=17)), 0.05)
    assert v == "not interpretable" and h3 == "not interpretable"
    v, h2, _, _ = classify(dict(base, NO28=_arm([0.7] * 20), NO5=_arm([0.5] * 20)), 0.05)
    assert v.startswith("met") and h2 == "not supported"


def test_validation_rejects_missing_route_statistics(tmp_path, monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection.ladder import run_nonoffspring as R
    o = E.run(seed=30, b=0.14, c=0.005, mode=E.CLASSPOOL, T=2000, sample_dt=1000.0, P=1000, nb_pairs=100,
              route=True)
    job = dict(stage="M", name="XC28_s0", arm="XC28", seed=30, mode=4, b=0.14, c=0.005, T=2000.0, dt=1000.0)
    meta = dict(job, code_sha="x", commit="y")
    good = tmp_path / "good.npz"
    np.savez_compressed(good, samples=o["samples"], hists=o["hists"], meta=__import__("json").dumps(meta))
    R.validate(good, job, "x", "y")
    s = o["samples"].copy(); s[1:, 15:18] = np.nan
    bad = tmp_path / "bad.npz"
    np.savez_compressed(bad, samples=s, hists=o["hists"], meta=__import__("json").dumps(meta))
    with pytest.raises(ValueError):
        R.validate(bad, job, "x", "y")
    s = o["samples"].copy(); s[:, 22] = np.nan
    np.savez_compressed(bad, samples=s, hists=o["hists"], meta=__import__("json").dumps(meta))
    with pytest.raises(ValueError):
        R.validate(bad, job, "x", "y")


def test_interim_verdict_rules():
    from ecological_models.nowak_mechanisms.kin_selection.ladder.run_nonoffspring import interim_verdict, T_M
    rows = [dict(name=f"r{i}", arm="NO28", t=10_000.0, el=30.0, cpu=30.0, age=10.0) for i in range(20)]
    v, reasons, cpu = interim_verdict(rows, {}, ["XC28"] * 60, [], 0.0, 0.0)
    assert v == "ok" and abs(cpu - 80 * 300 / 3600) < 1e-9          # 300 s per run, 80 runs: 6.7 CPU-h
    v, reasons, _ = interim_verdict(rows, {}, ["XC28"] * 60, ["x.failed"], 0.0, 0.0)
    assert v == "STOP"
    rows2 = rows[:-1] + [dict(name="slow", arm="NO28", t=10_000.0, el=30.0, cpu=30.0, age=1000.0)]
    assert interim_verdict(rows2, {}, [], [], 0.0, 0.0)[0] == "STOP"
    big = [dict(name=f"r{i}", arm="NO28", t=1_000.0, el=60.0, cpu=60.0, age=10.0) for i in range(20)]
    assert interim_verdict(big, {}, ["XC28"] * 60, [], 0.0, 0.0)[0] == "STOP"   # 6000 s per run -> 133 CPU-h
    assert T_M == 100_000.0
    assert interim_verdict([], {"a": 32_400.0}, [], [], 0.0, 0.0)[0] == "STOP"    # finished work alone over budget
    slow_wall = [dict(name=f"r{i}", arm="NO28", t=10_000.0, el=300.0, cpu=30.0, age=10.0) for i in range(20)]
    assert interim_verdict(slow_wall, {}, ["XC28"] * 60, [], 0.0, 0.0)[0] == "ok"   # wall time is not CPU time


def test_smoke_cannot_use_registered_folders(monkeypatch):
    from ecological_models.nowak_mechanisms.kin_selection.ladder import run_nonoffspring as R
    monkeypatch.setattr(R, "SCALE", 0.01)
    monkeypatch.setattr(R, "RAW", R.RAW_REG)
    monkeypatch.setattr(R, "DATA", R.DATA_REG / "smoke")
    with pytest.raises(SystemExit):
        R.require_registered("x")
