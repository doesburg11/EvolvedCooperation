import math

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.kin_selection.config.kin_selection_config import resolve_config
from ecological_models.nowak_mechanisms.kin_selection.kin_selection_model import (
    STAGE_JUVENILE, EcologicalKinSelectionModel)
from ecological_models.nowak_mechanisms.kin_selection.floor_control.config.floor_config import (
    NO_HELPER, REARING, STEP0_FLOORS, STEP0_REARING, STEP0_SEEDS)
from ecological_models.nowak_mechanisms.kin_selection.floor_control.floor_model import FloorKinSelectionModel
from ecological_models.nowak_mechanisms.kin_selection.floor_control.utils import analysis as an
from ecological_models.nowak_mechanisms.kin_selection.floor_control.utils import run_floor_test as rt


def cfg(**kw):
    return resolve_config({"random_seed": 4, "simulation_steps": 40, "write_latest_run": False,
                           "care_cost_per_unit": 0.03, **kw})


def test_floor_zero_is_the_base_model():
    base = EcologicalKinSelectionModel(cfg()).run()
    mine = FloorKinSelectionModel(cfg(), floor=0.0).run()
    assert base["summary"] == mine["summary"]


def test_floor_adds_care_before_saturation_and_neutral_ignores_helpers():
    seen = {}
    m = FloorKinSelectionModel(cfg(), floor=0.2)
    orig = EcologicalKinSelectionModel._apply_survival
    m._age_and_budget()
    care, rel, _ = m._provide_care()
    juv = [i.id for i in m.individuals if i.stage == STAGE_JUVENILE]
    EcologicalKinSelectionModel._apply_survival = lambda self, c, r: (seen.update(c), (0, 0.0, {}))[1]
    try:
        m._apply_survival(care, rel)
        assert all(seen[j] == pytest.approx(0.2 + care.get(j, 0.0)) for j in juv)
        n = FloorKinSelectionModel(cfg(care_cost_per_unit=0.0), floor=0.2, neutral=True)
        n._age_and_budget()
        c2, r2, _ = n._provide_care()
        seen.clear()
        n._apply_survival(c2, r2)
        assert seen and all(v == pytest.approx(0.2) for v in seen.values())
    finally:
        EcologicalKinSelectionModel._apply_survival = orig


def test_neutral_needs_zero_cost():
    with pytest.raises(ValueError):
        FloorKinSelectionModel(cfg(), floor=0.1, neutral=True)


def test_effective_care_excludes_floor_and_saturated_care():
    m = FloorKinSelectionModel(cfg(), floor=0.4)
    m._age_and_budget()
    juv = next(i for i in m.individuals if i.stage == STAGE_JUVENILE)
    orig = EcologicalKinSelectionModel._apply_survival
    EcologicalKinSelectionModel._apply_survival = lambda self, c, r: (0, 0.0, {})
    try:
        m._apply_survival({juv.id: 2.0}, {})   # 0.4 + 2.0 saturates at 0.9 -> effective 0.5
        m._apply_survival({juv.id: 0.1}, {})   # effective 0.1
    finally:
        EcologicalKinSelectionModel._apply_survival = orig
    assert m.care_sum[juv.id] / m.care_checks[juv.id] == pytest.approx(0.3)
    assert m.saturated_checks >= 1


def test_recruits_are_credited_once_at_maturity_and_cohort_rules():
    m = FloorKinSelectionModel(cfg(simulation_steps=60), floor=0.3)
    m.run()
    assert sum(m.recruited.values()) == 2 * len(m._credited & set(m.birth_record))
    maturity = m.config["juvenile_maturity_age"]
    for i in m.individuals:
        if i.id in m.birth_record and i.age >= maturity + 1:
            assert i.id in m._credited
    rows = m.cohort((20, 40))
    assert rows and all(r["w"] >= 0 and r["s"] >= 0 for r in rows)
    n_born = sum(1 for r in m.birth_record.values() if 20 <= r["born"] <= 40)
    assert len(rows) + m.excluded_from_cohort((20, 40)) == n_born


def test_unrelated_rearing_fosters_out_without_dispersal():
    m = FloorKinSelectionModel(resolve_config({"random_seed": 1, "simulation_steps": 30, "write_latest_run": False,
                                               **REARING["U"]}), floor=0.3)
    m.run()
    assert m.config["matured_dispersal_probability"] == 0.0
    kids = [i for i in m.individuals if i.mother_id is not None and i.born_step > 0]
    assert kids and all(i.fostered_from_birth for i in kids if i.stage == STAGE_JUVENILE)


