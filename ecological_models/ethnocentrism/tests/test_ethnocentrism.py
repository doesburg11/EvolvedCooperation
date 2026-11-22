"""Tests for the Ethnocentrism port. Run: ./.conda/bin/python -m pytest ecological_models/ethnocentrism/tests -q"""
from __future__ import annotations

import numpy as np
import pytest

from ecological_models.ethnocentrism.config.ethnocentrism_config import BASE, run_config
from ecological_models.ethnocentrism.ethnocentrism_model import EMPTY, Ethnocentrism, _neighbour_table


def small(**kw):
    return {**BASE, "width": 5, "height": 5, "ticks": 10, "lineage_sample_every": 0, **kw}


def place(m, cell, color, cs, cd, parent=EMPTY):
    m.agent[cell] = m._new_id(parent)
    m.color[cell], m.cs[cell], m.cd[cell] = color, cs, cd
    m.ptr[cell] = m.cfg["initial_ptr"]


def test_neighbour_table_torus():
    nbr = _neighbour_table(5, 4)
    assert sorted(nbr[0].tolist()) == sorted([15, 1, 5, 4])          # up wraps to last row, left wraps to col 4
    for cell in range(20):                                             # neighbourhood is symmetric
        for n in nbr[cell]:
            assert cell in nbr[n]
    with pytest.raises(ValueError):
        _neighbour_table(2, 5)


def test_interact_accounting():
    m = Ethnocentrism(small(), seed=0)
    # row 0: [A same-colour helper (cs, not cd)] [B same colour, selfish] [C other colour, helps different]
    place(m, 0, 0, True, False)
    place(m, 1, 0, False, False)
    place(m, 2, 1, False, True)
    m._interact()
    cost, gain, p0 = BASE["cost_of_giving"], BASE["gain_of_receiving"], BASE["initial_ptr"]
    # A gives to B; B gives nobody; C gives to B (different colour). A-C are not neighbours on a 5-wide torus.
    assert m.ptr[0] == pytest.approx(p0 - cost)
    assert m.ptr[1] == pytest.approx(p0 + 2 * gain)
    assert m.ptr[2] == pytest.approx(p0 - cost)
    t = m.turn
    assert t["meet"] == 4 and t["meetown"] == 2 and t["meetother"] == 2
    assert t["coopown"] == 1 and t["coopother"] == 1 and t["defother"] == 1


def test_mutation_always_changes_colour_and_toggles_flags():
    m = Ethnocentrism(small(mutation_rate=1.0), seed=1)
    place(m, 0, 2, True, False)
    for target in range(1, 25):
        m._hatch(0, target)
        assert m.color[target] != 2
        assert not m.cs[target] and m.cd[target]
    assert set(m.color[1:].tolist()) == {0, 1, 3}


def test_no_mutation_copies_parent_and_founder():
    m = Ethnocentrism(small(mutation_rate=0.0), seed=2)
    place(m, 0, 3, True, True)
    m._hatch(0, 1); m._hatch(1, 2)
    assert m.color[2] == 3 and m.cs[2] and m.cd[2]
    assert m.parent[m.agent[2]] == m.agent[1] and m.founder[m.agent[2]] == m.agent[0]


def test_reproduction_only_into_empty_neighbours_and_children_wait():
    m = Ethnocentrism(small(mutation_rate=0.0), seed=3)
    place(m, 12, 0, True, True)
    m.ptr[12] = 2.0                                                    # certain to reproduce
    m._reproduce()
    occupied = np.flatnonzero(m.agent != EMPTY).tolist()
    assert len(occupied) == 2                                          # one child, which did not reproduce itself
    child = [c for c in occupied if c != 12][0]
    assert child in m.nbr[12].tolist()


def test_reproduction_blocked_when_surrounded():
    m = Ethnocentrism(small(), seed=4)
    place(m, 12, 0, True, True)
    for n in m.nbr[12]:
        place(m, int(n), 0, True, True)
        m.ptr[int(n)] = -1.0                                           # neighbours never reproduce
    m.ptr[12] = 2.0
    before = len(m.parent)
    m._reproduce()
    assert len(m.parent) == before


