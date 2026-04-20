#!/usr/bin/env python3
"""
Live Pygame viewer for the Retained Benefit model.

Run from the repository root with:
  ./.conda/bin/python -m retained_benefit.retained_benefit_pygame_ui
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

import pygame

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m retained_benefit.retained_benefit_pygame_ui'."
    )

from .retained_benefit_model import RetainedBenefitModel, make_settings


GRID_MAJOR_STEP = 6
DEFAULT_FPS = 8
WORLD_TARGET_SIZE = 720
SIDEBAR_WIDTH = 390


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
    grid_color: tuple[int, int, int] = (224, 230, 224)
    grid_color_major: tuple[int, int, int] = (176, 192, 176)
    low_cooperation: tuple[int, int, int] = (244, 239, 229)
    mid_cooperation: tuple[int, int, int] = (120, 170, 230)
    high_cooperation: tuple[int, int, int] = (161, 52, 78)
    chart_axis: tuple[int, int, int] = (115, 143, 178)
    chart_grid: tuple[int, int, int] = (223, 233, 244)
    mean_color: tuple[int, int, int] = (161, 52, 78)
    assortment_color: tuple[int, int, int] = (28, 75, 143)
    dominant_color: tuple[int, int, int] = (99, 128, 61)


STYLE = ViewerStyle()


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
        (
            rect.x + (rect.width - label.get_width()) // 2,
            rect.y + (rect.height - label.get_height()) // 2,
        ),
    )


def _lerp_color(
    low: tuple[int, int, int],
    high: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, ratio))
    return tuple(
        int(round(a + (b - a) * ratio))
        for a, b in zip(low, high, strict=True)
    )


def _cooperation_color(value: float) -> tuple[int, int, int]:
    if value <= 0.5:
        return _lerp_color(STYLE.low_cooperation, STYLE.mid_cooperation, value / 0.5)
    return _lerp_color(
        STYLE.mid_cooperation,
        STYLE.high_cooperation,
        (value - 0.5) / 0.5,
    )


def _lineage_color(lineage_id: int) -> tuple[int, int, int]:
    hue = (lineage_id * 0.6180339887498949) % 1.0
    saturation = 0.55 + 0.18 * ((lineage_id * 37) % 7) / 6
    value = 0.80 + 0.08 * ((lineage_id * 19) % 5) / 4
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return int(r * 255), int(g * 255), int(b * 255)


class ModelUI:
    def __init__(self) -> None:
        self.settings = make_settings()
        self.running = False
        self.current_fps = DEFAULT_FPS
        self.view_mode = "cooperation"
        self.reset()

    def reset(self) -> None:
        self.model = RetainedBenefitModel(self.settings)
        self.running = False

    def step(self) -> bool:
        if self.model.step_count >= self.settings.simulation_steps:
            self.running = False
            return False
        self.model.step()
        if self.model.step_count >= self.settings.simulation_steps:
            self.running = False
        return True

    def latest_value(self, key: str) -> float:
        history = self.model.history.get(key, [])
        if not history:
            return 0.0
        return float(history[-1])

    def toggle_view(self) -> None:
        self.view_mode = "lineage" if self.view_mode == "cooperation" else "cooperation"


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
    title = title_font.render("Retained Benefit Live Grid", True, STYLE.header_text)
    subtitle = caption_font.render(
        "Toggle between cooperation intensity and inherited lineage structure.",
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
    pygame.draw.rect(screen, STYLE.low_cooperation, rect)
    for y in range(model_ui.settings.grid_height):
        for x in range(model_ui.settings.grid_width):
            if model_ui.view_mode == "cooperation":
                color = _cooperation_color(float(model_ui.model.cooperation[y, x]))
            else:
                color = _lineage_color(int(model_ui.model.lineage[y, x]))
            pygame.draw.rect(
                screen,
                color,
                (
                    rect.x + x * cell_size,
                    rect.y + y * cell_size,
                    cell_size,
                    cell_size,
                ),
            )

    for x in range(model_ui.settings.grid_width + 1):
        color = STYLE.grid_color_major if x % GRID_MAJOR_STEP == 0 else STYLE.grid_color
        width = 2 if x % GRID_MAJOR_STEP == 0 else 1
        pygame.draw.line(
            screen,
            color,
            (rect.x + x * cell_size, rect.y),
            (rect.x + x * cell_size, rect.bottom),
            width,
        )
    for y in range(model_ui.settings.grid_height + 1):
        color = STYLE.grid_color_major if y % GRID_MAJOR_STEP == 0 else STYLE.grid_color
        width = 2 if y % GRID_MAJOR_STEP == 0 else 1
        pygame.draw.line(
            screen,
            color,
            (rect.x, rect.y + y * cell_size),
            (rect.right, rect.y + y * cell_size),
            width,
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
    title = title_font.render("Selection Metrics", True, STYLE.text_color)
    subtitle = label_font.render(
        "Mean cooperation, local assortment, and dominant-lineage share.",
        True,
        STYLE.muted_text,
    )
    screen.blit(eyebrow, (rect.x + 18, rect.y + 14))
    screen.blit(title, (rect.x + 18, rect.y + 31))
    screen.blit(subtitle, (rect.x + 18, rect.y + 54))

    plot = pygame.Rect(rect.x + 46, rect.y + 84, rect.width - 64, rect.height - 126)
    pygame.draw.rect(screen, (255, 255, 255), plot)
    pygame.draw.rect(screen, STYLE.card_border, plot, 1)

    for tick in range(5):
        ratio = tick / 4
        y = plot.bottom - ratio * plot.height
        pygame.draw.line(screen, STYLE.chart_grid, (plot.x, y), (plot.right, y), 1)

    pygame.draw.line(screen, STYLE.header_background, (plot.x, plot.y), (plot.x, plot.bottom), 2)
    pygame.draw.line(screen, STYLE.chart_axis, (plot.x, plot.bottom), (plot.right, plot.bottom), 1)

    y_values = [0.0, 0.25, 0.50, 0.75, 1.0]
    for tick, value in enumerate(y_values):
        y = plot.bottom - (tick / 4) * plot.height
        surface = label_font.render(f"{value:.2f}", True, STYLE.muted_text)
        screen.blit(surface, (plot.x - 10 - surface.get_width(), y - surface.get_height() // 2))

    history = model_ui.model.history
    steps = history["step"]
    series = (
        ("mean_cooperation", STYLE.mean_color, "Mean h"),
        ("local_assortment", STYLE.assortment_color, "Assortment"),
        ("dominant_lineage_share", STYLE.dominant_color, "Dominant lineage"),
    )

    step_denominator = max(1, model_ui.settings.simulation_steps)
    for key, color, _ in series:
        values = history[key]
        if len(values) < 2:
            continue
        points: list[tuple[int, int]] = []
        for step_value, value in zip(steps, values, strict=True):
            x = plot.x + int((step_value / step_denominator) * plot.width)
            y = plot.bottom - int(max(0.0, min(1.0, value)) * plot.height)
            points.append((x, y))
        if len(points) >= 2:
            pygame.draw.lines(screen, color, False, points, 3)

    legend_x = rect.x + 18
    legend_y = rect.bottom - 28
    cursor_x = legend_x
    for _, color, label in series:
        pygame.draw.rect(screen, color, (cursor_x, legend_y + 4, 16, 12))
        surface = legend_font.render(label, True, STYLE.text_color)
        screen.blit(surface, (cursor_x + 22, legend_y))
        cursor_x += 34 + surface.get_width()


def _draw_controls_and_stats(
    screen: pygame.Surface,
    rect: pygame.Rect,
    model_ui: ModelUI,
    *,
    title_font: pygame.font.Font,
    label_font: pygame.font.Font,
    body_font: pygame.font.Font,
    chip_font: pygame.font.Font,
) -> dict[str, pygame.Rect]:
    _draw_card(screen, rect)
    eyebrow = label_font.render("CONTROLS", True, STYLE.button_primary)
    title = title_font.render("Viewer and Run State", True, STYLE.text_color)
    screen.blit(eyebrow, (rect.x + 18, rect.y + 14))
    screen.blit(title, (rect.x + 18, rect.y + 31))

    button_map: dict[str, pygame.Rect] = {}
    button_w = 102
    button_h = 34
    top_row_y = rect.y + 70
    second_row_y = top_row_y + button_h + 10
    x0 = rect.x + 18
    x1 = x0 + button_w + 10
    x2 = x1 + button_w + 10

    button_map["toggle_run"] = pygame.Rect(x0, top_row_y, button_w, button_h)
    button_map["step"] = pygame.Rect(x1, top_row_y, button_w, button_h)
    button_map["reset"] = pygame.Rect(x2, top_row_y, button_w, button_h)
    button_map["view_cooperation"] = pygame.Rect(x0, second_row_y, 150, button_h)
    button_map["view_lineage"] = pygame.Rect(x0 + 160, second_row_y, 120, button_h)
    button_map["fps_down"] = pygame.Rect(x0, second_row_y + button_h + 10, 70, button_h)
    button_map["fps_up"] = pygame.Rect(x0 + 80, second_row_y + button_h + 10, 70, button_h)

    play_label = "Pause" if model_ui.running else "Play"
    _draw_chip(screen, button_map["toggle_run"], play_label, STYLE.button_primary, chip_font)
    _draw_chip(screen, button_map["step"], "Step", STYLE.button_secondary, chip_font)
    _draw_chip(screen, button_map["reset"], "Reset", STYLE.button_secondary, chip_font)

    coop_fill = STYLE.button_primary if model_ui.view_mode == "cooperation" else STYLE.button_secondary
    lineage_fill = STYLE.button_primary if model_ui.view_mode == "lineage" else STYLE.button_secondary
    _draw_chip(screen, button_map["view_cooperation"], "View: Cooperation", coop_fill, chip_font)
    _draw_chip(screen, button_map["view_lineage"], "View: Lineage", lineage_fill, chip_font)
    _draw_chip(screen, button_map["fps_down"], "FPS -", STYLE.button_secondary, chip_font)
    _draw_chip(screen, button_map["fps_up"], "FPS +", STYLE.button_secondary, chip_font)

    stats_top = button_map["fps_down"].bottom + 20
    stats = (
        ("Step", f"{model_ui.model.step_count}/{model_ui.settings.simulation_steps}"),
        ("Mean h", f"{model_ui.latest_value('mean_cooperation'):.3f}"),
        ("Assortment", f"{model_ui.latest_value('local_assortment'):.3f}"),
        ("Dominant lineage", f"{model_ui.latest_value('dominant_lineage_share'):.3f}"),
        ("Lineages", f"{int(round(model_ui.latest_value('lineage_count')))}"),
        ("FPS", f"{model_ui.current_fps}"),
        ("Retained fraction", f"{model_ui.settings.retained_benefit_fraction:.2f}"),
        ("Benefit / cost", f"{model_ui.settings.cooperation_benefit:.2f} / {model_ui.settings.cooperation_cost:.2f}"),
    )
    for index, (label, value) in enumerate(stats):
        y = stats_top + index * 28
        label_surface = label_font.render(label, True, STYLE.muted_text)
        value_surface = body_font.render(value, True, STYLE.text_color)
        screen.blit(label_surface, (rect.x + 20, y))
        screen.blit(value_surface, (rect.x + 170, y - 1))

    note_top = stats_top + len(stats) * 28 + 16
    if model_ui.view_mode == "cooperation":
        note_title = label_font.render("Cooperation Scale", True, STYLE.button_primary)
        screen.blit(note_title, (rect.x + 20, note_top))
        scale_rect = pygame.Rect(rect.x + 20, note_top + 22, rect.width - 40, 18)
        for x in range(scale_rect.width):
            ratio = x / max(1, scale_rect.width - 1)
            pygame.draw.line(
                screen,
                _cooperation_color(ratio),
                (scale_rect.x + x, scale_rect.y),
                (scale_rect.x + x, scale_rect.bottom),
                1,
            )
        pygame.draw.rect(screen, STYLE.card_border, scale_rect, 1)
        left = label_font.render("0.0", True, STYLE.muted_text)
        middle = label_font.render("0.5", True, STYLE.muted_text)
        right = label_font.render("1.0", True, STYLE.muted_text)
        screen.blit(left, (scale_rect.x, scale_rect.bottom + 4))
        screen.blit(middle, (scale_rect.centerx - middle.get_width() // 2, scale_rect.bottom + 4))
        screen.blit(right, (scale_rect.right - right.get_width(), scale_rect.bottom + 4))
    else:
        note_title = label_font.render("Lineage View", True, STYLE.button_primary)
        line1 = body_font.render("Same color = same inherited lineage label.", True, STYLE.text_color)
        line2 = body_font.render("Use this view to inspect local clustering.", True, STYLE.text_color)
        screen.blit(note_title, (rect.x + 20, note_top))
        screen.blit(line1, (rect.x + 20, note_top + 24))
        screen.blit(line2, (rect.x + 20, note_top + 48))

    footer_top = rect.bottom - 62
    footer = (
        "Keys: Space play/pause, S or Right step, R reset, V toggle view, "
        "C cooperation, L lineage, +/- speed"
    )
    lines = (
        footer[:70],
        footer[70:],
    )
    for index, line in enumerate(lines):
        surface = label_font.render(line.strip(), True, STYLE.muted_text)
        screen.blit(surface, (rect.x + 18, footer_top + index * 18))

    return button_map


def main() -> None:
    style = STYLE
    model_ui = ModelUI()

    cell_size = max(
        2,
        min(
            WORLD_TARGET_SIZE // model_ui.settings.grid_width,
            WORLD_TARGET_SIZE // model_ui.settings.grid_height,
        ),
    )
    world_w = model_ui.settings.grid_width * cell_size
    world_h = model_ui.settings.grid_height * cell_size
    viewer_card_w = world_w + style.card_padding * 2
    viewer_card_h = world_h + style.world_top_offset + style.viewer_footer_height
    chart_card_h = 320
    controls_card_h = max(viewer_card_h - chart_card_h - style.gap, 360)
    main_h = max(viewer_card_h, chart_card_h + style.gap + controls_card_h)
    window_w = style.margin * 2 + viewer_card_w + style.gap + SIDEBAR_WIDTH
    window_h = style.margin * 2 + style.header_height + style.gap + main_h

    pygame.init()
    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption("Retained Benefit Live Grid")
    clock = pygame.time.Clock()

    small_font = pygame.font.SysFont(None, 20)
    title_font = pygame.font.SysFont(None, 38)
    subtitle_font = pygame.font.SysFont(None, 22)
    panel_title_font = pygame.font.SysFont(None, 30)
    label_font = pygame.font.SysFont(None, 20)
    body_font = pygame.font.SysFont(None, 24)
    chip_font = pygame.font.SysFont(None, 24)

    header_rect = pygame.Rect(style.margin, style.margin, window_w - style.margin * 2, style.header_height)
    viewer_card = pygame.Rect(style.margin, header_rect.bottom + style.gap, viewer_card_w, viewer_card_h)
    world_rect = pygame.Rect(
        viewer_card.x + style.card_padding,
        viewer_card.y + style.world_top_offset,
        world_w,
        world_h,
    )
    chart_card = pygame.Rect(viewer_card.right + style.gap, viewer_card.y, SIDEBAR_WIDTH, chart_card_h)
    controls_card = pygame.Rect(
        chart_card.x,
        chart_card.bottom + style.gap,
        SIDEBAR_WIDTH,
        main_h - chart_card_h - style.gap,
    )

    while True:
        if model_ui.running:
            model_ui.step()

        screen.fill(style.background_color)
        _draw_header_banner(
            screen,
            header_rect,
            small_font=small_font,
            title_font=title_font,
            caption_font=subtitle_font,
        )

        _draw_card(screen, viewer_card)
        viewer_eyebrow = label_font.render("WORLD", True, style.button_primary)
        viewer_title = panel_title_font.render(
            "Cooperation field" if model_ui.view_mode == "cooperation" else "Lineage structure",
            True,
            style.text_color,
        )
        viewer_subtitle = label_font.render(
            "Each cell is one inherited agent on the lattice.",
            True,
            style.muted_text,
        )
        screen.blit(viewer_eyebrow, (viewer_card.x + 18, viewer_card.y + 18))
        screen.blit(viewer_title, (viewer_card.x + 18, viewer_card.y + 36))
        screen.blit(viewer_subtitle, (viewer_card.x + 18, viewer_card.y + 62))
        _draw_world(screen, model_ui, world_rect, cell_size=cell_size)

        _draw_chart(
            screen,
            chart_card,
            model_ui,
            label_font=label_font,
            title_font=panel_title_font,
            legend_font=label_font,
        )
        button_map = _draw_controls_and_stats(
            screen,
            controls_card,
            model_ui,
            title_font=panel_title_font,
            label_font=label_font,
            body_font=body_font,
            chip_font=chip_font,
        )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    model_ui.running = not model_ui.running
                elif event.key in (pygame.K_s, pygame.K_RIGHT):
                    model_ui.running = False
                    model_ui.step()
                elif event.key == pygame.K_r:
                    model_ui.reset()
                elif event.key in (pygame.K_v,):
                    model_ui.toggle_view()
                elif event.key == pygame.K_c:
                    model_ui.view_mode = "cooperation"
                elif event.key == pygame.K_l:
                    model_ui.view_mode = "lineage"
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    model_ui.current_fps = min(60, model_ui.current_fps + 1)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    model_ui.current_fps = max(1, model_ui.current_fps - 1)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_map["toggle_run"].collidepoint(event.pos):
                    model_ui.running = not model_ui.running
                elif button_map["step"].collidepoint(event.pos):
                    model_ui.running = False
                    model_ui.step()
                elif button_map["reset"].collidepoint(event.pos):
                    model_ui.reset()
                elif button_map["view_cooperation"].collidepoint(event.pos):
                    model_ui.view_mode = "cooperation"
                elif button_map["view_lineage"].collidepoint(event.pos):
                    model_ui.view_mode = "lineage"
                elif button_map["fps_down"].collidepoint(event.pos):
                    model_ui.current_fps = max(1, model_ui.current_fps - 1)
                elif button_map["fps_up"].collidepoint(event.pos):
                    model_ui.current_fps = min(60, model_ui.current_fps + 1)

        clock.tick(model_ui.current_fps)


if __name__ == "__main__":
    main()
