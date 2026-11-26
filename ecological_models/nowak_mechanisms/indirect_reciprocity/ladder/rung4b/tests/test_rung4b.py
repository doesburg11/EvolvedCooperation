"""Tests for the rung-4b model (README.md, "Rung 4b")."""

import numpy as np
from numba import njit

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a import model as m4a
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4b import model

P = dict(q=0.8, o=0.5, e=0.1, a=0.02)
STARTS = ((0.1, 0.8, 0.1), (0.0, 0.9, 0.1), (0.3, 0.6, 0.1), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))


def _counts_4a(tr):
    return np.column_stack([np.round(tr[:, 0] * 1000), np.round(tr[:, 1] * 1000)]).astype(np.int64)


def _mono(row, n=1000):
    na, nc = row
    return na == n or nc == n or na + nc == 0


def _4b(start, arm, seed, gens, mu=0.0):
    return model.run(P["q"], P["o"], P["e"], P["a"], mu, start, arm, seed, gens=gens)


def test_mu0_equals_rung4a_counts_throughout():
    for start in STARTS:
        for arm in (model.TEST, model.SHUFFLED):
            for seed in (0, 5):
                tr, _, _ = m4a.run(P["q"], P["o"], P["e"], P["a"], start, arm, seed, gens=150)
                cb, au, _, _ = _4b(start, arm, seed, 150)
                assert np.array_equal(_counts_4a(tr), cb), (start, arm, seed)
                assert au[:, 3:6].sum() == 0


def test_mu0_counters_equal_rung4a_up_to_fixation():
    # cut the horizon at the generation in which a single strategy first remains: rung 4a has skipped nothing yet
    checked = 0
    for start in ((0.1, 0.8, 0.1), (0.3, 0.6, 0.1)):
        for arm in (model.TEST, model.SHUFFLED):
            for seed in range(6):
                cb, _, _, _ = _4b(start, arm, seed, 300)
                fix = [g for g in range(len(cb)) if _mono(cb[g])]
                horizon = fix[0] if fix else 300
                if horizon == 0:
                    continue
                tr, s4, g4 = m4a.run(P["q"], P["o"], P["e"], P["a"], start, arm, seed, gens=horizon)
                _, _, sb, gb = _4b(start, arm, seed, horizon)
                assert np.array_equal(s4, sb) and np.array_equal(g4, gb), (start, arm, seed, horizon)
                checked += bool(fix)
    assert checked >= 1                                   # at least one case with fixation was compared


@njit
def _draw():
    return np.random.random()


def test_mu0_makes_no_random_draw():
    model._seed(3)
    model.mutate_detail(10, 20, 30, 0.0)
    x = _draw()
    model._seed(3)
    assert _draw() == x


def test_every_generation_plays_all_encounters():
    for start in STARTS:
        _, au, sb, gb = _4b(start, model.TEST, 3, 60, mu=0.001)
        assert (au[:, 9] == 10000).all() and gb[16] == 10000 and gb[16] + sb[16] == 10000 * 60


def test_mutation_sampling_law_per_source():
    model._seed(11)
    reps = 40000
    arr = np.array([model.mutate_detail(200, 500, 300, 0.02) for _ in range(reps)], dtype=float)
    m_c, m_d, m_a, c_d, d_c, a_c = arr[:, 3], arr[:, 4], arr[:, 5], arr[:, 6], arr[:, 7], arr[:, 8]
    for m, n in ((m_c, 200), (m_d, 500), (m_a, 300)):            # Binomial(n, mu): mean and variance
        assert abs(m.mean() - n * 0.02) < 0.05 * n * 0.02 + 0.05
        assert abs(m.var() - n * 0.02 * 0.98) < 0.08 * n * 0.02 * 0.98 + 0.05
    for split, m in ((c_d, m_c), (d_c, m_d), (a_c, m_a)):        # Binomial(mutants, 0.5)
        assert abs(split.sum() / m.sum() - 0.5) < 0.01
        assert (split <= m).all()
    post = arr[:, :3]
    assert (post.sum(1) == 1000).all()
    assert np.allclose(post[:, 0], 200 - m_c + d_c + a_c)          # ALLC receives DISC's and ALLD's first share
    assert np.allclose(post[:, 1], 500 - m_d + c_d + (m_a - a_c))  # DISC receives ALLC's first share, ALLD's rest
    assert np.allclose(post[:, 2], 300 - m_a + (m_c - c_d) + (m_d - d_c))


def test_reintroduction_and_audit_balance():
    cb, au, _, _ = _4b((0.0, 1.0, 0.0), model.TEST, 2, 30, mu=0.01)
    assert cb[1:, 0].max() > 0 and cb[1:, 1].max() > 0 and au[:, 3:6].sum() > 0
    pre_c, pre_d, pre_a, m_c, m_d, m_a, c_d, d_c, a_c, _ = au.T
    assert (pre_c + pre_d + pre_a == 1000).all()
    assert np.array_equal(pre_a - m_a + (m_c - c_d) + (m_d - d_c), cb[1:, 0])
    assert np.array_equal(pre_c - m_c + d_c + a_c, cb[1:, 1])


def test_sanity_rule_holds_with_mutation_in_test_arm():
    _, _, sb, gb = _4b((0.1, 0.8, 0.1), model.TEST, 6, 100, mu=0.005)
    assert sb[0] == 0 and gb[0] == 0
