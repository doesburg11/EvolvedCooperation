#!/usr/bin/env python3
"""
Export a sampled replay bundle for the GitHub Pages public-goods demo.

Run from the repository root with:
  ./.conda/bin/python -m predpreygrass_public_goods.utils.export_github_pages_demo
"""

from __future__ import annotations

import json
import math
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m predpreygrass_public_goods.utils.export_github_pages_demo'."
    )


from .. import emerging_cooperation as eco


DEMO_OUTPUT_DIR = Path("docs/data/public-goods-demo")
PREVIEW_GIF_PATH = Path("assets/predprey_public_goods/public_goods_demo_preview.gif")
SAMPLE_EVERY_STEPS = 50
FRAME_CHUNK_SIZE = 40
GRASS_QUANTIZATION_LEVELS = 100
ROUND_DIGITS = 6
FRAME_STAT_DIGITS = 4
PREDATOR_TRAIT_DIGITS = 3
PREVIEW_FRAME_STRIDE = 3
PREVIEW_CELL_SIZE = 6
PREVIEW_FRAME_DURATION_MS = 110
PREVIEW_LOOP = 0
PREVIEW_GRASS_LOW = (244, 239, 229)
PREVIEW_GRASS_HIGH = (79, 138, 87)
PREVIEW_PREY_COLOR = (45, 95, 186)
PREVIEW_PREDATOR_LOW = (182, 70, 40)
PREVIEW_PREDATOR_HIGH = (121, 30, 36)
PREVIEW_PREDATOR_OUTLINE = (18, 18, 18)
SELECTED_CONFIG_KEYS = (
    "grid_width",
    "grid_height",
    "simulation_steps",
    "initial_predator_count",
    "initial_prey_count",
    "initial_predator_energy",
    "initial_predator_hunt_investment_trait_min",
    "initial_predator_hunt_investment_trait_max",
    "hunt_success_rule",
    "prey_detection_radius",
    "hunter_pool_radius",
    "threshold_synergy_min_hunters",
    "threshold_synergy_formation_energy_factor",
    "threshold_synergy_execution_energy_factor",
    "threshold_synergy_success_steepness",
    "threshold_synergy_max_success_probability",
    "predator_cooperation_cost_per_unit",
    "share_prey_equally",
    "random_seed",
)


def _round_number(value: float, digits: int = ROUND_DIGITS) -> float | None:
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    return round(numeric, digits)


def _json_ready_history(values: list[float], digits: int = ROUND_DIGITS) -> list[float | None]:
    return [_round_number(value, digits) for value in values]


def _predator_trait_stats(preds: list[eco.Predator]) -> tuple[float, float]:
    if not preds:
        return 0.0, 0.0
    traits = np.fromiter((pred.hunt_investment_trait for pred in preds), dtype=float, count=len(preds))
    return float(np.mean(traits)), float(np.var(traits))


def _serialize_grass(grass: np.ndarray, max_grass_energy_per_cell: float) -> list[int]:
    grass_scale = max(max_grass_energy_per_cell, 1e-9)
    normalized = np.clip(grass / grass_scale, 0.0, 1.0)
    quantized = np.rint(normalized * GRASS_QUANTIZATION_LEVELS).astype(np.uint8, copy=False)
    return quantized.ravel().tolist()


