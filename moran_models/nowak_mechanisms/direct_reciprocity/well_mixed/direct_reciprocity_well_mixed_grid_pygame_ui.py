#!/usr/bin/env python3
"""Display-grid viewer for the well-mixed direct-reciprocity model."""

from __future__ import annotations

import math

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "moran_models.nowak_mechanisms.direct_reciprocity.well_mixed."
        "direct_reciprocity_well_mixed_grid_pygame_ui'."
    )

import pygame

from .config.direct_reciprocity_well_mixed_config import config as model_config
from .direct_reciprocity_well_mixed_model import (
    STRATEGY_IDS,
    STRATEGY_NAMES,
    DirectReciprocityWellMixedModel,
)


STRATEGY_COLORS = {
    "ALLC": (75, 161, 95),
    "ALLD": (185, 63, 63),
    "TFT": (58, 112, 191),
    "GTFT": (112, 88, 181),
    "WSLS": (229, 154, 59),
}

STRATEGY_DISPLAY_NAMES = {
    "ALLC": "Always Cooperate",
    "ALLD": "Always Defect",
    "TFT": "Tit for Tat",
    "GTFT": "Generous Tit for Tat",
    "WSLS": "Win-Stay Lose-Shift",
}


PairSet = set[tuple[int, int]]


def _display_grid_shape(n_sites: int) -> tuple[int, int]:
    columns = max(1, int(math.ceil(math.sqrt(n_sites * 2.0))))
    rows = int(math.ceil(n_sites / columns))
    return columns, rows


def _normalized_pair(pair: tuple[int, int]) -> tuple[int, int]:
    i, j = pair
    return (i, j) if i < j else (j, i)


def _current_pair_set(model: DirectReciprocityWellMixedModel) -> PairSet:
    return {_normalized_pair((int(i), int(j))) for i, j in model.current_pairs}


def _advance_model(
    model: DirectReciprocityWellMixedModel,
    previous_pairs: PairSet,
) -> tuple[PairSet, PairSet, PairSet, PairSet]:
    model.step()
    current_pairs = _current_pair_set(model)
    retained_pairs = current_pairs & previous_pairs
    new_pairs = current_pairs - previous_pairs
    broken_pairs = previous_pairs - current_pairs
    return current_pairs, retained_pairs, new_pairs, broken_pairs


def _cell_center(index: int, columns: int, cell_size: int) -> tuple[int, int]:
    x = index % columns
    y = index // columns
    return x * cell_size + cell_size // 2, y * cell_size + cell_size // 2


def _draw_pair_links(
    screen: pygame.Surface,
    grid_rect: pygame.Rect,
    columns: int,
    cell_size: int,
    current_pairs: PairSet,
    retained_pairs: PairSet,
) -> None:
    link_surface = pygame.Surface((grid_rect.width, grid_rect.height), pygame.SRCALPHA)
    new_pairs = current_pairs - retained_pairs

    for i, j in sorted(new_pairs):
        pygame.draw.line(
            link_surface,
            (34, 69, 112, 42),
            _cell_center(i, columns, cell_size),
            _cell_center(j, columns, cell_size),
            1,
        )

    for i, j in sorted(retained_pairs):
        pygame.draw.line(
            link_surface,
            (20, 41, 72, 115),
            _cell_center(i, columns, cell_size),
            _cell_center(j, columns, cell_size),
            2,
        )

    screen.blit(link_surface, grid_rect.topleft)


