"""Tests for the Ethnocentrism port. Run: ./.conda/bin/python -m pytest ecological_models/ethnocentrism/tests -q"""
from __future__ import annotations

import math

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


def test_random_colour_inheritance():
    m = Ethnocentrism(small(width=40, height=40, mutation_rate=0.0, colour_inheritance="random"), seed=12)
    place(m, 0, 2, True, False)
    for target in range(1, 1600):
        m._hatch(0, target)
    counts = np.bincount(m.color[1:], minlength=4)
    assert counts.min() > 330 and counts.max() < 470               # ~uniform (expected 400 each), parent colour 2 not favoured
    assert m.cs[1:].all() and not m.cd[1:].any()                   # strategy still inherited
    assert all(f == m.agent[0] for f in m.founder)                 # pedigree unaffected
    with pytest.raises(ValueError):
        Ethnocentrism(small(colour_inheritance="sometimes"), seed=0)


def test_inherited_is_default():
    cfg = {**run_config("104"), "ticks": 150}
    no_key = {k: v for k, v in cfg.items() if k != "colour_inheritance"}
    assert Ethnocentrism(cfg, 3).run()["reporters"] == Ethnocentrism(no_key, 3).run()["reporters"]



def test_random_colour_all_parent_colours_with_mutation():
    m = Ethnocentrism(small(width=40, height=40, mutation_rate=0.5, colour_inheritance="random"), seed=13)
    for col in range(4):
        place(m, col, col, True, False)
    children = range(4, 1600)
    for target in children:
        m._hatch(target % 4, target)
    for col in range(4):
        kids = np.array([t for t in children if t % 4 == col])
        counts = np.bincount(m.color[kids], minlength=4)
        assert counts.min() > 60 and counts.max() < 140                 # ~99 each: uniform whatever the parent colour
        assert 0.40 < m.cs[kids].mean() < 0.60 and 0.40 < m.cd[kids].mean() < 0.60   # flags still mutate (rate 0.5)


def test_random_colour_judge():
    from ecological_models.ethnocentrism.utils.run_random_colour import judge
    rng = np.random.default_rng(0)
    inh, rnd = 0.75 + 0.02 * rng.standard_normal(30), 0.40 + 0.02 * rng.standard_normal(30)
    ok_gap = 0.01 * rng.standard_normal(30)
    assert judge(inh, rnd, ok_gap, 30)["verdict"] == "H1 met"
    assert judge(inh, rnd, np.full(30, 0.3), 30)["verdict"] == "invalid: manipulation check failed"
    cancelling = np.r_[np.full(15, 0.25), np.full(15, -0.25)]                 # mean 0 but large per-seed gaps
    assert judge(inh, rnd, cancelling, 30)["verdict"] == "invalid: manipulation check failed"
    assert judge(inh, rnd, np.r_[ok_gap[:29], np.nan], 30)["verdict"] == "invalid: manipulation check failed"
    assert judge(inh, rnd, ok_gap, 30, baseline_ok=False)["verdict"].startswith("invalid: inherited")
    assert judge(np.full(30, 0.75), np.full(30, 0.4), ok_gap, 30)["verdict"].startswith("invalid: endpoint")
    assert judge(inh[:1], rnd[:1], ok_gap, 30)["verdict"].startswith("invalid: endpoint")      # wrong run count
    assert judge(np.r_[inh[:29], np.nan], rnd, ok_gap, 30)["verdict"].startswith("invalid: endpoint")
    assert judge(inh, inh - 0.05, ok_gap, 30)["verdict"] == "H1 not met"                    # drop too small
    assert judge(rnd, inh, ok_gap, 30)["verdict"] == "H1 not met"                           # wrong direction
    noisy_r = 0.6 + 0.4 * rng.standard_normal(30)                                           # big drop, p not small
    v = judge(np.full(30, 0.75) + 0.4 * rng.standard_normal(30), noisy_r, ok_gap, 30)
    assert v["ethno_p"] > 0.001 and v["verdict"] == "H1 not met"
    edge = judge(np.full(30, 0.5) + np.r_[0.01, -0.01, np.zeros(28)], np.full(30, 0.4), ok_gap, 30)
    assert edge["ethno_drop"] == pytest.approx(0.1) and edge["ethno_p"] < 0.001 and edge["verdict"] == "H1 met"


def test_baseline_replay_check(tmp_path):
    from ecological_models.ethnocentrism.utils.run_random_colour import baseline_matches
    rep = {"cd-percent": 0.7123456789012345, "cc-percent": 0.1}
    runs = [{"seed": s, "population": 900 + s, "births_total": 5000, "reporters": dict(rep)} for s in range(3)]
    path = tmp_path / "runs.csv"
    def write(rows, births=5000, cd=rep["cd-percent"], extra_col=False):
        lines = ["experiment,seed,population,births_total,cd-percent,cc-percent" + (",dd-percent" if extra_col else "")]
        lines += [f"{e},{s},{p},{births},{repr(cd)},0.1" + (",0.2" if extra_col else "") for e, s, p in rows]
        path.write_text("\n".join(lines) + "\n")
    write([("104", s, 900 + s) for s in range(3)] + [("105", 0, 1)])
    assert baseline_matches(runs, path)
    write([("104", s, 900 + s) for s in range(2)])                                          # a seed missing
    assert not baseline_matches(runs, path)
    write([("104", 0, 1), ("104", 1, 901), ("104", 2, 902)])                                # population differs
    assert not baseline_matches(runs, path)
    assert not baseline_matches(runs, tmp_path / "absent.csv")
    good = [("104", s, 900 + s) for s in range(3)]
    write(good + [("104", 0, 900)])                                                         # duplicate seed
    assert not baseline_matches(runs, path)
    write(good, births=4999)                                                                # births differ
    assert not baseline_matches(runs, path)
    write(good, cd=0.7123456789012346)                                                      # reporter differs in last digit
    assert not baseline_matches(runs, path)
    write(good, extra_col=True)                                                             # reference has a reporter the run lacks
    assert not baseline_matches(runs, path)


def test_dispersal_places_child_anywhere_and_zero_is_unchanged():
    m = Ethnocentrism(small(width=9, height=9, mutation_rate=0.0, dispersal=1.0), seed=14)
    place(m, 40, 0, True, True)
    m.ptr[40] = 2.0
    far = 0
    for _ in range(60):
        m._reproduce()
        kids = [c for c in np.flatnonzero(m.agent != EMPTY).tolist() if c != 40]
        far += sum(c not in m.nbr[40].tolist() for c in kids)
        m.agent[kids] = EMPTY
    assert far > 40                                                  # 76 of 80 empty cells are not neighbours
    # blocked locally but dispersal finds the one empty cell elsewhere
    m = Ethnocentrism(small(mutation_rate=0.0, dispersal=1.0), seed=15)
    for cell in range(25):
        if cell != 0:
            place(m, cell, 0, True, True); m.ptr[cell] = -1.0
    m.ptr[12] = 2.0
    m._reproduce()
    assert (m.agent != EMPTY).all() and m.parent[m.agent[0]] == m.agent[12]
    cfg = {**run_config("104"), "ticks": 150}
    assert Ethnocentrism({**cfg, "dispersal": 0.0}, 4).run()["reporters"] == Ethnocentrism(
        {k: v for k, v in cfg.items() if k != "dispersal"}, 4).run()["reporters"]
    with pytest.raises(ValueError):
        Ethnocentrism(small(dispersal=1.5), seed=0)


