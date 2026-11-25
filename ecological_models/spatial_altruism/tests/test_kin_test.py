"""Checks for the kin-selection test runner (../PREREG_KIN_TEST.md): unchanged dynamics, control, founder ids."""
from __future__ import annotations

import numpy as np

from ecological_models.spatial_altruism.altruism_model import BLACK, AltruismModel, make_params
from ecological_models.spatial_altruism.utils.run_kin_test import KinTestModel, founder_sharing, shifts

P = dict(benefit_from_altruism=0.468, cost_of_altruism=0.156, harshness=0.96, disease=0.213,
         altruistic_probability=0.39, selfish_probability=0.39, model_variant="steady_state")


def _trajectory(model, steps=300):
    out = []
    for _ in range(steps):
        cont = model.go()
        out.append(model.pcolor.copy())
        if not cont:
            break
    return out


def test_bookkeeping_does_not_change_dynamics():
    # run one after the other: the model draws from NumPy's global stream, seeded in its constructor
    ta = _trajectory(AltruismModel(make_params({**P, "seed": 7})))
    tb = _trajectory(KinTestModel(make_params({**P, "seed": 7}), shuffle=False))
    assert len(ta) == len(tb)
    assert all(np.array_equal(x, y) for x, y in zip(ta, tb))


def test_shuffle_keeps_vacancy_map_and_counts():
    m = KinTestModel(make_params({**P, "seed": 3}), shuffle=True)
    for _ in range(20):
        m.go()
    occ = m.pcolor != BLACK
    counts = np.bincount(m.pcolor.ravel(), minlength=3)
    founders = np.sort(m.founder[occ])
    m._shuffle_occupants()
    assert np.array_equal(occ, m.pcolor != BLACK)
    assert np.array_equal(counts, np.bincount(m.pcolor.ravel(), minlength=3))
    assert np.array_equal(founders, np.sort(m.founder[occ]))
    assert np.array_equal(m.benefit_out > 0, m.pcolor == 2)


def test_founder_comes_from_a_same_type_candidate():
    m = KinTestModel(make_params({**P, "seed": 11}))
    for _ in range(30):
        prev_c, prev_f = m.pcolor.copy(), m.founder.copy()
        if not m.go():
            break
        ct, cf = shifts(prev_c), shifts(prev_f)
        for y, x in zip(*np.nonzero(m.pcolor != BLACK)):
            ok = [cf[k, y, x] for k in range(5) if ct[k, y, x] == m.pcolor[y, x]]
            assert m.founder[y, x] in ok
        assert (m.founder[m.pcolor == BLACK] == -1).all()


def test_founder_sharing_in_range():
    m = KinTestModel(make_params({**P, "seed": 5}))
    for _ in range(100):
        m.go()
    s, e = founder_sharing(m)
    assert 0 <= s <= 1 and 0 <= e <= 1


# ---- regressions for the Codex review fixes ----
from fractions import Fraction  # noqa: E402

from ecological_models.spatial_altruism.utils import run_kin_test as R  # noqa: E402


def test_choose_index_strictly_above_and_proportional():
    w = np.zeros((5, 1, 1))
    w[:, 0, 0] = [0.0, 0.0, 2.0, 0.0, 1.0]
    assert R.choose_index(w, np.array([[0.0]]))[0, 0] == 2            # zero draw skips zero-weight candidates
    assert R.choose_index(w, np.array([[0.66]]))[0, 0] == 2
    assert R.choose_index(w, np.array([[0.67]]))[0, 0] == 4
    assert R.choose_index(w, np.array([[0.999999]]))[0, 0] == 4


def test_neighbour_order_matches_model_roll():
    x = np.arange(9).reshape(3, 3)
    s = R.shifts(x)
    assert s[1, 0, 0] == x[1, 0] and s[2, 0, 0] == x[2, 0] and s[3, 0, 0] == x[0, 1] and s[4, 0, 0] == x[0, 2]


def test_exact_cutoffs():
    r = {"extinct_at": None, "late_occupied_exact": [1, 10], "mid_occupied_exact": [1, 8],
         "late_alt_share": 0.6}
    assert R.viable(r) and R.success(r)            # exactly 10% occupancy and 60% share pass
    assert R.s_passes(r)                           # 0.1 >= 0.8 * 0.125 exactly


def test_final_step_extinction_is_recorded(monkeypatch):
    calls = {"n": 0}
    orig = R.KinTestModel.go

    def go(self):
        cont = orig(self)
        calls["n"] += 1
        if calls["n"] == 3:                         # empty the grid on the third step, as the model's go() would
            self.pcolor[...] = 0
            self.benefit_out[...] = 0
        return cont
    monkeypatch.setattr(R.KinTestModel, "go", go)
    out = R.run(("T", 0.96, 0.213, 0.468, 0.05, 0.73, 123, False))
    assert out["extinct_at"] == 3 and not R.viable(out)
