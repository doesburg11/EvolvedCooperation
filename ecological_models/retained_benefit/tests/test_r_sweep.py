"""Tests for the pre-registered retained-fraction sweep (runner and analysis)."""

import json
import math
import random

import numpy as np
import pytest

from ecological_models.retained_benefit.retained_benefit_model import RetainedBenefitModel, make_settings
from ecological_models.retained_benefit.utils import analyze_r_sweep as an
from ecological_models.retained_benefit.utils import run_r_sweep as rs


def _model(r: float, bc: float, size: int = 5) -> RetainedBenefitModel:
    cfg = rs.run_config({"r": r, "benefit": bc * rs.COST, "cost": rs.COST}, seed=0, steps=1)
    cfg.update({"grid_width": size, "grid_height": size})
    return RetainedBenefitModel(make_settings(cfg))


@pytest.mark.parametrize("r", [0.0, 0.35, 1.0])
@pytest.mark.parametrize("bc", [3, 5, 8])
def test_direct_payoff_matches_model_lone_cooperator(r, bc):
    m = _model(r, bc)
    m.cooperation = np.zeros((5, 5))
    m.cooperation[2, 2] = 1.0
    m.lineage = np.arange(25, dtype=np.int32).reshape(5, 5)  # every site its own lineage
    fitness, _ = m._benefit_and_fitness()
    assert fitness[2, 2] - m.settings.base_fitness == pytest.approx(an.direct_payoff(bc, r, 1))


@pytest.mark.parametrize("r", [0.0, 0.35, 1.0])
@pytest.mark.parametrize("bc", [3, 5, 8])
def test_direct_payoff_matches_model_own_lineage(r, bc):
    m = _model(r, bc)
    m.cooperation = np.zeros((5, 5))
    m.cooperation[2, 2] = 1.0
    m.lineage = np.zeros((5, 5), dtype=np.int32)  # one lineage everywhere
    fitness, _ = m._benefit_and_fitness()
    assert fitness[2, 2] - m.settings.base_fitness == pytest.approx(an.direct_payoff(bc, r, 5))


def test_design_size_and_neutral_arm():
    arms = rs.build_arms()
    assert len(arms) == 3 * 11 + 1
    assert len(arms) * len(rs.SEEDS) == 340
    neutral = [a for a in arms if a["arm"] == "neutral"]
    assert len(neutral) == 1 and neutral[0]["benefit"] == 0.0 and neutral[0]["cost"] == 0.0
    assert sorted({a["r"] for a in arms if a["arm"] != "neutral"}) == rs.R_LEVELS


def test_run_config_changes_only_registered_keys():
    arm = {"r": 0.7, "benefit": 0.5, "cost": 0.1}
    cfg = rs.run_config(arm, seed=3, steps=17)
    changed = {k for k in cfg if cfg[k] != rs.DEMO_CONFIG.get(k)}
    assert changed <= {"retained_benefit_fraction", "cooperation_benefit", "cooperation_cost",
                       "simulation_steps", "random_seed"}
    assert cfg["random_seed"] == 3 and cfg["simulation_steps"] == 17


def test_simulate_is_deterministic_and_neutral_fitness_is_flat():
    cfg = rs.run_config({"r": 0.35, "benefit": 0.0, "cost": 0.0}, seed=1, steps=3)
    cfg.update({"grid_width": 8, "grid_height": 8})
    assert rs.simulate(cfg) == rs.simulate(cfg)
    m = RetainedBenefitModel(make_settings(cfg))
    fitness, _ = m._benefit_and_fitness()
    assert np.all(fitness == m.settings.base_fitness)


def test_summarize_tail_window():
    hist = {k: [0.0] * (rs.STEPS + 1) for k in
            ("step", "mean_cooperation", "var_cooperation", "local_assortment", "dominant_lineage_share", "lineage_count")}
    hist["step"] = [float(i) for i in range(rs.STEPS + 1)]
    hist["mean_cooperation"] = [1.0 if i > rs.STEPS - rs.TAIL_STEPS else 0.0 for i in range(rs.STEPS + 1)]
    row, traj = rs.summarize({"arm": "x", "bc": 3, "r": 0.0, "benefit": 0.3, "cost": 0.1}, 0, hist, 1.0)
    assert row["tail_mean_cooperation"] == 1.0 and row["steps"] == rs.STEPS
    assert [t["step"] for t in traj] == list(range(0, rs.STEPS + 1, rs.TRAJECTORY_INTERVAL))