def test_viscosity_judge():
    from ecological_models.ethnocentrism.utils import run_viscosity as rv
    rng = np.random.default_rng(1)
    hi = len(rv.DISPERSAL_LEVELS) - 1
    def runs(coop, founder, noise=0.01, meetings=1000):
        return [{"reporters": {rv.COOP: coop + noise * rng.standard_normal()}, "last100_meetings": meetings,
                 "lineage": [{"all_frac_same_founder": founder + noise * rng.standard_normal()}]} for _ in range(30)]
    cell = {("inherited", 0): runs(0.77, 0.75), ("random", 0): runs(0.76, 0.70),
            ("inherited", hi): runs(0.60, 0.10), ("random", hi): runs(0.30, 0.10)}
    v = rv.judge(cell, True)
    assert v["manipulation_ok"] and v["H1"]["met"] and v["H2"]["met"] and v["H2"]["verdict"] == "H2 met"
    bad = rv.judge(cell, False)
    assert bad["H1"]["verdict"].startswith("invalid: d=0") and not bad["H1"]["met"] and not bad["H2"]["met"]
    weak = {**cell, ("inherited", hi): runs(0.60, 0.65)}                     # founder share barely falls
    w = rv.judge(weak, True)
    assert w["H2"]["verdict"] == "invalid: manipulation check failed" and not w["H2"]["met"]
    # constant founder shares are a valid manipulation check (no test involved)
    const = {**cell, ("inherited", 0): runs(0.77, 0.75, noise=0.0), ("inherited", hi): runs(0.60, 0.10, noise=0.0)}
    assert rv.judge(const, True)["manipulation_ok"]
    nanf = {**cell, ("random", hi): [{**r, "lineage": [{"all_frac_same_founder": np.nan}]} for r in cell[("random", hi)]]}
    assert not rv.judge(nanf, True)["manipulation_ok"]
    same = {**cell, ("inherited", hi): runs(0.32, 0.10)}                     # no colour-rule difference at d=1
    assert rv.judge(same, True)["H2"]["verdict"] == "H2 not met"
    nomeet = {**cell, ("random", hi): runs(0.0, 0.10, meetings=0)}            # zero meetings: undefined, not 0%
    z = rv.judge(nomeet, True)
    assert z["H1"]["verdict"].startswith("invalid: endpoint") and z["H2"]["verdict"].startswith("invalid: endpoint")
    missing = {**cell, ("random", hi): [{"last100_meetings": 5}] * 30}       # keys missing -> invalid, no crash
    assert rv.judge(missing, True)["H1"]["verdict"].startswith("invalid")
    assert not rv.compare(np.full(30, 0.7), np.full(30, 0.3), 0.1, 30)["valid"]  # no standard error
    assert not rv.compare(np.full(29, 0.7), np.full(30, 0.3), 0.1, 30)["valid"]  # wrong count
    small_se = rv.compare(0.7 + 1e-9 * rng.standard_normal(30), np.full(30, 0.4), 0.1, 30)
    assert small_se["valid"] and small_se["criterion_met"]                   # tiny but real spread is valid
    nokey = {**cell, ("random", hi): [{"last100_meetings": 5, "lineage": r["lineage"]} for r in cell[("random", hi)]]}
    nk = rv.judge(nokey, True)                                               # endpoint key missing, lineage intact
    assert nk["manipulation_ok"] and nk["H1"]["verdict"].startswith("invalid: endpoint")
    edge = rv.compare(np.full(30, 0.5) + np.r_[0.01, -0.01, np.zeros(28)], np.full(30, 0.3), 0.2, 30)
    assert edge["criterion_met"]                                             # exact threshold passes


def test_fractional_dispersal_mixes_local_and_global():
    cfg = {**run_config("104"), "ticks": 200, "dispersal": 0.5}
    out = Ethnocentrism(cfg, 21).run()
    share = out["dispersed_total"] / out["offspring_total"]
    assert 0.45 < share < 0.75              # >= 0.5 of attempts; local attempts can be blocked, global rarely are
    m = Ethnocentrism(cfg, 21); m.run()
    immigrants = sum(p == EMPTY for p in m.parent)
    assert out["offspring_total"] + immigrants == out["births_total"] and 0 < immigrants <= 200


def test_viscosity_replay_check(tmp_path):
    from ecological_models.ethnocentrism.utils.run_viscosity import replays
    runs = [{"seed": s, "population": 10, "births_total": 5, "reporters": {"cd-percent": 0.5}} for s in range(2)]
    path = tmp_path / "r.csv"
    path.write_text("condition,seed,population,births_total,cd-percent\nrandom,0,10,5,0.5\nrandom,1,10,5,0.5\n"
                    "inherited,0,99,5,0.1\n")
    assert replays(runs, path, "condition", "random")
    assert not replays(runs, path, "condition", "inherited")
    for bad in ("random,1,11,5,0.5", "random,1,10,6,0.5", "random,1,10,5,0.50000001"):   # pop / births / reporter
        path.write_text("condition,seed,population,births_total,cd-percent\nrandom,0,10,5,0.5\n" + bad + "\n")
        assert not replays(runs, path, "condition", "random")


def test_skewed_random_colour():
    from ecological_models.ethnocentrism.config.ethnocentrism_config import SKEWED_COLOUR_WEIGHTS as W
    assert sum(W) == pytest.approx(1.0) and W[0] ** 2 + 3 * W[1] ** 2 == pytest.approx(0.80)
    m = Ethnocentrism(small(width=40, height=40, mutation_rate=0.0, colour_inheritance="random",
                            child_colour_weights=W), seed=16)
    for col in range(4):
        place(m, col, col, True, False)
    for target in range(4, 1600):
        m._hatch(target % 4, target)
    for col in range(4):                                               # independent of the parent's colour
        kids = np.arange(4, 1600)[np.arange(4, 1600) % 4 == col]
        assert 0.83 < (m.color[kids] == 0).mean() < 0.95
    assert {1, 2, 3} <= set(m.color[4:].tolist())
    with pytest.raises(ValueError):
        Ethnocentrism(small(colour_inheritance="random", child_colour_weights=[0.5, 0.5]), seed=0)
    with pytest.raises(ValueError):
        Ethnocentrism(small(child_colour_weights=W), seed=0)          # only with random colour
    z = Ethnocentrism(small(width=20, height=20, colour_inheritance="random", child_colour_weights=[0.5, 0.5, 0, 0],
                            mutation_rate=0.0), seed=17)
    place(z, 0, 0, True, False)
    for t in range(1, 400):
        z._hatch(0, t)
    assert set(z.color[1:].tolist()) == {0, 1}                        # zero-weight colours never drawn
    cfg = {**run_config("104"), "ticks": 150, "colour_inheritance": "random"}
    assert Ethnocentrism({**cfg, "child_colour_weights": None}, 5).run()["reporters"] == Ethnocentrism(
        {k: v for k, v in cfg.items() if k != "child_colour_weights"}, 5).run()["reporters"]


