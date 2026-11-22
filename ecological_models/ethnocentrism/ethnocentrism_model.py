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
     Experiment option (not in NetLogo): shuffle_fraction f > 0 then selects each occupied cell with probability f
     and permutes the agents (id, colour, flags, PTR) among the selected cells. Occupied cells stay occupied; the
     relatedness of neighbours is broken. No draws are made when f = 0.
  6. statistics: strategy counts after death and the tick's interaction counts go into 100-tick windows.
The world is a torus. The NetLogo reporters used by the BehaviorSpace experiments are reproduced under the same
names (fractions, not percents, as in NetLogo).

Speed: the per-agent loops (interaction, reproduction + hatching, pedigree MRCA search) are compiled with numba.
They draw from the same numpy Generator in the same order as the earlier pure-Python version, so every committed
run replays bit for bit (the floating-point operations on PTR are also kept in the same order).

Lineage tracking (not in NetLogo): every agent gets an id, a parent id, a founder id (the immigrant its line
descends from) and a birth tick. Every `lineage_sample_every` ticks, all unordered neighbour pairs are classified
by colour (same / different) and the pedigree is used to measure how closely they are related.
"""
from __future__ import annotations

import math
from collections import deque
from typing import Any

import numpy as np
from numba import njit

EMPTY = -1
# strategy code = 2 * cooperate_with_same + cooperate_with_different
CODE_DD, CODE_DC, CODE_CD, CODE_CC = 0, 1, 2, 3        # dd egoist, dc cosmopolitan, cd ethnocentric, cc altruist
LINEAGE_GROUP_KEYS = ("frac_same_founder", "gen_dist_mean", "gen_dist_median", "frac_gen_le2", "tmrca_median",
                      "r_pop_cs", "r_pop_cd", "r_reg_cs", "r_reg_cd")


# ---------------------------------------------------------------- compiled kernels
COLOUR_INHERITED, COLOUR_RANDOM, COLOUR_WEIGHTED = 0, 1, 2


@njit(cache=True)
def _hatch_nb(rng, parent_cell, cell, agent, color, cs, cd, ptr, ped, n_ids, tick, colour_mode, cdf, n_colors, mut):
    """Child of the agent in parent_cell into cell; returns the new id count. ped rows: parent, founder, birth, depth.
    Draw order (must not change): colour draw(s), then the cs flip draw, then the cd flip draw."""
    pid = agent[parent_cell]
    i = n_ids
    ped[0, i] = pid
    if pid == EMPTY:
        ped[1, i] = i
        ped[3, i] = 0
    else:
        ped[1, i] = ped[1, pid]
        ped[3, i] = ped[3, pid] + 1
    ped[2, i] = tick
    agent[cell] = i
    if colour_mode == COLOUR_RANDOM:                  # experiment: colour independent of the parent
        col = rng.integers(0, n_colors)
    elif colour_mode == COLOUR_WEIGHTED:              # skewed but still independent of the parent
        u = rng.random()
        col = 0
        for k in range(cdf.size):                     # == np.searchsorted(cdf, u, side="right")
            if cdf[k] <= u:
                col += 1
    else:
        col = np.int64(color[parent_cell])
        if rng.random() < mut:                        # NetLogo: redraw until the colour differs
            col = (col + 1 + rng.integers(0, n_colors - 1)) % n_colors
    color[cell] = col
    cs[cell] = cs[parent_cell] ^ (rng.random() < mut)
    cd[cell] = cd[parent_cell] ^ (rng.random() < mut)
    ptr[cell] = ptr[parent_cell]
    return i + 1


@njit(cache=True)
def _fenwick_add(tree, cell, delta):
    i = cell + 1
    while i < tree.size:
        tree[i] += delta
        i += i & -i


@njit(cache=True)
def _fenwick_kth(tree, k):
    """Cell index of the k-th (0-based) flagged cell in ascending order (== np.flatnonzero(flags)[k])."""
    n = tree.size - 1
    step = 1
    while step * 2 <= n:
        step *= 2
    pos, rem = 0, k + 1
    while step:
        if pos + step <= n and tree[pos + step] < rem:
            pos += step
            rem -= tree[pos]
        step //= 2
    return pos


@njit(cache=True)
def _reproduce_nb(rng, lucky, d, nbr, agent, color, cs, cd, ptr, ped, n_ids, tick, colour_mode, cdf, n_colors, mut):
    """Lucky cells in order: with prob. d (draw only if d > 0) the child goes to a uniformly chosen empty cell
    anywhere, else to a uniformly chosen empty von Neumann neighbour (up, right, down, left order)."""
    n_disp = 0
    tree = np.zeros(agent.size + 1, dtype=np.int64)   # Fenwick tree over empty cells, only used if d > 0
    n_empty = 0
    if d > 0:
        for c in range(agent.size):
            if agent[c] == EMPTY:
                tree[c + 1] += 1
                n_empty += 1
        for i in range(1, tree.size):
            j = i + (i & -i)
            if j < tree.size:
                tree[j] += tree[i]
    free = np.empty(4, dtype=np.int64)
    for cell in lucky:
        if d > 0 and rng.random() < d:                # experiment: disperse to any empty cell
            if n_empty > 0:
                target = _fenwick_kth(tree, rng.integers(0, n_empty))
                n_ids = _hatch_nb(rng, cell, target, agent, color, cs, cd, ptr, ped, n_ids, tick,
                                  colour_mode, cdf, n_colors, mut)
                _fenwick_add(tree, target, -1)
                n_empty -= 1
                n_disp += 1
            continue
        nf = 0
        for k4 in range(4):
            nb = nbr[cell, k4]
            if agent[nb] == EMPTY:
                free[nf] = nb
                nf += 1
        if nf:
            target = free[rng.integers(0, nf)]
            n_ids = _hatch_nb(rng, cell, target, agent, color, cs, cd, ptr, ped, n_ids, tick,
                              colour_mode, cdf, n_colors, mut)
            if d > 0:
                _fenwick_add(tree, target, -1)
                n_empty -= 1
    return n_ids, n_disp


@njit(cache=True)
def _interact_nb(agent, color, cs, cd, ptr, nbr, cost, gain, counts, by_code):
    """counts += meet, meetown, meetother, coopown, coopother, defother; by_code[code] += (meetings, own-colour
    meetings) per donor strategy code. Per direction, all donor costs are subtracted before the gains are added
    (the order of the earlier vectorised version, for identical floats)."""
    n = agent.size
    give = np.zeros(n, dtype=np.bool_)
    for k4 in range(4):
        for c in range(n):
            nb = nbr[c, k4]
            g = False
            if agent[c] != EMPTY and agent[nb] != EMPTY:
                counts[0] += 1
                code = 2 * np.int64(cs[c]) + np.int64(cd[c])
                by_code[code, 0] += 1
                if color[c] == color[nb]:
                    counts[1] += 1
                    by_code[code, 1] += 1
                    if cs[c]:
                        counts[3] += 1
                        g = True
                else:
                    counts[2] += 1
                    if cd[c]:
                        counts[4] += 1
                        g = True
                    else:
                        counts[5] += 1
            give[c] = g
        for c in range(n):                            # every cell, as the vectorised ptr -= cost * give did
            ptr[c] -= cost * (1.0 if give[c] else 0.0)    # (keeps signed zeros and inf * 0 = NaN identical)
        for c in range(n):
            if give[c]:
                ptr[nbr[c, k4]] += gain


@njit(cache=True)
def _mrca_nb(ida, idb, pairs, parent, depth, birth, tick, gen, tm):
    """For same-founder pairs: births separating the two (via the MRCA) and the MRCA's age in ticks."""
    for p in pairs:
        x, y = ida[p], idb[p]
        dx, dy = depth[x], depth[y]
        while dx > dy:
            x = parent[x]; dx -= 1
        while dy > dx:
            y = parent[y]; dy -= 1
        while x != y:
            x = parent[x]; y = parent[y]; dx -= 1
        gen[p] = depth[ida[p]] + depth[idb[p]] - 2 * dx
        tm[p] = tick - birth[x]


