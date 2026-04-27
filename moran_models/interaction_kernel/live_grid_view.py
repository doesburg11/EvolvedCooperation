#!/usr/bin/env python3
"""Reusable live grid viewer for shared Moran interaction mechanisms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pygame


@dataclass(frozen=True)
class UiConfig:
    cell_size: int = 24
    margin: int = 16
    header_height: int = 96
    footer_height: int = 16
    side_panel_width: int = 380
    default_fps: int = 20
    max_fps: int = 120
    min_fps: int = 1


UI = UiConfig()


def _trait_to_rgb(value: float) -> tuple[int, int, int]:
    """Map trait in [0, 1] to a blue -> orange gradient."""
    v = max(0.0, min(1.0, float(value)))
    low = (35, 88, 196)
    high = (229, 118, 42)
    return (
        int(low[0] + (high[0] - low[0]) * v),
        int(low[1] + (high[1] - low[1]) * v),
        int(low[2] + (high[2] - low[2]) * v),
    )


def _draw_trait_grid(
    screen: pygame.Surface,
    model: Any,
    grid_rect: pygame.Rect,
    cell_size: int,
) -> None:
    trait_grid = model.h.reshape(model.height, model.width)
    for y in range(model.height):
        for x in range(model.width):
            val = float(trait_grid[y, x])
            color = _trait_to_rgb(val)
            cell = pygame.Rect(
                grid_rect.x + x * cell_size,
                grid_rect.y + y * cell_size,
                cell_size,
                cell_size,
            )
            pygame.draw.rect(screen, color, cell)
    for x in range(model.width + 1):
        gx = grid_rect.x + x * cell_size
        pygame.draw.line(screen, (220, 226, 236), (gx, grid_rect.y), (gx, grid_rect.bottom), 1)
    for y in range(model.height + 1):
        gy = grid_rect.y + y * cell_size
        pygame.draw.line(screen, (220, 226, 236), (grid_rect.x, gy), (grid_rect.right, gy), 1)


def _latest_stats(model: Any, cfg: dict[str, Any]) -> tuple[float, float]:
    if model.history:
        latest = model.history[-1]
        return float(latest["mean_trait"]), float(latest["mean_fitness"])
    return float(model.h.mean()), float(cfg["base_fitness"])


def _status_text(model: Any, cfg: dict[str, Any], paused: bool, fps: int, step_count: int) -> str:
    mean_trait, mean_fitness = _latest_stats(model, cfg)
    mode = "paused" if paused else "running"
    return (
        f"step={step_count}  mean_trait={mean_trait:.4f}  "
        f"mean_fitness={mean_fitness:.4f}  fps={fps}  mode={mode}"
    )


def _wrap_text_lines(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wrap a line of text to fit within a maximum pixel width."""
    words = text.split()
    if not words:
        return [""]

    wrapped: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            wrapped.append(current)
            current = word
    wrapped.append(current)
    return wrapped