def test_confound_judge():
    from ecological_models.ethnocentrism.utils import run_confound as rc
    rng = np.random.default_rng(2)
    def arm(ethno, meetown, gap=0.0, meetings=1000, n=30):
        return [{"reporters": {rc.ETHNO: ethno + 0.02 * rng.standard_normal(), rc.MEETOWN: meetown},
                 "last100_meetings": meetings,
                 "lineage": [{"same_frac_same_founder": 0.7 + gap + 0.01 * rng.standard_normal(),
                              "diff_frac_same_founder": 0.7}]} for _ in range(n)]
    base = {"inherited": arm(0.75, 0.80), "random_uniform": arm(0.13, 0.25), "random_skewed": arm(0.40, 0.80)}
    v = rc.judge(base, True)
    assert v["manipulation_ok"] and v["H1"]["met"] and v["H2"]["met"]
    assert rc.judge({**base, "random_skewed": arm(0.40, 0.60)}, True)["H1"]["verdict"] == "invalid: manipulation check failed"
    assert rc.judge({**base, "random_skewed": arm(0.40, 0.80, gap=0.2)}, True)["H2"]["verdict"].startswith("invalid: manip")
    assert not rc.judge(base, False)["H1"]["met"]
    nomeet = rc.judge({**base, "random_skewed": arm(0.40, 0.80, meetings=0)}, True)
    assert nomeet["H1"]["verdict"].startswith("invalid")
    assert rc.judge({**base, "random_skewed": arm(0.40, 0.80, n=29)}, True)["H1"]["verdict"].startswith("invalid")
    nanmeet = rc.judge({**base, "random_skewed": arm(0.40, 0.80, meetings=float("nan"))}, True)
    assert nanmeet["H1"]["verdict"] == "invalid: manipulation check failed"      # meeting share undefined
    nan_eth = {**base, "inherited": [{**r, "reporters": {**r["reporters"], rc.ETHNO: np.nan}} for r in base["inherited"]]}
    assert rc.judge(nan_eth, True)["H1"]["verdict"].startswith("invalid: endpoint")
    flat = dict(base)
    for a in ("inherited", "random_skewed"):
        flat[a] = [{**r, "reporters": {**r["reporters"], rc.ETHNO: 0.5 if a == "inherited" else 0.3}} for r in base[a]]
    assert rc.judge(flat, True)["H1"]["verdict"].startswith("invalid: endpoint")         # no standard error
    assert rc.reporter({"reporters": {rc.ETHNO: 0.4}, "last100_meetings": 0}, rc.ETHNO) == 0.4   # strategy share defined
    v = rc.judge({**base, "random_skewed": arm(0.72, 0.80)}, True)
    assert v["H1"]["verdict"] == "H1 not met" and v["H2"]["verdict"] == "H2 met"


def test_confound_exposure():
    from ecological_models.ethnocentrism.utils.run_confound import exposure
    m = Ethnocentrism(small(), seed=0)
    place(m, 0, 0, True, False); place(m, 1, 0, False, False); place(m, 2, 1, True, False)   # row 0: E0 X0 E1
    e = exposure(m)
    # E0 (cell 0) has neighbour cell 1 (same colour); E1 (cell 2) has neighbour cell 1 (other colour): 1 of 2 own
    assert e["exp_ethno_own"] == pytest.approx(0.5)
    assert e["top_colour_share"] == pytest.approx(2 / 3)
    assert e["exp_top_colour_own"] == pytest.approx(2 / 3) and e["exp_other_colours_own"] == pytest.approx(0.0)


# ---------------------------------------------------------------- numba kernels: exact replay of committed runs
def test_fenwick_kth_matches_flatnonzero():
    from ecological_models.ethnocentrism.ethnocentrism_model import _fenwick_add, _fenwick_kth
    rng = np.random.default_rng(3)
    for n in (1, 2, 7, 64, 100):
        flags = rng.random(n) < 0.5
        tree = np.zeros(n + 1, dtype=np.int64)
        for c in np.flatnonzero(flags):
            _fenwick_add(tree, int(c), 1)
        while flags.any():
            idx = np.flatnonzero(flags)
            assert [_fenwick_kth(tree, k) for k in range(idx.size)] == idx.tolist()
            c = int(idx[rng.integers(idx.size)])
            flags[c] = False
            _fenwick_add(tree, c, -1)


def _same(csv_value: str, v) -> bool:
    x = float(csv_value)
    return (np.isnan(x) and np.isnan(v)) if (np.isnan(x) or (isinstance(v, float) and np.isnan(v))) else x == v


@pytest.mark.parametrize("which,job", [("viscosity", ("inherited", 2, 20000)),     # inherited colour, d = 0.5
                                       ("viscosity", ("random", 4, 41000)),        # random colour, d = 1
                                       ("confound", ("random_skewed", 3000))])     # weighted random colour
def test_numba_model_replays_committed_runs(which, job):
    """The compiled model must reproduce committed runs bit for bit (reporters, counts, final lineage sample)."""
    import csv
    from pathlib import Path
    from ecological_models.ethnocentrism.config.ethnocentrism_config import CONFOUND_DIR, VISC_DIR
    if which == "viscosity":
        from ecological_models.ethnocentrism.utils.run_viscosity import one
        d, key = Path(VISC_DIR), lambda row: row["condition"] == job[0] and int(row["seed"]) == job[2]
    else:
        from ecological_models.ethnocentrism.utils.run_confound import one
        d, key = Path(CONFOUND_DIR), lambda row: row["arm"] == job[0] and int(row["seed"]) == job[1]
    r = one(job)
    rows = [row for row in csv.DictReader(open(d / "runs.csv")) if key(row)]
    assert len(rows) == 1
    row = rows[0]
    assert int(row["population"]) == r["population"] and int(row["births_total"]) == r["births_total"]
    assert all(float(row[k]) == v for k, v in r["reporters"].items())
    lin = [row for row in csv.DictReader(open(d / "lineage.csv")) if key(row)]
    assert len(lin) == len(r["lineage"])
    last = lin[-1]
    assert all(_same(last[k], v) for k, v in r["lineage"][-1].items())


def _state(m):
    return (m.agent.tobytes(), m.color.tobytes(), m.cs.tobytes(), m.cd.tobytes(), m.ptr.tobytes(),
            m.rng.bit_generator.state, m.parent, m.founder, m.birth, m.n_dispersed, dict(m.turn), dict(m.agg))


def _lineage_equal(a, b):
    return a.keys() == b.keys() and all(
        (isinstance(a[k], float) and np.isnan(a[k]) and np.isnan(b[k])) or
        (np.asarray(a[k]).tobytes() == np.asarray(b[k]).tobytes() and type(a[k]) is type(b[k])) for k in a)


@pytest.mark.parametrize("colour", [{}, {"colour_inheritance": "random"},
                                    {"colour_inheritance": "random", "child_colour_weights": [0.7, 0.1, 0.1, 0.1]}])