def _serialize_frame(
    *,
    step: int,
    preds: list[eco.Predator],
    preys: list[eco.Prey],
    grass: np.ndarray,
    max_grass_energy_per_cell: float,
    mean_trait: float,
    trait_variance: float,
) -> dict[str, Any]:
    pred_energy, prey_energy, grass_energy, total_energy = eco.energy_budget(preds, preys, grass)
    return {
        "step": int(step),
        "grass": _serialize_grass(grass, max_grass_energy_per_cell),
        "predators": [
            [int(pred.x), int(pred.y), round(float(pred.hunt_investment_trait), PREDATOR_TRAIT_DIGITS)]
            for pred in preds
        ],
        "preys": [[int(prey.x), int(prey.y)] for prey in preys],
        "stats": {
            "predator_count": len(preds),
            "prey_count": len(preys),
            "mean_trait": _round_number(mean_trait, FRAME_STAT_DIGITS),
            "trait_variance": _round_number(trait_variance, FRAME_STAT_DIGITS),
            "grass_mean": _round_number(float(np.mean(grass)), FRAME_STAT_DIGITS),
            "predator_energy": _round_number(pred_energy, FRAME_STAT_DIGITS),
            "prey_energy": _round_number(prey_energy, FRAME_STAT_DIGITS),
            "grass_energy": _round_number(grass_energy, FRAME_STAT_DIGITS),
            "total_energy": _round_number(total_energy, FRAME_STAT_DIGITS),
        },
    }


def _blend_rgb(start: tuple[int, int, int], end: tuple[int, int, int], mix: float) -> tuple[int, int, int]:
    bounded_mix = max(0.0, min(1.0, float(mix)))
    return tuple(
        int(round(start[index] + (end[index] - start[index]) * bounded_mix))
        for index in range(3)
    )


def _build_demo_config() -> dict[str, Any]:
    cfg = eco.resolve_config(eco.model_config)
    cfg["enable_live_pygame_renderer"] = False
    cfg["plot_macro_energy_flows"] = False
    cfg["plot_trait_selection_diagnostics"] = False
    cfg["log_reward_sharing"] = False
    cfg["log_energy_accounting"] = False
    return cfg


def _init_world(cfg: dict[str, Any]) -> tuple[list[eco.Predator], list[eco.Prey], np.ndarray]:
    if cfg["random_seed"] is not None:
        random.seed(cfg["random_seed"])

    preds = [
        eco.Predator(
            random.randrange(cfg["grid_width"]),
            random.randrange(cfg["grid_height"]),
            cfg["initial_predator_energy"],
            eco.sample_predator_hunt_investment_trait(cfg),
        )
        for _ in range(cfg["initial_predator_count"])
    ]
    preys = [
        eco.Prey(
            random.randrange(cfg["grid_width"]),
            random.randrange(cfg["grid_height"]),
            eco.sample_prey_energy(cfg),
        )
        for _ in range(cfg["initial_prey_count"])
    ]
    grass = eco.init_grass_field(cfg)
    return preds, preys, grass


