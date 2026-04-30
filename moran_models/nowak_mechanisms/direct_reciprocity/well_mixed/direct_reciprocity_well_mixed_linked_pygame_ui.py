#!/usr/bin/env python3
"""Linked aggregate and display-grid viewer for the well-mixed model."""

from __future__ import annotations

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "moran_models.nowak_mechanisms.direct_reciprocity.well_mixed."
        "direct_reciprocity_well_mixed_linked_pygame_ui'."
    )

import pygame

from .config.direct_reciprocity_well_mixed_config import config as model_config
from .direct_reciprocity_well_mixed_grid_pygame_ui import (
    PairSet,
    _advance_model,
    _display_grid_shape,
    _draw_strategy_grid,
)
from .direct_reciprocity_well_mixed_model import (
    STRATEGY_IDS,
    STRATEGY_NAMES,
    DirectReciprocityWellMixedModel,
)
from .direct_reciprocity_well_mixed_pygame_ui import (
    STRATEGY_COLORS,
    STRATEGY_DISPLAY_NAMES,
    _draw_frequency_bars,
    _draw_panel_text,
    _draw_sparkline,
    _draw_strategy_frequencies_chart,
    _latest,
)


def _draw_pair_legend(
    screen: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
) -> int:
    y = _draw_panel_text(screen, font, "Pair Links", x, y)
    y += 8
    pygame.draw.line(screen, (34, 69, 112), (x, y), (x + 34, y), 1)
    _draw_panel_text(screen, font, "new or reshuffled pair", x + 46, y - 9)
    y += 28
    pygame.draw.line(screen, (20, 41, 72), (x, y), (x + 34, y), 3)
    _draw_panel_text(screen, font, "retained pair", x + 46, y - 9)
    return y + 24


def _draw_strategy_legend(
    screen: pygame.Surface,
    model: DirectReciprocityWellMixedModel,
    font: pygame.font.Font,
    x: int,
    y: int,
) -> int:
    y = _draw_panel_text(screen, font, "Strategies", x, y)
    for name in STRATEGY_NAMES:
        color = STRATEGY_COLORS[name]
        pygame.draw.rect(screen, color, pygame.Rect(x, y + 3, 16, 16))
        freq = float(model.strategy.tolist().count(STRATEGY_IDS[name]) / model.n_sites)
        y = _draw_panel_text(
            screen,
            font,
            f"{STRATEGY_DISPLAY_NAMES[name]}: {freq:.3f}",
            x + 24,
            y,
        )
    return y


def main() -> None:
    cfg = dict(model_config)
    model = DirectReciprocityWellMixedModel(cfg)

    columns, rows = _display_grid_shape(model.n_sites)
    cell_size = 26
    margin = 16
    header_height = 96
    panel_padding = 20
    right_panel_width = 520
    grid_w = columns * cell_size
    grid_h = rows * cell_size
    left_panel_width = grid_w + panel_padding * 2
    main_h = 660
    window_w = margin * 3 + left_panel_width + right_panel_width
    window_h = margin * 2 + header_height + main_h

    pygame.init()
    pygame.display.set_caption("Direct Reciprocity Well-Mixed Linked Viewer")
    screen = pygame.display.set_mode((window_w, window_h))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 34)
    body_font = pygame.font.SysFont(None, 23)
    small_font = pygame.font.SysFont(None, 21)

    left_panel_rect = pygame.Rect(margin, margin + header_height, left_panel_width, main_h)
    right_panel_rect = pygame.Rect(left_panel_rect.right + margin, left_panel_rect.y, right_panel_width, main_h)
    grid_rect = pygame.Rect(
        left_panel_rect.x + panel_padding,
        left_panel_rect.y + 76,
        grid_w,
        grid_h,
    )

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
            "Direct Reciprocity - Well-Mixed Linked Viewer",
            True,
            (255, 255, 255),
        )
        subtitle = small_font.render(
            "one model object drives both views | space play/pause | n step | r reset | up/down fps | esc quit",
            True,
            (255, 255, 255),
        )
        screen.blit(title, (margin, margin + 14))
        screen.blit(subtitle, (margin, margin + 52))

        pygame.draw.rect(screen, (234, 242, 251), left_panel_rect)
        pygame.draw.rect(screen, (208, 219, 234), left_panel_rect, 1)
        lx = left_panel_rect.x + panel_padding
        ly = left_panel_rect.y + 16
        ly = _draw_panel_text(screen, body_font, "Display-Only Agent Grid", lx, ly)
        _draw_panel_text(
            screen,
            small_font,
            "Fixed agent-ID slots; global links show current well-mixed pairs.",
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

        ly = grid_rect.bottom + 18
        ly = _draw_pair_legend(screen, small_font, lx, ly)
        ly += 8
        _draw_strategy_legend(screen, model, small_font, lx, ly)

        pygame.draw.rect(screen, (234, 242, 251), right_panel_rect)
        pygame.draw.rect(screen, (208, 219, 234), right_panel_rect, 1)
        px = right_panel_rect.x + 16
        py = right_panel_rect.y + 16
        panel_inner_w = right_panel_rect.width - 32
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

        py += 6
        freq_bar_rect = pygame.Rect(px, py, panel_inner_w, 172)
        _draw_frequency_bars(screen, model, freq_bar_rect, body_font, small_font)
        py = freq_bar_rect.bottom + 12

        chart_h = 100
        py = _draw_panel_text(screen, small_font, "Cooperation Rate", px, py)
        coop_rect = pygame.Rect(px, py, panel_inner_w, chart_h)
        _draw_sparkline(screen, model.history, coop_rect, "mean_cooperation_rate", (58, 112, 191), small_font)
        py = coop_rect.bottom + 10

        py = _draw_panel_text(screen, small_font, "Strategy Frequencies", px, py)
        freq_rect = pygame.Rect(px, py, panel_inner_w, chart_h)
        _draw_strategy_frequencies_chart(screen, model.history, freq_rect, small_font)
        py = freq_rect.bottom + 10

        notes = [
            f"n={model.n_sites}; display grid={columns}x{rows}.",
            f"Rounds per pair: {cfg['rounds_per_pair_per_step']}.",
            "Grid position does not affect interaction or replacement.",
        ]
        for line in notes:
            py = _draw_panel_text(screen, small_font, line, px, py)

        pygame.display.flip()
        clock.tick(frame_fps)

    pygame.quit()


if __name__ == "__main__":
    main()