def test_classify_rise_decline_flat_and_undefined():
    neutral = [0.10, 0.11, 0.09, 0.10, 0.105]
    assert an.classify([0.5, 0.52, 0.49, 0.51, 0.50], neutral)[0] == "rise"
    assert an.classify([0.01, 0.02, 0.015, 0.01, 0.012], neutral)[0] == "decline"
    assert an.classify([0.10, 0.11, 0.09, 0.10, 0.105], neutral)[0] == "flat"
    assert an.classify([0.2] * 5, [0.2] * 5)[0] == "flat"  # zero differences: undefined p is not significant


def test_unequal_constant_samples_are_undefined_not_significant():
    # floating-point variance of identical values can be a tiny nonzero number; must not yield a spurious rise
    assert math.isnan(an.paired_one_sided([0.3] * 10, [0.125] * 10, greater=True))
    assert an.classify([0.3] * 10, [0.125] * 10)[0] == "flat"


def _arm_value_rows(value_for, drop=None, tamper=None):
    rows = []
    for arm in rs.build_arms():
        if drop and arm["arm"] == drop:
            continue
        for s in rs.SEEDS:
            row = {"arm": arm["arm"], "bc": float(arm["bc"]), "r": arm["r"], "benefit": arm["benefit"],
                   "cost": arm["cost"], "seed": s, "steps": rs.STEPS,
                   "tail_mean_cooperation": value_for(arm) + random.Random(f"{arm['arm']}-{s}").gauss(0.0, 0.004)}
            rows.append(row)
    if tamper:
        tamper(rows)
    return rows


OK = {"replay_check": {"replay_exact": True}}


def _good(arm):
    if arm["arm"] == "neutral":
        return 0.10
    if arm["bc"] == 8:
        return 0.6
    if arm["bc"] == 3:
        return 0.05 + 0.4 * arm["r"]
    return 0.10


def test_analyze_all_met_and_support():
    res = an.analyze(_arm_value_rows(_good), OK)
    assert all(res["validity"].values())
    assert res["verdicts"] == {"P1": "met", "P2": "met", "P3": "met", "P4": "met"}
    assert res["interpretation"]["consistent_with_needing_retention_at_bc3"] == "consistent"
    json.dumps(res, allow_nan=False)  # strict JSON: no NaN anywhere


@pytest.mark.parametrize("which, value_for", [
    ("P1", lambda a: 0.10 if a["arm"] == "neutral" else (0.10 if a["bc"] == 8 and a["r"] == 0.5 else _good(a))),
    ("P2", lambda a: 0.10 if a["arm"] == "neutral" else (0.5 if a["arm"] == "bc3_r0.0" else _good(a))),
    ("P3", lambda a: 0.10 if a["arm"] == "neutral" else (0.45 if a["arm"] == "bc3_r0.0" else _good(a))),
    ("P4", lambda a: 0.10 if a["arm"] == "neutral" else (0.02 + 0.06 * a["r"] if a["bc"] == 3 else _good(a))),
])
def test_each_prediction_fails_independently(which, value_for):
    res = an.analyze(_arm_value_rows(value_for), OK)
    assert res["verdicts"][which] == "not met"
    assert res["interpretation"]["consistent_with_needing_retention_at_bc3"] == ("consistent" if which == "P1" else "not consistent")


def test_reduced_decline_alone_does_not_support_needs_retention():
    # r = 1 better than r = 0 but still below neutral: P3 met, P4 not met -> not supported
    res = an.analyze(_arm_value_rows(lambda a: 0.10 if a["arm"] == "neutral" else
                                     (0.01 + 0.05 * a["r"] if a["bc"] == 3 else _good(a))), OK)
    assert res["verdicts"]["P3"] == "met" and res["verdicts"]["P4"] == "not met"
    assert res["interpretation"]["consistent_with_needing_retention_at_bc3"] == "not consistent"


def test_r_star_null_endpoint_and_gap():
    def vf(a):
        if a["arm"] == "neutral":
            return 0.10
        if a["bc"] == 3:
            return 0.10  # never rises -> null
        if a["bc"] == 5:
            return 0.6 if a["r"] == 1.0 else 0.10  # only the endpoint -> 1.0
        return 0.6 if a["r"] != 0.3 else 0.10  # gap at 0.3 -> 0.4
    res = an.analyze(_arm_value_rows(vf), OK)
    assert res["exploratory_r_star"] == {"3": None, "5": 1.0, "8": 0.4}


@pytest.mark.parametrize("case", ["missing_neutral", "missing_arm", "missing_seed", "bad_metadata",
                                  "replay_string", "replay_false", "replay_null", "short_run", "blank_field"])