def _draw_strategy_grid(
    screen: pygame.Surface,
    model: DirectReciprocityWellMixedModel,
    grid_rect: pygame.Rect,
    columns: int,
    rows: int,
    cell_size: int,
    current_pairs: PairSet,
    retained_pairs: PairSet,
) -> None:
    pygame.draw.rect(screen, (255, 255, 255), grid_rect)

    for index in range(model.n_sites):
        x = index % columns
        y = index // columns
        strategy_name = STRATEGY_NAMES[int(model.strategy[index])]
        cell = pygame.Rect(
            grid_rect.x + x * cell_size,
            grid_rect.y + y * cell_size,
            cell_size,
            cell_size,
        )
        pygame.draw.rect(screen, STRATEGY_COLORS[strategy_name], cell)

    _draw_pair_links(screen, grid_rect, columns, cell_size, current_pairs, retained_pairs)

    grid_color = (222, 229, 238)
    for x in range(columns + 1):
        gx = grid_rect.x + x * cell_size
        pygame.draw.line(screen, grid_color, (gx, grid_rect.y), (gx, grid_rect.bottom), 1)
    for y in range(rows + 1):
        gy = grid_rect.y + y * cell_size
        pygame.draw.line(screen, grid_color, (grid_rect.x, gy), (grid_rect.right, gy), 1)

    pygame.draw.rect(screen, (186, 198, 214), grid_rect, 1)


def _chart_areas(rect: pygame.Rect) -> tuple[int, int, int, int]:
    lm, rm, tm, bm = 28, 6, 10, 14
    return rect.x + lm, rect.y + tm, rect.width - lm - rm, rect.height - tm - bm


