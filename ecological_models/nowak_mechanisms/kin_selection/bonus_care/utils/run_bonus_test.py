#!/usr/bin/env python3
"""Bonus-care test (README pre-registration): step 0 grid, cost probe, main test. Writes data/*.{csv,json}.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.bonus_care.utils.run_bonus_test
"""
from __future__ import annotations

import csv
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.bonus_care.utils.run_bonus_test")

from ...config.kin_selection_config import resolve_config
from ...floor_control.utils.analysis import (
    frequency_change, hamilton, persists, pooled_hamilton, spreads, trait_change,
)
from ..bonus_model import BonusCareModel
from ..config.bonus_config import (
    ARMS, COHORT_BIRTH_STEPS, COMMON, COST, DATA_DIR, FEMALE_BIRTH_STEPS, MAIN_SEEDS, NO_HELPER, PROBE_FOUNDERS,
    PROBE_MIN_KAPPA, PROBE_SEEDS, REARING, STEP0_P0, STEP0_REARING, STEP0_REPRO_COSTS, STEP0_SEEDS, STEPM1_CELL,
    STEPM1_MAX_BACKGROUND, STEPM1_MU, STEPM1_PAIRS, STEPM1_SAMPLE_STEPS, STEPM1_SEEDS, STEPS, WINDOW, WORKERS,
)
from .analysis import best_case_margin, care_weighted_relatedness, choose_cell, choose_mu, kappa, score


def build(rearing, seed, cell, mu, *, care_counts=True, care_costs=True, extra=None):
    repro_cost, p0 = cell
    cfg = resolve_config({"random_seed": seed, "simulation_steps": STEPS, "write_latest_run": False,
                          "care_cost_per_unit": COST if care_costs else 0.0, **COMMON,
                          "reproduction_energy_cost": repro_cost, "base_juvenile_survival_probability": p0,
                          **REARING[rearing], **(extra or {})})
    return BonusCareModel(cfg, care_counts=care_counts, allele_mutation=mu)


def fecundity(m) -> float:
    f = m.matured_females(FEMALE_BIRTH_STEPS)
    return float(np.mean([x["births"] for x in f])) if f else float("nan")


def run_stepm1_one(job):
    mu, seed = job
    m = build("U", seed, STEPM1_CELL, mu, extra=NO_HELPER)
    rng = np.random.default_rng(10_000 + seed)
    samples = []
    while m.step_index < STEPS and m.individuals:
        m.step()
        if m.step_index in STEPM1_SAMPLE_STEPS:
            samples.append(m.mean_random_adult_relatedness(STEPM1_PAIRS, rng))
    survived = m.step_index == STEPS and bool(m.individuals)
    return {"mu": mu, "seed": seed, "survived": int(survived),
            "background_relatedness": float(np.nanmean(samples)) if samples and survived else float("nan"),
            "final_population": len(m.individuals)}


def run_step0_one(job):
    rearing, repro_cost, p0, seed, mu = job
    m = build(rearing, seed, (repro_cost, p0), mu, extra=NO_HELPER)
    m.run()
    pop = list(m.history["population"])
    return {"rearing": rearing, "repro_cost": repro_cost, "p0": p0, "seed": seed,
            "persists": int(persists(pop, WINDOW)), "final_population": pop[-1],
            "births_per_matured_female": fecundity(m)}


def run_probe_one(job):
    seed, cell, mu = job
    m = build("K", seed, cell, mu, care_counts=False, care_costs=True, extra=PROBE_FOUNDERS)
    m.run()
    pop = list(m.history["population"])
    return {"seed": seed, "persists": int(persists(pop, WINDOW)), "females": m.matured_females(FEMALE_BIRTH_STEPS)}


