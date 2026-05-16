#!/usr/bin/env python3
"""
Proof-of-mechanism for the behaviorally anchored model.

Run from the repository root with:
  ./.conda/bin/python -m behaviorally_anchored_model.utils.proof_of_mechanism

Tests which capacities are load-bearing for cooperation to spread from a 10%
rare-helper foothold. The scenarios include full-model ablations, single
mechanisms, social-learning-only behavior change, and hard inverted controls.

Inverted scenarios (cooperation expected to stay flat or decline):
  network_reciprocity_only, group_selection_only, direct_reciprocity_only,
  social_learning_only, norm_enforcement_only, all_capacities_off,
  cost_too_high.

Normal scenarios (invasion frequency expected to rise):
  behaviorally_anchored_baseline, no_social_learning, no_norm_enforcement,
  no_direct_reciprocity, no_kin_selection, no_network_reciprocity,
  no_group_conflict, reputation_only, kin_selection_only, strong_all_channels.
"""

from __future__ import annotations

import math
from typing import Any

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m behaviorally_anchored_model.utils.proof_of_mechanism'."
    )

from ..config.behaviorally_anchored_config import (
    PROOF_SCENARIOS,
    PROOF_SEEDS,
    resolve_scenario_config,
)
from ..behaviorally_anchored_model import run_simulation


def _mean(values: list[float]) -> float:
    finite = [v for v in values if math.isfinite(v)]
    return sum(finite) / len(finite) if finite else math.nan


def run_proof() -> dict[str, Any]:
    scenario_names = [name for name, _ in PROOF_SCENARIOS]
    results: dict[str, dict[str, Any]] = {}

    # Inverted: mechanisms that cannot support invasion from rare alone
    # (with combined-model parameters), plus hard controls.
    inverted_scenarios = {
        "norm_enforcement_only",       # no genetic channel
        "network_reciprocity_only",    # insufficient alone at combined-model params
        "group_selection_only",        # insufficient alone at combined-model params
        "direct_reciprocity_only",     # no genetic reproductive channel
        "social_learning_only",        # behavior changes, no genetic channel
        "all_capacities_off",          # pure demographic baseline
        "cost_too_high",               # cost overwhelms all channels
    }

    for scenario_name in scenario_names:
        seed_results = []
        print(f"running {scenario_name}...", flush=True)
        for seed in PROOF_SEEDS:
            cfg = resolve_scenario_config(scenario_name, seed)
            payload = run_simulation(cfg)
            summary = payload["summary"]
            seed_results.append(
                {
                    "trait_change": summary["helping_trait_change"],
                    "invasion_frequency_change": summary["helping_invasion_frequency_change"],
                    "final_population": summary["final_population"],
                    "latest_mean_effective_helping": summary["latest_mean_effective_helping"],
                    "latest_social_learning_events": summary["latest_social_learning_events"],
                    "latest_mean_reputation": summary["latest_mean_reputation"],
                    "latest_norm_violation_rate": summary["latest_norm_violation_rate"],
                    "latest_mean_reciprocity_bond_memory": summary[
                        "latest_mean_reciprocity_bond_memory"
                    ],
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
        mean_effective_helping = _mean([
            r["latest_mean_effective_helping"] for r in seed_results
        ])
        mean_social_learning_events = _mean([
            r["latest_social_learning_events"] for r in seed_results
        ])
        mean_reputation = _mean([r["latest_mean_reputation"] for r in seed_results])
        mean_violation_rate = _mean([r["latest_norm_violation_rate"] for r in seed_results])
        mean_bond_memory = _mean([
            r["latest_mean_reciprocity_bond_memory"] for r in seed_results
        ])

        population_pass = mean_population >= min_population

        if scenario_name in inverted_scenarios:
            trait_pass = mean_trait_change < min_trait_increase
            invasion_pass = mean_invasion_change < min_invasion_increase
            overall_pass = trait_pass
        else:
            trait_pass = mean_trait_change >= min_trait_increase
            invasion_pass = mean_invasion_change >= min_invasion_increase
            overall_pass = invasion_pass and population_pass

        results[scenario_name] = {
            "pass": overall_pass,
            "trait_pass": trait_pass,
            "invasion_pass": invasion_pass,
            "population_pass": population_pass,
            "mean_trait_change": mean_trait_change,
            "mean_invasion_change": mean_invasion_change,
            "mean_population": mean_population,
            "mean_effective_helping": mean_effective_helping,
            "mean_social_learning_events": mean_social_learning_events,
            "mean_reputation": mean_reputation,
            "mean_violation_rate": mean_violation_rate,
            "mean_reciprocity_bond_memory": mean_bond_memory,
            "seed_results": seed_results,
        }

    return results


def main() -> None:
    print("[behaviorally_anchored_model] proof of mechanism")
    print(f"scenarios: {len(PROOF_SCENARIOS)}  seeds per scenario: {len(PROOF_SEEDS)}")
    print()

    results = run_proof()
    passed = sum(1 for r in results.values() if r["pass"])
    total = len(results)

    header = (
        f"{'scenario':<30} {'trait_Δ':>9} {'inv_Δ':>8} {'eff':>6}"
        f" {'learn':>6} {'pop':>5} {'rep':>7} {'bm':>6} {'result':>8}"
    )
    print(header)
    print("-" * len(header))

    for scenario_name, r in results.items():
        trait_str = f"{r['mean_trait_change']:+.4f}" if math.isfinite(r["mean_trait_change"]) else "   nan"
        inv_str = f"{r['mean_invasion_change']:+.4f}" if math.isfinite(r["mean_invasion_change"]) else "   nan"
        eff_str = f"{r['mean_effective_helping']:.3f}" if math.isfinite(r["mean_effective_helping"]) else "  nan"
        learn_str = f"{r['mean_social_learning_events']:.1f}" if math.isfinite(r["mean_social_learning_events"]) else "  nan"
        pop_str = f"{r['mean_population']:.0f}" if math.isfinite(r["mean_population"]) else "nan"
        rep_str = f"{r['mean_reputation']:.3f}" if math.isfinite(r["mean_reputation"]) else "  nan"
        bm_str = (
            f"{r['mean_reciprocity_bond_memory']:.3f}"
            if math.isfinite(r["mean_reciprocity_bond_memory"])
            else "  nan"
        )
        result_str = "PASS" if r["pass"] else "FAIL"
        print(
            f"{scenario_name:<30} {trait_str:>9} {inv_str:>8} {eff_str:>6}"
            f" {learn_str:>6} {pop_str:>5} {rep_str:>7} {bm_str:>6}"
            f" {result_str:>8}"
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
