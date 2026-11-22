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
