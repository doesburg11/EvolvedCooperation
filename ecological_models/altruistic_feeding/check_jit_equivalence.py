#!/usr/bin/env python3
"""Check that the replication patch's JIT gives the same trajectory as the authors' eager execution.

Runs the paper configuration twice for N steps from the same seed, once with `step_eco_loop` jitted and once eager
(ECOJAX_NO_JIT=1, in a subprocess), recording per step the agents' existence, positions, orientations, energies and
ages, and the plant map. Prints the first step at which they differ (or that they agree for all N steps).

  ~/simulation_results/altruistic_feeding/venv_050/bin/python check_jit_equivalence.py --steps 300
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np


def record(steps: int, out: str, level: float, seed: int) -> None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import run_feeding as rf
    from jax import random
    cfg = rf.make_config(level, seed, True, steps, tempfile.mkdtemp())
    np.random.seed(seed)
    key = random.PRNGKey(seed)
    env = rf.env_name_to_EnvClass[cfg["env"]["name"]](config=cfg["env"], n_agents_max=cfg["n_agents_max"],
                                                      n_agents_initial=cfg["n_agents_initial"])
    sp = rf.agent_name_to_AgentSpeciesClass[cfg["agents"]["name"]](
        config=cfg["agents"], n_agents_max=cfg["n_agents_max"], n_agents_initial=cfg["n_agents_initial"],
        observation_space=env.get_observation_space(), action_space=env.get_action_space(),
        model_class=rf.model_name_to_ModelClass[cfg["model"]["name"]], config_model=cfg["model"])
    env.agent_species, sp.env = sp, env
    rows = {"existing": [], "positions": [], "orientation": [], "energy": [], "age": [], "plants": [],
            "feeders": [], "feedees": [], "life_expectancy": [], "newborns": [], "parents": []}

    def cb(t, prev, new, info):
        a = new.state_env.agents
        rows["existing"].append(np.asarray(a.are_existing_agents))
        rows["positions"].append(np.asarray(a.positions_agents))
        rows["orientation"].append(np.asarray(a.orientation_agents))
        rows["energy"].append(np.asarray(a.energy_agents))
        rows["age"].append(np.asarray(a.age_agents))
        rows["plants"].append(np.asarray(new.state_env.map[:, :, env.dict_name_channel_to_idx["plants"]]))
        m = info["metrics"]
        rows["feeders"].append(np.nan_to_num(np.asarray(m["feeders"], dtype=float), nan=-1))
        rows["feedees"].append(np.nan_to_num(np.asarray(m["feedees"], dtype=float), nan=-1))
        rows["life_expectancy"].append(np.nan_to_num(np.asarray(m["life_expectancy"], dtype=float), nan=-1))
        rows["newborns"].append(np.asarray(new.eco_information.are_newborns_agents))
        rows["parents"].append(np.asarray(new.eco_information.indexes_parents).reshape(-1))

    key, sub = random.split(key)
    rf.eco_loop(env=env, agent_species=sp, config=cfg, key_random=sub, step_callback=cb)
    np.savez_compressed(out, **{k: np.stack(v) for k, v in rows.items()})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--level", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--record", default=None)
    a = ap.parse_args()
    if a.record:
        record(a.steps, a.record, a.level, a.seed)
        return
    d = tempfile.mkdtemp()
    paths = {}
    for mode in ("jit", "eager"):
        envv = dict(os.environ)
        envv.pop("ECOJAX_NO_JIT", None)
        if mode == "eager":
            envv["ECOJAX_NO_JIT"] = "1"
        paths[mode] = os.path.join(d, f"{mode}.npz")
        subprocess.run([sys.executable, __file__, "--steps", str(a.steps), "--level", str(a.level), "--seed",
                        str(a.seed), "--record", paths[mode]], env=envv, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    j, e = np.load(paths["jit"]), np.load(paths["eager"])
    first = None
    for k in j.files:
        if len(j[k]) != a.steps or len(e[k]) != a.steps:
            print(f"{k}: trace lengths {len(j[k])} (jit) / {len(e[k])} (eager), expected {a.steps}")
            sys.exit(2)
        exact = [np.array_equal(x, y) for x, y in zip(j[k], e[k])]
        if not all(exact):
            s = exact.index(False)
            first = s if first is None else min(first, s)
            close = np.allclose(j[k][s], e[k][s], atol=1e-5) if j[k].dtype.kind == "f" else False
            print(f"{k}: first difference at step {s} (allclose 1e-5 there: {close})")
        else:
            print(f"{k}: identical for all {len(exact)} steps")
    print("RESULT:", "identical" if first is None else f"diverges at step {first}")
    sys.exit(0 if first is None else 1)


if __name__ == "__main__":
    main()