def test_immigration_capped_by_empty_cells():
    m = Ethnocentrism(small(immigrants_per_day=30), seed=5)
    m._immigrate()
    assert (m.agent != EMPTY).sum() == 25
    m._immigrate()                                                     # full world: nobody more
    assert len(m.parent) == 25


def test_setup_full_and_unknown_setup():
    assert (Ethnocentrism(small(setup="full"), seed=0).agent != EMPTY).all()
    with pytest.raises(ValueError):
        Ethnocentrism(small(setup="half"), seed=0)


def test_lineage_pairs_known_pedigree():
    m = Ethnocentrism(small(mutation_rate=0.0), seed=6)
    place(m, 0, 0, True, True)                          # founder F at cell 0
    m._hatch(0, 1)                                      # child c1 at cell 1 (right of F)
    m._hatch(0, 5)                                      # child c2 at cell 5 (below F)
    place(m, 2, 1, False, False)                        # unrelated immigrant, other colour, right of c1
    m._hatch(5, 10)                                     # grandchild g at cell 10 (below c2)
    m.tick = 7
    L = m.lineage_metrics()
    # unordered pairs: F-c1, c1-imm, F-c2, c2-g  (cells 0-1, 1-2, 0-5, 5-10)
    assert L["all_n_pairs"] == 4 and L["same_n_pairs"] == 3 and L["diff_n_pairs"] == 1
    assert L["same_frac_same_founder"] == 1.0 and L["diff_frac_same_founder"] == 0.0
    assert L["same_gen_dist_mean"] == pytest.approx(1.0)  # all three are parent-offspring pairs
    assert L["same_frac_gen_le2"] == 1.0
    assert L["n_founders_alive"] == 2 and L["colour_fidelity"] == 1.0


def test_lineage_cousins():
    m = Ethnocentrism(small(mutation_rate=0.0), seed=7)
    place(m, 12, 0, True, True)                         # founder F (row 2, col 2)
    m._hatch(12, 7)                                     # child c1 (above), born at tick 0
    m.tick = 2
    m._hatch(12, 17)                                    # child c2 (below), born at tick 2
    m._hatch(7, 6); m._hatch(17, 16)                    # grandchildren g1 (left of c1), g2 (left of c2), tick 2
    m.agent[[12, 7, 17]] = EMPTY
    m.tick = 4
    m._hatch(6, 11)                                     # great-grandchild gg (row 2, col 1), born at tick 4
    m.tick = 9
    L = m.lineage_metrics()
    # living column g1 (6), gg (11), g2 (16): pairs g1-gg (parent-child, 1) and gg-g2 (3 + 2 = 5 births via F)
    assert L["all_n_pairs"] == 2 and L["same_frac_same_founder"] == 1.0
    assert L["same_gen_dist_mean"] == pytest.approx(3.0)
    assert L["same_frac_gen_le2"] == pytest.approx(0.5)
    assert L["same_tmrca_median"] == pytest.approx(((9 - 2) + (9 - 0)) / 2)   # MRCAs: g1 (born 2) and F (born 0)


def test_strategy_relatedness_checkerboard():
    m = Ethnocentrism(small(width=4, height=4), seed=8)
    for cell in range(16):
        y, x = divmod(cell, 4)
        place(m, cell, 0, bool((x + y) % 2), True)     # every neighbour pair differs in cs
    L = m.lineage_metrics()
    assert L["all_r_pop_cs"] == pytest.approx(-1.0) and L["all_r_reg_cs"] == pytest.approx(-1.0)
    assert np.isnan(L["all_r_pop_cd"]) and np.isnan(L["all_r_reg_cd"])                      # cd constant: relatedness undefined


def test_seed_determinism_and_reporter_ranges():
    cfg = {**run_config("104"), "ticks": 300}
    a, b = Ethnocentrism(cfg, 11).run(), Ethnocentrism(cfg, 11).run()
    assert a["reporters"] == b["reporters"] and a["lineage"] == b["lineage"]
    r = a["reporters"]
    assert all(0.0 <= v <= 1.0 for v in r.values())
    assert sum(r[k] for k in ("cc-percent", "cd-percent", "dc-percent", "dd-percent")) == pytest.approx(1.0)
    assert len(a["lineage"]) == 3                       # ticks 100, 200, 300


