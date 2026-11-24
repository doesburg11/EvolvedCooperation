"""Step 5 restart: births into free space on the K1 parental-care base (pre-registration STEP5_RESTART.md).

A standalone lattice model (the Moran engine refills every site, so it cannot hold vacancies). It keeps K1's
lattice, lineage labels, mutation, care routing and cost, and replaces the replacement lottery by deaths at rate
`d` and births into vacant sites.

Birth modes:
  local   -- target drawn uniformly among the parent's vacant grid neighbours; none -> attempt fails
  global  -- target drawn uniformly among all vacancies
  dd      -- local; if no vacant neighbour, a random vacancy anywhere, reached with probability `dd_survival`
  refill  -- no vacancies: each dead site is refilled by a parent drawn from its surviving neighbours with probability
             proportional to p_i (from all survivors if none survives); a parent can fill several sites

Care modes:
  offspring -- B*h_i split equally among i's living offspring (by id, any distance); lost if none
  neighbours -- B*h_i/4 to each grid neighbour; the share to an empty neighbour is lost; never self
  matched   -- n_i = i's living-offspring count; B*h_i/n_i to each of n_i occupied non-offspring grid neighbours drawn
               without replacement (redrawn each update); donors are visited in a random order and each recipient
               receives from at most one donor per update (amendment A1: like an offspring, which has one parent);
               missing recipients' shares are lost (shortfall); n_i = 0 -> lost
  none      -- no benefit (B = 0)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

WIDTH = HEIGHT = 24
N_SITES = WIDTH * HEIGHT
LINEAGES = 18
MUTATION_RATE = 0.02
MUTATION_SD = 0.04
C_COST = 0.2
T_SURV = 0.12
SEED_DEATH, SEED_BIRTH, SEED_RESOLVE, SEED_MATCHED = 11_000_000, 15_000_000, 16_000_000, 17_000_000


def neighbour_table(width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    """(N, 4) von Neumann neighbours on a torus, without self, in the order left, right, up, down."""
    nb = np.empty((width * height, 4), dtype=np.int64)
    for y in range(height):
        for x in range(width):
            i = y * width + x
            nb[i] = [y * width + (x - 1) % width, y * width + (x + 1) % width,
                     ((y - 1) % height) * width + x, ((y + 1) % height) * width + x]
    return nb


NB = neighbour_table()


@dataclass
class Params:
    B: float
    p0: float
    d: float
    care: str = "offspring"        # offspring | neighbours | matched | none
    births: str = "local"          # local | global | dd | refill
    attempt: int = 1               # 1: care on fecundity; 2: half on survival (R1 attempt-2 rule), half on fecundity
    C: float = C_COST
    dd_survival: float = 0.8
    mutation_rate: float = MUTATION_RATE
    mutation_sd: float = MUTATION_SD
    initial_mean: float = 0.05
    initial_sd: float = 0.02

    def __post_init__(self):
        assert self.care in {"offspring", "neighbours", "matched", "none"}
        assert self.births in {"local", "global", "dd", "refill"}
        assert self.attempt in (1, 2)


@dataclass
class State:
    occ: np.ndarray
    h: np.ndarray
    lineage: np.ndarray
    ident: np.ndarray
    parent: np.ndarray
    next_id: int
    step_index: int = 0
    last: dict = field(default_factory=dict)


class Step5Model:
    def __init__(self, params: Params, seed: int):
        self.p = params
        self.seed = seed
        rng0 = np.random.default_rng(seed)
        self.rng_death = np.random.default_rng(seed + SEED_DEATH)
        self.rng_birth = np.random.default_rng(seed + SEED_BIRTH)
        self.rng_resolve = np.random.default_rng(seed + SEED_RESOLVE)
        self.rng_matched = np.random.default_rng(seed + SEED_MATCHED)
        h = np.clip(rng0.normal(params.initial_mean, params.initial_sd, size=N_SITES), 0.0, 1.0)
        lineage = rng0.integers(0, LINEAGES, size=N_SITES)
        self.s = State(occ=np.ones(N_SITES, dtype=bool), h=h, lineage=lineage,
                       ident=np.arange(N_SITES, dtype=np.int64), parent=np.full(N_SITES, -1, dtype=np.int64),
                       next_id=N_SITES)

    # ------------------------------------------------------------------ care
    def offspring_counts(self) -> tuple[np.ndarray, np.ndarray]:
        """n[i] = living offspring of the occupant at site i; psite[j] = site of j's living parent (-1 if none)."""
        s = self.s
        psite = np.full(N_SITES, -1, dtype=np.int64)
        occ_sites = np.flatnonzero(s.occ)
        site_of = {int(s.ident[i]): int(i) for i in occ_sites}
        for j in occ_sites:
            pid = int(s.parent[j])
            if pid >= 0:
                psite[j] = site_of.get(pid, -1)
        n = np.bincount(psite[psite >= 0], minlength=N_SITES)
        return n, psite

    def care_received(self, n: np.ndarray, psite: np.ndarray) -> tuple[np.ndarray, float, float]:
        """Return R (care received per site), benefit produced and benefit lost (both weighted by B*h).

        For the matched control, the part of the loss due to too few eligible recipients is stored in
        `self.shortfall_lost`."""
        p, s = self.p, self.s
        self.shortfall_lost = 0.0
        R = np.zeros(N_SITES)
        give = np.where(s.occ, p.B * s.h, 0.0)
        produced = float(give.sum())
        lost = 0.0
        if p.care == "none" or p.B == 0:
            return R, produced, produced if produced else 0.0
        if p.care == "offspring":
            rec = np.flatnonzero(psite >= 0)
            R[rec] = give[psite[rec]] / n[psite[rec]]
            lost = float(give[(n == 0)].sum())
        elif p.care == "neighbours":
            share = give / 4.0
            for k in range(4):
                tgt = NB[:, k]
                ok = s.occ[tgt]
                np.add.at(R, tgt[ok], share[ok])
                lost += float(share[~ok].sum())
        elif p.care == "matched":
            donors = np.flatnonzero(s.occ & (give > 0.0))
            lost += float(give[donors[n[donors] == 0]].sum())
            donors = donors[n[donors] > 0]
            taken = np.zeros(N_SITES, dtype=bool)
            for i in donors[self.rng_matched.permutation(donors.size)] if donors.size else []:
                ni = int(n[i])
                cand = [int(j) for j in NB[i] if s.occ[j] and psite[j] != i and not taken[j]]
                m = min(ni, len(cand))
                if m:
                    pick = self.rng_matched.choice(len(cand), size=m, replace=False)
                    for q in pick:
                        R[cand[q]] += give[i] / ni
                        taken[cand[q]] = True
                short = give[i] * (ni - m) / ni
                lost += short
                self.shortfall_lost += short
        return R, produced, lost

    # ------------------------------------------------------------------ one update
    def step(self) -> dict:
        p, s = self.p, self.s
        occ0 = s.occ.copy()
        n, psite = self.offspring_counts()
        R, produced, lost = self.care_received(n, psite)
        if p.attempt == 1:
            W = 1.0 + R - p.C * s.h
            dprob = np.full(N_SITES, p.d)
        else:
            W = 1.0 + 0.5 * R - p.C * s.h
            dprob = p.d * np.exp(-0.5 * R / T_SURV)
        W = np.where(occ0, W, 0.0)
        # deaths (one uniform per site, always drawn)
        u = self.rng_death.random(N_SITES)
        dies = occ0 & (u < dprob)
        surv = occ0 & ~dies
        raw_p = p.p0 * np.maximum(0.0, W)
        clipped = int(np.sum(surv & (raw_p > 1.0)))
        pb = np.minimum(1.0, raw_p)
        vacant = ~surv
        exposure_num = int(np.sum(surv & vacant[NB].any(axis=1)))
        n_surv = int(surv.sum())

        births: list[tuple[int, int]] = []           # (target site, parent site)
        attempts = failed = 0
        if p.births == "refill":
            for t in np.flatnonzero(dies):
                cand = NB[t][surv[NB[t]]]
                if cand.size == 0:
                    cand = np.flatnonzero(surv)
                if cand.size == 0:
                    break
                w = pb[cand]
                if w.sum() <= 0:
                    continue
                par = int(cand[self.rng_resolve.choice(cand.size, p=w / w.sum())])
                births.append((int(t), par))
        else:
            a = self.rng_birth.random(N_SITES) < pb
            attempting = np.flatnonzero(surv & a)
            claims: dict[int, list[int]] = {}
            all_vac = np.flatnonzero(vacant)
            for i in attempting:
                attempts += 1
                vn = NB[i][vacant[NB[i]]]
                vn = np.sort(vn)
                if p.births == "global":
                    if all_vac.size == 0:
                        failed += 1
                        continue
                    t = int(all_vac[self.rng_birth.integers(all_vac.size)])
                elif vn.size:
                    t = int(vn[self.rng_birth.integers(vn.size)])
                elif p.births == "dd" and all_vac.size:
                    t = int(all_vac[self.rng_birth.integers(all_vac.size)])
                    if self.rng_birth.random() >= p.dd_survival:
                        failed += 1
                        continue
                else:
                    failed += 1
                    continue
                claims.setdefault(t, []).append(int(i))
            for t in sorted(claims):
                c = claims[t]
                par = c[0] if len(c) == 1 else c[int(self.rng_resolve.integers(len(c)))]
                births.append((t, par))
                failed += len(c) - 1          # claim losers (amendment A1)

        # apply deaths, then births (mutation for all births at once, in increasing target order)
        s.occ = surv.copy()
        births.sort()
        if births:
            tg = np.array([b[0] for b in births])
            pa = np.array([b[1] for b in births])
            newh = s.h[pa].copy()
            mut = self.rng_resolve.random(len(births)) < p.mutation_rate
            if mut.any():
                newh[mut] = np.clip(newh[mut] + self.rng_resolve.normal(0.0, p.mutation_sd, int(mut.sum())), 0.0, 1.0)
            newlin = s.lineage[pa].copy()
            newpar = s.ident[pa].copy()
            s.h[tg] = newh
            s.lineage[tg] = newlin
            s.parent[tg] = newpar
            s.ident[tg] = np.arange(s.next_id, s.next_id + len(births))
            s.next_id += len(births)
            s.occ[tg] = True
        s.h = np.where(s.occ, s.h, 0.0)
        s.step_index += 1

        occ_n0 = int(occ0.sum())
        hp = s.h[occ0] if occ_n0 else np.array([])
        s.last = {
            "occupancy_start": occ_n0 / N_SITES,
            "exposure": exposure_num / n_surv if n_surv else float("nan"),
            "exposed_survivors": exposure_num,
            "survivors": n_surv,
            "failed_per_occupant": failed / occ_n0 if occ_n0 else float("nan"),
            "shortfall_lost": self.shortfall_lost / produced if produced > 0 else float("nan"),
            "births_per_occupant": len(births) / occ_n0 if occ_n0 else float("nan"),
            "failed_per_attempt": failed / attempts if attempts else float("nan"),
            "clipped_fraction": clipped / n_surv if n_surv else float("nan"),
            "offspring_mean": float(n[occ0].mean()) if occ_n0 else float("nan"),
            "frac_no_offspring": float((n[occ0] == 0).mean()) if occ_n0 else float("nan"),
            "benefit_lost": lost / produced if produced > 0 else float("nan"),
            "mean_h_start": float(hp.mean()) if hp.size else float("nan"),
            "own_offspring_share": self._own_offspring_share(occ0, psite),
        }
        return s.last

    def _own_offspring_share(self, occ0: np.ndarray, psite: np.ndarray) -> float:
        """Mean over occupants with >= 1 occupied neighbour: share of occupied neighbours that are own offspring."""
        tot, cnt = 0.0, 0
        for i in np.flatnonzero(occ0):
            nbo = NB[i][occ0[NB[i]]]
            if nbo.size:
                tot += float(np.mean(psite[nbo] == i))
                cnt += 1
        return tot / cnt if cnt else float("nan")

    # ------------------------------------------------------------------ measures
    def mean_h(self) -> float:
        return float(self.s.h[self.s.occ].mean()) if self.s.occ.any() else float("nan")

    def occupancy(self) -> float:
        return float(self.s.occ.mean())

    def extinct(self) -> bool:
        return not self.s.occ.any()

    def neighbour_corr(self) -> float:
        """K1's estimator (analysis.neighbour_correlation): Pearson correlation of h across neighbour edges, each
        edge once, oriented from the lower to the higher site index as in K1's `np.triu` edge list, not
        symmetrized; restricted to edges with both ends occupied (amendment A1). NaN for fewer than 2 edges or a
        (numerically) uniform field."""
        s = self.s
        a0 = np.repeat(np.arange(N_SITES), 2)
        b0 = NB[:, [1, 3]].reshape(-1)
        a, b = np.minimum(a0, b0), np.maximum(a0, b0)      # K1 orientation: lower site index first
        ok = s.occ[a] & s.occ[b]
        if ok.sum() < 2:
            return float("nan")
        x, y = s.h[a[ok]], s.h[b[ok]]
        scale = max(1.0, float(np.abs(s.h).max()))
        if x.std() <= 1e-12 * scale or y.std() <= 1e-12 * scale:
            return float("nan")
        return float(np.corrcoef(x, y)[0, 1])

    def parent_offspring_corr(self) -> float:
        s = self.s
        _, psite = self.offspring_counts()
        j = np.flatnonzero(psite >= 0)
        if j.size < 3:
            return float("nan")
        x, y = s.h[psite[j]], s.h[j]
        if np.std(x) == 0 or np.std(y) == 0:
            return float("nan")
        return float(np.corrcoef(x, y)[0, 1])
