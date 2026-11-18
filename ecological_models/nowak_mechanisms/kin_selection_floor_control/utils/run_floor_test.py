#!/usr/bin/env python3
"""Step 0 (floor calibration) and the main test (README). Writes data/step0_*.{csv,json}, data/main_*.{csv,json}.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_floor_control.utils.run_floor_test
"""
from __future__ import annotations

import csv
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection_floor_control.utils.run_floor_test")

from ...kin_selection.config.kin_selection_config import resolve_config
from ..config.floor_config import (
    ARMS, COHORT_BIRTH_STEPS, COST, DATA_DIR, MAIN_SEEDS, NO_HELPER, REARING, STEP0_FLOORS, STEP0_REARING,
    STEP0_SEEDS, STEPS, WINDOW, WORKERS,
)
from ..floor_model import FloorKinSelectionModel
from .analysis import frequency_change, hamilton, persists, pooled_hamilton, score, spreads, trait_change


def build(rearing, seed, floor, neutral, extra=None):
    cfg = resolve_config({"random_seed": seed, "simulation_steps": STEPS, "write_latest_run": False,
                          "care_cost_per_unit": 0.0 if neutral else COST, **REARING[rearing], **(extra or {})})
    return FloorKinSelectionModel(cfg, floor=floor, neutral=neutral)


def run_step0_one(job):
    rearing, floor, seed = job
    m = build(rearing, seed, floor, False, NO_HELPER)
    m.run()
    pop = list(m.history["population"])
    return {"rearing": rearing, "floor": floor, "seed": seed, "persists": int(persists(pop, WINDOW)),
            "final_population": pop[-1]}


def choose_floor(rows) -> float | None:
    for f in STEP0_FLOORS:
        if all(sum(r["persists"] for r in rows if r["floor"] == f and r["rearing"] == q) == len(STEP0_SEEDS)
               for q in STEP0_REARING):
            return f
    return None


def run_main_one(job):
    arm, seed, f_star = job
    rearing, uses_floor, neutral = ARMS[arm]
    m = build(rearing, seed, f_star if uses_floor else 0.0, neutral)
    m.run()
    h = m.history
    pop = list(h["population"])
    ok = persists(pop, WINDOW)
    dt, df = trait_change(h), frequency_change(h)
    cohort = m.cohort(COHORT_BIRTH_STEPS)
    ham = hamilton(cohort)
    return {"arm": arm, "seed": seed, "persists": int(ok), "spreads": int(spreads(ok, dt, df)),
            "trait_change": dt, "frequency_change": df, "final_population": pop[-1],
            "steps_at_cap": int(sum(1 for p in pop[1:] if p >= int(m.config["max_population"]))),
            "births": int(sum(h["births"])),
            "male_fraction_end": float(np.mean([i.sex == "M" for i in m.individuals])) if m.individuals else float("nan"),
            "saturated_fraction": m.saturated_checks / m.juvenile_checks if m.juvenile_checks else float("nan"),
            "mean_care_relatedness": float(np.nanmean(np.asarray(h["mean_care_relatedness"][1:], float)))
            if len(pop) > 1 else float("nan"),
            "cohort_n": len(cohort), "cohort_excluded_no_check": m.excluded_from_cohort(COHORT_BIRTH_STEPS),
            "ham": ham, "cohort": cohort,
            "h_series": [float(x) for x in h["mean_helping_trait"][::10]]}


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    out = Path(DATA_DIR)
    with Pool(WORKERS) as pool:
        s0 = pool.map(run_step0_one, [(q, f, s) for q in STEP0_REARING for f in STEP0_FLOORS for s in STEP0_SEEDS])
        write_csv(out / "step0_runs.csv", s0)
        f_star = choose_floor(s0)
        table = {f"{q}/{f}": sum(r["persists"] for r in s0 if r["rearing"] == q and r["floor"] == f)
                 for q in STEP0_REARING for f in STEP0_FLOORS}
        (out / "step0_result.json").write_text(json.dumps({"f_star": f_star, "persisting_of_20": table}, indent=1))
        print("step 0:", json.dumps(table), "f* =", f_star)
        if f_star is None:
            raise SystemExit("no floor keeps the no-helper control alive in all seeds: the design says stop")
        rows = pool.map(run_main_one, [(a, s, f_star) for a in ARMS for s in MAIN_SEEDS], chunksize=2)
    main_by_arm = {a: [r for r in rows if r["arm"] == a] for a in ARMS}
    rng = np.random.default_rng(0)
    verdict = {"f_star": f_star, **score(main_by_arm, rng)}
    verdict["descriptive"] = {
        a: {k: float(np.nanmean([r[k] for r in v])) for k in
            ("final_population", "steps_at_cap", "births", "male_fraction_end", "saturated_fraction",
             "mean_care_relatedness", "cohort_n", "cohort_excluded_no_check")}
        for a, v in main_by_arm.items()}
    verdict["descriptive_counts"] = {a: {"persist": sum(r["persists"] for r in v), "spread": sum(r["spreads"] for r in v)}
                                     for a, v in main_by_arm.items()}
    verdict["pooled_hamilton"] = {a: pooled_hamilton(main_by_arm[a], rng) for a in ("K", "U")}
    verdict["mean_h_every_10_steps"] = {
        a: [float(np.nanmean([r["h_series"][t] for r in v if t < len(r["h_series"])]))
            for t in range(max(len(r["h_series"]) for r in v))] for a, v in main_by_arm.items()}
    flat = [{**{k: v for k, v in r.items() if k not in ("ham", "cohort", "h_series")},
             **{f"ham_{k}": v for k, v in r["ham"].items()}} for r in rows]
    for r in flat:
        for k in ("ham_b_h", "ham_c", "ham_b_s", "ham_r", "ham_margin"):
            r.setdefault(k, float("nan"))
    write_csv(out / "main_runs.csv", flat)
    (out / "main_verdict.json").write_text(json.dumps(verdict, indent=1, default=float))
    print(json.dumps({k: verdict[k] for k in ("f_star", "H0", "H1", "H1b", "H2", "H3", "H3_outcome")}, indent=1))


if __name__ == "__main__":
    main()
