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
from PIL import Image, ImageDraw, ImageFont


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
PREVIEW_FRAME_STRIDE = 4
PREVIEW_WORLD_CELL_SIZE = 6
PREVIEW_FRAME_DURATION_MS = 120
PREVIEW_LOOP = 0
PREVIEW_PAGE_WIDTH = 920
PREVIEW_PAGE_HEIGHT = 668
PREVIEW_MARGIN = 16
PREVIEW_GAP = 16
PREVIEW_HEADER_HEIGHT = 96
PREVIEW_MAIN_CARD_HEIGHT = 532
PREVIEW_CHART_CARD_HEIGHT = 320
PREVIEW_LEGEND_CARD_HEIGHT = 196
PREVIEW_VIEWER_CARD_WIDTH = 568
PREVIEW_SIDEBAR_CARD_WIDTH = 304
PREVIEW_CARD_PADDING = 18
PREVIEW_PAGE_BG = (255, 255, 255)
PREVIEW_CARD_BG = (247, 251, 255)
PREVIEW_CARD_BORDER = (214, 228, 245)
PREVIEW_TEXT_MAIN = (31, 45, 61)
PREVIEW_TEXT_MUTED = (78, 98, 121)
PREVIEW_BLUE_STRONG = (15, 51, 104)
PREVIEW_BLUE_MID = (28, 75, 143)
PREVIEW_BLUE_SOFT = (120, 170, 230)
PREVIEW_WHITE = (255, 255, 255)
PREVIEW_ACCENT_TRAIT = (28, 75, 143)
PREVIEW_ACCENT_PANEL = (234, 242, 251)
PREVIEW_CHART_BG = (255, 255, 255)
PREVIEW_CHART_GRID = (214, 228, 245)
PREVIEW_CHART_AXIS = (115, 143, 178)
PREVIEW_CHART_MARKER = (15, 51, 104)
PREVIEW_STATUS_BG = (234, 242, 251)
PREVIEW_BUTTON_BG = (28, 75, 143)
PREVIEW_BUTTON_TEXT = (255, 255, 255)
PREVIEW_BUTTON_ALT_BG = (120, 170, 230)
PREVIEW_SWATCH_BORDER = (15, 51, 104)
PREVIEW_GRASS_LOW = (244, 239, 229)
PREVIEW_GRASS_HIGH = (79, 138, 87)
PREVIEW_PREY_COLOR = (45, 95, 186)
PREVIEW_PREDATOR_LOW = (182, 70, 40)
PREVIEW_PREDATOR_HIGH = (121, 30, 36)
PREVIEW_PREDATOR_OUTLINE = (18, 18, 18)
PREVIEW_FONT_CACHE: dict[tuple[int, bool, bool], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}
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


def _load_preview_font(
    size: int,
    *,
    bold: bool = False,
    mono: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    cache_key = (size, bold, mono)
    if cache_key in PREVIEW_FONT_CACHE:
        return PREVIEW_FONT_CACHE[cache_key]

    if mono and bold:
        candidates = (
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "DejaVuSansMono-Bold.ttf",
        )
    elif mono:
        candidates = (
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "DejaVuSansMono.ttf",
        )
    elif bold:
        candidates = (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "DejaVuSans-Bold.ttf",
        )
    else:
        candidates = (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "DejaVuSans.ttf",
        )

    for candidate in candidates:
        try:
            font = ImageFont.truetype(candidate, size)
            PREVIEW_FONT_CACHE[cache_key] = font
            return font
        except OSError:
            continue

    fallback = ImageFont.load_default()
    PREVIEW_FONT_CACHE[cache_key] = fallback
    return fallback


def _text_box_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _draw_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int] = PREVIEW_CARD_BG,
    border: tuple[int, int, int] = PREVIEW_CARD_BORDER,
) -> None:
    draw.rectangle(box, fill=fill, outline=border, width=1)


def _draw_chip(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    text: str,
    fill: tuple[int, int, int],
    text_fill: tuple[int, int, int],
    mono: bool = True,
) -> None:
    draw.rectangle(box, fill=fill, outline=fill, width=1)
    font = _load_preview_font(13, bold=False, mono=mono)
    text_width, text_height = _text_box_size(draw, text, font)
    text_x = box[0] + (box[2] - box[0] - text_width) / 2
    text_y = box[1] + (box[3] - box[1] - text_height) / 2 - 1
    draw.text((text_x, text_y), text, fill=text_fill, font=font)


