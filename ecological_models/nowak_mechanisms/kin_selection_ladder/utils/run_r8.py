#!/usr/bin/env python3
"""Step R8 (README pre-registration 852cd06): per-run function shared by the Stage S screen and Stage M."""
from __future__ import annotations

import contextlib
import io

import numpy as np

from ..config.ladder_config import R8_STARTUP_STEPS, run_config
from ..ladder_model import make_engine
from .run_r1 import occupied_corr
from .run_step1 import corr_steps
from .run_steps01 import edge_pairs

SUM_KEYS = ("n_occ_start", "harvest_total", "n_fill_needed", "n_fill_emptied", "n_births", "n_claimants",
            "n_claims", "n_targets", "n_deaths", "n_starve_added", "n_draw_deaths", "births_low_h_sum", "n_low_h",
            "births_high_h_sum", "n_high_h")
MEAN_KEYS = ("G_mean", "G_juvenile", "G_parents", "S_mean", "D_mean", "S_juvenile", "D_juvenile", "S_parents",
             "D_parents", "death_mean", "frac_claimant", "starve_rate_recent_parents")       # per-update means


def run_one(job):
    """job = (arm, mech, updates, seed, steps, window_from). Window: start-of-update states after window_from, ...,
    steps - 1 completed updates."""
    arm, mech, updates, seed, steps, window_from = job
    mech = dict(mech)
    eng = make_engine(run_config(seed, updates, steps), replacement=mech.pop("replacement"),
                      death=mech.pop("death"), **mech)
    ei, ej = edge_pairs(eng)
    cs = corr_steps(steps)
    sums = {k: 0 for k in SUM_KEYS}
    means = {k: [] for k in MEAN_KEYS}
    window_states = 0
    traj, corr, startup, first_empty = [], [], {}, None
    with contextlib.redirect_stdout(io.StringIO()):
        while eng.step_index < steps:
            start = eng.step_index
            eng.step()
            t = eng.step_index
            if start >= window_from:
                window_states += 1
                for k in SUM_KEYS:
                    sums[k] += eng.last_diag[k]
                for k in MEAN_KEYS:
                    means[k].append(eng.last_diag[k])
            if first_empty is None and not eng.occ.any():
                first_empty = t
            if t in R8_STARTUP_STEPS:
                startup[f"occ_after_{t}"] = float(eng.occ.mean())
            if t % 50 == 0:
                traj.append(eng.occupied_mean_h())
            if t in cs:
                corr.append(occupied_corr(eng, ei, ej))
    final_occ = float(eng.occ.mean())
    row = {"arm": arm, "seed": seed, "steps_done": eng.step_index, "final_mean_trait": eng.occupied_mean_h(),
           "final_occupancy": final_occ, "extinct": int(not eng.occ.any()),
           "first_empty_update": -1 if first_empty is None else first_empty,
           "window_states": window_states, "site_steps": window_states * eng.n_sites,
           "occ_site_steps": int(sums["n_occ_start"]), "traj_every_50": traj, "neighbour_h_corr": corr,
           **{f"occ_after_{t}": startup.get(f"occ_after_{t}", float("nan")) for t in R8_STARTUP_STEPS}}
    row.update(sums)
    for k, v in means.items():
        a = np.asarray(v, dtype=float)
        row[k] = float(np.nanmean(a)) if a.size and np.isfinite(a).any() else float("nan")
    row["claims_per_target"] = sums["n_claims"] / sums["n_targets"] if sums["n_targets"] else float("nan")
    return row
