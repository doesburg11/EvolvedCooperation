#!/usr/bin/env python3
"""
Export a sampled replay bundle for the GitHub Pages Retained Benefit demo.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.retained_benefit.utils.export_github_pages_demo
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
        "'./.conda/bin/python -m ecological_models.retained_benefit.utils.export_github_pages_demo'."
    )

from ..config.retained_benefit_website_demo_config import config as website_demo_config
from ..retained_benefit_model import RetainedBenefitModel, make_settings


DEMO_OUTPUT_DIR = Path("docs/data/retained-benefit-demo")
SAMPLE_EVERY_STEPS = 5
FRAME_CHUNK_SIZE = 25
ROUND_DIGITS = 6
FRAME_DIGITS = 4
GRID_MAJOR_STEP = 6
SELECTED_CONFIG_KEYS = (
    "grid_width",
    "grid_height",
    "toroidal_world",
    "neighborhood_mode",
    "simulation_steps",
    "base_fitness",
    "cooperation_cost",
    "cooperation_benefit",
    "retained_benefit_fraction",
    "mutation_rate",
    "mutation_stddev",
    "initial_cooperation_mean",
    "initial_cooperation_stddev",
    "initial_lineage_count",
    "initial_lineage_block_size",
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
        chunk_frames = frames[start:start + FRAME_CHUNK_SIZE]
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


def _serialize_grid(values: Any) -> list[list[float]]:
    return [
        [_round_number(cell, FRAME_DIGITS) for cell in row]
        for row in values
    ]


def _serialize_lineage(values: Any) -> list[list[int]]:
    return [[int(cell) for cell in row] for row in values]


def _serialize_frame(model: RetainedBenefitModel, *, step: int) -> dict[str, Any]:
    latest_index = -1
    return {
        "step": int(step),
        "cooperation_grid": _serialize_grid(model.cooperation),
        "lineage_grid": _serialize_lineage(model.lineage),
        "stats": {
            "mean_cooperation": _round_number(
                model.history["mean_cooperation"][latest_index],
                FRAME_DIGITS,
            ),
            "var_cooperation": _round_number(
                model.history["var_cooperation"][latest_index],
                FRAME_DIGITS,
            ),
            "mean_fitness": _round_number(
                model.history["mean_fitness"][latest_index],
                FRAME_DIGITS,
            ),
            "local_assortment": _round_number(
                model.history["local_assortment"][latest_index],
                FRAME_DIGITS,
            ),
            "dominant_lineage_share": _round_number(
                model.history["dominant_lineage_share"][latest_index],
                FRAME_DIGITS,
            ),
            "lineage_count": int(round(model.history["lineage_count"][latest_index])),
        },
    }


def _build_summary(model: RetainedBenefitModel, frames: list[dict[str, Any]]) -> dict[str, Any]:
    history = model.history
    return {
        "step_hist": [int(value) for value in history["step"]],
        "mean_cooperation_hist": [_round_number(value) for value in history["mean_cooperation"]],
        "var_cooperation_hist": [_round_number(value) for value in history["var_cooperation"]],
        "mean_fitness_hist": [_round_number(value) for value in history["mean_fitness"]],
        "local_assortment_hist": [_round_number(value) for value in history["local_assortment"]],
        "dominant_lineage_share_hist": [
            _round_number(value) for value in history["dominant_lineage_share"]
        ],
        "lineage_count_hist": [int(round(value)) for value in history["lineage_count"]],
        "sampled_steps": [int(frame["step"]) for frame in frames],
        "steps_done": int(model.step_count),
        "final_mean_cooperation": _round_number(history["mean_cooperation"][-1]),
        "final_var_cooperation": _round_number(history["var_cooperation"][-1]),
        "final_mean_fitness": _round_number(history["mean_fitness"][-1]),
        "final_local_assortment": _round_number(history["local_assortment"][-1]),
        "final_dominant_lineage_share": _round_number(history["dominant_lineage_share"][-1]),
        "final_lineage_count": int(round(history["lineage_count"][-1])),
    }


def _run_sampled_demo() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    cfg = dict(website_demo_config)
    settings = make_settings(cfg)
    model = RetainedBenefitModel(settings)
    frames = [_serialize_frame(model, step=0)]

    while model.step_count < settings.simulation_steps:
        model.step()
        if (
            model.step_count % SAMPLE_EVERY_STEPS == 0
            or model.step_count == settings.simulation_steps
        ):
            if frames[-1]["step"] != model.step_count:
                frames.append(_serialize_frame(model, step=model.step_count))

        if model.step_count % 25 == 0 or model.step_count == settings.simulation_steps:
            print(
                f"export step={model.step_count:4d} "
                "mean_h="
                f"{float(model.history['mean_cooperation'][-1]):.3f} "
                "assortment="
                f"{float(model.history['local_assortment'][-1]):.3f} "
                "dominant_lineage="
                f"{float(model.history['dominant_lineage_share'][-1]):.3f}"
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
        "title": "Retained Benefit",
        "description": (
            "Sampled replay generated from the frozen website-demo configuration. "
            "The browser viewer replays exported states; it does not rerun the Python model."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "config_source": (
            "ecological_models/retained_benefit/config/retained_benefit_website_demo_config.py"
        ),
        "sample_every_steps": SAMPLE_EVERY_STEPS,
        "frame_chunk_size": FRAME_CHUNK_SIZE,
        "sampled_frame_count": len(frames),
        "grid_width": int(settings.grid_width),
        "grid_height": int(settings.grid_height),
        "grid_major_step": GRID_MAJOR_STEP,
        "simulation_steps": int(settings.simulation_steps),
        "random_seed": settings.random_seed,
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
