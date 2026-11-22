# FROZEN reference: the pure-Python model as of commit e17e493 (before the numba port), used only by the
# differential tests in test_ethnocentrism.py. Do not edit; the compiled model must match it bit for bit.
"""Python port of the NetLogo Ethnocentrism model (Wilensky 2003; Hammond & Axelrod 2006), with lineage tracking.

The update order is NetLogo's `go`, one tick:
  1. immigrate: min(immigrants_per_day, #empty) random empty cells get a new agent (random colour, random strategy).
  2. every agent's PTR (potential to reproduce) is reset to initial_ptr.
  3. interact: every agent (donor) meets each occupied von Neumann neighbour. Same colour -> it gives if
     cooperate_with_same, otherwise if cooperate_with_different. Giving costs the donor cost_of_giving and adds
     gain_of_receiving to the neighbour. PTR is not read during this phase, so the order does not matter.
  4. reproduce: agents alive before this phase, in random order, reproduce with probability PTR into a random empty
     von Neumann neighbour cell (occupancy updated as children are placed; children do not reproduce this tick).
     The child copies colour and strategy, then each mutates with probability mutation_rate (colour -> one of
     the other colours, each strategy flag toggled).
     Experiment option (not in NetLogo): colour_inheritance = "random" gives each child a colour drawn uniformly
     from all colours, independent of the parent (breaks the colour-descent link; strategy still inherited).
     With child_colour_weights set, the random colour is drawn from those weights instead of uniformly.
     Experiment option (not in NetLogo): with probability dispersal, a reproducing agent's child goes to a random
     empty cell anywhere in the world instead of a neighbouring one (lowers viscosity; 0 = NetLogo).
  5. death: every agent, including this tick's newborns, dies with probability death_rate.
  6. statistics: strategy counts after death and the tick's interaction counts go into 100-tick windows.
The world is a torus. The NetLogo reporters used by the BehaviorSpace experiments are reproduced under the same
names (fractions, not percents, as in NetLogo).

Lineage tracking (not in NetLogo): every agent gets an id, a parent id, a founder id (the immigrant its line
descends from) and a birth tick. Every `lineage_sample_every` ticks, all unordered neighbour pairs are classified
by colour (same / different) and the pedigree is used to measure how closely they are related.
"""
from __future__ import annotations

import math
from collections import deque
from typing import Any

import numpy as np

EMPTY = -1
# strategy code = 2 * cooperate_with_same + cooperate_with_different
CODE_DD, CODE_DC, CODE_CD, CODE_CC = 0, 1, 2, 3        # dd egoist, dc cosmopolitan, cd ethnocentric, cc altruist
LINEAGE_GROUP_KEYS = ("frac_same_founder", "gen_dist_mean", "gen_dist_median", "frac_gen_le2", "tmrca_median",
                      "r_pop_cs", "r_pop_cd", "r_reg_cs", "r_reg_cd")


def _neighbour_table(width: int, height: int) -> np.ndarray:
    """nbr[cell, k] for k = up, right, down, left on a torus (NetLogo neighbors4)."""
    if width < 3 or height < 3:
        raise ValueError("world must be at least 3x3 so the four neighbours are distinct")
    y, x = np.divmod(np.arange(width * height), width)
    return np.stack([((y - 1) % height) * width + x, y * width + (x + 1) % width,
                     ((y + 1) % height) * width + x, y * width + (x - 1) % width], axis=1)


