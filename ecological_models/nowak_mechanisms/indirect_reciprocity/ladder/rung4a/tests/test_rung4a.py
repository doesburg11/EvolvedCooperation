import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung3b import model as m3b
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a import model, run


def _play(n_alld, n_allc, n, q, o, e, a, arm=0, seed=0, k=10):
    model._seed(seed)
    is_disc = np.ones(n, dtype=np.bool_)
    is_disc[:n_alld + n_allc] = False
    is_allc = np.zeros(n, dtype=np.bool_)
    is_allc[n_alld:n_alld + n_allc] = True
    st = np.zeros(model.NSTATS)
    net = model.play(is_disc, is_allc, k, 3.0, 1.0, q, o, e, a, arm, st)
    return net, st


def test_no_allc_reproduces_rung3b_exactly():
    for seed in (0, 2, 9):
        for arm in (model.TEST, model.SHUFFLED):
            tr, s1, g1 = model.run(0.6, 0.5, 0.1, 0.02, (0.0, 0.9, 0.1), arm, seed, gens=80)
            y, s2, g2 = m3b.run(0.6, 0.5, 0.1, 0.02, 0.9, arm, seed, gens=80)
            assert np.array_equal(np.round(tr[:, 0] * 1000), np.round((1.0 - y) * 1000))  # ALLD counts identical
            assert np.allclose(tr[:, 2], y, atol=1e-12)
            assert (tr[:, 1] == 0).all()
            assert np.array_equal(s1[:12], s2) and np.array_equal(g1[:12], g2)


def test_allc_action_law():
    # all ALLC, q = 1 (irrelevant: ALLC never consults), e = 0.3: intended helps = encounters, no consultation counted
    net, st = _play(0, 200, 200, 1.0, 1.0, 0.3, 0.0, seed=1)
    assert st[17] == st[16] == 2000  # always intends to help
    assert st[1] == st[4] == st[12] == 0  # never consults
    assert net.sum() == pytest.approx(st[3] * 2.0)  # pays only on successful helps
    assert 0.65 < st[3] / 2000 < 0.75


def test_allc_assessed_and_flipped_like_anyone():
    _, st = _play(50, 100, 200, 0.6, 0.5, 0.1, 0.05, seed=3)
    assert st[14] > 0 and st[15] > 0  # ALLC qualifying failures and bad assessments occur
    assert st[0] == 0


def test_allc_helps_bad_recipients_too():
    # ALLC + ALLD, e = 0, o = 1: ALLD turn bad after refusing good ALLC; ALLC keep helping them
    _, st = _play(100, 100, 200, 0.6, 1.0, 0.0, 0.0, seed=4)
    assert st[3] == pytest.approx(st[17])  # every intended help succeeds and ALLC intend all


@pytest.mark.parametrize("arm", [0, 1])
def test_sanity_two_way(arm):
    tot = np.zeros(model.NSTATS)
    for seed in range(3):
        _, st = _play(100, 200, 1000, 0.6, 0.5, 0.1, 0.02, arm=arm, seed=seed)
        tot += st
    if arm == 0:
        assert tot[0] == 0


def test_mixed_allc_disc_keeps_evolving():
    tr, st, _ = model.run(0.6, 0.5, 0.1, 0.02, (0.5, 0.5, 0.0), model.TEST, 1, gens=50)
    assert (tr[:, 0] == 0).all()
    assert st[16] == 1000 * 10 * 49 or tr[-1, 1] in (0.0, 1.0)  # plays every generation until single-type fixation


def test_single_strategy_absorbing():
    for start in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
        tr, st, g1 = model.run(0.6, 0.5, 0.1, 0.02, start, model.TEST, 0, gens=3)
        assert (tr == tr[0]).all() and st[16] == 0 and g1[16] == 0


