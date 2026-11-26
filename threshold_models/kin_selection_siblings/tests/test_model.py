"""Deterministic checks registered in threshold_models/kin_selection_siblings/README.md."""

import numpy as np

from threshold_models.kin_selection_siblings.model import (
    Params,
    founders,
    generation,
    hamilton,
    predicted_change,
    predator_trees,
    run_trajectory,
)


def _all_predators(p):
    return np.ones(p.trees, dtype=bool)


def test_altruist_with_zero_cost_loses_no_one():
    p = Params(sexual=True, n=2, c=0.0, homes=10, puddles_per_home=2)
    groups = np.ones((20, 2), dtype=np.int8)
    origin = np.zeros((20, 2), dtype=np.int8)
    _, _, info = generation(groups, origin, p, _all_predators(p), np.random.default_rng(1))
    assert info["n_survivors"] == 40


def test_coward_noticer_survives_alone():
    p = Params(sexual=False, n=3, c=1.0, homes=50, puddles_per_home=1)
    groups = np.zeros((50, 3), dtype=np.int8)
    origin = np.zeros((50, 3), dtype=np.int8)
    _, _, info = generation(groups, origin, p, _all_predators(p), np.random.default_rng(2))
    assert info["n_survivors"] == 50


def test_no_predators_everyone_survives_and_zero_prediction():
    p = Params(sexual=True, n=3, c=1.0, homes=50, puddles_per_home=2, a=0.0)
    rng = np.random.default_rng(3)
    groups, origin = founders(p, 0.5, rng)
    _, _, info = generation(groups, origin, p, predator_trees(p, rng), rng)
    assert info["n_survivors"] == groups.size
    assert predicted_change(p, 0.5) == 0.0


def test_asexual_puddles_are_clonal():
    p = Params(sexual=False, n=3, c=0.5, homes=100, puddles_per_home=1)
    rng = np.random.default_rng(4)
    groups, origin = founders(p, 0.5, rng)
    for _ in range(5):
        groups, origin, _ = generation(groups, origin, p, predator_trees(p, rng), rng)
        assert np.all(groups == groups[:, :1])


def test_sexual_children_copy_the_recorded_parent():
    p = Params(sexual=True, n=3, c=0.9, homes=100, puddles_per_home=2)
    rng = np.random.default_rng(5)
    groups, origin = founders(p, 0.5, rng)
    new_groups, new_origin, info = generation(groups, origin, p, predator_trees(p, rng), rng)
    pairs = info["pairs"]
    assert np.array_equal(new_groups, np.take_along_axis(pairs, new_origin, axis=1))
    assert set(np.unique(new_origin)) <= {0, 1}


def test_exact_number_of_predator_trees():
    p = Params(sexual=True, n=2, c=0.5, homes=10, puddles_per_home=2, trees=100, a=0.25)
    for seed in range(5):
        assert predator_trees(p, np.random.default_rng(seed)).sum() == 25


def test_prediction_zero_on_the_rule():
    for p in (Params(True, 2, 0.5, 10, 2), Params(True, 3, 1.0, 10, 2), Params(False, 2, 1.0, 10, 1)):
        assert hamilton(p) == 0.0
        assert predicted_change(p, 0.3) == 0.0


def test_homes_never_exceeded_and_population_constant():
    for p in (Params(True, 2, 0.7, 250, 2), Params(False, 2, 1.0, 500, 1), Params(True, 3, 1.0, 250, 2)):
        rng = np.random.default_rng(6)
        groups, origin = founders(p, 0.5, rng)
        predators = predator_trees(p, rng)
        for _ in range(20):
            groups, origin, _ = generation(groups, origin, p, predators, rng)
            assert groups.shape[0] == p.homes * p.puddles_per_home


def test_same_seed_same_run():
    p = Params(True, 2, 0.6, 250, 2)
    assert np.array_equal(run_trajectory(p, 0.5, 30, 7), run_trajectory(p, 0.5, 30, 7))
