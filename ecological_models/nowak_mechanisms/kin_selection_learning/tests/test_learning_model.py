import math

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.kin_selection.config.kin_selection_config import resolve_config
from ecological_models.nowak_mechanisms.kin_selection.kin_selection_model import (
    STAGE_JUVENILE,
    EcologicalKinSelectionModel,
)
from ecological_models.nowak_mechanisms.kin_selection_learning.config.learning_config import LEARNING, STEP1_SEEDS
from ecological_models.nowak_mechanisms.kin_selection_learning.learning_model import LearnedHelpingModel
from ecological_models.nowak_mechanisms.kin_selection_learning.utils import run_step0, run_step1


def cfg(**kw):
    return resolve_config({"random_seed": 3, "simulation_steps": 40, "write_latest_run": False, **kw})


def learning(alpha=0.01):
    return {**LEARNING, "alpha": alpha}


def test_version_a_is_the_unchanged_model():
    base = EcologicalKinSelectionModel(cfg()).run()
    mine = LearnedHelpingModel(cfg(), "A", LEARNING).run()
    assert base["summary"] == mine["summary"]
    for key in base["history"]:
        assert np.allclose(np.asarray(base["history"][key], float), np.asarray(mine["history"][key], float),
                           equal_nan=True)


def test_learner_needs_alpha_and_valid_version():
    with pytest.raises(ValueError):
        LearnedHelpingModel(cfg(), "B", LEARNING)
    with pytest.raises(ValueError):
        LearnedHelpingModel(cfg(), "D", learning())


@pytest.mark.parametrize("version", ["B", "C"])
def test_care_does_not_change_genes_and_cost_is_the_energy_drop(version):
    m = LearnedHelpingModel(cfg(), version, learning())
    for _ in range(3):
        m.step()
    genes = {i.id: i.helping_trait for i in m.individuals}
    energy = {i.id: i.energy for i in m.individuals}
    m._age_and_budget()
    energy_after_budget = {i.id: i.energy for i in m.individuals}
    m._provide_care()
    assert all(i.helping_trait == genes[i.id] for i in m.individuals)
    assert m._pending, "carers should have pending actions"
    rate = m.config["care_cost_per_unit"]
    for i in m.individuals:
        if i.id in m._pending:
            action, e, cost, eps = m._pending[i.id]
            assert 0.0 <= action <= 1.0
            assert math.isclose(cost, energy_after_budget[i.id] - i.energy, abs_tol=1e-12)
            assert cost <= action * m.config["care_capacity_per_helper"] * rate + 1e-12
    assert energy  # silence unused


def test_learn_update_matches_the_rule():
    m = LearnedHelpingModel(cfg(), "C", learning(alpha=0.3))
    carer = next(i for i in m.individuals if m._is_carer(i))
    carer.helping_trait, carer.household_id = 0.4, 99
    m.effort[carer.id], m.baseline[carer.id] = 0.3, -0.5
    m._pending = {carer.id: (0.45, 0.3, 0.1, 0.15)}
    m._learn({99: 2})
    V = LEARNING["juvenile_energy_value"]
    reward = -0.1 - 0.4 * V * 2
    stake = m.config["care_cost_per_unit"] * m.capacity(carer) + 0.4 * V
    expected = min(1.0, max(0.0, 0.3 + 0.3 * ((reward + 0.5) / stake) * 0.15 / 0.1))
    assert math.isclose(m.effort[carer.id], expected)
    assert math.isclose(m.baseline[carer.id], -0.5 + 0.1 * (reward + 0.5))


def test_first_reward_only_sets_the_baseline_and_b_ignores_kin():
    m = LearnedHelpingModel(cfg(), "B", learning())
    carer = next(i for i in m.individuals if m._is_carer(i))
    carer.helping_trait, carer.household_id = 0.9, 7
    m.effort[carer.id], m.baseline[carer.id] = 0.3, None
    m._pending = {carer.id: (0.5, 0.3, 0.2, 0.2)}
    m._learn({7: 3})
    assert m.effort[carer.id] == 0.3
    assert math.isclose(m.baseline[carer.id], -0.2)  # k = 0 in B


def test_household_deaths_are_counted_from_survival():
    m = LearnedHelpingModel(cfg(base_juvenile_survival_probability=0.0, care_benefit_to_survival=0.0),
                            "C", learning())
    m._age_and_budget()
    care, care_r, _ = m._provide_care()
    seen = {}
    m._learn = lambda deaths: seen.update(deaths)
    juv = [i for i in m.individuals if i.stage == STAGE_JUVENILE and i.household_id is not None]
    m._apply_survival(care, care_r)
    expected = {}
    for j in juv:
        expected[j.household_id] = expected.get(j.household_id, 0) + 1
    assert seen == expected and sum(seen.values()) > 0


def test_selfish_learner_effort_falls_from_the_real_start():
    m = LearnedHelpingModel(cfg(care_cost_per_unit=0.3, simulation_steps=20), "B", learning(alpha=0.3))
    m.run()
    assert m.history["mean_expressed_helping"][0] == pytest.approx(LEARNING["initial_effort"])
    assert m.history["mean_expressed_helping"][-1] < 0.02


