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
from moran_models.interaction_kernel.core.selection import (
    _local_softmax_probabilities, inherit_trait_and_lineage, local_replacement_step,
)

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


class ParentalMechanism(LadderMechanism):
    """Step K1: benefit routed in equal shares to the helper's living offspring (engine-supplied `parent_site`: the
    site of each occupant's living parent, or -1). Helpers with none: benefit lost (care="offspring") or sent
    uniformly to the 4 grid neighbours (care="hybrid"). Records the lottery's parent indices for id bookkeeping."""

    def __init__(self, *, care: str, **kw):
        if care not in {"offspring", "hybrid", "neighbours", "young_neighbours"}:
            raise ValueError(f"unknown care mode {care}")
        if kw.get("self_in_routing", True) or kw.get("track_genome") or kw.get("kin", "label") != "label":
            raise ValueError("parental care needs self out of routing, label kin (uniform weights), no genome")
        super().__init__(**kw)
        self.care = care
        self.parent_site: np.ndarray | None = None
        self.last_parents: np.ndarray | None = None
        self.birth_scale = 1.0                                   # R1: share of care acting on fecundity (1 - lam)
        self.juvenile: np.ndarray | None = None                  # R2: only these occupants receive care (None: all)
        self.birth_override: tuple[np.ndarray, np.ndarray] | None = None   # R3a: (care term, cost) for the lottery

    def raw_positive_output(self, trait, extra_state, cfg):
        return super().compute_positive_output(trait, extra_state, cfg)

    def compute_private_cost(self, trait, extra_state, cfg):
        if self.birth_override is not None:
            return self.birth_override[1]
        return super().compute_private_cost(trait, extra_state, cfg)

    def compute_positive_output(self, trait, extra_state, cfg):
        if self.birth_override is not None:
            return self.birth_override[0]
        out = self.raw_positive_output(trait, extra_state, cfg)
        return out if self.birth_scale == 1.0 else self.birth_scale * out

    def build_positive_kernel(self, neighbor_mask, lineage, extra_state, cfg):
        if self.birth_override is not None:                      # R3a lottery: W = 1 + care term - cost, per site
            return np.eye(neighbor_mask.shape[0])
        if self.care == "neighbours":                            # R1 control: uniform over the 4 neighbours
            return super().build_positive_kernel(neighbor_mask, lineage, extra_state, cfg)
        n = neighbor_mask.shape[0]
        if self.care == "young_neighbours":                      # R2 control: equal shares among juvenile neighbours
            mask = neighbor_mask.copy()
            np.fill_diagonal(mask, False)
            K = (mask & self.juvenile[None, :]).astype(float)
            rows = K.sum(axis=1)
            K[rows > 0] /= rows[rows > 0, None]
            return K
        ps = self.parent_site
        K = np.zeros((n, n), dtype=float)
        ok = ps >= 0
        if self.juvenile is not None:
            ok &= self.juvenile
        js = np.nonzero(ok)[0]
        K[ps[js], js] = 1.0
        rows = K.sum(axis=1)
        has = rows > 0
        K[has] /= rows[has, None]
        if self.care == "hybrid" and (~has).any():
            K[~has] = super().build_positive_kernel(neighbor_mask, lineage, extra_state, cfg)[~has]
        return K

    def inherit_extra_state(self, extra_state, parent_indices, step_context, rng, cfg):
        self.last_parents = np.asarray(parent_indices).copy()
        return super().inherit_extra_state(extra_state, parent_indices, step_context, rng, cfg)


class ParentalEngine(OverlappingEngine):
    """Step K1: OverlappingEngine plus id / parent-id bookkeeping. Before each step, each occupant's living parent
    (if any) is located; after it, newborns (dead sites) get fresh ids and the id of their start-of-step parent,
    survivors keep theirs. No random draws."""

    def __init__(self, cfg, mechanism: ParentalMechanism, death: float, global_candidates: bool):
        super().__init__(cfg, mechanism, death, global_candidates)
        self.ids = np.arange(self.n_sites, dtype=np.int64)
        self.parent_ids = np.full(self.n_sites, -1, dtype=np.int64)
        self.next_id = self.n_sites
        self.last_diag: dict[str, float] = {}

    def parent_sites(self) -> np.ndarray:
        order = np.argsort(self.ids)
        sorted_ids = self.ids[order]
        pos = np.clip(np.searchsorted(sorted_ids, self.parent_ids), 0, self.n_sites - 1)
        found = (self.parent_ids >= 0) & (sorted_ids[pos] == self.parent_ids)
        return np.where(found, order[pos], -1)

    def step(self):
        ps = self.parent_sites()
        self.mechanism.parent_site = ps
        counts = np.bincount(ps[ps >= 0], minlength=self.n_sites)
        none = counts == 0
        tot = float(self.h.sum())
        js = np.nonzero(ps >= 0)[0]
        a, b = self.h[ps[js]], self.h[js]
        po = float(np.corrcoef(a, b)[0, 1]) if len(js) >= 2 and a.std() > 0 and b.std() > 0 else float("nan")
        self.last_diag = {"offspring_mean": float(counts.mean()), "frac_no_offspring": float(none.mean()),
                          "benefit_lost": float(self.h[none].sum() / tot) if tot > 0 else float("nan"),
                          "parent_offspring_corr": po}
        old_ids = self.ids.copy()
        metrics = super().step()
        dead = ~self.last_survivors
        k = int(dead.sum())
        self.parent_ids[dead] = old_ids[self.mechanism.last_parents[dead]]
        self.ids[dead] = np.arange(self.next_id, self.next_id + k, dtype=np.int64)
        self.next_id += k
        return metrics


