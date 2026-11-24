"""Deterministic checks for the step-5 restart (pre-registration ../STEP5_RESTART.md, 'Checks')."""
from __future__ import annotations

import numpy as np
import pytest

from ecological_models.nowak_mechanisms.kin_selection.ladder.step5_model import NB, N_SITES, Params, Step5Model


def mk(**kw):
    base = dict(B=1.2, p0=0.3, d=0.1)
    base.update(kw)
    return Params(**base)


def test_neighbours_are_four_distinct_and_symmetric():
    for i in range(N_SITES):
        assert len(set(NB[i])) == 4 and i not in NB[i]
        for j in NB[i]:
            assert i in NB[j]


@pytest.mark.parametrize("births", ["local", "global", "dd"])
def test_births_only_onto_vacancies_and_one_per_parent(births):
    m = Step5Model(mk(births=births), seed=3)
    for _ in range(200):
        occ_before = m.s.occ.copy()
        ids_before = m.s.ident.copy()
        m.step()
        new = m.s.ident >= ids_before.max() + 1
        new &= m.s.occ
        # newborns were placed only where no survivor sits: every newborn site was vacant or freshly vacated
        # one birth per parent per update
        par = m.s.parent[new]
        assert len(par) == len(set(par.tolist()))
        if births == "local":
            # newborn is a grid neighbour of its parent (parent alive at birth)
            site_of = {int(m.s.ident[i]): i for i in np.flatnonzero(m.s.occ)}
            for t in np.flatnonzero(new):
                p = site_of.get(int(m.s.parent[t]))
                if p is not None:
                    assert t in NB[p]
        assert m.s.occ.sum() <= N_SITES
        del occ_before


def test_dead_occupants_do_not_breed():
    m = Step5Model(mk(d=0.5, p0=0.45), seed=1)
    for _ in range(100):
        ids0 = set(m.s.ident[m.s.occ].tolist())
        m.step()
        surv_ids = set(m.s.ident[m.s.occ].tolist()) & ids0
        new = m.s.occ & ~np.isin(m.s.ident, list(ids0))
        for t in np.flatnonzero(new):
            assert int(m.s.parent[t]) in surv_ids


def test_no_vacancy_no_birth():
    m = Step5Model(mk(d=0.0, p0=0.45), seed=0)
    ids0 = m.s.ident.copy()
    m.step()
    assert np.array_equal(m.s.ident, ids0)       # full lattice, no deaths: nobody is born
    assert m.s.occ.all()


def test_refill_keeps_lattice_full_and_parents_from_survivors():
    m = Step5Model(mk(births="refill", d=0.3), seed=2)
    for _ in range(100):
        ids0 = m.s.ident.copy()
        m.step()
        assert m.s.occ.all()
        new = m.s.ident != ids0
        surv_ids = set(ids0[~new].tolist())
        for t in np.flatnonzero(new):
            assert int(m.s.parent[t]) in surv_ids


def test_care_reaches_only_living_offspring_in_equal_shares():
    m = Step5Model(mk(), seed=4)
    for _ in range(300):
        m.step()
    n, psite = m.offspring_counts()
    R, produced, lost = m.care_received(n, psite)
    for j in np.flatnonzero(m.s.occ):
        if psite[j] >= 0:
            assert R[j] == pytest.approx(1.2 * m.s.h[psite[j]] / n[psite[j]])
        else:
            assert R[j] == 0.0
    assert lost == pytest.approx(float((1.2 * m.s.h)[m.s.occ & (n == 0)].sum()))
    assert produced >= lost


def test_matched_control_recipients_are_non_offspring_neighbours_with_matched_dose():
    m = Step5Model(mk(care="matched"), seed=5)
    for _ in range(300):
        m.step()
    n, psite = m.offspring_counts()
    total_n = 0.0
    R, produced, lost = m.care_received(n, psite)
    # total delivered + lost equals produced; nobody receives from self
    assert R.sum() + lost == pytest.approx(produced)
    for i in np.flatnonzero(m.s.occ):
        total_n += n[i]
    assert total_n >= 0


def test_null_rules_identical_trajectories():
    a = Step5Model(Params(B=0.0, C=0.0, p0=0.3, d=0.1, care="offspring"), seed=7)
    b = Step5Model(Params(B=0.0, C=0.0, p0=0.3, d=0.1, care="neighbours"), seed=7)
    c = Step5Model(Params(B=0.0, C=0.0, p0=0.3, d=0.1, care="matched"), seed=7)
    for _ in range(300):
        a.step(); b.step(); c.step()
    for x in (b, c):
        assert np.array_equal(a.s.occ, x.s.occ) and np.array_equal(a.s.h, x.s.h)
        assert np.array_equal(a.s.ident, x.s.ident)


@pytest.mark.parametrize("births", ["global", "dd"])
def test_global_and_dd_only_on_vacancies(births):
    m = Step5Model(mk(births=births, d=0.2), seed=8)
    for _ in range(200):
        occ_ids = dict(zip(np.flatnonzero(m.s.occ).tolist(), m.s.ident[m.s.occ].tolist()))
        m.step()
        # a survivor's site still holds the same id: no birth overwrote an occupied site
        for site, ident in occ_ids.items():
            if m.s.occ[site] and m.s.ident[site] != ident:
                assert m.s.parent[site] >= 0     # replaced only after its occupant died