def _draw_mean_trait_sparkline(
    screen: pygame.Surface,
    history: list[dict[str, float]],
    chart_rect: pygame.Rect,
    font: pygame.font.Font,
    step_count: int,
) -> None:
    pygame.draw.rect(screen, (255, 255, 255), chart_rect)
    pygame.draw.rect(screen, (210, 220, 238), chart_rect, 1)

    left_pad = 44
    right_pad = 10
    top_pad = 10
    bottom_pad = 28
    plot_rect = pygame.Rect(
        chart_rect.x + left_pad,
        chart_rect.y + top_pad,
        chart_rect.width - left_pad - right_pad,
        chart_rect.height - top_pad - bottom_pad,
    )

    axis_color = (120, 170, 230)
    pygame.draw.line(screen, axis_color, (plot_rect.x, plot_rect.y), (plot_rect.x, plot_rect.bottom), 2)
    pygame.draw.line(
        screen,
        axis_color,
        (plot_rect.x, plot_rect.bottom),
        (plot_rect.right, plot_rect.bottom),
        2,
    )

    y_ticks = [0.0, 0.25, 0.5, 0.75, 1.0]
    grid_color = (214, 228, 245)
    text_color = (31, 45, 61)
    for tick in y_ticks:
        y = plot_rect.bottom - int(tick * plot_rect.height)
        pygame.draw.line(screen, axis_color, (plot_rect.x - 5, y), (plot_rect.x, y), 1)
        if tick > 0.0:
            pygame.draw.line(screen, grid_color, (plot_rect.x, y), (plot_rect.right, y), 1)
        label = font.render(f"{tick:.2f}", True, text_color)
        screen.blit(label, (chart_rect.x + 4, y - 8))

    x_max = max(1, step_count)
    x_ticks = [0, x_max // 2, x_max]
    for tick in x_ticks:
        frac = tick / x_max
        x = plot_rect.x + int(frac * plot_rect.width)
        pygame.draw.line(screen, axis_color, (x, plot_rect.bottom), (x, plot_rect.bottom + 5), 1)
        label = font.render(str(tick), True, text_color)
        screen.blit(label, (x - label.get_width() // 2, plot_rect.bottom + 8))

    if len(history) < 2:
        return

    values = [max(0.0, min(1.0, float(step["mean_trait"]))) for step in history]
    points: list[tuple[int, int]] = []
    for i, value in enumerate(values):
        x = plot_rect.x + int(i * (plot_rect.width - 1) / max(1, len(values) - 1))
        y = plot_rect.bottom - int(value * (plot_rect.height - 1))
        points.append((x, y))

    if len(points) >= 2:
        pygame.draw.lines(screen, (28, 75, 143), False, points, 2)


def run_live_grid_view(
    *,
    model_class: type,
    model_config: dict[str, Any],
    window_caption: str,
    header_title: str,
    explanation_builder: Callable[[dict[str, Any]], list[str]],
) -> None:
    """Run the shared live grid viewer for a named mechanism package."""
    cfg = dict(model_config)
    model = model_class(cfg)

    grid_w = model.width * UI.cell_size
    grid_h = model.height * UI.cell_size
    window_w = UI.margin * 3 + grid_w + UI.side_panel_width
    window_h = UI.margin * 2 + UI.header_height + grid_h + UI.footer_height

    pygame.init()
    pygame.display.set_caption(window_caption)
    screen = pygame.display.set_mode((window_w, window_h))
    clock = pygame.time.Clock()

    color_primary_blue = (15, 51, 104)
    color_pale_surface = (234, 242, 251)
    color_border = (214, 228, 245)
    color_body_text = (31, 45, 61)
    color_white = (255, 255, 255)

    title_font = pygame.font.SysFont(None, 34)
    body_font = pygame.font.SysFont(None, 24)
    hint_font = pygame.font.SysFont(None, 22)

    grid_rect = pygame.Rect(UI.margin, UI.margin + UI.header_height, grid_w, grid_h)
    panel_rect = pygame.Rect(grid_rect.right + UI.margin, grid_rect.y, UI.side_panel_width, grid_h)

    running = True
    paused = False
    frame_fps = UI.default_fps
    step_count = 0
    max_steps = int(cfg["simulation_steps"])

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    model = model_class(cfg)
                    step_count = 0
                    paused = False
                elif event.key == pygame.K_n:
                    if step_count < max_steps:
                        model.step()
                        step_count += 1
                elif event.key == pygame.K_UP:
                    frame_fps = min(UI.max_fps, frame_fps + 1)
                elif event.key == pygame.K_DOWN:
                    frame_fps = max(UI.min_fps, frame_fps - 1)

        if not paused and step_count < max_steps:
            model.step()
            step_count += 1
        if step_count >= max_steps:
            paused = True

        screen.fill((248, 250, 255))
        pygame.draw.rect(screen, color_primary_blue, (0, 0, window_w, UI.margin + UI.header_height))

        title = title_font.render(header_title, True, color_white)
        subtitle = hint_font.render(
            "space play/pause | n single-step | r reset | up/down fps | esc quit",
            True,
            color_white,
        )
        screen.blit(title, (UI.margin, UI.margin + 14))
        screen.blit(subtitle, (UI.margin, UI.margin + 52))

        _draw_trait_grid(screen, model, grid_rect, UI.cell_size)
        pygame.draw.rect(screen, color_pale_surface, panel_rect)
        pygame.draw.rect(screen, color_border, panel_rect, 1)

        mean_trait, mean_fitness = _latest_stats(model, cfg)
        if len(model.history) >= 30:
            delta = float(model.history[-1]["mean_trait"] - model.history[-30]["mean_trait"])
        elif len(model.history) >= 2:
            delta = float(model.history[-1]["mean_trait"] - model.history[0]["mean_trait"])
        else:
            delta = 0.0
        trend_word = "rising" if delta > 0.0 else ("falling" if delta < 0.0 else "flat")

        panel_inner_x = panel_rect.x + 16
        panel_inner_w = panel_rect.width - 32
        panel_inner_bottom = panel_rect.bottom - 16

        chart_height = 150
        chart_rect = pygame.Rect(panel_inner_x, panel_inner_bottom - chart_height, panel_inner_w, chart_height)
        chart_title_y = chart_rect.y - 28

        stats_lines = [
            f"Step: {step_count} / {max_steps}",
            f"Mean trait h: {mean_trait:.4f}",
            f"Mean fitness: {mean_fitness:.4f}",
            f"Recent trend (about 30 steps): {trend_word} ({delta:+.4f})",
        ]
        stats_line_height = 24
        stats_block_h = len(stats_lines) * stats_line_height
        stats_y = chart_title_y - 10 - stats_block_h

        swatch_size = 24
        legend_gap = 2
        legend_top = stats_y - 14 - (swatch_size * 2 + legend_gap)
        swatch_y = legend_top

        expl_box_rect = pygame.Rect(
            panel_rect.x + 8,
            panel_rect.y + 8,
            panel_rect.width - 16,
            max(40, legend_top - panel_rect.y - 16),
        )
        color_secondary_blue = (28, 75, 143)
        pygame.draw.rect(screen, color_secondary_blue, expl_box_rect, 2)

        panel_title = body_font.render("What is happening", True, color_primary_blue)
        screen.blit(panel_title, (expl_box_rect.x + 8, expl_box_rect.y + 8))

        expl_lines = explanation_builder(cfg)
        line_height = 22
        text_x = expl_box_rect.x + 8
        text_max_width = expl_box_rect.width - 16
        text_top = expl_box_rect.y + 38
        text_bottom = expl_box_rect.bottom - 8

        wrapped_lines: list[str] = []
        for line in expl_lines:
            wrapped_lines.extend(_wrap_text_lines(line, hint_font, text_max_width))

        line_y = text_top
        for line in wrapped_lines:
            if line_y + line_height > text_bottom:
                break
            rendered = hint_font.render(line, True, color_body_text)
            screen.blit(rendered, (text_x, line_y))
            line_y += line_height

        pygame.draw.rect(screen, _trait_to_rgb(0.0), (panel_inner_x, swatch_y, swatch_size, swatch_size))
        low_label = hint_font.render("h = 0.0 (low cooperation)", True, color_body_text)
        low_label_y = swatch_y + (swatch_size - low_label.get_height()) // 2
        screen.blit(low_label, (panel_inner_x + 32, low_label_y))

        second_swatch_y = swatch_y + swatch_size + legend_gap
        pygame.draw.rect(
            screen,
            _trait_to_rgb(1.0),
            (panel_inner_x, second_swatch_y, swatch_size, swatch_size),
        )
        high_label = hint_font.render("h = 1.0 (high cooperation)", True, color_body_text)
        high_label_y = second_swatch_y + (swatch_size - high_label.get_height()) // 2
        screen.blit(high_label, (panel_inner_x + 32, high_label_y))

        for line in stats_lines:
            rendered = hint_font.render(line, True, color_primary_blue)
            screen.blit(rendered, (panel_inner_x, stats_y))
            stats_y += stats_line_height

        chart_title = hint_font.render("Mean cooperation over time", True, color_primary_blue)
        screen.blit(chart_title, (panel_inner_x, chart_title_y))
        _draw_mean_trait_sparkline(screen, model.history, chart_rect, hint_font, step_count)

        status = body_font.render(_status_text(model, cfg, paused, frame_fps, step_count), True, color_body_text)
        screen.blit(status, (UI.margin, grid_rect.bottom + 6))

        pygame.display.flip()
        clock.tick(frame_fps)

    pygame.quit()