class SurvivalCareEngine(ParentalEngine):
    """Step R1: care lowers the recipient's death probability, d_i = death * exp(-lam R_i / T), unnormalized and
    uncapped (R_i >= 0); births by the softmax over W = 1 + (1 - lam) R - C h. Death draws: one uniform per site from
    the death stream, as in OverlappingEngine, so lam = 0 reproduces ParentalEngine exactly."""

    def __init__(self, cfg, mechanism: ParentalMechanism, death: float, global_candidates: bool, care_lam: float):
        if not 0.0 <= care_lam <= 1.0:
            raise ValueError("care_lam must be in [0, 1]")
        super().__init__(cfg, mechanism, death, global_candidates)
        self.care_lam = float(care_lam)
        self.temperature = float(cfg["selection_temperature"])
        mechanism.birth_scale = 1.0 - self.care_lam

    def received_care(self) -> np.ndarray:
        K = self.mechanism.build_positive_kernel(self.neighbor_mask, self.lineage, self.extra_state, self.cfg)
        return K.T @ self.mechanism.raw_positive_output(self.h, self.extra_state, self.cfg)

    def death_probabilities(self, R: np.ndarray) -> np.ndarray:
        if self.care_lam == 0.0:
            return np.full(self.n_sites, self.death)
        return self.death * np.exp(-self.care_lam * R / self.temperature)

    def step(self):
        if self.extra_state:
            raise ValueError("no extra state supported")
        ps = self.parent_sites()
        self.mechanism.parent_site = ps
        counts = np.bincount(ps[ps >= 0], minlength=self.n_sites)
        none = counts == 0
        tot = float(self.h.sum())
        js = np.nonzero(ps >= 0)[0]
        a, b = self.h[ps[js]], self.h[js]
        po = float(np.corrcoef(a, b)[0, 1]) if len(js) >= 2 and a.std() > 0 and b.std() > 0 else float("nan")
        R = self.received_care()
        d = self.death_probabilities(R)
        cared = R > 0
        mean_or_nan = lambda m: float(d[m].mean()) if m.any() else float("nan")
        if self.mechanism.care == "neighbours":
            lost = 0.0                                           # neighbour help is never lost
        else:
            lost = float(self.h[none].sum() / tot) if tot > 0 else float("nan")
        self.last_diag = {"offspring_mean": float(counts.mean()), "frac_no_offspring": float(none.mean()),
                          "benefit_lost": lost, "parent_offspring_corr": po, "death_mean": float(d.mean()),
                          "death_cared": mean_or_nan(cared), "death_uncared": mean_or_nan(~cared),
                          "death_parents": mean_or_nan(~none), "frac_cared": float(cared.mean())}
        old_h, old_lineage, old_ids = self.h.copy(), self.lineage.copy(), self.ids.copy()
        survive = self.death_rng.random(self.n_sites) >= d
        metrics = (GlobalReplacementEngine.step(self) if self.global_candidates
                   else MoranInteractionEngine.step(self))
        self.h[survive] = old_h[survive]
        self.lineage[survive] = old_lineage[survive]
        self.last_survivors = survive
        dead = ~survive
        k = int(dead.sum())
        self.parent_ids[dead] = old_ids[self.mechanism.last_parents[dead]]
        self.ids[dead] = np.arange(self.next_id, self.next_id + k, dtype=np.int64)
        self.next_id += k
        return metrics


class AgedSurvivalCareEngine(SurvivalCareEngine):
    """Step R2: SurvivalCareEngine plus ages; care reaches only juveniles (age < care_juvenile at the payoff
    computation). Newborns start at age 0, survivors age by 1 at the end of each step, founders start at 0. No draws."""

    def __init__(self, cfg, mechanism, death, global_candidates, care_lam, care_juvenile: int):
        if int(care_juvenile) < 1:
            raise ValueError("care_juvenile must be >= 1")
        super().__init__(cfg, mechanism, death, global_candidates, care_lam)
        self.care_juvenile = int(care_juvenile)
        self.ages = np.zeros(self.n_sites, dtype=np.int64)

    def step(self):
        juv = self.ages < self.care_juvenile
        self.mechanism.juvenile = juv
        ps = self.parent_sites()
        self.mechanism.parent_site = ps
        K = self.mechanism.build_positive_kernel(self.neighbor_mask, self.lineage, self.extra_state, self.cfg)
        no_recipient = K.sum(axis=1) == 0
        tot = float(self.h.sum())
        jo = (ps >= 0) & juv
        juv_offspring = np.bincount(ps[jo], minlength=self.n_sites)
        extra = {"benefit_lost": float(self.h[no_recipient].sum() / tot) if tot > 0 else float("nan"),
                 "juvenile_offspring_mean": float(juv_offspring.mean()), "juvenile_fraction": float(juv.mean()),
                 "mean_age": float(self.ages.mean())}
        metrics = super().step()                                 # recomputes the same parent sites and kernel
        self.last_diag.update(extra)
        s = self.last_survivors
        self.ages[s] += 1
        self.ages[~s] = 0
        return metrics


