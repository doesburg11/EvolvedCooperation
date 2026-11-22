import math

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.kin_selection.config.kin_selection_config import resolve_config
from ecological_models.nowak_mechanisms.kin_selection.bonus_care.bonus_model import BonusCareModel
from ecological_models.nowak_mechanisms.kin_selection.bonus_care.utils.analysis import (
    best_case_margin, care_weighted_relatedness, choose_cell, choose_mu, h0b, kappa, score,
)
from ecological_models.nowak_mechanisms.kin_selection.bonus_care.utils.run_bonus_test import build


def _model(steps=60, **kw):
    return BonusCareModel(resolve_config({"random_seed": 1, "simulation_steps": steps, "write_latest_run": False,
                                          **kw.pop("cfg", {})}), **kw)


def test_care_not_counted_but_paid_in_probe():
    m = build("K", 3, (0.7, 0.8), 0.0, care_counts=False, care_costs=True,
              extra={"simulation_steps": 40, "rare_helper_founder_probability": 0.5})
    assert m.neutral and float(m.config["care_cost_per_unit"]) > 0
    m.run()
    assert sum(m.history["total_care"]) > 0          # helpers still spend care (and energy)
    assert max(m.care_sum.values(), default=0.0) == 0.0  # but none of it reaches survival


def test_main_arm_counts_care_and_neutral_is_free():
    m = build("K", 3, (0.7, 0.8), 0.0, extra={"simulation_steps": 40, "rare_helper_founder_probability": 0.5})
    m.run()
    assert not m.neutral and max(m.care_sum.values()) > 0
    n = build("K", 3, (0.7, 0.8), 0.0, care_counts=False, care_costs=False, extra={"simulation_steps": 5})
    assert n.neutral and float(n.config["care_cost_per_unit"]) == 0.0


def test_survival_without_care_is_p0():
    # with care not counted, juvenile survival per check should be p0 (energy deaths aside)
    m = build("K", 5, (0.7, 0.9), 0.0, care_counts=False, care_costs=False, extra={"simulation_steps": 120})
    m.run()
    rates = [x for x in m.history["juvenile_survival_rate"][1:] if math.isfinite(x)]
    assert abs(np.mean(rates) - 0.9) < 0.03


def test_birth_slots_are_random_order():
    m = _model(steps=1)
    ids_before = [i.id for i in m.individuals]
    m._reproduce()
    assert sorted(i.id for i in m.individuals)[:len(ids_before)] == sorted(ids_before)
    assert [i.id for i in m.individuals][:len(ids_before)] != ids_before


def test_reproduce_respects_cap_with_random_order():
    m = build("K", 2, (0.35, 0.9), 0.0, care_counts=False, care_costs=False, extra={"simulation_steps": 300})
    m.run()
    assert max(m.history["population"]) <= int(m.config["max_population"])


def test_choose_cell_lowest_p0_then_highest_cost():
    rows = []
    for q in ("K", "U"):
        for c in (1.0, 0.5):
            for p in (0.7, 0.8):
                ok = (p == 0.8) or (c == 0.5)
                rows += [{"rearing": q, "repro_cost": c, "p0": p, "persists": int(ok)} for _ in range(3)]
    assert choose_cell(rows, [1.0, 0.5], [0.7, 0.8], ("K", "U"), 3) == (0.5, 0.7)
    rows = [r if not (r["rearing"] == "U" and r["p0"] == 0.7) else {**r, "persists": 0} for r in rows]
    assert choose_cell(rows, [1.0, 0.5], [0.7, 0.8], ("K", "U"), 3) == (1.0, 0.8)
    assert choose_cell([{**r, "persists": 0} for r in rows], [1.0, 0.5], [0.7, 0.8], ("K", "U"), 3) is None


