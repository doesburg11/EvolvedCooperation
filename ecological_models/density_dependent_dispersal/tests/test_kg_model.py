"""Tests for the numba port of Kanwal and Gardner (2022)."""

import numpy as np

from ecological_models.density_dependent_dispersal import kg_model as K


def _buffers(N, n, k):
    nk = n * k
    return dict(J=np.empty((N * nk, 3)), R=np.empty((N * nk, 3)), Dsp=np.empty((N * nk, 3)),
                dest=np.empty(N * nk, np.int64), imm_cnt=np.empty(N, np.int64), imm_off=np.empty(N, np.int64),
                imm_idx=np.empty(N * nk, np.int64), B_new=np.empty((N, n, 3)), rec=np.zeros(5))


def _step(B, n, k, m, c, dd=True, shuffle=False, b_init=0.3, seed=0):
    K._seed(seed)
    b = _buffers(B.shape[0], n, k)
    K.step(B, n, k, m, c, dd, shuffle, b_init, b["J"], b["R"], b["Dsp"], b["dest"], b["imm_cnt"], b["imm_off"],
           b["imm_idx"], b["B_new"], b["rec"])
    return b["B_new"], b["rec"]


def test_survival_rate_matches_rule():
    # no mutation, z = 0.4 everywhere: S = 0.5 + 0.5 * 0.6 * 0.4 = 0.62, E[SE] = 0.75 -> survivors 0.465 of n*k
    N, n, k = 4000, 2, 100
    B = np.zeros((N, n, 3)); B[:, :, 0] = B[:, :, 1] = 0.2; B[:, :, 2] = 0.4
    _, rec = _step(B, n, k, 0.0, 0.5)
    frac = rec[3] / (N * n * k)
    assert abs(frac - 0.62 * 0.75) < 0.01


def test_breeders_come_from_pool_and_count_is_fixed():
    N, n, k = 200, 3, 100
    B = np.zeros((N, n, 3)); B[:, :, 0] = B[:, :, 1] = 0.25; B[:, :, 2] = 0.3
    Bn, rec = _step(B, n, k, 0.0, 0.4)
    assert Bn.shape == (N, n, 3)
    assert np.allclose(Bn[:, :, 2], 0.3) and np.allclose(Bn[:, :, 0], 0.25)   # m = 0: no new values
    assert rec[2] == 0


def test_dispersal_rule_density_dependent_vs_fixed():
    # b1 = 0.5 (at P = k/2), b2 = 0.9 (at P = k); survivors per breeder stay in about 30..62, so D stays in
    # [0, 1] and the mean attempt rate is linear in the mean P. Under fixed dispersal it is b1 whatever the density.
    N, n, k = 2000, 2, 100
    B = np.zeros((N, n, 3)); B[:, :, 0] = 0.5; B[:, :, 1] = 0.9; B[:, :, 2] = 0.5
    _, rec_dd = _step(B, n, k, 0.0, 0.0, dd=True, seed=1)
    _, rec_f = _step(B, n, k, 0.0, 0.0, dd=False, seed=1)
    d_dd = rec_dd[0] / rec_dd[1]
    d_f = rec_f[0] / rec_f[1]
    assert abs(d_f - 0.5) < 0.01
    P = rec_dd[3] / (N * n)                       # mean survivors per breeder, about 46.9
    expected = (P - 50) * 0.4 / 50 + 0.5
    assert abs(d_dd - expected) < 0.01 and d_dd < 0.5 - 0.01


def test_dispersal_cost_kills_dispersers():
    N, n, k = 300, 2, 100
    B = np.zeros((N, n, 3)); B[:, :, 0] = B[:, :, 1] = 1.0; B[:, :, 2] = 0.5
    _, rec = _step(B, n, k, 0.0, 0.25, dd=False)
    assert abs(rec[4] / rec[3] - 0.75) < 0.01          # everyone attempts, 75% arrive


def test_all_dispersers_die_gives_refill():
    N, n, k = 50, 2, 100
    B = np.zeros((N, n, 3)); B[:, :, 0] = B[:, :, 1] = 1.0; B[:, :, 2] = 0.0
    Bn, rec = _step(B, n, k, 0.0, 1.0, dd=False, b_init=0.33)
    assert rec[2] == N
    assert np.allclose(Bn[:, :, 0], 0.33) and np.allclose(Bn[:, :, 1], 0.33)
    assert 0.3 < Bn[:, :, 2].mean() < 0.7                # new random z


def test_shuffle_removes_patch_structure():
    # patch i's breeders carry z = i / N; with no dispersal, unshuffled offspring stay; shuffled ones are mixed
    N, n, k = 300, 2, 100
    B = np.zeros((N, n, 3)); B[:, :, 2] = (np.arange(N) / N)[:, None]
    B[:, :, 0] = B[:, :, 1] = 0.0
    Bn, _ = _step(B, n, k, 0.0, 0.0, dd=False, shuffle=False)
    Bs, _ = _step(B, n, k, 0.0, 0.0, dd=False, shuffle=True)
    idx = np.repeat(np.arange(N), n)
    assert np.corrcoef(idx, Bn[:, :, 2].ravel())[0, 1] > 0.99
    assert abs(np.corrcoef(idx, Bs[:, :, 2].ravel())[0, 1]) < 0.15


def test_mutation_rates():
    N, n, k = 200, 5, 100
    B = np.zeros((N, n, 3)); B[:, :, 0] = B[:, :, 1] = 0.5; B[:, :, 2] = 0.0
    K._seed(3)
    b = _buffers(N, n, k)
    # c = 1 with b = 0 means no one disperses; survivors stay; read juveniles back from J before compaction is
    # not possible, so check breeders: fraction with z != 0 should be about m (selection is weak for 1 step)
    K.step(B, n, k, 0.05, 0.0, False, False, 0.5, b["J"], b["R"], b["Dsp"], b["dest"], b["imm_cnt"],
           b["imm_off"], b["imm_idx"], b["B_new"], b["rec"])
    Bn = b["B_new"]
    assert abs((Bn[:, :, 2] != 0).mean() - 0.05) < 0.015
    moved = (Bn[:, :, 0] != 0.5).mean()
    assert abs(moved - 0.05) < 0.015
    assert set(np.round(np.unique(Bn[:, :, 0]), 2)) <= {0.45, 0.5, 0.55}


def test_run_records_and_rare_start():
    o = K.run(2, 0.8, G=5, seed=1, init_z="zero", total_breeders=2000)
    assert o["z"][0] == 0.0 and o["z"][5] > 0.0
    assert len(o["z"]) == 6 and np.isnan(o["d_mean"][0]) and not np.isnan(o["d_mean"][5])
