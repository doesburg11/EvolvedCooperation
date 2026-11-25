#!/usr/bin/env python3
"""One run of the Taylor-Davies et al. (2024) altruistic-feeding model, with the registered measures
(PREREGISTRATION_DRAFT.md, "Measures (registered)").

Uses the authors' code (external/EcoJAX at 24524cc + patches/ecojax_24524cc.patch: JIT re-enabled, a per-step callback,
the authors' own logger bypassed when the callback is used). The model itself is unchanged. Measures are computed
here with unique agent ids, because the authors' parent bookkeeping uses reusable agent slots.

Run with the replication environment (JAX 0.5.0, flax 0.10.2):
  ~/simulation_results/altruistic_feeding/venv_050/bin/python run_feeding.py --level 0.5 --seed 0 --feeding 1 \
      --steps 250000 --window 25000 --out results/
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

ECOJAX = Path(__file__).resolve().parents[2] / "external" / "EcoJAX"
sys.path.insert(0, str(ECOJAX))
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402
from hydra import compose, initialize_config_dir  # noqa: E402
from jax import random  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402

from ecojax.agents import agent_name_to_AgentSpeciesClass  # noqa: E402
from ecojax.core.eco_loop import eco_loop  # noqa: E402
from ecojax.environment import env_name_to_EnvClass  # noqa: E402
from ecojax.models import model_name_to_ModelClass  # noqa: E402
from ecojax.register_hydra import register_hydra_resolvers  # noqa: E402

INFANCY = 100
N_MAX = 2500

# Paper's stated values (Section 2.1); other parameters at the code defaults (PREREGISTRATION_DRAFT.md, A0).
PAPER_OVERRIDES = [
    "env.energy_initial=65",
    "env.energy_loss_idle=0.1",          # 0.1 passively per step ...
    "env.energy_loss_action=1.1",        # ... plus 1.0 per non-idle action (transfer is exempt in the code)
    "env.energy_food=20",
    "env.energy_max=200",
    "env.energy_req_reprod=85",          # the code tests strictly '>' (paper: 'at or above')
    "env.energy_cost_reprod=30",
    "env.energy_transfer_loss=20",
    "env.energy_transfer_gain=20",
    "env.infancy_duration=100",
    "env.proportion_plant_initial=0.1",
    "env.p_base_plant_growth=0.003",
    "env.p_base_plant_death=0.0",
    "env.allow_multiple_agents_per_tile=False",
    "n_agents_max=2500",
    "n_agents_initial=2000",
    "agents.hp_initial.strength_mutation=0.02",
]


def make_config(level: float, seed: int, feeding: bool, steps: int, out_dir: str) -> dict:
    register_hydra_resolvers()
    actions = "[forward,right,left,eat,reproduce,transfer,idle]" if feeding else "[forward,right,left,eat,reproduce,idle]"
    over = PAPER_OVERRIDES + [
        f"+env.infant_move_prob={level}", "+env.infant_eat_prob=1.0", "+env.infant_food_energy_mult=1.0",
        f"env.list_actions={actions}", f"n_timesteps={steps}", f"+seed={seed}",
        "do_render=False", "do_tqdm=False", "do_csv=False", "do_tb=False", "do_wandb=False",
        f"log_dir_path={out_dir}", "do_global_log=True",
    ]
    with initialize_config_dir(config_dir=str(ECOJAX / "configs"), version_base=None):
        cfg = compose(config_name="default.yaml", overrides=over)
    cfg = OmegaConf.to_container(cfg, resolve=True)
    cfg["run_name"] = f"move{level}_seed{seed}_feed{int(feeding)}"
    cfg["env"]["metrics"]["config_video"]["dir_videos"] = os.path.join(out_dir, "videos")
    return cfg


class Measurer:
    """Registered measures over the window, with unique agent ids from `track_start` on."""

    def __init__(self, env, steps: int, window: int, feeding: bool):
        self.env, self.feeding = env, feeding
        self.win_start = steps - window
        self.track_start = max(0, self.win_start - 1000)    # every agent alive in the window is born after this
        self.uid = np.full(N_MAX, -1, dtype=np.int64)        # -1: unknown (existed before tracking)
        self.parent_uid = np.full(N_MAX, -1, dtype=np.int64)
        self.next_uid = 0
        self.fed_infant = {}                                  # uid -> times fed while an infant
        self.c = dict(feeds=0, feeds_to_offspring=0, feeds_to_infants=0, facing_any=0, facing_offspring=0,
                      pop_sum=0, win_steps=0, cap_steps=0, infant_deaths=0, deaths=0, stale_flags=0,
                      feeds_env_offspring=0, run_cap_steps=0, run_steps=0, feed_count_mismatch=0)
        self.death_records = []                               # (lifespan, times fed as infant)
        self.extinct_at = None
        self._facing = jax.jit(self._facing_slots)

    def _facing_slots(self, state_env):
        ag = state_env.agents
        pos, ori, ex = ag.positions_agents, ag.orientation_agents, ag.are_existing_agents
        idx = jnp.arange(pos.shape[0])
        tgt = jax.vmap(self.env.get_facing_pos)(pos, ori)
        smap = jnp.full((self.env.height, self.env.width), -1, dtype=jnp.int32)
        smap = smap.at[pos[:, 0], pos[:, 1]].max(jnp.where(ex, idx, -1).astype(jnp.int32))
        faced = smap[tgt[:, 0], tgt[:, 1]]
        return jnp.where(ex, faced, -1)

    def __call__(self, t, prev, new, info):
        m = info["metrics"]
        n_now = int(m["n_agents"])                            # post-step population (scalar)
        self.c["run_steps"] += 1
        self.c["run_cap_steps"] += int(n_now >= N_MAX)
        if n_now == 0 and self.extinct_at is None:
            self.extinct_at = int(t) + 1
        if self.extinct_at is not None:
            return True                                       # stop the loop: an extinct population stays extinct
        if t < self.track_start:
            return
        ex_prev = np.asarray(prev.state_env.agents.are_existing_agents).astype(bool)
        age_prev = np.asarray(prev.state_env.agents.age_agents)
        # unknown-but-existing agents at tracking start get ids (their parents are unknown)
        unk = ex_prev & (self.uid < 0)
        if unk.any():
            n = int(unk.sum())
            self.uid[unk] = np.arange(self.next_uid, self.next_uid + n)
            self.next_uid += n
        in_win = t >= self.win_start
        # 1) feeds (pre-step agents)
        if self.feeding:
            feeders = np.flatnonzero(np.nan_to_num(np.asarray(m["feeders"], dtype=float)) > 0)
            if feeders.size != int(m["num_transfers"]):        # requires the unmasked feed arrays (patch)
                self.c["feed_count_mismatch"] += 1
            if feeders.size:
                feedees = np.asarray(m["feedees"])[feeders].astype(np.int64)
                for f, r in zip(feeders, feedees):
                    if age_prev[r] < INFANCY:
                        self.fed_infant[self.uid[r]] = self.fed_infant.get(self.uid[r], 0) + 1
                if in_win:
                    true_off = self.parent_uid[feedees] == self.uid[feeders]
                    env_off = np.nan_to_num(np.asarray(m["to_offspring"], dtype=float))[feeders] > 0
                    self.c["feeds"] += feeders.size
                    self.c["feeds_to_offspring"] += int(true_off.sum())
                    self.c["feeds_to_infants"] += int((age_prev[feedees] < INFANCY).sum())
                    self.c["feeds_env_offspring"] += int(env_off.sum())
                    self.c["stale_flags"] += int((env_off != true_off).sum())
            if in_win:
                faced = np.asarray(self._facing(prev.state_env))
                facers = np.flatnonzero(faced >= 0)
                self.c["facing_any"] += facers.size
                self.c["facing_offspring"] += int((self.parent_uid[faced[facers]] == self.uid[facers]).sum())
        # 2) deaths (pre-step ids)
        le = np.asarray(m["life_expectancy"], dtype=float)
        dead = np.flatnonzero(np.isfinite(le))
        if in_win and dead.size:
            for s in dead:
                self.death_records.append((float(le[s]), self.fed_infant.get(self.uid[s], 0)))
            self.c["deaths"] += dead.size
            self.c["infant_deaths"] += int((le[dead] < INFANCY).sum())
        for s in dead:
            self.uid[s] = -2                                  # dead; slot free
            self.parent_uid[s] = -1
        # 3) births (new ids)
        eco = new.eco_information
        newborn = np.flatnonzero(np.asarray(eco.are_newborns_agents).astype(bool))
        if newborn.size:
            parents = np.asarray(eco.indexes_parents).reshape(-1)[newborn].astype(np.int64)
            self.parent_uid[newborn] = np.where(parents >= 0, self.uid[np.clip(parents, 0, N_MAX - 1)], -1)
            self.uid[newborn] = np.arange(self.next_uid, self.next_uid + newborn.size)
            self.next_uid += newborn.size
        if in_win:
            self.c["pop_sum"] += int(ex_prev.sum())
            self.c["win_steps"] += 1
            self.c["cap_steps"] += int(ex_prev.sum() >= N_MAX)

    def results(self) -> dict:
        c = self.c
        out = dict(c)
        mean_pop = c["pop_sum"] / c["win_steps"] if c["win_steps"] else float("nan")
        out["mean_population"] = mean_pop
        out["cap_share"] = c["cap_steps"] / c["win_steps"] if c["win_steps"] else float("nan")
        out["ISR"] = 1 - c["infant_deaths"] / c["deaths"] if c["deaths"] else float("nan")
        if self.feeding:
            out["amount"] = c["feeds"] / mean_pop if mean_pop and mean_pop > 0 else float("nan")
            p_feed = c["feeds_to_offspring"] / c["feeds"] if c["feeds"] else float("nan")
            p_face = c["facing_offspring"] / c["facing_any"] if c["facing_any"] else float("nan")
            out["selectivity"] = p_feed - p_face
            out["stale_flag_share"] = c["stale_flags"] / c["feeds"] if c["feeds"] else float("nan")
            fed = [life for life, k in self.death_records if k > 0]
            unfed = [life for life, k in self.death_records if k == 0]
            out["n_deaths_fed_infant"], out["n_deaths_unfed"] = len(fed), len(unfed)
            out["b_hat_pct"] = (100 * (np.mean(fed) / np.mean(unfed) - 1)) if fed and unfed and np.mean(unfed) > 0 \
                else float("nan")
            # authors' estimator (sensitivity): equal weight per positive feed-count group
            groups = {}
            for life, k in self.death_records:
                groups.setdefault(k, []).append(life)
            if 0 in groups and len(groups) > 1 and np.mean(groups[0]) > 0:
                base = np.mean(groups[0])
                out["b_hat_pct_authors"] = 100 * float(np.mean([np.mean(v) / base - 1 for k, v in groups.items() if k > 0]))
            else:
                out["b_hat_pct_authors"] = float("nan")
        out["run_cap_share"] = c["run_cap_steps"] / c["run_steps"] if c["run_steps"] else float("nan")
        out["extinct_at"] = self.extinct_at
        return out


def run(level: float, seed: int, feeding: bool, steps: int, window: int, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    cfg = make_config(level, seed, feeding, steps, out_dir)
    np.random.seed(seed)
    key = random.PRNGKey(seed)
    env = env_name_to_EnvClass[cfg["env"]["name"]](config=cfg["env"], n_agents_max=cfg["n_agents_max"],
                                                   n_agents_initial=cfg["n_agents_initial"])
    species = agent_name_to_AgentSpeciesClass[cfg["agents"]["name"]](
        config=cfg["agents"], n_agents_max=cfg["n_agents_max"], n_agents_initial=cfg["n_agents_initial"],
        observation_space=env.get_observation_space(), action_space=env.get_action_space(),
        model_class=model_name_to_ModelClass[cfg["model"]["name"]], config_model=cfg["model"])
    env.agent_species, species.env = species, env
    meas = Measurer(env, steps, window, feeding)
    key, sub = random.split(key)
    t0 = time.time()
    eco_loop(env=env, agent_species=species, config=cfg, key_random=sub, step_callback=meas)
    res = {"level": level, "seed": seed, "feeding": int(feeding), "steps": steps, "window": window,
           "wall_seconds": round(time.time() - t0, 1), "overrides": PAPER_OVERRIDES, **meas.results()}
    res["complete"] = bool(res["extinct_at"] is not None or
                           (res["run_steps"] == steps and res["win_steps"] == window))
    res = {k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in res.items()}
    final = os.path.join(out_dir, f"result_move{level}_seed{seed}_feed{int(feeding)}.json")
    tmp = final + ".tmp"
    with open(tmp, "w") as f:
        json.dump(res, f, indent=1)
    os.replace(tmp, final)                                    # atomic: no truncated result files
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=float, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--feeding", type=int, choices=(0, 1), required=True)
    ap.add_argument("--steps", type=int, required=True)
    ap.add_argument("--window", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(json.dumps(run(a.level, a.seed, bool(a.feeding), a.steps, a.window, a.out), indent=1))