class CarryOverEngine(AgedSurvivalCareEngine):
    """Step R3a: care received and cost paid accumulate in condition stores, S <- rho S + R and D <- rho D + C h;
    death d = death * exp(-lam S / T), fecundity W = 1 + (1 - lam) S - D. Newborns start with S = D = 0, survivors
    keep theirs. rho = 0 reproduces AgedSurvivalCareEngine exactly. No random draws beyond the base step's."""

    def __init__(self, cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho: float):
        if not 0.0 <= care_rho < 1.0:
            raise ValueError("care_rho must be in [0, 1)")
        super().__init__(cfg, mechanism, death, global_candidates, care_lam, care_juvenile)
        self.care_rho = float(care_rho)
        self.S = np.zeros(self.n_sites)
        self.D = np.zeros(self.n_sites)

    def step(self):
        if self.extra_state:
            raise ValueError("no extra state supported")
        mech = self.mechanism
        juv = self.ages < self.care_juvenile
        mech.juvenile = juv
        ps = self.parent_sites()
        mech.parent_site = ps
        K = mech.build_positive_kernel(self.neighbor_mask, self.lineage, self.extra_state, self.cfg)
        R = K.T @ mech.raw_positive_output(self.h, self.extra_state, self.cfg)
        cost = mech.compute_private_cost(self.h, self.extra_state, self.cfg)
        self.S = self.care_rho * self.S + R
        self.D = self.care_rho * self.D + cost
        d = self.death_probabilities(self.S)
        counts = np.bincount(ps[ps >= 0], minlength=self.n_sites)
        has_kids = counts > 0
        jo = (ps >= 0) & juv
        tot = float(self.h.sum())
        js = np.nonzero(ps >= 0)[0]
        a, b = self.h[ps[js]], self.h[js]
        po = float(np.corrcoef(a, b)[0, 1]) if len(js) >= 2 and a.std() > 0 and b.std() > 0 else float("nan")
        cared = R > 0
        m = lambda x, mask: float(x[mask].mean()) if mask.any() else float("nan")
        no_recipient = K.sum(axis=1) == 0
        self.last_diag = {
            "offspring_mean": float(counts.mean()), "frac_no_offspring": float((~has_kids).mean()),
            "benefit_lost": float(self.h[no_recipient].sum() / tot) if tot > 0 else float("nan"),
            "parent_offspring_corr": po, "death_mean": float(d.mean()), "death_cared": m(d, cared),
            "death_uncared": m(d, ~cared), "death_parents": m(d, has_kids), "frac_cared": float(cared.mean()),
            "juvenile_offspring_mean": float(np.bincount(ps[jo], minlength=self.n_sites).mean()),
            "juvenile_fraction": float(juv.mean()), "mean_age": float(self.ages.mean()),
            "S_mean": float(self.S.mean()), "D_mean": float(self.D.mean()), "S_juvenile": m(self.S, juv),
            "D_juvenile": m(self.D, juv), "S_parents": m(self.S, has_kids), "D_parents": m(self.D, has_kids)}
        old_h, old_lineage, old_ids = self.h.copy(), self.lineage.copy(), self.ids.copy()
        survive = self.death_rng.random(self.n_sites) >= d
        self.last_payoff_D = self.D.copy()                       # R3b diagnostics: D at this payoff computation
        mech.birth_override = ((1.0 - self.care_lam) * self.S, self.D.copy())
        try:
            metrics = (GlobalReplacementEngine.step(self) if self.global_candidates
                       else MoranInteractionEngine.step(self))
        finally:
            mech.birth_override = None
        self.h[survive] = old_h[survive]
        self.lineage[survive] = old_lineage[survive]
        self.last_survivors = survive
        dead = ~survive
        k = int(dead.sum())
        self.parent_ids[dead] = old_ids[mech.last_parents[dead]]
        self.ids[dead] = np.arange(self.next_id, self.next_id + k, dtype=np.int64)
        self.next_id += k
        self.S[dead] = 0.0
        self.D[dead] = 0.0
        self.ages[survive] += 1
        self.ages[dead] = 0
        return metrics


