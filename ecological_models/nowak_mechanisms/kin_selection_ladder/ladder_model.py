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

GENOME_LOCI = 64
GENOME_STREAM_OFFSET = 7_000_000
GLOBAL_STREAM_OFFSET = 9_000_000
GLOBAL_CANDIDATES = 5


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


def make_engine(cfg: dict[str, Any], replacement: str = "local", **mechanism_kwargs) -> MoranInteractionEngine:
    mech = LadderMechanism(seed=int(cfg["random_seed"]), **mechanism_kwargs)
    if replacement == "local":
        return MoranInteractionEngine(cfg, mech)
    if replacement == "global":
        return GlobalReplacementEngine(cfg, mech)
    raise ValueError(f"unknown replacement {replacement}")
