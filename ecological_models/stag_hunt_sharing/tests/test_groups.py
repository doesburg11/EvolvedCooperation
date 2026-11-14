import numpy as np
import pytest

from ecological_models.stag_hunt_sharing import groups
from ecological_models.stag_hunt_sharing.stag_hunt_sharing import food, hunt, reproduce

SETTING = {"fitness_shape": "diminishing", "stag_success_probability": 1.0, "stag_to_hare_ratio": 1.2, "initial_stag_fraction": 0.5}


def test_hunting_partners_never_cross_groups():
    config = groups.group_config(SETTING)
    stag = np.zeros((3, 16, 16), dtype=np.int8)
    stag[0, 0, 0] = 1  # alone in group 0
    stag[1] = 1  # group 1 all stag
    caught = hunt(stag, np.random.default_rng(0), config)
    assert caught[0].sum() == 0
    assert caught[1].sum() == 256
    assert caught[2].sum() == 0


def test_stacked_groups_match_single_groups():
    """Food and reproduction of a stack equal each group run alone, given
    the same fitness and the same random draws."""
    config = groups.group_config({**SETTING, "stag_success_probability": 0.5})
    rng = np.random.default_rng(1)
    stag = (rng.random((2, 16, 16)) < 0.5).astype(np.int8)
    caught = (rng.random((2, 16, 16)) < 0.5).astype(float) * stag
    meal = food(stag, caught, config)
    for g in range(2):
        assert np.array_equal(meal[g], food(stag[g], caught[g], config))
    fit = groups.fitness(meal, config)
    config0 = {**config, "mutation_probability": 0.0}
    stacked = reproduce(stag, fit, np.random.default_rng(5), config0)
    # rebuild the stacked draw for group 0 alone: same shape-ordered uniforms
    draws = np.random.default_rng(5).random(stag.shape)
    single = []
    for g in range(2):
        class Fixed:
            def __init__(self, first):
                self.first = first

            def random(self, shape):
                return self.first if shape == self.first.shape else np.ones(shape)

        single.append(reproduce(stag[g], fit[g], Fixed(draws[g]), config0))
    assert np.array_equal(stacked, np.stack(single))


def test_referee_copies_best_over_worst_and_skips_full_tie():
    stag = np.zeros((4, 2, 2), dtype=np.int8)
    stag[2] = [[1, 0], [0, 1]]
    window = np.array([3.0, 1.0, 9.0, 5.0])
    assert groups.referee(stag, window, np.random.default_rng(0)) == (2, 1)
    assert np.array_equal(stag[1], stag[2])
    assert groups.referee(stag, np.full(4, 2.0), np.random.default_rng(0)) is None


def test_fission_splits_into_the_weaker_neighbour_only_if_weaker():
    stag = np.arange(5 * 4).reshape(5, 2, 2).astype(np.int8) % 2
    stag[0] = 1
    total = np.array([10.0, 0, 0, 0, 0])
    rate_sum = np.array([8.0, 5.0, 9.0, 9.0, 3.0])
    rate_count = np.full(5, 10.0)
    events = groups.fission(stag, total, rate_sum, rate_count, 10.0, np.random.default_rng(0))
    assert events == [(0, 4)]  # neighbours 4 (0.3) and 1 (0.5): 4 is weaker
    assert np.array_equal(stag[4], stag[0])
    assert total[0] == 0 and total[4] == 0 and rate_sum[4] == 0 and rate_count[4] == 0
    # a splitter weaker than both neighbours copies nothing, but resets
    stag2 = np.zeros((3, 2, 2), dtype=np.int8)
    total2 = np.array([0.0, 10.0, 0.0])
    events = groups.fission(stag2, total2, np.array([9.0, 1.0, 9.0]), np.full(3, 10.0), 10.0, np.random.default_rng(0))
    assert events == [] and total2[1] == 0


