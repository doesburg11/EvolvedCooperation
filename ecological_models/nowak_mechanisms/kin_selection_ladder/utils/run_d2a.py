#!/usr/bin/env python3
"""Diagnostic D2a (README pre-registration 422ccd6): where does selection on h come from in A-global?

Exact expected fitness per start-of-step occupant i: w_i = (1 - d_i) + sum_{k: i in C_k} d_k p_ik, so that
cov(h, w) (population covariance) is the expected change in mean h before mutation, given state and candidate sets.
Measurements draw no random numbers; the global arm's candidate sets and the realized parents are recorded by
wrapping the engine's own functions.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_d2a
"""
from __future__ import annotations

import contextlib
import io
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_ladder.utils.run_d2a")

from .. import ladder_model as lm
from ..config.ladder_config import DATA_DIR, WORKERS, run_config, step1c_arms, step2a_arms

D2A_STEPS = 2000
D2A_SEEDS = list(range(5))
D2A_SAMPLES = list(range(250, D2A_STEPS + 1, 250))
ASSOC = 0.02


def d2a_arms():
    a, l2 = step2a_arms(1), step1c_arms(2)
    return {"A-global": a["A-global"], "A-local": a["A-local"], "L2-global": l2["L2-global"]}


def payoff(eng):
    """Recompute the engine's payoff x and birth fitness W from the start-of-step state (no draws)."""
    cfg, mech = eng.cfg, eng.mechanism
    expressed = eng.expressed_trait()
    K = mech.build_positive_kernel(eng.neighbor_mask, eng.lineage, eng.extra_state, cfg)
    Kn = mech.build_negative_kernel(eng.neighbor_mask, eng.lineage, eng.extra_state, cfg)
    W = float(cfg["base_fitness"]) + K.T @ mech.compute_positive_output(expressed, eng.extra_state, cfg) \
        - Kn.T @ mech.compute_negative_output(expressed, eng.extra_state, cfg) \
        - mech.compute_private_cost(expressed, eng.extra_state, cfg)
    return W - float(cfg["base_fitness"]), W


def birth_probs(values, temperature):
    z = (values - values.max()) / max(temperature, 1e-9)
    e = np.exp(z)
    return e / e.sum()


def expected_fitness(d, W, cands, lam, temperature, n):
    surv = 1.0 - d
    off = np.zeros(n)
    for k, c in enumerate(cands):
        p = birth_probs((1.0 - lam) * W[c], temperature)
        np.add.at(off, c, d[k] * p)
    return surv, off


def cov_contrib(h, y, mask=None):
    """(1/n) sum over i in mask of (h_i - mean h)(y_i - mean y): class parts add up to the total covariance."""
    dev = (h - h.mean()) * (y - y.mean())
    return float(dev[mask].sum() / len(h)) if mask is not None else float(dev.mean())


def run_one(job):
    arm, mech, updates, seed = job
    mech = dict(mech)
    eng = lm.make_engine(run_config(seed, updates, D2A_STEPS), replacement=mech.pop("replacement"),
                         death=mech.pop("death"), lam=mech.pop("lam"), norm=mech.pop("norm", "local"), **mech)
    rec = {}
    real_draw, real_repl = eng.draw_candidates, lm.local_replacement_step

    def draw():
        rec["cands"] = real_draw()
        return rec["cands"]

    def repl(*args):
        out = real_repl(*args)
        rec["parents"] = out[2]
        return out

    eng.draw_candidates = draw
    lm.local_replacement_step = repl
    has_age = hasattr(eng, "age")
    acc = {k: 0.0 for k in ("surv_part", "birth_part", "surv_juv", "surv_adult", "birth_juv", "birth_adult",
                            "real_survivor", "real_parent", "real_mutation", "real_total")}
    assoc = {"pearson_all": [], "spearman_all": [], "spearman_adult": [], "spearman_juv": []}
    max_d_err = 0.0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            while eng.step_index < D2A_STEPS:
                h0 = eng.h.copy()
                juv = (eng.age < eng.juvenile_period) if has_age else np.zeros(eng.n_sites, bool)
                x, W = payoff(eng)
                d = eng.death_probabilities(x)
                eng.step()
                max_d_err = max(max_d_err, float(np.abs(eng.last_death_prob - d).max()))
                cands = rec["cands"] if eng.global_candidates else eng.neighbor_indices
                surv, off = expected_fitness(d, W, cands, eng.lam, eng.temperature, eng.n_sites)
                acc["surv_part"] += cov_contrib(h0, surv)
                acc["birth_part"] += cov_contrib(h0, off)
                acc["surv_juv"] += cov_contrib(h0, surv, juv)
                acc["surv_adult"] += cov_contrib(h0, surv, ~juv)
                acc["birth_juv"] += cov_contrib(h0, off, juv)
                acc["birth_adult"] += cov_contrib(h0, off, ~juv)
                # realized accounting
                s = eng.last_survivors
                D = 1.0 - s.mean()
                H = h0.mean()
                acc["real_survivor"] += (1 - D) * (h0[s].mean() - H) if s.any() else 0.0
                if D > 0:
                    dead = ~s
                    mp = h0[rec["parents"][dead]].mean()
                    acc["real_parent"] += D * (mp - H)
                    acc["real_mutation"] += D * (eng.h[dead].mean() - mp)
                acc["real_total"] += eng.h.mean() - H
                if eng.step_index in D2A_SAMPLES:
                    assoc["pearson_all"].append(float(np.corrcoef(h0, x)[0, 1]) if x.std() > 0 else float("nan"))
                    assoc["spearman_all"].append(float(spearmanr(h0, x).statistic))
                    for name, m in (("spearman_adult", ~juv), ("spearman_juv", juv)):
                        ok = m.sum() > 2 and x[m].std() > 0 and h0[m].std() > 0
                        assoc[name].append(float(spearmanr(h0[m], x[m]).statistic) if ok else float("nan"))
    finally:
        lm.local_replacement_step = real_repl
    acc["expected_total"] = acc["surv_part"] + acc["birth_part"]
    return {"arm": arm, "seed": seed, **acc, "max_death_prob_error": max_d_err, "final_mean_h": float(eng.h.mean()),
            **{k: float(np.nanmean(v)) if np.isfinite(v).any() else float("nan") for k, v in assoc.items()}}


