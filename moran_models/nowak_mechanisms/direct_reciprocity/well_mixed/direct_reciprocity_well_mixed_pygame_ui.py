#!/usr/bin/env python3
"""Live viewer for the pure direct-reciprocity well-mixed model."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "moran_models.nowak_mechanisms.direct_reciprocity.well_mixed."
        "direct_reciprocity_well_mixed_pygame_ui'."
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


def _draw_frequency_bars(
    screen: pygame.Surface,
    model: DirectReciprocityWellMixedModel,
    rect: pygame.Rect,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> None:
    pygame.draw.rect(screen, (234, 242, 251), rect)
    pygame.draw.rect(screen, (208, 219, 234), rect, 1)

    title = font.render("Strategy Composition", True, (31, 45, 61))
    screen.blit(title, (rect.x + 16, rect.y + 14))

    bar_area_y = rect.y + 46
    bar_area_h = rect.height - 60
    bar_h = max(8, bar_area_h // len(STRATEGY_NAMES) - 8)
    gap = (bar_area_h - bar_h * len(STRATEGY_NAMES)) // (len(STRATEGY_NAMES) + 1)
    label_w = 170
    pct_w = 36
    right_margin = 16
    bar_max_w = rect.width - label_w - 16 - pct_w - 8 - right_margin

    for k, name in enumerate(STRATEGY_NAMES):
        freq = float(model.strategy.tolist().count(STRATEGY_IDS[name]) / model.n_sites)
        y = bar_area_y + gap + k * (bar_h + gap)

        lbl = small_font.render(f"{STRATEGY_DISPLAY_NAMES[name]}", True, (31, 45, 61))
        screen.blit(lbl, (rect.x + 16, y + (bar_h - lbl.get_height()) // 2))

        bar_x = rect.x + 16 + label_w
        bar_w = max(2, int(freq * bar_max_w))
        pygame.draw.rect(screen, STRATEGY_COLORS[name], pygame.Rect(bar_x, y, bar_w, bar_h))
        pygame.draw.rect(screen, (208, 219, 234), pygame.Rect(bar_x + bar_w, y, bar_max_w - bar_w, bar_h))

        pct = small_font.render(f"{freq:.2f}", True, (80, 95, 110))
        screen.blit(pct, (bar_x + bar_max_w + 8, y + (bar_h - pct.get_height()) // 2))


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
        (plot_x + int(i * plot_w / max(1, len(values) - 1)),
         plot_y + plot_h - int(v * plot_h))
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
            (plot_x + int(i * plot_w / max(1, len(values) - 1)),
             plot_y + plot_h - int(v * plot_h))
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

    margin = 16
    header_height = 96
    freq_bar_w = 520
    side_panel_width = 400
    main_h = 480
    window_w = margin * 3 + freq_bar_w + side_panel_width
    window_h = margin * 2 + header_height + main_h

    pygame.init()
    pygame.display.set_caption("Direct Reciprocity Well-Mixed Live Viewer")
    screen = pygame.display.set_mode((window_w, window_h))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 34)
    body_font = pygame.font.SysFont(None, 23)
    small_font = pygame.font.SysFont(None, 21)

    freq_bar_rect = pygame.Rect(margin, margin + header_height, freq_bar_w, main_h)
    panel_rect = pygame.Rect(freq_bar_rect.right + margin, freq_bar_rect.y, side_panel_width, main_h)

    running = True
    paused = False
    frame_fps = 20
    max_steps = int(cfg["simulation_steps"])
    step_count = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_n and step_count < max_steps:
                    model.step()
                    step_count += 1
                elif event.key == pygame.K_r:
                    model = DirectReciprocityWellMixedModel(cfg)
                    step_count = 0
                    paused = False
                elif event.key == pygame.K_UP:
                    frame_fps = min(120, frame_fps + 1)
                elif event.key == pygame.K_DOWN:
                    frame_fps = max(1, frame_fps - 1)

        if not paused and step_count < max_steps:
            model.step()
            step_count += 1
        if step_count >= max_steps:
            paused = True

        screen.fill((248, 250, 255))
        pygame.draw.rect(screen, (15, 51, 104), (0, 0, window_w, margin + header_height))
        title = title_font.render("Direct Reciprocity  –  Well-Mixed Moran Model  –  Any agent can meet any other", True, (255, 255, 255))
        subtitle = small_font.render(
            "space play/pause | n step | r reset | up/down fps | esc quit",
            True,
            (255, 255, 255),
        )
        screen.blit(title, (margin, margin + 14))
        screen.blit(subtitle, (margin, margin + 52))

        _draw_frequency_bars(screen, model, freq_bar_rect, body_font, small_font)

        pygame.draw.rect(screen, (234, 242, 251), panel_rect)
        pygame.draw.rect(screen, (208, 219, 234), panel_rect, 1)

        px = panel_rect.x + 16
        py = panel_rect.y + 16
        panel_inner_w = panel_rect.width - 32
        mode = "paused" if paused else "running"
        py = _draw_panel_text(screen, body_font, f"step={step_count} / {max_steps}  fps={frame_fps}  {mode}", px, py)
        py = _draw_panel_text(
            screen,
            body_font,
            f"cooperation rate={_latest(model, 'mean_cooperation_rate'):.3f}",
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
            f"PD payoffs: T={cfg['temptation_payoff']}, R={cfg['reward_payoff']}, "
            f"P={cfg['punishment_payoff']}, S={cfg['sucker_payoff']}.",
            f"Rounds per pair: {cfg['rounds_per_pair_per_step']}.",
        ]
        for line in notes:
            py = _draw_panel_text(screen, small_font, line, px, py)

        pygame.display.flip()
        clock.tick(frame_fps)

    pygame.quit()


if __name__ == "__main__":
    main()
