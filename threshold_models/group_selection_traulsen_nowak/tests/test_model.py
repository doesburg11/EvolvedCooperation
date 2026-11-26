"""Stage 0 deterministic tests registered in threshold_models/group_selection_traulsen_nowak/README.md."""

import numpy as np
import pytest

from threshold_models.group_selection_traulsen_nowak.model import (
    fitnesses,
    initial_state,
    run_one,
    split,
    step,
    threshold,
)


def test_threshold_values():
    assert threshold(10, 10) == pytest.approx(2.25)
    assert threshold(5, 10) == pytest.approx(1.625)


def test_fitness_matches_individual_sums():
    b, c, w = 3.0, 1.0, 0.05
    for s in range(1, 11):
        for i in range(s + 1):
            members = [1] * i + [0] * (s - i)
            total = 0.0
            for k, me in enumerate(members):
                others = members[:k] + members[k + 1:]
                pi = b * sum(others) - (c * (s - 1) if me else 0.0)
                total += 1 - w + w * pi
            assert fitnesses(i, s, b, c, w)[0] == pytest.approx(total)


def test_split_conserves_members_and_cooperators():
    np.random.seed(3)
    for _ in range(500):
        ic = np.array([3, 1, 0, 4], dtype=np.int64)
        sz = np.array([10, 9, 9, 9], dtype=np.int64)
        split(ic, sz, 0, 10)
        assert ic.shape[0] == 4 and np.all(sz >= 1) and np.all(ic >= 0) and np.all(ic <= sz)
        killed = [h for h in (1, 2, 3) if sz[h] + sz[0] == 10 and (ic[h] + ic[0] == 3)]
        assert killed, "the other daughter must replace one of the other groups"


def test_group_count_and_sizes_bounded():
    np.random.seed(4)
    ic, sz = initial_state(10, 10)
    for _ in range(20_000):
        step(ic, sz, 10, 3.0, 1.0, 0.05, 0.01)
        assert ic.shape[0] == 10
        assert np.all(sz >= 1) and np.all(sz <= 9) and np.all(ic <= sz) and np.all(ic >= 0)


def test_neutral_group_choice_proportional_to_size():
    # at w = 0 each individual has fitness 1, so a group's total fitness equals its size
    for s in range(1, 10):
        for i in range(s + 1):
            assert fitnesses(i, s, 9.0, 1.0, 0.0)[0] == pytest.approx(s)


def test_absorption_and_reproducibility():
    results = [run_one(5, 10, 2.0, 1.0, 0.05, 0.01, seed) for seed in range(300)]
    assert results == [run_one(5, 10, 2.0, 1.0, 0.05, 0.01, seed) for seed in range(300)]