def run_main_one(job):
    arm, seed, cell, mu = job
    rearing, acts = ARMS[arm]
    m = build(rearing, seed, cell, mu, care_counts=acts, care_costs=acts)
    m.run()
    h = m.history
    pop = list(h["population"])
    ok = persists(pop, WINDOW)
    dt, df = trait_change(h), frequency_change(h)
    cohort = m.cohort(COHORT_BIRTH_STEPS)
    return {"arm": arm, "seed": seed, "persists": int(ok), "spreads": int(spreads(ok, dt, df)),
            "trait_change": dt, "frequency_change": df, "final_population": pop[-1],
            "steps_at_cap": int(sum(1 for p in pop[1:] if p >= int(m.config["max_population"]))),
            "births": int(sum(h["births"])), "births_per_matured_female": fecundity(m),
            "saturated_fraction": m.saturated_checks / m.juvenile_checks if m.juvenile_checks else float("nan"),
            "care_weighted_relatedness": care_weighted_relatedness(h["total_care"][1:], h["mean_care_relatedness"][1:]),
            "household_care_fraction": float(np.nanmean(np.asarray(h["household_care_fraction"][1:], float)))
            if len(pop) > 1 else float("nan"),
            "cohort_n": len(cohort), "cohort_excluded_no_check": m.excluded_from_cohort(COHORT_BIRTH_STEPS),
            "ham": hamilton(cohort), "cohort": cohort,
            "h_series": [float(x) for x in h["mean_helping_trait"][::20]]}


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    out = Path(DATA_DIR)
    out.mkdir(parents=True, exist_ok=True)
    with Pool(WORKERS) as pool:
        # step -1 (amendment 1): allele mutation rate
        sm1 = pool.map(run_stepm1_one, [(mu, s) for mu in STEPM1_MU for s in STEPM1_SEEDS])
        write_csv(out / "stepm1_runs.csv", sm1)
        mu = choose_mu(sm1, STEPM1_MU, len(STEPM1_SEEDS), STEPM1_MAX_BACKGROUND)
        (out / "stepm1_result.json").write_text(json.dumps({"mu_star": mu, "runs": sm1}, indent=1))
        print("step -1 mu* =", mu, flush=True)
        if mu is None:
            raise SystemExit("no allele mutation rate keeps background relatedness low: the amendment says stop")
        # step 0
        jobs = [(q, c, p, s, mu) for q in STEP0_REARING for c in STEP0_REPRO_COSTS for p in STEP0_P0 for s in STEP0_SEEDS]
        s0 = pool.map(run_step0_one, jobs, chunksize=2)
        write_csv(out / "step0_runs.csv", s0)
        cell = choose_cell(s0, STEP0_REPRO_COSTS, STEP0_P0, STEP0_REARING, len(STEP0_SEEDS))
        table = {f"{q}/cost{c}/p0{p}": sum(r["persists"] for r in s0
                                          if r["rearing"] == q and r["repro_cost"] == c and r["p0"] == p)
                 for q in STEP0_REARING for c in STEP0_REPRO_COSTS for p in STEP0_P0}
        fec = {f"{q}/cost{c}/p0{p}": float(np.nanmean([r["births_per_matured_female"] for r in s0
                                                       if r["rearing"] == q and r["repro_cost"] == c and r["p0"] == p]))
               for q in STEP0_REARING for c in STEP0_REPRO_COSTS for p in STEP0_P0}
        result = {"mu_star": mu, "cell": cell, "persisting_of_20": table, "births_per_matured_female": fec}
        print("step 0 cell:", cell, flush=True)
        if cell is None:
            (out / "step0_result.json").write_text(json.dumps(result, indent=1))
            raise SystemExit("no cell keeps the no-helper control alive in all seeds: the design says stop")
        # cost probe
        probe = pool.map(run_probe_one, [(s, cell, mu) for s in PROBE_SEEDS])
        k = kappa([p["females"] for p in probe])
        result["probe"] = {**k, "persisting_of_20": sum(p["persists"] for p in probe),
                           "best_case_margin": best_case_margin(cell[1], k["kappa"])}
        result["probe"]["theory_predicts_spread"] = bool(result["probe"]["best_case_margin"] > 0)
        (out / "step0_result.json").write_text(json.dumps(result, indent=1))
        print("probe:", json.dumps(result["probe"]), flush=True)
        if not k["kappa"] >= PROBE_MIN_KAPPA:
            raise SystemExit(f"kappa {k['kappa']:.3f} < {PROBE_MIN_KAPPA}: helping is nearly free, the design says stop")
        # main test
        rows = pool.map(run_main_one, [(a, s, cell, mu) for a in ARMS for s in MAIN_SEEDS], chunksize=2)
    by_arm = {a: [r for r in rows if r["arm"] == a] for a in ARMS}
    rng = np.random.default_rng(0)
    verdict = {"mu_star": mu, "cell": cell, **score(by_arm, rng)}
    keys = ("final_population", "steps_at_cap", "births", "births_per_matured_female", "saturated_fraction",
            "care_weighted_relatedness", "household_care_fraction", "cohort_n", "cohort_excluded_no_check")
    verdict["descriptive"] = {a: {k2: float(np.nanmean([r[k2] for r in v])) for k2 in keys} for a, v in by_arm.items()}
    verdict["pooled_hamilton"] = {a: pooled_hamilton(by_arm[a], rng) for a in ("K", "U")}
    verdict["mean_h_every_20_steps"] = {
        a: [float(np.nanmean([r["h_series"][t] for r in v if t < len(r["h_series"])]))
            for t in range(max(len(r["h_series"]) for r in v))] for a, v in by_arm.items()}
    flat = [{**{k2: v for k2, v in r.items() if k2 not in ("ham", "cohort", "h_series")},
             **{f"ham_{k2}": r["ham"].get(k2, float("nan")) for k2 in ("n", "analysable", "c", "b_s", "r", "margin")}}
            for r in rows]
    write_csv(out / "main_runs.csv", flat)
    (out / "main_verdict.json").write_text(json.dumps(verdict, indent=1, default=float))
    print(json.dumps({k2: verdict[k2] for k2 in ("mu_star", "cell", "H0", "H0b", "H1", "H1b", "H2", "H3", "H3_outcome")}, indent=1))


if __name__ == "__main__":
    main()