class BirthCostEngine(CarryOverEngine):
    """Step R3b: after the step, each parent that survived it adds k * birth_cost to its depletion store D, where
    k is its number of realized births (newborns at sites whose occupant died this step). Lottery wins at surviving
    sites are discarded and charge nothing; a parent that died the same step pays nothing. The charge does not
    change this step's lottery; it enters the next one as rho * k * birth_cost. birth_cost = 0 is R3a exactly.
    No random draws are added. Db is a diagnostic-only copy of the birth part of D (same decay, never used)."""

    def __init__(self, cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho,
                 birth_cost: float):
        if not birth_cost >= 0.0:
            raise ValueError("birth_cost must be >= 0")
        super().__init__(cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho)
        self.birth_cost = float(birth_cost)
        self.Db = np.zeros(self.n_sites)
        self.last_charged = np.zeros(self.n_sites, dtype=bool)

    def charge_births(self, survive: np.ndarray, last_parents: np.ndarray) -> np.ndarray:
        """Births per old site counted over the dead (newborn) sites; only surviving parents are charged."""
        dead = ~survive
        k = np.bincount(np.asarray(last_parents)[dead], minlength=self.n_sites)
        k = np.where(survive, k, 0)
        self.D += self.birth_cost * k
        self.Db += self.birth_cost * k
        return k

    def step(self):
        self.Db *= self.care_rho                                # decays with D (D <- rho D + C h in the base step)
        db_payoff = self.Db.copy()
        prev_charged = self.last_charged
        metrics = super().step()
        survive = self.last_survivors
        dead = ~survive
        self.Db[dead] = 0.0
        k = self.charge_births(survive, self.mechanism.last_parents)
        births = int(dead.sum())
        m = lambda x, mask: float(x[mask].mean()) if mask.any() else float("nan")
        self.last_diag.update({
            "births_per_occupant": births / self.n_sites,
            "frac_births_charged": float(k.sum() / births) if births else float("nan"),
            "Db_mean": float(db_payoff.mean()),
            "D_recent_parents": m(self.last_payoff_D, prev_charged)})
        self.last_charged = k > 0
        return metrics