class Ethnocentrism:
    def __init__(self, cfg: dict[str, Any], seed: int):
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.W, self.H = cfg["width"], cfg["height"]
        self.N = self.W * self.H
        self.nbr = _neighbour_table(self.W, self.H)
        self.agent = np.full(self.N, EMPTY, dtype=np.int64)    # agent id per cell
        self.color = np.zeros(self.N, dtype=np.int8)
        self.cs = np.zeros(self.N, dtype=bool)                 # cooperate with same colour
        self.cd = np.zeros(self.N, dtype=bool)                 # cooperate with different colour
        self.ptr = np.zeros(self.N, dtype=np.float64)
        # pedigree, indexed by agent id
        self.parent: list[int] = []
        self.founder: list[int] = []
        self.birth: list[int] = []
        self.tick = 0
        self.n_dispersed = 0                                   # offspring placed by global dispersal
        self.agg = dict(meet=0, meetown=0, meetother=0, coopown=0, coopother=0, defother=0)
        self.turn = dict(self.agg)
        self.win = {k: deque(maxlen=100) for k in
                    ("cc", "cd", "dc", "dd", "coopown", "defother", "meetown", "coop", "meet", "meetother")}
        self.lineage_samples: list[dict[str, Any]] = []
        if cfg["setup"] == "full":
            for cell in range(self.N):
                self._create_immigrant(cell)
        elif cfg["setup"] != "empty":
            raise ValueError(f"unknown setup {cfg['setup']!r}")
        if cfg.get("colour_inheritance", "inherited") not in ("inherited", "random"):
            raise ValueError(f"unknown colour_inheritance {cfg['colour_inheritance']!r}")
        w = cfg.get("child_colour_weights")
        if w is not None:
            if cfg.get("colour_inheritance", "inherited") != "random":
                raise ValueError("child_colour_weights only applies with colour_inheritance 'random'")
            w = np.asarray(w, dtype=float)
            if w.shape != (cfg["n_colors"],) or (w < 0).any() or not math.isclose(w.sum(), 1.0, abs_tol=1e-12):
                raise ValueError("child_colour_weights must be n_colors non-negative weights summing to 1")
            self._colour_cdf = np.cumsum(w) / w.sum()
            self._colour_cdf[-1] = 1.0                         # rng.random() < 1, so the index stays in range
        if not 0.0 <= cfg.get("dispersal", 0.0) <= 1.0:
            raise ValueError(f"dispersal must be in [0, 1], got {cfg['dispersal']!r}")

    # ---------------------------------------------------------------- agents
    def _new_id(self, parent: int) -> int:
        i = len(self.parent)
        self.parent.append(parent)
        self.founder.append(i if parent == EMPTY else self.founder[parent])
        self.birth.append(self.tick)
        return i

    def _create_immigrant(self, cell: int) -> None:
        c = self.cfg
        self.agent[cell] = self._new_id(EMPTY)
        self.color[cell] = self.rng.integers(c["n_colors"])
        self.cs[cell] = self.rng.random() < c["immigrant_chance_cooperate_with_same"]
        self.cd[cell] = self.rng.random() < c["immigrant_chance_cooperate_with_different"]
        self.ptr[cell] = c["initial_ptr"]

    def _hatch(self, parent_cell: int, cell: int) -> None:
        c, rng = self.cfg, self.rng
        self.agent[cell] = self._new_id(int(self.agent[parent_cell]))
        if c.get("colour_inheritance", "inherited") == "random":   # experiment: colour independent of the parent
            w = c.get("child_colour_weights")
            if w is None:
                col = int(rng.integers(c["n_colors"]))
            else:                                              # skewed but still independent of the parent
                col = int(np.searchsorted(self._colour_cdf, rng.random(), side="right"))
        else:
            col = int(self.color[parent_cell])
            if rng.random() < c["mutation_rate"]:             # NetLogo: redraw until the colour differs
                col = (col + 1 + int(rng.integers(c["n_colors"] - 1))) % c["n_colors"]
        self.color[cell] = col
        self.cs[cell] = self.cs[parent_cell] ^ (rng.random() < c["mutation_rate"])
        self.cd[cell] = self.cd[parent_cell] ^ (rng.random() < c["mutation_rate"])
        self.ptr[cell] = self.ptr[parent_cell]

    # ---------------------------------------------------------------- one tick
    def step(self) -> None:
        self._immigrate()
        self.ptr[self.agent != EMPTY] = self.cfg["initial_ptr"]
        self._interact()
        self._reproduce()
        self._death()
        self._update_stats()
        self.tick += 1
        every = self.cfg["lineage_sample_every"]
        if every and (self.tick % every == 0 or self.tick == self.cfg["ticks"]):
            self.lineage_samples.append(self.lineage_metrics())

    def _immigrate(self) -> None:
        empty = np.flatnonzero(self.agent == EMPTY)
        k = min(self.cfg["immigrants_per_day"], empty.size)
        for cell in self.rng.choice(empty, size=k, replace=False):
            self._create_immigrant(int(cell))

    def _interact(self) -> None:
        """Donor = cell, recipient = its neighbour; PTR is only written here, so order does not matter."""
        c = self.cfg
        occ = self.agent != EMPTY
        t = dict.fromkeys(self.agg, 0)
        for k4 in range(4):
            nb = self.nbr[:, k4]
            pair = occ & occ[nb]
            same = pair & (self.color == self.color[nb])
            other = pair & ~same
            give = (same & self.cs) | (other & self.cd)
            t["meet"] += int(pair.sum())
            t["meetown"] += int(same.sum())
            t["meetother"] += int(other.sum())
            t["coopown"] += int((same & self.cs).sum())
            t["coopother"] += int((other & self.cd).sum())
            t["defother"] += int((other & ~self.cd).sum())
            self.ptr -= c["cost_of_giving"] * give
            np.add.at(self.ptr, nb[give], c["gain_of_receiving"])
        self.turn = t
        for key, v in t.items():
            self.agg[key] += v

    def _reproduce(self) -> None:
        """Agents alive now, in random order; children are placed at once but do not reproduce this tick."""
        rng, agent, nbr = self.rng, self.agent, self.nbr
        order = rng.permutation(np.flatnonzero(agent != EMPTY))
        lucky = order[rng.random(order.size) < self.ptr[order]]   # the per-agent draw NetLogo makes, in order
        d = self.cfg.get("dispersal", 0.0)
        for cell in lucky.tolist():
            if d > 0 and rng.random() < d:                       # experiment: disperse to any empty cell
                empties = np.flatnonzero(agent == EMPTY)
                if empties.size:
                    self._hatch(cell, int(empties[int(rng.integers(empties.size))]))
                    self.n_dispersed += 1
                continue
            free = [n for n in nbr[cell].tolist() if agent[n] == EMPTY]
            if free:
                self._hatch(cell, free[int(rng.integers(len(free)))])

    def _death(self) -> None:
        dies = (self.agent != EMPTY) & (self.rng.random(self.N) < self.cfg["death_rate"])
        self.agent[dies] = EMPTY

    def _update_stats(self) -> None:
        t, w = self.turn, self.win
        occ = self.agent != EMPTY
        code = 2 * self.cs.astype(np.int8) + self.cd.astype(np.int8)
        counts = np.bincount(code[occ], minlength=4)
        w["dd"].append(int(counts[CODE_DD])); w["dc"].append(int(counts[CODE_DC]))
        w["cd"].append(int(counts[CODE_CD])); w["cc"].append(int(counts[CODE_CC]))
        w["coopown"].append(t["coopown"]); w["defother"].append(t["defother"]); w["meetown"].append(t["meetown"])
        w["coop"].append(t["coopown"] + t["coopother"]); w["meet"].append(t["meet"]); w["meetother"].append(t["meetother"])

    def run(self) -> dict[str, Any]:
        while self.tick < self.cfg["ticks"]:
            self.step()
        return {"reporters": self.reporters(), "lineage": self.lineage_samples,
                "population": int((self.agent != EMPTY).sum()), "births_total": len(self.parent),  # incl. immigrants
                "offspring_total": sum(p != EMPTY for p in self.parent), "dispersed_total": self.n_dispersed,
                "last100_meetings": int(sum(self.win["meet"]))}

    # ---------------------------------------------------------------- NetLogo reporters
    def reporters(self) -> dict[str, float]:
        t, a, w = self.turn, self.agg, self.win
        d = lambda x, y: x / max(1, y)
        mean = lambda q: sum(q) / max(1, len(q))
        cc, cd, dc, dd = mean(w["cc"]), mean(w["cd"]), mean(w["dc"]), mean(w["dd"])
        tot = max(1, cc + cd + dc + dd)
        s = {k: sum(q) for k, q in w.items()}
        return {
            "meetown-percent": d(t["meetown"], t["meet"]), "meetown-agg-percent": d(a["meetown"], a["meet"]),
            "coopown-percent": d(t["coopown"], t["meetown"]), "coopown-agg-percent": d(a["coopown"], a["meetown"]),
            "defother-percent": d(t["defother"], t["meetother"]), "defother-agg-percent": d(a["defother"], a["meetother"]),
            "consist-ethno-percent": d(t["defother"] + t["coopown"], t["meet"]),
            "consist-ethno-agg-percent": d(a["defother"] + a["coopown"], a["meet"]),
            "coop-percent": d(t["coopown"] + t["coopother"], t["meet"]),
            "coop-agg-percent": d(a["coopown"] + a["coopother"], a["meet"]),
            "cc-percent": cc / tot, "cd-percent": cd / tot, "dc-percent": dc / tot, "dd-percent": dd / tot,
            "last100coopown-percent": d(s["coopown"], s["meetown"]),
            "last100defother-percent": d(s["defother"], s["meetother"]),
            "last100consist-ethno-percent": d(s["defother"] + s["coopown"], s["meet"]),
            "last100meetown-percent": d(s["meetown"], s["meet"]),
            "last100coop-percent": d(s["coop"], s["meet"]),
        }

    # ---------------------------------------------------------------- lineage
    def _chain(self, i: int) -> list[int]:
        """Ancestor ids from the founder down to i (inclusive)."""
        out = []
        while i != EMPTY:
            out.append(i)
            i = self.parent[i]
        out.reverse()
        return out

    def lineage_metrics(self) -> dict[str, Any]:
        """Pedigree relatedness of all unordered von Neumann neighbour pairs, split by same/different colour.

        For each pair: same founder (shares an immigrant ancestor) or not; if so, the most recent common ancestor
        (MRCA), the number of births separating the two (`gen_dist`, birth events from MRCA to each, summed; 1 =
        parent-offspring, 2 = siblings or grandparent-grandchild) and the MRCA's age (`tmrca`, ticks since its birth). Two strategy statistics,
        for x = cooperate_with_same (cs) and cooperate_with_different (cd); see the comments where they are computed.
        Undefined values (no pairs of a kind, no variation) are NaN; the output keys are always the same.
        """
        occ = self.agent != EMPTY
        cells = np.flatnonzero(occ)
        nan = float("nan")
        out: dict[str, Any] = {"tick": self.tick, "population": int(cells.size), "n_founders_alive": 0,
                               "frac_pairs_same_colour": nan, "colour_fidelity": nan}
        for g in ("all", "same", "diff"):
            out[f"{g}_n_pairs"] = 0
            for k in LINEAGE_GROUP_KEYS:
                out[f"{g}_{k}"] = nan
        if cells.size == 0:
            return out
        a_list, b_list = [], []
        for k4 in (1, 2):                                       # right, down: each unordered pair once
            nb = self.nbr[:, k4]
            m = occ & occ[nb]
            a_list.append(np.flatnonzero(m)); b_list.append(nb[m])
        A, B = np.concatenate(a_list), np.concatenate(b_list)
        founder = np.asarray(self.founder, dtype=np.int64)
        out["n_founders_alive"] = int(np.unique(founder[self.agent[cells]]).size)
        if A.size == 0:
            return out
        same_col = self.color[A] == self.color[B]
        ida, idb = self.agent[A], self.agent[B]
        same_f = founder[ida] == founder[idb]
        chains: dict[int, list[int]] = {}
        gen = np.full(A.size, -1, dtype=np.int64)
        tm = np.full(A.size, -1, dtype=np.int64)
        for p in np.flatnonzero(same_f).tolist():
            x, y = int(ida[p]), int(idb[p])
            cx = chains.get(x) or chains.setdefault(x, self._chain(x))
            cy = chains.get(y) or chains.setdefault(y, self._chain(y))
            j = 0
            n = min(len(cx), len(cy))
            while j < n and cx[j] == cy[j]:
                j += 1
            mrca = cx[j - 1]                                    # j >= 1: same founder
            gen[p] = (len(cx) - j) + (len(cy) - j)
            tm[p] = self.tick - self.birth[mrca]
        out["frac_pairs_same_colour"] = float(same_col.mean())
        for name, mask in (("all", np.ones(A.size, bool)), ("same", same_col), ("diff", ~same_col)):
            n = int(mask.sum())
            out[f"{name}_n_pairs"] = n
            if n == 0:
                continue
            sf = same_f[mask]
            out[f"{name}_frac_same_founder"] = float(sf.mean())
            g, tt = gen[mask][sf], tm[mask][sf]
            if g.size:
                out[f"{name}_gen_dist_mean"] = float(g.mean())
                out[f"{name}_gen_dist_median"] = float(np.median(g))
                out[f"{name}_tmrca_median"] = float(np.median(tt))
            out[f"{name}_frac_gen_le2"] = float((g <= 2).sum() / n)   # at most two births apart, of all pairs
            for trait, arr in (("cs", self.cs), ("cd", self.cd)):
                xs = arr[cells].astype(float)
                xbar, var = xs.mean(), xs.var()
                xa, xb = arr[A[mask]].astype(float), arr[B[mask]].astype(float)
                # r_pop: joint flag over pairs relative to the living population (pre-registered statistic;
                # not bounded by 1, and raised by helpers being enriched in the group as well as by kinship).
                out[f"{name}_r_pop_{trait}"] = float(((xa * xb).mean() - xbar ** 2) / var) if var > 0 else nan
                # r_reg: Hamilton regression of partner's flag on own flag over the group's ordered pairs
                # (symmetric, so the pooled-endpoint correlation); baseline is the group's own endpoints.
                both = np.concatenate([xa, xb]); vb = both.var()
                out[f"{name}_r_reg_{trait}"] = float(((xa * xb).mean() - both.mean() ** 2) / vb) if vb > 0 else nan
        same_f_pairs = int(same_f.sum())
        out["colour_fidelity"] = float((same_col & same_f).sum() / same_f_pairs) if same_f_pairs else nan
        return out
