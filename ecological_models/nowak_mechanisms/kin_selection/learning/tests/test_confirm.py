import math

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.kin_selection.config.kin_selection_config import resolve_config
from ecological_models.nowak_mechanisms.kin_selection.learning.config.learning_config import (
    CONFIRM_ARMS, CONFIRM_SEEDS, LEARNING)
from ecological_models.nowak_mechanisms.kin_selection.learning.learning_model import LearnedHelpingModel
from ecological_models.nowak_mechanisms.kin_selection.learning.utils import run_confirm as rc


def cfg(**kw):
    return resolve_config({"random_seed": 5, "simulation_steps": 30, "care_cost_per_unit": 0.03,
                           "write_latest_run": False, "rare_helper_founder_probability": 0.0, **kw})


def test_persistence_uses_the_whole_window_and_short_histories_fail():
    pop = [150] * 221
    assert rc.persists(pop, (181, 220))
    pop[200] = 99
    assert not rc.persists(pop, (181, 220))
    assert not rc.persists([150] * 220, (181, 220))  # died out before step 220


def test_window_cost():
    h = {"total_helper_energy_cost": [9, 1, 2, 3], "adult_count": [9, 1, 1, 2], "elder_count": [9, 1, 1, 0]}
    assert rc.window_cost(h, (1, 3)) == pytest.approx(6 / 6)


def test_alpha_zero_keeps_effort_and_constant_arm_is_deterministic():
    m = LearnedHelpingModel(cfg(), "B", {**LEARNING, "alpha": 0.0, "initial_effort": 0.15,
                                          "exploration_stddev": 0.0})
    m.run()
    e = [x for x in m.history["mean_expressed_helping"] if math.isfinite(x)]
    assert all(x == pytest.approx(0.15) for x in e)
    m = LearnedHelpingModel(cfg(), "C", {**LEARNING, "alpha": 0.0})
    m.run()
    assert all(v == pytest.approx(LEARNING["initial_effort"]) for v in m.effort.values())


def test_constant_arm_cares_at_that_effort():
    m = LearnedHelpingModel(cfg(), "B", {**LEARNING, "alpha": 0.0, "initial_effort": 0.3, "exploration_stddev": 0.0})
    for _ in range(3):
        m.step()
    m._age_and_budget()
    m._provide_care()
    assert m._pending and all(a == pytest.approx(0.3) for a, *_ in m._pending.values())


def test_frozen_kin_regard_ignores_parents():
    m = LearnedHelpingModel(cfg(), "C", {**LEARNING, "alpha": 0.2, "frozen_kin_regard": True})
    mother = next(i for i in m.individuals if i.sex == "F")
    father = next(i for i in m.individuals if i.sex == "M")
    mother.helping_trait = father.helping_trait = 0.9
    kids = [m._create_child(mother, father, initial_child=False).helping_trait for _ in range(200)]
    assert max(kids) <= 0.04 and min(kids) >= 0.0
    m2 = LearnedHelpingModel(cfg(), "C", {**LEARNING, "alpha": 0.2})
    mother = next(i for i in m2.individuals if i.sex == "F")
    father = next(i for i in m2.individuals if i.sex == "M")
    mother.helping_trait = father.helping_trait = 0.9
    assert np.mean([m2._create_child(mother, father, initial_child=False).helping_trait for _ in range(50)]) > 0.8


def rows_for(rates, start="weak", cost=None):
    n = len(CONFIRM_SEEDS)
    out = []
    for arm, k in rates.items():
        for i, s in enumerate(CONFIRM_SEEDS):
            out.append({"arm": arm, "start": start, "seed": s, "steps": 220, "persists": int(i < k),
                        "cost_per_carer_step": (cost or {}).get(arm, 1.0), "mean_action_1_60": 0.08})
    assert all(k <= n for k in rates.values())
    return out


def test_paired_sign_test():
    r = rows_for({"C": 36, "A": 4})
    p = rc.paired(r, "C", "A", "weak", 0.40)
    assert p["only_better"] == 32 and p["only_worse"] == 0 and p["met"]
    r = rows_for({"C": 20, "A": 20})
    assert not rc.paired(r, "C", "A", "weak", 0.40)["met"] and rc.paired(r, "C", "A", "weak", 0.4)["p"] == 1.0


def consts(k):
    return {a: k for a in rc.CONFIRM_CONSTANT_ARMS}


def test_h3_no_match_is_met_inside_grid():
    r = rows_for({"C": 38, **consts(10)})
    out = rc.h3(r, np.random.default_rng(0))
    assert out["matching_arms"] == [] and out["met"]