class ThresholdEngine(BirthCostEngine):
    """Step R3c: a start-of-step occupant can win a birth only if its lottery fecundity W = 1 + (1 - lam) S - D
    (payoff time) is >= theta; a site needing a birth (occupant died, or already empty) whose pool holds no eligible
    occupant stays empty. Empty sites neither help, pay, receive, breed nor die; stores and age are 0, id and
    parent id -1, h 0 and lineage -1 (never read). Random streams: every site makes one lottery draw (an all-masked
    pool draws over its unfiltered pool, result discarded), and mutation, death and global-candidate draws are made
    for all sites, so with theta = -inf and a full lattice this is BirthCostEngine exactly."""

    def __init__(self, cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho, birth_cost,
                 theta: float):
        super().__init__(cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho, birth_cost)
        if np.isnan(theta):
            raise ValueError("theta must be a number (-inf allowed)")
        self.theta = float(theta)
        self.occ = np.ones(self.n_sites, dtype=bool)

    def condition_score(self) -> np.ndarray:
        return float(self.cfg["base_fitness"]) + (1.0 - self.care_lam) * self.S - np.zeros(self.n_sites) - self.D

    def survival_mask(self, u: np.ndarray, d: np.ndarray, W: np.ndarray, occ: np.ndarray) -> np.ndarray:
        return (u >= d) & occ

    def eligible_mask(self, W: np.ndarray) -> np.ndarray:
        return self.occ & (W >= self.theta)

    @staticmethod
    def pool_probs(w: np.ndarray, e: np.ndarray, temp: float) -> np.ndarray:
        """Softmax over the eligible candidates; the unfiltered softmax if all or none are eligible (none: the
        draw is discarded). The all-eligible case is the core lottery's exact computation."""
        if e.all() or not e.any():
            return _local_softmax_probabilities(w, temp)
        probs = np.zeros(len(w))
        probs[e] = _local_softmax_probabilities(w[e], temp)
        return probs

    def lottery(self, W: np.ndarray, eligible: np.ndarray):
        """One draw per site; returns (parent site per site, has an eligible candidate, pool was trimmed)."""
        temp = float(self.cfg["selection_temperature"])
        n = self.n_sites
        parents = np.empty(n, dtype=np.int32)
        has = np.zeros(n, dtype=bool)
        trimmed = np.zeros(n, dtype=bool)
        for i, pool in enumerate(self.neighbor_indices):
            e = eligible[pool]
            probs = self.pool_probs(W[pool], e, temp)
            has[i] = bool(e.any())
            trimmed[i] = bool((self.occ[pool] & ~e).any())             # an occupant excluded by the threshold
            parents[i] = int(pool[int(self.rng.choice(len(pool), p=probs))])
        return parents, has, trimmed

    def step(self):
        if self.extra_state:
            raise ValueError("no extra state supported")
        mech, occ, n = self.mechanism, self.occ, self.n_sites
        juv = (self.ages < self.care_juvenile) & occ
        mech.juvenile = juv
        ps = self.parent_sites()
        mech.parent_site = ps
        K = mech.build_positive_kernel(self.neighbor_mask, self.lineage, self.extra_state, self.cfg)
        R = K.T @ mech.raw_positive_output(self.h, self.extra_state, self.cfg)
        cost = mech.compute_private_cost(self.h, self.extra_state, self.cfg)
        self.Db *= self.care_rho
        db_payoff = self.Db.copy()
        prev_charged = self.last_charged
        self.S = self.care_rho * self.S + R
        self.D = self.care_rho * self.D + cost
        d = self.death_probabilities(self.S)
        # diagnostics over occupied sites (identical to R3b's when the lattice is full)
        m = lambda x, mask: float(x[mask].mean()) if mask.any() else float("nan")
        counts = np.bincount(ps[ps >= 0], minlength=n)
        has_kids = (counts > 0) & occ
        jo = (ps >= 0) & juv
        tot = float(self.h[occ].sum())
        js = np.nonzero(ps >= 0)[0]
        a, b = self.h[ps[js]], self.h[js]
        po = float(np.corrcoef(a, b)[0, 1]) if len(js) >= 2 and a.std() > 0 and b.std() > 0 else float("nan")
        cared = (R > 0) & occ
        no_recipient = (K.sum(axis=1) == 0) & occ
        self.last_diag = {
            "offspring_mean": m(counts.astype(float), occ), "frac_no_offspring": m((counts == 0).astype(float), occ),
            "benefit_lost": float(self.h[no_recipient].sum() / tot) if tot > 0 else float("nan"),
            "parent_offspring_corr": po, "death_mean": m(d, occ), "death_cared": m(d, cared),
            "death_uncared": m(d, occ & ~cared), "death_parents": m(d, has_kids), "frac_cared": m(cared.astype(float), occ),
            "juvenile_offspring_mean": m(np.bincount(ps[jo], minlength=n).astype(float), occ),
            "juvenile_fraction": m(juv.astype(float), occ), "mean_age": m(self.ages.astype(float), occ),
            "S_mean": m(self.S, occ), "D_mean": m(self.D, occ), "S_juvenile": m(self.S, juv),
            "D_juvenile": m(self.D, juv), "S_parents": m(self.S, has_kids), "D_parents": m(self.D, has_kids)}
        self.last_payoff_D = self.D.copy()
        old_h, old_lineage, old_ids = self.h.copy(), self.lineage.copy(), self.ids.copy()
        # condition score W = base + (1 - lam) S - D, as R3a's lottery override computes it (payoff time)
        W = self.condition_score()
        self.last_W = W
        survive = self.survival_mask(self.death_rng.random(n), d, W, occ)
        need = ~survive
        if self.global_candidates:
            self.neighbor_indices = self.draw_candidates()
        eligible = self.eligible_mask(W)
        parents, has, trimmed = self.lottery(W, eligible)
        self.last_eligible = eligible
        new_h, new_lineage = inherit_trait_and_lineage(
            self.h, self.lineage, parents, self.rng, float(self.cfg["mutation_rate"]),
            float(self.cfg["mutation_stddev"]))
        self.extra_state = mech.inherit_extra_state(self.extra_state, parents, {}, self.rng, self.cfg)
        self.history.append(compute_step_metrics(self.h, R, np.zeros(n), W))
        self.step_index += 1
        fill = need & has
        vac = need & ~has
        # DR4: realized births per old site, before the survivor filter (parents that died this step count too)
        self.last_births_by_parent = np.bincount(parents[fill], minlength=n)
        self.h = np.where(survive, old_h, np.where(fill, new_h, 0.0))
        self.lineage = np.where(survive, old_lineage, np.where(fill, new_lineage, -1)).astype(old_lineage.dtype)
        self.last_survivors = survive
        nf = int(fill.sum())
        self.ids = np.where(survive, old_ids, -1).astype(np.int64)
        self.parent_ids = np.where(survive, self.parent_ids, -1).astype(np.int64)
        self.ids[fill] = np.arange(self.next_id, self.next_id + nf, dtype=np.int64)
        self.parent_ids[fill] = old_ids[parents[fill]]
        self.next_id += nf
        for x in (self.S, self.D, self.Db):
            x[need] = 0.0
        self.ages[survive] += 1
        self.ages[need] = 0
        k = np.bincount(parents[fill], minlength=n)
        k = np.where(survive, k, 0)
        self.D += self.birth_cost * k
        self.Db += self.birth_cost * k
        self.occ = survive | fill
        nn = int(need.sum())
        nocc = int(occ.sum())
        low = occ & (old_h < 0.5)
        high = occ & (old_h >= 0.5)
        inel = occ & ~eligible
        self.last_diag.update({
            "births_per_occupant": nf / nocc if nocc else float("nan"),
            "frac_births_charged": float(k.sum() / nf) if nf else float("nan"),
            "Db_mean": m(db_payoff, occ), "D_recent_parents": m(self.last_payoff_D, prev_charged),
            "occupancy": nocc / n,
            "frac_fill_trimmed": float((trimmed & need).sum() / nn) if nn else float("nan"),
            "frac_fill_emptied": float(vac.sum() / nn) if nn else float("nan"),
            "frac_ineligible": m(inel.astype(float), occ),
            "frac_ineligible_low_h": m(inel.astype(float), low),
            "frac_ineligible_high_h": m(inel.astype(float), high)})
        self.last_charged = k > 0
        return self.history[-1]

    def occupied_mean_h(self) -> float:
        return float(self.h[self.occ].mean()) if self.occ.any() else float("nan")


