"""Kin-selection ladder, steps 0-1 (pre-registration: README.md in this folder, commit 4c5fefb).

The Moran engine (moran_models/interaction_kernel/core) with a mechanism that can:

- remove self from benefit routing only (self_in_routing=False): the routing mask is the neighbourhood without the
  diagonal; replacement still uses the full neighbourhood, self included;
- weight routing by inherited founder labels (kin="label", the Moran model), by genomic relatedness (kin="genome",
  step 1: weight 0.2 + 0.6 r), or uniformly (kin="none");
- give self its own routing weight (self_weight, step 0c), instead of the same-label weight it gets as its own kin;
- track a clonal neutral genome (64 loci, all-unique founder alleles) whose mutations (each locus becomes a new
  allele with probability mu per birth) come from a separate random stream, so the genealogy does not depend on mu.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from moran_models.interaction_kernel.core.engine import MoranInteractionEngine
from moran_models.interaction_kernel.core.kernels import build_kin_weighted_kernel, normalize_rows
from moran_models.interaction_kernel.core.mechanisms import ConfigDrivenKernelMechanism
from moran_models.interaction_kernel.core.metrics import compute_step_metrics
from moran_models.interaction_kernel.core.selection import local_replacement_step

GENOME_LOCI = 64
GENOME_STREAM_OFFSET = 7_000_000
GLOBAL_STREAM_OFFSET = 9_000_000
GLOBAL_CANDIDATES = 5
DEATH_STREAM_OFFSET = 11_000_000
AGE_STREAM_OFFSET = 13_000_000
DB_GLOBAL_CANDIDATES = 4


class LadderMechanism(ConfigDrivenKernelMechanism):
    name = "kin_ladder"

    def __init__(self, *, self_in_routing: bool = True, kin: str = "label", track_genome: bool = False,
                 mu: float = 0.0, seed: int = 0, loci: int = GENOME_LOCI, self_weight: float | None = None):
        if kin not in {"label", "genome", "none"}:
            raise ValueError(f"unknown kin mode {kin}")
        if not 0.0 <= mu <= 1.0:
            raise ValueError("mu must be in [0, 1]")
        if self_weight is not None and (not self_in_routing or kin != "label" or not np.isfinite(self_weight)
                                        or self_weight < 0):
            raise ValueError("self_weight needs self in routing, label kin, and a finite weight >= 0")
        self.self_weight = None if self_weight is None else float(self_weight)
        self.self_in_routing = bool(self_in_routing)
        self.kin = kin
        self.track_genome = bool(track_genome or kin == "genome")
        self.mu = float(mu)
        self.loci = int(loci)
        self.genome_rng = np.random.default_rng(GENOME_STREAM_OFFSET + int(seed))
        self.next_allele = 0

    def initialize_extra_state(self, cfg, n_sites, rng):
        del cfg, rng  # no draws from the engine stream
        if not self.track_genome:
            return {}
        self.next_allele = n_sites * self.loci
        return {"genome": np.arange(n_sites * self.loci, dtype=np.int64).reshape(n_sites, self.loci)}

    def routing_mask(self, neighbor_mask: np.ndarray) -> np.ndarray:
        if self.self_in_routing:
            return neighbor_mask
        mask = neighbor_mask.copy()
        np.fill_diagonal(mask, False)
        return mask

    def build_positive_kernel(self, neighbor_mask, lineage, extra_state, cfg):
        mask = self.routing_mask(neighbor_mask)
        same_w, other_w = float(cfg["kin_weight_same_lineage"]), float(cfg["kin_weight_other_lineage"])
        if self.kin == "none":
            return normalize_rows(mask.astype(float))
        if self.kin == "label":
            if self.self_weight is None:
                return build_kin_weighted_kernel(mask, lineage, same_w, other_w)
            same = (lineage[:, None] == lineage[None, :]).astype(float)
            weights = (other_w + (same_w - other_w) * same) * mask
            np.fill_diagonal(weights, self.self_weight * np.diag(mask))
            return normalize_rows(weights)
        i, j = np.nonzero(mask)
        g = extra_state["genome"]
        r = (g[i] == g[j]).mean(axis=1)
        weights = np.zeros(mask.shape, dtype=float)
        weights[i, j] = other_w + (same_w - other_w) * r
        return normalize_rows(weights)

    def inherit_extra_state(self, extra_state, parent_indices, step_context, rng, cfg):
        out = super().inherit_extra_state(extra_state, parent_indices, step_context, rng, cfg)
        if "genome" in out and self.mu > 0.0:
            g = out["genome"]
            hit = self.genome_rng.random(g.shape) < self.mu
            n = int(hit.sum())
            if n:
                g[hit] = np.arange(self.next_allele, self.next_allele + n, dtype=np.int64)
                self.next_allele += n
        return out


class GlobalReplacementEngine(MoranInteractionEngine):
    """Step 0d control: benefit routing stays on the grid, but each site's replacement lottery draws its 5 candidate
    parents uniformly at random from the whole grid (without replacement; the focal site only by chance), fresh each
    step and site, from a separate random stream."""

    def __init__(self, cfg, mechanism):
        super().__init__(cfg, mechanism)
        self.global_rng = np.random.default_rng(GLOBAL_STREAM_OFFSET + int(cfg["random_seed"]))

    def draw_candidates(self) -> list[np.ndarray]:
        keys = self.global_rng.random((self.n_sites, self.n_sites))
        picks = np.argpartition(keys, GLOBAL_CANDIDATES, axis=1)[:, :GLOBAL_CANDIDATES]
        return [row.astype(np.int32) for row in picks]

    def step(self):
        # routing uses self.neighbor_mask (grid, built at init); replacement uses self.neighbor_indices
        self.neighbor_indices = self.draw_candidates()
        return super().step()


class OverlappingEngine(GlobalReplacementEngine):
    """Step 1: overlapping generations. Each occupant dies with probability `death` (separate stream), independent of
    h; dead sites get the base lottery's offspring (self + 4 start-of-step occupants, or 5 random sites when
    global_candidates), survivors keep their site and h. The base step runs in full (same engine-stream draws), and
    survivors are then restored, so death = 1 reproduces the base (or 0d's global arm) exactly."""

    def __init__(self, cfg, mechanism, death: float, global_candidates: bool):
        if not 0.0 < death <= 1.0:
            raise ValueError("death must be in (0, 1]")
        super().__init__(cfg, mechanism)
        self.death = float(death)
        self.global_candidates = bool(global_candidates)
        self.death_rng = np.random.default_rng(DEATH_STREAM_OFFSET + int(cfg["random_seed"]))

    def step(self):
        if self.extra_state:
            raise ValueError("overlapping generations support no extra state (e.g. genomes)")
        old_h, old_lineage = self.h.copy(), self.lineage.copy()
        survive = self.death_rng.random(self.n_sites) >= self.death
        metrics = (GlobalReplacementEngine.step(self) if self.global_candidates
                   else MoranInteractionEngine.step(self))
        self.h[survive] = old_h[survive]
        self.lineage[survive] = old_lineage[survive]
        self.last_survivors = survive
        return metrics


class DeathBirthEngine(OverlappingEngine):
    """Step K0 attempt 2: as OverlappingEngine, but a dead site's own start-of-step occupant is excluded from its
    lottery. Local: candidates are the 4 grid neighbours. Global: DB_GLOBAL_CANDIDATES distinct sites drawn uniformly
    from the whole grid excluding the focal site (stream seed + 9,000,000). Routing is untouched (it uses the grid
    neighbor_mask built at init)."""

    def __init__(self, cfg, mechanism, death: float, global_candidates: bool):
        super().__init__(cfg, mechanism, death, global_candidates)
        self.neighbor_indices = [n[n != i].astype(np.int32) for i, n in enumerate(self.neighbor_indices)]

    def draw_candidates(self) -> list[np.ndarray]:
        keys = self.global_rng.random((self.n_sites, self.n_sites))
        np.fill_diagonal(keys, np.inf)
        picks = np.argpartition(keys, DB_GLOBAL_CANDIDATES, axis=1)[:, :DB_GLOBAL_CANDIDATES]
        return [row.astype(np.int32) for row in picks]


class SurvivalSelectionEngine(OverlappingEngine):
    """Step 1b: selection moved (with weight lam) from the birth lottery to a death lottery.

    Payoff x = W - base_fitness. Death: d_i = min(1, death * w_i / mean(w over self + 4 grid neighbours)),
    w = exp(-lam * x / T), drawn from the death stream. Birth: softmax over (1 - lam) * W with temperature T among
    the start-of-step occupants of the replacement candidates (grid self + 4, or 5 random sites when global).
    lam = 0 reproduces OverlappingEngine exactly (same draws in the same order)."""

    def __init__(self, cfg, mechanism, death: float, global_candidates: bool, lam: float, norm: str = "local"):
        if not 0.0 <= lam <= 1.0:
            raise ValueError("lam must be in [0, 1]")
        if norm not in ("local", "global"):
            raise ValueError(f"unknown death normalization {norm}")
        self.norm = norm                                        # step 1b: local (self + 4); step 1c: whole grid
        super().__init__(cfg, mechanism, death, global_candidates)
        self.lam = float(lam)
        self.temperature = float(cfg["selection_temperature"])
        self.grid_mask = self.neighbor_mask.astype(float)       # death lottery stays on the grid
        self.grid_counts = self.grid_mask.sum(axis=1)

    def death_probabilities(self, x: np.ndarray) -> np.ndarray:
        if self.lam == 0.0:
            return np.full(self.n_sites, self.death)
        z = -self.lam * x / self.temperature
        w = np.exp(z - z.max())                                    # a global shift leaves the ratios unchanged
        if self.norm == "global":
            return np.minimum(1.0, self.death * w / w.mean())
        local_mean = (self.grid_mask @ w) / self.grid_counts
        return np.minimum(1.0, self.death * w / local_mean)

    def step(self):
        # Re-implements the base step without step_context / inherit_extra_state / post_reproduction_update: safe only
        # because extra state is rejected here and LadderMechanism's post-reproduction hook is a no-op.
        if self.extra_state:
            raise ValueError("survival selection supports no extra state (e.g. genomes)")
        cfg, mech = self.cfg, self.mechanism
        K_plus = mech.build_positive_kernel(self.neighbor_mask, self.lineage, self.extra_state, cfg)
        K_minus = mech.build_negative_kernel(self.neighbor_mask, self.lineage, self.extra_state, cfg)
        expressed = self.expressed_trait()                          # step 2a: age-dependent expression
        R_plus = K_plus.T @ mech.compute_positive_output(expressed, self.extra_state, cfg)
        R_minus = K_minus.T @ mech.compute_negative_output(expressed, self.extra_state, cfg)
        W = float(cfg["base_fitness"]) + R_plus - R_minus - mech.compute_private_cost(expressed, self.extra_state, cfg)
        x = W - float(cfg["base_fitness"])
        d = self.death_probabilities(x)
        survive = self.death_rng.random(self.n_sites) >= d
        self.history.append(compute_step_metrics(self.h, R_plus, R_minus, W))
        if self.global_candidates:
            self.neighbor_indices = self.draw_candidates()
        old_h, old_lineage = self.h.copy(), self.lineage.copy()
        self.h, self.lineage, _ = local_replacement_step(
            self.h, self.lineage, (1.0 - self.lam) * W, self.neighbor_indices, self.rng, self.temperature,
            float(cfg["mutation_rate"]), float(cfg["mutation_stddev"]))
        self.h[survive] = old_h[survive]
        self.lineage[survive] = old_lineage[survive]
        self.last_survivors = survive
        self.last_death_prob = d
        self.after_replacement(survive)
        self.step_index += 1
        return self.history[-1]

    def expressed_trait(self) -> np.ndarray:
        return self.h

    def after_replacement(self, survive: np.ndarray) -> None:
        pass


class AgeEngine(SurvivalSelectionEngine):
    """Step 2a: ages, with age-dependent helping. An occupant is a juvenile while age < juvenile_period; juveniles
    express juvenile_strength of their trait (produce and pay at that strength), adults all of it. Payoffs use the
    start-of-step ages; afterwards survivors age by 1 and newborns start at 0. Initial ages: 0 with probability 0.5,
    else 1, from a separate stream. juvenile_period = 0 makes everyone an adult and reproduces the parent engine."""

    def __init__(self, cfg, mechanism, death, global_candidates, lam, norm, juvenile_period: int,
                 juvenile_strength: float):
        if juvenile_period < 0 or not 0.0 <= juvenile_strength <= 1.0:
            raise ValueError("juvenile_period >= 0 and juvenile_strength in [0, 1] required")
        super().__init__(cfg, mechanism, death, global_candidates, lam, norm)
        self.juvenile_period = int(juvenile_period)
        self.juvenile_strength = float(juvenile_strength)
        age_rng = np.random.default_rng(AGE_STREAM_OFFSET + int(cfg["random_seed"]))
        self.age = np.where(age_rng.random(self.n_sites) < 0.5, 0, 1).astype(np.int64)

    def juvenile_mask(self) -> np.ndarray:
        return self.age < self.juvenile_period

    def expressed_trait(self) -> np.ndarray:
        juv = self.juvenile_mask()
        self.last_juvenile_fraction = float(juv.mean())
        if not juv.any():
            return self.h
        return np.where(juv, self.juvenile_strength * self.h, self.h)

    def after_replacement(self, survive: np.ndarray) -> None:
        self.age = np.where(survive, self.age + 1, 0)


def make_engine(cfg: dict[str, Any], replacement: str = "local", death: float | None = None,
                lam: float | None = None, norm: str = "local", juvenile_period: int | None = None,
                juvenile_strength: float = 0.0, exclude_focal: bool = False,
                **mechanism_kwargs) -> MoranInteractionEngine:
    if exclude_focal and (death is None or lam is not None or juvenile_period is not None):
        raise ValueError("exclude_focal is only for the overlapping-generations engine (step K0 attempt 2)")
    mech = LadderMechanism(seed=int(cfg["random_seed"]), **mechanism_kwargs)
    if juvenile_period is not None:
        if lam is None or death is None or replacement not in ("local", "global"):
            raise ValueError("ages need death, lam and local/global replacement")
        return AgeEngine(cfg, mech, death, replacement == "global", lam, norm, juvenile_period, juvenile_strength)
    if lam is not None:
        if death is None or replacement not in ("local", "global"):
            raise ValueError("survival selection needs death and local/global replacement")
        return SurvivalSelectionEngine(cfg, mech, death, replacement == "global", lam, norm)
    if death is not None:
        if replacement not in ("local", "global"):
            raise ValueError(f"unknown replacement {replacement}")
        engine_cls = DeathBirthEngine if exclude_focal else OverlappingEngine
        return engine_cls(cfg, mech, death, global_candidates=replacement == "global")
    if replacement == "local":
        return MoranInteractionEngine(cfg, mech)
    if replacement == "global":
        return GlobalReplacementEngine(cfg, mech)
    raise ValueError(f"unknown replacement {replacement}")
