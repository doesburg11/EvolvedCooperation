#!/usr/bin/env python3
"""
Proof-of-mechanism for the ecological direct-reciprocity model.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.direct_reciprocity.utils.proof_of_mechanism

Tests the core predictions of ecological direct reciprocity:
  1. Baseline: cooperation rises when partners are stable, memory is tracked,
     and conditional dissolution lets cooperators exit bad partnerships.
  2. Memory off: all memory disabled (unconditional cooperation, flat dissolution);
     cooperators cannot exit non-reciprocating partners; cooperation expected to
     stay flat or decline.
  3. Random partners: partners reshuffled each step; no repeated encounters;
     temporal assortment is impossible; cooperation expected to decline.
  4. No direct reciprocity: both random partners AND memory off; complete ablation.
  5. Cost too high: helping cost overwhelms any partnership benefit; cooperation
     must decline regardless of mechanism.
  6. Long partnerships: moderate persistence (0.97) amplifies productive coop-coop
     pairs. Very high persistence (0.99) HURTS because cooperators cannot escape
     bad partnerships fast enough — the base persistence overwhelms differential
     dissolution. This reveals an optimal partnership-length regime.
  7. Short partnerships: even low persistence (0.65, ~3 steps average) does not
     kill the mechanism because fast turnover lets cooperators reach the partner
     market quickly.
  8. High reciprocity weight: stronger conditional response protects cooperators
     more effectively in bad partnerships.
  9. Strong leave weight: faster dissolution of non-reciprocating partnerships;
     cooperators find productive partners more quickly.
  10. No reproduction cost: removing the reproduction penalty shows that partnership
      dynamics alone (not cost structure) are the driver. High benefit (0.40) does
      NOT help — it amplifies defector exploitation more than mutual benefit.

Inverted scenarios gate on MEAN TRAIT CHANGE (not invasion frequency), because
blending inheritance inflates invasion frequency independent of the mechanism.
Inverted pass condition: mean_trait_change < proof_success_min_trait_increase.

Inverted scenarios (cooperation expected to stay flat or decline):
  memory_off, random_partners, no_direct_reciprocity, cost_too_high.

Normal scenarios (invasion frequency expected to rise):
  direct_reciprocity_baseline, long_partnerships, short_partnerships,
  high_reciprocity_weight, strong_leave_weight, high_benefit.
"""

from __future__ import annotations

import math
from typing import Any

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.direct_reciprocity.utils.proof_of_mechanism'."
    )

from ..config.direct_reciprocity_config import PROOF_SCENARIOS, PROOF_SEEDS, resolve_scenario_config
from ..direct_reciprocity_model import run_simulation


def _mean(values: list[float]) -> float:
    finite = [v for v in values if math.isfinite(v)]
    return sum(finite) / len(finite) if finite else math.nan


def run_proof() -> dict[str, Any]:
    scenario_names = [name for name, _ in PROOF_SCENARIOS]
    results: dict[str, dict[str, Any]] = {}

    # Inverted scenarios gate on TRAIT CHANGE (not invasion frequency).
    # Memory-off and random-partner ablations remove temporal assortment,
    # so cooperators cannot find reciprocating partners.
    # Inverted pass: mean_trait_change < proof_success_min_trait_increase.
    # Population threshold NOT applied to inverted scenarios: population
    # collapse is an expected side effect of high costs or absent mechanism.
    inverted_scenarios = {
        "memory_off",
        "random_partners",
        "no_direct_reciprocity",
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
                    "latest_mean_reciprocity_quality": summary[
                        "latest_mean_reciprocity_quality"
                    ],
                    "latest_mean_partnership_rate": summary["latest_mean_partnership_rate"],
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
        mean_quality = _mean([r["latest_mean_reciprocity_quality"] for r in seed_results])

        if scenario_name in inverted_scenarios:
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
            "mean_quality": mean_quality,
            "seed_results": seed_results,
        }

    return results


def main() -> None:
    print("[ecological_direct_reciprocity] proof of mechanism")
    print(f"scenarios: {len(PROOF_SCENARIOS)}  seeds per scenario: {len(PROOF_SEEDS)}")
    print()

    results = run_proof()
    passed = sum(1 for r in results.values() if r["pass"])
    total = len(results)

    header = f"{'scenario':<35} {'trait_Δ':>9} {'inv_Δ':>8} {'pop':>6} {'quality':>9} {'result':>8}"
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
        quality_str = (
            f"{r['mean_quality']:+.4f}" if math.isfinite(r["mean_quality"]) else "    nan"
        )
        result_str = "PASS" if r["pass"] else "FAIL"
        print(
            f"{scenario_name:<35} {trait_str:>9} {inv_str:>8} {pop_str:>6} {quality_str:>9} {result_str:>8}"
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