def test_invalid_inputs_gate_all_verdicts(case):
    drop, tamper, manifest = None, None, OK
    if case == "missing_neutral":
        drop = "neutral"
    elif case == "missing_arm":
        drop = "bc5_r0.3"
    elif case == "missing_seed":
        tamper = lambda rows: rows.pop()  # noqa: E731
    elif case == "bad_metadata":
        def tamper(rows):
            rows[0]["r"] = rows[0]["r"] + 0.05
    elif case == "replay_string":
        manifest = {"replay_check": {"replay_exact": "yes"}}
    elif case == "replay_false":
        manifest = {"replay_check": {"replay_exact": False}}
    elif case == "replay_null":
        manifest = {"replay_check": None}
    elif case == "short_run":
        def tamper(rows):
            rows[3]["steps"] = rs.STEPS - 1
    elif case == "blank_field":
        def tamper(rows):
            rows[4]["tail_mean_cooperation"] = an._num("")
            rows[5]["r"] = an._num("")
    res = an.analyze(_arm_value_rows(_good, drop=drop, tamper=tamper), manifest)
    assert not all(res["validity"].values())
    assert set(res["verdicts"].values()) == {"invalid"} and res["cells"] == {}


def test_replay_check_uses_exporter_rounding(tmp_path):
    from ecological_models.retained_benefit.utils.export_github_pages_demo import _round_number
    steps = list(range(rs.DEMO_CONFIG["simulation_steps"] + 1))
    raw = {"step": [float(s) for s in steps],
           "mean_cooperation": [0.1234567891 + 1e-9 * s for s in steps],
           "local_assortment": [0.5 + 1e-8 * s for s in steps],
           "dominant_lineage_share": [0.07] * len(steps)}
    pub = {"step_hist": steps, **{k + "_hist": [_round_number(v) for v in raw[k]]
                                  for k in ("mean_cooperation", "local_assortment", "dominant_lineage_share")}}
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(pub))
    assert rs.replay_check(raw, str(path))["replay_exact"] is True
    raw["mean_cooperation"][5] += 1e-3
    assert rs.replay_check(raw, str(path))["replay_exact"] is False


def test_run_sweep_short_jobs_with_workers(tmp_path, monkeypatch):
    """Exercise the worker pool and atomic output path with tiny jobs (replay check stubbed)."""
    monkeypatch.setattr(rs, "STEPS", 4)
    monkeypatch.setattr(rs, "replay_check", lambda: {"replay_exact": True})
    monkeypatch.setattr(rs, "set_niceness", lambda: 0)

    def tiny(arm, seed, steps):
        cfg = dict(rs.DEMO_CONFIG)
        cfg.update({"retained_benefit_fraction": arm["r"], "cooperation_benefit": arm["benefit"],
                    "cooperation_cost": arm["cost"], "simulation_steps": steps, "random_seed": seed,
                    "grid_width": 6, "grid_height": 6})
        return cfg
    monkeypatch.setattr(rs, "run_config", tiny)
    out = tmp_path / "r_sweep"
    arms = rs.build_arms()[:2] + [a for a in rs.build_arms() if a["arm"] == "neutral"]
    manifest = rs.run_sweep(out, arms, [0, 1], workers=2)
    assert manifest["n_runs"] == 6 and (out / "runs.csv").exists() and not (tmp_path / "r_sweep.partial").exists()
    with pytest.raises(SystemExit):
        rs.run_sweep(out, arms, [0, 1], workers=2)
    # a leftover partial bundle blocks a new run instead of being deleted
    out2 = tmp_path / "other"
    (tmp_path / "other.partial").mkdir()
    with pytest.raises(SystemExit):
        rs.run_sweep(out2, arms, [0, 1], workers=2)
    assert (tmp_path / "other.partial").exists()


def test_load_runs_tolerates_malformed_fields(tmp_path):
    path = tmp_path / "runs.csv"
    path.write_text("arm,bc,r,benefit,cost,seed,steps,tail_mean_cooperation\nneutral,0,0.35,0,0,x,,\n")
    row = an.load_runs(path)[0]
    assert row["seed"] is None and row["steps"] is None and math.isnan(row["tail_mean_cooperation"])


def test_direct_payoff_signs_used_in_predictions():
    # b/c = 8: positive in every lineage mix; b/c = 3, r = 0: negative in every mix.
    assert all(an.direct_payoff(8, r, n) > 0 for r in rs.R_LEVELS for n in range(1, 6))
    assert all(an.direct_payoff(3, 0.0, n) < 0 for n in range(1, 6))
    assert math.isclose(an.direct_payoff(5, 0.0, 5), 0.0, abs_tol=1e-12)
