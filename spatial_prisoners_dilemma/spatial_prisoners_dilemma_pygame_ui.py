#!/usr/bin/env python3
"""
Live Pygame viewer for the spatial Prisoner's Dilemma model.

Run from the repository root with:
  ./.conda/bin/python -m spatial_prisoners_dilemma.spatial_prisoners_dilemma_pygame_ui
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m spatial_prisoners_dilemma.spatial_prisoners_dilemma_pygame_ui'."
    )

from .spatial_prisoners_dilemma import SpatialPrisonersDilemmaModel, make_settings


GRID_MAJOR_STEP = 5
DEFAULT_FPS = 8
WORLD_TARGET_SIZE = 720
SIDEBAR_WIDTH = 360


@dataclass(frozen=True)
class ViewerStyle:
    margin: int = 16
    gap: int = 16
    card_padding: int = 18
    header_height: int = 96
    world_top_offset: int = 136
    viewer_footer_height: int = 58
    background_color: tuple[int, int, int] = (255, 255, 255)
    card_background: tuple[int, int, int] = (247, 251, 255)
    card_border: tuple[int, int, int] = (214, 228, 245)
    accent_panel: tuple[int, int, int] = (234, 242, 251)
    header_background: tuple[int, int, int] = (15, 51, 104)
    header_text: tuple[int, int, int] = (255, 255, 255)
    text_color: tuple[int, int, int] = (31, 45, 61)
    muted_text: tuple[int, int, int] = (78, 98, 121)
    button_primary: tuple[int, int, int] = (28, 75, 143)
    button_secondary: tuple[int, int, int] = (120, 170, 230)
    button_disabled: tuple[int, int, int] = (186, 197, 214)
    button_text: tuple[int, int, int] = (255, 255, 255)
    empty_color: tuple[int, int, int] = (244, 239, 229)
    cooperate_color: tuple[int, int, int] = (120, 170, 230)
    defect_color: tuple[int, int, int] = (181, 83, 67)
    tit_for_tat_color: tuple[int, int, int] = (15, 51, 104)
    random_color: tuple[int, int, int] = (200, 155, 60)
    grid_color: tuple[int, int, int] = (224, 230, 224)
    grid_color_major: tuple[int, int, int] = (176, 192, 176)
    chart_axis: tuple[int, int, int] = (115, 143, 178)
    chart_grid: tuple[int, int, int] = (223, 233, 244)


STYLE = ViewerStyle()


def _strategy_color(style: ViewerStyle, strategy_id: int) -> tuple[int, int, int]:
    if strategy_id == 0:
        return style.cooperate_color
    if strategy_id == 1:
        return style.defect_color
    if strategy_id == 2:
        return style.tit_for_tat_color
    return style.random_color


def _draw_card(
    screen: pygame.Surface,
    rect: pygame.Rect,
    *,
    fill: tuple[int, int, int] | None = None,
    border: tuple[int, int, int] | None = None,
) -> None:
    pygame.draw.rect(screen, fill or STYLE.card_background, rect)
    pygame.draw.rect(screen, border or STYLE.card_border, rect, 1)


def _draw_chip(
    screen: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    fill: tuple[int, int, int],
    font: pygame.font.Font,
    *,
    text_color: tuple[int, int, int] | None = None,
) -> None:
    pygame.draw.rect(screen, fill, rect)
    label = font.render(text, True, text_color or STYLE.button_text)
    screen.blit(
        label,
        (rect.x + (rect.width - label.get_width()) // 2, rect.y + (rect.height - label.get_height()) // 2),
    )


class ModelUI:
    def __init__(self) -> None:
        self.settings = make_settings()
        self.running = False
        self.reset()

    def reset(self) -> None:
        self.model = SpatialPrisonersDilemmaModel(self.settings)
        self.running = False

    def step(self) -> bool:
        if not self.model.agents:
            self.running = False
            return False
        if self.model.step_index >= self.settings.simulation_steps:
            self.running = False
            return False

        alive = self.model.step()
        if not alive or self.model.step_index >= self.settings.simulation_steps:
            self.running = False
        return alive

    @property
    def latest_index(self) -> int:
        return -1

    def latest_value(self, key: str) -> int | float:
        history = self.model.history.get(key, [])
        if not history:
            return 0
        return history[self.latest_index]


def _draw_header_banner(
    screen: pygame.Surface,
    rect: pygame.Rect,
    *,
    small_font: pygame.font.Font,
    title_font: pygame.font.Font,
    caption_font: pygame.font.Font,
) -> None:
    _draw_card(screen, rect, fill=STYLE.header_background, border=STYLE.header_background)
    eyebrow = small_font.render("EVOLVED COOPERATION", True, STYLE.header_text)
    title = title_font.render("Spatial Prisoner's Dilemma Live Grid", True, STYLE.header_text)
    subtitle = caption_font.render(
        "Step through the active Python model with same-trait strategy coloring.",
        True,
        STYLE.header_text,
    )
    screen.blit(eyebrow, (rect.x + 20, rect.y + 14))
    screen.blit(title, (rect.x + 20, rect.y + 30))
    screen.blit(subtitle, (rect.x + 20, rect.y + 70))


def _draw_world(
    screen: pygame.Surface,
    model_ui: ModelUI,
    rect: pygame.Rect,
    *,
    cell_size: int,
) -> None:
    pygame.draw.rect(screen, STYLE.empty_color, rect)

    for agent in model_ui.model.agents:
        same_trait_strategy = agent.strategy_id // 10
        color = _strategy_color(STYLE, same_trait_strategy)
        pygame.draw.rect(
            screen,
            color,
            (
                rect.x + agent.x * cell_size,
                rect.y + agent.y * cell_size,
                cell_size,
                cell_size,
            ),
        )

    for x in range(model_ui.settings.grid_width + 1):
        color = STYLE.grid_color_major if x % GRID_MAJOR_STEP == 0 else STYLE.grid_color
        line_width = 2 if x % GRID_MAJOR_STEP == 0 else 1
        pygame.draw.line(
            screen,
            color,
            (rect.x + x * cell_size, rect.y),
            (rect.x + x * cell_size, rect.bottom),
            line_width,
        )
    for y in range(model_ui.settings.grid_height + 1):
        color = STYLE.grid_color_major if y % GRID_MAJOR_STEP == 0 else STYLE.grid_color
        line_width = 2 if y % GRID_MAJOR_STEP == 0 else 1
        pygame.draw.line(
            screen,
            color,
            (rect.x, rect.y + y * cell_size),
            (rect.right, rect.y + y * cell_size),
            line_width,
        )


def _draw_chart(
    screen: pygame.Surface,
    rect: pygame.Rect,
    model_ui: ModelUI,
    *,
    label_font: pygame.font.Font,
    title_font: pygame.font.Font,
    legend_font: pygame.font.Font,
) -> None:
    _draw_card(screen, rect)
    eyebrow = label_font.render("HISTORY", True, STYLE.button_primary)
    title = title_font.render("Same-Trait Strategy Families", True, STYLE.text_color)
    subtitle = label_font.render(
        "Counts over time in the active run.",
        True,
        STYLE.muted_text,
    )
    screen.blit(eyebrow, (rect.x + 18, rect.y + 14))
    screen.blit(title, (rect.x + 18, rect.y + 31))
    screen.blit(subtitle, (rect.x + 18, rect.y + 54))

    plot = pygame.Rect(rect.x + 46, rect.y + 82, rect.width - 64, rect.height - 118)
    pygame.draw.rect(screen, (255, 255, 255), plot)
    pygame.draw.rect(screen, STYLE.card_border, plot, 1)

    for tick in range(5):
        ratio = tick / 4
        y = plot.bottom - ratio * plot.height
        pygame.draw.line(screen, STYLE.chart_grid, (plot.x, y), (plot.right, y), 1)

    pygame.draw.line(screen, STYLE.header_background, (plot.x, plot.y), (plot.x, plot.bottom), 2)
    pygame.draw.line(screen, STYLE.chart_axis, (plot.x, plot.bottom), (plot.right, plot.bottom), 1)

    max_value = max(1, model_ui.settings.agent_hard_limit)
    y_values = [0, max_value / 4, max_value / 2, max_value * 3 / 4, max_value]
    for tick, value in enumerate(y_values):
        y = plot.bottom - (tick / 4) * plot.height
        surface = label_font.render(f"{int(value)}", True, STYLE.muted_text)
        screen.blit(surface, (plot.x - 10 - surface.get_width(), y - surface.get_height() // 2))

    history = model_ui.model.history
    steps = history["step"]
    series = (
        ("same_trait_cooperate", STYLE.cooperate_color, "Co-op"),
        ("same_trait_defect", STYLE.defect_color, "Defect"),
        ("same_trait_tit_for_tat", STYLE.tit_for_tat_color, "Tit-for-tat"),
        ("same_trait_random", STYLE.random_color, "Random"),
    )

    step_denominator = max(1, model_ui.settings.simulation_steps)
    for key, color, _ in series:
        values = history[key]
        if len(values) < 2:
            continue
        points: list[tuple[int, int]] = []
        for step_value, count in zip(steps, values):
            x = plot.x + int((step_value / step_denominator) * plot.width)
            y = plot.bottom - int((count / max_value) * plot.height)
            points.append((x, y))
        if len(points) >= 2:
            pygame.draw.lines(screen, color, False, points, 2)

    marker_x = plot.x + int((model_ui.model.step_index / step_denominator) * plot.width)
    pygame.draw.line(screen, STYLE.header_background, (marker_x, plot.y), (marker_x, plot.bottom), 1)

    legend_x = plot.x
    legend_y = rect.bottom - 24
    for color, label in (
        (STYLE.cooperate_color, "Co-op"),
        (STYLE.defect_color, "Defect"),
        (STYLE.tit_for_tat_color, "Tit-for-tat"),
        (STYLE.random_color, "Random"),
    ):
        swatch = pygame.Rect(legend_x, legend_y, 14, 14)
        pygame.draw.rect(screen, color, swatch)
        pygame.draw.rect(screen, STYLE.header_background, swatch, 1)
        surface = legend_font.render(label, True, STYLE.text_color)
        screen.blit(surface, (legend_x + 22, legend_y - 1))
        legend_x += 22 + surface.get_width() + 18


def _draw_stats_panel(
    screen: pygame.Surface,
    rect: pygame.Rect,
    model_ui: ModelUI,
    *,
    small_font: pygame.font.Font,
    title_font: pygame.font.Font,
) -> None:
    _draw_card(screen, rect)
    eyebrow = small_font.render("STATUS", True, STYLE.button_primary)
    title = title_font.render("Current Step", True, STYLE.text_color)
    subtitle = small_font.render(
        "Play, pause, step, or reset the active model.",
        True,
        STYLE.muted_text,
    )
    screen.blit(eyebrow, (rect.x + 18, rect.y + 14))
    screen.blit(title, (rect.x + 18, rect.y + 31))
    screen.blit(subtitle, (rect.x + 18, rect.y + 54))

    info_rows = (
        ("Step", str(model_ui.model.step_index)),
        ("Population", str(len(model_ui.model.agents))),
        ("Mean energy", f"{float(model_ui.latest_value('mean_energy')):.2f}"),
        ("Births", str(int(model_ui.latest_value('births')))),
        ("Deaths", str(int(model_ui.latest_value('deaths_total')))),
        ("Pairs", str(int(model_ui.latest_value('interaction_pairs')))),
        (
            "Moves",
            f"{int(model_ui.latest_value('movement_successes'))}/"
            f"{int(model_ui.latest_value('movement_attempts'))}",
        ),
        ("Same-trait Co-op", str(int(model_ui.latest_value('same_trait_cooperate')))),
        ("Same-trait Defect", str(int(model_ui.latest_value('same_trait_defect')))),
        (
            "Same-trait Tit-for-tat",
            str(int(model_ui.latest_value('same_trait_tit_for_tat'))),
        ),
        ("Same-trait Random", str(int(model_ui.latest_value('same_trait_random')))),
    )

    inner = pygame.Rect(rect.x + 18, rect.y + 84, rect.width - 36, rect.height - 120)
    pygame.draw.rect(screen, STYLE.accent_panel, inner)
    pygame.draw.rect(screen, STYLE.card_border, inner, 1)

    row_y = inner.y + 14
    for label, value in info_rows:
        label_surface = small_font.render(label, True, STYLE.muted_text)
        value_surface = small_font.render(value, True, STYLE.text_color)
        screen.blit(label_surface, (inner.x + 12, row_y))
        screen.blit(value_surface, (inner.right - 12 - value_surface.get_width(), row_y))
        row_y += 24

    note_lines = (
        "Legend:",
        "Light blue = Co-op",
        "Rust red = Defect",
        "Deep blue = Tit-for-tat",
        "Ochre = Random",
        "",
        "Keys: Space play/pause, S or Right step, R reset, +/- fps",
    )
    note_y = rect.bottom - 104
    for line in note_lines:
        surface = small_font.render(line, True, STYLE.muted_text if line != "Legend:" else STYLE.text_color)
        screen.blit(surface, (rect.x + 18, note_y))
        note_y += 18


def main() -> None:
    model_ui = ModelUI()
    settings = model_ui.settings

    cell_size = max(6, min(12, WORLD_TARGET_SIZE // max(settings.grid_width, settings.grid_height)))
    world_w = settings.grid_width * cell_size
    world_h = settings.grid_height * cell_size

    viewer_card_w = world_w + STYLE.card_padding * 2
    viewer_card_h = world_h + STYLE.world_top_offset + STYLE.viewer_footer_height
    chart_card_h = 336
    stats_card_h = max(viewer_card_h - chart_card_h - STYLE.gap, 320)
    main_h = max(viewer_card_h, chart_card_h + STYLE.gap + stats_card_h)
    window_w = STYLE.margin * 2 + viewer_card_w + STYLE.gap + SIDEBAR_WIDTH
    window_h = STYLE.margin * 2 + STYLE.header_height + STYLE.gap + main_h

    pygame.init()
    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption("Spatial Prisoner's Dilemma Live Grid")
    clock = pygame.time.Clock()

    small_font = pygame.font.SysFont(None, 20)
    panel_font = pygame.font.SysFont(None, 28)
    panel_large_font = pygame.font.SysFont(None, 32)
    panel_caption_font = pygame.font.SysFont(None, 20)
    legend_font = pygame.font.SysFont(None, 18)

    header_rect = pygame.Rect(
        STYLE.margin,
        STYLE.margin,
        window_w - STYLE.margin * 2,
        STYLE.header_height,
    )
    viewer_card = pygame.Rect(
        STYLE.margin,
        header_rect.bottom + STYLE.gap,
        viewer_card_w,
        viewer_card_h,
    )
    world_rect = pygame.Rect(
        viewer_card.x + STYLE.card_padding,
        viewer_card.y + STYLE.world_top_offset,
        world_w,
        world_h,
    )
    chart_card = pygame.Rect(
        viewer_card.right + STYLE.gap,
        viewer_card.y,
        SIDEBAR_WIDTH,
        chart_card_h,
    )
    stats_card = pygame.Rect(
        chart_card.x,
        chart_card.bottom + STYLE.gap,
        SIDEBAR_WIDTH,
        main_h - chart_card_h - STYLE.gap,
    )

    button_y = viewer_card.y + 68
    play_rect = pygame.Rect(viewer_card.x + 18, button_y, 92, 34)
    reset_rect = pygame.Rect(play_rect.right + 10, button_y, 92, 34)
    step_rect = pygame.Rect(reset_rect.right + 10, button_y, 88, 34)
    fps_rect = pygame.Rect(viewer_card.right - 102, button_y, 84, 34)

    current_fps = DEFAULT_FPS
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    model_ui.running = not model_ui.running
                elif event.key in (pygame.K_s, pygame.K_RIGHT):
                    if not model_ui.running:
                        model_ui.step()
                elif event.key == pygame.K_r:
                    model_ui.reset()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    current_fps = min(60, current_fps + 2)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    current_fps = max(1, current_fps - 2)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(event.pos):
                    model_ui.running = not model_ui.running
                elif reset_rect.collidepoint(event.pos):
                    model_ui.reset()
                elif step_rect.collidepoint(event.pos) and not model_ui.running:
                    model_ui.step()

        if model_ui.running:
            model_ui.step()

        screen.fill(STYLE.background_color)
        _draw_header_banner(
            screen,
            header_rect,
            small_font=small_font,
            title_font=panel_large_font,
            caption_font=panel_caption_font,
        )

        _draw_card(screen, viewer_card)
        eyebrow = small_font.render("REPLAY", True, STYLE.button_primary)
        title = panel_font.render("World State", True, STYLE.text_color)
        subtitle = panel_caption_font.render(
            "Live run using the active config file and same-trait strategy colors.",
            True,
            STYLE.muted_text,
        )
        screen.blit(eyebrow, (viewer_card.x + 18, viewer_card.y + 14))
        screen.blit(title, (viewer_card.x + 18, viewer_card.y + 31))
        screen.blit(subtitle, (viewer_card.x + 18, viewer_card.y + 54))

        _draw_chip(
            screen,
            play_rect,
            "Pause" if model_ui.running else "Play",
            STYLE.button_primary,
            small_font,
        )
        _draw_chip(screen, reset_rect, "Reset", STYLE.button_secondary, small_font)
        _draw_chip(
            screen,
            step_rect,
            "Step",
            STYLE.button_secondary if not model_ui.running else STYLE.button_disabled,
            small_font,
        )
        _draw_chip(screen, fps_rect, f"{current_fps} fps", STYLE.button_secondary, small_font)

        world_frame = pygame.Rect(world_rect.x - 2, world_rect.y - 2, world_rect.width + 4, world_rect.height + 4)
        pygame.draw.rect(screen, STYLE.accent_panel, world_frame)
        pygame.draw.rect(screen, STYLE.card_border, world_frame, 1)
        _draw_world(screen, model_ui, world_rect, cell_size=cell_size)

        footer_left = small_font.render(f"Step {model_ui.model.step_index}", True, STYLE.text_color)
        footer_right = panel_caption_font.render(
            f"Population {len(model_ui.model.agents)} / {settings.agent_hard_limit}",
            True,
            STYLE.muted_text,
        )
        screen.blit(footer_left, (viewer_card.x + 18, viewer_card.bottom - 42))
        screen.blit(footer_right, (viewer_card.x + 18, viewer_card.bottom - 22))

        _draw_chart(
            screen,
            chart_card,
            model_ui,
            label_font=small_font,
            title_font=panel_font,
            legend_font=legend_font,
        )
        _draw_stats_panel(
            screen,
            stats_card,
            model_ui,
            small_font=small_font,
            title_font=panel_font,
        )

        pygame.display.flip()
        clock.tick(current_fps)

    pygame.quit()


if __name__ == "__main__":
    main()
