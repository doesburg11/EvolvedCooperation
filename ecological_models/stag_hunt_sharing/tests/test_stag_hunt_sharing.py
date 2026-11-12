"""Tests of stag_hunt_sharing.py: partners, sharing as a pure transfer,
who receives, fitness shapes, reproduction and settings."""

import numpy as np
import pytest

from ecological_models.stag_hunt_sharing import stag_hunt_sharing as m
from ecological_models.stag_hunt_sharing.config.stag_hunt_sharing_config import MODEL


def config(**changes):
    return {**MODEL, "grid_size": 9, **changes}


def grid(cells, n=9):
    g = np.zeros((n, n), dtype=np.int8)
    for y, x in cells:
        g[y, x] = 1
    return g


def test_a_stag_hunter_needs_a_partner_among_its_four_neighbours():
    rng = np.random.default_rng(0)
    c = config(stag_success_probability=1.0)
    caught = m.hunt(grid([(4, 4), (4, 5), (0, 0), (1, 1)]), rng, c)  # (0,0)-(1,1) only diagonal
    assert caught[4, 4] == caught[4, 5] == 1
    assert caught[0, 0] == caught[1, 1] == 0
    assert m.hunt(grid([(0, 0), (8, 0)]), rng, c)[0, 0] == 1  # neighbours across the torus edge


@pytest.mark.parametrize("target", ["all", "stag"])
@pytest.mark.parametrize("radius", [1, 2, 4, "global"])
@pytest.mark.parametrize("share", [0.0, 0.3, 1.0])
def test_sharing_moves_food_but_never_creates_or_destroys_it(radius, share, target):
    rng = np.random.default_rng(1)
    stag = (rng.random((9, 9)) < 0.5).astype(np.int8)
    caught = (stag.astype(bool) & (rng.random((9, 9)) < 0.7)).astype(float)
    c = config(share_fraction=share, sharing_radius=radius, share_target=target)
    unshared = m.food(stag, caught, config(share_fraction=0.0, sharing_radius=radius))
    assert m.food(stag, caught, c).sum() == pytest.approx(unshared.sum())


def test_a_caught_stag_is_split_between_catcher_and_the_8_neighbours():
    c = config(share_fraction=0.5, sharing_radius=1, hare_payoff=1.0, stag_success_probability=0.8, stag_to_hare_ratio=1.0)
    value = m.stag_payoff(c)
    assert value == pytest.approx(1.25)
    stag = grid([(4, 4)])
    caught = stag.astype(float)
    meal = m.food(stag, caught, c)
    assert meal[4, 4] == pytest.approx(value * 0.5)
    assert meal[3, 3] == pytest.approx(1.0 + value * 0.5 / 8)  # a hare neighbour gets hare plus a share
    assert meal[2, 2] == pytest.approx(1.0)  # beyond the radius
    assert m.food(stag, np.zeros((9, 9)), c)[4, 4] == 0  # a failed stag hunter gets nothing


def test_radius_two_reaches_24_neighbours_and_global_everyone_else():
    stag = grid([(4, 4)])
    caught = stag.astype(float)
    c2 = config(share_fraction=1.0, sharing_radius=2, stag_to_hare_ratio=0.8, stag_success_probability=0.8)
    meal = m.food(stag, caught, c2)
    assert meal[2, 2] == pytest.approx(1.0 + 1.0 / 24) and meal[1, 1] == pytest.approx(1.0)
    cg = config(share_fraction=1.0, sharing_radius="global", stag_to_hare_ratio=0.8, stag_success_probability=0.8)
    assert m.food(stag, caught, cg)[0, 0] == pytest.approx(1.0 + 1.0 / 80)


def test_fitness_shapes():
    meal = np.array([0.0, 1.0, 3.0])
    assert m.fitness(meal, config(fitness_shape="linear", fitness_baseline=0.1)) == pytest.approx([0.1, 1.1, 3.1])
    diminishing = m.fitness(meal, config(fitness_shape="diminishing", fitness_baseline=0.1, food_scale=1.0))
    assert diminishing == pytest.approx(0.1 + 1 - np.exp(-meal))
    # diminishing returns: the second unit of food is worth less than the first
    assert diminishing[1] - diminishing[0] > (diminishing[2] - diminishing[1]) / 2


