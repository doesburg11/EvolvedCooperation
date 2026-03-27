#!/usr/bin/env python3
"""
emerging_cooperation.py

Minimal ecology (no learning) with:
1) Heatmap of local clustering (local neighborhood mean cooperation level)
2) Spatial animation (live grid)
3) Lotka–Volterra-style oscillation plot (Predators vs Prey + phase plot)
4) Trait evolution: continuous cooperation level in [0,1]

Animation (maximum clarity):
- Base layer: clustering heatmap (local mean predator cooperation)
- Overlay: prey density heatmap with:
    * interpolation="nearest"
    * log scaling via LogNorm (so dense patches don’t wash out everything)
    * zeros masked (LogNorm can’t represent 0)
- Predators: open circles, edge color encodes cooperation trait

Fixes:
- Robust scatter.set_offsets() with true empty (0,2) numpy arrays
- Keep animation alive via fig.ani

Run:
  python emerging_cooperation.py
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple, Dict

import numpy as np
import matplotlib.pyplot as plt  # pyright: ignore[reportMissingModuleSource]
import matplotlib.animation as animation  # pyright: ignore[reportMissingModuleSource]
import matplotlib.cm as cm  # pyright: ignore[reportMissingModuleSource]
import matplotlib.colors as mcolors  # pyright: ignore[reportMissingModuleSource]
from matplotlib.colors import LogNorm  # pyright: ignore[reportMissingModuleSource]


# ============================================================
# CONFIG
# ============================================================

W, H = 60, 60

PRED_INIT = 65
PREY_INIT = 575
PRED_ENERGY_INIT = 1.4

STEPS = 1000

# --- Predator energetics ---
METAB_PRED = 0.055
MOVE_COST = 0.008
COOP_COST = 0.08       # keep cooperation costly without overwhelming coexistence
BIRTH_THRESH_PRED = 4.8
PRED_REPRO_PROB = 0.045
PRED_MAX = 800
MUT_RATE = 0.03
MUT_SIGMA = 0.08
LOCAL_BIRTH_R = 1

# --- Hunt mechanics ---
HUNT_R = 1
HUNT_RULE = "energy_threshold_gate"  # "energy_threshold_gate", "energy_threshold", or "probabilistic"
P0 = 0.56                           # final prey-collapse-penalty tuner winner in the tested 96-candidate grid
HUNTER_POOL_R = 1                    # used when HUNT_RULE starts with "energy_threshold"
EQUAL_SPLIT_REWARDS = True           # True: equal split, False: contribution-weighted split
COOPERATIVE_HUNTER_EFFORT_MIN = 0.65

# Optional reaction-norm plasticity (default OFF keeps pure nature dynamics).
# When enabled, expressed cooperation is trait-based but shifts deterministically
# with prey/predator ratio (no action channel / no learning policy).
ENABLE_PLASTICITY = False
PLASTICITY_STRENGTH = 0.25
PLASTICITY_RATIO_SETPOINT = 4.0
PLASTICITY_RATIO_SCALE = 2.0

LOG_REWARD_SPLIT = False             # keep live-render runs readable by default
LOG_ENERGY_BUDGET = False            # keep live-render runs readable by default
ENERGY_LOG_EVERY = 1                 # set >1 to reduce logging volume
ENERGY_INVARIANT_TOL = 1e-6          # tolerance for per-step invariant residual

# --- Prey dynamics ---
PREY_MOVE_PROB = 0.30
PREY_REPRO_PROB = 0.07
PREY_MAX = 3200
PREY_ENERGY_MEAN = 1.1
PREY_ENERGY_SIGMA = 0.25
PREY_ENERGY_MIN = 0.10
PREY_METAB = 0.05
PREY_MOVE_COST = 0.01
PREY_BIRTH_THRESH = 2.0
PREY_BIRTH_SPLIT = 0.42
PREY_BITE_SIZE = 0.24

# --- Grass dynamics ---
GRASS_INIT = 0.8
GRASS_MAX = 3.0
GRASS_REGROWTH = 0.055

# --- Visualization ---
ANIMATE = False
ANIMATE_SIMPLE_GRID = False
ANIM_STEPS = 500
ANIM_INTERVAL_MS = 40
PLOT_MACRO_ENERGY_FLOWS = True
LIVE_RENDER_PYGAME = True
LIVE_RENDER_FPS = 30
LIVE_RENDER_CELL_SIZE = 14      # target upper bound; pygame renderer auto-fits lower on smaller displays

CLUST_R = 2

# Predator marker look
PRED_SIZE = 70
PRED_EDGE_LINEWIDTH = 1.2

# Layering (alpha)
PREY_DENSITY_ALPHA = 0.35   # overlay strength
CLUSTER_ALPHA = 1.0         # base clustering heatmap alpha

SEED = 0                    # deterministic default seed for the current baseline run length
RESTART_ON_EXTINCTION = False
MAX_RESTARTS = 60           # only used when restart mode is enabled

# Populated by run_sim(); used by plot_macro_energy_flows().
LAST_ENERGY_FLOW_HISTORY: Dict[str, List[float]] = {}
LAST_GRASS_SNAPS: List[np.ndarray] = []


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Predator:
    x: int
    y: int
    energy: float
    coop: float  # continuous trait in [0,1]


@dataclass
class Prey:
    x: int
    y: int
    energy: float


def wrap(v: int, L: int) -> int:
    return v % L


def clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def sample_prey_energy() -> float:
    e = PREY_ENERGY_MEAN + random.gauss(0.0, PREY_ENERGY_SIGMA)
    return max(PREY_ENERGY_MIN, e)


def init_grass_field() -> np.ndarray:
    """Initialize per-cell grass energy."""
    return np.full((H, W), GRASS_INIT, dtype=float)


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


def plasticity_shift(prey_count: int, pred_count: int) -> float:
    """Deterministic reaction-norm shift in expressed cooperation."""
    if not ENABLE_PLASTICITY:
        return 0.0
    ratio = prey_count / max(1, pred_count)
    scale = max(1e-9, PLASTICITY_RATIO_SCALE)
    return PLASTICITY_STRENGTH * float(np.tanh((ratio - PLASTICITY_RATIO_SETPOINT) / scale))


# ============================================================
# CORE ECOLOGY
# ============================================================

def step_world(
    preds: List[Predator],
    preys: List[Prey],
    grass: np.ndarray,
    split_stats: dict | None = None,
    flow_stats: dict | None = None,
) -> Tuple[List[Predator], List[Prey], np.ndarray]:
    """One tick update: grass regrowth, prey/predator budgets, hunting, cleanup, reproduction."""

    # ---- Grass regrowth
    grass_before = float(np.sum(grass))
    np.minimum(grass + GRASS_REGROWTH, GRASS_MAX, out=grass)
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
        flow_stats["cooperative_hunter_count"] = 0.0
        flow_stats["multi_hunter_hunter_count"] = 0.0
        flow_stats["multi_hunter_kills"] = 0.0
        flow_stats["group_hunt_effort_sum"] = 0.0

    # ---- Prey move + energy household + reproduce
    # Removal is applied in an explicit cleanup phase after engagements.
    preys_after_update: List[Prey] = []
    prey_dead_indices = set()
    newborn_preys: List[Prey] = []
    prey_count = len(preys)

    crowd = prey_count / max(1, PREY_MAX)
    repro_scale = max(0.0, 1.0 - crowd)

    for pr in preys:
        moved = False
        if random.random() < PREY_MOVE_PROB:
            pr.x = wrap(pr.x + random.choice([-1, 0, 1]), W)
            pr.y = wrap(pr.y + random.choice([-1, 0, 1]), H)
            moved = True

        parent_idx = len(preys_after_update)
        preys_after_update.append(pr)

        pr.energy, spent = drain_energy(pr.energy, PREY_METAB)
        prey_metab_loss += spent
        if moved:
            pr.energy, spent = drain_energy(pr.energy, PREY_MOVE_COST)
            prey_move_loss += spent
        if pr.energy <= 0.0:
            prey_dead_indices.add(parent_idx)
            continue

        bite = min(PREY_BITE_SIZE, float(grass[pr.y, pr.x]))
        if bite > 0.0:
            grass[pr.y, pr.x] -= bite
            pr.energy += bite
            grass_to_prey += bite

        if pr.energy <= 0.0:
            prey_dead_indices.add(parent_idx)
            continue

        if pr.energy >= PREY_BIRTH_THRESH and random.random() < PREY_REPRO_PROB * repro_scale:
            child_energy = pr.energy * PREY_BIRTH_SPLIT
            pr.energy -= child_energy
            prey_birth_transfer += child_energy
            cx = wrap(pr.x + random.choice([-1, 0, 1]), W)
            cy = wrap(pr.y + random.choice([-1, 0, 1]), H)
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

    live_prey_count = len(preys) - len(prey_dead_indices)
    coop_shift = plasticity_shift(live_prey_count, len(preds))
    expressed_coop = [clamp01(pd.coop + coop_shift) for pd in preds]
    pred_expr_by_id = {id(pd): ec for pd, ec in zip(preds, expressed_coop)}

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
        for dy in range(-HUNT_R, HUNT_R + 1):
            yy = (py + dy) % H
            for dx in range(-HUNT_R, HUNT_R + 1):
                xx = (px + dx) % W
                candidate_pred_idxs.extend(pred_by_cell.get((xx, yy), []))
        candidate_pred_idxs = [i for i in candidate_pred_idxs if i not in predators_committed]

        hunter_idxs: List[int] = []
        kill_success = False
        if candidate_pred_idxs:
            if HUNT_RULE == "probabilistic":
                hunter_idxs = candidate_pred_idxs
                sum_contrib = sum(expressed_coop[i] for i in hunter_idxs)
                pkill = 1.0 - (1.0 - P0) ** (sum_contrib + 1e-6)
                kill_success = random.random() < pkill
            elif HUNT_RULE in ("energy_threshold", "energy_threshold_gate"):
                prey_energy = prey.energy
                hunter_idxs = []
                for dy in range(-HUNTER_POOL_R, HUNTER_POOL_R + 1):
                    yy = (py + dy) % H
                    for dx in range(-HUNTER_POOL_R, HUNTER_POOL_R + 1):
                        xx = (px + dx) % W
                        hunter_idxs.extend(pred_by_cell.get((xx, yy), []))

                if hunter_idxs:
                    hunter_idxs = [i for i in hunter_idxs if i not in predators_committed]

                if hunter_idxs:
                    total_hunt_contribution = sum(preds[i].energy * expressed_coop[i] for i in hunter_idxs)
                    if total_hunt_contribution < prey_energy:
                        kill_success = False
                    elif HUNT_RULE == "energy_threshold":
                        kill_success = True
                    else:
                        sum_contrib = sum(expressed_coop[i] for i in hunter_idxs)
                        pkill = 1.0 - (1.0 - P0) ** (sum_contrib + 1e-6)
                        kill_success = random.random() < pkill
            else:
                raise ValueError(f"Unknown HUNT_RULE: {HUNT_RULE}")

        if kill_success and hunter_idxs:
            prey_killed_indices.add(prey_idx)

            n_hunters = len(hunter_idxs)
            captured_energy = max(0.0, prey.energy)
            prey_to_pred += captured_energy
            shares: List[float]
            hunter_capacities = [preds[i].energy for i in hunter_idxs]
            hunter_efforts = [expressed_coop[i] for i in hunter_idxs]
            contribs = [capacity * effort for capacity, effort in zip(hunter_capacities, hunter_efforts)]
            total_contrib = sum(contribs)

            if captured_energy <= 1e-12:
                shares = [0.0] * n_hunters
            elif EQUAL_SPLIT_REWARDS:
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

            if split_stats is not None:
                split_stats["kills"] += 1
                split_stats["captured_energy_sum"] += captured_energy
                if n_hunters > 1:
                    # 0.0 = perfectly equal split, larger = more unequal split.
                    if captured_energy > 1e-12:
                        equal_share = captured_energy / n_hunters
                        inequality = sum(abs(s - equal_share) for s in shares) / captured_energy
                        reward_shares = [s / captured_energy for s in shares]
                    else:
                        inequality = 0.0
                        reward_shares = [0.0] * n_hunters
                    cooperative_hunter_count = sum(
                        1
                        for effort, reward_share in zip(hunter_efforts, reward_shares)
                        if effort >= COOPERATIVE_HUNTER_EFFORT_MIN and reward_share > 1e-12
                    )
                    split_stats["multi_hunter_kills"] += 1
                    split_stats["inequality_sum"] += inequality
                    if flow_stats is not None:
                        flow_stats["cooperative_hunter_count"] += cooperative_hunter_count
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
    pred_crowd = len(preds) / max(1, PRED_MAX)
    prey_availability = len(preys) / max(1, PREY_INIT)
    pred_repro_scale = max(0.0, 1.0 - pred_crowd) * min(1.0, prey_availability)

    random.shuffle(preds)
    for pd in preds:
        pd.energy, spent = drain_energy(pd.energy, METAB_PRED)
        pred_metab_loss += spent
        pd.energy, spent = drain_energy(pd.energy, MOVE_COST)
        pred_move_loss += spent
        coop_for_cost = pred_expr_by_id.get(id(pd), pd.coop)
        pd.energy, spent = drain_energy(pd.energy, COOP_COST * coop_for_cost)
        pred_coop_loss += spent

        pd.x = wrap(pd.x + random.choice([-1, 0, 1]), W)
        pd.y = wrap(pd.y + random.choice([-1, 0, 1]), H)

        if (
            pd.energy >= BIRTH_THRESH_PRED
            and random.random() < PRED_REPRO_PROB * pred_repro_scale
        ):
            pd.energy *= 0.5
            pred_birth_transfer += pd.energy
            child = Predator(pd.x, pd.y, pd.energy, pd.coop)

            child.x = wrap(child.x + random.randint(-LOCAL_BIRTH_R, LOCAL_BIRTH_R), W)
            child.y = wrap(child.y + random.randint(-LOCAL_BIRTH_R, LOCAL_BIRTH_R), H)

            if random.random() < MUT_RATE:
                child.coop = clamp01(child.coop + random.gauss(0.0, MUT_SIGMA))

            newborn_preds.append(child)

        parent_idx = len(updated_preds)
        updated_preds.append(pd)
        if pd.energy <= 0.0:
            pred_dead_indices.add(parent_idx)

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
        flow_stats["coop_shift"] = coop_shift
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
# CLUSTERING HEATMAP
# ============================================================

def compute_local_clustering_field(preds: List[Predator], r: int) -> np.ndarray:
    """HxW field: mean predator coop in neighborhood radius r around each cell."""
    cell_sum = np.zeros((H, W), dtype=float)
    cell_cnt = np.zeros((H, W), dtype=int)

    for pd in preds:
        cell_sum[pd.y, pd.x] += pd.coop
        cell_cnt[pd.y, pd.x] += 1

    field = np.zeros((H, W), dtype=float)

    for y in range(H):
        for x in range(W):
            s = 0.0
            c = 0
            for dy in range(-r, r + 1):
                yy = (y + dy) % H
                for dx in range(-r, r + 1):
                    xx = (x + dx) % W
                    s += cell_sum[yy, xx]
                    c += cell_cnt[yy, xx]
            field[y, x] = (s / c) if c > 0 else 0.0

    return field


def compute_prey_density(preys: List[Prey]) -> np.ndarray:
    """HxW array: prey count per cell."""
    dens = np.zeros((H, W), dtype=float)
    for pr in preys:
        dens[pr.y, pr.x] += 1.0
    return dens


def mask_zeros_for_lognorm(arr: np.ndarray) -> np.ma.MaskedArray:
    """Mask zeros (and negatives) so LogNorm can be used safely."""
    return np.ma.masked_less_equal(arr, 0.0)


# ============================================================
# RUN SIMULATION
# ============================================================

def run_sim(seed_override: int | None = None) -> Tuple[
    List[int],
    List[int],
    List[float],
    List[float],
    List[float],
    List[float],
    List[List[Predator]],
    List[List[Prey]],
    List[Predator],
    bool,
    int | None,
]:
    global LAST_ENERGY_FLOW_HISTORY, LAST_GRASS_SNAPS
    if seed_override is not None:
        random.seed(seed_override)
    elif SEED is not None:
        random.seed(SEED)

    preds: List[Predator] = [
        Predator(random.randrange(W), random.randrange(H), PRED_ENERGY_INIT, random.random())
        for _ in range(PRED_INIT)
    ]
    preys: List[Prey] = [
        Prey(random.randrange(W), random.randrange(H), sample_prey_energy())
        for _ in range(PREY_INIT)
    ]
    grass = init_grass_field()
    live_renderer = None
    renderer_closed = False
    if LIVE_RENDER_PYGAME:
        try:
            try:
                from .pygame_renderer import PyGameRenderer
            except ImportError:
                from pygame_renderer import PyGameRenderer
        except Exception as exc:
            raise RuntimeError("failed to import the live pygame renderer") from exc
        live_renderer = PyGameRenderer(
            W,
            H,
            cell_size=LIVE_RENDER_CELL_SIZE,
            fps=LIVE_RENDER_FPS,
            auto_fit=True,
            title="Emerging Cooperation Viewer",
        )

    pred_hist: List[int] = []
    prey_hist: List[int] = []
    mean_coop_hist: List[float] = []
    var_coop_hist: List[float] = []
    cooperative_hunter_share_hist: List[float] = []
    group_hunt_mean_effort_hist: List[float] = []

    preds_snaps: List[List[Predator]] = []
    preys_snaps: List[List[Prey]] = []
    grass_snaps: List[np.ndarray] = []
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
        "coop_shift_sum": 0.0,
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
        "coop_shift": [],
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

    extinction_step: int | None = None

    for t in range(STEPS):
        flow_stats: Dict[str, float] = {}
        preds, preys, grass = step_world(
            preds,
            preys,
            grass,
            split_stats=split_stats,
            flow_stats=flow_stats,
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
        coop_shift = flow_stats.get("coop_shift", 0.0)
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
        flow_totals["coop_shift_sum"] += coop_shift
        flow_hist["grass_regen"].append(grass_in)
        flow_hist["coop_shift"].append(coop_shift)
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
            cooperative_hunter_share = flow_stats.get("cooperative_hunter_count", 0.0) / multi_hunter_hunter_count
            group_hunt_mean_effort = flow_stats.get("group_hunt_effort_sum", 0.0) / multi_hunter_hunter_count
        else:
            cooperative_hunter_share = float("nan")
            group_hunt_mean_effort = float("nan")
        cooperative_hunter_share_hist.append(cooperative_hunter_share)
        group_hunt_mean_effort_hist.append(group_hunt_mean_effort)

        if pred_n > 0:
            mu = sum(p.coop for p in preds) / pred_n
            var = sum((p.coop - mu) ** 2 for p in preds) / pred_n
        else:
            mu = 0.0
            var = 0.0

        mean_coop_hist.append(mu)
        var_coop_hist.append(var)

        if live_renderer is not None:
            live_stats = {
                "grass_cap": GRASS_MAX,
                "grass_mean": float(grass.mean()),
                "grass_max": float(grass.max()),
                "mean_coop": mu,
                "var_coop": var,
                "cooperative_hunter_share": cooperative_hunter_share,
                "group_hunt_mean_effort": group_hunt_mean_effort,
                "cooperative_hunter_count": flow_stats.get("cooperative_hunter_count", 0.0),
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

        if ANIMATE and t < ANIM_STEPS:
            preds_snaps.append([Predator(p.x, p.y, p.energy, p.coop) for p in preds])
            preys_snaps.append([Prey(p.x, p.y, p.energy) for p in preys])
            grass_snaps.append(grass.copy())

        if (t + 1) % 200 == 0:
            print(f"t={t+1:4d} preds={pred_n:4d} preys={prey_n:4d} mean_coop={mu:.3f} var={var:.3f}")
        if LOG_ENERGY_BUDGET and ((t + 1) % ENERGY_LOG_EVERY == 0):
            inv_flag = "OK" if abs_invariant_residual <= ENERGY_INVARIANT_TOL else "WARN"
            print(
                f"E t={t+1:4d} pred={pred_e:9.2f} prey={prey_e:9.2f} grass={grass_e:9.2f} "
                f"total={total_e:10.2f} d_step={step_drift:+8.2f} d_from_init={total_e - init_total_e:+10.2f} "
                f"shift={coop_shift:+6.3f} grass_in={grass_in:7.2f} "
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
    success = extinction_step is None and not renderer_closed and steps_done == STEPS
    if LOG_REWARD_SPLIT:
        kills = split_stats["kills"]
        multi = split_stats["multi_hunter_kills"]
        mean_captured_per_kill = (split_stats["captured_energy_sum"] / kills) if kills > 0 else 0.0
        mean_inequality = (split_stats["inequality_sum"] / multi) if multi > 0 else 0.0
        split_mode = "equal" if EQUAL_SPLIT_REWARDS else "contribution_weighted"
        print(
            f"Reward split [{split_mode}]: kills={kills} "
            f"mean_captured_energy={mean_captured_per_kill:.3f} "
            f"multi_hunter_kills={multi} "
            f"mean_split_inequality={mean_inequality:.3f}"
        )
    if LOG_ENERGY_BUDGET:
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
            f"mean_coop_shift={(flow_totals['coop_shift_sum'] / max(1, steps_done)):+.4f} "
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
            f"coop_cost={total_coop_cost:.2f} "
            f"net_after_coop={total_hunt_income - total_coop_cost:.2f}"
        )
        if total_hunt_income > 1e-12:
            coop_tradeoff_msg += f" cost_share_of_hunt_income={total_coop_cost / total_hunt_income:.3f}"
        else:
            coop_tradeoff_msg += " cost_share_of_hunt_income=n/a"
        print(coop_tradeoff_msg)
    LAST_ENERGY_FLOW_HISTORY = flow_hist
    LAST_GRASS_SNAPS = grass_snaps
    return (
        pred_hist,
        prey_hist,
        mean_coop_hist,
        var_coop_hist,
        cooperative_hunter_share_hist,
        group_hunt_mean_effort_hist,
        preds_snaps,
        preys_snaps,
        preds,
        success,
        extinction_step,
    )


# ============================================================
# PLOTS
# ============================================================

def plot_lv_style(pred_hist: List[int], prey_hist: List[int]) -> None:
    plt.figure()
    plt.plot(prey_hist, label="Prey")
    plt.plot(pred_hist, label="Predators")
    plt.xlabel("Time step")
    plt.ylabel("Count")
    plt.title("Population oscillations (Lotka–Volterra style)")
    plt.legend()
    plt.show()

    plt.figure()
    plt.plot(prey_hist, pred_hist)
    plt.xlabel("Prey count")
    plt.ylabel("Predator count")
    plt.title("Phase plot (Predators vs Prey)")
    plt.show()


def plot_trait_evolution(mean_coop_hist: List[float], var_coop_hist: List[float]) -> None:
    plt.figure()
    plt.plot(mean_coop_hist)
    plt.xlabel("Time step")
    plt.ylabel("Mean cooperation level")
    plt.title("Trait evolution: mean cooperation level over time")
    plt.ylim(0, 1)
    plt.show()

    plt.figure()
    plt.plot(var_coop_hist)
    plt.xlabel("Time step")
    plt.ylabel("Variance of cooperation level")
    plt.title("Trait evolution: variance over time")
    plt.show()


def plot_macro_energy_flows(flow_hist: Dict[str, List[float]]) -> None:
    """Plot macro energy flow channels per tick plus net balance diagnostics."""
    steps = len(flow_hist.get("grass_regen", []))
    if steps == 0:
        print("No energy-flow history available for plotting.")
        return

    t = np.arange(1, steps + 1)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10.0, 9.2), sharex=True)

    ax1.plot(t, flow_hist["grass_regen"], label="photosynthesis -> grass")
    ax1.plot(t, flow_hist["grass_to_prey"], label="grass -> prey")
    ax1.plot(t, flow_hist["prey_to_pred"], label="prey -> predator")
    ax1.plot(t, flow_hist["prey_decay"], label="prey -> decay")
    ax1.plot(t, flow_hist["pred_decay"], label="predator -> decay")
    ax1.set_ylabel("Energy per tick")
    ax1.set_title("Macro Energy Flows Per Tick")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.grid(True, alpha=0.25)

    ax2.plot(t, flow_hist["prey_to_pred"], label="hunt income")
    ax2.plot(t, flow_hist["pred_coop_loss"], label="cooperation cost")
    ax2.plot(t, flow_hist["coop_net_hunt_return"], label="net after coop", color="black", linewidth=2.0)
    ax2.axhline(0.0, color="gray", linewidth=1.0, alpha=0.7)
    ax2.set_ylabel("Energy per tick")
    ax2.set_title("Cooperation Cost vs Hunt Income")
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, alpha=0.25)

    ax3.plot(t, flow_hist["grass_stock"], label="grass energy stock")
    ax3.plot(t, flow_hist["prey_stock"], label="prey energy stock")
    ax3.plot(t, flow_hist["pred_stock"], label="predator energy stock")
    ax3.plot(
        t,
        flow_hist["total_stock"],
        label="total energy stock (sum)",
        color="black",
        linewidth=2.0,
    )
    ax3.set_xlabel("Time step")
    ax3.set_ylabel("Energy stock")
    ax3.set_title("Net Balance (Cumulative Energy Stocks)")
    ax3.legend(loc="upper right", fontsize=9)
    ax3.grid(True, alpha=0.25)

    fig.tight_layout()
    plt.show()


# ============================================================
# ANIMATION (disentangled 3-panel view)
# ============================================================

def animate_world(preds_snaps: List[List[Predator]], preys_snaps: List[List[Prey]]) -> None:
    if not preds_snaps:
        print("No snapshots recorded for animation.")
        return

    n_frames = min(len(preds_snaps), len(preys_snaps))
    if n_frames <= 0:
        print("No frames available for animation.")
        return

    fig, (ax_clust, ax_prey, ax_pred) = plt.subplots(1, 3, figsize=(16.0, 5.2), constrained_layout=True)

    # Panel 1: local cooperation heatmap
    clust0 = compute_local_clustering_field(preds_snaps[0], CLUST_R)
    clust_im = ax_clust.imshow(
        clust0,
        origin="lower",
        interpolation="nearest",
        cmap="viridis",
        vmin=0.0,
        vmax=1.0,
    )
    clust_cb = fig.colorbar(clust_im, ax=ax_clust)
    clust_cb.set_label("Local mean cooperation")
    ax_clust.set_title("Local Cooperation")

    # Panel 2: prey density heatmap (log scale)
    prey0 = compute_prey_density(preys_snaps[0])
    prey0m = mask_zeros_for_lognorm(prey0)
    prey_vmax0 = max(1.0, float(prey0.max()))
    prey_im = ax_prey.imshow(
        prey0m,
        origin="lower",
        interpolation="nearest",
        cmap="magma",
        norm=LogNorm(vmin=1.0, vmax=prey_vmax0),
    )
    prey_cb = fig.colorbar(prey_im, ax=ax_prey)
    prey_cb.set_label("Prey density (log; zeros masked)")
    ax_prey.set_title("Prey Density")

    # Panel 3: predator positions colored by coop trait
    ax_pred.set_facecolor("#f5f5f5")
    empty_xy = np.empty((0, 2), dtype=float)
    pred_cmap = cm.get_cmap()
    pred_norm = mcolors.Normalize(vmin=0.0, vmax=1.0)
    pred_scatter = ax_pred.scatter(
        [],
        [],
        marker="o",
        s=PRED_SIZE * 0.8,
        facecolors=np.empty((0, 4), dtype=float),
        edgecolors="black",
        linewidths=0.35,
        label="Predator position",
    )
    pred_cb = fig.colorbar(cm.ScalarMappable(norm=pred_norm, cmap=pred_cmap), ax=ax_pred)
    pred_cb.set_label("Predator coop trait")
    ax_pred.set_title("Predator Trait Map")
    ax_pred.legend(loc="upper right", fontsize=9, frameon=True)

    for ax in (ax_clust, ax_prey, ax_pred):
        ax.set_xlim(-0.5, W - 0.5)
        ax.set_ylim(-0.5, H - 0.5)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

    title = fig.suptitle(f"Live grid (step 1/{n_frames})")

    def init():
        pred_scatter.set_offsets(empty_xy)
        pred_scatter.set_facecolors(np.empty((0, 4), dtype=float))
        title.set_text(f"Live grid (step 1/{n_frames})")
        return clust_im, prey_im, pred_scatter, title

    def update(frame_idx: int):
        preds = preds_snaps[frame_idx]
        preys = preys_snaps[frame_idx]

        # Panel 1 update
        clust = compute_local_clustering_field(preds, CLUST_R)
        clust_im.set_data(clust)

        # Panel 2 update
        prey_d = compute_prey_density(preys)
        prey_dm = mask_zeros_for_lognorm(prey_d)
        vmax = max(1.0, float(prey_d.max()))
        prey_im.norm = LogNorm(vmin=1.0, vmax=vmax)
        prey_im.set_data(prey_dm)

        # Panel 3 update
        if preds:
            pred_xy = np.array([(p.x, p.y) for p in preds], dtype=float)
            coop = np.array([p.coop for p in preds], dtype=float)
            colors = pred_cmap(pred_norm(coop))
            pred_scatter.set_offsets(pred_xy)
            pred_scatter.set_facecolors(colors)
        else:
            pred_scatter.set_offsets(empty_xy)
            pred_scatter.set_facecolors(np.empty((0, 4), dtype=float))

        title.set_text(f"Live grid (step {frame_idx+1}/{n_frames})")
        return clust_im, prey_im, pred_scatter, title

    fig.ani = animation.FuncAnimation(
        fig,
        update,
        frames=n_frames,
        init_func=init,
        interval=ANIM_INTERVAL_MS,
        blit=False,
        repeat=False,
    )

    plt.show()


def animate_simple_grid(
    preds_snaps: List[List[Predator]],
    preys_snaps: List[List[Prey]],
    grass_snaps: List[np.ndarray],
) -> None:
    """Simple live grid: grass as background, prey and predators as markers."""
    if not preds_snaps or not preys_snaps or not grass_snaps:
        print("No snapshots recorded for simple grid animation.")
        return

    n_frames = min(len(preds_snaps), len(preys_snaps), len(grass_snaps))
    if n_frames <= 0:
        print("No frames available for simple grid animation.")
        return

    fig, ax = plt.subplots()
    grass_im = ax.imshow(
        grass_snaps[0],
        origin="lower",
        cmap="YlGn",
        interpolation="nearest",
        vmin=0.0,
        vmax=GRASS_MAX,
    )
    cb = plt.colorbar(grass_im, ax=ax)
    cb.set_label("Grass energy")

    empty_xy = np.empty((0, 2), dtype=float)

    prey_scatter = ax.scatter(
        [], [],
        marker="s",
        s=16,
        c="#3b82f6",
        edgecolors="white",
        linewidths=0.3,
        label="Prey",
    )
    pred_scatter = ax.scatter(
        [], [],
        marker="o",
        s=28,
        c="#ef4444",
        edgecolors="black",
        linewidths=0.4,
        label="Predator",
    )

    ax.set_xlim(-0.5, W - 0.5)
    ax.set_ylim(-0.5, H - 0.5)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend(loc="upper right")

    def init():
        grass_im.set_data(grass_snaps[0])
        prey_scatter.set_offsets(empty_xy)
        pred_scatter.set_offsets(empty_xy)
        ax.set_title("Simple live grid (grass + prey + predators)")
        return grass_im, prey_scatter, pred_scatter

    def update(frame_idx: int):
        preds = preds_snaps[frame_idx]
        preys = preys_snaps[frame_idx]
        grass = grass_snaps[frame_idx]

        grass_im.set_data(grass)

        if preys:
            prey_xy = np.array([(p.x, p.y) for p in preys], dtype=float)
            prey_scatter.set_offsets(prey_xy)
        else:
            prey_scatter.set_offsets(empty_xy)

        if preds:
            pred_xy = np.array([(p.x, p.y) for p in preds], dtype=float)
            pred_scatter.set_offsets(pred_xy)
        else:
            pred_scatter.set_offsets(empty_xy)

        ax.set_title(f"Simple live grid (step {frame_idx+1}/{n_frames})")
        return grass_im, prey_scatter, pred_scatter

    fig.ani = animation.FuncAnimation(
        fig,
        update,
        frames=n_frames,
        init_func=init,
        interval=ANIM_INTERVAL_MS,
        blit=False,
        repeat=False,
    )
    plt.show()


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    attempts = 0
    while True:
        seed = None
        if SEED is not None:
            seed = SEED + attempts

        (
            pred_hist,
            prey_hist,
            mean_coop_hist,
            var_coop_hist,
            _,
            _,
            preds_snaps,
            preys_snaps,
            preds_final,
            success,
            extinction_step,
        ) = run_sim(seed_override=seed)

        if not RESTART_ON_EXTINCTION or success:
            break

        attempts += 1
        if attempts > MAX_RESTARTS:
            print(
                f"Failed to reach full {STEPS} steps after {MAX_RESTARTS} restarts "
                f"(last extinction at step {extinction_step})."
            )
            break
        print(f"Restarting (attempt {attempts}/{MAX_RESTARTS})...")

    print(
        f"RUN STATUS: {'FULL RUN OK' if success else 'EXTINCTION'} | "
        f"seed={seed} | steps_completed={len(pred_hist)} | "
        f"min_preds={min(pred_hist)} | min_preys={min(prey_hist)} | "
        f"final_preds={pred_hist[-1]} | final_preys={prey_hist[-1]}"
    )

    plot_lv_style(pred_hist, prey_hist)
    plot_trait_evolution(mean_coop_hist, var_coop_hist)

    if preds_final:
        # Summary stats for the final window and current population
        tail_n = min(200, len(mean_coop_hist))
        if tail_n > 0:
            tail_mean = sum(mean_coop_hist[-tail_n:]) / tail_n
            tail_var = sum(var_coop_hist[-tail_n:]) / tail_n
            print(f"Mean coop (last {tail_n}): {tail_mean:.3f}")
            print(f"Var  coop (last {tail_n}): {tail_var:.4f}")
        final_mean = sum(p.coop for p in preds_final) / len(preds_final)
        print(f"Mean coop (final pop): {final_mean:.3f}")

    if PLOT_MACRO_ENERGY_FLOWS:
        plot_macro_energy_flows(LAST_ENERGY_FLOW_HISTORY)

    if ANIMATE and ANIMATE_SIMPLE_GRID:
        animate_simple_grid(preds_snaps, preys_snaps, LAST_GRASS_SNAPS)

    if ANIMATE:
        animate_world(preds_snaps, preys_snaps)


if __name__ == "__main__":
    main()