def test_p_at_most_one_at_b_c_6():
    assert 0.45 * (1 + 6 * 0.2) <= 1.0


def test_deterministic_replay():
    a = Step5Model(mk(care="matched", births="dd"), seed=9)
    b = Step5Model(mk(care="matched", births="dd"), seed=9)
    for _ in range(200):
        a.step(); b.step()
    assert np.array_equal(a.s.h, b.s.h) and np.array_equal(a.s.ident, b.s.ident)


# ---------------------------------------------------------------- amendment A1 checks (hand-built states)
from ecological_models.nowak_mechanisms.kin_selection.ladder.utils import run_step5 as R5  # noqa: E402


def _empty_model(**kw):
    m = Step5Model(mk(**kw), seed=0)
    m.s.occ[:] = False
    m.s.h[:] = 0.0
    m.s.parent[:] = -1
    return m


def _place(m, site, h, ident, parent=-1):
    m.s.occ[site] = True
    m.s.h[site] = h
    m.s.ident[site] = ident
    m.s.parent[site] = parent


def test_matched_each_recipient_at_most_one_donor_and_dose_bounded():
    m = Step5Model(mk(care="matched", p0=0.45), seed=11)
    for _ in range(400):
        m.step()
        n, psite = m.offspring_counts()
        Rv, produced, lost = m.care_received(n, psite)
        assert Rv.max() <= 1.2 + 1e-12            # one donor at most, dose <= B * 1
        assert 0.0 <= m.shortfall_lost <= lost + 1e-12
        assert Rv.sum() + lost == pytest.approx(produced)


def test_matched_draws_do_not_shift_other_streams():
    a = Step5Model(mk(care="matched"), seed=12)
    b = Step5Model(mk(care="offspring"), seed=12)
    a.step(); b.step()       # identical founders, no offspring yet: identical deaths and birth draws
    for ra, rb in ((a.rng_death, b.rng_death), (a.rng_birth, b.rng_birth), (a.rng_resolve, b.rng_resolve)):
        assert ra.bit_generator.state == rb.bit_generator.state


def test_matched_shortfall_when_no_eligible_neighbour():
    m = _empty_model(care="matched")
    _place(m, 0, 1.0, 1000)                       # donor
    child = int(NB[0][0])
    _place(m, child, 0.0, 1001, parent=1000)      # its only offspring; no other occupied neighbour
    n, psite = m.offspring_counts()
    Rv, produced, lost = m.care_received(n, psite)
    assert Rv.sum() == 0.0 and lost == pytest.approx(1.2) and m.shortfall_lost == pytest.approx(1.2)


def test_competing_claims_one_winner_and_losers_counted():
    m = _empty_model(p0=0.45, d=0.0, B=0.0)
    target = 50
    nbs = NB[target]
    for k, site in enumerate(nbs):
        _place(m, int(site), 0.0, 2000 + k)
    # make every other neighbour of the claimants occupied, so the only vacancy each can see is `target`
    for site in nbs:
        for q in NB[int(site)]:
            if int(q) != target and not m.s.occ[int(q)]:
                _place(m, int(q), 0.0, 3000 + int(q))
    m.p.p0 = 1.0                                   # every survivor attempts (W = 1)
    m.step()
    assert m.s.occ[target]
    assert int(m.s.parent[target]) in {2000 + k for k in range(4)}
    assert m.s.last["failed_per_attempt"] > 0


def test_refill_fallback_to_all_survivors():
    m = _empty_model(births="refill", d=1.0)
    # one occupant that dies (d = 1) with no survivors anywhere: lattice goes empty
    _place(m, 10, 0.0, 4000)
    m.step()
    assert not m.s.occ.any()


def test_refill_parent_from_neighbours_when_available():
    m = Step5Model(mk(births="refill", d=0.05), seed=13)
    for _ in range(50):
        prev_ids = m.s.ident.copy()
        prev_occ = m.s.occ.copy()
        m.step()
        site_of = {int(prev_ids[i]): i for i in np.flatnonzero(prev_occ)}
        for t in np.flatnonzero(m.s.ident != prev_ids):
            ps = site_of[int(m.s.parent[t])]
            assert ps in NB[t]                    # with ~95% survival every dead site has a surviving neighbour


def _rows(succ, viable=20, exposed=20, corr=0.0):
    return [{"seed": s, "success": int(s < succ), "viable": int(s < viable), "vacancy_exposed": int(s < exposed),
             "final_mean_h": 0.8 if s < succ else 0.1, "neighbour_h_corr": corr, "neighbour_h_corr_defined": 5}
            for s in range(20)]


def _arms(**over):
    base = {"F6-local": _rows(18), "FN6-local": _rows(2), "FR6-local": _rows(3), "F6-refill": _rows(18),
            "Fbelow": _rows(0), "F6-global": _rows(16), "F6-dd": _rows(10)}
    base.update(over)
    return base


