#!/usr/bin/env python3
"""Mitteldorf and Wilson (2000) as a kin-selection test (pre-registration ../PREREG_KIN_TEST.md).

Stage S (demographic screen) -> choice written -> Stage M (test, control, references) -> mechanical classification.
The model's dynamics are the unchanged `AltruismModel`; this file adds (a) founder-id bookkeeping on a separate random
stream that does not touch the model's stream, and (b) the control's occupied-only shuffle on its own stream.

Run from the repo root:
  ./.conda/bin/python -m ecological_models.spatial_altruism.utils.run_kin_test
"""
from __future__ import annotations

import json
import math
import os
import subprocess
from fractions import Fraction
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if not __package__:
    raise SystemExit("Run with ./.conda/bin/python -m ecological_models.spatial_altruism.utils.run_kin_test")

from ..altruism_model import BLACK, GREEN, PINK, AltruismModel, make_params

OUT = Path("ecological_models/spatial_altruism/data/kin_test")
B, C, DISEASE = 0.468, 0.156, 0.213
STEPS = 1000
S_HARSH = [0.96, 0.9, 0.8, 0.7, 0.6, 0.5]
S_SEEDS = list(range(500, 510))
M_SEEDS = list(range(100, 150))
OCC0 = 0.78
LATE = (900, 1000)            # history indices for steps 901-1000
MID = (400, 500)              # steps 401-500
WORKERS = 8
BK_OFFSET, SHUFFLE_OFFSET = 7_000_000, 8_000_000


def shifts(x):
    """Self and the 4 neighbours, in the same order as the model's np.roll neighbourhood (torus)."""
    return np.stack([x, np.roll(x, -1, 0), np.roll(x, 1, 0), np.roll(x, -1, 1), np.roll(x, 1, 1)])


class KinTestModel(AltruismModel):
    def __init__(self, params, shuffle: bool = False):
        self.shuffle = shuffle
        seed = int(params.seed)
        self.rng_bk = np.random.default_rng(seed + BK_OFFSET)
        self.rng_shuffle = np.random.default_rng(seed + SHUFFLE_OFFSET)
        super().__init__(params)
        self.founder = np.full(self.pcolor.shape, -1, dtype=np.int64)
        occ = self.pcolor != BLACK
        self.founder[occ] = np.arange(int(occ.sum()))
        self.births_into_empty = 0
        self.last_births = 0
        self.pre_help_sharing = (None, None)

    def _shuffle_occupants(self):
        occ = np.flatnonzero((self.pcolor != BLACK).ravel())
        if occ.size < 2:
            return
        perm = occ[self.rng_shuffle.permutation(occ.size)]
        for arr in (self.pcolor, self.benefit_out, self.founder):
            flat = arr.reshape(-1)
            flat[occ] = flat[perm].copy()

    def go(self):
        if np.all((self.pcolor != PINK) & (self.pcolor != GREEN)):
            return False
        if self.shuffle:
            self._shuffle_occupants()
        self.pre_help_sharing = founder_sharing(self)          # founder clustering at the point help acts
        self._compute_altruism_benefit()
        self._perform_fitness_check()
        prev_color, prev_fit, prev_founder = self.pcolor.copy(), self.fitness.copy(), self.founder.copy()
        self._lottery()
        self._assign_founders(prev_color, prev_fit, prev_founder)
        self.last_births = int(((prev_color == BLACK) & (self.pcolor != BLACK)).sum())
        self.births_into_empty += self.last_births
        self.ticks += 1
        self._apply_disturbance_if_due()
        return True

    def _assign_founders(self, prev_color, prev_fit, prev_founder):
        """Parent drawn among the won type's candidates (self + 4 neighbours) in proportion to fitness."""
        ct, cf, cfo = shifts(prev_color), shifts(prev_fit), shifts(prev_founder)
        u = self.rng_bk.random(self.pcolor.shape)            # always drawn: constant stream use
        new = np.full(self.pcolor.shape, -1, dtype=np.int64)
        for typ in (PINK, GREEN):
            won = self.pcolor == typ
            if not won.any():
                continue
            w = np.where(ct == typ, cf, 0.0).astype(np.float64)
            k = choose_index(w, u)
            pick = np.take_along_axis(cfo, k[None], axis=0)[0]
            new[won] = pick[won]
        self.founder = new


