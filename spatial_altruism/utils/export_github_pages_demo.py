#!/usr/bin/env python3
"""
Export a sampled replay bundle for the GitHub Pages spatial-altruism demo.

Run from the repository root with:
  ./.conda/bin/python -m spatial_altruism.utils.export_github_pages_demo
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m spatial_altruism.utils.export_github_pages_demo'."
    )

from ..altruism_model import AltruismModel, make_params
from ..config.altruism_config import resolve_config
from ..config.altruism_website_demo_config import config as website_demo_config


DEMO_OUTPUT_DIR = Path("docs/data/spatial-altruism-demo")
PREVIEW_GIF_PATH = Path("assets/spatial_altruism/spatial_altruism_demo_preview.gif")
SAMPLE_EVERY_STEPS = 4
FRAME_CHUNK_SIZE = 40
ROUND_DIGITS = 6
FRAME_STAT_DIGITS = 4
PREVIEW_FRAME_STRIDE = 3
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
PREVIEW_WORLD_CELL_SIZE = 6
PREVIEW_PAGE_BG = (255, 255, 255)
PREVIEW_CARD_BG = (247, 251, 255)
PREVIEW_CARD_BORDER = (214, 228, 245)
PREVIEW_TEXT_MAIN = (31, 45, 61)
PREVIEW_TEXT_MUTED = (78, 98, 121)
PREVIEW_BLUE_STRONG = (15, 51, 104)
PREVIEW_BLUE_MID = (28, 75, 143)
PREVIEW_BLUE_SOFT = (120, 170, 230)
PREVIEW_WHITE = (255, 255, 255)
PREVIEW_ACCENT_PANEL = (234, 242, 251)
PREVIEW_CHART_BG = (255, 255, 255)
PREVIEW_CHART_GRID = (214, 228, 245)
PREVIEW_CHART_AXIS = (115, 143, 178)
PREVIEW_CHART_MARKER = (15, 51, 104)
PREVIEW_EMPTY = (244, 239, 229)
PREVIEW_EMPTY_LINE = (139, 123, 96)
PREVIEW_SELFISH = (45, 95, 186)
PREVIEW_ALTRUIST = (171, 53, 87)
PREVIEW_GRID_MINOR = (224, 230, 224)
PREVIEW_GRID_MAJOR = (176, 192, 176)
PREVIEW_SWATCH_BORDER = (15, 51, 104)
PREVIEW_FONT_CACHE: dict[tuple[int, bool, bool], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}
SELECTED_CONFIG_KEYS = (
    "width",
    "height",
    "torus",
    "model_variant",
    "altruistic_probability",
    "selfish_probability",
    "benefit_from_altruism",
    "cost_of_altruism",
    "disease",
    "harshness",
    "uniform_culling_interval",
    "uniform_culling_fraction",
    "seed",
    "demo_steps",
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
) -> None:
    draw.rectangle(box, fill=fill, outline=fill, width=1)
    font = _load_preview_font(13, mono=True)
    text_width, text_height = _text_box_size(draw, text, font)
    text_x = box[0] + (box[2] - box[0] - text_width) / 2
    text_y = box[1] + (box[3] - box[1] - text_height) / 2 - 1
    draw.text((text_x, text_y), text, fill=text_fill, font=font)


def _draw_world_canvas(
    frame: dict[str, Any],
    *,
    grid_width: int,
    grid_height: int,
    major_step: int,
) -> Image.Image:
    image = Image.new(
        "RGB",
        (grid_width * PREVIEW_WORLD_CELL_SIZE, grid_height * PREVIEW_WORLD_CELL_SIZE),
        PREVIEW_EMPTY,
    )
    draw = ImageDraw.Draw(image)
    state_to_color = {
        0: PREVIEW_EMPTY,
        1: PREVIEW_SELFISH,
        2: PREVIEW_ALTRUIST,
    }

    for y in range(grid_height):
        for x in range(grid_width):
            state = int(frame["patches"][y * grid_width + x])
            left = x * PREVIEW_WORLD_CELL_SIZE
            top = y * PREVIEW_WORLD_CELL_SIZE
            draw.rectangle(
                (
                    left,
                    top,
                    left + PREVIEW_WORLD_CELL_SIZE - 1,
                    top + PREVIEW_WORLD_CELL_SIZE - 1,
                ),
                fill=state_to_color.get(state, PREVIEW_EMPTY),
            )

    full_width = grid_width * PREVIEW_WORLD_CELL_SIZE
    full_height = grid_height * PREVIEW_WORLD_CELL_SIZE
    for x in range(grid_width + 1):
        color = PREVIEW_GRID_MAJOR if x % major_step == 0 else PREVIEW_GRID_MINOR
        line_width = 2 if x % major_step == 0 else 1
        x_pix = x * PREVIEW_WORLD_CELL_SIZE
        draw.line((x_pix, 0, x_pix, full_height), fill=color, width=line_width)
    for y in range(grid_height + 1):
        color = PREVIEW_GRID_MAJOR if y % major_step == 0 else PREVIEW_GRID_MINOR
        line_width = 2 if y % major_step == 0 else 1
        y_pix = y * PREVIEW_WORLD_CELL_SIZE
        draw.line((0, y_pix, full_width, y_pix), fill=color, width=line_width)

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
    subtitle: str,
    step: int,
    steps_done: int,
    series_list: list[tuple[list[float | None], tuple[int, int, int], str]],
    max_value: float,
) -> None:
    _draw_card(draw, box)
    x0, y0, x1, y1 = box
    title_font = _load_preview_font(22, bold=True)
    subtitle_font = _load_preview_font(13)
    legend_font = _load_preview_font(12)
    tick_font = _load_preview_font(11, mono=True)

    draw.text((x0 + 18, y0 + 18), title, fill=PREVIEW_TEXT_MAIN, font=title_font)
    draw.text((x0 + 18, y0 + 46), subtitle, fill=PREVIEW_TEXT_MUTED, font=subtitle_font)

    legend_x = x0 + 18
    legend_y = y0 + 68
    for _, color, label in series_list:
        draw.line((legend_x, legend_y + 8, legend_x + 18, legend_y + 8), fill=color, width=3)
        draw.text((legend_x + 24, legend_y), label, fill=PREVIEW_TEXT_MAIN, font=legend_font)
        legend_x += 24 + _text_box_size(draw, label, legend_font)[0] + 18

    plot_box = (x0 + 46, y0 + 100, x1 - 18, y1 - 28)
    draw.rectangle(plot_box, fill=PREVIEW_CHART_BG, outline=PREVIEW_CARD_BORDER, width=1)

    for grid_index in range(5):
        grid_y = plot_box[1] + grid_index * (plot_box[3] - plot_box[1]) / 4
        draw.line((plot_box[0], grid_y, plot_box[2], grid_y), fill=PREVIEW_CHART_GRID, width=1)

    draw.line((plot_box[0], plot_box[1], plot_box[0], plot_box[3]), fill=PREVIEW_CHART_AXIS, width=1)
    draw.line((plot_box[0], plot_box[3], plot_box[2], plot_box[3]), fill=PREVIEW_CHART_AXIS, width=1)

    for tick_index in range(5):
        ratio = tick_index / 4
        tick_value = max_value * (1 - ratio)
        tick_y = plot_box[1] + ratio * (plot_box[3] - plot_box[1])
        tick_text = f"{tick_value:.0f}"
        tick_width, tick_height = _text_box_size(draw, tick_text, tick_font)
        draw.text(
            (plot_box[0] - 8 - tick_width, tick_y - tick_height / 2),
            tick_text,
            fill=PREVIEW_TEXT_MUTED,
            font=tick_font,
        )

    for values, color, _ in series_list:
        _draw_series_line(draw, plot_box=plot_box, values=values, color=color, max_value=max_value)

    marker_ratio = 0.0 if steps_done <= 0 else max(0.0, min(1.0, step / steps_done))
    marker_x = plot_box[0] + marker_ratio * (plot_box[2] - plot_box[0])
    draw.line((marker_x, plot_box[1], marker_x, plot_box[3]), fill=PREVIEW_CHART_MARKER, width=2)

    end_label = f"{steps_done}"
    draw.text((plot_box[0], plot_box[3] + 6), "0", fill=PREVIEW_TEXT_MUTED, font=tick_font)
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
    grid_major_step: int,
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
    chart_box = (
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
        "Spatial Altruism",
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
    _draw_chip(draw, play_button_box, text="Play", fill=PREVIEW_BLUE_MID, text_fill=PREVIEW_WHITE)
    _draw_chip(draw, restart_button_box, text="Restart", fill=PREVIEW_BLUE_SOFT, text_fill=PREVIEW_WHITE)
    _draw_chip(draw, speed_box, text="8 fps", fill=PREVIEW_BLUE_SOFT, text_fill=PREVIEW_WHITE)
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

    world_rect = (
        viewer_box[0] + 18,
        viewer_box[1] + 146,
        viewer_box[0] + 18 + grid_width * PREVIEW_WORLD_CELL_SIZE,
        viewer_box[1] + 146 + grid_height * PREVIEW_WORLD_CELL_SIZE,
    )
    world_canvas = _draw_world_canvas(
        frame,
        grid_width=grid_width,
        grid_height=grid_height,
        major_step=grid_major_step,
    )
    draw.rectangle(
        (world_rect[0] - 2, world_rect[1] - 2, world_rect[2] + 2, world_rect[3] + 2),
        fill=PREVIEW_ACCENT_PANEL,
        outline=PREVIEW_CARD_BORDER,
        width=1,
    )
    image.paste(world_canvas, (world_rect[0], world_rect[1]))

    step_text = f"Step {frame['step']}"
    occupied_fraction = float(frame["stats"]["occupied_fraction"] or 0.0)
    caption_text = (
        f"Altruists {frame['stats']['altruist_count']}, selfish {frame['stats']['selfish_count']}, "
        f"empty {frame['stats']['empty_count']} ({occupied_fraction:.1%} occupied)."
    )
    draw.text((viewer_box[0] + 18, viewer_box[3] - 44), step_text, fill=PREVIEW_TEXT_MAIN, font=mono_font)
    draw.text((viewer_box[0] + 18, viewer_box[3] - 24), caption_text, fill=PREVIEW_TEXT_MUTED, font=viewer_text_font)

    _draw_chart(
        draw,
        box=chart_box,
        title="Population Balance",
        subtitle="Altruist, selfish, and empty patch counts",
        step=int(frame["step"]),
        steps_done=int(summary["steps_done"]),
        series_list=[
            (summary["altruist_hist"], PREVIEW_ALTRUIST, "Altruist"),
            (summary["selfish_hist"], PREVIEW_SELFISH, "Selfish"),
            (summary["empty_hist"], PREVIEW_EMPTY_LINE, "Empty"),
        ],
        max_value=float(grid_width * grid_height),
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
        (PREVIEW_ALTRUIST, "Altruist patches"),
        (PREVIEW_SELFISH, "Selfish patches"),
        (PREVIEW_EMPTY, "Empty patches"),
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

    note = "Chart lines use the same state colors as the lattice."
    draw.text((legend_box[0] + 30, legend_box[3] - 38), note, fill=PREVIEW_TEXT_MUTED, font=viewer_text_font)
    return image


def _build_demo_config() -> dict[str, Any]:
    cfg = resolve_config(website_demo_config)
    cfg["demo_plot_enabled"] = False
    cfg["ui_history_visible_default"] = True
    return cfg


def _serialize_frame(model: AltruismModel, *, step: int) -> dict[str, Any]:
    altruist_count, selfish_count, empty_count = model.counts()
    total = altruist_count + selfish_count + empty_count
    occupied = altruist_count + selfish_count
    return {
        "step": int(step),
        "patches": model.pcolor.astype(int, copy=False).ravel().tolist(),
        "stats": {
            "altruist_count": altruist_count,
            "selfish_count": selfish_count,
            "empty_count": empty_count,
            "occupied_fraction": _round_number(occupied / max(total, 1), FRAME_STAT_DIGITS),
            "altruist_share_of_occupied": _round_number(altruist_count / max(occupied, 1), FRAME_STAT_DIGITS),
            "selfish_share_of_occupied": _round_number(selfish_count / max(occupied, 1), FRAME_STAT_DIGITS),
        },
    }


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


def _run_sampled_demo(cfg: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    model = AltruismModel(make_params(cfg))
    initial_altruists, initial_selfish, initial_empty = model.counts()
    altruist_hist: list[float | None] = [float(initial_altruists)]
    selfish_hist: list[float | None] = [float(initial_selfish)]
    empty_hist: list[float | None] = [float(initial_empty)]
    occupied_fraction_hist: list[float | None] = [
        _round_number((initial_altruists + initial_selfish) / max(initial_altruists + initial_selfish + initial_empty, 1))
    ]
    frames = [_serialize_frame(model, step=0)]
    extinction_step: int | None = None

    for step in range(1, int(cfg["demo_steps"]) + 1):
        before_tick = model.ticks
        alive = model.go()
        after_tick = model.ticks

        if after_tick > before_tick:
            altruists, selfish, empty = model.counts()
            altruist_hist.append(float(altruists))
            selfish_hist.append(float(selfish))
            empty_hist.append(float(empty))
            occupied_fraction_hist.append(
                _round_number((altruists + selfish) / max(altruists + selfish + empty, 1))
            )
            if after_tick % SAMPLE_EVERY_STEPS == 0 or after_tick == int(cfg["demo_steps"]):
                frames.append(_serialize_frame(model, step=after_tick))

        if not alive:
            extinction_step = after_tick
            if frames[-1]["step"] != after_tick:
                frames.append(_serialize_frame(model, step=after_tick))
            break

        if step % 100 == 0:
            altruists, selfish, empty = model.counts()
            print(
                f"export step={after_tick:4d} "
                f"altruists={altruists:4d} selfish={selfish:4d} empty={empty:4d}"
            )

    steps_done = int(model.ticks)
    final_altruists, final_selfish, final_empty = model.counts()
    success = extinction_step is None and steps_done == int(cfg["demo_steps"])
    summary = {
        "altruist_hist": altruist_hist,
        "selfish_hist": selfish_hist,
        "empty_hist": empty_hist,
        "occupied_fraction_hist": occupied_fraction_hist,
        "sampled_steps": [int(frame["step"]) for frame in frames],
        "steps_done": steps_done,
        "success": success,
        "extinction_step": extinction_step,
        "final_altruist_count": final_altruists,
        "final_selfish_count": final_selfish,
        "final_empty_count": final_empty,
        "final_occupied_fraction": _round_number(
            (final_altruists + final_selfish) / max(final_altruists + final_selfish + final_empty, 1),
            FRAME_STAT_DIGITS,
        ),
    }
    return summary, frames


def _write_preview_gif(
    frames: list[dict[str, Any]],
    summary: dict[str, Any],
    *,
    grid_width: int,
    grid_height: int,
    grid_major_step: int,
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
            grid_major_step=grid_major_step,
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
        grid_width=int(cfg["width"]),
        grid_height=int(cfg["height"]),
        grid_major_step=5,
    )
    summary_path = DEMO_OUTPUT_DIR / "summary.json"
    _write_json(summary_path, summary, pretty=True)

    manifest = {
        "format_version": 1,
        "title": "Spatial Altruism",
        "description": (
            "Sampled replay generated from the frozen website-demo configuration. "
            "The browser viewer replays exported states; it does not rerun the Python model."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "config_source": "spatial_altruism/config/altruism_website_demo_config.py",
        "sample_every_steps": SAMPLE_EVERY_STEPS,
        "frame_chunk_size": FRAME_CHUNK_SIZE,
        "sampled_frame_count": len(frames),
        "grid_width": int(cfg["width"]),
        "grid_height": int(cfg["height"]),
        "grid_major_step": 5,
        "simulation_steps": int(cfg["demo_steps"]),
        "random_seed": cfg["seed"],
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
    print(f"Wrote preview GIF to {PREVIEW_GIF_PATH}.")


if __name__ == "__main__":
    main()