@pytest.mark.parametrize("dispersal", [0.0, 0.3, 1.0])
def test_numba_model_matches_frozen_pure_python_every_tick(colour, dispersal):
    """Arrays (as bytes, so signed zeros count), Generator state, pedigree and lineage after every tick."""
    from ecological_models.ethnocentrism.tests.reference_model_pure_python import Ethnocentrism as Reference
    cfg = {**BASE, "width": 9, "height": 7, "ticks": 120, "lineage_sample_every": 30, "immigrants_per_day": 3,
           "mutation_rate": 0.05, "dispersal": dispersal, **colour}
    a, b = Reference(cfg, 11), Ethnocentrism(cfg, 11)
    b.ped = np.zeros((4, 2), dtype=np.int64)                          # force pedigree growth many times
    while a.tick < cfg["ticks"]:
        a.step(); b.step()
        assert _state(a) == _state(b), f"diverged at tick {a.tick}"
    assert len(a.lineage_samples) == len(b.lineage_samples)
    assert all(_lineage_equal(x, y) for x, y in zip(a.lineage_samples, b.lineage_samples))
    ra, rb = a.run(), b.run()                                         # new keys added; old ones unchanged
    assert all(k in rb and (k == "lineage" or ra[k] == rb[k]) for k in ra)


def test_numba_hatch_edge_cases_match_frozen_pure_python():
    """Hatching from an empty parent cell, and dispersal on a full grid (no vacancy), as the old code did."""
    from ecological_models.ethnocentrism.tests.reference_model_pure_python import Ethnocentrism as Reference
    a, b = Reference(small(setup="full", dispersal=1.0), 5), Ethnocentrism(small(setup="full", dispersal=1.0), 5)
    a.step(); b.step()                                                # grid starts full: dispersal finds no cell
    assert _state(a) == _state(b)
    for m in (a, b):
        m.agent[3] = EMPTY
        m._hatch(3, 4)                                                # empty parent: child is its own founder
    assert _state(a) == _state(b)


def test_n_colors_validation():
    for n in (129, 256):
        for setup in ("empty", "full"):                               # validated before agents are created
            with pytest.raises(ValueError):
                Ethnocentrism(small(n_colors=n, setup=setup), 0)
    Ethnocentrism(small(n_colors=128, setup="full"), 0).run()        # ids 0..127 fit int8, as before
    with pytest.raises(ValueError):
        Ethnocentrism(small(n_colors=4.0), 0)
    with pytest.raises(ValueError):
        Ethnocentrism(small(n_colors=1), 0)                         # inherited colour with mutation
    Ethnocentrism(small(n_colors=1, mutation_rate=0.0), 0).run()     # one colour, no mutation: allowed, as before


# ---------------------------------------------------------------- shuffle experiment
def _agents(m):
    occ = np.flatnonzero(m.agent != EMPTY)
    return occ, sorted(zip(m.agent[occ].tolist(), m.color[occ].tolist(), m.cs[occ].tolist(), m.cd[occ].tolist(),
                           m.ptr[occ].tolist()))


def test_shuffle_keeps_cells_and_agents_and_moves_attributes_together():
    m = Ethnocentrism(small(setup="full", shuffle_fraction=1.0, n_colors=4), 3)
    m.ptr[:] = np.arange(m.N) / 100                                    # distinct PTR per agent
    occ0, agents0 = _agents(m)
    ids0 = m.agent.copy()
    m._shuffle()
    occ1, agents1 = _agents(m)
    assert occ0.tolist() == occ1.tolist() and agents0 == agents1      # same cells, same agents with their attributes
    assert (m.agent != ids0).any()                                     # and they moved
    m2 = Ethnocentrism(small(shuffle_fraction=0.5), 3)
    for c in (0, 6, 12, 18):
        place(m2, c, c % 4, True, False)
    occ0, agents0 = _agents(m2)
    m2._shuffle()                                                      # partial shuffle on a sparse grid
    occ1, agents1 = _agents(m2)
    assert occ1.tolist() == occ0.tolist() and agents1 == agents0


def test_shuffle_fraction_zero_makes_no_draws():
    cfg = small(ticks=30, immigrants_per_day=3)
    a = Ethnocentrism({k: v for k, v in cfg.items() if k != "shuffle_fraction"}, 4)
    b = Ethnocentrism({**cfg, "shuffle_fraction": 0.0}, 4)
    a.run(); b.run()
    assert a.rng.bit_generator.state == b.rng.bit_generator.state and (a.agent == b.agent).all()
    c = Ethnocentrism({**cfg, "shuffle_fraction": 0.5}, 4)
    c.run()
    assert c.rng.bit_generator.state != a.rng.bit_generator.state
    for bad in (-0.1, 1.5):
        with pytest.raises(ValueError):
            Ethnocentrism(small(shuffle_fraction=bad), 0)


def test_interaction_kinship_counts_pairs_and_random_mixing_baseline():
    m = Ethnocentrism(small(), 0)
    place(m, 0, 0, True, False)                                        # founder X
    m.agent[1] = m._new_id(int(m.agent[0]))                            # X's child, right of it
    place(m, 2, 0, True, False)                                        # founder Y, right of the child
    m._interaction_kinship()
    k = m.ikin
    assert k["pairs"] == 2 and k["same_founder"] == 1 and k["ticks_with_pairs"] == 1
    assert k["expected_weighted"] == pytest.approx(2 * (2 * 1) / (3 * 2))   # founders 2 + 1 agents: 1/3 per pair


def test_meetings_by_code_add_up():
    m = Ethnocentrism({**BASE, "width": 9, "height": 9, "ticks": 150, "lineage_sample_every": 0,
                       "immigrants_per_day": 5}, 2)
    r = m.run()
    by = np.array(r["last100_meetings_by_code"])
    assert by[:, 0].sum() == sum(m.win["meet"]) and by[:, 1].sum() == sum(m.win["meetown"])
    assert r["last100_agent_ticks"] == sum(sum(m.win[c]) for c in ("cc", "cd", "dc", "dd"))
    assert m.ikin["ticks"] == 100


def _shuffle_run(cell, seed, coop=0.7, dd=0.1, excess=0.6, meetings=100, agent_ticks=100000):
    k = {"pairs": 1000, "same_founder": int(round(1000 * (excess + 0.05))), "expected_weighted": 50.0,
         "ticks_with_pairs": 100, "ticks": 100}
    return {"cell": cell, "seed": seed, "reporters": {"last100coop-percent": coop, "dd-percent": dd},
            "last100_meetings": meetings, "last100_agent_ticks": agent_ticks,
            "last100_egoist_ticks": int(round(dd * agent_ticks)), "interaction_kinship": k}


def _shuffle_cells(r1_coop=0.1, r1_dd=0.8, r1_excess=0.0, **over):
    rng = np.random.default_rng(0)
    cells = {"R0": [_shuffle_run("R0", i, coop=0.75 + 0.01 * rng.standard_normal(), dd=0.08 + 0.01 * rng.standard_normal())
                    for i in range(30)],
             "R1": [_shuffle_run("R1", i, coop=r1_coop + 0.01 * rng.standard_normal(),
                                 dd=r1_dd + 0.01 * rng.standard_normal(), excess=r1_excess, **over) for i in range(30)]}
    return cells