def test_local_reproduction_draws_only_from_the_cell_and_its_eight_neighbours():
    rng = np.random.default_rng(2)
    stag = grid([(4, 4)])
    fit = np.where(stag == 1, 1e9, 1e-9)
    child = m.reproduce(stag, fit, rng, config(mutation_probability=0.0, dispersal="local"))
    assert (child == grid([(y, x) for y in (3, 4, 5) for x in (3, 4, 5)])).all()


def test_global_reproduction_can_draw_from_anywhere():
    rng = np.random.default_rng(3)
    stag = grid([(0, 0)])
    fit = np.where(stag == 1, 1e9, 1e-9)
    assert m.reproduce(stag, fit, rng, config(mutation_probability=0.0, dispersal="global")).all()


def test_mutation_flips():
    rng = np.random.default_rng(4)
    stag = np.zeros((9, 9), dtype=np.int8)
    assert m.reproduce(stag, np.ones((9, 9)), rng, config(mutation_probability=1.0)).all()


@pytest.mark.parametrize("change", [{"share_fraction": 1.5}, {"sharing_radius": 0}, {"sharing_radius": 5}, {"fitness_shape": "x"}, {"dispersal": "x"}, {"dispersal": 0}, {"dispersal": 5}, {"dispersal": True}, {"share_target": "x"}, {"measure_last": 0}, {"unknown": 1}])
def test_settings_are_checked(change):
    with pytest.raises(ValueError):
        m.check(config(**change))


def test_a_short_run_and_the_obvious_limits():
    lots = m.run(config(generations=200, measure_last=50, stag_to_hare_ratio=5.0, initial_stag_fraction=0.5, share_fraction=0.0), 0)
    little = m.run(config(generations=200, measure_last=50, stag_to_hare_ratio=0.3, initial_stag_fraction=0.5, share_fraction=0.0), 0)
    assert lots["stag_fraction"] > 0.9 and little["stag_fraction"] < 0.1


def test_conditions_drop_radii_without_sharing():
    rows = m.conditions()
    assert all(r["sharing_radius"] == 1 for r in rows if r["share_fraction"] == 0)
    assert len({tuple(sorted(r.items(), key=lambda kv: kv[0])) for r in rows}) == len(rows)


@pytest.mark.parametrize("dispersal", ["local", "global"])
def test_parents_are_drawn_in_proportion_to_fitness(dispersal):
    # a 3 x 3 torus: every cell's 3 x 3 block is the whole grid, so local and
    # global draws have the same odds: one stag with fitness 4 against eight
    # hares with fitness 1 -> 4 / 12 = 1/3 of offspring are stag
    rng = np.random.default_rng(5)
    stag = np.zeros((3, 3), dtype=np.int8)
    stag[1, 1] = 1
    fit = np.where(stag == 1, 4.0, 1.0)
    c = {**MODEL, "grid_size": 3, "mutation_probability": 0.0, "dispersal": dispersal}
    share = np.mean([m.reproduce(stag, fit, rng, c).mean() for _ in range(4000)])
    assert share == pytest.approx(1 / 3, abs=0.01)


def test_the_plot_refuses_share_zero_rows_from_several_radii():
    from ecological_models.stag_hunt_sharing.utils.plot_sweep import table

    row = {"initial_stag_fraction": 0.5, "fitness_shape": "linear", "dispersal": "local", "share_fraction": 0.0, "stag_to_hare_ratio": 1.0, "stag_fraction": 0.0}
    table([dict(row, sharing_radius=1)])
    with pytest.raises(ValueError):
        table([dict(row, sharing_radius=1), dict(row, sharing_radius=2)])


