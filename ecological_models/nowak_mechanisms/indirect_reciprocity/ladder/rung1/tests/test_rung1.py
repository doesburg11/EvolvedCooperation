import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung1 import model, run, theory


def test_other_excludes_two_and_is_uniform():
    model._seed(0)
    counts = np.zeros(6)
    for _ in range(60000):
        counts[model._other(6, 1, 4)] += 1
    assert counts[1] == 0 and counts[4] == 0
    assert np.allclose(counts[[0, 2, 3, 5]] / 60000, 0.25, atol=0.01)


def _mean_payoffs(n_disc, q, shuffled, reps=200, n=200):
    model._seed(1)
    is_disc = np.zeros(n, dtype=np.bool_)
    is_disc[:n_disc] = True
    acc = np.zeros(n)
    for _ in range(reps):
        acc += model.payoffs(is_disc, model.K, model.B, model.C, q, shuffled) / model.K
    acc /= reps
    return acc[:n_disc].mean(), acc[n_disc:].mean()


@pytest.mark.parametrize("shuffled", [False, True])
def test_payoffs_match_theory(shuffled, monkeypatch):
    n, n_disc, q = 200, 150, 0.6
    monkeypatch.setattr(theory, "N", n)
    pd, pa = theory.payoffs(n_disc, q, shuffled)
    md, ma = _mean_payoffs(n_disc, q, shuffled, n=n)
    assert md == pytest.approx(pd, abs=0.02)
    assert ma == pytest.approx(pa, abs=0.02)


def test_alld_never_helps_and_costs_only_disc():
    model._seed(2)
    is_disc = np.zeros(50, dtype=np.bool_)
    net = model.payoffs(is_disc, 10, 3.0, 1.0, 0.6, False)
    assert (net == 0).all()


def test_absorbing_and_trajectory_shape():
    tr = model.run(0.6, 1.0, False, 0, gens=5)
    assert tr.shape == (6,) and (tr == 1.0).all()
    tr = model.run(0.6, 0.0, True, 0, gens=5)
    assert (tr == 0.0).all()


def test_reproducible_by_seed():
    a = model.run(0.6, 0.9, True, 7, gens=20)
    b = model.run(0.6, 0.9, True, 7, gens=20)
    assert np.array_equal(a, b)


def test_verdict_rules():
    def rows(t_ok, s_ok):
        out = []
        for name, (q, start, _) in run.CONDITIONS.items():
            for arm, ok in (("test", t_ok), ("shuffled", s_ok)):
                for sd in run.SEEDS:
                    out.append({"condition": name, "q": q, "start_disc": start, "arm": arm, "seed": sd,
                                "gens": run.GENS, "final_disc": 0.9 if sd < ok else 0.1})
        return out
    r = rows(20, 0); r[0]["final_disc"] = 1.2
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = rows(20, 0); r[0]["q"] = 0.5
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = rows(20, 0); r = [x for x in r if not (x["condition"] == "rare" and x["seed"] == 3)]
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = rows(20, 0); del r[5]["gens"]
    assert run.verdict(r)[0] == "NO VERDICT (data)"
    r = rows(16, 4); r[0]["final_disc"] = 0.8  # endpoint inclusive
    assert run.verdict(r)[1] == 16
    assert run.verdict(rows(16, 4))[0] == "MET"
    assert run.verdict(rows(15, 0))[0] == "NOT MET"
    assert run.verdict(rows(20, 5))[0] == "NOT MET"
    assert run.verdict(rows(20, 0)[:-1])[0] == "NO VERDICT (data)"