class StarvationEngine(ThresholdEngine):
    """Step R3d: an occupied site with condition score W < sigma (payoff time, after the stores are updated) dies
    this step whatever its death draw; the draw is still made for every site. sigma <= theta. No random draws are
    added; sigma = -inf is ThresholdEngine exactly. Pools and eligibility are frozen at payoff time, so a starving
    occupant (W < sigma <= theta, ineligible) can never parent a realized birth."""

    def __init__(self, cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho, birth_cost,
                 theta, sigma: float):
        super().__init__(cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho, birth_cost,
                         theta)
        if np.isnan(sigma) or not sigma <= theta:
            raise ValueError("sigma must be a number <= theta")
        self.sigma = float(sigma)
        self._starve = None

    def survival_mask(self, u, d, W, occ):
        base = (u >= d) & occ
        starve = occ & (W < self.sigma)
        self._starve = (starve, starve & base, ~base & occ)
        return base & ~starve

    def step(self):
        occ0, h0, juv0 = self.occ.copy(), self.h.copy(), (self.ages < self.care_juvenile) & self.occ
        prev_charged = self.last_charged.copy()
        metrics = super().step()
        starve, added, base_dead = self._starve
        m = lambda x, mask: float(x[mask].mean()) if mask.any() else float("nan")
        deaths = int((occ0 & ~self.last_survivors).sum())
        nocc = int(occ0.sum())
        self.last_diag.update({
            "n_starve_added": int(added.sum()), "n_deaths": deaths,
            "starve_added_per_occ": added.sum() / nocc if nocc else float("nan"),
            "starve_all_per_occ": starve.sum() / nocc if nocc else float("nan"),
            "starve_added_share": float(added.sum() / deaths) if deaths else float("nan"),
            "starve_rate_low_h": m(starve.astype(float), occ0 & (h0 < 0.5)),
            "starve_rate_high_h": m(starve.astype(float), occ0 & (h0 >= 0.5)),
            "starve_rate_recent_parents": m(starve.astype(float), occ0 & prev_charged),
            "starve_rate_juveniles": m(starve.astype(float), juv0)})
        # DR4 diagnostics: realized births by parent h class (counts, pooled by the runner) and ineligibility of
        # recent parents; occupants and classes are the start-of-step ones, as for the other class rates
        kb = self.last_births_by_parent
        low, high = occ0 & (h0 < 0.5), occ0 & (h0 >= 0.5)
        self.last_diag.update({
            "births_low_h_sum": int(kb[low].sum()), "n_low_h": int(low.sum()),
            "births_high_h_sum": int(kb[high].sum()), "n_high_h": int(high.sum()),
            "frac_ineligible_recent_parents": m((~self.last_eligible).astype(float), occ0 & prev_charged)})
        self.last_starved = starve
        return metrics


HARVEST_CAP = 0.2                                   # R4: 1 - rho, so a fully fed occupant's store settles at 1


class IncomeEngine(StarvationEngine):
    """Step R4: the free baseline 1 in W is replaced by an income store G fed by a renewable site resource r.

    Within a step: (1) every start-of-step occupant (dying ones included) harvests g = min(r, 0.2) from its own
    site, r <- r - g; (2) G <- rho G + g for those occupants (and S, D as in R3d); (3) W = G + (1 - lam) S - D is
    computed once and used for starvation, eligibility and the lottery; (4) deaths and births as in R3d; a site
    that needed a fill (newborn or left empty) gets G = 1; (5) every site regrows r <- r + gamma (1 - r) from its
    post-harvest stock. A site keeps its resource on turnover. No random draws are added; gamma = 1 is R3d exactly.
    DR4: g_start (default 1) replaces the founders' and newborns' starting store G = 1 (and the G of an emptied
    site, never read); g_start = 1 is R4 exactly."""

    def __init__(self, cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho, birth_cost,
                 theta, sigma, gamma: float, g_start: float = 1.0):
        super().__init__(cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho, birth_cost,
                         theta, sigma)
        if np.isnan(gamma) or not 0.0 < gamma <= 1.0:
            raise ValueError("gamma must be in (0, 1]")
        if self.care_rho + HARVEST_CAP != 1.0:                  # the gamma = 1 = R3d guarantee needs cap = 1 - rho
            raise ValueError("R4 needs care_rho = 0.8 (harvest cap 0.2 = 1 - rho)")
        if not np.isfinite(g_start):
            raise ValueError("g_start must be finite")
        self.gamma = float(gamma)
        self.g_start = float(g_start)
        self.r = np.ones(self.n_sites)
        self.G = np.full(self.n_sites, self.g_start)
        self.last_harvest = np.zeros(self.n_sites)

    def condition_score(self) -> np.ndarray:
        return self.G + (1.0 - self.care_lam) * self.S - np.zeros(self.n_sites) - self.D

    def harvest(self, occ: np.ndarray) -> np.ndarray:
        g = np.where(occ, np.minimum(self.r, HARVEST_CAP), 0.0)
        self.r = self.r - g
        self.G = np.where(occ, self.care_rho * self.G + g, self.G)
        return g

    def regrow(self) -> None:
        self.r = self.r + self.gamma * (1.0 - self.r)

    def step(self):
        occ0 = self.occ.copy()
        r_pre = self.r.copy()
        juv0 = (self.ages < self.care_juvenile) & occ0
        ps = self.parent_sites()
        kids0 = (np.bincount(ps[ps >= 0], minlength=self.n_sites) > 0) & occ0
        g = self.harvest(occ0)
        G_payoff = self.G.copy()
        self.last_harvest = g
        metrics = super().step()
        self.G[~self.last_survivors] = self.g_start                # newborns and empty sites
        self.regrow()
        m = lambda x, mask: float(x[mask].mean()) if mask.any() else float("nan")
        empty0 = ~occ0
        self.last_diag.update({
            "harvest_total": float(g[occ0].sum()), "n_occ_start": int(occ0.sum()),
            "harvest_mean": m(g, occ0), "G_mean": m(G_payoff, occ0), "G_juvenile": m(G_payoff, juv0),
            "G_parents": m(G_payoff, kids0), "r_occupied": m(r_pre, occ0), "r_empty": m(r_pre, empty0),
            "frac_harvest_capped": m((r_pre < HARVEST_CAP).astype(float), occ0)})
        return metrics