def test_shuffle_judge():
    from ecological_models.ethnocentrism.utils.run_shuffle import excess_of, judge
    j = judge(_shuffle_cells(), True, True)
    assert j["manipulation"]["ok"] and j["H1"]["verdict"] == "H1 met" and j["H2"]["verdict"] == "H2 met"
    assert j["manipulation"]["drop"] == pytest.approx(0.6)
    j = judge(_shuffle_cells(r1_coop=0.7, r1_dd=0.1), True, True)        # no effect
    assert j["H1"]["verdict"] == "H1 not met" and not j["H1"]["met"] and j["H2"]["verdict"] == "H2 not met"
    assert judge(_shuffle_cells(), False, True)["H1"]["verdict"].startswith("invalid: missing")
    assert judge(_shuffle_cells(), True, False)["H2"]["verdict"].startswith("invalid: f = 0")
    j = judge(_shuffle_cells(r1_excess=0.45), True, True)                 # excess drop 0.15 < 0.20
    assert j["H1"]["verdict"] == "invalid: manipulation check failed" and not j["H1"]["met"]
    cells = _shuffle_cells()
    cells["R1"][0]["interaction_kinship"]["ticks_with_pairs"] = 99      # a run without 100 measured ticks
    assert excess_of(cells["R1"][0]) != excess_of(cells["R1"][0])        # NaN
    assert judge(cells, True, True)["H1"]["verdict"] == "invalid: manipulation check undefined"
    cells = _shuffle_cells()
    cells["R1"][3]["last100_meetings"] = 0                               # cooperation undefined -> H1 invalid
    j = judge(cells, True, True)
    assert j["H1"]["verdict"].startswith("invalid: endpoint") and j["H2"]["verdict"] == "H2 met"
    cells = _shuffle_cells()
    cells["R0"][5]["last100_agent_ticks"] = 0                            # egoist share undefined -> H2 invalid
    assert judge(cells, True, True)["H2"]["verdict"].startswith("invalid: endpoint")
    cells = _shuffle_cells()
    cells["R1"][2]["reporters"]["last100coop-percent"] = float("nan")   # non-finite endpoint -> that test invalid
    j = judge(cells, True, True)
    assert j["H1"]["verdict"].startswith("invalid: endpoint") and j["H2"]["verdict"] == "H2 met"
    cells = _shuffle_cells()
    cells["R1"].pop()                                                    # wrong number of runs
    assert judge(cells, True, True)["H1"]["verdict"].startswith("invalid")
    cells = _shuffle_cells()
    del cells["R1"][0]["interaction_kinship"]["same_founder"]           # malformed record: no crash, invalid
    assert judge(cells, False, False)["H1"]["verdict"].startswith("invalid: missing")


def test_shuffle_compare_boundaries():
    from ecological_models.ethnocentrism.utils.run_shuffle import compare
    a = 0.7 + 0.01 * np.random.default_rng(1).standard_normal(30)
    assert compare(a, a - 0.20, 0.20)["criterion_met"]                   # exactly the minimum (float tolerance)
    assert not compare(a, a - 0.199, 0.20)["criterion_met"]
    assert not compare(np.full(30, 0.5), np.full(30, 0.2), 0.20)["valid"]   # no standard error
    b = a - 0.20 + 0.3 * np.random.default_rng(2).standard_normal(30)    # large spread: p above 0.001
    c = compare(a, b, 0.0)
    assert c["valid"] and (c["p"] < 0.001) == c["criterion_met"]


def test_shuffle_egoist_ratio_uses_raw_counts():
    from ecological_models.ethnocentrism.utils.run_shuffle import egoist_of
    r = {"reporters": {"dd-percent": 0.99}, "last100_agent_ticks": 99, "last100_egoist_ticks": 99}
    assert egoist_of(r) == 1.0
    assert egoist_of({**r, "last100_agent_ticks": 0}) != egoist_of({**r, "last100_agent_ticks": 0})   # NaN


def test_shuffle_meeting_mix_with_absent_strategies():
    from ecological_models.ethnocentrism.utils.run_shuffle import meeting_mix
    by = [[0, 0], [0, 0], [0, 0], [40, 10]]                              # only altruists (code 3) meet
    mm = meeting_mix([{"last100_meetings_by_code": by}])
    assert mm["help_rate_implied"]["mean"] == 1.0 and mm["meeting_share_altruist"]["mean"] == 1.0


def _full_record(cell, seed):
    from ecological_models.ethnocentrism.config.ethnocentrism_config import SHUFFLE_CELLS
    from ecological_models.ethnocentrism.utils import run_shuffle as rs
    colour, f, _ = SHUFFLE_CELLS[cell]
    return {"cell": cell, "colour": colour, "shuffle_fraction": f, "seed": seed, "reporters": {"a": 0.5},
            "lineage": [{"tick": t, **{k: 0.0 for k in rs.DESCRIBE_LINEAGE}} for t in range(100, rs.TICKS + 1, 100)],
            "interaction_kinship": {"pairs": 100, "same_founder": 50, "expected_weighted": 10.0,
                                    "ticks_with_pairs": 100, "ticks": 100},
            "last100_meetings_by_code": [[100, 0], [0, 0], [0, 0], [100, 50]], "population": 1, "births_total": 1,
            "offspring_total": 0, "dispersed_total": 0, "last100_meetings": 200, "last100_agent_ticks": 1,
            "last100_egoist_ticks": 0}


def test_shuffle_batch_ok():
    import copy
    from ecological_models.ethnocentrism.config.ethnocentrism_config import SHUFFLE_CELLS
    from ecological_models.ethnocentrism.utils import run_shuffle as rs
    keys = {"a"}
    res = [_full_record(c, s) for c, (_, _, seeds) in SHUFFLE_CELLS.items() for s in seeds]
    assert rs.batch_ok(res, keys)
    assert not rs.batch_ok(res, set())                                   # no reporter set: fails closed
    assert not rs.batch_ok(res[:-1], keys)                               # missing
    assert not rs.batch_ok(res + [res[0]], keys)                         # duplicate
    assert not rs.batch_ok(res[:-1] + [{"cell": res[-1]["cell"], "seed": res[-1]["seed"], "error": "x"}], keys)
    def broken(fn):
        bad = copy.deepcopy(res); fn(bad[7]); return rs.batch_ok(bad, keys)
    assert not broken(lambda r: r["lineage"].pop())                      # missing lineage sample
    assert not broken(lambda r: r["lineage"][3].pop("all_r_reg_cs"))     # missing lineage field
    assert not broken(lambda r: r.pop("offspring_total"))               # missing count
    assert not broken(lambda r: r["interaction_kinship"].pop("pairs"))
    assert not broken(lambda r: r["interaction_kinship"].update(same_founder=101))  # more same-founder than pairs
    assert not broken(lambda r: r.update(last100_meetings=3))            # meetings by code do not add up
    assert not broken(lambda r: r["interaction_kinship"].update(pairs=99, same_founder=49))   # meetings != 2 * pairs
    assert not broken(lambda r: r["interaction_kinship"].update(ticks_with_pairs=101))
    assert not broken(lambda r: r["lineage"][2].update(population="x"))  # non-numeric lineage value
    assert not broken(lambda r: r.update(interaction_kinship=[1, 2]))    # wrong type
    assert not broken(lambda r: r.update(shuffle_fraction=0.3))          # wrong treatment metadata
    assert not broken(lambda r: r["reporters"].pop("a"))
    assert broken(lambda r: r["reporters"].update(a=float("nan")))      # non-finite endpoint: judged per test