def _draw_stat_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    label: str,
    value: str,
) -> None:
    draw.rectangle(box, fill=PREVIEW_WHITE, outline=PREVIEW_CARD_BORDER, width=1)
    label_font = _load_preview_font(12, mono=True)
    value_font = _load_preview_font(18, bold=True)
    draw.text((box[0] + 12, box[1] + 10), label, fill=PREVIEW_TEXT_MUTED, font=label_font)
    draw.text((box[0] + 12, box[1] + 31), value, fill=PREVIEW_TEXT_MAIN, font=value_font)


def _draw_world_canvas(
    frame: dict[str, Any],
    *,
    grid_width: int,
    grid_height: int,
    grass_quantization_levels: int,
) -> Image.Image:
    image = Image.new(
        "RGB",
        (grid_width * PREVIEW_WORLD_CELL_SIZE, grid_height * PREVIEW_WORLD_CELL_SIZE),
        PREVIEW_GRASS_LOW,
    )
    draw = ImageDraw.Draw(image)

    for y in range(grid_height):
        for x in range(grid_width):
            grass_value = frame["grass"][y * grid_width + x] / max(grass_quantization_levels, 1)
            color = _blend_rgb(PREVIEW_GRASS_LOW, PREVIEW_GRASS_HIGH, grass_value)
            left = x * PREVIEW_WORLD_CELL_SIZE
            top = y * PREVIEW_WORLD_CELL_SIZE
            draw.rectangle(
                (
                    left,
                    top,
                    left + PREVIEW_WORLD_CELL_SIZE - 1,
                    top + PREVIEW_WORLD_CELL_SIZE - 1,
                ),
                fill=color,
            )

    prey_margin = max(1, PREVIEW_WORLD_CELL_SIZE // 5)
    for prey_x, prey_y in frame["preys"]:
        left = prey_x * PREVIEW_WORLD_CELL_SIZE + prey_margin
        top = prey_y * PREVIEW_WORLD_CELL_SIZE + prey_margin
        draw.rectangle(
            (
                left,
                top,
                left + PREVIEW_WORLD_CELL_SIZE - prey_margin - 1,
                top + PREVIEW_WORLD_CELL_SIZE - prey_margin - 1,
            ),
            fill=PREVIEW_PREY_COLOR,
        )

    predator_radius = max(1, int(round(PREVIEW_WORLD_CELL_SIZE * 0.35)))
    for pred_x, pred_y, pred_trait in frame["predators"]:
        center_x = pred_x * PREVIEW_WORLD_CELL_SIZE + PREVIEW_WORLD_CELL_SIZE / 2
        center_y = pred_y * PREVIEW_WORLD_CELL_SIZE + PREVIEW_WORLD_CELL_SIZE / 2
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


def _downsample_series(values: list[float | None], target_points: int) -> list[float | None]:
    if not values:
        return []
    if target_points <= 1:
        return [values[-1]]
    last_index = len(values) - 1
    return [values[int(round(index * last_index / (target_points - 1)))] for index in range(target_points)]


def _draw_series_line(
    draw: ImageDraw.ImageDraw,
    *,
    plot_box: tuple[int, int, int, int],
    values: list[float | None],
    color: tuple[int, int, int],
    max_value: float,
) -> None:
    plot_width = max(2, plot_box[2] - plot_box[0])
    series = _downsample_series(values, plot_width)
    if not series:
        return

    points: list[tuple[float, float]] = []
    x_denominator = max(1, len(series) - 1)
    y_scale = max(max_value, 1e-9)
    for index, value in enumerate(series):
        if value is None:
            if len(points) >= 2:
                draw.line(points, fill=color, width=3)
            points = []
            continue
        x = plot_box[0] + index * (plot_box[2] - plot_box[0]) / x_denominator
        y = plot_box[3] - float(value) * (plot_box[3] - plot_box[1]) / y_scale
        points.append((x, y))

    if len(points) >= 2:
        draw.line(points, fill=color, width=3)


def _draw_chart(
    draw: ImageDraw.ImageDraw,
    *,
    box: tuple[int, int, int, int],
    title: str,
    subtitle: str | None,
    step: int,
    steps_done: int,
    series_list: list[tuple[list[float | None], tuple[int, int, int]]],
    max_value: float,
) -> None:
    _draw_card(draw, box)
    x0, y0, x1, y1 = box
    title_font = _load_preview_font(22, bold=True)
    subtitle_font = _load_preview_font(13)
    draw.text((x0 + 18, y0 + 18), title, fill=PREVIEW_TEXT_MAIN, font=title_font)
    plot_top = y0 + 56
    if subtitle:
        draw.text((x0 + 18, y0 + 46), subtitle, fill=PREVIEW_TEXT_MUTED, font=subtitle_font)
        plot_top = y0 + 76

    plot_box = (x0 + 46, plot_top, x1 - 18, y1 - 28)
    draw.rectangle(plot_box, fill=PREVIEW_CHART_BG, outline=PREVIEW_CARD_BORDER, width=1)

    for grid_index in range(5):
        grid_y = plot_box[1] + grid_index * (plot_box[3] - plot_box[1]) / 4
        draw.line((plot_box[0], grid_y, plot_box[2], grid_y), fill=PREVIEW_CHART_GRID, width=1)

    draw.line((plot_box[0], plot_box[1], plot_box[0], plot_box[3]), fill=PREVIEW_CHART_AXIS, width=1)
    draw.line((plot_box[0], plot_box[3], plot_box[2], plot_box[3]), fill=PREVIEW_CHART_AXIS, width=1)

    tick_font = _load_preview_font(11, mono=True)
    for tick_index in range(5):
        ratio = tick_index / 4
        tick_value = max_value * (1 - ratio)
        tick_y = plot_box[1] + ratio * (plot_box[3] - plot_box[1])
        tick_text = f"{tick_value:.2f}" if max_value <= 1.0 else f"{tick_value:.0f}"
        tick_width, tick_height = _text_box_size(draw, tick_text, tick_font)
        draw.text(
            (plot_box[0] - 8 - tick_width, tick_y - tick_height / 2),
            tick_text,
            fill=PREVIEW_TEXT_MUTED,
            font=tick_font,
        )

    for values, color in series_list:
        _draw_series_line(draw, plot_box=plot_box, values=values, color=color, max_value=max_value)

    marker_ratio = 0.0 if steps_done <= 0 else max(0.0, min(1.0, step / steps_done))
    marker_x = plot_box[0] + marker_ratio * (plot_box[2] - plot_box[0])
    draw.line((marker_x, plot_box[1], marker_x, plot_box[3]), fill=PREVIEW_CHART_MARKER, width=2)

    start_label = "0"
    end_label = f"{steps_done}"
    draw.text((plot_box[0], plot_box[3] + 6), start_label, fill=PREVIEW_TEXT_MUTED, font=tick_font)
    end_width, _ = _text_box_size(draw, end_label, tick_font)
    draw.text((plot_box[2] - end_width, plot_box[3] + 6), end_label, fill=PREVIEW_TEXT_MUTED, font=tick_font)


def _render_preview_frame(
    frame: dict[str, Any],
    *,
    frame_index: int,
    sampled_frame_count: int,
    summary: dict[str, Any],
    grid_width: int,
    grid_height: int,
    grass_quantization_levels: int,
) -> Image.Image:
    image = Image.new("RGB", (PREVIEW_PAGE_WIDTH, PREVIEW_PAGE_HEIGHT), PREVIEW_PAGE_BG)
    draw = ImageDraw.Draw(image)

    header_box = (
        PREVIEW_MARGIN,
        PREVIEW_MARGIN,
        PREVIEW_PAGE_WIDTH - PREVIEW_MARGIN,
        PREVIEW_MARGIN + PREVIEW_HEADER_HEIGHT,
    )
    viewer_box = (
        PREVIEW_MARGIN,
        header_box[3] + PREVIEW_GAP,
        PREVIEW_MARGIN + PREVIEW_VIEWER_CARD_WIDTH,
        header_box[3] + PREVIEW_GAP + PREVIEW_MAIN_CARD_HEIGHT,
    )
    legend_box = (
        viewer_box[2] + PREVIEW_GAP,
        viewer_box[1] + PREVIEW_CHART_CARD_HEIGHT + PREVIEW_GAP,
        viewer_box[2] + PREVIEW_GAP + PREVIEW_SIDEBAR_CARD_WIDTH,
        viewer_box[1] + PREVIEW_CHART_CARD_HEIGHT + PREVIEW_GAP + PREVIEW_LEGEND_CARD_HEIGHT,
    )
    trait_chart_box = (
        viewer_box[2] + PREVIEW_GAP,
        viewer_box[1],
        viewer_box[2] + PREVIEW_GAP + PREVIEW_SIDEBAR_CARD_WIDTH,
        viewer_box[1] + PREVIEW_CHART_CARD_HEIGHT,
    )

    _draw_card(draw, header_box, fill=PREVIEW_BLUE_STRONG, border=PREVIEW_BLUE_STRONG)
    _draw_card(draw, viewer_box)
    _draw_card(draw, legend_box)

    eyebrow_font = _load_preview_font(13, mono=True)
    hero_title_font = _load_preview_font(32, bold=True)
    hero_text_font = _load_preview_font(15)
    draw.text((header_box[0] + 20, header_box[1] + 14), "EVOLVED COOPERATION", fill=PREVIEW_WHITE, font=eyebrow_font)
    draw.text(
        (header_box[0] + 20, header_box[1] + 30),
        "Predator-Prey Public Goods Replay",
        fill=PREVIEW_WHITE,
        font=hero_title_font,
    )
    hero_note = (
        "Sampled browser replay of the Python model. "
        "The preview mirrors the replay page layout."
    )
    draw.text((header_box[0] + 20, header_box[1] + 70), hero_note, fill=PREVIEW_WHITE, font=hero_text_font)

    viewer_title_font = _load_preview_font(23, bold=True)
    viewer_text_font = _load_preview_font(13)
    mono_font = _load_preview_font(13, mono=True)
    mono_small_font = _load_preview_font(12, mono=True)
    draw.text((viewer_box[0] + 18, viewer_box[1] + 14), "REPLAY", fill=PREVIEW_BLUE_STRONG, font=eyebrow_font)
    draw.text((viewer_box[0] + 18, viewer_box[1] + 31), "World State", fill=PREVIEW_TEXT_MAIN, font=viewer_title_font)

    play_button_box = (viewer_box[0] + 18, viewer_box[1] + 68, viewer_box[0] + 98, viewer_box[1] + 102)
    restart_button_box = (viewer_box[0] + 106, viewer_box[1] + 68, viewer_box[0] + 202, viewer_box[1] + 102)
    speed_box = (viewer_box[2] - 150, viewer_box[1] + 68, viewer_box[2] - 18, viewer_box[1] + 102)
    _draw_chip(draw, play_button_box, text="Play", fill=PREVIEW_BUTTON_BG, text_fill=PREVIEW_BUTTON_TEXT)
    _draw_chip(draw, restart_button_box, text="Restart", fill=PREVIEW_BUTTON_ALT_BG, text_fill=PREVIEW_WHITE)
    _draw_chip(draw, speed_box, text="8 fps", fill=PREVIEW_BUTTON_ALT_BG, text_fill=PREVIEW_WHITE)
    draw.text((speed_box[0] - 64, speed_box[1] + 9), "Playback", fill=PREVIEW_TEXT_MUTED, font=mono_small_font)

    slider_label_y = viewer_box[1] + 116
    draw.text((viewer_box[0] + 18, slider_label_y), "Frame", fill=PREVIEW_TEXT_MUTED, font=mono_font)
    slider_track_box = (viewer_box[0] + 74, slider_label_y + 8, viewer_box[2] - 104, slider_label_y + 14)
    draw.rectangle(slider_track_box, fill=PREVIEW_ACCENT_PANEL, outline=PREVIEW_CARD_BORDER, width=1)
    frame_ratio = 0.0 if sampled_frame_count <= 1 else frame_index / (sampled_frame_count - 1)
    slider_thumb_x = slider_track_box[0] + frame_ratio * (slider_track_box[2] - slider_track_box[0])
    draw.rectangle(
        (
            slider_thumb_x - 8,
            slider_track_box[1] - 6,
            slider_thumb_x + 8,
            slider_track_box[3] + 6,
        ),
        fill=PREVIEW_BLUE_MID,
        outline=PREVIEW_BLUE_STRONG,
    )
    frame_index_text = f"{frame_index + 1} / {sampled_frame_count}"
    frame_index_width, _ = _text_box_size(draw, frame_index_text, mono_font)
    draw.text(
        (viewer_box[2] - 18 - frame_index_width, slider_label_y),
        frame_index_text,
        fill=PREVIEW_TEXT_MUTED,
        font=mono_font,
    )

    world_rect = (viewer_box[0] + 18, viewer_box[1] + 146, viewer_box[0] + 18 + grid_width * PREVIEW_WORLD_CELL_SIZE, viewer_box[1] + 146 + grid_height * PREVIEW_WORLD_CELL_SIZE)
    world_canvas = _draw_world_canvas(
        frame,
        grid_width=grid_width,
        grid_height=grid_height,
        grass_quantization_levels=grass_quantization_levels,
    )
    draw.rectangle(
        (world_rect[0] - 2, world_rect[1] - 2, world_rect[2] + 2, world_rect[3] + 2),
        fill=PREVIEW_ACCENT_PANEL,
        outline=PREVIEW_CARD_BORDER,
        width=1,
    )
    image.paste(world_canvas, (world_rect[0], world_rect[1]))

    step_text = f"Step {frame['step']}"
    caption_text = (
        f"Predators {frame['stats']['predator_count']}, prey {frame['stats']['prey_count']}, "
        f"mean trait {float(frame['stats']['mean_trait'] or 0.0):.3f}."
    )
    draw.text((viewer_box[0] + 18, viewer_box[3] - 44), step_text, fill=PREVIEW_TEXT_MAIN, font=mono_font)
    draw.text((viewer_box[0] + 18, viewer_box[3] - 24), caption_text, fill=PREVIEW_TEXT_MUTED, font=viewer_text_font)

    _draw_chart(
        draw,
        box=trait_chart_box,
        title="Cooperation Rate",
        subtitle="Mean Hunt-Investment Trait",
        step=int(frame["step"]),
        steps_done=int(summary["steps_done"]),
        series_list=[(summary["mean_trait_hist"], PREVIEW_ACCENT_TRAIT)],
        max_value=1.0,
    )

    legend_title_font = _load_preview_font(23, bold=True)
    draw.text((legend_box[0] + 18, legend_box[1] + 14), "GUIDE", fill=PREVIEW_BLUE_STRONG, font=eyebrow_font)
    draw.text((legend_box[0] + 18, legend_box[1] + 31), "Legend", fill=PREVIEW_TEXT_MAIN, font=legend_title_font)
    draw.rectangle(
        (legend_box[0] + 18, legend_box[1] + 66, legend_box[2] - 18, legend_box[3] - 18),
        fill=PREVIEW_ACCENT_PANEL,
        outline=PREVIEW_CARD_BORDER,
        width=1,
    )
    legend_rows = (
        (PREVIEW_GRASS_HIGH, "Grass"),
        (PREVIEW_PREY_COLOR, "Prey"),
        (_blend_rgb(PREVIEW_PREDATOR_LOW, PREVIEW_PREDATOR_HIGH, 0.85), "Predator"),
    )
    for index, (color, label) in enumerate(legend_rows):
        swatch_top = legend_box[1] + 88 + index * 28
        draw.rectangle(
            (legend_box[0] + 30, swatch_top, legend_box[0] + 44, swatch_top + 14),
            fill=color,
            outline=PREVIEW_SWATCH_BORDER,
            width=1,
        )
        draw.text((legend_box[0] + 52, swatch_top - 2), label, fill=PREVIEW_TEXT_MAIN, font=viewer_text_font)

    return image


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


def _write_preview_gif(
    frames: list[dict[str, Any]],
    summary: dict[str, Any],
    *,
    grid_width: int,
    grid_height: int,
    grass_quantization_levels: int,
) -> None:
    selected_frames = frames[::PREVIEW_FRAME_STRIDE]
    if selected_frames[-1]["step"] != frames[-1]["step"]:
        selected_frames.append(frames[-1])
    selected_frame_count = len(selected_frames)

    preview_frames = [
        _render_preview_frame(
            frame,
            frame_index=index,
            sampled_frame_count=selected_frame_count,
            summary=summary,
            grid_width=grid_width,
            grid_height=grid_height,
            grass_quantization_levels=grass_quantization_levels,
        ).quantize(colors=96, method=Image.MEDIANCUT)
        for index, frame in enumerate(selected_frames)
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
        summary,
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
