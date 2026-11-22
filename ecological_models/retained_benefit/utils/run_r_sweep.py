"""Retained-fraction sweep (pre-registered 2026-11-22; see the module README, "Pre-registration: retained-fraction sweep").

Runs every cell of the registered grid from the frozen website-demo configuration, changing only
`retained_benefit_fraction`, `cooperation_benefit`, `cooperation_cost`, `simulation_steps` and `random_seed`.
No CLI: the design is fixed in the constants below.

Run from the repository root:

    ./.conda/bin/python -m ecological_models.retained_benefit.utils.run_r_sweep

Writes `ecological_models/retained_benefit/data/r_sweep/runs.csv` (one row per run) and
`trajectories.csv` (every TRAJECTORY_INTERVAL steps), then a `manifest.json`.
"""

from __future__ import annotations

import os

# One numerical thread per process; set before NumPy is imported (amendment A1).
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_var] = "1"

import csv  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

if not __package__:
    raise SystemExit(
        "Run from the repo root with "
        "'./.conda/bin/python -m ecological_models.retained_benefit.utils.run_r_sweep'."
    )

from ..config.retained_benefit_website_demo_config import config as DEMO_CONFIG  # noqa: E402
from ..retained_benefit_model import RetainedBenefitModel, make_settings  # noqa: E402
from .export_github_pages_demo import _round_number  # noqa: E402

# ---------------------------------------------------------------- registered design
R_LEVELS = [round(0.1 * i, 1) for i in range(11)]  # 0.0, 0.1, ..., 1.0
COST = 0.10
BC_RATIOS = [3, 5, 8]  # benefit = ratio * COST
SEEDS = list(range(10))
STEPS = 1000
TAIL_STEPS = 100  # outcome: mean cooperation averaged over the last TAIL_STEPS recorded steps
TRAJECTORY_INTERVAL = 50
WORKERS = 5
NICE = 10
OUT_DIR = Path("ecological_models/retained_benefit/data/r_sweep")


def build_arms() -> list[dict]:
    """All registered arms: the 3 x 11 sweep plus one neutral control (b = c = 0)."""
    arms = []
    for ratio in BC_RATIOS:
        for r in R_LEVELS:
            arms.append({"arm": f"bc{ratio}_r{r:.1f}", "bc": ratio, "r": r,
                         "benefit": round(ratio * COST, 10), "cost": COST})
    # r is irrelevant without benefit; 0.35 keeps the demo value.
    arms.append({"arm": "neutral", "bc": 0, "r": 0.35, "benefit": 0.0, "cost": 0.0})
    return arms


def run_config(arm: dict, seed: int, steps: int) -> dict:
    cfg = dict(DEMO_CONFIG)
    cfg.update({
        "retained_benefit_fraction": arm["r"],
        "cooperation_benefit": arm["benefit"],
        "cooperation_cost": arm["cost"],
        "simulation_steps": steps,
        "random_seed": seed,
        "write_log": False,
        "show_matplotlib_plots": False,
        "summary_interval_steps": 0,
    })
    return cfg


def simulate(cfg: dict) -> dict[str, list[float]]:
    """Step the model exactly as `RetainedBenefitModel.run` does, without its logging side effects."""
    model = RetainedBenefitModel(make_settings(cfg))
    for _ in range(model.settings.simulation_steps):
        model.step()
    return model.history


def summarize(arm: dict, seed: int, history: dict[str, list[float]], seconds: float) -> tuple[dict, list[dict]]:
    coop = history["mean_cooperation"]
    tail = coop[-TAIL_STEPS:]
    row = {
        "arm": arm["arm"], "bc": arm["bc"], "r": arm["r"], "benefit": arm["benefit"], "cost": arm["cost"],
        "seed": seed, "steps": len(coop) - 1,
        "initial_mean_cooperation": coop[0],
        "final_mean_cooperation": coop[-1],
        "tail_mean_cooperation": sum(tail) / len(tail),
        "final_var_cooperation": history["var_cooperation"][-1],
        "final_local_assortment": history["local_assortment"][-1],
        "final_dominant_lineage_share": history["dominant_lineage_share"][-1],
        "final_lineage_count": history["lineage_count"][-1],
        "seconds": round(seconds, 2),
    }
    traj = []
    for i, step in enumerate(history["step"]):
        if int(step) % TRAJECTORY_INTERVAL == 0:
            traj.append({"arm": arm["arm"], "seed": seed, "step": int(step),
                         "mean_cooperation": history["mean_cooperation"][i],
                         "var_cooperation": history["var_cooperation"][i],
                         "local_assortment": history["local_assortment"][i],
                         "dominant_lineage_share": history["dominant_lineage_share"][i]})
    return row, traj


