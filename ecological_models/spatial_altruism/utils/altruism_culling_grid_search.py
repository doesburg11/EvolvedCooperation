#!/usr/bin/env python3
"""
Culling-focused coexistence sweep for the spatial altruism model.

Edit the grid block in this file and the active defaults in
`ecological_models/spatial_altruism/config/altruism_config.py`, then run from the repo root:
  ./.conda/bin/python -m ecological_models.spatial_altruism.utils.altruism_culling_grid_search
"""

import csv
import itertools
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m ecological_models.spatial_altruism.utils.altruism_culling_grid_search'."
    )

from ..altruism_model import AltruismModel, make_params


CSV_PATH = "ecological_models/spatial_altruism/data/culling_grid_search_results.csv"


def run_and_report(params, steps=(1000,)):
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
                "selfish": green,
                "black": black,
                "pop": pop,
                "total": total,
            }
    return results


def build_param_override(param_dict):
    variant = param_dict["model_variant"]
    interval = int(param_dict["disturbance_interval"])
    fraction = float(param_dict["disturbance_fraction"])
    override = {
        "model_variant": variant,
        "benefit_from_altruism": float(param_dict["benefit_from_altruism"]),
        "cost_of_altruism": float(param_dict["cost_of_altruism"]),
        "harshness": float(param_dict["harshness"]),
        "altruistic_probability": float(param_dict["altruistic_probability"]),
        "selfish_probability": float(param_dict["selfish_probability"]),
        "disease": 0.0,
    }
    if variant == "uniform_culling":
        override["uniform_culling_interval"] = interval
        override["uniform_culling_fraction"] = fraction
    elif variant == "compact_swath":
        override["compact_swath_interval"] = interval
        override["compact_swath_fraction"] = fraction
    else:
        raise ValueError(f"Unsupported culling variant '{variant}'.")
    return override


def simulate_param_set(combo, param_names, n_reps, steps):
    param_dict = dict(zip(param_names, combo))
    coexist_count = 0
    altruists_sum = 0
    selfish_sum = 0
    black_sum = 0
    occupied_sum = 0

    for _ in range(n_reps):
        params = make_params(build_param_override(param_dict))
        results = run_and_report(params, steps)
        final = results[max(steps)]
        if final["altruists"] > 0 and final["selfish"] > 0:
            coexist_count += 1
        altruists_sum += final["altruists"]
        selfish_sum += final["selfish"]
        black_sum += final["black"]
        occupied_sum += final["pop"] / max(final["total"], 1)

    coexist_prob = coexist_count / n_reps
    row = {
        "model_variant": str(param_dict["model_variant"]),
        "benefit_from_altruism": float(param_dict["benefit_from_altruism"]),
        "cost_of_altruism": float(param_dict["cost_of_altruism"]),
        "harshness": float(param_dict["harshness"]),
        "disturbance_interval": int(param_dict["disturbance_interval"]),
        "disturbance_fraction": float(param_dict["disturbance_fraction"]),
        "altruistic_probability": float(param_dict["altruistic_probability"]),
        "selfish_probability": float(param_dict["selfish_probability"]),
        "coexist_prob": float(coexist_prob),
        "altruist_avg": float(altruists_sum / n_reps),
        "selfish_avg": float(selfish_sum / n_reps),
        "black_avg": float(black_sum / n_reps),
        "occupied_avg": float(occupied_sum / n_reps),
    }
    key = (
        str(param_dict["model_variant"]),
        round(float(param_dict["benefit_from_altruism"]), 6),
        round(float(param_dict["cost_of_altruism"]), 6),
        round(float(param_dict["harshness"]), 6),
        int(param_dict["disturbance_interval"]),
        round(float(param_dict["disturbance_fraction"]), 6),
        round(float(param_dict["altruistic_probability"]), 6),
        round(float(param_dict["selfish_probability"]), 6),
    )
    return key, row, coexist_prob, coexist_count