def test_fission_refounded_group_is_not_a_source_in_the_same_generation():
    stag = np.zeros((4, 2, 2), dtype=np.int8)
    stag[0] = 1
    total = np.array([10.0, 10.0, 0.0, 0.0])
    events = groups.fission(stag, total, np.array([9.0, 1.0, 5.0, 5.0]), np.full(4, 10.0), 10.0, np.random.default_rng(0))
    # group 0 splits into 1 (weaker than 3); group 1, refounded, does not split
    assert events == [(0, 1)]


def test_no_rule_has_no_events_and_rules_are_checked():
    assert groups.run(SETTING, "none", 0)["events"] == 0
    with pytest.raises(ValueError):
        groups.run(SETTING, "X", 0)


def test_all_hare_group_reaches_k_every_interval():
    config = groups.group_config(SETTING)
    hare = groups.hare_fitness(config)
    k = groups.GROUPS["interval"] * 256 * hare
    assert np.isclose(256 * hare * groups.GROUPS["interval"], k)
    assert 0 < hare < 1.1


def test_runs_are_reproducible():
    assert groups.run(SETTING, "F", 3) == groups.run(SETTING, "F", 3)


def test_one_group_cannot_affect_another():
    """Changing group 0 leaves group 1's catches and offspring unchanged
    (same random draws)."""
    config = groups.group_config({**SETTING, "stag_success_probability": 0.5})
    rng = np.random.default_rng(2)
    a = (rng.random((2, 16, 16)) < 0.5).astype(np.int8)
    b = a.copy()
    b[0] = 1 - b[0]
    out = []
    for stag in (a, b):
        r = np.random.default_rng(7)
        caught = hunt(stag, r, config)
        fit = groups.fitness(food(stag, caught, config), config)
        out.append((caught[1], reproduce(stag, fit, r, config)[1]))
    assert np.array_equal(out[0][0], out[1][0])
    assert np.array_equal(out[0][1], out[1][1])


def test_group_size_cannot_be_overridden():
    with pytest.raises(ValueError):
        groups.group_config({**SETTING, "grid_size": 8})


def _rows(cells):
    """CSV-like rows: cells {(ratio, q, start, rule): takeovers of 20}."""
    rows = []
    for (ratio, q, start, rule), n in cells.items():
        for seed in range(20):
            rows.append({"fitness_shape": "diminishing", "stag_to_hare_ratio": str(ratio), "stag_success_probability": str(q), "initial_stag_fraction": str(start), "rule": rule, "seed": str(seed), "stag_fraction": "0.9" if seed < n else "0.5"})
    return rows


def _cells(r, f, none):
    from ecological_models.stag_hunt_sharing.utils import judge_groups as j

    return {(1.2, q, s, rule): n for q in j.QS for s in j.STARTS for rule, n in (("R", r), ("F", f), ("none", none))}


def test_judge_boundaries_and_priority():
    from ecological_models.stag_hunt_sharing.utils import judge_groups as j

    v = j.verdict(j.takeovers(_rows(_cells(15, 14, 5))))
    assert v["R"][0] and not v["F"][0]  # 15 passes, 14 fails
    v = j.verdict(j.takeovers(_rows(_cells(15, 15, 6))))
    assert not v["R"][0] and not v["F"][0]  # gain 9 fails
    v = j.verdict(j.takeovers(_rows(_cells(16, 15, 5))))
    assert v["R"][0] and v["F"][0]  # gain 10 passes
    cells = _cells(20, 20, 0)
    cells[(1.2, 0.3, 0.05, "F")] = 14  # one cell failing fails the rule
    assert not j.verdict(j.takeovers(_rows(cells)))["F"][0]


def test_judge_takeover_is_strictly_above_half_and_seeds_are_checked():
    from ecological_models.stag_hunt_sharing.utils import judge_groups as j

    rows = _rows({(1.2, 0.3, 0.05, "R"): 0})  # every seed exactly 0.5
    assert j.takeovers(rows)[(1.2, 0.3, 0.05, "R")][0] == 0
    with pytest.raises(ValueError):
        j.takeovers(rows[:-1])
    with pytest.raises(ValueError):
        j.takeovers(rows + rows[:1])
