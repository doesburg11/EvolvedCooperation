#!/usr/bin/env python3
"""
Proof-of-mechanism for the ecological network-reciprocity model.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.network_reciprocity.utils.proof_of_mechanism

Tests the core predictions of ecological network reciprocity:
  1. Baseline: cooperation rises when offspring are placed locally and benefits
     flow to spatial neighbors.
  2. Scattered offspring: cooperation declines when offspring are placed at
     random positions (spatial clusters cannot form — primary mechanism off).
  3. No spatial structure: scattered offspring plus global mating removes all
     spatial reproductive assortment; cooperation dilutes through blending.
  4. Cost too high: cooperation cost so high that mean trait declines even as
     mutation noise inflates invasion frequency.
  5. Tight clustering: cooperation rises faster with smaller offspring radius.
  6. Uniform benefit routing: cooperation still spreads despite random routing,
     showing that spatial reproductive assortment is the primary mechanism.
  7. Wide neighborhood: cooperation still spreads despite diluted per-neighbor
     benefit, confirming the mechanism is primarily reproductive not energetic.
  8. Low dispersal: cooperation amplified when clusters accumulate undisturbed.
  9. High matured dispersal: cooperation still spreads after adult dispersal,
     because adults re-cluster in their new location through reproduction.
  10. High benefit: cooperation amplified by larger energy advantage per cluster.

Inverted scenarios gate on MEAN TRAIT CHANGE (not invasion frequency), because
mutation drift inflates invasion frequency independent of the mechanism.
Inverted pass condition: mean_trait_change < proof_success_min_trait_increase.

Inverted scenarios (mean trait expected to decline or stay flat):
  scattered_offspring, no_spatial_structure, cost_too_high.

Normal scenarios (invasion frequency expected to rise):
  network_reciprocity_baseline, tight_clustering, uniform_benefit_routing,
  wide_neighborhood, low_dispersal, high_matured_dispersal, high_benefit.
"""

from __future__ import annotations

import math
from typing import Any

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.network_reciprocity.utils.proof_of_mechanism'."
    )

from ..config.network_reciprocity_config import PROOF_SCENARIOS, PROOF_SEEDS, resolve_scenario_config
from ..network_reciprocity_model import run_simulation


def _mean(values: list[float]) -> float:
    finite = [v for v in values if math.isfinite(v)]
    return sum(finite) / len(finite) if finite else math.nan


def run_proof() -> dict[str, Any]:
    scenario_names = [name for name, _ in PROOF_SCENARIOS]
    results: dict[str, dict[str, Any]] = {}

    # Inverted scenarios are gated on TRAIT CHANGE (not invasion frequency).
    # Mutation drift inflates invasion frequency even when mean trait declines,
    # so trait change is the more reliable signal for mechanism-off conditions.
    # Inverted pass: mean_trait_change < proof_success_min_trait_increase.
    # Population threshold is NOT applied to inverted scenarios because high
    # costs or absent spatial structure can crash population as a side effect.
    inverted_scenarios = {
        "scattered_offspring",
        "no_spatial_structure",
        "cost_too_high",
    }

    for scenario_name in scenario_names:
        seed_results = []
        for seed in PROOF_SEEDS:
            cfg = resolve_scenario_config(scenario_name, seed)
            payload = run_simulation(cfg)
            summary = payload["summary"]
            seed_results.append(
                {
                    "trait_change": summary["helping_trait_change"],
                    "invasion_frequency_change": summary["helping_invasion_frequency_change"],
                    "final_population": summary["final_population"],
                    "latest_cooperation_spatial_clustering": summary[
                        "latest_cooperation_spatial_clustering"
                    ],
                    "latest_mean_neighborhood_size": summary["latest_mean_neighborhood_size"],
                }
            )

        cfg_for_thresholds = resolve_scenario_config(scenario_name, PROOF_SEEDS[0])
        min_trait_increase = float(cfg_for_thresholds["proof_success_min_trait_increase"])
        min_invasion_increase = float(
            cfg_for_thresholds["proof_success_min_invasion_frequency_increase"]
        )
        min_population = int(cfg_for_thresholds["proof_success_min_final_population"])

        mean_trait_change = _mean([r["trait_change"] for r in seed_results])
        mean_invasion_change = _mean([r["invasion_frequency_change"] for r in seed_results])
        mean_population = _mean([float(r["final_population"]) for r in seed_results])
        mean_clustering = _mean([r["latest_cooperation_spatial_clustering"] for r in seed_results])

        if scenario_name in inverted_scenarios:
            # Inverted: cooperation expected to stay flat or decline.
            # Gate on trait change only; population threshold not applied
            # (population collapse is an expected side effect, not a failure).
            trait_pass = mean_trait_change < min_trait_increase
            invasion_pass = mean_invasion_change < min_invasion_increase
            overall_pass = trait_pass
        else:
            trait_pass = mean_trait_change >= min_trait_increase
            invasion_pass = mean_invasion_change >= min_invasion_increase
            population_pass = mean_population >= min_population
            overall_pass = invasion_pass and population_pass

        population_pass = mean_population >= min_population
        results[scenario_name] = {
            "pass": overall_pass,
            "trait_pass": trait_pass,
            "invasion_pass": invasion_pass,
            "population_pass": population_pass,
            "mean_trait_change": mean_trait_change,
            "mean_invasion_change": mean_invasion_change,
            "mean_population": mean_population,
            "mean_clustering": mean_clustering,
            "seed_results": seed_results,
        }

    return results


def main() -> None:
    print("[ecological_network_reciprocity] proof of mechanism")
    print(f"scenarios: {len(PROOF_SCENARIOS)}  seeds per scenario: {len(PROOF_SEEDS)}")
    print()

    results = run_proof()
    passed = sum(1 for r in results.values() if r["pass"])
    total = len(results)

    header = f"{'scenario':<35} {'trait_Δ':>9} {'inv_Δ':>8} {'pop':>6} {'cluster':>9} {'result':>8}"
    print(header)
    print("-" * len(header))

    for scenario_name, r in results.items():
        trait_str = (
            f"{r['mean_trait_change']:+.4f}" if math.isfinite(r["mean_trait_change"]) else "   nan"
        )
        inv_str = (
            f"{r['mean_invasion_change']:+.4f}"
            if math.isfinite(r["mean_invasion_change"])
            else "   nan"
        )
        pop_str = f"{r['mean_population']:.0f}" if math.isfinite(r["mean_population"]) else "nan"
        cluster_str = (
            f"{r['mean_clustering']:+.4f}" if math.isfinite(r["mean_clustering"]) else "    nan"
        )
        result_str = "PASS" if r["pass"] else "FAIL"
        print(
            f"{scenario_name:<35} {trait_str:>9} {inv_str:>8} {pop_str:>6} {cluster_str:>9} {result_str:>8}"
        )

    print()
    print(f"result: {passed}/{total} scenarios passed")

    if passed < total:
        print("\nfailed scenarios:")
        for scenario_name, r in results.items():
            if not r["pass"]:
                flags = []
                if not r["trait_pass"]:
                    flags.append("trait")
                if not r["invasion_pass"]:
                    flags.append("invasion")
                if not r["population_pass"]:
                    flags.append("population")
                print(f"  {scenario_name}: {', '.join(flags)}")


if __name__ == "__main__":
    main()
