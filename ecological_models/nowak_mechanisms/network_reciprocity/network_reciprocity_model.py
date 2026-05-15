#!/usr/bin/env python3
"""
Ecological network-reciprocity model with spatial positions and local benefit routing.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.network_reciprocity.network_reciprocity_model

Mechanism: cooperation spreads because individuals who reproduce locally create
spatial cooperator clusters. Cooperators within a cluster deliver benefits
preferentially to nearby cooperators, making the cluster energetically
self-sustaining. This is the ecological analog of Nowak's b/c > k condition:
cooperation pays when enough neighbors are cooperators to cover individual cost.

The key structural requirements are:
  1. Local offspring placement (offspring_placement_radius < interaction_radius)
     so that cooperator clusters form through reproduction.
  2. Local benefit routing (benefits flow within interaction_radius) so that
     cooperators within clusters preferentially help each other.

Both requirements are testable ablations: random_offspring_placement and
random_benefit_routing each independently break the mechanism.

Boundary with kin-selection model:
  - Kin selection: helping is directed toward same-lineage juveniles (explicit
    relatedness bias); rearing dependency is load-bearing.
  - Network reciprocity: helping flows uniformly to spatial neighbors without
    any relatedness discrimination; spatial clustering arises from local
    reproduction, not from kin recognition.

Boundary with group-selection model:
  - Group selection: explicit group structure with inter-group conflict and
    energy bonus for winners; cooperation spreads via differential group fitness.
  - Network reciprocity: no group structure; cooperation spreads via spatial
    clustering and per-individual benefit within the cluster.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np


if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.network_reciprocity.network_reciprocity_model'."
    )

from .config.network_reciprocity_config import config as active_config
from .config.network_reciprocity_config import resolve_config


SEX_FEMALE = "F"
SEX_MALE = "M"
STAGE_JUVENILE = "juvenile"
STAGE_ADULT = "adult"
STAGE_ELDER = "elder"

_ADULT_STAGES = {STAGE_ADULT, STAGE_ELDER}


@dataclass
class Individual:
    id: int
    sex: str
    age: int
    stage: str
    x: float
    y: float
    energy: float
    helping_trait: float
    mother_id: int | None
    father_id: int | None
    born_step: int


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


class EcologicalNetworkReciprocityModel:
    """
    Demographic ABM where cooperation spreads through spatial clustering.

    Individuals occupy a continuous unit square [0, 1] x [0, 1].
    Adults help spatial neighbors within interaction_radius, paying a fixed
    energy cost regardless of how many neighbors they have. The total benefit
    budget is split equally among recipients. Offspring are born near their
    mother, creating spatial cooperator clusters that are self-reinforcing once
    a sufficient fraction of local neighbors are cooperators.
    """

    def __init__(self, run_config: Mapping[str, Any]):
        self.config = resolve_config(run_config)
        self.rng = np.random.default_rng(self.config["random_seed"])
        self.individuals: list[Individual] = []
        self.next_id = 0
        self.step_index = 0
        self.history: dict[str, list[Any]] = defaultdict(list)
        self.offspring_counts: dict[int, int] = {}
        self.birth_helping_traits: dict[int, float] = {}
        self.death_ages: dict[int, int] = {}
        self.initial_mean_helping_trait = 0.0
        self._initialize_population()
        self.initial_mean_helping_trait = self._mean_helping_trait()
        self._record_history(births=0, deaths=0, clustering=math.nan, mean_neighborhood_size=math.nan)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _initialize_population(self) -> None:
        patch_count = int(self.config["initial_patch_count"])
        pairs_per_patch = int(self.config["founder_pairs_per_patch"])
        children_per_pair = int(self.config["initial_children_per_pair"])
        r = float(self.config["patch_init_radius"])
        margin = r + 0.02

        cx_arr = self.rng.uniform(margin, 1.0 - margin, size=patch_count)
        cy_arr = self.rng.uniform(margin, 1.0 - margin, size=patch_count)

        for pi in range(patch_count):
            cx = float(cx_arr[pi])
            cy = float(cy_arr[pi])
            for _ in range(pairs_per_patch):
                mx = float(np.clip(cx + self.rng.uniform(-r, r), 0.0, 1.0))
                my = float(np.clip(cy + self.rng.uniform(-r, r), 0.0, 1.0))
                fx = float(np.clip(cx + self.rng.uniform(-r, r), 0.0, 1.0))
                fy = float(np.clip(cy + self.rng.uniform(-r, r), 0.0, 1.0))
                mother = self._create_founder(SEX_FEMALE, mx, my)
                father = self._create_founder(SEX_MALE, fx, fy)
                self.individuals.extend([mother, father])
                mid_x, mid_y = (mx + fx) / 2.0, (my + fy) / 2.0
                for _ in range(children_per_pair):
                    child = self._create_child(mother, father, initial_child=True, ref_x=mid_x, ref_y=mid_y)
                    self.individuals.append(child)

    def _create_founder(self, sex: str, x: float, y: float) -> Individual:
        age = int(self.rng.integers(
            int(self.config["initial_adult_age_min"]),
            int(self.config["initial_adult_age_max"]) + 1,
        ))
        ind = Individual(
            id=self._take_id(),
            sex=sex,
            age=age,
            stage=self._stage_for_age(age),
            x=x,
            y=y,
            energy=float(self.config["initial_adult_energy"]),
            helping_trait=self._sample_initial_helping_trait(),
            mother_id=None,
            father_id=None,
            born_step=0,
        )
        self._register_birth(ind)
        return ind

    def _create_child(
        self,
        mother: Individual,
        father: Individual,
        *,
        initial_child: bool,
        ref_x: float,
        ref_y: float,
    ) -> Individual:
        if initial_child:
            age = int(self.rng.integers(
                int(self.config["initial_child_age_min"]),
                int(self.config["initial_child_age_max"]) + 1,
            ))
            energy = float(self.config["initial_juvenile_energy"])
        else:
            age = 0
            energy = float(self.config["child_energy"])

        trait = 0.5 * (mother.helping_trait + father.helping_trait)
        if self.rng.random() < float(self.config["helping_mutation_probability"]):
            trait += float(self.rng.normal(0.0, float(self.config["helping_mutation_stddev"])))
        trait = clamp01(trait)

        if bool(self.config["random_offspring_placement"]):
            x = float(self.rng.uniform(0.0, 1.0))
            y = float(self.rng.uniform(0.0, 1.0))
        else:
            place_r = float(self.config["offspring_placement_radius"])
            x = float(np.clip(ref_x + self.rng.uniform(-place_r, place_r), 0.0, 1.0))
            y = float(np.clip(ref_y + self.rng.uniform(-place_r, place_r), 0.0, 1.0))

        child = Individual(
            id=self._take_id(),
            sex=self._random_sex(),
            age=age,
            stage=self._stage_for_age(age),
            x=x,
            y=y,
            energy=energy,
            helping_trait=trait,
            mother_id=mother.id,
            father_id=father.id,
            born_step=self.step_index,
        )
        self._register_birth(child)
        return child

    def _take_id(self) -> int:
        nid = self.next_id
        self.next_id += 1
        return nid

    def _register_birth(self, ind: Individual) -> None:
        self.offspring_counts[ind.id] = 0
        self.birth_helping_traits[ind.id] = ind.helping_trait

    def _register_death(self, ind: Individual) -> None:
        self.death_ages[ind.id] = ind.age

    def _sample_initial_helping_trait(self) -> float:
        if self.rng.random() < float(self.config["rare_helper_founder_probability"]):
            return float(self.config["rare_helper_trait_value"])
        return float(self.rng.uniform(
            float(self.config["initial_helping_trait_min"]),
            float(self.config["initial_helping_trait_max"]),
        ))

    def _random_sex(self) -> str:
        return SEX_FEMALE if self.rng.random() < 0.5 else SEX_MALE

    def _stage_for_age(self, age: int) -> str:
        if age < int(self.config["juvenile_maturity_age"]):
            return STAGE_JUVENILE
        if age >= int(self.config["elder_age"]):
            return STAGE_ELDER
        return STAGE_ADULT

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self) -> None:
        self.step_index += 1
        self._age_and_budget()
        self._provide_local_benefits()
        deaths = self._apply_survival()
        self._apply_maturation_dispersal()
        births = self._reproduce()
        deaths += self._apply_density_mortality()
        clustering, mean_nbr_size = self._compute_spatial_metrics()
        self._record_history(births=births, deaths=deaths, clustering=clustering, mean_neighborhood_size=mean_nbr_size)

    def _age_and_budget(self) -> None:
        for ind in self.individuals:
            ind.age += 1
            ind.stage = self._stage_for_age(ind.age)
            if ind.stage == STAGE_JUVENILE:
                ind.energy += float(self.config["juvenile_foraging_energy_gain"])
                ind.energy -= float(self.config["juvenile_metabolic_cost"])
            elif ind.stage == STAGE_ADULT:
                ind.energy += float(self.config["adult_foraging_energy_gain"])
                ind.energy -= float(self.config["adult_metabolic_cost"])
            else:
                ind.energy += float(self.config["elder_foraging_energy_gain"])
                ind.energy -= float(self.config["elder_metabolic_cost"])
            ind.energy = min(ind.energy, float(self.config["max_energy"]))

    def _provide_local_benefits(self) -> None:
        """
        Each adult delivers cooperation_benefit_per_step total energy, split
        equally among neighbors within interaction_radius. Costs are deducted
        from cooperating adults regardless of neighbor count.

        When random_benefit_routing is True, total adult benefit budget is
        distributed uniformly to all individuals — this removes spatial
        assortment from benefit delivery while keeping total energy constant.
        """
        n = len(self.individuals)
        if n < 2:
            return

        xs = np.array([ind.x for ind in self.individuals])
        ys = np.array([ind.y for ind in self.individuals])
        traits = np.array([ind.helping_trait for ind in self.individuals])
        adult_mask = np.array([ind.stage in _ADULT_STAGES for ind in self.individuals], dtype=float)

        benefit_rate = float(self.config["cooperation_benefit_per_step"])
        cost_rate = float(self.config["helping_cost_per_step"])
        radius = float(self.config["interaction_radius"])
        max_energy = float(self.config["max_energy"])

        # Per-adult benefit budget.
        budgets = traits * benefit_rate * adult_mask  # (n,)

        if bool(self.config["random_benefit_routing"]):
            # Total budget distributed uniformly to all individuals except self.
            total_budget = float(np.sum(budgets))
            per_individual = total_budget / max(1.0, float(n - 1))
            energy_gains = np.full(n, per_individual)
        else:
            # Vectorised pairwise distance: (n, n) matrix.
            dx = xs[:, None] - xs[None, :]
            dy = ys[:, None] - ys[None, :]
            neighbor_mask = (dx * dx + dy * dy < radius * radius)
            np.fill_diagonal(neighbor_mask, False)

            n_neighbors = neighbor_mask.sum(axis=1).astype(float)  # (n,)
            # Each adult's budget split equally among their neighbors.
            scales = np.where(n_neighbors > 0, budgets / np.maximum(n_neighbors, 1.0), 0.0)
            # energy_gains[j] = sum over donors i of (scale[i] if j in i's neighbourhood).
            energy_gains = neighbor_mask.T @ scales  # (n,)

        energy_costs = traits * cost_rate * adult_mask  # (n,)

        for i, ind in enumerate(self.individuals):
            ind.energy = min(
                ind.energy + float(energy_gains[i]) - float(energy_costs[i]),
                max_energy,
            )

    def _apply_survival(self) -> int:
        survivors = []
        deaths = 0
        for ind in self.individuals:
            if ind.energy <= 0.0 or ind.age > int(self.config["max_age"]):
                self._register_death(ind)
                deaths += 1
                continue
            if ind.stage == STAGE_JUVENILE:
                if self.rng.random() > float(self.config["base_juvenile_survival_probability"]):
                    self._register_death(ind)
                    deaths += 1
                    continue
            elif ind.stage == STAGE_ADULT:
                if self.rng.random() > float(self.config["adult_survival_probability"]):
                    self._register_death(ind)
                    deaths += 1
                    continue
            else:
                if self.rng.random() > float(self.config["elder_survival_probability"]):
                    self._register_death(ind)
                    deaths += 1
                    continue
            survivors.append(ind)
        self.individuals = survivors
        return deaths

    def _apply_maturation_dispersal(self) -> None:
        disp_prob = float(self.config["matured_dispersal_probability"])
        disp_r = float(self.config["matured_dispersal_radius"])
        maturity_age = int(self.config["juvenile_maturity_age"])
        for ind in self.individuals:
            if (
                ind.stage == STAGE_ADULT
                and ind.age == maturity_age
                and self.rng.random() < disp_prob
            ):
                ind.x = float(np.clip(ind.x + self.rng.uniform(-disp_r, disp_r), 0.0, 1.0))
                ind.y = float(np.clip(ind.y + self.rng.uniform(-disp_r, disp_r), 0.0, 1.0))

    def _reproduce(self) -> int:
        if len(self.individuals) >= int(self.config["max_population"]):
            return 0

        repr_cost_scale = float(self.config["helping_reproduction_cost_scale"])
        mating_r = float(self.config["mating_radius"])
        same_area_pref = float(self.config["same_area_mate_preference_probability"])
        base_repr_prob = float(self.config["female_reproduction_probability"])
        min_energy = float(self.config["reproduction_energy_threshold"])
        max_pop = int(self.config["max_population"])

        adult_males = [
            ind for ind in self.individuals
            if ind.sex == SEX_MALE
            and ind.stage == STAGE_ADULT
            and int(self.config["male_min_reproduction_age"]) <= ind.age <= int(self.config["male_max_reproduction_age"])
        ]
        adult_females = [
            ind for ind in self.individuals
            if ind.sex == SEX_FEMALE
            and ind.stage == STAGE_ADULT
            and int(self.config["female_min_reproduction_age"]) <= ind.age <= int(self.config["female_max_reproduction_age"])
            and ind.energy >= min_energy
        ]

        births: list[Individual] = []
        for mother in adult_females:
            if len(self.individuals) + len(births) >= max_pop:
                break
            eff_repr = base_repr_prob * max(0.0, 1.0 - mother.helping_trait * repr_cost_scale)
            if self.rng.random() > eff_repr:
                continue

            nearby = [m for m in adult_males if math.hypot(m.x - mother.x, m.y - mother.y) < mating_r]
            if nearby and (not adult_males or self.rng.random() < same_area_pref):
                candidates = nearby
            else:
                candidates = adult_males
            if not candidates:
                continue

            father = candidates[int(self.rng.integers(0, len(candidates)))]
            mother.energy -= float(self.config["reproduction_energy_cost"])
            child = self._create_child(mother, father, initial_child=False, ref_x=mother.x, ref_y=mother.y)
            births.append(child)
            self.offspring_counts[mother.id] += 1
            self.offspring_counts[father.id] += 1

        self.individuals.extend(births)
        return len(births)

    def _apply_density_mortality(self) -> int:
        max_pop = int(self.config["max_population"])
        excess = len(self.individuals) - max_pop
        if excess <= 0:
            return 0
        jitter = self.rng.random(len(self.individuals)) * 0.01
        ranked = sorted(
            zip(self.individuals, jitter),
            key=lambda item: (item[0].energy + item[1], item[0].age),
        )
        removed_ids = {ind.id for ind, _ in ranked[:excess]}
        for ind, _ in ranked[:excess]:
            self._register_death(ind)
        self.individuals = [ind for ind in self.individuals if ind.id not in removed_ids]
        return excess

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def _compute_spatial_metrics(self) -> tuple[float, float]:
        """
        Cooperation spatial clustering: mean over adults of
        (mean neighbor helping_trait - global mean helping_trait).

        Positive clustering means cooperators are surrounded by above-average
        cooperation — the necessary condition for network reciprocity to operate.
        This is the ecological analog of the spatial assortment coefficient.
        """
        adults = [ind for ind in self.individuals if ind.stage in _ADULT_STAGES]
        if len(adults) < 2:
            return math.nan, math.nan

        n = len(adults)
        xs = np.array([a.x for a in adults])
        ys = np.array([a.y for a in adults])
        traits = np.array([a.helping_trait for a in adults])
        global_mean = float(np.mean(traits))

        dx = xs[:, None] - xs[None, :]
        dy = ys[:, None] - ys[None, :]
        neighbor_mask = (dx * dx + dy * dy < float(self.config["interaction_radius"]) ** 2)
        np.fill_diagonal(neighbor_mask, False)

        n_neighbors = neighbor_mask.sum(axis=1).astype(float)
        trait_sums = neighbor_mask @ traits
        nbr_means = np.where(
            n_neighbors > 0,
            trait_sums / np.maximum(n_neighbors, 1.0),
            global_mean,
        )
        has_neighbors = n_neighbors > 0
        clustering_vals = (nbr_means - global_mean)[has_neighbors]
        clustering = float(np.mean(clustering_vals)) if len(clustering_vals) > 0 else math.nan
        mean_nbr = float(np.mean(n_neighbors))
        return clustering, mean_nbr

    # ------------------------------------------------------------------
    # History and output
    # ------------------------------------------------------------------

    def _record_history(
        self,
        *,
        births: int,
        deaths: int,
        clustering: float,
        mean_neighborhood_size: float,
    ) -> None:
        population = len(self.individuals)
        juvenile_count = sum(1 for ind in self.individuals if ind.stage == STAGE_JUVENILE)
        adult_count = sum(1 for ind in self.individuals if ind.stage == STAGE_ADULT)
        elder_count = population - juvenile_count - adult_count

        self.history["step"].append(self.step_index)
        self.history["population"].append(population)
        self.history["juvenile_count"].append(juvenile_count)
        self.history["adult_count"].append(adult_count)
        self.history["elder_count"].append(elder_count)
        self.history["births"].append(int(births))
        self.history["deaths"].append(int(deaths))
        self.history["mean_helping_trait"].append(self._mean_helping_trait())
        self.history["helping_invasion_frequency"].append(self._helping_invasion_frequency())
        self.history["mean_energy"].append(self._mean_energy())
        self.history["cooperation_spatial_clustering"].append(float(clustering))
        self.history["mean_neighborhood_size"].append(float(mean_neighborhood_size))

    def _mean_helping_trait(self) -> float:
        values = [ind.helping_trait for ind in self.individuals]
        return float(np.mean(values)) if values else math.nan

    def _helping_invasion_frequency(self) -> float:
        values = [ind.helping_trait for ind in self.individuals]
        if not values:
            return math.nan
        threshold = float(self.config["helping_trait_invasion_threshold"])
        return sum(1 for v in values if v >= threshold) / len(values)

    def _mean_energy(self) -> float:
        return float(np.mean([ind.energy for ind in self.individuals])) if self.individuals else math.nan

    def _last_finite_history(self, key: str) -> float:
        for value in reversed(self.history[key]):
            if value is None:
                continue
            v = float(value)
            if math.isfinite(v):
                return v
        return math.nan

    def run(self) -> dict[str, Any]:
        while self.step_index < int(self.config["simulation_steps"]) and self.individuals:
            self.step()
        return self.to_payload()

    def to_payload(self) -> dict[str, Any]:
        return {"summary": self.final_summary(), "history": dict(self.history)}

    def final_summary(self) -> dict[str, Any]:
        final_mean = self._mean_helping_trait()
        return {
            "steps_done": self.step_index,
            "initial_mean_helping_trait": self.initial_mean_helping_trait,
            "final_mean_helping_trait": final_mean,
            "helping_trait_change": (
                final_mean - self.initial_mean_helping_trait
                if math.isfinite(final_mean) else math.nan
            ),
            "initial_helping_invasion_frequency": self.history["helping_invasion_frequency"][0],
            "final_helping_invasion_frequency": self._helping_invasion_frequency(),
            "helping_invasion_frequency_change": (
                self._helping_invasion_frequency()
                - self.history["helping_invasion_frequency"][0]
            ),
            "final_population": len(self.individuals),
            "final_mean_energy": self._mean_energy(),
            "latest_cooperation_spatial_clustering": self._last_finite_history(
                "cooperation_spatial_clustering"
            ),
            "latest_mean_neighborhood_size": self._last_finite_history(
                "mean_neighborhood_size"
            ),
        }


def run_simulation(run_config: Mapping[str, Any]) -> dict[str, Any]:
    """Run one ecological network-reciprocity simulation from a resolved config."""
    model = EcologicalNetworkReciprocityModel(run_config)
    payload = model.run()
    if bool(model.config["write_latest_run"]):
        _write_latest_run(model.config, payload)
    return payload


def _write_latest_run(run_config: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    output_dir = Path(str(run_config["data_dir"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "latest_run.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(_json_ready(payload), handle, indent=2, sort_keys=False)
        handle.write("\n")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def main() -> None:
    payload = run_simulation(resolve_config(active_config))
    summary = payload["summary"]
    print("[ecological_network_reciprocity] final summary")
    print(f"steps_done={summary['steps_done']}")
    print(f"final_population={summary['final_population']}")
    print(
        "mean_helping_trait="
        f"{summary['initial_mean_helping_trait']:.4f}"
        " -> "
        f"{summary['final_mean_helping_trait']:.4f}"
    )
    print(f"helping_trait_change={summary['helping_trait_change']:.4f}")
    print(
        "helping_invasion_frequency="
        f"{summary['initial_helping_invasion_frequency']:.4f}"
        " -> "
        f"{summary['final_helping_invasion_frequency']:.4f}"
    )
    print(
        f"latest_cooperation_spatial_clustering={summary['latest_cooperation_spatial_clustering']:.4f}"
    )
    print(
        f"latest_mean_neighborhood_size={summary['latest_mean_neighborhood_size']:.1f}"
    )


if __name__ == "__main__":
    main()
