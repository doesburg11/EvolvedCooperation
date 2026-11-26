import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3a import model as m3a
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3b import model, run


def _play(n_disc, n, q, o, e, a, arm=0, seed=0, k=10):
    model._seed(seed)
    is_disc = np.zeros(n, dtype=np.bool_)
    is_disc[:n_disc] = True
    st = np.zeros(model.NSTATS)
    net = model.play(is_disc, k, 3.0, 1.0, q, o, e, a, arm, st)
    return net, st


def test_a_zero_reproduces_rung3a_exactly():
    for seed in (0, 5):
        for arm in (model.TEST, model.SHUFFLED):
            x, s1, g1 = model.run(0.6, 0.5, 0.1, 0.0, 0.9, arm, seed, gens=60)
            y, s2, g2 = m3a.run(0.6, 0.5, 0.1, 0.9, arm, seed, gens=60)
            assert np.array_equal(x, y)
            assert np.array_equal(s1[:9], s2) and np.array_equal(g1[:9], g2)


@pytest.mark.parametrize("o,e,a", [(0.5, 0.1, 0.02), (1.0, 0.3, 0.2), (0.25, 0.0, 0.1)])
def test_sanity_and_flips_both_directions(o, e, a):
    tot = np.zeros(model.NSTATS)
    for seed in range(4):
        _, st = _play(150, 200, 0.6, o, e, a, seed=seed)
        tot += st
    assert tot[0] == 0
    assert tot[9] > 0 and tot[10] > 0 and tot[11] > 0  # flips to good, to bad, and of ALLD records


def test_flip_rate_close_to_a():
    # all ALLD, o = 1: every act observed; each flip draw is one per act -> flips / acts ~ a
    _, st = _play(0, 400, 0.6, 1.0, 0.0, 0.1, seed=1)
    assert (st[9] + st[10]) / 4000 == pytest.approx(0.1, abs=0.015)


def test_no_flips_at_a_zero():
    _, st = _play(150, 200, 0.6, 0.5, 0.1, 0.0)
    assert st[9] == st[10] == st[11] == 0


def test_disc_good_share_near_screen():
    tot = good = 0.0
    for seed in range(10):
        _, st = _play(900, 1000, 0.6, 0.5, 0.1, 0.02, seed=seed)
        tot += st[4]
        good += st[5]
    assert 0.89 < good / tot < 0.94  # screen 0.913


def _rows(t_ok, s_ok, viol=0.0):
    out = []
    for name, (a, arms) in run.CONDITIONS.items():
        for arm in arms:
            ok = t_ok if arm == "test" else s_ok
            for sd in run.SEEDS:
                r = {"condition": name, "q": run.Q, "o": run.O, "e": run.E, "a": a, "start_disc": run.START,
                     "arm": arm, "seed": sd, "gens": run.GENS, "final_disc": 0.9 if sd < ok else 0.1, "disc_gen100": 0.5}
                for f in run.FIELDS:
                    r[f] = r["g1_" + f] = 1.0
                if a == 0.0:
                    for f in ("flips_good", "flips_bad", "flips_alld"):
                        r[f] = r["g1_" + f] = 0.0
                r["violations"] = viol if arm == "test" else 3.0
                r["g1_violations"] = 0.0
                out.append(r)
    return out


def test_verdict_rules():
    assert run.verdict(_rows(16, 4))[0] == "MET"
    assert run.verdict(_rows(15, 0))[0] == "NOT MET"
    assert run.verdict(_rows(20, 5))[0] == "NOT MET"
    assert run.verdict(_rows(20, 0, viol=1.0))[0].startswith("INVALID")
    r = _rows(20, 0); r.pop()
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["a"] = 0.05
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["g1_helps"] = 3.0
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["flips_alld"] = 5.0
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = [x for x in _rows(20, 0)]
    a0 = next(x for x in r if x["condition"] == "a000")
    a0["flips_good"] = 1.0
    assert run.verdict(r)[0] == "NO VERDICT (data)"


def test_alld_records_flip_both_ways():
    # all-ALLD population: every flip is an ALLD flip; both directions must occur
    _, st = _play(0, 300, 0.6, 1.0, 0.0, 0.1, seed=7)
    assert st[11] == st[9] + st[10]
    assert st[9] > 0 and st[10] > 0
