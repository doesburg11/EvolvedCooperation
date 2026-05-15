#!/usr/bin/env python3
"""
Proof-of-mechanism for the ecological indirect-reciprocity model.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.utils.proof_of_mechanism

Tests the core predictions of ecological indirect reciprocity with public reputation
and reputation-weighted mate choice:

  1. Baseline: both channels active (reputation-gated energy routing AND
     reputation-based mate preference). Cooperation invades from 10% rare helpers.

  2. Random benefit routing: energy channel ablated (benefits distributed to
     random adults). Reputation-based mate preference remains intact. Cooperation
     spreads through the GENETIC channel alone — confirms that assortative mating
     via reputation is the load-bearing ecological mechanism, not energy routing.

  3. No mate preference: genetic channel ablated (random mate choice). Energy
     routing to high-reputation cooperators remains intact. Cooperation FAILS —
     energy routing alone cannot sustain invasion from rare with blending inheritance
     in a well-mixed population.

  4. Impossible threshold: reputation threshold = 0.99 (unreachable). Eligible
     events never fire (initial rep = 0.65 < 0.99), so reputation never updates
     and everyone retains the same starting reputation. Effect: both channels
     simultaneously broken — no energy routing AND no mate-preference
     discrimination (all males have identical reputation). Cooperation declines.

  5. No mate preference + low q: both channels weak/absent simultaneously.
     q = 0.05 << c/b = 0.16 (Nowak condition violated for energy routing) AND
     no reputation-based mate choice. Cooperation expected to decline.

  6. Cost too high: helping cost (0.20) overwhelms any energy or genetic
     advantage from both channels. Cooperation declines regardless of mechanism.

  7. High observation prob: q = 0.95. Stronger energy routing AND faster
     reputation divergence sharpens mate-preference discrimination.
     Cooperation spreads faster than baseline.

  8. Fast reputation update: weight = 0.50. Defectors detected and excluded
     within a few steps; cooperators quickly build high reputation and attract
     mates. Cooperation spreads fastest.

  9. Slow reputation update: weight = 0.05. Reputation signal sluggish;
     discrimination delayed but still functions. Tests mechanism robustness
     to slow reputation dynamics.

  10. No reproduction cost: reproduction penalty removed.
      Tests that reputation-based benefit drives spread, not cost removal.

Key ecological finding: the genetic channel (reputation-weighted mate selection)
is the load-bearing mechanism for cooperation invasion. Ablating energy routing
(random_benefit_routing) still allows invasion; ablating mate preference alone
prevents it. Energy routing provides a secondary energy advantage but is not
sufficient for invasion from rare with blending inheritance in a well-mixed model.

Inverted scenarios (cooperation expected to stay flat or decline):
  no_mate_preference, impossible_threshold, no_mate_preference_low_q, cost_too_high.

Normal scenarios (invasion frequency expected to rise):
  indirect_reciprocity_baseline, random_benefit_routing, high_observation_prob,
  fast_reputation_update, slow_reputation_update, no_reproduction_cost.
"""

from __future__ import annotations

import math
from typing import Any

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.indirect_reciprocity.utils.proof_of_mechanism'."
    )

from ..config.indirect_reciprocity_config import PROOF_SCENARIOS, PROOF_SEEDS, resolve_scenario_config
from ..indirect_reciprocity_model import run_simulation


def _mean(values: list[float]) -> float:
    finite = [v for v in values if math.isfinite(v)]
    return sum(finite) / len(finite) if finite else math.nan


def run_proof() -> dict[str, Any]:
    scenario_names = [name for name, _ in PROOF_SCENARIOS]
    results: dict[str, dict[str, Any]] = {}

    # Inverted scenarios gate on TRAIT CHANGE (not invasion frequency).
    # Ablating the genetic channel (mate preference) prevents invasion from
    # rare with blending inheritance, so trait change stays near zero or
    # declines. Inverted pass: mean_trait_change < proof_success_min_trait_increase.
    # Population threshold NOT applied to inverted scenarios.
    inverted_scenarios = {
        "no_mate_preference",
        "impossible_threshold",
        "no_mate_preference_low_q",
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
                    "latest_mean_reputation": summary["latest_mean_reputation"],
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
        mean_reputation = _mean([r["latest_mean_reputation"] for r in seed_results])

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
            "mean_reputation": mean_reputation,
            "seed_results": seed_results,
        }

    return results


def main() -> None:
    print("[ecological_indirect_reciprocity] proof of mechanism")
    print(f"scenarios: {len(PROOF_SCENARIOS)}  seeds per scenario: {len(PROOF_SEEDS)}")
    print()

    results = run_proof()
    passed = sum(1 for r in results.values() if r["pass"])
    total = len(results)

    header = f"{'scenario':<38} {'trait_Δ':>9} {'inv_Δ':>8} {'pop':>5} {'rep':>7} {'result':>8}"
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
        rep_str = (
            f"{r['mean_reputation']:.3f}" if math.isfinite(r["mean_reputation"]) else "  nan"
        )
        result_str = "PASS" if r["pass"] else "FAIL"
        print(
            f"{scenario_name:<38} {trait_str:>9} {inv_str:>8} {pop_str:>5} {rep_str:>7} {result_str:>8}"
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
