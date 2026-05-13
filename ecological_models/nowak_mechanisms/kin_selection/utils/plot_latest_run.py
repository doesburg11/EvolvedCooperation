#!/usr/bin/env python3
"""Generate static plots for the ecological kin-selection outputs.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.utils.plot_latest_run
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.kin_selection.utils.plot_latest_run'."
    )

from ..config.kin_selection_config import config as active_config


DATA_DIR = Path(str(active_config["data_dir"]))
LATEST_RUN_PATH = DATA_DIR / "latest_run.json"
PROOF_SUMMARY_GLOB = "ecological_kin_selection_proof_*_summary.csv"
TRAJECTORY_OUTPUT_PATH = DATA_DIR / "latest_run_trajectory.png"
PROOF_OUTPUT_PATH = DATA_DIR / "latest_proof_summary.png"

SCENARIO_ORDER = [
    "kin_biased_rearing",
    "no_relatedness_bias",
    "shuffled_relatedness",
    "no_rearing_dependency",
    "unrelated_rearing_groups",
    "high_juvenile_dispersal",
    "cost_too_high",
]


def _series(values: list[Any]) -> list[float]:
    return [math.nan if value is None else float(value) for value in values]


def _read_latest_run() -> dict[str, Any]:
    if not LATEST_RUN_PATH.exists():
        raise FileNotFoundError(
            f"Missing {LATEST_RUN_PATH}; run kin_selection_model.py first"
        )
    with LATEST_RUN_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _latest_proof_summary_path() -> Path:
    paths = sorted(DATA_DIR.glob(PROOF_SUMMARY_GLOB))
    if not paths:
        raise FileNotFoundError(
            f"Missing {PROOF_SUMMARY_GLOB}; run proof_of_mechanism.py first"
        )
    return paths[-1]


def _read_proof_summary(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Proof summary is empty: {path}")
    return rows


def _as_float(row: dict[str, Any], key: str) -> float:
    value = row[key]
    if value in {"", "nan", "NaN", "None"}:
        return math.nan
    return float(value)


def plot_latest_run() -> Path:
    payload = _read_latest_run()
    history = payload["history"]

    steps = _series(history["step"])
    mean_helping = _series(history["mean_helping_trait"])
    adult_helping = _series(history["adult_mean_helping_trait"])
    helping_invasion_frequency = _series(history["helping_invasion_frequency"])
    population = _series(history["population"])
    juveniles = _series(history["juvenile_count"])
    adults = _series(history["adult_count"])
    elders = _series(history["elder_count"])
    juvenile_survival = _series(history["juvenile_survival_rate"])
    total_care = _series(history["total_care"])
    mean_care_relatedness = _series(history["mean_care_relatedness"])
    mean_available_care_relatedness = _series(
        history["mean_available_care_relatedness"]
    )
    care_assortment_gain = _series(history["care_assortment_gain"])
    kin_care_fraction = _series(history["kin_care_fraction"])
    expected_benefit = _series(history["expected_juvenile_survival_benefit"])
    helper_reproduction_cost = _series(history["expected_helper_reproduction_cost"])
    hamilton_margin_proxy = _series(history["hamilton_margin_proxy"])

    fig, axes = plt.subplots(3, 2, figsize=(13, 11), constrained_layout=True)
    fig.suptitle("Ecological Kin Selection: Latest Run", fontsize=15)

    ax = axes[0, 0]
    ax.plot(steps, population, label="population", color="#1f2937", linewidth=2)
    ax.plot(steps, juveniles, label="juveniles", color="#2563eb", linewidth=1.8)
    ax.plot(steps, adults, label="adults", color="#16a34a", linewidth=1.8)
    ax.plot(steps, elders, label="elders", color="#9333ea", linewidth=1.8)
    ax.set_title("Demography")
    ax.set_xlabel("step")
    ax.set_ylabel("count")
    ax.legend(frameon=False)

    ax = axes[0, 1]
    ax.plot(steps, mean_helping, label="all individuals", color="#0f766e", linewidth=2)
    ax.plot(steps, adult_helping, label="adults", color="#f97316", linewidth=1.8)
    ax.plot(
        steps,
        helping_invasion_frequency,
        label="rare-helper frequency",
        color="#be123c",
        linewidth=1.8,
    )
    ax.set_title("Helping Trait")
    ax.set_xlabel("step")
    ax.set_ylabel("mean h")
    ax.legend(frameon=False)

    ax = axes[1, 0]
    ax.plot(
        steps,
        juvenile_survival,
        label="juvenile survival",
        color="#dc2626",
        linewidth=2,
    )
    ax.plot(
        steps,
        mean_care_relatedness,
        label="mean care relatedness",
        color="#7c3aed",
        linewidth=1.8,
    )
    ax.plot(
        steps,
        mean_available_care_relatedness,
        label="available relatedness",
        color="#a855f7",
        linestyle="--",
        linewidth=1.5,
    )
    ax.plot(
        steps,
        kin_care_fraction,
        label="kin care fraction",
        color="#0891b2",
        linewidth=1.8,
    )
    ax.set_title("Rearing Mechanism")
    ax.set_xlabel("step")
    ax.set_ylabel("rate / relatedness")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(frameon=False)

    ax = axes[1, 1]
    ax.plot(steps, total_care, label="total care", color="#854d0e", linewidth=2)
    ax.plot(
        steps,
        expected_benefit,
        label="expected juvenile benefit",
        color="#16a34a",
        linewidth=1.8,
    )
    ax.set_title("Total Care")
    ax.set_xlabel("step")
    ax.set_ylabel("care / expected survivals")
    ax.legend(frameon=False)

    ax = axes[2, 0]
    ax.plot(
        steps,
        care_assortment_gain,
        label="care assortment gain",
        color="#4f46e5",
        linewidth=2,
    )
    ax.axhline(0.0, color="#111827", linewidth=1)
    ax.set_title("Assortment From Targeting")
    ax.set_xlabel("step")
    ax.set_ylabel("care r - available r")
    ax.legend(frameon=False)

    ax = axes[2, 1]
    ax.plot(
        steps,
        hamilton_margin_proxy,
        label="Hamilton-margin proxy",
        color="#059669",
        linewidth=2,
    )
    ax.plot(
        steps,
        helper_reproduction_cost,
        label="helper reproduction cost proxy",
        color="#dc2626",
        linewidth=1.8,
    )
    ax.axhline(0.0, color="#111827", linewidth=1)
    ax.set_title("Measured Benefit-Cost Proxy")
    ax.set_xlabel("step")
    ax.set_ylabel("expected events")
    ax.legend(frameon=False)

    for ax in axes.flat:
        ax.grid(True, alpha=0.25)

    TRAJECTORY_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(TRAJECTORY_OUTPUT_PATH, dpi=160)
    plt.close(fig)
    return TRAJECTORY_OUTPUT_PATH


def plot_proof_summary() -> Path:
    summary_path = _latest_proof_summary_path()
    rows_by_scenario = {
        str(row["scenario"]): row for row in _read_proof_summary(summary_path)
    }
    rows = [
        rows_by_scenario[scenario]
        for scenario in SCENARIO_ORDER
        if scenario in rows_by_scenario
    ]
    labels = [str(row["scenario"]) for row in rows]
    short_labels = [
        label.replace("_", "\n")
        .replace("relatedness", "rel.")
        .replace("juvenile", "juv.")
        for label in labels
    ]
    delta_h = [_as_float(row, "mean_helping_trait_change") for row in rows]
    success_rates = [_as_float(row, "success_rate") for row in rows]
    care_relatedness = [_as_float(row, "mean_care_relatedness") for row in rows]
    kin_care_fraction = [_as_float(row, "mean_kin_care_fraction") for row in rows]
    assortment_gain = [_as_float(row, "mean_care_assortment_gain") for row in rows]
    hamilton_margin = [_as_float(row, "mean_hamilton_margin_proxy") for row in rows]
    lrs_difference = [
        _as_float(row, "mean_lifetime_offspring_difference_rare_minus_resident")
        for row in rows
    ]

    fig, axes = plt.subplots(4, 1, figsize=(12, 14), constrained_layout=True)
    fig.suptitle("Ecological Kin Selection: Proof Scenarios", fontsize=15)

    colors = ["#16a34a" if rate >= 1.0 else "#64748b" for rate in success_rates]
    ax = axes[0]
    ax.bar(short_labels, delta_h, color=colors)
    ax.axhline(0.0, color="#111827", linewidth=1)
    ax.set_title("Mean Helping Trait Change")
    ax.set_ylabel("final h - initial h")
    ax.grid(True, axis="y", alpha=0.25)

    ax = axes[1]
    x_positions = list(range(len(rows)))
    width = 0.38
    ax.bar(
        [x - width / 2 for x in x_positions],
        care_relatedness,
        width,
        label="mean care relatedness",
        color="#7c3aed",
    )
    ax.bar(
        [x + width / 2 for x in x_positions],
        kin_care_fraction,
        width,
        label="kin care fraction",
        color="#0891b2",
    )
    ax.set_title("Care Targeting")
    ax.set_ylabel("rate / relatedness")
    ax.set_ylim(0.0, 1.05)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(short_labels)
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.25)

    ax = axes[2]
    x_positions = list(range(len(rows)))
    width = 0.38
    ax.bar(
        [x - width / 2 for x in x_positions],
        assortment_gain,
        width,
        label="care assortment gain",
        color="#4f46e5",
    )
    ax.bar(
        [x + width / 2 for x in x_positions],
        hamilton_margin,
        width,
        label="Hamilton-margin proxy",
        color="#059669",
    )
    ax.axhline(0.0, color="#111827", linewidth=1)
    ax.set_title("Measured Diagnostics")
    ax.set_ylabel("relatedness / expected events")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(short_labels)
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.25)

    ax = axes[3]
    ax.bar(short_labels, lrs_difference, color="#0f766e")
    ax.axhline(0.0, color="#111827", linewidth=1)
    ax.set_title("Lifetime Reproductive Success")
    ax.set_ylabel("rare helper offspring - resident offspring")
    ax.grid(True, axis="y", alpha=0.25)

    PROOF_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PROOF_OUTPUT_PATH, dpi=160)
    plt.close(fig)
    return PROOF_OUTPUT_PATH


def main() -> None:
    trajectory_path = plot_latest_run()
    proof_path = plot_proof_summary()
    print(f"[plot_latest_run] trajectory -> {trajectory_path}")
    print(f"[plot_latest_run] proof      -> {proof_path}")


if __name__ == "__main__":
    main()
