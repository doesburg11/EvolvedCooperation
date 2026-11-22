#!/usr/bin/env python3
"""Ladder steps 0 and 1 (README pre-registration). Writes data/*.csv and data/verdict.json.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_steps01
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.ladder.utils.run_steps01")

from ..config.ladder_config import (
    ATTEMPT2_MU_DIVISOR, BELOW_B, CAL_MU, CAL_PAIR_SEED, CAL_RANDOM_PAIRS, CAL_SAMPLE_STEPS, CAL_SEEDS, COMMON,
    DATA_DIR, NEUTRAL, NOBIAS_TRIGGER, RARE, SEEDS, STEP0_ARMS, STEP0_LOW_ARMS, STEPS, SUCCESS_FINAL_MEAN_TRAIT,
    UNIFORM, WORKERS, run_config,
)
from ..ladder_model import make_engine
from .analysis import check_seeds, choose_mu, score_t0a, score_t0b, score_t1


def run_arm_seed(job):
    arm, mech, updates, seed = job
    eng = make_engine(run_config(seed, updates), **mech)
    with contextlib.redirect_stdout(io.StringIO()):
        payload = eng.run()
    final = float(payload["final_mean_trait"])
    # history[t] is the state after t updates (recorded before update t+1); steps 50..950, then the final state
    traj = [payload["history"][t]["mean_trait"] for t in range(50, STEPS, 50)] + [final]
    return {"arm": arm, "seed": seed, "final_mean_trait": final, "success": int(final >= SUCCESS_FINAL_MEAN_TRAIT),
            "final_identity_count": int(payload["final_identity_count"]), "traj_every_50": traj}


def edge_pairs(eng):
    i, j = np.nonzero(np.triu(eng.neighbor_mask, k=1))
    return i, j


def random_pairs(eng, n, seed):
    rng = np.random.default_rng(seed)
    out = set()
    while len(out) < n:
        a, b = (int(x) for x in rng.integers(0, eng.n_sites, 2))
        if a == b or eng.neighbor_mask[a, b]:
            continue
        out.add((min(a, b), max(a, b)))
    arr = np.array(sorted(out))
    return arr[:, 0], arr[:, 1]


def run_cal_one(job):
    mu, seed = job
    eng = make_engine(run_config(seed, NEUTRAL), kin="label", track_genome=True, mu=mu)
    ei, ej = edge_pairs(eng)
    ri, rj = random_pairs(eng, CAL_RANDOM_PAIRS, CAL_PAIR_SEED)
    g_c, l_c = [], []
    with contextlib.redirect_stdout(io.StringIO()):
        for _ in range(STEPS):
            eng.step()
            if eng.step_index in CAL_SAMPLE_STEPS:
                g, lab = eng.extra_state["genome"], eng.lineage
                g_c.append(float((g[ei] == g[ej]).mean() - (g[ri] == g[rj]).mean()))
                l_c.append(float((lab[ei] == lab[ej]).mean() - (lab[ri] == lab[rj]).mean()))
    assert len(g_c) == len(CAL_SAMPLE_STEPS)
    return {"mu": mu, "seed": seed, "genome_contrast": float(np.mean(g_c)), "label_contrast": float(np.mean(l_c)),
            "genome_traj": g_c, "label_traj": l_c, "final_lineage": eng.lineage.tolist()}


def by_arm(rows, arms):
    out = {a: [r for r in rows if r["arm"] == a] for a in arms}
    for a, v in out.items():
        check_seeds(v, SEEDS)
    return out


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in rows[0] if not isinstance(rows[0][k], list)], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def mean_traj(rows):
    return [float(np.mean([r["traj_every_50"][t] for r in rows])) for t in range(len(rows[0]["traj_every_50"]))]


def main():
    out = Path(DATA_DIR)
    out.mkdir(parents=True, exist_ok=True)
    verdict = {}
    all_rows = []
    with Pool(WORKERS) as pool:
        rows = pool.map(run_arm_seed, [(a, m, u, s) for a, (m, u) in STEP0_ARMS.items() for s in SEEDS])
        all_rows += rows
        arms = by_arm(rows, STEP0_ARMS)
        verdict["T0a"] = score_t0a(arms)
        if sum(r["success"] for r in arms["S-nobias"]) >= NOBIAS_TRIGGER:
            low = pool.map(run_arm_seed, [(a, m, u, s) for a, (m, u) in STEP0_LOW_ARMS.items() for s in SEEDS])
            all_rows += low
            arms.update(by_arm(low, STEP0_LOW_ARMS))
        verdict["T0b"] = score_t0b(arms, NOBIAS_TRIGGER)
        verdict["step0_descriptive"] = {a: {"successes": sum(r["success"] for r in v),
                                            "mean_final_h": float(np.mean([r["final_mean_trait"] for r in v])),
                                            "mean_final_lineages": float(np.mean([r["final_identity_count"] for r in v])),
                                            "mean_h_every_50": mean_traj(v)} for a, v in arms.items()}
        print("T0a", verdict["T0a"]["met"], "T0b", verdict["T0b"]["met"], flush=True)
        if verdict["T0b"]["met"]:
            B = verdict["T0b"]["scored_at_B"]
            cal = pool.map(run_cal_one, [(mu, s) for mu in CAL_MU for s in CAL_SEEDS])
            for s in CAL_SEEDS:  # pre-registered: identical genealogy across mu for a seed
                ref = [r["final_lineage"] for r in cal if r["seed"] == s]
                if any(x != ref[0] for x in ref):
                    raise RuntimeError(f"seed {s}: genealogy differs across mu")
            write_csv(out / "step1_cal.csv", cal)
            verdict["step1_cal"] = choose_mu(cal, CAL_MU)
            verdict["step1_cal"]["trajectories"] = {
                f"mu{mu}": [float(np.mean([r["genome_traj"][t] for r in cal if r["mu"] == mu])) for t in range(len(CAL_SAMPLE_STEPS))]
                for mu in CAL_MU}
            verdict["step1_cal"]["trajectories"]["label"] = [
                float(np.mean([r["label_traj"][t] for r in cal])) for t in range(len(CAL_SAMPLE_STEPS))]
            min_kin = 12 if B == 0.6 else 15
            mu = verdict["step1_cal"]["mu_star"]
            for attempt in (1, 2):
                g_arms = {
                    "G-kin": ({"self_in_routing": False, "kin": "genome", "mu": mu}, {**RARE, "B_plus_scale": B}),
                    "G-nobias": ({"self_in_routing": False, "kin": "none"}, {**RARE, **UNIFORM, "B_plus_scale": B}),
                    "G-below": ({"self_in_routing": False, "kin": "genome", "mu": mu}, {**COMMON, "B_plus_scale": BELOW_B}),
                }
                g_rows = pool.map(run_arm_seed, [(a, m, u, s) for a, (m, u) in g_arms.items() for s in SEEDS])
                for r in g_rows:
                    r["arm"] = f"{r['arm']}@att{attempt}"
                all_rows += g_rows
                ga = {a.split("@")[0]: v for a, v in by_arm(g_rows, {f"{a}@att{attempt}" for a in g_arms}).items()}
                t1 = score_t1(ga, min_kin)
                t1["mu"] = mu
                t1["descriptive"] = {a: {"mean_final_h": float(np.mean([r["final_mean_trait"] for r in v])),
                                         "mean_h_every_50": mean_traj(v)} for a, v in ga.items()}
                verdict[f"T1_attempt{attempt}"] = t1
                print(f"T1 attempt {attempt} (mu {mu}):", t1["met"], flush=True)
                if t1["met"]:
                    break
                mu = mu / ATTEMPT2_MU_DIVISOR
    write_csv(out / "runs.csv", all_rows)
    (out / "verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({k: (v.get("met") if isinstance(v, dict) else v) for k, v in verdict.items()}, indent=1))


if __name__ == "__main__":
    main()