def main():
    base_params = make_params()

    def clamp(val):
        return min(max(val, 0.0), 1.0)

    grid = {
        "model_variant": ["uniform_culling", "compact_swath"],
        "benefit_from_altruism": [clamp(round(x, 2)) for x in np.arange(0.00, 1.00 + 0.05, 0.05)],
        "cost_of_altruism": [clamp(round(x, 2)) for x in np.arange(0.00, 0.35 + 0.05, 0.05)],
        "harshness": [round(base_params.harshness, 2)],
        "disturbance_interval": sorted(
            {int(base_params.uniform_culling_interval), int(base_params.compact_swath_interval)}
        ),
        "disturbance_fraction": sorted(
            {
                0.25,
                0.50,
                round(float(base_params.uniform_culling_fraction), 2),
                round(float(base_params.compact_swath_fraction), 2),
            }
        ),
        "altruistic_probability": [float(base_params.altruistic_probability)],
        "selfish_probability": [float(base_params.selfish_probability)],
    }
    param_names = list(grid.keys())
    param_combos = list(itertools.product(*[grid[k] for k in param_names]))
    print(f"Culling grid search: {len(param_combos)} combinations\n")

    completed = set()
    if os.path.exists(CSV_PATH):
        try:
            df_conv = pd.read_csv(CSV_PATH)
            for row in df_conv.itertuples(index=False):
                completed.add(
                    (
                        str(row.model_variant),
                        round(row.benefit_from_altruism, 6),
                        round(row.cost_of_altruism, 6),
                        round(row.harshness, 6),
                        int(row.disturbance_interval),
                        round(row.disturbance_fraction, 6),
                        round(row.altruistic_probability, 6),
                        round(row.selfish_probability, 6),
                    )
                )
        except Exception as exc:
            print(f"Warning: Could not read CSV: {exc}")

    write_header = not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0
    fieldnames = [
        "model_variant",
        "benefit_from_altruism",
        "cost_of_altruism",
        "harshness",
        "disturbance_interval",
        "disturbance_fraction",
        "altruistic_probability",
        "selfish_probability",
        "coexist_prob",
        "altruist_avg",
        "selfish_avg",
        "black_avg",
        "occupied_avg",
    ]
    steps = (1000,)
    n_reps = 5
    found = 0
    batch_size = 250
    results_buffer = []
    total = len(param_combos)

    with ProcessPoolExecutor(max_workers=min(32, os.cpu_count() or 1)) as executor:
        futures = []
        for combo in param_combos:
            param_dict = dict(zip(param_names, combo))
            key = (
                str(param_dict["model_variant"]),
                round(float(param_dict["benefit_from_altruism"]), 6),
                round(float(param_dict["cost_of_altruism"]), 6),
                round(float(param_dict["harshness"]), 6),
                int(param_dict["disturbance_interval"]),
                round(float(param_dict["disturbance_fraction"]), 6),
                round(float(param_dict["altruistic_probability"]), 6),
                round(float(param_dict["selfish_probability"]), 6),
            )
            if key in completed:
                continue
            futures.append(executor.submit(simulate_param_set, combo, param_names, n_reps, steps))

        completed_count = len(completed)
        for future in as_completed(futures):
            _, row, coexist_prob, coexist_count = future.result()
            completed_count += 1
            results_buffer.append(
                {
                    key: (
                        "{:.6g}".format(float(value)).strip()
                        if isinstance(value, (float, int))
                        else str(value).strip()
                    )
                    for key, value in row.items()
                }
            )
            if coexist_prob > 0:
                found += 1
                print(f"\nParams: {row}")
                print(f"Coexistence probability: {coexist_prob:.2f} ({coexist_count}/{n_reps})")
            if len(results_buffer) >= batch_size:
                with open(CSV_PATH, "a", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    if write_header:
                        writer.writeheader()
                        write_header = False
                    writer.writerows(results_buffer)
                results_buffer = []
            print(
                f"Progress: {completed_count} / {total} parameter sets completed "
                f"({completed_count / total:.1%})"
            )

        if results_buffer:
            with open(CSV_PATH, "a", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerows(results_buffer)

    print(f"\nFound {found} parameter sets with coexistence probability > 0.")
    print(f"Results appended to {CSV_PATH} in batches.")


if __name__ == "__main__":
    main()
