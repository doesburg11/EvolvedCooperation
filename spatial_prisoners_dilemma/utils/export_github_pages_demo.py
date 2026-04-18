#!/usr/bin/env python3
"""
Export a sampled replay bundle for the GitHub Pages spatial Prisoner's Dilemma demo.

Run from the repository root with:
  ./.conda/bin/python -m spatial_prisoners_dilemma.utils.export_github_pages_demo
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m spatial_prisoners_dilemma.utils.export_github_pages_demo'."
    )

from ..config.spatial_prisoners_dilemma_website_demo_config import (
    config as website_demo_config,
)
from ..spatial_prisoners_dilemma import (
    STRATEGY_LABELS,
    STRATEGY_HISTORY_KEYS,
    SpatialPrisonersDilemmaModel,
    make_settings,
)


DEMO_OUTPUT_DIR = Path("docs/data/spatial-prisoners-dilemma-demo")
SAMPLE_EVERY_STEPS = 4
FRAME_CHUNK_SIZE = 40
ROUND_DIGITS = 6
FRAME_STAT_DIGITS = 4
GRID_MAJOR_STEP = 5
SELECTED_CONFIG_KEYS = (
    "grid_width",
    "grid_height",
    "initial_agent_fraction",
    "carrying_capacity_fraction",
    "simulation_steps",
    "cost_of_living",
    "travel_cost",
    "reproduce_min_energy",
    "reproduce_cost",
    "reproduction_inheritance",
    "max_children_per_step",
    "payoff_cc",
    "payoff_cd",
    "payoff_dc",
    "payoff_dd",
    "max_energy",
    "initial_energy_mean",
    "initial_energy_stddev",
    "initial_energy_min",
    "env_noise",
    "trait_count",
    "pure_strategy",
    "strategy_per_trait",
    "mutation_rate",
    "strategy_weights",
    "random_seed",
)


def _round_number(value: float, digits: int = ROUND_DIGITS) -> float | None:
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    return round(numeric, digits)


def _git_commit() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    commit = completed.stdout.strip()
    return commit or None


def _write_json(path: Path, payload: Any, *, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        if pretty:
            json.dump(payload, handle, indent=2, sort_keys=False)
        else:
            json.dump(payload, handle, separators=(",", ":"), sort_keys=False)
        handle.write("\n")


def _write_frame_chunks(output_dir: Path, frames: list[dict[str, Any]]) -> list[str]:
    frame_paths: list[str] = []
    for chunk_index, start in enumerate(range(0, len(frames), FRAME_CHUNK_SIZE)):
        chunk_frames = frames[start: start + FRAME_CHUNK_SIZE]
        chunk_path = output_dir / f"frames_{chunk_index:04d}.json"
        frame_paths.append(chunk_path.name)
        payload = {
            "chunk_index": chunk_index,
            "start_frame_index": start,
            "end_frame_index": start + len(chunk_frames) - 1,
            "frames": chunk_frames,
        }
        _write_json(chunk_path, payload, pretty=False)
    return frame_paths


def _same_trait_strategy_name(strategy_id: int) -> str:
    return STRATEGY_LABELS[strategy_id // 10]


def _serialize_frame(model: SpatialPrisonersDilemmaModel, *, step: int) -> dict[str, Any]:
    latest_index = -1
    return {
        "step": int(step),
        "agents": [
            [
                int(agent.x),
                int(agent.y),
                int(agent.trait),
                int(agent.strategy_id // 10),
                int(agent.strategy_id % 10),
                int((agent.strategy_id // 10) == (agent.strategy_id % 10)),
            ]
            for agent in sorted(model.agents, key=lambda agent: agent.id)
        ],
        "stats": {
            "population": int(model.history["population"][latest_index]),
            "mean_energy": _round_number(
                model.history["mean_energy"][latest_index],
                FRAME_STAT_DIGITS,
            ),
            "births": int(model.history["births"][latest_index]),
            "deaths_total": int(model.history["deaths_total"][latest_index]),
            "interaction_pairs": int(model.history["interaction_pairs"][latest_index]),
            "movement_successes": int(model.history["movement_successes"][latest_index]),
            "pure_count": int(model.history["pure_count"][latest_index]),
            "contingent_count": int(model.history["contingent_count"][latest_index]),
            "same_trait_cooperate": int(model.history["same_trait_cooperate"][latest_index]),
            "same_trait_defect": int(model.history["same_trait_defect"][latest_index]),
            "same_trait_tit_for_tat": int(model.history["same_trait_tit_for_tat"][latest_index]),
            "same_trait_random": int(model.history["same_trait_random"][latest_index]),
            "other_trait_cooperate": int(model.history["other_trait_cooperate"][latest_index]),
            "other_trait_defect": int(model.history["other_trait_defect"][latest_index]),
            "other_trait_tit_for_tat": int(model.history["other_trait_tit_for_tat"][latest_index]),
            "other_trait_random": int(model.history["other_trait_random"][latest_index]),
        },
    }


def _build_summary(model: SpatialPrisonersDilemmaModel, frames: list[dict[str, Any]]) -> dict[str, Any]:
    steps_done = int(model.step_index)
    extinction_step = None
    if not model.agents and steps_done < model.settings.simulation_steps:
        extinction_step = steps_done

    final_summary = model.final_summary()
    history = model.history
    return {
        "step_hist": [int(value) for value in history["step"]],
        "population_hist": [int(value) for value in history["population"]],
        "mean_energy_hist": [
            _round_number(value) for value in history["mean_energy"]
        ],
        "births_hist": [int(value) for value in history["births"]],
        "deaths_total_hist": [int(value) for value in history["deaths_total"]],
        "interaction_pairs_hist": [int(value) for value in history["interaction_pairs"]],
        "movement_successes_hist": [int(value) for value in history["movement_successes"]],
        "pure_count_hist": [int(value) for value in history["pure_count"]],
        "contingent_count_hist": [int(value) for value in history["contingent_count"]],
        **{
            f"same_trait_{suffix}_hist": [
                int(value) for value in history[f"same_trait_{suffix}"]
            ]
            for suffix in STRATEGY_HISTORY_KEYS.values()
        },
        **{
            f"other_trait_{suffix}_hist": [
                int(value) for value in history[f"other_trait_{suffix}"]
            ]
            for suffix in STRATEGY_HISTORY_KEYS.values()
        },
        "sampled_steps": [int(frame["step"]) for frame in frames],
        "steps_done": steps_done,
        "success": extinction_step is None and steps_done == model.settings.simulation_steps,
        "extinction_step": extinction_step,
        "final_population": int(final_summary["population"]),
        "final_mean_energy": _round_number(final_summary["mean_energy"]),
        "final_same_trait_strategy_counts": final_summary["same_trait_strategy_counts"],
        "final_other_trait_strategy_counts": final_summary["other_trait_strategy_counts"],
        "final_pure_count": int(final_summary["pure_count"]),
        "final_contingent_count": int(final_summary["contingent_count"]),
    }


def _run_sampled_demo() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    cfg = dict(website_demo_config)
    settings = make_settings(cfg)
    model = SpatialPrisonersDilemmaModel(settings)
    frames = [_serialize_frame(model, step=0)]

    while model.step_index < settings.simulation_steps and model.agents:
        model.step()
        if (
            model.step_index % SAMPLE_EVERY_STEPS == 0
            or model.step_index == settings.simulation_steps
            or not model.agents
        ):
            if frames[-1]["step"] != model.step_index:
                frames.append(_serialize_frame(model, step=model.step_index))

        if model.step_index % 25 == 0 or not model.agents:
            latest_index = -1
            print(
                f"export step={model.step_index:4d} "
                f"population={int(model.history['population'][latest_index]):4d} "
                f"mean_energy={float(model.history['mean_energy'][latest_index]):7.2f} "
                f"same_tft={int(model.history['same_trait_tit_for_tat'][latest_index]):4d} "
                f"same_defect={int(model.history['same_trait_defect'][latest_index]):4d}"
            )

    summary = _build_summary(model, frames)
    return cfg, frames, summary


def main() -> None:
    cfg, frames, summary = _run_sampled_demo()

    if DEMO_OUTPUT_DIR.exists():
        for child in DEMO_OUTPUT_DIR.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    DEMO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    frame_paths = _write_frame_chunks(DEMO_OUTPUT_DIR, frames)
    summary_path = DEMO_OUTPUT_DIR / "summary.json"
    _write_json(summary_path, summary, pretty=True)

    settings = make_settings(cfg)
    manifest = {
        "format_version": 1,
        "title": "Spatial Prisoner's Dilemma",
        "description": (
            "Sampled replay generated from the frozen website-demo configuration. "
            "The browser viewer replays exported states; it does not rerun the Python model."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "config_source": (
            "spatial_prisoners_dilemma/config/"
            "spatial_prisoners_dilemma_website_demo_config.py"
        ),
        "sample_every_steps": SAMPLE_EVERY_STEPS,
        "frame_chunk_size": FRAME_CHUNK_SIZE,
        "sampled_frame_count": len(frames),
        "grid_width": int(settings.grid_width),
        "grid_height": int(settings.grid_height),
        "grid_major_step": GRID_MAJOR_STEP,
        "agent_hard_limit": int(settings.agent_hard_limit),
        "simulation_steps": int(settings.simulation_steps),
        "trait_count": int(settings.trait_count),
        "random_seed": settings.random_seed,
        "strategy_labels": {
            str(strategy_id): label for strategy_id, label in STRATEGY_LABELS.items()
        },
        "summary_path": summary_path.name,
        "frame_paths": frame_paths,
        "config_excerpt": {key: cfg[key] for key in SELECTED_CONFIG_KEYS},
        "full_config": cfg,
    }
    _write_json(DEMO_OUTPUT_DIR / "manifest.json", manifest, pretty=True)

    print(
        f"Exported GitHub Pages demo bundle to {DEMO_OUTPUT_DIR} "
        f"with {len(frames)} sampled frames across {len(frame_paths)} chunk files."
    )


if __name__ == "__main__":
    main()
