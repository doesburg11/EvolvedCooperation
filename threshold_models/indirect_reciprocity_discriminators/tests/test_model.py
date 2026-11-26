"""Stage 0 deterministic tests registered in threshold_models/indirect_reciprocity_discriminators/README.md."""

import numpy as np
import pytest

from threshold_models.indirect_reciprocity_discriminators.model import (
    alld_share,
    expected_payoffs,
    generation,
    helped_matrix_counts,
    one_generation_changes,
    q_star,
    trajectory_finals,
)

DISC, ALLD = 0, 1


def test_closed_form_payoffs_match_encounter_play():
    """Encounter-by-encounter play on a small population, with q drawn per encounter, against the closed form."""
    rng = np.random.default_rng(7)
    N, b, c, q = 8, 3.0, 1.0, 0.4
    strat = np.array([DISC] * 5 + [ALLD] * 3)
    totals = np.zeros(N)
    reps = 40_000
    for _ in range(reps):
        pay = np.zeros(N)
        for d in range(N):
            for r in range(N):
                if d == r or strat[d] == ALLD:
                    continue
                if strat[r] == DISC or rng.random() >= q:
                    pay[d] -= c
                    pay[r] += b
        totals += pay
    pa, pd = expected_payoffs(3, N, b, c, q)
    assert totals[strat == ALLD].mean() / reps / (N - 1) == pytest.approx(pa, rel=0.01)
    assert totals[strat == DISC].mean() / reps / (N - 1) == pytest.approx(pd, rel=0.01)


def test_help_rate_to_alld():
    np.random.seed(1)
    given, received = helped_matrix_counts(200, 300, 0.35)
    assert given.sum() == received.sum()
    assert given.sum() / (200 * 300) == pytest.approx(0.65, abs=0.005)


def test_payoffs_equal_at_q_star():
    for b, c in ((3.0, 1.0), (2.0, 1.0)):
        q = q_star(10, 1000, b, c)
        pa, pd = expected_payoffs(10, 1000, b, c, q)
        assert pa == pytest.approx(pd, rel=1e-12)


def test_share_matches_expected_fitness_on_average():
    N, n, b, c, q, s = 200, 20, 3.0, 1.0, 0.5, 0.1
    np.random.seed(2)
    shares = [alld_share(n, N, b, c, q, s) for _ in range(300)]
    pa, pd = expected_payoffs(n, N, b, c, q)
    expected = n * (1 + s * pa) / (n * (1 + s * pa) + (N - n) * (1 + s * pd))
    assert np.mean(shares) == pytest.approx(expected, rel=1e-3)


def test_absorbing_states_and_reproducibility():
    assert generation(0, 100, 3.0, 1.0, 0.4, 0.1) == 0
    assert generation(100, 100, 3.0, 1.0, 0.4, 0.1) == 100
    a = one_generation_changes(10, 300, 3.0, 1.0, 0.4, 0.1, 5, 50)
    assert np.array_equal(a, one_generation_changes(10, 300, 3.0, 1.0, 0.4, 0.1, 5, 50))
    t = trajectory_finals(10, 300, 3.0, 1.0, 0.4, 0.1, 5, 5, 10)
    assert np.array_equal(t, trajectory_finals(10, 300, 3.0, 1.0, 0.4, 0.1, 5, 5, 10))