def choose_index(w: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Per site, the first candidate whose cumulative weight is strictly above u * total (w: (5, H, W) >= 0)."""
    cum = np.cumsum(w, axis=0)
    x = u * cum[-1]
    return (cum <= x[None]).sum(axis=0).clip(0, w.shape[0] - 1)


def founder_sharing(m):
    """Share of occupied neighbour pairs (each edge once) with the same founder, and the random-mixing expectation."""
    occ = m.pcolor != BLACK
    f = m.founder
    same = n = 0
    for ax in (0, 1):
        nb_occ = np.roll(occ, -1, ax)
        both = occ & nb_occ
        same += int((both & (f == np.roll(f, -1, ax))).sum())
        n += int(both.sum())
    N = int(occ.sum())
    if n == 0 or N < 2:
        return None, None
    _, cnt = np.unique(f[occ], return_counts=True)
    expected = float((cnt * (cnt - 1)).sum() / (N * (N - 1)))
    return same / n, expected


def run(job):
    kind, harsh, disease, b, alt_p, self_p, seed, shuffle = job
    p = make_params({"seed": seed, "altruistic_probability": alt_p, "selfish_probability": self_p,
                     "benefit_from_altruism": b, "cost_of_altruism": C, "harshness": harsh, "disease": disease,
                     "model_variant": "steady_state"})
    m = KinTestModel(p, shuffle=shuffle)
    assert m.pcolor.shape == (51, 51) and m.p.torus, "registered geometry: 51 x 51 torus"
    a0, s0, e0 = m.counts()
    H, W = m.pcolor.shape
    alt0 = m.pcolor == PINK
    init_clust = float((alt0 & (shifts(m.pcolor)[1:] == PINK).any(axis=0)).sum() / max(1, alt0.sum()))
    hist, births, traj, extinct_at = [], [], [], None
    for t in range(STEPS):
        if not m.go():                        # only if the grid was already empty before this step
            extinct_at = t
            break
        a, s, e = m.counts()
        hist.append((a, s, e))
        births.append(m.last_births)
        if a + s == 0:                        # the step that emptied the grid
            extinct_at = t + 1
            break
        if (t + 1) % 50 == 0:
            occ = a + s
            traj.append({"step": t + 1, "alt_share": a / occ if occ else None, "occupied": occ / (H * W)})
    n = H * W
    def window(lo, hi):
        h = hist[lo:hi]
        if len(h) < hi - lo:
            return None, None
        occ = Fraction(sum(a + s for a, s, e in h), n * len(h))          # exact, for the registered cutoffs
        sh = [a / (a + s) for a, s, e in h if a + s > 0]
        return occ, (math.fsum(sh) / len(sh) if len(sh) == len(h) else None)
    late_occ, late_share = window(*LATE)
    mid_occ, _ = window(*MID)
    fs, fe = founder_sharing(m) if extinct_at is None else (None, None)
    pfs, pfe = m.pre_help_sharing if extinct_at is None else (None, None)
    late_births = sum(births[LATE[0]:LATE[1]]) if len(births) >= LATE[1] else None
    return {"kind": kind, "harshness": harsh, "disease": disease, "b": b, "c": C, "alt_p": alt_p, "self_p": self_p,
            "seed": seed, "shuffle": int(shuffle), "steps_done": len(hist), "extinct_at": extinct_at,
            "init_alt": a0, "init_self": s0, "init_alt_clustered_share": init_clust,
            "late_occupied_exact": [late_occ.numerator, late_occ.denominator] if late_occ is not None else None,
            "mid_occupied_exact": [mid_occ.numerator, mid_occ.denominator] if mid_occ is not None else None,
            "late_occupied": float(late_occ) if late_occ is not None else None, "late_alt_share": late_share,
            "mid_occupied": float(mid_occ) if mid_occ is not None else None,
            "births_into_empty_late": late_births, "births_into_empty_total": m.births_into_empty,
            "founder_sharing_post_lottery": fs, "founder_sharing_random": fe,
            "founder_sharing_pre_help": pfs, "founder_sharing_pre_help_random": pfe,
            "traj": traj}


def frac(r, key):
    v = r.get(key + "_exact")
    return Fraction(v[0], v[1]) if v else None


def s_passes(r):
    lo, mid = frac(r, "late_occupied"), frac(r, "mid_occupied")
    return (r["extinct_at"] is None and lo is not None and Fraction(1, 10) <= lo <= Fraction(95, 100)
            and mid is not None and lo >= Fraction(8, 10) * mid)


def s_reason(r):
    if r["extinct_at"] is not None:
        return f"extinct at {r['extinct_at']}"
    if not Fraction(1, 10) <= frac(r, "late_occupied") <= Fraction(95, 100):
        return f"late occupancy {r['late_occupied']:.3f} outside [0.10, 0.95]"
    if frac(r, "late_occupied") < Fraction(8, 10) * frac(r, "mid_occupied"):
        return f"decline {r['mid_occupied']:.3f} -> {r['late_occupied']:.3f}"
    return "ok"


def viable(r):
    lo = frac(r, "late_occupied")
    return r["extinct_at"] is None and lo is not None and lo >= Fraction(1, 10)


def success(r):
    return (viable(r) and frac(r, "late_occupied") <= Fraction(95, 100) and r["late_alt_share"] is not None
            and r["late_alt_share"] >= 0.60)


def classify(T, X):
    vt, vx = sum(map(viable, T)), sum(map(viable, X))
    st, sx = sum(map(success, T)), sum(map(success, X))
    if vt < 40 or vx < 40:
        cls = "not a valid test"
    elif st < 30:
        cls = "local failure"
    elif sx > 10 or st - sx < 20:
        cls = "comparison failed"
    else:
        cls = "met"
    return {"class": cls, "T_viable": vt, "X_viable": vx, "T_successes": st, "X_successes": sx}


def summary(rows):
    def m(k):
        v = [r[k] for r in rows if r[k] is not None]
        return float(np.mean(v)) if v else None
    return {"n": len(rows), "viable": sum(map(viable, rows)), "successes": sum(map(success, rows)),
            "extinct": sum(r["extinct_at"] is not None for r in rows), "late_alt_share": m("late_alt_share"),
            "late_occupied": m("late_occupied"), "founder_sharing_post_lottery": m("founder_sharing_post_lottery"),
            "founder_sharing_random": m("founder_sharing_random"),
            "founder_sharing_pre_help": m("founder_sharing_pre_help"),
            "founder_sharing_pre_help_random": m("founder_sharing_pre_help_random"),
            "births_into_empty_late": m("births_into_empty_late"),
            "init_alt_clustered_share": m("init_alt_clustered_share")}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()):
        raise SystemExit(f"{OUT} is not empty; refusing to overwrite a registered run.")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "ecological_models/spatial_altruism",
                            ":(exclude)ecological_models/spatial_altruism/data"],
                           capture_output=True, text=True).stdout.strip()
    with Pool(WORKERS) as pool:
        sjobs = [("S", h, DISEASE, B, ap, sp, s, False) for h in S_HARSH for (ap, sp) in ((OCC0, 0.0), (0.0, OCC0))
                 for s in S_SEEDS]
        srows = pool.map(run, sjobs)
        points = []
        for h in S_HARSH:
            rr = [r for r in srows if r["harshness"] == h]
            points.append({"harshness": h, "passes": all(map(s_passes, rr)),
                           "reasons": {("altruists" if r["alt_p"] > 0 else "selfish") + f"_seed{r['seed']}": s_reason(r)
                                       for r in rr}})
        passing = [q["harshness"] for q in points if q["passes"]]
        chosen = max(passing) if passing else None
        (OUT / "stage_s.json").write_text(json.dumps({"points": points, "chosen_harshness": chosen,
                                                       "runs": srows}, indent=1))
        print("Stage S chosen harshness:", chosen, flush=True)
        verdict = {"git_commit": commit, "tree_clean": dirty == "", "stage_s_chosen": chosen,
                   "stage_s_paper_point_passes": next(q["passes"] for q in points if q["harshness"] == 0.96)}
        # descriptive: the demo setting (harshness 0.96) from the rare start, whatever Stage S chose.
        # The keys "stage_s_paper_point_passes" and "paper_point_rare_start" keep their original names for the
        # recorded data; 0.96 is the repo's demo setting, not the paper's (erratum in RESULTS_KIN_TEST.md).
        pjobs = [("P", 0.96, DISEASE, B, 0.05, 0.73, s, False) for s in M_SEEDS]
        if chosen is None:
            prow = pool.map(run, pjobs)
            verdict["class"] = "stopped: no screened point qualified"
            verdict["paper_point_rare_start"] = summary(prow)
            (OUT / "stage_m_runs.json").write_text(json.dumps(prow, indent=1))
        else:
            mjobs = ([("T", chosen, DISEASE, B, 0.05, 0.73, s, False) for s in M_SEEDS] +
                     [("X", chosen, DISEASE, B, 0.05, 0.73, s, True) for s in M_SEEDS] +
                     [("D", 0.0, 0.0, B, 0.05, 0.73, s, False) for s in M_SEEDS] +
                     [("W", chosen, DISEASE, 1.0, 0.05, 0.73, s, False) for s in M_SEEDS] + pjobs)
            mrows = pool.map(run, mjobs)
            (OUT / "stage_m_runs.json").write_text(json.dumps(mrows, indent=1))
            arms = {k: [r for r in mrows if r["kind"] == k] for k in "TXDWP"}
            verdict.update(classify(arms["T"], arms["X"]))
            verdict["arms"] = {k: summary(v) for k, v in arms.items()}
            verdict["paired_T_minus_X_late_alt_share"] = float(np.mean(
                [a["late_alt_share"] - b["late_alt_share"] for a, b in zip(arms["T"], arms["X"])
                 if a["late_alt_share"] is not None and b["late_alt_share"] is not None] or [np.nan]))
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    main()
