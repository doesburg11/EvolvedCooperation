"""Stage 0 deterministic tests registered in threshold_models/network_reciprocity_lattice/README.md."""

import numpy as np
import pytest

from threshold_models.network_reciprocity_lattice.model import (
    choose_parent,
    db_step,
    init_state,
    lattice,
    run_one,
    threshold,
)


@pytest.mark.parametrize("hood,k", [("von_neumann", 4), ("moore", 8)])
def test_lattice_regular_symmetric_no_self(hood, k):
    nbr = lattice(10, hood)
    assert nbr.shape == (100, k)
    for i in range(100):
        assert len(set(nbr[i])) == k and i not in nbr[i]
        for j in nbr[i]:
            assert i in nbr[j]


def test_thresholds():
    assert threshold(100, 4) == pytest.approx(98 / 23)
    assert threshold(100, 8) == pytest.approx(98 / 10.5)


@pytest.mark.parametrize("hood", ["von_neumann", "moore"])
def test_incremental_payoffs_match_recomputation(hood):
    nbr = lattice(10, hood)
    k = nbr.shape[1]
    np.random.seed(11)
    s, nc = init_state(nbr, k, 37)
    for _ in range(5000):
        db_step(s, nc, nbr, 6.0, 1.0, 0.05, k)
        expected = np.array([s[nbr[i]].sum() for i in range(100)])
        assert np.array_equal(nc, expected)


def test_neutral_parent_choice_is_uniform():
    nbr = lattice(10, "moore")
    k = nbr.shape[1]
    s, nc = init_state(nbr, k, 0)
    rng = np.random.default_rng(3)
    counts = np.zeros(k)
    for u in rng.random(80_000):
        counts[choose_parent(5, s, nc, nbr, 9.0, 1.0, 0.0, k, u)] += 1
    assert np.all(np.abs(counts / counts.sum() - 1 / k) < 0.006)


def test_selection_favours_fitter_neighbour():
    nbr = lattice(10, "von_neumann")
    k = nbr.shape[1]
    s, nc = init_state(nbr, k, 0)
    # site 1 is a defector next to the cooperator at 0; site 0 is a neighbour of 1
    from threshold_models.network_reciprocity_lattice.model import payoff

    j_coop = list(nbr[1]).index(0)
    nc[0] = 3  # give the cooperator three cooperating neighbours (bookkeeping only) so it is the fittest
    w = 0.1
    f = [1 - w + w * payoff(nbr[1, j], s, nc, 8.0, 1.0, k) for j in range(k)]
    assert min(f) > 0 and f[j_coop] == max(f)
    expected = f[j_coop] / sum(f)
    rng = np.random.default_rng(4)
    hits = sum(choose_parent(1, s, nc, nbr, 8.0, 1.0, w, k, u) == j_coop for u in rng.random(40_000))
    assert hits / 40_000 == pytest.approx(expected, abs=0.01)


def test_runs_end_at_absorption_and_are_reproducible():
    nbr = lattice(10, "von_neumann")
    results = [run_one(nbr, 6.0, 1.0, 0.01, seed) for seed in range(200)]
    assert results == [run_one(nbr, 6.0, 1.0, 0.01, seed) for seed in range(200)]
    assert all(r in (True, False) for r in results)