def test_toy_calibration_learns_toward_the_optimum_and_away_from_zero_regard():
    from ecological_models.nowak_mechanisms.kin_selection_learning.utils import calibrate_alpha as ca
    c = resolve_config({"care_cost_per_unit": 0.3})
    target = ca.best_effort(0.65, c)
    assert 0.6 < target < 0.8          # saturation at 1.25 a = 0.9 -> a = 0.72
    assert ca.best_effort(0.0, c) == 0.0
    rng = np.random.default_rng(0)
    assert abs(ca.simulate(0.5, 0.65, 0.05, c, rng) - target) < 0.1
    assert ca.simulate(0.5, 0.0, 0.5, c, rng) < 0.1
    assert ca.simulate(0.0, 0.65, 0.05, c, rng) == pytest.approx(0.05)  # alpha 0: no learning


def test_choose_cost_rule():
    assert run_step0.choose_cost({0.03: 0.9, 0.1: 0.55, 0.2: 0.45, 0.3: 0.1}) == 0.2  # tie 0.05: highest cost
    assert run_step0.choose_cost({0.03: 0.9, 0.1: 0.8}) is None
    assert run_step0.choose_cost({0.1: 0.3, 0.2: 0.75}) == 0.1


def test_step1_score():
    n = len(STEP1_SEEDS)

    def rows(v, st, k):
        return [{"version": v, "start": st, "success": int(i < k)} for i in range(n)]
    r = (rows("A", "rare", 20) + rows("B", "rare", 2) + rows("C", "rare", 16)
         + rows("A", "weak", 4) + rows("B", "weak", 0) + rows("C", "weak", 16))
    s = run_step1.score(r)
    assert s["T1"] and s["T2"] and s["T3"] and s["T3_fisher_p"] < 0.05
    r = (rows("A", "rare", 20) + rows("B", "rare", 5) + rows("C", "rare", 12)
         + rows("A", "weak", 4) + rows("B", "weak", 0) + rows("C", "weak", 10))
    s = run_step1.score(r)
    assert not s["T1"] and not s["T2"] and not s["T3"]  # B 0.125 > 0.10; C 0.30 < 0.50-0.15; 0.25-0.10 < 0.20


def test_constant_reward_does_not_move_effort():
    """No signal, no drift: a learner whose reward never changes keeps its effort."""
    m = LearnedHelpingModel(cfg(), "B", learning(alpha=1.0))
    carer = next(i for i in m.individuals if m._is_carer(i))
    m.effort[carer.id], m.baseline[carer.id] = 0.4, -0.2
    for action in (0.1, 0.9, 0.5, 0.0):
        m._pending = {carer.id: (action, m.effort[carer.id], 0.2, action - 0.4)}
        m._learn({})
    assert m.effort[carer.id] == pytest.approx(0.4)


def test_no_learning_without_a_chance_to_help():
    m = LearnedHelpingModel(cfg(enable_rearing_dependency=True), "B", learning(alpha=1.0))
    m._age_and_budget()
    for i in m.individuals:
        i.stage = "adult" if i.stage == STAGE_JUVENILE else i.stage  # no juveniles anywhere
    m._provide_care()
    assert m._pending == {}


def test_grandmother_stake_uses_her_larger_capacity():
    m = LearnedHelpingModel(cfg(), "C", learning())
    elder = next(i for i in m.individuals if m._is_carer(i))
    elder.sex, elder.stage = "F", "elder"
    assert m.capacity(elder) == pytest.approx(
        m.config["care_capacity_per_helper"] * m.config["grandmother_care_capacity_multiplier"])
    elder.sex = "M"
    assert m.capacity(elder) == pytest.approx(m.config["care_capacity_per_helper"])


@pytest.mark.parametrize("flags", [{"enable_rearing_dependency": False, "enable_care_benefit": False},
                                   {"enable_care_benefit": False}])
def test_no_learning_when_care_cannot_matter(flags):
    m = LearnedHelpingModel(cfg(**flags), "C", learning())
    m._age_and_budget()
    m._provide_care()
    assert m._pending == {}


def test_extinction_before_baseline_scores_as_failure():
    payload = {"history": {"mean_expressed_helping": [0.05] * 10}, "summary": {"final_population": 0}}
    ok, rise = run_step1.step1_success(payload)
    assert ok is False and math.isnan(rise)


def test_score_rejects_incomplete_cells():
    rows = [{"version": v, "start": st, "seed": s, "success": 0}
            for v in ("A", "B", "C") for st in ("rare", "weak") for s in STEP1_SEEDS]
    run_step1.score(rows)
    with pytest.raises(ValueError):
        run_step1.score(rows[:-1])
    dup = rows[:-1] + [dict(rows[0])]
    with pytest.raises(ValueError):
        run_step1.score(dup)


def test_history_index_is_the_step():
    m = LearnedHelpingModel(cfg(simulation_steps=5), "B", learning())
    m.run()
    assert list(m.history["step"]) == list(range(len(m.history["step"])))
    assert len(m.history["mean_expressed_helping"]) == len(m.history["step"])