def classify(rows_by_arm):
    a_local_ref = abs(np.mean([r["expected_total"] for r in rows_by_arm["A-local"]]))
    out = {}
    for arm, rows in rows_by_arm.items():
        tot = [r["expected_total"] for r in rows]
        if all(t > 0 for t in tot):
            sel = "positive"
        elif all(abs(t) < 0.1 * a_local_ref for t in tot):
            sel = "absent"
        else:
            sel = "mixed"
        part = None
        if sel == "positive":
            surv_wins = sum(r["surv_part"] > 0 and r["surv_part"] > r["birth_part"] for r in rows)
            birth_wins = sum(r["birth_part"] > 0 and r["birth_part"] > r["surv_part"] for r in rows)
            part = "survival" if surv_wins >= 4 else ("birth" if birth_wins >= 4 else "both")
        sp = {c: [r[c] for r in rows] for c in ("spearman_all", "spearman_adult", "spearman_juv")}
        present = any(all(v > ASSOC for v in sp[c]) for c in ("spearman_all", "spearman_adult"))
        absent = all(len(sp[c]) == len(rows) and all(np.isfinite(v) and abs(v) <= ASSOC for v in sp[c]) for c in sp)
        assoc = "present" if present else ("absent" if absent else "mixed")
        out[arm] = {"expected_selection": sel, "part": part, "association": assoc}
    a = out["A-global"]
    if a["expected_selection"] == "positive" and a["association"] == "present":
        reading = "selection through an association of own helping with its payoff that the overall neighbour correlation misses"
    elif a["expected_selection"] == "positive" and a["association"] == "absent":
        reading = "a path these measures do not capture: audit the code before interpreting"
    elif a["expected_selection"] == "positive":
        reading = "expected selection positive, association mixed: no registered reading"
    else:
        reading = "step-2a spread may be drift-like or lagged"
    return out, reading


def main():
    out = Path(DATA_DIR)
    arms = d2a_arms()
    with Pool(WORKERS) as pool:
        rows = pool.map(run_one, [(a, m, u, s) for a, (m, u) in arms.items() for s in D2A_SEEDS])
    by_arm = {a: [r for r in rows if r["arm"] == a] for a in arms}
    if max(r["max_death_prob_error"] for r in rows) > 1e-12:
        raise SystemExit("recomputed death probabilities differ from the engine's: code check failed")
    cls, reading = classify(by_arm)
    keys = [k for k in rows[0] if k not in ("arm", "seed")]
    verdict = {"classification": cls, "A_global_reading": reading,
               "means": {a: {k: float(np.mean([r[k] for r in v])) for k in keys} for a, v in by_arm.items()},
               "runs": rows}
    (out / "d2a_verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({"classification": cls, "reading": reading}, indent=1))
    for a, m in verdict["means"].items():
        print(a, {k: round(v, 5) for k, v in m.items()})


if __name__ == "__main__":
    main()