def _run_sampled_demo(cfg: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    preds, preys, grass = _init_world(cfg)

    pred_hist: list[int] = []
    prey_hist: list[int] = []
    mean_trait_hist: list[float] = []
    trait_variance_hist: list[float] = []
    successful_group_trait_hist: list[float] = []

    initial_mean_trait, initial_trait_variance = _predator_trait_stats(preds)
    frames = [
        _serialize_frame(
            step=0,
            preds=preds,
            preys=preys,
            grass=grass,
            max_grass_energy_per_cell=float(cfg["max_grass_energy_per_cell"]),
            mean_trait=initial_mean_trait,
            trait_variance=initial_trait_variance,
        )
    ]

    split_stats = {
        "kills": 0,
        "captured_energy_sum": 0.0,
        "multi_hunter_kills": 0,
        "inequality_sum": 0.0,
    }
    extinction_step: int | None = None

    for step in range(1, int(cfg["simulation_steps"]) + 1):
        flow_stats: dict[str, float] = {}
        preds, preys, grass = eco.step_world(
            preds,
            preys,
            grass,
            split_stats=split_stats,
            flow_stats=flow_stats,
            config=cfg,
        )

        pred_hist.append(len(preds))
        prey_hist.append(len(preys))

        mean_trait, trait_variance = _predator_trait_stats(preds)
        mean_trait_hist.append(mean_trait)
        trait_variance_hist.append(trait_variance)

        multi_hunter_hunter_count = flow_stats.get("multi_hunter_hunter_count", 0.0)
        if multi_hunter_hunter_count > 0.0:
            successful_group_trait = flow_stats.get("group_hunt_effort_sum", 0.0) / multi_hunter_hunter_count
        else:
            successful_group_trait = float("nan")
        successful_group_trait_hist.append(successful_group_trait)

        should_sample_frame = step % SAMPLE_EVERY_STEPS == 0 or step == int(cfg["simulation_steps"])
        if should_sample_frame:
            frames.append(
                _serialize_frame(
                    step=step,
                    preds=preds,
                    preys=preys,
                    grass=grass,
                    max_grass_energy_per_cell=float(cfg["max_grass_energy_per_cell"]),
                    mean_trait=mean_trait,
                    trait_variance=trait_variance,
                )
            )

        if not preds or not preys:
            extinction_step = step
            if frames[-1]["step"] != step:
                frames.append(
                    _serialize_frame(
                        step=step,
                        preds=preds,
                        preys=preys,
                        grass=grass,
                        max_grass_energy_per_cell=float(cfg["max_grass_energy_per_cell"]),
                        mean_trait=mean_trait,
                        trait_variance=trait_variance,
                    )
                )
            break

        if step % 500 == 0:
            print(
                f"export step={step:5d} "
                f"preds={len(preds):4d} preys={len(preys):4d} "
                f"mean_trait={mean_trait:.3f}"
            )

    steps_done = len(pred_hist)
    success = extinction_step is None and steps_done == int(cfg["simulation_steps"])
    summary = {
        "pred_hist": pred_hist,
        "prey_hist": prey_hist,
        "mean_trait_hist": _json_ready_history(mean_trait_hist),
        "trait_variance_hist": _json_ready_history(trait_variance_hist),
        "successful_group_trait_hist": _json_ready_history(successful_group_trait_hist),
        "sampled_steps": [int(frame["step"]) for frame in frames],
        "steps_done": steps_done,
        "success": success,
        "extinction_step": extinction_step,
        "final_predator_count": len(preds),
        "final_prey_count": len(preys),
        "final_mean_trait": _round_number(mean_trait_hist[-1], FRAME_STAT_DIGITS) if mean_trait_hist else None,
        "final_trait_variance": (
            _round_number(trait_variance_hist[-1], FRAME_STAT_DIGITS) if trait_variance_hist else None
        ),
    }
    return summary, frames


def _render_preview_frame(
    frame: dict[str, Any],
    *,
    grid_width: int,
    grid_height: int,
    grass_quantization_levels: int,
) -> Image.Image:
    image = Image.new(
        "RGB",
        (grid_width * PREVIEW_CELL_SIZE, grid_height * PREVIEW_CELL_SIZE),
        PREVIEW_GRASS_LOW,
    )
    draw = ImageDraw.Draw(image)

    for y in range(grid_height):
        for x in range(grid_width):
            grass_value = frame["grass"][y * grid_width + x] / max(grass_quantization_levels, 1)
            color = _blend_rgb(PREVIEW_GRASS_LOW, PREVIEW_GRASS_HIGH, grass_value)
            left = x * PREVIEW_CELL_SIZE
            top = y * PREVIEW_CELL_SIZE
            draw.rectangle(
                (
                    left,
                    top,
                    left + PREVIEW_CELL_SIZE - 1,
                    top + PREVIEW_CELL_SIZE - 1,
                ),
                fill=color,
            )

    prey_margin = max(1, PREVIEW_CELL_SIZE // 5)
    for prey_x, prey_y in frame["preys"]:
        left = prey_x * PREVIEW_CELL_SIZE + prey_margin
        top = prey_y * PREVIEW_CELL_SIZE + prey_margin
        draw.rectangle(
            (
                left,
                top,
                left + PREVIEW_CELL_SIZE - prey_margin - 1,
                top + PREVIEW_CELL_SIZE - prey_margin - 1,
            ),
            fill=PREVIEW_PREY_COLOR,
        )

    predator_radius = max(1, int(round(PREVIEW_CELL_SIZE * 0.35)))
    for pred_x, pred_y, pred_trait in frame["predators"]:
        center_x = pred_x * PREVIEW_CELL_SIZE + PREVIEW_CELL_SIZE / 2
        center_y = pred_y * PREVIEW_CELL_SIZE + PREVIEW_CELL_SIZE / 2
        predator_color = _blend_rgb(PREVIEW_PREDATOR_LOW, PREVIEW_PREDATOR_HIGH, pred_trait)
        draw.ellipse(
            (
                center_x - predator_radius,
                center_y - predator_radius,
                center_x + predator_radius,
                center_y + predator_radius,
            ),
            fill=predator_color,
            outline=PREVIEW_PREDATOR_OUTLINE,
            width=1,
        )

    return image


def _write_preview_gif(
    frames: list[dict[str, Any]],
    *,
    grid_width: int,
    grid_height: int,
    grass_quantization_levels: int,
) -> None:
    selected_frames = frames[::PREVIEW_FRAME_STRIDE]
    if selected_frames[-1]["step"] != frames[-1]["step"]:
        selected_frames.append(frames[-1])

    preview_frames = [
        _render_preview_frame(
            frame,
            grid_width=grid_width,
            grid_height=grid_height,
            grass_quantization_levels=grass_quantization_levels,
        ).quantize(colors=128, method=Image.MEDIANCUT)
        for frame in selected_frames
    ]

    PREVIEW_GIF_PATH.parent.mkdir(parents=True, exist_ok=True)
    preview_frames[0].save(
        PREVIEW_GIF_PATH,
        save_all=True,
        append_images=preview_frames[1:],
        duration=PREVIEW_FRAME_DURATION_MS,
        loop=PREVIEW_LOOP,
        optimize=False,
        disposal=2,
    )


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
        chunk_frames = frames[start : start + FRAME_CHUNK_SIZE]
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


def main() -> None:
    cfg = _build_demo_config()
    summary, frames = _run_sampled_demo(cfg)

    if DEMO_OUTPUT_DIR.exists():
        shutil.rmtree(DEMO_OUTPUT_DIR)
    DEMO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    frame_paths = _write_frame_chunks(DEMO_OUTPUT_DIR, frames)
    _write_preview_gif(
        frames,
        grid_width=int(cfg["grid_width"]),
        grid_height=int(cfg["grid_height"]),
        grass_quantization_levels=GRASS_QUANTIZATION_LEVELS,
    )
    summary_path = DEMO_OUTPUT_DIR / "summary.json"
    _write_json(summary_path, summary, pretty=True)

    manifest = {
        "format_version": 1,
        "title": "Predator-Prey Public Goods Replay",
        "description": (
            "Sampled replay generated from the active public-goods configuration. "
            "The browser viewer replays exported states; it does not rerun the Python model."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sample_every_steps": SAMPLE_EVERY_STEPS,
        "frame_chunk_size": FRAME_CHUNK_SIZE,
        "grass_quantization_levels": GRASS_QUANTIZATION_LEVELS,
        "sampled_frame_count": len(frames),
        "grid_width": int(cfg["grid_width"]),
        "grid_height": int(cfg["grid_height"]),
        "max_grass_energy_per_cell": float(cfg["max_grass_energy_per_cell"]),
        "simulation_steps": int(cfg["simulation_steps"]),
        "random_seed": cfg["random_seed"],
        "summary_path": summary_path.name,
        "frame_paths": frame_paths,
        "config_excerpt": {key: cfg[key] for key in SELECTED_CONFIG_KEYS},
    }
    _write_json(DEMO_OUTPUT_DIR / "manifest.json", manifest, pretty=True)

    print(
        f"Exported GitHub Pages demo bundle to {DEMO_OUTPUT_DIR} "
        f"with {len(frames)} sampled frames across {len(frame_paths)} chunk files."
    )
    print(f"Wrote preview GIF to {PREVIEW_GIF_PATH}.")


if __name__ == "__main__":
    main()