def test_kappa_slope_normalised_per_run():
    # births = 4 * (1 - 0.3 h): relative births fall by 0.3 per unit h (scaled by the run mean)
    h = [0.0, 0.65, 0.0, 0.65]
    run1 = [{"h": x, "births": 4 * (1 - 0.3 * x)} for x in h]
    run2 = [{"h": x, "births": 8 * (1 - 0.3 * x)} for x in h]
    k = kappa([run1, run2])
    mean = (1 + (1 - 0.3 * 0.65)) / 2
    assert k["kappa"] == pytest.approx(0.3 / mean)
    assert math.isnan(kappa([[{"h": 0.0, "births": 1.0}]])["kappa"])


def test_best_case_margin():
    assert best_case_margin(1.0, 0.1) == pytest.approx(-0.1)
    assert best_case_margin(0.8, 0.2) == pytest.approx(0.25 * (1 - 0.8 ** 4) / 0.8 ** 4 - 0.2)


def test_care_weighted_relatedness_skips_empty_steps():
    assert care_weighted_relatedness([0.0, 2.0, 1.0, 3.0], [math.nan, 0.3, 0.6, math.nan]) == pytest.approx(0.4)
    assert math.isnan(care_weighted_relatedness([0.0], [math.nan]))


def test_h0b_thresholds():
    assert h0b([0.3, 0.3], [0.04, 0.05])["H0b"]
    assert not h0b([0.3], [0.06])["H0b"]
    assert not h0b([0.1], [0.04])["H0b"]          # 0.04 > 0.1 / 3
    assert not h0b([math.nan], [0.0])["H0b"]


def _run(arm, persists=1, spreads=0, dt=0.0, rel=0.3):
    return {"arm": arm, "persists": persists, "spreads": spreads, "trait_change": dt,
            "care_weighted_relatedness": rel, "ham": {"analysable": False}, "cohort": []}


def test_score_gates_on_h0b():
    main = {"K": [_run("K", spreads=1, dt=0.1) for _ in range(40)], "U": [_run("U", rel=0.2) for _ in range(40)],
            "K-N": [_run("K-N") for _ in range(40)], "U-N": [_run("U-N") for _ in range(40)]}
    out = score(main, np.random.default_rng(0))
    assert out["H0"] and not out["H0b"] and out["H1"] is None and out["H3_outcome"].startswith("not testable")
    for r in main["U"]:
        r["care_weighted_relatedness"] = 0.01
    out = score(main, np.random.default_rng(0))
    assert out["H0b"] and out["H1"] is True and out["H3_outcome"] == "inconclusive"


def test_allele_mutation_makes_new_unique_alleles():
    m = _model(steps=1, allele_mutation=1.0)
    mother, father = m.individuals[0], m.individuals[1]
    before = m.next_allele_id
    g = m._inherit_genome(mother.genome, father.genome)
    assert g.min() >= before and len(np.unique(g)) == g.size and m.next_allele_id == before + g.size
    m0 = _model(steps=1, allele_mutation=0.0)
    g0 = m0._inherit_genome(m0.individuals[0].genome, m0.individuals[1].genome)
    assert set(g0[:, 0]) <= set(m0.individuals[0].genome.ravel())
    with pytest.raises(ValueError):
        _model(steps=1, allele_mutation=1.5)


def test_allele_mutation_lowers_background_relatedness():
    from ecological_models.nowak_mechanisms.kin_selection.bonus_care.config.bonus_config import NO_HELPER
    vals = {}
    for mu in (0.0, 0.05):
        m = build("U", 0, (0.5, 0.9), mu, extra={**NO_HELPER, "simulation_steps": 300})
        m.run()
        vals[mu] = m.mean_random_adult_relatedness(300, np.random.default_rng(0))
    assert vals[0.05] < vals[0.0]


def test_choose_mu():
    rows = [{"mu": 0.01, "survived": 1, "background_relatedness": 0.05}] * 2 + \
           [{"mu": 0.02, "survived": 1, "background_relatedness": 0.02},
            {"mu": 0.02, "survived": 0, "background_relatedness": float("nan")}] + \
           [{"mu": 0.05, "survived": 1, "background_relatedness": 0.03}] * 2
    assert choose_mu(rows, [0.01, 0.02, 0.05], 2, 0.03) == 0.05
    assert choose_mu(rows, [0.01, 0.02], 2, 0.03) is None