def test_no_helper_control_has_zero_helping():
    m = FloorKinSelectionModel(cfg(**NO_HELPER), floor=0.3)
    m.run()
    assert np.nanmax(np.asarray(m.history["mean_helping_trait"], float)) == 0.0


def test_hamilton_recovers_known_coefficients():
    rng = np.random.default_rng(0)
    h = rng.random(4000)
    s = 0.3 * h + rng.random(4000)
    male = rng.integers(0, 2, 4000)
    w = 2.0 - 0.5 * h + 1.0 * s + 0.1 * male
    rows = [{"w": a, "h": b, "s": c, "male": d} for a, b, c, d in zip(w, h, s, male)]
    res = an.hamilton(rows)
    wm = w.mean()
    assert res["analysable"]
    assert res["c"] == pytest.approx(0.5 / wm, rel=1e-6) and res["b_s"] == pytest.approx(1.0 / wm, rel=1e-6)
    assert res["r"] == pytest.approx(0.3, abs=0.03)
    assert res["margin"] == pytest.approx(res["r"] * res["b_s"] - res["c"])


def test_hamilton_unanalysable_cases():
    assert not an.hamilton([{"w": 1, "h": 0.1, "s": 0.2, "male": 0}] * 10)["analysable"]       # too few
    rows = [{"w": 0.0, "h": i / 100, "s": i / 50, "male": i % 2} for i in range(100)]
    assert not an.hamilton(rows)["analysable"]                                                  # mean w 0
    rows = [{"w": 1.0 + i % 3, "h": 0.2, "s": i / 50, "male": i % 2} for i in range(100)]
    assert not an.hamilton(rows)["analysable"]                                                  # no h variance


def test_persists_and_spread_rules():
    assert an.persists([150] * 221, (181, 220)) and not an.persists([150] * 220, (181, 220))
    p = [150] * 221
    p[190] = 99
    assert not an.persists(p, (181, 220))
    assert an.spreads(True, 0.015, 0.02) and not an.spreads(False, 0.5, 0.5) and not an.spreads(True, 0.01, 0.5)
    h = {"mean_helping_trait": [0.05, 0.1, math.nan], "helping_invasion_frequency": [0.03, 0.2, math.nan]}
    assert an.trait_change(h) == pytest.approx(0.05) and an.frequency_change(h) == pytest.approx(0.17)


def test_choose_floor_needs_all_seeds_in_both_modes():
    rows = [{"rearing": q, "floor": f, "seed": s, "persists": int(f >= 0.15 or (q == "K" and f >= 0.1))}
            for q in STEP0_REARING for f in STEP0_FLOORS for s in STEP0_SEEDS]
    assert rt.choose_floor(rows) == 0.15
    rows = [dict(r, persists=0) if r["seed"] == 0 else r for r in rows]
    assert rt.choose_floor(rows) is None


def fake_runs(n_persist, n_spread, dtrait, margins=None, n=40):
    out = []
    for i in range(n):
        m = None if margins is None else margins[i % len(margins)]
        ham = {"analysable": m is not None, "c": 0.2, "b_s": 1.0, "r": 0.3, "margin": m} if m is not None \
            else {"analysable": False}
        out.append({"persists": int(i < n_persist), "spreads": int(i < n_spread), "trait_change": dtrait[i % len(dtrait)],
                    "ham": ham, "cohort": []})
    return out


def test_score_all_met_and_failure_modes():
    rng = np.random.default_rng(0)
    main = {"K": fake_runs(40, 20, [0.2, 0.3], margins=[0.1, 0.12]),
            "U": fake_runs(40, 2, [-0.01, 0.0], margins=[-0.05, 0.02]),
            "K-N": fake_runs(40, 0, [0.0, 0.001]), "U-N": fake_runs(40, 0, [0.0, 0.001])}
    v = an.score(main, rng)
    assert v["H0"] and v["H1"] and v["H1b"] and v["H2"] and v["H3"] and v["H3_outcome"] == "met"
    main["U"] = fake_runs(35, 2, [-0.01, 0.0], margins=[-0.05, 0.02])
    v = an.score(main, rng)
    assert not v["H0"] and v["H1"] is None and v["H3"] is None and v["H3_outcome"].startswith("not testable")
    main["U"] = fake_runs(40, 11, [-0.01, 0.0], margins=[-0.05, 0.02])     # K-U = 9 < 10, U spread 11 > 4
    v = an.score(main, rng)
    assert not v["H1"] and not v["H2"]
    main["U"] = fake_runs(40, 2, [-0.01, 0.0], margins=[-0.05, 0.02])
    main["K"] = fake_runs(40, 20, [0.2, 0.3], margins=[0.1, None, None, None])  # only 10 analysable
    assert an.score(main, rng)["H3_outcome"] == "inconclusive"