def test_stag_target_shares_only_with_other_stag_hunters():
    c = config(share_fraction=0.5, sharing_radius=1, share_target="stag", stag_to_hare_ratio=1.0, stag_success_probability=0.8)
    value = m.stag_payoff(c)
    stag = grid([(4, 4), (4, 5), (3, 3)])  # (4,4) catches; (4,5) and (3,3) are stag neighbours, (3,3) failed
    caught = grid([(4, 4)]).astype(float)
    meal = m.food(stag, caught, c)
    assert meal[4, 4] == pytest.approx(value * 0.5)
    assert meal[4, 5] == pytest.approx(value * 0.25) and meal[3, 3] == pytest.approx(value * 0.25)
    assert meal[5, 5] == pytest.approx(1.0)  # a hare neighbour gets nothing extra
    alone = m.food(grid([(4, 4)]), grid([(4, 4)]).astype(float), c)
    assert alone[4, 4] == pytest.approx(value)  # no stag hunter near: the catcher keeps it all


def test_stag_target_global_splits_among_all_other_stag_hunters():
    c = config(share_fraction=1.0, sharing_radius="global", share_target="stag", stag_to_hare_ratio=0.8, stag_success_probability=0.8)
    stag = grid([(0, 0), (4, 4), (8, 8)])
    meal = m.food(stag, grid([(0, 0)]).astype(float), c)
    assert meal[0, 0] == 0 and meal[4, 4] == pytest.approx(0.5) and meal[8, 8] == pytest.approx(0.5)
    assert meal[2, 2] == pytest.approx(1.0)


def test_local_dispersal_is_radius_one_draw_for_draw():
    stag = (np.random.default_rng(6).random((9, 9)) < 0.4).astype(np.int8)
    fit = np.random.default_rng(7).random((9, 9)) + 0.1
    a = m.reproduce(stag, fit, np.random.default_rng(8), config(dispersal="local"))
    b = m.reproduce(stag, fit, np.random.default_rng(8), config(dispersal=1))
    assert (a == b).all()


def test_dispersal_radius_two_reaches_the_5_by_5_block():
    rng = np.random.default_rng(9)
    stag = grid([(4, 4)])
    fit = np.where(stag == 1, 1e9, 1e-9)
    child = m.reproduce(stag, fit, rng, config(mutation_probability=0.0, dispersal=2))
    assert (child == grid([(y, x) for y in range(2, 7) for x in range(2, 7)])).all()


def test_targeted_conditions_keep_one_share_zero_row_per_world():
    from ecological_models.stag_hunt_sharing.config.stag_hunt_sharing_config import SWEEP_TARGETED

    rows = m.conditions(SWEEP_TARGETED)
    zero = [r for r in rows if r["share_fraction"] == 0]
    assert all(r["share_target"] == "all" and r["sharing_radius"] == 1 for r in zero)
    assert len(zero) == 5 * 2 * 4 and len(rows) == 5 * 2 * 4 * (1 + 3 * 2 * 2)


def test_targeted_plot_refuses_share_zero_rows_from_several_targets():
    from ecological_models.stag_hunt_sharing.utils.plot_sweep import table_targeted

    row = {"fitness_shape": "linear", "dispersal": 1, "share_fraction": 0.0, "stag_to_hare_ratio": 1.0, "stag_fraction": 0.0, "sharing_radius": 1}
    table_targeted([dict(row, share_target="all")])
    with pytest.raises(ValueError):
        table_targeted([dict(row, share_target="all"), dict(row, share_target="stag")])


def test_stag_target_normalises_per_catcher():
    # two catchers with different numbers of stag neighbours: each splits its
    # own share among its own recipients
    c = config(share_fraction=1.0, sharing_radius=1, share_target="stag", stag_to_hare_ratio=0.8, stag_success_probability=0.8)
    stag = grid([(4, 4), (4, 5), (4, 6), (3, 4)])  # value 1
    caught = grid([(4, 4), (4, 6)]).astype(float)
    meal = m.food(stag, caught, c)
    # (4,4) has stag neighbours (4,5), (3,4): 1/2 each. (4,6) has (4,5) only: 1.
    assert meal[4, 4] == 0 and meal[4, 6] == 0
    assert meal[4, 5] == pytest.approx(0.5 + 1.0) and meal[3, 4] == pytest.approx(0.5)
    assert meal.sum() == pytest.approx(2 + (81 - 4) * 1.0)