def test_shuffle_validate_replay_files(tmp_path):
    from ecological_models.ethnocentrism.utils import run_shuffle as rs
    missing = tmp_path / "missing.csv"
    empty = tmp_path / "empty.csv"; empty.write_text("")
    import csv as _csv
    from ecological_models.ethnocentrism.config.ethnocentrism_config import SHUFFLE_CELLS
    res = [_full_record(c, s) for c, (_, _, seeds) in SHUFFLE_CELLS.items() for s in seeds]
    good_r = tmp_path / "random.csv"; good_p = tmp_path / "port.csv"
    with open(good_r, "w", newline="") as f:
        w = _csv.writer(f); w.writerow(["condition", "seed", "population", "births_total", "a"])
        for s in SHUFFLE_CELLS["R0"][2]:
            w.writerow(["random", s, 1, 1, 0.5])
    with open(good_p, "w", newline="") as f:
        w = _csv.writer(f); w.writerow(["experiment", "seed", "population", "births_total", "a"])
        for s in SHUFFLE_CELLS["I0"][2]:
            w.writerow(["104", s, 1, 1, 0.5])
    assert rs.validate(res, good_r, good_p) == (True, True)
    for r in (missing, empty):                                           # either replay file missing or empty
        assert rs.validate(res, r, good_p) == (False, False) and rs.validate(res, good_r, r) == (False, False)
    dup = tmp_path / "dup.csv"
    dup.write_text(good_r.read_text().replace("births_total,a", "births_total,a,a", 1))
    assert rs.validate(res, dup, good_p) == (False, False)               # duplicate column
    changed = tmp_path / "changed.csv"
    changed.write_text(good_r.read_text().replace(",0.5\n", ",0.25\n", 1))
    assert rs.validate(res, changed, good_p) == (True, False)            # a value differs: no replay


def test_shuffle_draw_sequence_is_as_registered():
    for setup, cells in (("full", None), ("empty", []), ("empty", [7])):  # many, zero and one occupied cells
        m = Ethnocentrism(small(setup=setup, shuffle_fraction=0.5), 8)
        for c in cells or []:
            place(m, c, 1, True, True)
        g = np.random.default_rng(); g.bit_generator.state = m.rng.bit_generator.state
        before = m.agent.copy()
        occ = np.flatnonzero(before != EMPTY)
        sel = occ[g.random(occ.size) < 0.5]
        expect = before.copy(); expect[sel] = before[sel[g.permutation(sel.size)]]
        m._shuffle()
        assert (m.agent == expect).all() and m.rng.bit_generator.state == g.bit_generator.state


def test_interaction_kinship_pools_ticks_by_pairs():
    m = Ethnocentrism(small(), 0)
    place(m, 0, 0, True, False); m.agent[1] = m._new_id(int(m.agent[0]))      # tick 1: one pair, same founder
    m._interaction_kinship()
    place(m, 12, 0, True, False); place(m, 13, 0, True, False)                # tick 2: two pairs (0-1, 12-13)
    m._interaction_kinship()
    k = m.ikin
    assert k["pairs"] == 3 and k["same_founder"] == 2 and k["ticks_with_pairs"] == 2 and k["ticks"] == 2
    # tick 1: founders {X: 2} -> expected 1, one pair; tick 2: {X: 2, Y: 1, Z: 1} -> 2/12 per pair, two pairs
    assert k["expected_weighted"] == pytest.approx(1 * 1 + 2 * (2 / 12))


# ---------------------------------------------------------------- Hamilton's-rule prediction test
def test_relatedness_cs_within_tick_regression():
    m = Ethnocentrism(small(n_colors=1, colour_inheritance="random"), 0)
    for c, cs in ((0, True), (1, True), (2, False), (12, False)):      # row 0: H H N ; cell 12 isolated
        place(m, c, 0, cs, False)
    m._relatedness_cs()
    # directed pairs: 0->1 (1,1), 1->0 (1,1), 1->2 (1,0), 2->1 (0,1): n 4, sx 3, sy 3, sxy 2
    k = m.rkin
    assert k["pairs"] == 4 and k["ticks_with_pairs"] == 1 and k["ticks"] == 1
    assert k["sum_ncov"] == pytest.approx(2 - 3 * 3 / 4) and k["sum_nvar"] == pytest.approx(3 - 9 / 4)
    from ecological_models.ethnocentrism.utils.run_hamilton import r_of
    x = np.array([1, 1, 1, 0]); y = np.array([1, 1, 0, 1])
    assert r_of({"relatedness_cs": k}) == pytest.approx(np.cov(x, y, bias=True)[0, 1] / x.var())
    m2 = Ethnocentrism(small(), 0)
    m2._relatedness_cs()                                               # no pairs: tick counted, zero weight
    assert m2.rkin["ticks"] == 1 and m2.rkin["ticks_with_pairs"] == 0 and m2.rkin["sum_nvar"] == 0


def test_relatedness_window_and_one_colour_model():
    cfg = {**BASE, "width": 9, "height": 9, "ticks": 60, "lineage_sample_every": 0, "immigrants_per_day": 5,
           "n_colors": 1, "colour_inheritance": "random", "relatedness_window": (20, 50)}
    m = Ethnocentrism(cfg, 1)
    r = m.run()
    assert r["relatedness_cs"]["ticks"] == 30
    assert (m.color == 0).all() and r["reporters"]["last100meetown-percent"] == 1.0   # every meeting own colour
    assert r["last100_helper_ticks"] == sum(m.win["cc"]) + sum(m.win["cd"])
    assert Ethnocentrism({**cfg, "relatedness_window": None}, 1).run()["relatedness_cs"]["ticks"] == 0
    a = Ethnocentrism({**cfg, "relatedness_window": None}, 1); a.run()          # measurement makes no draws
    assert a.rng.bit_generator.state == m.rng.bit_generator.state


def test_hamilton_feasibility_rule():
    from ecological_models.ethnocentrism.utils import run_hamilton as rh
    cut = 2 * rh.HAM_C / rh.HAM_B_CAP
    h = {l: [0.5] * rh.HAM_N for l in range(4)}
    f = rh.feasibility({0: [0.6] * 60, 1: [0.3] * 60, 2: [cut * 1.000001] * 60, 3: [cut * 0.999] * 60}, h)
    assert f["kept"] == [0, 1, 2] and f["feasible"]                    # just above the cut kept, just below not
    f = rh.feasibility({0: [0.6] * 60, 1: [0.3] * 59 + [float("nan")], 2: [0.2] * 60, 3: [-0.1] * 60}, h)
    assert f["kept"] == [0, 2] and not f["feasible"]                   # NaN r and r <= 0 dropped; < 3 kept
    f = rh.feasibility({l: [0.5] * 60 for l in range(4)}, {**h, 1: [0.5] * 59 + [float("nan")]})
    assert f["kept"] == [0, 2, 3]                                      # undefined neutral helper share: dropped
    man = rh.manifest_from(rh.feasibility({0: [0.6] * 60, 1: [0.3] * 60, 2: [0.2] * 60, 3: [0.01] * 60}, h))
    assert man["kept_levels"] == [0, 1, 2] and len(man["cells"]) == 12
    c = man["cells"][3]
    assert c["level"] == 0 and c["k"] == 3 and c["b"] == pytest.approx(2.0 * rh.HAM_C / 0.6)
    assert c["seeds"] == [200000 + 3000 + i for i in range(60)]


