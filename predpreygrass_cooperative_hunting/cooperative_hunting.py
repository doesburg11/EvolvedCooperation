#!/usr/bin/env python3
"""
cooperative_hunting.py

Module-only entrypoint. Run from the repo root with:
  ./.conda/bin/python -m predpreygrass_cooperative_hunting.cooperative_hunting

Minimal ecology (no learning) with:
1) Live pygame renderer
2) Lotka–Volterra-style oscillation plot (Predators vs Prey + phase plot)
3) Trait evolution: continuous hunt investment trait in [0,1]

Run:
  ./.conda/bin/python -m predpreygrass_cooperative_hunting.cooperative_hunting
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np


# This module is intentionally package-relative only. Avoid mutating sys.path.
if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m predpreygrass_cooperative_hunting.cooperative_hunting'."
    )

from .config.emerging_cooperation_config import (
    config as model_config,
    resolve_config,
)
from .utils.matplot_plotting import (
    plot_lv_style,
    plot_macro_energy_flows,
    plot_trait_selection_diagnostics,
    plot_trait_evolution,
)


# ============================================================
# CONFIG
# ============================================================

ConfigDict = Dict[str, Any]
CFG: ConfigDict = resolve_config(model_config)

# Populated by run_sim(); used by the plotting helpers.
LAST_ENERGY_FLOW_HISTORY: Dict[str, List[float]] = {}
LAST_TRAIT_SELECTION_HISTORY: Dict[str, List[float]] = {}
LAST_FINAL_PREDATOR_TRAITS: List[float] = []


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Predator:
    x: int
    y: int
    energy: float
    hunt_investment_trait: float  # continuous trait in [0,1]


@dataclass
class Prey:
    x: int
    y: int
    energy: float


def wrap(v: int, L: int) -> int:
    return v % L


def clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def logistic(v: float) -> float:
    """Numerically stable logistic transform."""
    if v >= 0.0:
        z = math.exp(-v)
        return 1.0 / (1.0 + z)
    z = math.exp(v)
    return z / (1.0 + z)


def step_distance(dx: int, dy: int) -> float:
    """Euclidean length of a single wrapped grid step."""
    return math.hypot(dx, dy)


def sample_prey_energy(config: ConfigDict | None = None) -> float:
    cfg = CFG if config is None else resolve_config(config)
    e = cfg["initial_prey_energy_mean"] + random.gauss(0.0, cfg["initial_prey_energy_stddev"])
    return max(cfg["initial_prey_energy_min"], e)


def sample_predator_hunt_investment_trait(config: ConfigDict | None = None) -> float:
    cfg = CFG if config is None else resolve_config(config)
    trait_min = float(cfg["initial_predator_hunt_investment_trait_min"])
    trait_max = float(cfg["initial_predator_hunt_investment_trait_max"])
    if not 0.0 <= trait_min <= 1.0:
        raise ValueError(
            "initial_predator_hunt_investment_trait_min must be within [0, 1]"
        )
    if not 0.0 <= trait_max <= 1.0:
        raise ValueError(
            "initial_predator_hunt_investment_trait_max must be within [0, 1]"
        )
    if trait_min > trait_max:
        raise ValueError(
            "initial_predator_hunt_investment_trait_min must be <= "
            "initial_predator_hunt_investment_trait_max"
        )
    return trait_min + (trait_max - trait_min) * random.random()


def init_grass_field(config: ConfigDict | None = None) -> np.ndarray:
    """Initialize per-cell grass energy."""
    cfg = CFG if config is None else resolve_config(config)
    return np.full(
        (cfg["grid_height"], cfg["grid_width"]),
        cfg["initial_grass_energy"],
        dtype=float,
    )


def energy_budget(preds: List[Predator], preys: List[Prey], grass: np.ndarray) -> Tuple[float, float, float, float]:
    """Return (predator_energy, prey_energy, grass_energy, total_energy)."""
    pred_e = sum(p.energy for p in preds)
    prey_e = sum(p.energy for p in preys)
    grass_e = float(np.sum(grass))
    return pred_e, prey_e, grass_e, pred_e + prey_e + grass_e


def drain_energy(energy: float, amount: float) -> Tuple[float, float]:
    """Consume up to `amount` from energy and return (new_energy, consumed)."""
    if amount <= 0.0 or energy <= 0.0:
        return energy, 0.0
    consumed = min(energy, amount)
    return energy - consumed, consumed


def threshold_synergy_kill_probability(
    *,
    hunter_count: int,
    total_contribution: float,
    prey_energy: float,
    config: ConfigDict | None = None,
) -> float:
    """
    Human-motivated threshold-synergy hunt rule.

    Variables:
    - `hunter_count`: number of predators participating in the local coalition.
    - `total_contribution`: summed effective effort `sum(predator_energy_i * trait_i)`.
    - `prey_energy`: current prey energy, used as a simple prey difficulty proxy.
    - `threshold_synergy_min_hunters`: minimum coalition size required to mount a hunt.
    - `threshold_synergy_formation_energy_factor`: formation threshold as a multiple of prey energy.
    - `threshold_synergy_execution_energy_factor`: midpoint of the kill sigmoid as a multiple of prey energy.
    - `threshold_synergy_success_steepness`: steepness of the sigmoid around the execution threshold.
    - `threshold_synergy_max_success_probability`: asymptotic success ceiling after thresholds are met.
    """
    cfg = CFG if config is None else resolve_config(config)
    min_hunters = int(cfg["threshold_synergy_min_hunters"])
    formation_factor = float(cfg["threshold_synergy_formation_energy_factor"])
    execution_factor = float(cfg["threshold_synergy_execution_energy_factor"])
    success_steepness = float(cfg["threshold_synergy_success_steepness"])
    max_success_probability = float(cfg["threshold_synergy_max_success_probability"])

    if min_hunters < 1:
        raise ValueError("threshold_synergy_min_hunters must be >= 1")
    if formation_factor <= 0.0:
        raise ValueError("threshold_synergy_formation_energy_factor must be > 0")
    if execution_factor <= 0.0:
        raise ValueError("threshold_synergy_execution_energy_factor must be > 0")
    if success_steepness <= 0.0:
        raise ValueError("threshold_synergy_success_steepness must be > 0")
    if not 0.0 <= max_success_probability <= 1.0:
        raise ValueError("threshold_synergy_max_success_probability must be within [0, 1]")

    if hunter_count < min_hunters:
        return 0.0

    formation_threshold = prey_energy * formation_factor
    if total_contribution < formation_threshold:
        return 0.0

    execution_threshold = prey_energy * execution_factor
    return clamp01(
        max_success_probability
        * logistic(success_steepness * (total_contribution - execution_threshold))
    )


# ============================================================
# CORE ECOLOGY
# ============================================================

def step_world(
    preds: List[Predator],
    preys: List[Prey],
    grass: np.ndarray,
    split_stats: dict | None = None,
    flow_stats: dict | None = None,
    config: ConfigDict | None = None,
) -> Tuple[List[Predator], List[Prey], np.ndarray]:
    """One tick update: grass regrowth, prey/predator budgets, hunting, cleanup, reproduction."""
    cfg = CFG if config is None else resolve_config(config)
    grid_width = cfg["grid_width"]
    grid_height = cfg["grid_height"]
    grass_regrowth_per_step = cfg["grass_regrowth_per_step"]
    max_grass_energy_per_cell = cfg["max_grass_energy_per_cell"]
    prey_move_probability = cfg["prey_move_probability"]
    prey_metabolic_cost = cfg["prey_metabolic_cost"]
    prey_move_cost_per_unit = cfg["prey_move_cost_per_unit"]
    prey_grass_intake_per_step = cfg["prey_grass_intake_per_step"]
    prey_reproduction_energy_threshold = cfg["prey_reproduction_energy_threshold"]
    prey_reproduction_probability = cfg["prey_reproduction_probability"]
    prey_offspring_energy_fraction = cfg["prey_offspring_energy_fraction"]
    prey_detection_radius = cfg["prey_detection_radius"]
    hunt_success_rule = cfg["hunt_success_rule"]
    base_hunt_success_probability = cfg["base_hunt_success_probability"]
    hunter_pool_radius = cfg["hunter_pool_radius"]
    share_prey_equally = cfg["share_prey_equally"]
    predator_crowding_soft_cap = cfg["predator_crowding_soft_cap"]
    initial_prey_count = cfg["initial_prey_count"]
    predator_metabolic_cost = cfg["predator_metabolic_cost"]
    predator_move_cost_per_unit = cfg["predator_move_cost_per_unit"]
    predator_cooperation_cost_per_unit = cfg["predator_cooperation_cost_per_unit"]
    predator_reproduction_energy_threshold = cfg["predator_reproduction_energy_threshold"]
    predator_reproduction_probability = cfg["predator_reproduction_probability"]
    offspring_birth_radius = cfg["offspring_birth_radius"]
    cooperation_mutation_probability = cfg["cooperation_mutation_probability"]
    cooperation_mutation_stddev = cfg["cooperation_mutation_stddev"]

    # ---- Grass regrowth
    grass_before = float(np.sum(grass))
    np.minimum(grass + grass_regrowth_per_step, max_grass_energy_per_cell, out=grass)
    grass_regen = float(np.sum(grass)) - grass_before
    grass_to_prey = 0.0
    prey_to_pred = 0.0
    prey_birth_transfer = 0.0
    pred_birth_transfer = 0.0
    prey_metab_loss = 0.0
    prey_move_loss = 0.0
    pred_metab_loss = 0.0
    pred_move_loss = 0.0
    pred_coop_loss = 0.0
    if flow_stats is not None:
        flow_stats["multi_hunter_hunter_count"] = 0.0
        flow_stats["multi_hunter_kills"] = 0.0
        flow_stats["group_hunt_effort_sum"] = 0.0
        flow_stats["successful_hunter_trait_sum"] = 0.0
        flow_stats["successful_hunter_count"] = 0.0
        flow_stats["reproducing_parent_trait_sum"] = 0.0
        flow_stats["reproducing_parent_count"] = 0.0
        flow_stats["dead_predator_trait_sum"] = 0.0
        flow_stats["dead_predator_count"] = 0.0

    # ---- Prey move + energy household + reproduce
    # Removal is applied in an explicit cleanup phase after engagements.
    preys_after_update: List[Prey] = []
    prey_dead_indices = set()
    newborn_preys: List[Prey] = []

    for pr in preys:
        move_distance = 0.0
        if random.random() < prey_move_probability:
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            pr.x = wrap(pr.x + dx, grid_width)
            pr.y = wrap(pr.y + dy, grid_height)
            move_distance = step_distance(dx, dy)

        parent_idx = len(preys_after_update)
        preys_after_update.append(pr)

        pr.energy, spent = drain_energy(pr.energy, prey_metabolic_cost)
        prey_metab_loss += spent
        if move_distance > 0.0:
            pr.energy, spent = drain_energy(pr.energy, prey_move_cost_per_unit * move_distance)
            prey_move_loss += spent
        if pr.energy <= 0.0:
            prey_dead_indices.add(parent_idx)
            continue

        bite = min(prey_grass_intake_per_step, float(grass[pr.y, pr.x]))
        if bite > 0.0:
            grass[pr.y, pr.x] -= bite
            pr.energy += bite
            grass_to_prey += bite

        if pr.energy <= 0.0:
            prey_dead_indices.add(parent_idx)
            continue

        if (
            pr.energy >= prey_reproduction_energy_threshold
            and random.random() < prey_reproduction_probability
        ):
            child_energy = pr.energy * prey_offspring_energy_fraction
            pr.energy -= child_energy
            cx = wrap(pr.x + random.choice([-1, 0, 1]), grid_width)
            cy = wrap(pr.y + random.choice([-1, 0, 1]), grid_height)
            prey_birth_transfer += child_energy
            newborn_preys.append(Prey(cx, cy, child_energy))
    preys = preys_after_update

    # ---- Index prey by cell
    prey_by_cell: Dict[Tuple[int, int], List[int]] = {}
    for i, pr in enumerate(preys):
        if i in prey_dead_indices:
            continue
        prey_by_cell.setdefault((pr.x, pr.y), []).append(i)

    # ---- Index predators by cell
    pred_by_cell: Dict[Tuple[int, int], List[int]] = {}
    for i, pd in enumerate(preds):
        pred_by_cell.setdefault((pd.x, pd.y), []).append(i)

    hunt_investment_trait_levels = [pd.hunt_investment_trait for pd in preds]

    # ---- Prey-centric engagements: capture resolution only (feeding/repro already applied this tick)
    prey_killed_indices = set()
    predators_committed = set()

    live_prey_indices = [i for i in range(len(preys)) if i not in prey_dead_indices]
    random.shuffle(live_prey_indices)

    for prey_idx in live_prey_indices:
        if prey_idx in prey_killed_indices:
            continue

        prey = preys[prey_idx]
        px, py = prey.x, prey.y

        candidate_pred_idxs: List[int] = []
        for dy in range(-prey_detection_radius, prey_detection_radius + 1):
            yy = (py + dy) % grid_height
            for dx in range(-prey_detection_radius, prey_detection_radius + 1):
                xx = (px + dx) % grid_width
                candidate_pred_idxs.extend(pred_by_cell.get((xx, yy), []))
        candidate_pred_idxs = [i for i in candidate_pred_idxs if i not in predators_committed]

        hunter_idxs: List[int] = []
        kill_success = False
        if candidate_pred_idxs:
            if hunt_success_rule == "probabilistic":
                hunter_idxs = candidate_pred_idxs
                sum_contrib = sum(hunt_investment_trait_levels[i] for i in hunter_idxs)
                pkill = 1.0 - (1.0 - base_hunt_success_probability) ** (sum_contrib + 1e-6)
                kill_success = random.random() < pkill
            elif hunt_success_rule == "threshold_synergy":
                prey_energy = prey.energy
                hunter_idxs = []
                for dy in range(-hunter_pool_radius, hunter_pool_radius + 1):
                    yy = (py + dy) % grid_height
                    for dx in range(-hunter_pool_radius, hunter_pool_radius + 1):
                        xx = (px + dx) % grid_width
                        hunter_idxs.extend(pred_by_cell.get((xx, yy), []))

                if hunter_idxs:
                    hunter_idxs = [i for i in hunter_idxs if i not in predators_committed]

                if hunter_idxs:
                    total_hunt_contribution = sum(
                        preds[i].energy * hunt_investment_trait_levels[i] for i in hunter_idxs
                    )
                    pkill = threshold_synergy_kill_probability(
                        hunter_count=len(hunter_idxs),
                        total_contribution=total_hunt_contribution,
                        prey_energy=prey_energy,
                        config=cfg,
                    )
                    kill_success = random.random() < pkill
            elif hunt_success_rule in ("energy_threshold", "energy_threshold_gate"):
                prey_energy = prey.energy
                hunter_idxs = []
                for dy in range(-hunter_pool_radius, hunter_pool_radius + 1):
                    yy = (py + dy) % grid_height
                    for dx in range(-hunter_pool_radius, hunter_pool_radius + 1):
                        xx = (px + dx) % grid_width
                        hunter_idxs.extend(pred_by_cell.get((xx, yy), []))

                if hunter_idxs:
                    hunter_idxs = [i for i in hunter_idxs if i not in predators_committed]

                if hunter_idxs:
                    total_hunt_contribution = sum(
                        preds[i].energy * hunt_investment_trait_levels[i] for i in hunter_idxs
                    )
                    if total_hunt_contribution < prey_energy:
                        kill_success = False
                    elif hunt_success_rule == "energy_threshold":
                        kill_success = True
                    else:
                        sum_contrib = sum(hunt_investment_trait_levels[i] for i in hunter_idxs)
                        pkill = 1.0 - (1.0 - base_hunt_success_probability) ** (sum_contrib + 1e-6)
                        kill_success = random.random() < pkill
            else:
                raise ValueError(f"Unknown hunt_success_rule: {hunt_success_rule}")

        if kill_success and hunter_idxs:
            prey_killed_indices.add(prey_idx)

            n_hunters = len(hunter_idxs)
            captured_energy = max(0.0, prey.energy)
            prey_to_pred += captured_energy
            shares: List[float]
            hunter_capacities = [preds[i].energy for i in hunter_idxs]
            hunter_efforts = [hunt_investment_trait_levels[i] for i in hunter_idxs]
            contribs = [capacity * effort for capacity, effort in zip(hunter_capacities, hunter_efforts)]
            total_contrib = sum(contribs)

            if captured_energy <= 1e-12:
                shares = [0.0] * n_hunters
            elif share_prey_equally:
                share = captured_energy / n_hunters
                shares = [share] * n_hunters
                for i in hunter_idxs:
                    preds[i].energy += share
            else:
                if total_contrib <= 1e-12:
                    share = captured_energy / n_hunters
                    shares = [share] * n_hunters
                    for i in hunter_idxs:
                        preds[i].energy += share
                else:
                    shares = []
                    for i, ci in zip(hunter_idxs, contribs):
                        gain = captured_energy * (ci / total_contrib)
                        shares.append(gain)
                        preds[i].energy += gain

            if flow_stats is not None:
                flow_stats["successful_hunter_trait_sum"] += sum(hunter_efforts)
                flow_stats["successful_hunter_count"] += n_hunters
            if split_stats is not None:
                split_stats["kills"] += 1
                split_stats["captured_energy_sum"] += captured_energy
                if n_hunters > 1:
                    # 0.0 = perfectly equal split, larger = more unequal split.
                    if captured_energy > 1e-12:
                        equal_share = captured_energy / n_hunters
                        inequality = sum(abs(s - equal_share) for s in shares) / captured_energy
                    else:
                        inequality = 0.0
                    split_stats["multi_hunter_kills"] += 1
                    split_stats["inequality_sum"] += inequality
                    if flow_stats is not None:
                        flow_stats["multi_hunter_hunter_count"] += n_hunters
                        flow_stats["multi_hunter_kills"] += 1.0
                        flow_stats["group_hunt_effort_sum"] += sum(hunter_efforts)
            predators_committed.update(hunter_idxs)
            continue

    # ---- Explicit removal phase (starved + hunted prey)
    prey_remove_indices = prey_dead_indices | prey_killed_indices
    if prey_remove_indices:
        preys = [pr for i, pr in enumerate(preys) if i not in prey_remove_indices]
    if newborn_preys:
        # Newborn prey enter after engagements and act from the next tick onward.
        preys.extend(newborn_preys)

    # ---- Predator costs, movement, reproduction, death
    updated_preds: List[Predator] = []
    newborn_preds: List[Predator] = []
    pred_dead_indices = set()
    predator_crowding_fraction = len(preds) / max(1, predator_crowding_soft_cap)
    prey_availability_ratio = len(preys) / max(1, initial_prey_count)
    predator_reproduction_scale = max(0.0, 1.0 - predator_crowding_fraction) * min(
        1.0,
        prey_availability_ratio,
    )

    random.shuffle(preds)
    for pd in preds:
        pd.energy, spent = drain_energy(pd.energy, predator_metabolic_cost)
        pred_metab_loss += spent
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        move_distance = step_distance(dx, dy)
        pd.energy, spent = drain_energy(pd.energy, predator_move_cost_per_unit * move_distance)
        pred_move_loss += spent
        pd.energy, spent = drain_energy(
            pd.energy,
            predator_cooperation_cost_per_unit * pd.hunt_investment_trait,
        )
        pred_coop_loss += spent

        pd.x = wrap(pd.x + dx, grid_width)
        pd.y = wrap(pd.y + dy, grid_height)

        if (
            pd.energy >= predator_reproduction_energy_threshold
            and random.random() < predator_reproduction_probability * predator_reproduction_scale
        ):
            if flow_stats is not None:
                flow_stats["reproducing_parent_trait_sum"] += pd.hunt_investment_trait
                flow_stats["reproducing_parent_count"] += 1.0
            pd.energy *= 0.5
            pred_birth_transfer += pd.energy
            child = Predator(pd.x, pd.y, pd.energy, pd.hunt_investment_trait)

            child.x = wrap(
                child.x + random.randint(-offspring_birth_radius, offspring_birth_radius),
                grid_width,
            )
            child.y = wrap(
                child.y + random.randint(-offspring_birth_radius, offspring_birth_radius),
                grid_height,
            )

            if random.random() < cooperation_mutation_probability:
                child.hunt_investment_trait = clamp01(
                    child.hunt_investment_trait + random.gauss(0.0, cooperation_mutation_stddev)
                )

            newborn_preds.append(child)

        parent_idx = len(updated_preds)
        updated_preds.append(pd)
        if pd.energy <= 0.0:
            pred_dead_indices.add(parent_idx)
            if flow_stats is not None:
                flow_stats["dead_predator_trait_sum"] += pd.hunt_investment_trait
                flow_stats["dead_predator_count"] += 1.0

    # ---- Explicit removal phase (starved predators)
    if pred_dead_indices:
        alive_updated_preds = [pd for i, pd in enumerate(updated_preds) if i not in pred_dead_indices]
    else:
        alive_updated_preds = updated_preds
    new_preds = alive_updated_preds + newborn_preds

    dissipative_loss = (
        prey_metab_loss
        + prey_move_loss
        + pred_metab_loss
        + pred_move_loss
        + pred_coop_loss
    )
    if flow_stats is not None:
        flow_stats["grass_regen"] = grass_regen
        flow_stats["grass_to_prey"] = grass_to_prey
        flow_stats["prey_to_pred"] = prey_to_pred
        flow_stats["prey_birth_transfer"] = prey_birth_transfer
        flow_stats["pred_birth_transfer"] = pred_birth_transfer
        flow_stats["prey_metab_loss"] = prey_metab_loss
        flow_stats["prey_move_loss"] = prey_move_loss
        flow_stats["pred_metab_loss"] = pred_metab_loss
        flow_stats["pred_move_loss"] = pred_move_loss
        flow_stats["pred_coop_loss"] = pred_coop_loss
        flow_stats["dissipative_loss"] = dissipative_loss

    return new_preds, preys, grass

# ============================================================
# RUN SIMULATION
# ============================================================


def run_sim(
    seed_override: int | None = None,
    config: ConfigDict | None = None,
) -> Tuple[
    List[int],
    List[int],
    List[float],
    List[float],
    List[float],
    List[Predator],
    bool,
    int | None,
]:
    global LAST_ENERGY_FLOW_HISTORY, LAST_TRAIT_SELECTION_HISTORY, LAST_FINAL_PREDATOR_TRAITS
    cfg = CFG if config is None else resolve_config(config)
    if seed_override is not None:
        random.seed(seed_override)
    elif cfg["random_seed"] is not None:
        random.seed(cfg["random_seed"])

    preds: List[Predator] = [
        Predator(
            random.randrange(cfg["grid_width"]),
            random.randrange(cfg["grid_height"]),
            cfg["initial_predator_energy"],
            sample_predator_hunt_investment_trait(cfg),
        )
        for _ in range(cfg["initial_predator_count"])
    ]
    preys: List[Prey] = [
        Prey(
            random.randrange(cfg["grid_width"]),
            random.randrange(cfg["grid_height"]),
            sample_prey_energy(cfg),
        )
        for _ in range(cfg["initial_prey_count"])
    ]
    grass = init_grass_field(cfg)
    live_renderer = None
    renderer_closed = False
    if cfg["enable_live_pygame_renderer"]:
        try:
            from .utils.pygame_renderer import PyGameRenderer
        except Exception as exc:
            raise RuntimeError("failed to import the live pygame renderer") from exc
        live_renderer = PyGameRenderer(
            cfg["grid_width"],
            cfg["grid_height"],
            cell_size=cfg["live_render_cell_size"],
            fps=cfg["live_render_frames_per_second"],
            auto_fit=True,
            title="Cooperative Hunting Viewer",
            total_steps=cfg["simulation_steps"],
        )

    pred_hist: List[int] = []
    prey_hist: List[int] = []
    mean_hunt_investment_trait_hist: List[float] = []
    var_hunt_investment_trait_hist: List[float] = []
    successful_group_hunt_mean_hunt_investment_trait_hist: List[float] = []

    split_stats = {
        "kills": 0,
        "captured_energy_sum": 0.0,
        "multi_hunter_kills": 0,
        "inequality_sum": 0.0,
    }
    pred_e, prey_e, grass_e, total_e = energy_budget(preds, preys, grass)
    init_total_e = total_e
    prev_total_e = total_e
    sum_abs_step_drift = 0.0
    sum_abs_invariant_residual = 0.0
    max_abs_invariant_residual = 0.0
    flow_totals = {
        "grass_regen": 0.0,
        "grass_to_prey": 0.0,
        "prey_to_pred": 0.0,
        "prey_birth_transfer": 0.0,
        "pred_birth_transfer": 0.0,
        "prey_metab_loss": 0.0,
        "prey_move_loss": 0.0,
        "pred_metab_loss": 0.0,
        "pred_move_loss": 0.0,
        "pred_coop_loss": 0.0,
        "dissipative_loss": 0.0,
    }
    flow_hist = {
        "grass_regen": [],
        "grass_to_prey": [],
        "prey_to_pred": [],
        "pred_coop_loss": [],
        "coop_net_hunt_return": [],
        "coop_cost_fraction_of_hunt_income": [],
        "prey_decay": [],
        "pred_decay": [],
        "net_balance": [],
        "grass_stock": [],
        "prey_stock": [],
        "pred_stock": [],
        "total_stock": [],
        "delta_total": [],
        "invariant_residual": [],
    }
    trait_selection_hist = {
        "mean_trait": [],
        "trait_p10": [],
        "trait_p50": [],
        "trait_p90": [],
        "successful_hunter_mean_trait": [],
        "successful_hunter_selection_diff": [],
        "successful_hunter_count": [],
        "reproducing_parent_mean_trait": [],
        "reproducing_parent_selection_diff": [],
        "reproducing_parent_count": [],
        "dead_predator_mean_trait": [],
        "dead_predator_selection_diff": [],
        "dead_predator_count": [],
    }

    extinction_step: int | None = None

    for t in range(cfg["simulation_steps"]):
        flow_stats: Dict[str, float] = {}
        preds, preys, grass = step_world(
            preds,
            preys,
            grass,
            split_stats=split_stats,
            flow_stats=flow_stats,
            config=cfg,
        )

        pred_n = len(preds)
        prey_n = len(preys)

        pred_hist.append(pred_n)
        prey_hist.append(prey_n)
        pred_e, prey_e, grass_e, total_e = energy_budget(preds, preys, grass)
        step_drift = total_e - prev_total_e
        sum_abs_step_drift += abs(step_drift)
        prev_total_e = total_e
        grass_in = flow_stats.get("grass_regen", 0.0)
        dissipative = flow_stats.get("dissipative_loss", 0.0)
        grass_to_prey = flow_stats.get("grass_to_prey", 0.0)
        prey_to_pred = flow_stats.get("prey_to_pred", 0.0)
        pred_coop_loss = flow_stats.get("pred_coop_loss", 0.0)
        coop_net_hunt_return = prey_to_pred - pred_coop_loss
        coop_cost_fraction = (
            pred_coop_loss / prey_to_pred if prey_to_pred > 1e-12 else float("nan")
        )
        prey_decay = flow_stats.get("prey_metab_loss", 0.0) + flow_stats.get("prey_move_loss", 0.0)
        pred_decay = (
            flow_stats.get("pred_metab_loss", 0.0)
            + flow_stats.get("pred_move_loss", 0.0)
            + flow_stats.get("pred_coop_loss", 0.0)
        )
        flow_net = grass_in - prey_decay - pred_decay
        net_balance = total_e
        expected_step_delta = grass_in - dissipative
        invariant_residual = step_drift - expected_step_delta
        abs_invariant_residual = abs(invariant_residual)
        sum_abs_invariant_residual += abs_invariant_residual
        if abs_invariant_residual > max_abs_invariant_residual:
            max_abs_invariant_residual = abs_invariant_residual
        for k in flow_totals:
            flow_totals[k] += flow_stats.get(k, 0.0)
        flow_hist["grass_regen"].append(grass_in)
        flow_hist["grass_to_prey"].append(grass_to_prey)
        flow_hist["prey_to_pred"].append(prey_to_pred)
        flow_hist["pred_coop_loss"].append(pred_coop_loss)
        flow_hist["coop_net_hunt_return"].append(coop_net_hunt_return)
        flow_hist["coop_cost_fraction_of_hunt_income"].append(coop_cost_fraction)
        flow_hist["prey_decay"].append(prey_decay)
        flow_hist["pred_decay"].append(pred_decay)
        flow_hist["net_balance"].append(net_balance)
        flow_hist["grass_stock"].append(grass_e)
        flow_hist["prey_stock"].append(prey_e)
        flow_hist["pred_stock"].append(pred_e)
        flow_hist["total_stock"].append(total_e)
        flow_hist["delta_total"].append(step_drift)
        flow_hist["invariant_residual"].append(invariant_residual)
        multi_hunter_hunter_count = flow_stats.get("multi_hunter_hunter_count", 0.0)
        if multi_hunter_hunter_count > 0.0:
            successful_group_hunt_mean_hunt_investment_trait = (
                flow_stats.get("group_hunt_effort_sum", 0.0) / multi_hunter_hunter_count
            )
        else:
            successful_group_hunt_mean_hunt_investment_trait = float("nan")
        successful_group_hunt_mean_hunt_investment_trait_hist.append(
            successful_group_hunt_mean_hunt_investment_trait
        )

        if pred_n > 0:
            trait_values = np.fromiter(
                (p.hunt_investment_trait for p in preds),
                dtype=float,
                count=pred_n,
            )
            mu = float(np.mean(trait_values))
            var = float(np.var(trait_values))
            p10, p50, p90 = np.quantile(trait_values, [0.10, 0.50, 0.90])
        else:
            mu = 0.0
            var = 0.0
            p10 = p50 = p90 = 0.0

        mean_hunt_investment_trait_hist.append(mu)
        var_hunt_investment_trait_hist.append(var)
        successful_hunter_count = flow_stats.get("successful_hunter_count", 0.0)
        reproducing_parent_count = flow_stats.get("reproducing_parent_count", 0.0)
        dead_predator_count = flow_stats.get("dead_predator_count", 0.0)
        successful_hunter_mean_trait = (
            flow_stats.get("successful_hunter_trait_sum", 0.0) / successful_hunter_count
            if successful_hunter_count > 0.0
            else float("nan")
        )
        reproducing_parent_mean_trait = (
            flow_stats.get("reproducing_parent_trait_sum", 0.0) / reproducing_parent_count
            if reproducing_parent_count > 0.0
            else float("nan")
        )
        dead_predator_mean_trait = (
            flow_stats.get("dead_predator_trait_sum", 0.0) / dead_predator_count
            if dead_predator_count > 0.0
            else float("nan")
        )
        trait_selection_hist["mean_trait"].append(mu)
        trait_selection_hist["trait_p10"].append(float(p10))
        trait_selection_hist["trait_p50"].append(float(p50))
        trait_selection_hist["trait_p90"].append(float(p90))
        trait_selection_hist["successful_hunter_mean_trait"].append(successful_hunter_mean_trait)
        trait_selection_hist["successful_hunter_selection_diff"].append(
            successful_hunter_mean_trait - mu
            if successful_hunter_count > 0.0
            else float("nan")
        )
        trait_selection_hist["successful_hunter_count"].append(successful_hunter_count)
        trait_selection_hist["reproducing_parent_mean_trait"].append(reproducing_parent_mean_trait)
        trait_selection_hist["reproducing_parent_selection_diff"].append(
            reproducing_parent_mean_trait - mu
            if reproducing_parent_count > 0.0
            else float("nan")
        )
        trait_selection_hist["reproducing_parent_count"].append(reproducing_parent_count)
        trait_selection_hist["dead_predator_mean_trait"].append(dead_predator_mean_trait)
        trait_selection_hist["dead_predator_selection_diff"].append(
            dead_predator_mean_trait - mu if dead_predator_count > 0.0 else float("nan")
        )
        trait_selection_hist["dead_predator_count"].append(dead_predator_count)

        if live_renderer is not None:
            live_stats = {
                "grass_cap": cfg["max_grass_energy_per_cell"],
                "grass_mean": float(grass.mean()),
                "grass_max": float(grass.max()),
                "mean_hunt_investment_trait": mu,
                "var_hunt_investment_trait": var,
                "successful_group_hunt_mean_hunt_investment_trait": (
                    successful_group_hunt_mean_hunt_investment_trait
                ),
                "multi_hunter_hunter_count": multi_hunter_hunter_count,
                "multi_hunter_kill_count": flow_stats.get("multi_hunter_kills", 0.0),
                "energy": {
                    "pred": pred_e,
                    "prey": prey_e,
                    "grass": grass_e,
                    "total": total_e,
                },
            }
            if not live_renderer.update_emerging(preds, preys, grass, t + 1, live_stats):
                renderer_closed = True
                print(f"Run interrupted at step {t+1}: live renderer window closed.")
                break

        if (t + 1) % 200 == 0:
            print(
                f"t={t+1:4d} preds={pred_n:4d} preys={prey_n:4d} "
                f"mean_hunt_investment_trait={mu:.3f} var={var:.3f}"
            )
        if cfg["log_energy_accounting"] and (
            (t + 1) % cfg["energy_log_interval_steps"] == 0
        ):
            inv_flag = (
                "OK"
                if abs_invariant_residual <= cfg["energy_invariant_tolerance"]
                else "WARN"
            )
            print(
                f"E t={t+1:4d} pred={pred_e:9.2f} prey={prey_e:9.2f} grass={grass_e:9.2f} "
                f"total={total_e:10.2f} d_step={step_drift:+8.2f} d_from_init={total_e - init_total_e:+10.2f} "
                f"grass_in={grass_in:7.2f} "
                f"g2p={grass_to_prey:7.2f} p2pred={prey_to_pred:7.2f} "
                f"prey_decay={prey_decay:7.2f} pred_decay={pred_decay:7.2f} "
                f"net_flow={flow_net:+8.2f} dissip={dissipative:7.2f} "
                f"exp_d={expected_step_delta:+8.2f} "
                f"resid={invariant_residual:+.6f} [{inv_flag}]"
            )

        if pred_n == 0 or prey_n == 0:
            extinction_step = t + 1
            print(f"Extinction at step {extinction_step}: preds={pred_n} preys={prey_n}")
            break

    if live_renderer is not None:
        live_renderer.close()

    steps_done = len(pred_hist)
    success = (
        extinction_step is None
        and not renderer_closed
        and steps_done == cfg["simulation_steps"]
    )
    if cfg["log_reward_sharing"]:
        kills = split_stats["kills"]
        multi = split_stats["multi_hunter_kills"]
        mean_captured_per_kill = (split_stats["captured_energy_sum"] / kills) if kills > 0 else 0.0
        mean_inequality = (split_stats["inequality_sum"] / multi) if multi > 0 else 0.0
        split_mode = "equal" if cfg["share_prey_equally"] else "contribution_weighted"
        print(
            f"Reward split [{split_mode}]: kills={kills} "
            f"mean_captured_energy={mean_captured_per_kill:.3f} "
            f"multi_hunter_kills={multi} "
            f"mean_split_inequality={mean_inequality:.3f}"
        )
    if cfg["log_energy_accounting"]:
        mean_abs_step_drift = (sum_abs_step_drift / steps_done) if steps_done > 0 else 0.0
        mean_abs_invariant_residual = (sum_abs_invariant_residual / steps_done) if steps_done > 0 else 0.0
        print(
            f"Energy budget: init_total={init_total_e:.2f} final_total={total_e:.2f} "
            f"net_delta={total_e - init_total_e:+.2f} mean_abs_step_delta={mean_abs_step_drift:.2f} "
            f"mean_abs_invariant_residual={mean_abs_invariant_residual:.6f} "
            f"max_abs_invariant_residual={max_abs_invariant_residual:.6f}"
        )
        print(
            "Energy flows (totals): "
            f"grass_regen={flow_totals['grass_regen']:.2f} "
            f"grass_to_prey={flow_totals['grass_to_prey']:.2f} "
            f"prey_to_pred={flow_totals['prey_to_pred']:.2f} "
            f"prey_birth_transfer={flow_totals['prey_birth_transfer']:.2f} "
            f"pred_birth_transfer={flow_totals['pred_birth_transfer']:.2f} "
            f"prey_metab_loss={flow_totals['prey_metab_loss']:.2f} "
            f"prey_move_loss={flow_totals['prey_move_loss']:.2f} "
            f"pred_metab_loss={flow_totals['pred_metab_loss']:.2f} "
            f"pred_move_loss={flow_totals['pred_move_loss']:.2f} "
            f"pred_coop_loss={flow_totals['pred_coop_loss']:.2f} "
            f"dissipative_loss={flow_totals['dissipative_loss']:.2f}"
        )
        total_hunt_income = flow_totals["prey_to_pred"]
        total_coop_cost = flow_totals["pred_coop_loss"]
        coop_tradeoff_msg = (
            "Cooperation tradeoff: "
            f"hunt_income={total_hunt_income:.2f} "
            f"predator_cooperation_cost={total_coop_cost:.2f} "
            f"net_after_coop={total_hunt_income - total_coop_cost:.2f}"
        )
        if total_hunt_income > 1e-12:
            coop_tradeoff_msg += f" cost_share_of_hunt_income={total_coop_cost / total_hunt_income:.3f}"
        else:
            coop_tradeoff_msg += " cost_share_of_hunt_income=n/a"
        print(coop_tradeoff_msg)
    LAST_ENERGY_FLOW_HISTORY = flow_hist
    LAST_TRAIT_SELECTION_HISTORY = trait_selection_hist
    LAST_FINAL_PREDATOR_TRAITS = [p.hunt_investment_trait for p in preds]
    return (
        pred_hist,
        prey_hist,
        mean_hunt_investment_trait_hist,
        var_hunt_investment_trait_hist,
        successful_group_hunt_mean_hunt_investment_trait_hist,
        preds,
        success,
        extinction_step,
    )

# ============================================================
# MAIN
# ============================================================


def main(config: ConfigDict | None = None) -> None:
    cfg = CFG if config is None else resolve_config(config)
    attempts = 0
    while True:
        seed = None
        if cfg["random_seed"] is not None:
            seed = cfg["random_seed"] + attempts

        (
            pred_hist,
            prey_hist,
            mean_hunt_investment_trait_hist,
            var_hunt_investment_trait_hist,
            _,
            preds_final,
            success,
            extinction_step,
        ) = run_sim(seed_override=seed, config=cfg)

        if not cfg["restart_after_extinction"] or success:
            break

        attempts += 1
        if attempts > cfg["max_restart_attempts"]:
            print(
                f"Failed to reach full {cfg['simulation_steps']} steps after "
                f"{cfg['max_restart_attempts']} restarts "
                f"(last extinction at step {extinction_step})."
            )
            break
        print(f"Restarting (attempt {attempts}/{cfg['max_restart_attempts']})...")

    print(
        f"RUN STATUS: {'FULL RUN OK' if success else 'EXTINCTION'} | "
        f"seed={seed} | steps_completed={len(pred_hist)} | "
        f"min_preds={min(pred_hist)} | min_preys={min(prey_hist)} | "
        f"final_preds={pred_hist[-1]} | final_preys={prey_hist[-1]}"
    )

    plot_lv_style(pred_hist, prey_hist)
    plot_trait_evolution(mean_hunt_investment_trait_hist, var_hunt_investment_trait_hist)

    if preds_final:
        # Summary stats for the final window and current population
        tail_n = min(200, len(mean_hunt_investment_trait_hist))
        if tail_n > 0:
            tail_mean = sum(mean_hunt_investment_trait_hist[-tail_n:]) / tail_n
            tail_var = sum(var_hunt_investment_trait_hist[-tail_n:]) / tail_n
            print(f"Mean hunt investment trait (last {tail_n}): {tail_mean:.3f}")
            print(f"Var  hunt investment trait (last {tail_n}): {tail_var:.4f}")
        final_mean = sum(p.hunt_investment_trait for p in preds_final) / len(preds_final)
        print(f"Mean hunt investment trait (final pop): {final_mean:.3f}")

    if cfg["plot_trait_selection_diagnostics"]:
        plot_trait_selection_diagnostics(
            LAST_TRAIT_SELECTION_HISTORY,
            LAST_FINAL_PREDATOR_TRAITS,
        )

    if cfg["plot_macro_energy_flows"]:
        plot_macro_energy_flows(LAST_ENERGY_FLOW_HISTORY)


if __name__ == "__main__":
    main()
