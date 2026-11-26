import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung2b import model as m2b
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3a import model, run


def _play(n_disc, n, q, o, e, arm=0, seed=0, k=10):
    model._seed(seed)
    is_disc = np.zeros(n, dtype=np.bool_)
    is_disc[:n_disc] = True
    st = np.zeros(model.NSTATS)
    net = model.play(is_disc, k, 3.0, 1.0, q, o, e, arm, st)
    return net, st


def test_e_zero_reproduces_rung2b_exactly():
    for seed in (0, 3):
        for arm3, arm2 in ((model.TEST, m2b.TEST), (model.SHUFFLED, m2b.SHUFFLED)):
            a, _, _ = model.run(0.6, 0.5, 0.0, 0.9, arm3, seed, gens=60)
            b, _, _ = m2b.run(0.6, 0.5, 0.9, arm2, seed, gens=60)
            assert np.array_equal(a, b)


@pytest.mark.parametrize("e,o", [(0.1, 0.5), (0.3, 1.0), (0.05, 0.25)])
def test_two_way_sanity_holds_and_failures_occur_both_ways(e, o):
    tot = np.zeros(model.NSTATS)
    for seed in range(4):
        _, st = _play(150, 200, 0.6, o, e, seed=seed)
        tot += st
    assert tot[0] == 0
    assert tot[6] > 0 and tot[7] > 0  # qualifying failures with and without consultation
    assert tot[8] == tot[6] + tot[7]  # every DISC bad assessment is a qualifying failure


def test_no_errors_no_bad_disc():
    _, st = _play(150, 200, 0.6, 0.5, 0.0)
    assert st[8] == 0 and st[6] == 0 and st[7] == 0


def test_failed_help_pays_nothing():
    # all DISC, q = 0 (always intend help), e = 0.5: helps ~ half the encounters, net = (b - c) * helps
    net, st = _play(100, 100, 0.0, 1.0, 0.5, seed=2)
    assert net.sum() == pytest.approx(st[3] * 2.0)
    assert 0.45 < st[3] / 1000 < 0.55


def test_image_scoring_marks_failures_and_justified_refusals_bad():
    _, st = _play(150, 200, 1.0, 1.0, 0.0, arm=model.IMAGE, seed=1)
    assert st[8] > 0  # justified refusals are bad under image scoring
    _, st = _play(150, 200, 1.0, 1.0, 0.0, arm=model.TEST, seed=1)
    assert st[8] == 0


def test_disc_good_share_near_screen():
    tot = good = 0.0
    for seed in range(10):
        _, st = _play(900, 1000, 0.6, 0.5, 0.1, seed=seed)
        tot += st[4]
        good += st[5]
    assert 0.90 < good / tot < 0.95  # screen 0.926


def _rows(t_ok, s_ok, viol=0.0):
    out = []
    for name, (e, arms) in run.CONDITIONS.items():
        for arm in arms:
            ok = t_ok if arm == "test" else s_ok
            for sd in run.SEEDS:
                r = {"condition": name, "q": run.Q, "o": run.O, "e": e, "start_disc": run.START, "arm": arm,
                     "seed": sd, "gens": run.GENS, "final_disc": 0.9 if sd < ok else 0.1, "disc_gen100": 0.5}
                for f in run.FIELDS:
                    r[f] = r["g1_" + f] = 1.0
                r["disc_bad"] = r["g1_disc_bad"] = 2.0  # = qualifying failures (1 + 1)
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
    r = _rows(20, 0); r[0]["consult_alld_good"] = 2.0
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["e"] = 0.2
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["g1_helps"] = float("nan")
    assert run.verdict(r)[0] == "NO VERDICT (data)"


def test_verdict_rejects_contradictory_counters():
    r = _rows(20, 0); r[0]["g1_helps"] = 5.0  # generation 1 above the whole run
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["disc_bad"] = 7.0  # test arm: bad assessments must equal qualifying failures
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0); r[0]["helps"] = 5_000_001.0
    assert run.verdict(r)[0] == "NO VERDICT (data)"


def test_image_scoring_marks_failed_helps_bad():
    # q = 0: every DISC always intends help, so every DISC bad assessment under image scoring is a failure
    _, st = _play(200, 200, 0.0, 1.0, 0.3, arm=model.IMAGE, seed=4)
    assert st[8] > 0
    assert st[8] >= st[6] + st[7]  # failures toward good and (if any) bad recipients are all bad
    _, st = _play(200, 200, 0.0, 1.0, 0.3, arm=model.TEST, seed=4)
    assert st[0] == 0 and st[8] == st[6] + st[7]


def test_unobserved_acts_keep_records():
    tot = np.zeros(model.NSTATS)
    for seed in range(3):
        _, st = _play(150, 200, 0.6, 0.2, 0.2, seed=seed)
        tot += st
    assert tot[0] == 0