def _ham_record(stage, level, k, seed, settings, helper=4, agents=10, ncov=0.5, nvar=1.0):
    return {"stage": stage, "level": level, "k": k, "seed": seed, "settings": settings, "reporters": {"a": 0.1},
            "population": 3, "births_total": 3, "offspring_total": 1, "last100_agent_ticks": agents,
            "last100_helper_ticks": helper, "relatedness_cs": {"pairs": 2000, "sum_ncov": ncov, "sum_nvar": nvar,
                                                               "ticks_with_pairs": 900, "ticks": 1000}}


def _write_stage0(tmp_path, records, **summary):
    import json as _json
    (tmp_path / "stage0_records.json").write_text(_json.dumps(records))
    (tmp_path / "stage0_summary.json").write_text(_json.dumps({"status": "valid", "replay_ok": True,
                                                               "batch_ok": True, **summary}))


def test_hamilton_stage1_rederives_manifest_from_raw_stage0(tmp_path):
    import json as _json
    from ecological_models.ethnocentrism.utils import run_hamilton as rh
    recs = [_ham_record(0, l, None, s, rh.settings(l, 0.0, 0.0), ncov=0.5 - 0.1 * l)
            for l in range(4) for s in rh.ham_seeds(0, l)]
    _write_stage0(tmp_path, recs)
    derived = rh.stage0_from_records(tmp_path, {"a"})
    assert derived is not None
    man, neutral = derived
    assert man["kept_levels"] == [0, 1, 2, 3] and neutral[0].shape == (60,)       # r 0.5, 0.4, 0.3, 0.2: all kept
    assert man["r"]["0"] == 0.5 and man["cells"][0]["b"] == pytest.approx(0.5 * rh.HAM_C / 0.5)
    assert rh.stage0_from_records(tmp_path, set()) is None                       # no reporter set
    _write_stage0(tmp_path, recs, replay_ok=False)
    assert rh.stage0_from_records(tmp_path, {"a"}) is None                       # replay failed
    _write_stage0(tmp_path, [r for r in recs if r["level"] != 3])
    assert rh.stage0_from_records(tmp_path, {"a"}) is None                       # a whole dropped level missing
    bad = _json.loads(_json.dumps(recs)); bad[5]["relatedness_cs"]["pairs"] = -2
    _write_stage0(tmp_path, bad)
    assert rh.stage0_from_records(tmp_path, {"a"}) is None                       # impossible record
    (tmp_path / "stage0_records.json").unlink()
    assert rh.stage0_from_records(tmp_path, {"a"}) is None


def test_hamilton_refuses_rerun_and_replays_before_dispatch(tmp_path, monkeypatch):
    from ecological_models.ethnocentrism.utils import run_hamilton as rh
    class FakePool:
        def __init__(self, *a): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def map(self, fn, it, chunksize=1):
            assert fn is not rh.one, "registered runs dispatched after a failed replay"
            return [{"seed": s, "error": "x"} for s in it]
    monkeypatch.setattr(rh, "Pool", FakePool)
    s = rh.stage0(tmp_path, 1)
    assert s["status"] == "invalid" and not s["replay_ok"]
    with pytest.raises(SystemExit):
        rh.stage0(tmp_path, 1)                                                   # second batch refused
    (tmp_path / "stage1_summary.json").write_text("{}")
    with pytest.raises(SystemExit):
        rh.stage1(tmp_path, 1)


def test_hamilton_inclusive_cap_and_kstar_without_welch():
    from ecological_models.ethnocentrism.utils import run_hamilton as rh
    cut = 2 * rh.HAM_C / rh.HAM_B_CAP
    h = {l: [0.5] * rh.HAM_N for l in range(4)}
    f = rh.feasibility({l: [cut] * 60 for l in range(4)}, h)
    assert f["kept"] == [0, 1, 2, 3]                                             # every input exactly at the cap
    neutral = {0: np.full(60, 0.5)}
    cells = {(0, ki): np.full(60, 0.5 + d) for ki, d in enumerate([-0.2, -0.1, 0.1, 0.2])}
    j = rh.judge(cells, neutral, [0], True)                                      # constant: Welch invalid
    assert j["H1"]["verdict"] == "invalid" and j["k_star"]["0"] == pytest.approx(1.0, rel=1e-9)


def test_relatedness_cs_pools_ticks_with_unequal_pairs():
    m = Ethnocentrism(small(n_colors=1, colour_inheritance="random"), 0)
    place(m, 0, 0, True, False); place(m, 1, 0, True, False)                    # tick A: H-H (2 directed pairs)
    m._relatedness_cs()
    place(m, 2, 0, False, False); place(m, 12, 0, False, False); place(m, 13, 0, True, False)   # tick B
    m._relatedness_cs()
    # tick B directed pairs: 0<->1 (1,1)x2, 1<->2 (1,0),(0,1), 12<->13 (0,1),(1,0): n 6, sx 4, sxy 2
    k = m.rkin
    assert k["pairs"] == 8 and k["ticks_with_pairs"] == 2
    assert k["sum_ncov"] == pytest.approx((2 - 2 * 2 / 2) + (2 - 4 * 4 / 6))
    assert k["sum_nvar"] == pytest.approx((2 - 4 / 2) + (4 - 16 / 6))
    cfg = {**BASE, "width": 7, "height": 7, "ticks": 10, "lineage_sample_every": 0, "n_colors": 1,
           "colour_inheritance": "random", "immigrants_per_day": 5, "relatedness_window": (3, 7)}
    seen = []
    mm = Ethnocentrism(cfg, 2)
    orig = mm._relatedness_cs
    mm._relatedness_cs = lambda: (seen.append(mm.tick), orig())
    mm.run()
    assert seen == [3, 4, 5, 6]                                                  # tick counter 3..6, window end open


