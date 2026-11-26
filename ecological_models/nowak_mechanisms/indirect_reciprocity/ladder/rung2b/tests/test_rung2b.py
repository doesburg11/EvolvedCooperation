import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2 import model as m2
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2b import model, run


def _play(n_disc, n, q, o, arm=0, seed=0, k=10):
    model._seed(seed)
    is_disc = np.zeros(n, dtype=np.bool_)
    is_disc[:n_disc] = True
    st = np.zeros(6)
    net = model.play(is_disc, k, 3.0, 1.0, q, o, arm, st)
    return net, st


def test_o_one_reproduces_rung2_exactly():
    for seed in (0, 4):
        a, _, _ = model.run(0.6, 1.0, 0.9, model.TEST, seed, gens=60)
        b, _ = m2.run(0.6, 0.9, m2.TEST, seed, gens=60)
        assert np.array_equal(a, b)
        a, _, _ = model.run(0.6, 1.0, 0.9, model.SHUFFLED, seed, gens=60)
        b, _ = m2.run(0.6, 0.9, m2.SHUFFLED, seed, gens=60)
        assert np.array_equal(a, b)


@pytest.mark.parametrize("o", [1.0, 0.5, 0.1])
def test_disc_never_bad_in_test_arm(o):
    for seed in range(4):
        _, st = _play(150, 200, 0.6, o, seed=seed)
        assert st[0] == 0


def test_unobserved_share_matches_geometric():
    # share of ALLD with no observed act in a generation of k acts = (1 - o)^k
    for o in (0.25, 0.1):
        tot = un = 0.0
        for seed in range(20):
            _, st = _play(100, 400, 0.6, o, seed=seed)
            tot += st[5]
            un += st[4]
        assert un / tot == pytest.approx((1 - o) ** 10, abs=0.03)


def test_good_alld_share_g1_near_refined_screen():
    tot = good = 0.0
    for seed in range(10):
        _, st = _play(900, 1000, 0.6, 0.5, seed=seed)
        tot += st[1]
        good += st[2]
    assert 0.18 < good / tot < 0.26  # refined screen 0.214, script 0.227


def test_generation1_stats_separate():
    tr, st, g1 = model.run(0.6, 0.5, 0.9, model.TEST, 1, gens=3)
    assert g1[5] == 100  # 100 ALLD at the start
    assert st[5] > 0 or tr[1] == 1.0


def test_o_validation():
    with pytest.raises(ValueError):
        model.run(0.6, 0.0, 0.9, model.TEST, 0, gens=2)


def _rows(t_ok, s_ok, bad=0.0):
    out = []
    for name, (q, o, arms) in run.CONDITIONS.items():
        for arm in arms:
            ok = t_ok if arm == "test" else s_ok
            for sd in run.SEEDS:
                out.append({"condition": name, "q": q, "o": o, "start_disc": run.START, "arm": arm, "seed": sd,
                            "gens": run.GENS, "final_disc": 0.9 if sd < ok else 0.1,
                            "disc_bad": bad if arm == "test" else 2.0, "disc_bad_g1": 0.0, "disc_gen100": 0.5,
                            "g1_consult_alld": 50.0, "g1_consult_alld_good": 10.0, "g1_alld_unobserved": 1.0,
                            "g1_alld": 100.0, "consult_alld": 60.0, "consult_alld_good": 12.0})
    return out


def test_verdict_rules():
    assert run.verdict(_rows(16, 4))[0] == "MET"
    assert run.verdict(_rows(15, 0))[0] == "NOT MET"
    assert run.verdict(_rows(20, 5))[0] == "NOT MET"
    assert run.verdict(_rows(20, 0, bad=1.0))[0].startswith("INVALID")
    r = _rows(20, 0); r.pop()
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["disc_bad"] = float("nan")
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["o"] = 0.3
    assert run.verdict(r)[0] == "NO VERDICT (data)"


def test_verdict_rejects_bad_diagnostics():
    for field, v in (("g1_alld_unobserved", -1.0), ("g1_consult_alld_good", 51.0), ("disc_gen100", float("nan")),
                     ("g1_alld", 99.0), ("consult_alld", 1.5)):
        r = _rows(20, 0)
        r[3][field] = v
        assert run.verdict(r)[0] == "NO VERDICT (data)", field
    r = _rows(20, 0)
    del r[3]["g1_alld"]
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0)
    r[1] = dict(r[0])  # duplicate seed
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0)
    r[0]["disc_bad_g1"] = 1.0  # generation-1-only sanity failure
    assert run.verdict(r)[0].startswith("INVALID")
