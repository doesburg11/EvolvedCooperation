import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2 import model, run


def _play(n_disc, n, q, arm, seed=0, k=10):
    model._seed(seed)
    is_disc = np.zeros(n, dtype=np.bool_)
    is_disc[:n_disc] = True
    st = np.zeros(4)
    net = model.play(is_disc, k, 3.0, 1.0, q, arm, st)
    return net, st


def test_disc_never_bad_in_test_arm():
    for seed in range(5):
        _, st = _play(150, 200, 0.6, model.TEST, seed)
        assert st[0] == 0
    _, st = _play(150, 200, 1.0, model.TEST, 9)
    assert st[0] == 0


def test_image_scoring_makes_refusing_disc_bad():
    _, st = _play(150, 200, 1.0, model.IMAGE, 1)
    assert st[0] > 0


def test_shuffled_can_make_disc_bad():
    _, st = _play(150, 200, 1.0, model.SHUFFLED, 1)
    assert st[0] > 0


def test_all_alld_no_help_and_all_disc_full_help():
    net, st = _play(0, 50, 0.6, model.TEST)
    assert (net == 0).all() and st[3] == 0
    net, st = _play(50, 50, 0.6, model.TEST)
    assert st[3] == 50 * 10  # everyone good, every encounter helped
    assert net.sum() == pytest.approx(50 * 10 * (3.0 - 1.0))


def test_good_alld_share_near_screen():
    # at 10% ALLD, a consulting DISC finds an ALLD with a good record about 13-14% of the time (screen 0.132-0.136)
    tot = good = 0.0
    for seed in range(10):
        _, st = _play(900, 1000, 0.6, model.TEST, seed)
        tot += st[1]
        good += st[2]
    assert 0.11 < good / tot < 0.16


def test_q_zero_disc_helps_everyone():
    net, st = _play(100, 200, 0.0, model.TEST)
    assert st[3] == 100 * 10 and st[1] == 0


def test_reproducible_and_absorbing():
    a = model.run(0.6, 0.9, model.TEST, 3, gens=10)
    b = model.run(0.6, 0.9, model.TEST, 3, gens=10)
    assert np.array_equal(a[0], b[0])
    tr, _ = model.run(0.6, 1.0, model.TEST, 0, gens=3)
    assert (tr == 1.0).all()


def _rows(t_ok, s_ok, bad=0.0):
    out = []
    for name, (q, start, arms) in run.CONDITIONS.items():
        for arm in arms:
            ok = t_ok if arm == "test" else s_ok
            for sd in run.SEEDS:
                out.append({"condition": name, "q": q, "start_disc": start, "arm": arm, "seed": sd, "gens": run.GENS,
                            "final_disc": 0.9 if sd < ok else 0.1, "disc_bad": bad if arm == "test" else 3.0})
    return out


def test_verdict_rules():
    assert run.verdict(_rows(16, 4))[0] == "MET"
    assert run.verdict(_rows(15, 0))[0] == "NOT MET"
    assert run.verdict(_rows(20, 5))[0] == "NOT MET"
    assert run.verdict(_rows(20, 0, bad=1.0))[0].startswith("INVALID")
    r = _rows(20, 0); r.pop()
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["final_disc"] = -0.1
    assert run.verdict(r)[0] == "NO VERDICT (data)"


def test_verdict_rejects_bad_sanity_counters():
    for v in (float("nan"), -1.0, 0.5):
        r = _rows(20, 0)
        r[0]["disc_bad"] = v
        assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0)
    del r[0]["disc_bad"]
    assert run.verdict(r)[0] == "NO VERDICT (data)"


def test_simple_standing_table_deterministic():
    # two agents, q = 1: DISC 0 meets ALLD 1 (record good at start) -> helps; ALLD refuses a good DISC -> bad;
    # then DISC refuses the bad ALLD -> stays good (justified); ALLD refusing ... stays bad/good per table
    model._seed(5)
    is_disc = np.array([True, False])
    st = np.zeros(4)
    net = model.play(is_disc, 4, 3.0, 1.0, 1.0, model.TEST, st)
    assert st[0] == 0  # DISC never bad
    # DISC helps only while the ALLD record is good: at most in the first round, before the ALLD has acted
    assert st[3] <= 1