def test_h3_match_uses_cheapest_matching_arm_cost():
    cost = {"C": 1.0, **{a: 2.0 for a in rc.CONFIRM_CONSTANT_ARMS}}
    rates = {"C": 38, **consts(10), "D0.20": 38, "D0.30": 38}
    out = rc.h3(rows_for(rates, cost=cost), np.random.default_rng(0))
    assert out["cheapest_matching_arm"] == "D0.20" and out["met"]
    cost["D0.20"] = 1.1
    assert not rc.h3(rows_for(rates, cost=cost), np.random.default_rng(0))["met"]


def test_every_arm_and_long_run_is_scheduled_once():
    jobs = rc.jobs()
    assert len(jobs) == len(set(jobs))
    n = sum(len(starts) for _, _, starts in CONFIRM_ARMS.values()) * len(CONFIRM_SEEDS) + 4 * len(CONFIRM_SEEDS)
    assert len(jobs) == n


def test_exact_thresholds_pass_without_float_rounding():
    r = rows_for({"C": 17, "A": 1})            # 16/40 = 0.40 exactly
    assert rc.paired(r, "C", "A", "weak", 0.40)["met"]
    r = rows_for({"C": 15, "A": 0})            # 0.375 < 0.40
    assert not rc.paired(r, "C", "A", "weak", 0.40)["met"]
    r = rows_for({"C": 12, "C-nolearn": 0})    # 12/40 = 0.30 exactly
    assert rc.paired(r, "C", "C-nolearn", "weak", 0.30)["met"]


def test_h3_matching_boundary_is_four_runs():
    rates = {"C": 32, **consts(0), "D0.30": 28}  # exactly 0.10 below C: matching
    assert rc.h3(rows_for(rates), np.random.default_rng(0))["matching_arms"] == ["D0.30"]
    rates["D0.30"] = 27
    assert rc.h3(rows_for(rates), np.random.default_rng(0))["matching_arms"] == []


def test_h3_picks_the_cheapest_matching_arm_and_breaks_ties_by_effort():
    rates = {"C": 38, **consts(38)}
    cost = {"C": 1.0, **{a: 2.0 for a in rc.CONFIRM_CONSTANT_ARMS}, "N0.20": 1.05}
    out = rc.h3(rows_for(rates, cost=cost), np.random.default_rng(0))
    assert out["cheapest_matching_arm"] == "N0.20" and not out["met"]
    cost = {"C": 1.0, **{a: 2.0 for a in rc.CONFIRM_CONSTANT_ARMS}}
    out = rc.h3(rows_for(rates, cost=cost), np.random.default_rng(0))
    assert out["cheapest_matching_arm"] == "C-nolearn" and out["met"]  # tie at cost 2: lowest effort 0.05, then name


def test_h3_no_match_outside_grid_is_inconclusive():
    r = rows_for({"C": 38, **consts(0)})
    for x in r:
        x["mean_action_1_60"] = 0.4
    out = rc.h3(r, np.random.default_rng(0))
    assert out["outcome"] == "inconclusive" and not out["met"]


def test_zero_or_nan_c_cost_is_skipped_in_ratios():
    rates = {"C": 38, **consts(38)}
    r = rows_for(rates, cost={"C": 0.0, **{a: 2.0 for a in rc.CONFIRM_CONSTANT_ARMS}})
    out = rc.h3(r, np.random.default_rng(0))
    assert out["ratios_used"] == 0 and not out["met"]


def test_mean_care_action_is_the_realized_noisy_action():
    m = LearnedHelpingModel(cfg(simulation_steps=40), "C", {**LEARNING, "alpha": 0.0})
    m.run()
    a = [x for x in m.history["mean_care_action"] if math.isfinite(x)]
    assert a and 0.06 < np.mean(a) < 0.085  # clamp(0.05 + N(0, 0.1)) has mean about 0.07
    assert len(m.history["mean_care_action"]) == len(m.history["step"])


def test_frozen_arm_keeps_cs_main_random_stream():
    """Until the first birth, C and C-frozen draw the same main-stream numbers."""
    a = LearnedHelpingModel(cfg(), "C", {**LEARNING, "alpha": 0.2})
    b = LearnedHelpingModel(cfg(), "C", {**LEARNING, "alpha": 0.2, "frozen_kin_regard": True})
    assert [i.energy for i in a.individuals] == [i.energy for i in b.individuals]
    assert a.rng.random() == b.rng.random()


def test_long_run_and_cost_window_with_extinction():
    h = {"total_helper_energy_cost": [0, 2, 2], "adult_count": [5, 2, 0], "elder_count": [0, 0, 0]}
    assert rc.window_cost(h, (1, 60)) == pytest.approx(2.0)  # truncated history: alive steps only
    assert not rc.persists([200] * 300, (401, 440))