def test_contested_vacancy_goes_to_one_parent():
    m = Ethnocentrism(small(mutation_rate=0.0), seed=9)
    # cells 11 and 13 both border only one free cell, 12; fill everything else
    for cell in range(25):
        if cell != 12:
            place(m, cell, 0, True, True)
            m.ptr[cell] = -1.0
    m.ptr[11] = m.ptr[13] = 2.0
    m._reproduce()
    assert (m.agent != EMPTY).all() and len(m.parent) == 25       # exactly one child, in cell 12
    assert m.parent[m.agent[12]] in (m.agent[11], m.agent[13])


def test_full_tick_newborn_can_die_and_stats_after_death():
    cfg = small(width=3, height=3, ticks=1, initial_ptr=1.0, death_rate=1.0, mutation_rate=0.0)
    m = Ethnocentrism(cfg, 0)
    out = m.run()
    assert m.parent == [EMPTY, 0]                                  # immigrant reproduced once, child did not
    assert out["population"] == 0 and list(m.win["cc"]) == [0]     # both died; counts taken after death


def test_last100_window_rollover():
    m = Ethnocentrism(small(immigrants_per_day=0), seed=0)
    for tick in range(101):
        m.turn = {"meet": 7 if tick == 0 else 10 if tick == 100 else 2, "meetown": 1, "meetother": 0,
                  "coopown": 1, "coopother": 0, "defother": 0}
        m._update_stats()
    r = m.reporters()
    assert len(m.win["meet"]) == 100                               # tick 0 evicted
    assert r["last100meetown-percent"] == pytest.approx(100 / (99 * 2 + 10))


def test_r_pop_vs_r_reg_when_helpers_enriched():
    m = Ethnocentrism(small(), seed=10)
    # a same-colour helper pair and an isolated non-helper elsewhere
    place(m, 0, 0, True, True); place(m, 1, 0, True, True)
    place(m, 12, 1, False, True); place(m, 18, 2, False, True)
    L = m.lineage_metrics()
    assert L["same_n_pairs"] == 1 and L["diff_n_pairs"] == 0
    assert L["same_r_pop_cs"] == pytest.approx((1 - 0.25) / 0.25)  # 3: helpers enriched in the group
    assert np.isnan(L["same_r_reg_cs"])                            # no variation among the group's endpoints
    assert np.isnan(L["diff_frac_same_founder"])                   # stable keys, NaN when no pairs


def test_empty_world_lineage_schema():
    m = Ethnocentrism(small(), seed=0)
    L = m.lineage_metrics()
    full = Ethnocentrism(small(setup="full"), seed=0).lineage_metrics()
    assert set(L) == set(full) and L["population"] == 0


def test_netlogo_reference_validation(tmp_path, monkeypatch):
    from ecological_models.ethnocentrism.utils import run_experiments as rx
    d = tmp_path / "netlogo_exp104"; d.mkdir()
    cols = ["[run number]", *rx.NETLOGO_PARAM, "max-pxcor", "max-pycor", "[step]", *rx.CHECK_METRICS]
    cfg = run_config("104")
    def row(i, step=2000):
        return [str(i), *[str(cfg[v]) for v in rx.NETLOGO_PARAM.values()], "50", "50", str(step),
                *["0.5"] * len(rx.CHECK_METRICS)]
    def write(rows):
        (d / "table.csv").write_text("\n".join(",".join(r) for r in [["x"], cols, *rows]) + "\n")
    monkeypatch.setattr(rx, "NETLOGO_RESULTS_DIR", str(tmp_path))
    write([row(i) for i in range(1, 11)])
    assert len(rx.netlogo_table("104")) == 10
    for bad in ([row(i) for i in range(1, 10)],                    # truncated
                [row(1)] * 10,                                     # duplicated run numbers
                [row(i, step=1000) for i in range(1, 11)]):        # not the final tick
        write(bad)
        with pytest.raises(ValueError):
            rx.netlogo_table("104")
    assert rx.flag(float("nan"), 0.0) and rx.flag(0.0001, 0.06)
    assert not rx.flag(0.0001, 0.04) and not rx.flag(0.01, 0.2)