R5A_EXPOSURE_CUTOFF = 0.01                          # R5a pilot: |g - min(r, 0.2)| > 0.01 counts as exposed
                                                    # frac_exposed in last_diag is per step; the pilot pools counts


class ForagingEngine(IncomeEngine):
    """Step R5a: each start-of-step occupant forages its von Neumann neighbourhood (own site + 4 grid neighbours,
    the fixed grid in every arm). Demand 0.2 w_is on site s (w_own on the own site, (1 - w_own)/4 on each
    neighbour). Site s with total demand Q_s gives each forager the fraction a_s = min(1, r_s / Q_s) of its demand and
    loses min(r_s, Q_s); a site with Q_s = 0 is skipped. g_i = 0.2 sum_s w_is a_s, set to the literal 0.2 when every
    a_s in N(i) is 1. Everything else as R4; no random draws added; gamma = 1 is R3d exactly."""

    def __init__(self, cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho, birth_cost,
                 theta, sigma, gamma, w_own: float):
        super().__init__(cfg, mechanism, death, global_candidates, care_lam, care_juvenile, care_rho, birth_cost,
                         theta, sigma, gamma)
        if np.isnan(w_own) or not 0.0 < w_own <= 1.0:
            raise ValueError("w_own must be in (0, 1]")
        self.w_own = float(w_own)
        self.w_nb = (1.0 - self.w_own) / 4.0
        grid = self.neighbor_mask.astype(bool)
        if not (grid.sum(axis=1) == 5).all() or not grid.diagonal().all():
            raise ValueError("foraging needs a 5-site von Neumann grid neighbourhood")
        self.forage_grid = grid
        self.forage_w = np.where(np.eye(self.n_sites, dtype=bool), self.w_own, np.where(grid, self.w_nb, 0.0))
        self._r_pre_forage = None

    def harvest(self, occ: np.ndarray) -> np.ndarray:
        r = self.r
        self._r_pre_forage = r.copy()
        dm = np.where(occ[:, None], HARVEST_CAP * self.forage_w, 0.0)    # demand of forager i on site s
        Q = dm.sum(axis=0)
        pos = Q > 0
        a = np.ones(self.n_sites)
        a[pos] = np.minimum(1.0, r[pos] / Q[pos])
        g = dm @ a
        short = (self.forage_grid & (a < 1.0)[None, :]).any(axis=1)
        g = np.where(occ, np.where(short, g, HARVEST_CAP), 0.0)
        self.r = r - np.where(pos, np.minimum(r, Q), 0.0)
        self.G = np.where(occ, self.care_rho * self.G + g, self.G)
        return g

    @staticmethod
    def exposure_mask(g: np.ndarray, r_pre: np.ndarray, occ: np.ndarray) -> np.ndarray:
        """Occupants whose harvest differs by more than 0.01 from R4's own-site rule min(r, 0.2), same state."""
        # strict cutoff with a float tolerance (Codex R5a review: a true 0.01 difference can compute as 0.0100...09)
        return occ & (np.abs(g - np.minimum(r_pre, HARVEST_CAP)) > R5A_EXPOSURE_CUTOFF + 1e-12)

    def step(self):
        occ0 = self.occ.copy()
        metrics = super().step()
        g, r_pre = self.last_harvest, self._r_pre_forage
        exposed = self.exposure_mask(g, r_pre, occ0)
        near = occ0 & (self.forage_grid & ~occ0[None, :]).any(axis=1)
        m = lambda x, mask: float(x[mask].mean()) if mask.any() else float("nan")
        self.last_exposed = exposed
        self.last_diag.update({
            "n_exposed": int(exposed.sum()), "n_near_empty": int(near.sum()),
            "frac_exposed": m(exposed.astype(float), occ0),
            "harvest_near_empty": m(g, near), "harvest_away_empty": m(g, occ0 & ~near)})
        return metrics


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
                juvenile_strength: float = 0.0, exclude_focal: bool = False, care: str | None = None,
                care_lam: float | None = None, care_juvenile: int | None = None, care_rho: float | None = None,
                care_birth_cost: float | None = None, care_theta: float | None = None,
                care_sigma: float | None = None, care_gamma: float | None = None,
                care_g_start: float | None = None, care_forage_own: float | None = None, **mechanism_kwargs) -> MoranInteractionEngine:
    if exclude_focal and (death is None or lam is not None or juvenile_period is not None):
        raise ValueError("exclude_focal is only for the overlapping-generations engine (step K0 attempt 2)")
    if care is not None:
        if death is None or lam is not None or juvenile_period is not None or exclude_focal \
                or replacement not in ("local", "global"):
            raise ValueError("parental care is only for the K0 overlapping-generations engine")
        mech = ParentalMechanism(care=care, seed=int(cfg["random_seed"]), **mechanism_kwargs)
        if care_forage_own is not None and (care_gamma is None or care_g_start is not None):
            raise ValueError("care_forage_own needs care_gamma (R5a is built on R4), without care_g_start")
        if care_g_start is not None and care_gamma is None:
            raise ValueError("care_g_start needs care_gamma (DR4 is built on R4)")
        if care_gamma is not None and care_sigma is None:
            raise ValueError("care_gamma needs care_sigma (R4 is built on R3d)")
        if care_sigma is not None and care_juvenile is None:
            raise ValueError("care_sigma needs care_juvenile, care_rho, care_birth_cost and care_theta")
        if care_theta is not None and care_juvenile is None:
            raise ValueError("care_theta needs care_juvenile, care_rho and care_birth_cost")
        if care_birth_cost is not None and care_juvenile is None:
            raise ValueError("care_birth_cost needs care_juvenile and care_rho")
        if care_rho is not None and care_juvenile is None:
            raise ValueError("care_rho needs care_juvenile")
        if care_juvenile is not None:
            if care_lam is None or care not in ("offspring", "young_neighbours"):
                raise ValueError("care_juvenile needs care_lam and offspring or young_neighbours care")
            if care_sigma is not None:
                if care_theta is None or care_birth_cost is None or care_rho is None:
                    raise ValueError("care_sigma needs care_theta, care_birth_cost and care_rho")
                if care_forage_own is not None:
                    return ForagingEngine(cfg, mech, death, replacement == "global", care_lam, care_juvenile,
                                          care_rho, care_birth_cost, care_theta, care_sigma, care_gamma,
                                          care_forage_own)
                if care_gamma is not None:
                    return IncomeEngine(cfg, mech, death, replacement == "global", care_lam, care_juvenile,
                                        care_rho, care_birth_cost, care_theta, care_sigma, care_gamma,
                                        1.0 if care_g_start is None else care_g_start)
                return StarvationEngine(cfg, mech, death, replacement == "global", care_lam, care_juvenile,
                                        care_rho, care_birth_cost, care_theta, care_sigma)
            if care_theta is not None:
                if care_birth_cost is None or care_rho is None:
                    raise ValueError("care_theta needs care_birth_cost and care_rho")
                return ThresholdEngine(cfg, mech, death, replacement == "global", care_lam, care_juvenile,
                                       care_rho, care_birth_cost, care_theta)
            if care_birth_cost is not None:
                if care_rho is None:
                    raise ValueError("care_birth_cost needs care_rho")
                return BirthCostEngine(cfg, mech, death, replacement == "global", care_lam, care_juvenile,
                                       care_rho, care_birth_cost)
            if care_rho is not None:
                return CarryOverEngine(cfg, mech, death, replacement == "global", care_lam, care_juvenile, care_rho)
            return AgedSurvivalCareEngine(cfg, mech, death, replacement == "global", care_lam, care_juvenile)
        if care == "young_neighbours":
            raise ValueError("young_neighbours care needs care_juvenile")
        if care_lam is not None:
            return SurvivalCareEngine(cfg, mech, death, replacement == "global", care_lam)
        if care == "neighbours":
            raise ValueError("care='neighbours' is only for the survival-care engine (R1)")
        return ParentalEngine(cfg, mech, death, global_candidates=replacement == "global")
    if any(x is not None for x in (care_lam, care_juvenile, care_rho, care_birth_cost, care_theta, care_sigma,
                                   care_gamma, care_g_start, care_forage_own)):
        raise ValueError("care_lam / care_juvenile / care_rho / care_birth_cost need care")
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