def test_stag_target_global_with_one_stag_hunter_keeps_its_catch():
    c = config(share_fraction=0.5, sharing_radius="global", share_target="stag", stag_to_hare_ratio=0.8, stag_success_probability=0.8)
    meal = m.food(grid([(0, 0)]), grid([(0, 0)]).astype(float), c)
    assert meal[0, 0] == pytest.approx(1.0) and meal[1, 1] == pytest.approx(1.0)


def test_stag_target_reaches_across_the_torus_edge():
    c = config(share_fraction=1.0, sharing_radius=1, share_target="stag", stag_to_hare_ratio=0.8, stag_success_probability=0.8)
    meal = m.food(grid([(0, 0), (8, 8)]), grid([(0, 0)]).astype(float), c)
    assert meal[8, 8] == pytest.approx(1.0)


def test_sharing_radius_true_is_refused():
    with pytest.raises(ValueError):
        m.check(config(sharing_radius=True))


def _fake_rows(effect_of):
    from ecological_models.stag_hunt_sharing.config.stag_hunt_sharing_config import RUN, SWEEP_TARGETED

    rows = []
    for c in m.conditions(SWEEP_TARGETED):
        for seed in RUN["seeds"]:
            rows.append({**{k: str(v) for k, v in c.items()}, "seed": str(seed), "stag_fraction": str(0.5 + effect_of(c))})
    return rows


def test_judge_classifies_against_the_matched_baseline():
    from ecological_models.stag_hunt_sharing.utils import judge_targeted as j

    def effect(c):
        if c["share_fraction"] == 0:
            return 0.0
        if c["share_target"] == "stag" and c["fitness_shape"] == "diminishing" and c["dispersal"] == 1 and c["stag_to_hare_ratio"] == 1.0:
            return 0.1
        return -0.1 if c["share_target"] == "all" else 0.0

    records = j.effects(_fake_rows(effect))
    assert len(records) == 480
    result = {name[:2]: (n, helps, hurts, met) for name, n, helps, hurts, met in j.predictions(records)}
    assert result["P1"] == (30, 6, 0, True)
    assert result["P2"] == (120, 0, 0, True)
    assert result["P3"] == (240, 0, 240, True)


def test_judge_refuses_missing_or_duplicated_seeds():
    from ecological_models.stag_hunt_sharing.utils import judge_targeted as j

    rows = _fake_rows(lambda c: 0.0)
    with pytest.raises(ValueError):
        j.effects(rows[1:])
    with pytest.raises(ValueError):
        j.effects(rows + rows[:1])


def test_judge_lowq_matches_baselines_within_each_q():
    from ecological_models.stag_hunt_sharing.config.stag_hunt_sharing_config import RUN, SWEEP_TARGETED_LOWQ
    from ecological_models.stag_hunt_sharing.utils import judge_targeted as j

    def value(c):
        base = 0.2 if c["stag_success_probability"] == 0.2 else 0.6
        if c["share_fraction"] > 0 and c["share_target"] == "stag" and c["fitness_shape"] == "diminishing" and c["stag_success_probability"] == 0.5:
            return base + 0.1
        return base

    rows = [
        {**{k: str(v) for k, v in c.items()}, "seed": str(seed), "stag_fraction": str(value(c))}
        for c in m.conditions(SWEEP_TARGETED_LOWQ)
        for seed in RUN["seeds"]
    ]
    records = j.effects(rows, SWEEP_TARGETED_LOWQ)
    assert len(records) == 2 * 4 * 2 * 2 * 3 * 2
    result = {name[:2]: (n, helps, hurts, met) for name, n, helps, hurts, met in j.predictions_lowq(records)}
    assert result["R1"] == (24, 24, 0, True)
    assert result["R2"] == (24, 0, 0, False)
    assert result["R3"] == (96, 0, 0, True)
