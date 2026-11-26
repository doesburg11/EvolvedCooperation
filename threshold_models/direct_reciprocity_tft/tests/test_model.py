"""Stage 0 deterministic tests registered in threshold_models/direct_reciprocity_tft/README.md."""

import numpy as np
import pytest

from threshold_models.direct_reciprocity_tft.model import (
    alld_share,
    expected_payoffs,
    generation,
    one_generation_changes,
    tft_round_sums,
    trajectory_finals,
    w_star,
)

TFT, ALLD = 0, 1


def _play(a, b_strat, rounds, b, c):
    """Round-by-round repeated donation game; returns (payoff of a, payoff of b_strat)."""
    pa = pb = 0.0
    last_a = last_b = 1  # TFT opens with cooperation
    for t in range(rounds):
        move_a = 1 if (a == TFT and (t == 0 or last_b == 1)) else 0
        move_b = 1 if (b_strat == TFT and (t == 0 or last_a == 1)) else 0
        pa += b * move_b - c * move_a
        pb += b * move_a - c * move_b
        last_a, last_b = move_a, move_b
    return pa, pb


def test_closed_form_payoffs_match_round_by_round_play():
    b, c = 3.0, 1.0
    for rounds in (1, 2, 5):
        assert _play(TFT, TFT, rounds, b, c) == ((b - c) * rounds, (b - c) * rounds)
        assert _play(TFT, ALLD, rounds, b, c) == (-c, b)
        assert _play(ALLD, ALLD, rounds, b, c) == (0.0, 0.0)


def test_mean_rounds():
    np.random.seed(1)
    sums = tft_round_sums(300, 0.6)
    assert sums.mean() / 299 == pytest.approx(1 / 0.4, rel=0.02)


def test_payoffs_equal_at_w_star():
    for b, c in ((3.0, 1.0), (2.0, 1.0)):
        w = w_star(10, 1000, b, c)
        pa, pt = expected_payoffs(10, 1000, b, c, w)
        assert pa == pytest.approx(pt, rel=1e-12)
        assert w > c / b


def test_share_matches_expected_fitness_on_average():
    N, n, b, c, w, s = 200, 20, 3.0, 1.0, 0.5, 0.1
    np.random.seed(2)
    shares = [alld_share(n, N, b, c, w, s) for _ in range(300)]
    pa, pt = expected_payoffs(n, N, b, c, w)
    expected = n * (1 + s * pa) / (n * (1 + s * pa) + (N - n) * (1 + s * pt))
    assert np.mean(shares) == pytest.approx(expected, rel=1e-3)


def test_absorbing_states():
    assert generation(0, 100, 3.0, 1.0, 0.4, 0.1) == 0
    assert generation(100, 100, 3.0, 1.0, 0.4, 0.1) == 100


def test_same_seed_same_runs():
    a = one_generation_changes(10, 300, 3.0, 1.0, 0.4, 0.1, 5, 50)
    assert np.array_equal(a, one_generation_changes(10, 300, 3.0, 1.0, 0.4, 0.1, 5, 50))
    t = trajectory_finals(10, 300, 3.0, 1.0, 0.4, 0.1, 5, 5, 10)
    assert np.array_equal(t, trajectory_finals(10, 300, 3.0, 1.0, 0.4, 0.1, 5, 5, 10))
