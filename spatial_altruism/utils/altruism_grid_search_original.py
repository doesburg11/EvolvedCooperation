#!/usr/bin/env python3
"""
Baseline coexistence sweep for the spatial altruism model.

Edit the grid block in this file and the active defaults in
`spatial_altruism/config/altruism_config.py`, then run from the repo root:
  ./.conda/bin/python -m spatial_altruism.utils.altruism_grid_search_original
"""

import csv
import itertools
import os

import numpy as np
import pandas as pd

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m spatial_altruism.utils.altruism_grid_search_original'."
    )

from ..altruism_model import AltruismModel, make_params


def run_and_report(params, steps=[1000]):
    model = AltruismModel(params)
    results = {}
    max_step = max(steps)

    for t in range(1, max_step + 1):
        model.go()
        if t in steps:
            pink, green, black = model.counts()
            pop = pink + green
            total = pink + green + black
            results[t] = {
                "altruists": pink,
                "%_altruists": 100 * pink / pop if pop > 0 else 0,
                "selfish": green,
                "%_selfish": 100 * green / pop if pop > 0 else 0,
                "black": black,
                "%_black": 100 * black / total if total > 0 else 0,
                "pop": pop,
                "total": total,
            }
    return results


def main():
    base_params = make_params()
    if base_params.model_variant != "steady_state":
        raise SystemExit(
            "spatial_altruism.utils.altruism_grid_search_original targets the "
            "steady-state disease/harshness parameter space. Set "
            "model_variant='steady_state' or create a culling-specific sweep."
        )

    def clamp(val):
        return min(max(val, 0.00), 1.0 - 0.00)

    grid = {
        "benefit_from_altruism": [clamp(round(x, 2)) for x in np.arange(0.00, 1.00 + 0.01, 0.01)],
        "cost_of_altruism": [clamp(round(x, 2)) for x in np.arange(0.00, 0.35 + 0.01, 0.01)],
        "disease": [0.25],
        "harshness": [
            0.85,
            0.86,
            0.87,
            0.88,
            0.89,
            0.90,
            0.91,
            0.92,
            0.93,
            0.94,
            0.95,
            0.96,
            0.97,
            0.98,
            0.99,
            1.00,
        ],
    }
    param_names = list(grid.keys())
    param_combos = list(itertools.product(*[grid[k] for k in param_names]))
    print(f"Grid search: {len(param_combos)} combinations\n")
    steps = [1000]
    found = 0
    n_reps = 10
    csv_path = "spatial_altruism/data/grid_search_results.csv"
    completed = set()
    if os.path.exists(csv_path):
        try:
            df_conv = pd.read_csv(csv_path)
            for row in df_conv.itertuples(index=False):
                completed.add(
                    (
                        round(row.benefit_from_altruism, 6),
                        round(row.cost_of_altruism, 6),
                        round(row.disease, 6),
                        round(row.harshness, 6),
                    )
                )
        except Exception as e:
            print(f"Warning: Could not read CSV: {e}")
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    total = len(param_combos)
    completed_count = 0
    for combo in param_combos:
        param_dict = dict(zip(param_names, combo))
        param_tuple = (
            round(param_dict["benefit_from_altruism"], 6),
            round(param_dict["cost_of_altruism"], 6),
            round(param_dict["disease"], 6),
            round(param_dict["harshness"], 6),
        )
        if param_tuple in completed:
            completed_count += 1
            continue
        coexist_count = 0
        for _ in range(n_reps):
            params = make_params(param_dict)
            results = run_and_report(params, steps)
            r = results.get(1000, None)
            if r and r["altruists"] > 0 and r["selfish"] > 0:
                coexist_count += 1
        coexist_prob = coexist_count / n_reps
        if coexist_prob > 0:
            found += 1
            print(f"\nParams: {param_dict}")
            print(f"Coexistence probability: {coexist_prob:.2f} ({coexist_count}/{n_reps})")
        row = {
            "benefit_from_altruism": float(param_dict["benefit_from_altruism"]),
            "cost_of_altruism": float(param_dict["cost_of_altruism"]),
            "disease": float(param_dict["disease"]),
            "harshness": float(param_dict["harshness"]),
            "coexist_prob": float(coexist_prob),
        }
        with open(csv_path, "a", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "benefit_from_altruism",
                    "cost_of_altruism",
                    "disease",
                    "harshness",
                    "coexist_prob",
                ],
            )
            if write_header:
                writer.writeheader()
                write_header = False
            clean_row = {
                k: (
                    "{:.6g}".format(float(v)).strip()
                    if isinstance(v, float) or isinstance(v, int)
                    else str(v).strip()
                )
                for k, v in row.items()
            }
            writer.writerow(clean_row)
        completed_count += 1
        print(
            f"Progress: {completed_count} / {total} parameter sets completed "
            f"({completed_count / total:.1%})"
        )
    print(f"\nFound {found} parameter sets with coexistence probability > 0.")
    print("Results appended to spatial_altruism/data/grid_search_results.csv after each run.")


if __name__ == "__main__":
    main()