def _job(args: tuple[dict, int]) -> tuple[dict, list[dict]]:
    arm, seed = args
    t0 = time.perf_counter()
    history = simulate(run_config(arm, seed, STEPS))
    return summarize(arm, seed, history, time.perf_counter() - t0)


def replay_check(history: dict[str, list[float]] | None = None,
                 published_path: str = "docs/data/retained-benefit-demo/summary.json") -> dict:
    """Validity check: the demo arm, run for the demo's 250 steps, must reproduce the published replay exactly at
    the exporter's own precision (`export_github_pages_demo._round_number`), with the same step sequence."""
    pub = json.load(open(published_path))
    if history is None:
        history = simulate(dict(DEMO_CONFIG))
    keys = ["mean_cooperation", "local_assortment", "dominant_lineage_share"]
    steps_ok = [int(v) for v in history["step"]] == pub["step_hist"] == list(range(DEMO_CONFIG["simulation_steps"] + 1))
    values_ok = all([_round_number(v) for v in history[k]] == pub[k + "_hist"] for k in keys)
    return {"replay_exact": bool(steps_ok and values_ok), "steps_match": bool(steps_ok),
            "values_match": bool(values_ok), "steps": len(history["mean_cooperation"]) - 1}


def set_niceness(target: int = NICE) -> int:
    """Raise this process's niceness to `target` (absolute, not added); workers inherit it."""
    current = os.nice(0)
    if current < target:
        current = os.nice(target - current)
    return current


def run_sweep(out_dir: Path, arms: list[dict], seeds: list[int], workers: int = WORKERS) -> dict:
    """Run all jobs and publish the bundle atomically: written to `<out_dir>.partial`, renamed when complete."""
    if out_dir.exists():
        raise SystemExit(f"{out_dir} exists; refusing to overwrite a registered run.")
    partial = out_dir.with_name(out_dir.name + ".partial")
    partial.parent.mkdir(parents=True, exist_ok=True)
    try:
        partial.mkdir()  # exclusive: fails if another run is in progress or a stale partial bundle exists
    except FileExistsError:
        raise SystemExit(f"{partial} exists: another run may be in progress, or a failed run left it. "
                         "Check and remove it by hand before rerunning.") from None

    check = replay_check()
    print("replay check:", check)
    if not check["replay_exact"]:
        shutil.rmtree(partial)
        raise SystemExit("Replay check failed: the demo arm does not reproduce the published replay. Not running.")

    niceness = set_niceness()
    jobs = [(arm, seed) for arm in arms for seed in seeds]
    started = time.time()
    rows, trajs = [], []
    with Pool(workers) as pool:
        for i, (row, traj) in enumerate(pool.imap_unordered(_job, jobs), 1):
            rows.append(row)
            trajs.extend(traj)
            if i % 20 == 0 or i == len(jobs):
                elapsed = time.time() - started
                print(f"{i}/{len(jobs)} runs, {elapsed / 60:.1f} min, projected total "
                      f"{elapsed / i * len(jobs) / 60:.0f} min", flush=True)

    rows.sort(key=lambda x: (x["arm"], x["seed"]))
    trajs.sort(key=lambda x: (x["arm"], x["seed"], x["step"]))
    for name, data in (("runs.csv", rows), ("trajectories.csv", trajs)):
        with open(partial / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "ecological_models/retained_benefit"],
                           capture_output=True, text=True).stdout.strip()
    manifest = {"design": {"r_levels": R_LEVELS, "bc_ratios": BC_RATIOS, "cost": COST, "seeds": seeds,
                           "steps": STEPS, "tail_steps": TAIL_STEPS, "arms": [a["arm"] for a in arms]},
                "replay_check": check, "n_runs": len(rows), "git_commit": commit,
                "module_tree_clean": dirty == "", "niceness": niceness,
                "workers": workers, "wall_seconds": round(time.time() - started, 1)}
    (partial / "manifest.json").write_text(json.dumps(manifest, indent=2))
    partial.rename(out_dir)
    print("done:", manifest["n_runs"], "runs,", manifest["wall_seconds"], "s")
    return manifest


def main() -> None:
    run_sweep(OUT_DIR, build_arms(), SEEDS)


if __name__ == "__main__":
    main()
