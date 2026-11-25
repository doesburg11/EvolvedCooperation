"""Synthetic checks of run_feeding.Measurer (unique ids across slot reuse, measures per the registered definitions).

Run with the replication environment:
  ~/simulation_results/altruistic_feeding/venv_050/bin/python -m pytest -q test_measures.py
"""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace as NS

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_feeding as rf  # noqa: E402

N = rf.N_MAX


class FakeEnv:
    height = width = 10

    def get_facing_pos(self, pos, ori):
        import jax.numpy as jnp
        return (pos + jnp.array([1, 0])) % 10      # everyone faces +x


def state(existing, ages, positions=None, newborn=None, parents=None):
    ex = np.zeros(N, bool)
    ex[list(existing)] = True
    age = np.zeros(N, int)
    for k, v in ages.items():
        age[k] = v
    pos = np.zeros((N, 2), int) if positions is None else positions
    nb = np.zeros(N, bool)
    par = np.full(N, -1)
    for k, v in (newborn or {}).items():
        nb[k] = True
        par[k] = v
    agents = NS(are_existing_agents=ex, age_agents=age, positions_agents=pos, orientation_agents=np.zeros(N, int))
    return NS(state_env=NS(agents=agents), eco_information=NS(are_newborns_agents=nb, indexes_parents=par))


def info(feeders=(), feedees=(), to_off=(), deaths=None):
    f = np.full(N, np.nan)
    f[:] = 0.0
    fe = np.zeros(N)
    to = np.zeros(N)
    for a, b, c in zip(feeders, feedees, to_off):
        f[a], fe[a], to[a] = 1.0, b, float(c)
    le = np.full(N, np.nan)
    for k, v in (deaths or {}).items():
        le[k] = v
    return {"metrics": {"feeders": f, "feedees": fe, "to_offspring": to, "life_expectancy": le}}


def make(steps=10, window=5):
    m = rf.Measurer.__new__(rf.Measurer)
    rf.Measurer.__init__(m, FakeEnv(), steps, window, True)
    m.track_start = 0
    m._facing = m._facing_slots          # unjitted: the fake state is not a JAX pytree
    return m


def test_parent_identity_survives_slot_reuse_and_stale_env_flag_detected():
    m = make(steps=10, window=10)
    m.win_start = 0
    # t0: agent in slot 0 (adult) gives birth into slot 1
    m(0, state({0}, {0: 200}), state({0, 1}, {0: 201, 1: 0}, newborn={1: 0}), info())
    # t1: slot 0 dies; t2: a newborn of slot 1? no - an unrelated founder-born agent: slot 2 parent of a newborn in slot 0
    m(1, state({0, 1}, {0: 201, 1: 1}), state({1}, {1: 2}), info(deaths={0: 201}))
    m(2, state({1, 2}, {1: 2, 2: 300}), state({0, 1, 2}, {0: 0, 1: 3, 2: 301}, newborn={0: 2}), info())
    # t3: the new occupant of slot 0 feeds slot 1 (not its offspring; env's slot-based flag would say it is)
    m(3, state({0, 1, 2}, {0: 1, 1: 3, 2: 301}), state({0, 1, 2}, {0: 2, 1: 4, 2: 302}),
      info(feeders=[0], feedees=[1], to_off=[1]))
    assert m.c["feeds"] == 1 and m.c["feeds_to_offspring"] == 0
    assert m.c["stale_flags"] == 1 and m.c["feeds_to_infants"] == 1
    assert m.fed_infant[m.uid[1]] == 1


def test_isr_and_b_hat():
    m = make(steps=10, window=10)
    m.win_start = 0
    ex = {0, 1, 2, 3}
    ages = {0: 50, 1: 50, 2: 50, 3: 300}
    # slot 3 (adult) feeds infant slot 0 once
    m(0, state(ex, ages), state(ex, ages), info(feeders=[3], feedees=[0], to_off=[0]))
    # deaths: slot 0 (fed infant) at age 80, slot 1 (unfed) at 40, slot 2 (unfed) at 120
    m(1, state(ex, ages), state({3}, {3: 301}), info(deaths={0: 80, 1: 40, 2: 120}))
    r = m.results()
    assert r["ISR"] == pytest.approx(1 - 2 / 3)
    assert r["b_hat_pct"] == pytest.approx(100 * (80 / np.mean([40, 120]) - 1))
    assert r["n_deaths_fed_infant"] == 1 and r["n_deaths_unfed"] == 2


def test_selectivity_formula():
    m = make()
    m.c.update(feeds=10, feeds_to_offspring=6, facing_any=100, facing_offspring=20, pop_sum=500, win_steps=5)
    r = m.results()
    assert r["selectivity"] == pytest.approx(0.6 - 0.2)
    assert r["amount"] == pytest.approx(10 / 100)


def test_outside_window_counts_nothing_but_tracks_ids():
    m = make(steps=10, window=2)
    m.track_start = 0
    m(0, state({0}, {0: 200}), state({0, 1}, {0: 201, 1: 0}, newborn={1: 0}),
      info(feeders=[0], feedees=[1], to_off=[1]))
    assert m.c["feeds"] == 0 and m.parent_uid[1] == m.uid[0]