def _neighbour_table(width: int, height: int) -> np.ndarray:
    """nbr[cell, k] for k = up, right, down, left on a torus (NetLogo neighbors4)."""
    if width < 3 or height < 3:
        raise ValueError("world must be at least 3x3 so the four neighbours are distinct")
    y, x = np.divmod(np.arange(width * height), width)
    return np.stack([((y - 1) % height) * width + x, y * width + (x + 1) % width,
                     ((y + 1) % height) * width + x, y * width + (x - 1) % width], axis=1)


class Ethnocentrism:
    def __init__(self, cfg: dict[str, Any], seed: int):
        # cfg is copied and read once: the kernels' parameters below are fixed at construction. Supported numeric
        # inputs are Python / numpy float64-compatible numbers (a longdouble cost, or np.errstate(invalid="raise"),
        # can behave differently from the earlier pure-Python version).
        cfg = dict(cfg)
        if isinstance(cfg["n_colors"], bool) or not isinstance(cfg["n_colors"], (int, np.integer)) \
                or not 1 <= cfg["n_colors"] <= 128:
            raise ValueError("n_colors must be an integer in 1..128 (colour ids 0..127 are stored as int8)")
        if cfg["n_colors"] == 1 and cfg["mutation_rate"] > 0 and cfg.get("colour_inheritance", "inherited") == "inherited":
            raise ValueError("colour mutation needs at least 2 colours")   # numpy's integers(0) raised here before
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
        # pedigree, indexed by agent id: rows parent, founder, birth tick, depth (births since the founder)
        self.ped = np.zeros((4, 4096), dtype=np.int64)
        self.n_ids = 0
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
        if not 0.0 <= cfg.get("shuffle_fraction", 0.0) <= 1.0:
            raise ValueError(f"shuffle_fraction must be in [0, 1], got {cfg['shuffle_fraction']!r}")
        self._shuffle_f = float(cfg.get("shuffle_fraction", 0.0))
        # last-100-tick accumulators (no random draws): meetings by donor strategy, and founder sharing among the
        # neighbour pairs that are about to interact (after immigration, before interaction)
        self.by_code = np.zeros((4, 2), dtype=np.int64)
        self.ikin = {"pairs": 0, "same_founder": 0, "expected_weighted": 0.0, "ticks_with_pairs": 0, "ticks": 0}
        # The compiled kernels take plain Python floats (a numpy float32 threshold would compare differently).
        self._mut, self._cost, self._gain = (float(cfg["mutation_rate"]), float(cfg["cost_of_giving"]),
                                             float(cfg["gain_of_receiving"]))
        self._dispersal = float(cfg.get("dispersal", 0.0))
        self._colour_mode = (COLOUR_INHERITED if cfg.get("colour_inheritance", "inherited") == "inherited"
                             else COLOUR_RANDOM if w is None else COLOUR_WEIGHTED)
        if self._colour_mode != COLOUR_WEIGHTED:
            self._colour_cdf = np.ones(1)                     # unused placeholder, keeps the kernel signature typed

    # ---------------------------------------------------------------- pedigree
    # parent / founder / birth return snapshots (new lists), not live views.
    @property
    def parent(self) -> list[int]:
        return self.ped[0, :self.n_ids].tolist()

    @property
    def founder(self) -> list[int]:
        return self.ped[1, :self.n_ids].tolist()

    @property
    def birth(self) -> list[int]:
        return self.ped[2, :self.n_ids].tolist()

    def _reserve(self, extra: int) -> None:
        if self.n_ids + extra > self.ped.shape[1]:
            grown = np.zeros((4, max(2 * self.ped.shape[1], self.n_ids + extra)), dtype=np.int64)
            grown[:, :self.n_ids] = self.ped[:, :self.n_ids]
            self.ped = grown

    # ---------------------------------------------------------------- agents
    def _new_id(self, parent: int) -> int:
        self._reserve(1)
        i = self.n_ids
        self.ped[:, i] = (parent, i if parent == EMPTY else self.ped[1, parent], self.tick,
                          0 if parent == EMPTY else self.ped[3, parent] + 1)
        self.n_ids += 1
        return i

    def _create_immigrant(self, cell: int) -> None:
        c = self.cfg
        self.agent[cell] = self._new_id(EMPTY)
        self.color[cell] = self.rng.integers(c["n_colors"])
        self.cs[cell] = self.rng.random() < c["immigrant_chance_cooperate_with_same"]
        self.cd[cell] = self.rng.random() < c["immigrant_chance_cooperate_with_different"]
        self.ptr[cell] = c["initial_ptr"]

    def _kernel_args(self) -> tuple:
        c = self.cfg
        return (self.agent, self.color, self.cs, self.cd, self.ptr, self.ped, self.n_ids, self.tick,
                self._colour_mode, self._colour_cdf, int(c["n_colors"]), self._mut)

    def _hatch(self, parent_cell: int, cell: int) -> None:
        """Child of the agent in parent_cell into cell (copies colour, strategy and PTR, then mutates)."""
        self._reserve(1)
        self.n_ids = _hatch_nb(self.rng, parent_cell, cell, *self._kernel_args())

    # ---------------------------------------------------------------- one tick
    def _in_last100(self) -> bool:
        return self.tick >= self.cfg["ticks"] - 100

    def step(self) -> None:
        self._immigrate()
        self.ptr[self.agent != EMPTY] = self.cfg["initial_ptr"]
        if self._in_last100():
            self._interaction_kinship()
        self._interact()
        self._reproduce()
        self._death()
        if self._shuffle_f > 0:
            self._shuffle()
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

    def _shuffle(self) -> None:
        """Select each occupied cell with prob. f (one draw per occupied cell, in cell order), then permute the
        agents among the selected cells (one rng.permutation(k), also for k = 0 or 1)."""
        occ = np.flatnonzero(self.agent != EMPTY)
        sel = occ[self.rng.random(occ.size) < self._shuffle_f]
        src = sel[self.rng.permutation(sel.size)]
        for arr in (self.agent, self.color, self.cs, self.cd, self.ptr):
            arr[sel] = arr[src]

    def _interaction_kinship(self) -> None:
        """Unordered occupied neighbour pairs now: how many share a founder, against random mixing of the living."""
        occ = self.agent != EMPTY
        k = self.ikin
        k["ticks"] += 1
        A = np.concatenate([np.flatnonzero(occ & occ[self.nbr[:, d]]) for d in (1, 2)])
        B = np.concatenate([self.nbr[:, d][occ & occ[self.nbr[:, d]]] for d in (1, 2)])
        if A.size == 0:
            return
        founder = self.ped[1]
        f_live = founder[self.agent[occ]]
        n = np.bincount(f_live).astype(float)
        N = float(f_live.size)
        expected = float((n * (n - 1)).sum() / (N * (N - 1)))     # N >= 2, since there is at least one pair
        k["pairs"] += int(A.size)
        k["same_founder"] += int((founder[self.agent[A]] == founder[self.agent[B]]).sum())
        k["expected_weighted"] += expected * A.size
        k["ticks_with_pairs"] += 1

    def _interact(self) -> None:
        """Donor = cell, recipient = its neighbour; PTR is only written here, so order does not matter."""
        counts = np.zeros(6, dtype=np.int64)
        by_code = np.zeros((4, 2), dtype=np.int64)
        _interact_nb(self.agent, self.color, self.cs, self.cd, self.ptr, self.nbr,
                     self._cost, self._gain, counts, by_code)
        if self._in_last100():
            self.by_code += by_code
        t = dict(zip(("meet", "meetown", "meetother", "coopown", "coopother", "defother"), counts.tolist()))
        self.turn = t
        for key, v in t.items():
            self.agg[key] += v

    def _reproduce(self) -> None:
        """Agents alive now, in random order; children are placed at once but do not reproduce this tick."""
        rng, agent = self.rng, self.agent
        order = rng.permutation(np.flatnonzero(agent != EMPTY))
        lucky = order[rng.random(order.size) < self.ptr[order]]   # the per-agent draw NetLogo makes, in order
        self._reserve(lucky.size)
        self.n_ids, n_disp = _reproduce_nb(rng, lucky, self._dispersal, self.nbr,
                                           *self._kernel_args())
        self.n_dispersed += n_disp

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
                "population": int((self.agent != EMPTY).sum()), "births_total": self.n_ids,  # incl. immigrants
                "offspring_total": int((self.ped[0, :self.n_ids] != EMPTY).sum()), "dispersed_total": self.n_dispersed,
                "last100_meetings": int(sum(self.win["meet"])),
                "last100_agent_ticks": int(sum(sum(self.win[c]) for c in ("cc", "cd", "dc", "dd"))),
                "last100_egoist_ticks": int(sum(self.win["dd"])),
                "last100_meetings_by_code": self.by_code.tolist(),   # [code][meetings, own-colour meetings]
                "interaction_kinship": dict(self.ikin)}

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
        founder = self.ped[1, :self.n_ids]
        out["n_founders_alive"] = int(np.unique(founder[self.agent[cells]]).size)
        if A.size == 0:
            return out
        same_col = self.color[A] == self.color[B]
        ida, idb = self.agent[A], self.agent[B]
        same_f = founder[ida] == founder[idb]
        gen = np.full(A.size, -1, dtype=np.int64)
        tm = np.full(A.size, -1, dtype=np.int64)
        _mrca_nb(ida, idb, np.flatnonzero(same_f), self.ped[0], self.ped[3], self.ped[2], self.tick, gen, tm)
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
