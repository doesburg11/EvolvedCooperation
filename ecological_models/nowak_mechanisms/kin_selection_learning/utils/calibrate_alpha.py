#!/usr/bin/env python3
"""Learning-rate calibration (README "Learning-rate calibration", amended), stand-alone, no model outcome data.

A toy household with the model's care and survival rules at cost c* (from step0_result.json): ALPHA_TOY_CARERS
learner(s) care for ALPHA_TOY_JUVENILES juveniles each step (equal split); each juvenile dies with the model's
survival probability given its care; dead juveniles are replaced so the household stays the same size. One learner
means the test measures learning speed under death noise, not free riding (which is part of the experiment).

alpha = the smallest candidate at which, averaged over REPLICATES households after ALPHA_STEPS steps,
(i) learners with k = rare_helper_trait_value starting at initial_effort end within ALPHA_TOLERANCE of the toy's
reward-maximizing effort e*, and (ii) learners with k = 0 starting at 0.5 end below ALPHA_LOW_EFFORT.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_learning.utils.calibrate_alpha
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_learning.utils.calibrate_alpha")

from ...kin_selection.config.kin_selection_config import resolve_config
from ..config.learning_config import (
    ALPHA_CANDIDATES,
    ALPHA_LOW_EFFORT,
    ALPHA_STEPS,
    ALPHA_TOLERANCE,
    ALPHA_TOY_CARERS,
    ALPHA_TOY_JUVENILES,
    DATA_DIR,
    LEARNING,
)

REPLICATES = 400


def survival(care, cfg):
    return np.clip(cfg["base_juvenile_survival_probability"]
                   + cfg["care_benefit_to_survival"] * np.minimum(care, cfg["care_saturation"]), 0, 1)


def expected_reward(a, k, cfg, n_carers=ALPHA_TOY_CARERS, n_juv=ALPHA_TOY_JUVENILES):
    """Expected reward of one learner when all n_carers act with effort a (single learner: its own optimum)."""
    care = n_carers * a * cfg["care_capacity_per_helper"] / n_juv
    deaths = n_juv * (1 - survival(care, cfg))
    return -cfg["care_cost_per_unit"] * a * cfg["care_capacity_per_helper"] - k * LEARNING["juvenile_energy_value"] * deaths


def best_effort(k, cfg):
    grid = np.linspace(0, 1, 1001)
    return float(grid[np.argmax(expected_reward(grid, k, cfg))])


def simulate(alpha, k, e_start, cfg, rng, n_carers=ALPHA_TOY_CARERS, n_juv=ALPHA_TOY_JUVENILES):
    sigma, beta, value = LEARNING["exploration_stddev"], LEARNING["baseline_rate"], LEARNING["juvenile_energy_value"]
    cap, cpu = cfg["care_capacity_per_helper"], cfg["care_cost_per_unit"]
    stake = cpu * cap + k * value  # as in the model
    e = np.full((REPLICATES, n_carers), float(e_start))
    b = None
    for _ in range(ALPHA_STEPS):
        eps = rng.normal(0, sigma, e.shape)
        a = np.clip(e + eps, 0, 1)
        care = (a * cap).sum(1, keepdims=True) / n_juv
        deaths = (rng.random((REPLICATES, n_juv)) > survival(care, cfg)).sum(1, keepdims=True)
        r = -cpu * a * cap - k * value * deaths
        if b is None:  # as in the model: the first reward only sets the baseline
            b = r.copy()
            continue
        e = np.clip(e + alpha * ((r - b) / stake) * eps / sigma, 0, 1)
        b = b + beta * (r - b)
    return float(e.mean())


def calibrate(c_star, rng):
    cfg = resolve_config({"care_cost_per_unit": c_star})
    k_high = float(cfg["rare_helper_trait_value"])
    target = best_effort(k_high, cfg)
    rows, chosen = [], None
    for alpha in ALPHA_CANDIDATES:
        high = simulate(alpha, k_high, LEARNING["initial_effort"], cfg, rng)
        low = simulate(alpha, 0.0, 0.5, cfg, rng)
        ok = abs(high - target) <= ALPHA_TOLERANCE and low < ALPHA_LOW_EFFORT
        rows.append({"alpha": alpha, "effort_k_high": high, "effort_k0": low, "passes": ok})
        if ok and chosen is None:
            chosen = alpha
    return {"c_star": c_star, "k_high": k_high, "target_effort": target, "rows": rows, "alpha": chosen}


def main() -> None:
    out = Path(DATA_DIR)
    step0 = json.loads((out / "step0_result.json").read_text())
    if step0["c_star"] is None:
        raise SystemExit("step 0 found no c*; the design says stop")
    result = calibrate(step0["c_star"], np.random.default_rng(0))
    (out / "alpha_result.json").write_text(json.dumps(result, indent=1))
    print(f"c* {result['c_star']}, target effort e* = {result['target_effort']:.3f}")
    for r in result["rows"]:
        print(f"alpha {r['alpha']:<6}: k high -> {r['effort_k_high']:.3f}, k=0 -> {r['effort_k0']:.3f}"
              f"  {'PASS' if r['passes'] else ''}")
    print("alpha =", result["alpha"])


if __name__ == "__main__":
    main()