def _draw_axes(
    screen: pygame.Surface,
    rect: pygame.Rect,
    font: pygame.font.Font,
) -> None:
    plot_x, plot_y, plot_w, plot_h = _chart_areas(rect)
    ax_color = (120, 140, 160)
    grid_color = (220, 228, 238)
    label_color = (80, 95, 110)

    pygame.draw.line(screen, ax_color, (plot_x, plot_y), (plot_x, plot_y + plot_h), 1)
    pygame.draw.line(screen, ax_color, (plot_x, plot_y + plot_h), (plot_x + plot_w, plot_y + plot_h), 1)

    for val, label_str in [(0.0, "0"), (1.0, "1")]:
        ty = plot_y + plot_h - int(val * plot_h)
        if val > 0.0:
            pygame.draw.line(screen, grid_color, (plot_x + 1, ty), (plot_x + plot_w, ty), 1)
        pygame.draw.line(screen, ax_color, (plot_x - 3, ty), (plot_x, ty), 1)
        lbl = font.render(label_str, True, label_color)
        screen.blit(lbl, (plot_x - 4 - lbl.get_width(), ty - lbl.get_height() // 2))


def _draw_sparkline(
    screen: pygame.Surface,
    history: list[dict[str, float]],
    rect: pygame.Rect,
    metric: str,
    color: tuple[int, int, int],
    font: pygame.font.Font,
) -> None:
    pygame.draw.rect(screen, (255, 255, 255), rect)
    pygame.draw.rect(screen, (208, 219, 234), rect, 1)
    _draw_axes(screen, rect, font)
    if len(history) < 2:
        return

    plot_x, plot_y, plot_w, plot_h = _chart_areas(rect)
    values = [max(0.0, min(1.0, float(row[metric]))) for row in history]
    points = [
        (
            plot_x + int(i * plot_w / max(1, len(values) - 1)),
            plot_y + plot_h - int(v * plot_h),
        )
        for i, v in enumerate(values)
    ]
    if len(points) >= 2:
        pygame.draw.lines(screen, color, False, points, 2)


def _draw_strategy_frequencies_chart(
    screen: pygame.Surface,
    history: list[dict[str, float]],
    rect: pygame.Rect,
    font: pygame.font.Font,
) -> None:
    pygame.draw.rect(screen, (255, 255, 255), rect)
    pygame.draw.rect(screen, (208, 219, 234), rect, 1)
    _draw_axes(screen, rect, font)
    if len(history) < 2:
        return

    plot_x, plot_y, plot_w, plot_h = _chart_areas(rect)
    for name in STRATEGY_NAMES:
        metric = f"{name}_frequency"
        color = STRATEGY_COLORS[name]
        values = [max(0.0, min(1.0, float(row.get(metric, 0.0)))) for row in history]
        points = [
            (
                plot_x + int(i * plot_w / max(1, len(values) - 1)),
                plot_y + plot_h - int(v * plot_h),
            )
            for i, v in enumerate(values)
        ]
        if len(points) >= 2:
            pygame.draw.lines(screen, color, False, points, 2)


def _draw_panel_text(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int] = (31, 45, 61),
) -> int:
    label = font.render(text, True, color)
    screen.blit(label, (x, y))
    return y + label.get_height() + 6


def _latest(model: DirectReciprocityWellMixedModel, key: str) -> float:
    if not model.history:
        return 0.0
    return float(model.history[-1][key])


def main() -> None:
    cfg = dict(model_config)
    model = DirectReciprocityWellMixedModel(cfg)

    columns, rows = _display_grid_shape(model.n_sites)
    cell_size = 28
    margin = 16
    header_height = 96
    grid_padding = 20
    side_panel_width = 420
    grid_w = columns * cell_size
    grid_h = rows * cell_size
    left_panel_width = grid_w + grid_padding * 2
    main_h = max(grid_h + 150, 520)
    window_w = margin * 3 + left_panel_width + side_panel_width
    window_h = margin * 2 + header_height + main_h

    pygame.init()
    pygame.display.set_caption("Direct Reciprocity Well-Mixed Display Grid")
    screen = pygame.display.set_mode((window_w, window_h))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 34)
    body_font = pygame.font.SysFont(None, 23)
    small_font = pygame.font.SysFont(None, 21)

    left_panel_rect = pygame.Rect(margin, margin + header_height, left_panel_width, main_h)
    grid_rect = pygame.Rect(
        left_panel_rect.x + grid_padding,
        left_panel_rect.y + 72,
        grid_w,
        grid_h,
    )
    panel_rect = pygame.Rect(left_panel_rect.right + margin, left_panel_rect.y, side_panel_width, main_h)

    previous_pairs: PairSet = set()
    current_pairs: PairSet = set()
    retained_pairs: PairSet = set()
    new_pairs: PairSet = set()
    broken_pairs: PairSet = set()

    running = True
    paused = False
    frame_fps = 20
    max_steps = int(cfg["simulation_steps"])
    step_count = 0

    while running:
        advanced_this_frame = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_n and step_count < max_steps:
                    current_pairs, retained_pairs, new_pairs, broken_pairs = _advance_model(model, previous_pairs)
                    previous_pairs = current_pairs
                    step_count += 1
                    advanced_this_frame = True
                elif event.key == pygame.K_r:
                    model = DirectReciprocityWellMixedModel(cfg)
                    previous_pairs = set()
                    current_pairs = set()
                    retained_pairs = set()
                    new_pairs = set()
                    broken_pairs = set()
                    step_count = 0
                    paused = False
                elif event.key == pygame.K_UP:
                    frame_fps = min(120, frame_fps + 1)
                elif event.key == pygame.K_DOWN:
                    frame_fps = max(1, frame_fps - 1)

        if not paused and not advanced_this_frame and step_count < max_steps:
            current_pairs, retained_pairs, new_pairs, broken_pairs = _advance_model(model, previous_pairs)
            previous_pairs = current_pairs
            step_count += 1
        if step_count >= max_steps:
            paused = True

        screen.fill((248, 250, 255))
        pygame.draw.rect(screen, (15, 51, 104), (0, 0, window_w, margin + header_height))
        title = title_font.render(
            "Direct Reciprocity - Well-Mixed Model - Display-Only Grid",
            True,
            (255, 255, 255),
        )
        subtitle = small_font.render(
            "space play/pause | n step | r reset | up/down fps | esc quit",
            True,
            (255, 255, 255),
        )
        screen.blit(title, (margin, margin + 14))
        screen.blit(subtitle, (margin, margin + 52))

        pygame.draw.rect(screen, (234, 242, 251), left_panel_rect)
        pygame.draw.rect(screen, (208, 219, 234), left_panel_rect, 1)
        lx = left_panel_rect.x + grid_padding
        ly = left_panel_rect.y + 16
        ly = _draw_panel_text(screen, body_font, "Agent Display Grid", lx, ly)
        ly = _draw_panel_text(
            screen,
            small_font,
            "Grid position is fixed by agent id; pair links are global.",
            lx,
            ly,
            (80, 95, 110),
        )

        _draw_strategy_grid(
            screen,
            model,
            grid_rect,
            columns,
            rows,
            cell_size,
            current_pairs,
            retained_pairs,
        )

        legend_y = grid_rect.bottom + 18
        _draw_panel_text(screen, small_font, "Pair links", lx, legend_y)
        legend_y += 26
        pygame.draw.line(screen, (34, 69, 112), (lx, legend_y), (lx + 34, legend_y), 1)
        _draw_panel_text(screen, small_font, "new or reshuffled pair", lx + 46, legend_y - 9)
        legend_y += 28
        pygame.draw.line(screen, (20, 41, 72), (lx, legend_y), (lx + 34, legend_y), 3)
        _draw_panel_text(screen, small_font, "retained pair", lx + 46, legend_y - 9)

        pygame.draw.rect(screen, (234, 242, 251), panel_rect)
        pygame.draw.rect(screen, (208, 219, 234), panel_rect, 1)

        px = panel_rect.x + 16
        py = panel_rect.y + 16
        panel_inner_w = panel_rect.width - 32
        mode = "paused" if paused else "running"
        p_value = float(cfg["partner_persistence_probability"])
        retained_fraction = len(retained_pairs) / max(1, len(current_pairs))

        py = _draw_panel_text(screen, body_font, f"step={step_count} / {max_steps}  fps={frame_fps}  {mode}", px, py)
        py = _draw_panel_text(screen, body_font, f"cooperation rate={_latest(model, 'mean_cooperation_rate'):.3f}", px, py)
        py = _draw_panel_text(screen, body_font, f"p={p_value:.2f}  retained pairs={retained_fraction:.3f}", px, py)
        py = _draw_panel_text(
            screen,
            small_font,
            f"pairs={len(current_pairs)}  new={len(new_pairs)}  broken={len(broken_pairs)}",
            px,
            py,
        )

        py += 4
        chart_h = 80
        py = _draw_panel_text(screen, small_font, "Cooperation Rate", px, py)
        coop_rect = pygame.Rect(px, py, panel_inner_w, chart_h)
        _draw_sparkline(screen, model.history, coop_rect, "mean_cooperation_rate", (58, 112, 191), small_font)
        py = coop_rect.bottom + 10

        py = _draw_panel_text(screen, small_font, "Strategy Frequencies", px, py)
        freq_rect = pygame.Rect(px, py, panel_inner_w, chart_h)
        _draw_strategy_frequencies_chart(screen, model.history, freq_rect, small_font)
        py = freq_rect.bottom + 10

        py = _draw_panel_text(screen, small_font, "Legend", px, py)
        for name in STRATEGY_NAMES:
            color = STRATEGY_COLORS[name]
            pygame.draw.rect(screen, color, pygame.Rect(px, py + 3, 16, 16))
            freq = float(model.strategy.tolist().count(STRATEGY_IDS[name]) / model.n_sites)
            py = _draw_panel_text(
                screen,
                small_font,
                f"{STRATEGY_DISPLAY_NAMES[name]}: {freq:.3f}",
                px + 24,
                py,
            )

        py += 8
        notes = [
            f"n={model.n_sites}; display grid={columns}x{rows}.",
            f"Rounds per pair: {cfg['rounds_per_pair_per_step']}.",
            "Spatial location does not affect interaction or replacement.",
        ]
        for line in notes:
            py = _draw_panel_text(screen, small_font, line, px, py)

        pygame.display.flip()
        clock.tick(frame_fps)

    pygame.quit()


if __name__ == "__main__":
    main()