def _rows(t_ok, s_ok, viol=0.0):
    out = []
    for name, (start, arms) in run.CONDITIONS.items():
        for arm in arms:
            ok = t_ok if arm in ("test", "image") else s_ok
            for sd in run.SEEDS:
                r = {"condition": name, "q": run.Q, "o": run.O, "e": run.E, "a": run.A, "start_allc": start[0],
                     "start_disc": start[1], "start_alld": start[2], "arm": arm, "seed": sd, "gens": run.GENS,
                     "final_alld": 0.1 if sd < ok else 0.9, "final_allc": 0.0, "final_disc": 0.9 if sd < ok else 0.1,
                     "coop_gen100": 0.5}
                for f in run.FIELDS:
                    r[f] = r["g1_" + f] = 1.0
                r["encounters"] = 20000.0
                r["g1_encounters"] = 10000.0
                r["g1_allc_intends"] = round(start[0] * 1000) * 10
                r["allc_intends"] = r["g1_allc_intends"] + 1.0 if start[0] > 0 else 0.0
                r["max_alld"] = 0.0 if start[2] == 0 else 0.2
                if start[2] == 0:
                    r["final_alld"], r["final_disc"] = 0.0, 1.0
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
    r = _rows(20, 0); r[0]["final_disc"] = 0.95
    assert run.verdict(r)[0] == "NO VERDICT (data)"  # shares no longer sum to 1
    r = _rows(20, 0); r[0]["helps"] = 30000.0
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0)
    x = next(v for v in r if v["condition"] == "no_allc")
    x["final_allc"], x["final_disc"] = 0.05, x["final_disc"] - 0.05
    assert run.verdict(r)[0] == "NO VERDICT (data)"


def test_verdict_rejects_impossible_and_contradictory_rows():
    r = _rows(20, 0)
    x = next(v for v in r if v["condition"] == "no_alld")
    x["final_alld"], x["final_disc"] = 0.1, 0.9
    assert run.verdict(r)[0] == "NO VERDICT (data)"  # ALLD reappeared without mutation
    r = _rows(20, 0)
    x = next(v for v in r if v["condition"] == "main")
    x["g1_allc_intends"] = 0.0
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = _rows(20, 0)
    r[0]["consult_alld"] = r[0]["consult_disc"] = r[0]["consult_allc"] = 15000.0
    assert run.verdict(r)[0] == "NO VERDICT (data)"


def test_neutral_three_type_reproduction():
    # s = 0: offspring composition is multinomial with the parents' shares; means over seeds match the start
    nc, na = [], []
    for seed in range(300):
        tr, _, _ = model.run(0.6, 0.5, 0.1, 0.02, (0.2, 0.5, 0.3), model.TEST, seed, gens=1, s=0.0)
        na.append(tr[1, 0])
        nc.append(tr[1, 1])
    assert np.mean(na) == pytest.approx(0.3, abs=0.005)
    assert np.mean(nc) == pytest.approx(0.2, abs=0.005)
    # multinomial variance of the ALLC share: 0.2 * 0.8 / 1000
    assert np.var(nc) == pytest.approx(0.16 / 1000, rel=0.25)


def test_recipient_counters_exact_small():
    # q = 1, o = 1, e = a = 0: every DISC donor consults; counters by recipient type sum to DISC encounters
    _, st = _play(30, 30, 100, 1.0, 1.0, 0.0, 0.0, seed=6)
    assert st[1] + st[4] + st[12] == 40 * 10  # 40 DISC x 10 rounds
    assert st[17] == 30 * 10


def test_attempt2_verdict_uses_its_own_conditions():
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung4a import run_attempt2 as r2

    def rows(t_ok, s_ok, allc_g1=500.0, start=r2.START):
        out = []
        for arm, ok in (("test", t_ok), ("shuffled", s_ok)):
            for sd in run.SEEDS:
                r = {"condition": "main", "q": run.Q, "o": run.O, "e": run.E, "a": run.A, "start_allc": start[0],
                     "start_disc": start[1], "start_alld": start[2], "arm": arm, "seed": sd, "gens": run.GENS,
                     "final_alld": 0.0 if sd < ok else 1.0, "final_allc": 0.0, "final_disc": 1.0 if sd < ok else 0.0,
                     "coop_gen100": 0.5, "max_alld": 0.2}
                for f in run.FIELDS:
                    r[f] = r["g1_" + f] = 1.0
                r["encounters"], r["g1_encounters"] = 20000.0, 10000.0
                r["g1_allc_intends"], r["allc_intends"] = allc_g1, allc_g1 + 1.0
                r["violations"] = r["g1_violations"] = 0.0
                out.append(r)
        return out
    assert r2.verdict(rows(16, 4))[0] == "MET"
    assert r2.verdict(rows(15, 4))[0] == "NOT MET"
    assert r2.verdict(rows(16, 4, allc_g1=1000.0))[0] == "NO VERDICT (data)"
    assert r2.verdict(rows(16, 4, start=(0.1, 0.8, 0.1)))[0] == "NO VERDICT (data)"
    assert r2.verdict(rows(16, 4)[:-1])[0] == "NO VERDICT (data)"
    assert run.CONDITIONS["main"][0] == (0.1, 0.8, 0.1)  # attempt 1's list restored