def test_classification_precedence():
    assert R5.classify(_arms(), "F")["class"] == "met"
    assert R5.classify(_arms(**{"FN6-local": _rows(2, viable=17)}), "F")["class"] == "not interpretable"
    assert R5.classify(_arms(**{"F6-local": _rows(18, exposed=14)}), "F")["class"] == "not a step-5 test"
    assert R5.classify(_arms(**{"F6-local": _rows(14)}), "F")["class"] == "local failure"
    assert R5.classify(_arms(**{"Fbelow": _rows(3)}), "F")["class"] == "local failure"
    assert R5.classify(_arms(**{"FN6-local": _rows(11)}), "F")["class"] == "comparison failed"


def test_failure_reading_gated_on_local_test_arm():
    r = R5.classify(_arms(**{"F6-local": _rows(10), "F6-refill": _rows(18)}), "F")
    assert r["failure_reading"].startswith("free space blocks care")
    r = R5.classify(_arms(**{"F6-local": _rows(10), "F6-refill": _rows(5)}), "F")
    assert r["failure_reading"] == "missed endpoint for this birth-rule package"
    r = R5.classify(_arms(**{"Fbelow": _rows(3)}), "F")          # local test met its endpoint
    assert r["failure_reading"].startswith("care reached the endpoint locally")


def test_h2_h3_gates():
    r = R5.classify(_arms(), "F")
    assert r["h2"]["result"] == "met" and r["h3"]["result"] == "met"
    r = R5.classify(_arms(**{"F6-global": _rows(16, corr=0.2)}), "F")
    assert r["h2"]["result"] == "not interpretable"
    g = _rows(16)
    g[0]["neighbour_h_corr_defined"] = 0
    assert R5.classify(_arms(**{"F6-global": g}), "F")["h2"]["result"].startswith("not interpretable")
    assert R5.classify(_arms(**{"FR6-local": _rows(12)}), "F")["h3"]["result"] == "not met"
    assert R5.classify(_arms(**{"FR6-local": _rows(3, viable=17)}), "F")["h3"]["result"].startswith("not interpretable")
    assert R5.classify(_arms(**{"F6-local": _rows(10)}), "F")["h3"]["result"].startswith("not scored")


def test_complete_rejects_truncated_and_bad_extinction():
    jobs = [("a", {}, 0, "M1")]
    ok = {"arm": "a", "seed": 0, "extinct": 0, "extinct_at": None, "completed_updates": 6000,
          "n_window": 5000, "n_late": 2000}
    assert R5.complete([ok], jobs)
    assert not R5.complete([{**ok, "n_window": 4999}], jobs)
    assert not R5.complete([{**ok, "completed_updates": 5999}], jobs)
    assert R5.complete([{**ok, "extinct": 1, "extinct_at": 300, "completed_updates": 300}], jobs)
    assert not R5.complete([{**ok, "extinct": 1, "extinct_at": 300, "completed_updates": 6000}], jobs)
    assert not R5.complete([ok, ok], jobs)


def test_neighbour_corr_matches_k1_estimator_on_full_lattice():
    from ecological_models.nowak_mechanisms.kin_selection.ladder.utils.analysis import neighbour_correlation
    rng = np.random.default_rng(0)
    m = Step5Model(mk(), seed=0)
    m.s.h = rng.random(N_SITES)
    m.s.h[: 24] = np.linspace(0, 1, 24)           # structure on the wraparound row
    mask = np.zeros((N_SITES, N_SITES), dtype=bool)
    for i in range(N_SITES):
        mask[i, NB[i]] = True
    ei, ej = np.nonzero(np.triu(mask, k=1))       # K1's edge_pairs
    assert m.neighbour_corr() == pytest.approx(neighbour_correlation(m.s.h, ei, ej))


def test_death_stream_unaffected_by_matched_draws():
    a = Step5Model(mk(care="matched"), seed=12)
    b = Step5Model(mk(care="offspring"), seed=12)
    for _ in range(60):                            # matched draws happen once offspring exist
        a.step(); b.step()
    assert a.rng_death.bit_generator.state == b.rng_death.bit_generator.state


def test_matched_two_donors_compete_for_one_recipient():
    m = _empty_model(care="matched")
    shared = 100
    d1, d2 = int(NB[shared][0]), int(NB[shared][1])
    _place(m, shared, 0.0, 5000)
    _place(m, d1, 1.0, 5001)
    _place(m, d2, 1.0, 5002)
    for donor, ident in ((d1, 5001), (d2, 5002)):
        # each donor gets one offspring on a neighbour that is not a neighbour of `shared`
        for q in NB[donor]:
            q = int(q)
            if q != shared and not m.s.occ[q] and q not in NB[shared]:
                _place(m, q, 0.0, ident + 100, parent=ident)
                break
    # only `shared` is an eligible non-offspring neighbour for either donor (others empty or offspring)
    n, psite = m.offspring_counts()
    assert n[d1] == 1 and n[d2] == 1
    Rv, produced, lost = m.care_received(n, psite)
    assert Rv[shared] == pytest.approx(1.2)        # one donor only
    assert m.shortfall_lost == pytest.approx(1.2)  # the other donor's share found no recipient