def test_hamilton_classify_hypothesis_kstar():
    from ecological_models.ethnocentrism.utils import run_hamilton as rh
    g = np.random.default_rng(0)
    neut = 0.5 + 0.02 * g.standard_normal(60)
    up, down, same = neut + 0.1, neut - 0.1, 0.5 + 0.02 * g.standard_normal(60)
    assert rh.classify(up, neut, 2.0)["class"] == "correct" and rh.classify(down, neut, 0.5)["class"] == "correct"
    assert rh.classify(down, neut, 2.0)["class"] == "wrong" and rh.classify(up, neut, 0.8)["class"] == "wrong"
    assert rh.classify(same, neut, 1.25)["class"] == "unclear"
    assert rh.classify(up[:59], neut, 2.0)["class"] == "invalid"
    assert rh.classify(np.full(60, 0.5), np.full(60, 0.5), 2.0)["class"] == "invalid"   # no standard error
    bad = up.copy(); bad[0] = np.nan
    assert rh.classify(bad, neut, 2.0)["class"] == "invalid"
    assert rh.hypothesis(["correct"] * 6, True) == "met"
    assert rh.hypothesis(["correct", "unclear"], True) == "inconclusive"
    assert rh.hypothesis(["correct", "wrong", "unclear"], True) == "not met: reversal"
    assert rh.hypothesis(["wrong", "invalid"], True) == "invalid" and rh.hypothesis(["correct"], False) == "invalid"
    assert rh.hypothesis([], True) == "invalid"
    lk = np.log(rh.HAM_K)
    k = rh.k_star([-0.2, -0.1, 0.1, 0.3])
    assert k == pytest.approx(math.exp(lk[1] + 0.5 * (lk[2] - lk[1])))
    assert rh.k_star([-0.2, 0.0, 0.1, 0.3]) == 0.8
    for bad in ([-0.2, -0.1, -0.05, -0.01], [0.1, -0.1, 0.1, 0.2], [-0.1, 0.1, -0.1, 0.1], [0.0, 0.1, 0.2, 0.3],
                [-0.1, 0.0, 0.0, 0.1], [0.1, 0.05, -0.1, -0.2], [-0.1, float("nan"), 0.1, 0.2]):
        assert math.isnan(rh.k_star(bad)), bad


def test_hamilton_judge_and_batch():
    from ecological_models.ethnocentrism.utils import run_hamilton as rh
    g = np.random.default_rng(1)
    neutral = {l: 0.5 + 0.02 * g.standard_normal(60) for l in range(3)}
    shift = {0: -0.1, 1: -0.05, 2: 0.05, 3: 0.1}
    cells = {(l, ki): neutral[l] + shift[ki] + 0.001 * g.standard_normal(60) for l in range(3) for ki in range(4)}
    j = rh.judge(cells, neutral, [0, 1, 2], True)
    assert j["H1"]["verdict"] == "met" and j["H2"]["verdict"] == "met" and j["H1"]["n_correct"] == 6
    assert j["k_star"]["0"] == pytest.approx(1.0, abs=0.05)
    assert rh.judge(cells, neutral, [0, 1, 2], False)["H1"]["verdict"] == "invalid"
    cells2 = dict(cells); cells2[(1, 0)] = neutral[1] + 0.1                 # k = 0.5 cell goes up: reversal
    assert rh.judge(cells2, neutral, [0, 1, 2], True)["H1"]["verdict"] == "not met: reversal"
    cells3 = dict(cells); del cells3[(2, 3)]
    assert rh.judge(cells3, neutral, [0, 1, 2], True)["H1"]["verdict"] == "invalid"
    # batch / well-formed
    st = rh.settings(1, 0.0, 0.0)
    rec = _ham_record(0, 1, None, 5, st)
    exp = {(0, 1, None, 5): st}
    assert rh.batch_ok([rec], exp, {"a"})
    assert not rh.batch_ok([rec, rec], exp, {"a"}) and not rh.batch_ok([], exp, {"a"})
    assert not rh.batch_ok([{**rec, "settings": rh.settings(1, 0.01, 0.0)}], exp, {"a"})   # wrong benefit
    assert not rh.batch_ok([{**rec, "last100_helper_ticks": 11}], exp, {"a"})
    assert not rh.batch_ok([{**rec, "relatedness_cs": {**rec["relatedness_cs"], "ticks": 999}}], exp, {"a"})
    assert not rh.batch_ok([{**rec, "error": "x"}], exp, {"a"}) and not rh.batch_ok([rec], exp, set())
    for bad in ({"pairs": -2}, {"pairs": 1001}, {"pairs": 1000, "ticks_with_pairs": 900}, {"sum_ncov": 1.5}):
        assert not rh.batch_ok([{**rec, "relatedness_cs": {**rec["relatedness_cs"], **bad}}], exp, {"a"}), bad
    assert not rh.batch_ok([{**rec, "offspring_total": 4}], exp, {"a"})       # more offspring than births
    assert not rh.batch_ok([{**rec, "k": -1}], exp, {"a"})                       # stage-0 key with a k value


def test_hamilton_strict_records_exact_boundary_and_reservation(tmp_path):
    from ecological_models.ethnocentrism.utils import run_hamilton as rh
    st = rh.settings(1, 0.0, 0.0)
    rec = _ham_record(0, 1, None, 5, st)
    exp = {(0, 1, None, 5): st}
    zero = {"pairs": 0, "ticks_with_pairs": 0, "sum_ncov": 0.5, "sum_nvar": 1.0, "ticks": 1000}
    assert not rh.batch_ok([{**rec, "relatedness_cs": zero}], exp, {"a"})       # no pairs but variance
    assert rh.batch_ok([{**rec, "relatedness_cs": {**zero, "sum_ncov": 0.0, "sum_nvar": 0.0}}], exp, {"a"})
    assert not rh.batch_ok([{**rec, "level": True}], {(0, True, None, 5): st}, {"a"})   # bool id
    assert not rh.batch_ok([{**rec, "seed": 5.0}], {(0, 1, None, 5.0): st}, {"a"})      # float seed
    assert not rh.batch_ok([{**rec, "reporters": {"a": float("inf")}}], exp, {"a"})    # non-finite reporter
    assert not rh.batch_ok([{**rec, "relatedness_cs": {**rec["relatedness_cs"], "sum_nvar": 501.0}}], exp, {"a"})
    big = {**rec, "last100_agent_ticks": 200, "last100_helper_ticks": 50,
           "reporters": {"a": 0.1, "cc-percent": 0.1, "cd-percent": 0.15}}
    assert rh.batch_ok([big], exp, {"a", "cc-percent", "cd-percent"})            # 0.25 = 50 / 200
    assert not rh.batch_ok([{**big, "last100_helper_ticks": 60}], exp, {"a", "cc-percent", "cd-percent"})
    # exact boundary from raw sums: ncov 1, nvar 24 -> r = 1/24 -> b at k = 2 is exactly the 0.12 cap
    recs = [_ham_record(0, l, None, s, rh.settings(l, 0.0, 0.0), ncov=1.0, nvar=24.0)
            for l in range(4) for s in rh.ham_seeds(0, l)]
    _, r_values, h_values = rh.neutral_values(recs)
    assert rh.feasibility(r_values, h_values)["kept"] == [0, 1, 2, 3]
    man = rh.manifest_from(rh.feasibility(r_values, h_values))
    assert max(c["b"] for c in man["cells"]) == rh.HAM_B_CAP                     # exactly the cap, not above
    recs2 = [_ham_record(0, l, None, s, rh.settings(l, 0.0, 0.0), ncov=1.0, nvar=24.000001)
             for l in range(4) for s in rh.ham_seeds(0, l)]
    assert rh.feasibility(*rh.neutral_values(recs2)[1:])["kept"] == []          # just below: dropped
    # reservation: a leftover marker refuses the stage, and reserve() is exclusive
    rh.reserve(tmp_path / "stage1_summary.json")
    with pytest.raises(SystemExit):
        rh.reserve(tmp_path / "stage1_summary.json")
    with pytest.raises(SystemExit):
        rh.stage1(tmp_path, 1)
