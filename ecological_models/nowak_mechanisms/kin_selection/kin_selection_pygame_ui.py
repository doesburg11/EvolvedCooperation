#!/usr/bin/env python3
"""
Live Pygame viewer for the ecological kin-selection model.

Run from the repository root with:
  ./.conda/bin/python -m ecological_models.nowak_mechanisms.kin_selection.kin_selection_pygame_ui
"""

from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass

import pygame

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m "
        "ecological_models.nowak_mechanisms.kin_selection.kin_selection_pygame_ui'."
    )

from .config.kin_selection_config import config as active_config
from .config.kin_selection_config import resolve_config
from .kin_selection_model import (
    STAGE_ADULT,
    STAGE_ELDER,
    STAGE_JUVENILE,
    EcologicalKinSelectionModel,
    Individual,
)


SIDEBAR_WIDTH = 380
VIEW_MODES = ("trait", "stage", "group", "energy")


@dataclass(frozen=True)
class ViewerStyle:
    margin: int = 16
    gap: int = 14
    card_padding: int = 18
    header_height: int = 92
    world_top_offset: int = 112
    world_footer_height: int = 54
    background_color: tuple[int, int, int] = (255, 255, 255)
    card_background: tuple[int, int, int] = (247, 250, 252)
    card_border: tuple[int, int, int] = (210, 222, 235)
    header_background: tuple[int, int, int] = (26, 58, 92)
    header_text: tuple[int, int, int] = (255, 255, 255)
    text_color: tuple[int, int, int] = (31, 41, 55)
    muted_text: tuple[int, int, int] = (88, 104, 123)
    button_primary: tuple[int, int, int] = (33, 88, 151)
    button_secondary: tuple[int, int, int] = (103, 150, 198)
    button_text: tuple[int, int, int] = (255, 255, 255)
    empty_cell: tuple[int, int, int] = (238, 242, 247)
    panel_fill: tuple[int, int, int] = (250, 252, 254)
    panel_border: tuple[int, int, int] = (199, 213, 228)
    low_trait: tuple[int, int, int] = (235, 238, 226)
    mid_trait: tuple[int, int, int] = (96, 165, 170)
    high_trait: tuple[int, int, int] = (172, 68, 88)
    juvenile_color: tuple[int, int, int] = (57, 117, 181)
    adult_color: tuple[int, int, int] = (57, 148, 107)
    elder_color: tuple[int, int, int] = (132, 86, 164)
    chart_axis: tuple[int, int, int] = (111, 128, 148)
    chart_grid: tuple[int, int, int] = (224, 232, 240)
    mean_trait_line: tuple[int, int, int] = (172, 68, 88)
    care_relatedness_line: tuple[int, int, int] = (92, 75, 176)
    kin_care_line: tuple[int, int, int] = (8, 137, 155)
    population_line: tuple[int, int, int] = (31, 41, 55)


@dataclass(frozen=True)
class ViewerLayout:
    window_w: int
    window_h: int
    header_rect: pygame.Rect
    world_card: pygame.Rect
    world_rect: pygame.Rect
    chart_card: pygame.Rect
    controls_card: pygame.Rect
    cell_size: int
    group_columns: int
    group_rows: int
    group_cell_columns: int
    group_cell_rows: int
    group_gap: int


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


def _draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    *,
    active: bool = False,
) -> None:
    fill = STYLE.button_primary if active else STYLE.button_secondary
    pygame.draw.rect(screen, fill, rect)
    label = font.render(text, True, STYLE.button_text)
    screen.blit(
        label,
        (
            rect.x + (rect.width - label.get_width()) // 2,
            rect.y + (rect.height - label.get_height()) // 2,
        ),
    )


def _clean_value(value: float) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return float(value)


def _lerp_color(
    low: tuple[int, int, int],
    high: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, ratio))
    return tuple(
        int(round(start + (end - start) * ratio))
        for start, end in zip(low, high, strict=True)
    )


def _trait_color(value: float) -> tuple[int, int, int]:
    if value <= 0.5:
        return _lerp_color(STYLE.low_trait, STYLE.mid_trait, value / 0.5)
    return _lerp_color(STYLE.mid_trait, STYLE.high_trait, (value - 0.5) / 0.5)


def _energy_color(value: float, max_energy: float) -> tuple[int, int, int]:
    ratio = value / max(1e-9, max_energy)
    return _lerp_color((231, 95, 69), (78, 161, 92), ratio)


def _group_color(group_id: int) -> tuple[int, int, int]:
    hue = (group_id * 0.6180339887498949) % 1.0
    saturation = 0.58
    value = 0.82
    red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)
    return int(red * 255), int(green * 255), int(blue * 255)


def _stage_color(stage: str) -> tuple[int, int, int]:
    if stage == STAGE_JUVENILE:
        return STYLE.juvenile_color
    if stage == STAGE_ADULT:
        return STYLE.adult_color
    return STYLE.elder_color


def _individual_color(
    individual: Individual,
    *,
    view_mode: str,
    max_energy: float,
) -> tuple[int, int, int]:
    if view_mode == "stage":
        return _stage_color(individual.stage)
    if view_mode == "group":
        return _group_color(individual.group_id)
    if view_mode == "energy":
        return _energy_color(individual.energy, max_energy)
    return _trait_color(individual.helping_trait)


class ModelUI:
    def __init__(self) -> None:
        self.config = resolve_config(active_config)
        self.running = False
        self.current_fps = int(self.config["live_viewer_frames_per_second"])
        self.view_mode = "trait"
        self.reset()

    def reset(self) -> None:
        self.model = EcologicalKinSelectionModel(self.config)
        self.running = False

    def step(self) -> bool:
        if not self.model.individuals:
            self.running = False
            return False
        if self.model.step_index >= int(self.config["simulation_steps"]):
            self.running = False
            return False
        self.model.step()
        if self.model.step_index >= int(self.config["simulation_steps"]):
            self.running = False
        return bool(self.model.individuals)

    def latest_value(self, key: str) -> float:
        values = self.model.history.get(key, [])
        if not values:
            return math.nan
        value = _clean_value(float(values[-1]))
        return math.nan if value is None else value

    def toggle_view(self) -> None:
        index = VIEW_MODES.index(self.view_mode)
        self.view_mode = VIEW_MODES[(index + 1) % len(VIEW_MODES)]


def build_layout(model_ui: ModelUI) -> ViewerLayout:
    cfg = model_ui.config
    cell_size = int(cfg["live_viewer_cell_size"])
    group_columns = int(cfg["live_viewer_group_columns"])
    group_count = int(cfg["initial_group_count"])
    group_rows = math.ceil(group_count / group_columns)
    group_cell_columns = int(cfg["live_viewer_group_cell_columns"])
    group_cell_rows = int(cfg["live_viewer_group_cell_rows"])
    group_gap = 8

    group_w = group_cell_columns * cell_size
    group_h = group_cell_rows * cell_size
    world_w = group_columns * group_w + (group_columns - 1) * group_gap
    world_h = group_rows * group_h + (group_rows - 1) * group_gap
    world_card_w = world_w + STYLE.card_padding * 2
    world_card_h = world_h + STYLE.world_top_offset + STYLE.world_footer_height
    chart_card_h = 330
    controls_card_h = max(world_card_h - chart_card_h - STYLE.gap, 360)
    main_h = max(world_card_h, chart_card_h + STYLE.gap + controls_card_h)
    window_w = STYLE.margin * 2 + world_card_w + STYLE.gap + SIDEBAR_WIDTH
    window_h = STYLE.margin * 2 + STYLE.header_height + STYLE.gap + main_h

    header_rect = pygame.Rect(
        STYLE.margin,
        STYLE.margin,
        window_w - STYLE.margin * 2,
        STYLE.header_height,
    )
    world_card = pygame.Rect(
        STYLE.margin,
        header_rect.bottom + STYLE.gap,
        world_card_w,
        world_card_h,
    )
    world_rect = pygame.Rect(
        world_card.x + STYLE.card_padding,
        world_card.y + STYLE.world_top_offset,
        world_w,
        world_h,
    )
    chart_card = pygame.Rect(
        world_card.right + STYLE.gap,
        world_card.y,
        SIDEBAR_WIDTH,
        chart_card_h,
    )
    controls_card = pygame.Rect(
        chart_card.x,
        chart_card.bottom + STYLE.gap,
        SIDEBAR_WIDTH,
        main_h - chart_card_h - STYLE.gap,
    )
    return ViewerLayout(
        window_w=window_w,
        window_h=window_h,
        header_rect=header_rect,
        world_card=world_card,
        world_rect=world_rect,
        chart_card=chart_card,
        controls_card=controls_card,
        cell_size=cell_size,
        group_columns=group_columns,
        group_rows=group_rows,
        group_cell_columns=group_cell_columns,
        group_cell_rows=group_cell_rows,
        group_gap=group_gap,
    )


def _draw_header(
    screen: pygame.Surface,
    rect: pygame.Rect,
    *,
    small_font: pygame.font.Font,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
) -> None:
    _draw_card(screen, rect, fill=STYLE.header_background, border=STYLE.header_background)
    eyebrow = small_font.render("ECOLOGICAL NOWAK MECHANISMS", True, STYLE.header_text)
    title = title_font.render("Kin Selection Live Grid", True, STYLE.header_text)
    subtitle = body_font.render(
        "Sexual reproduction, pedigree relatedness, juvenile rearing, and kin-biased care.",
        True,
        STYLE.header_text,
    )
    screen.blit(eyebrow, (rect.x + 20, rect.y + 13))
    screen.blit(title, (rect.x + 20, rect.y + 29))
    screen.blit(subtitle, (rect.x + 20, rect.y + 67))


def _individual_sort_key(individual: Individual) -> tuple[int, int, int, int]:
    stage_order = {STAGE_JUVENILE: 0, STAGE_ADULT: 1, STAGE_ELDER: 2}
    return (stage_order[individual.stage], individual.age, individual.sex == "M", individual.id)


def _draw_world(
    screen: pygame.Surface,
    model_ui: ModelUI,
    layout: ViewerLayout,
    *,
    label_font: pygame.font.Font,
    title_font: pygame.font.Font,
) -> None:
    _draw_card(screen, layout.world_card)
    eyebrow = label_font.render("GROUP GRID", True, STYLE.button_primary)
    title = title_font.render(f"View: {model_ui.view_mode}", True, STYLE.text_color)
    subtitle = label_font.render(
        "Each block is a group; each filled cell is one living individual.",
        True,
        STYLE.muted_text,
    )
    screen.blit(eyebrow, (layout.world_card.x + 18, layout.world_card.y + 16))
    screen.blit(title, (layout.world_card.x + 18, layout.world_card.y + 34))
    screen.blit(subtitle, (layout.world_card.x + 18, layout.world_card.y + 62))

    grouped: dict[int, list[Individual]] = {
        group_id: []
        for group_id in range(int(model_ui.config["initial_group_count"]))
    }
    for individual in model_ui.model.individuals:
        grouped.setdefault(individual.group_id, []).append(individual)

    max_energy = float(model_ui.config["max_energy"])
    group_w = layout.group_cell_columns * layout.cell_size
    group_h = layout.group_cell_rows * layout.cell_size
    for group_id, individuals in grouped.items():
        group_col = group_id % layout.group_columns
        group_row = group_id // layout.group_columns
        group_x = layout.world_rect.x + group_col * (group_w + layout.group_gap)
        group_y = layout.world_rect.y + group_row * (group_h + layout.group_gap)
        group_rect = pygame.Rect(group_x, group_y, group_w, group_h)
        pygame.draw.rect(screen, STYLE.panel_fill, group_rect)
        pygame.draw.rect(screen, STYLE.panel_border, group_rect, 1)

        label = label_font.render(str(group_id), True, STYLE.muted_text)
        screen.blit(label, (group_rect.x + 3, group_rect.y + 2))

        sorted_individuals = sorted(individuals, key=_individual_sort_key)
        capacity = layout.group_cell_columns * layout.group_cell_rows
        for index, individual in enumerate(sorted_individuals[:capacity]):
            cell_col = index % layout.group_cell_columns
            cell_row = index // layout.group_cell_columns
            cell_rect = pygame.Rect(
                group_rect.x + cell_col * layout.cell_size,
                group_rect.y + cell_row * layout.cell_size,
                layout.cell_size,
                layout.cell_size,
            )
            color = _individual_color(
                individual,
                view_mode=model_ui.view_mode,
                max_energy=max_energy,
            )
            pygame.draw.rect(screen, color, cell_rect.inflate(-1, -1))

        if len(sorted_individuals) > capacity:
            overflow = label_font.render("+", True, STYLE.text_color)
            screen.blit(overflow, (group_rect.right - 10, group_rect.bottom - 15))

    legend_y = layout.world_card.bottom - 36
    if model_ui.view_mode == "stage":
        legend = (
            ("juvenile", STYLE.juvenile_color),
            ("adult", STYLE.adult_color),
            ("elder", STYLE.elder_color),
        )
    elif model_ui.view_mode == "energy":
        legend = (("low energy", _energy_color(0.0, 1.0)), ("high energy", _energy_color(1.0, 1.0)))
    elif model_ui.view_mode == "group":
        legend = (("group color", _group_color(0)), ("different group", _group_color(1)))
    else:
        legend = (("low h", _trait_color(0.0)), ("mid h", _trait_color(0.5)), ("high h", _trait_color(1.0)))

    cursor_x = layout.world_card.x + 18
    for label, color in legend:
        pygame.draw.rect(screen, color, (cursor_x, legend_y + 4, 16, 12))
        surface = label_font.render(label, True, STYLE.text_color)
        screen.blit(surface, (cursor_x + 22, legend_y))
        cursor_x += 38 + surface.get_width()


def _draw_line_series(
    screen: pygame.Surface,
    rect: pygame.Rect,
    steps: list[int],
    values: list[float],
    *,
    color: tuple[int, int, int],
    max_step: int,
    max_value: float,
    line_width: int = 3,
) -> None:
    points = []
    for step, value in zip(steps, values, strict=True):
        clean = _clean_value(value)
        if clean is None:
            continue
        x = rect.x + int((step / max(1, max_step)) * rect.width)
        y = rect.bottom - int((max(0.0, min(max_value, clean)) / max_value) * rect.height)
        points.append((x, y))
    if len(points) >= 2:
        pygame.draw.lines(screen, color, False, points, line_width)


def _draw_chart(
    screen: pygame.Surface,
    rect: pygame.Rect,
    model_ui: ModelUI,
    *,
    label_font: pygame.font.Font,
    title_font: pygame.font.Font,
) -> None:
    _draw_card(screen, rect)
    eyebrow = label_font.render("HISTORY", True, STYLE.button_primary)
    title = title_font.render("Selection And Rearing", True, STYLE.text_color)
    screen.blit(eyebrow, (rect.x + 18, rect.y + 14))
    screen.blit(title, (rect.x + 18, rect.y + 32))

    plot = pygame.Rect(rect.x + 46, rect.y + 78, rect.width - 64, rect.height - 126)
    pygame.draw.rect(screen, (255, 255, 255), plot)
    pygame.draw.rect(screen, STYLE.card_border, plot, 1)
    for tick in range(5):
        y = plot.bottom - (tick / 4) * plot.height
        pygame.draw.line(screen, STYLE.chart_grid, (plot.x, y), (plot.right, y), 1)
    pygame.draw.line(screen, STYLE.chart_axis, (plot.x, plot.y), (plot.x, plot.bottom), 2)
    pygame.draw.line(screen, STYLE.chart_axis, (plot.x, plot.bottom), (plot.right, plot.bottom), 1)

    history = model_ui.model.history
    steps = [int(value) for value in history["step"]]
    max_step = int(model_ui.config["simulation_steps"])
    population_scaled = [
        float(value) / max(1.0, float(model_ui.config["max_population"]))
        for value in history["population"]
    ]
    series = (
        ("mean_helping_trait", STYLE.mean_trait_line, "Mean h"),
        ("mean_care_relatedness", STYLE.care_relatedness_line, "Care r"),
        ("kin_care_fraction", STYLE.kin_care_line, "Kin care"),
    )
    for key, color, _ in series:
        _draw_line_series(
            screen,
            plot,
            steps,
            [float(value) for value in history[key]],
            color=color,
            max_step=max_step,
            max_value=1.0,
        )
    _draw_line_series(
        screen,
        plot,
        steps,
        population_scaled,
        color=STYLE.population_line,
        max_step=max_step,
        max_value=1.0,
        line_width=2,
    )

    legend = (
        ("Mean h", STYLE.mean_trait_line),
        ("Care r", STYLE.care_relatedness_line),
        ("Kin care", STYLE.kin_care_line),
        ("Pop/cap", STYLE.population_line),
    )
    cursor_x = rect.x + 18
    legend_y = rect.bottom - 28
    for label, color in legend:
        pygame.draw.rect(screen, color, (cursor_x, legend_y + 4, 16, 12))
        surface = label_font.render(label, True, STYLE.text_color)
        screen.blit(surface, (cursor_x + 22, legend_y))
        cursor_x += 34 + surface.get_width()


def _format_float(value: float) -> str:
    if not math.isfinite(value):
        return "n/a"
    return f"{value:.3f}"


def _draw_controls(
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
    title = title_font.render("Run State", True, STYLE.text_color)
    screen.blit(eyebrow, (rect.x + 18, rect.y + 14))
    screen.blit(title, (rect.x + 18, rect.y + 32))

    button_map: dict[str, pygame.Rect] = {}
    button_w = 102
    button_h = 34
    x0 = rect.x + 18
    x1 = x0 + button_w + 10
    x2 = x1 + button_w + 10
    y0 = rect.y + 72
    button_map["toggle_run"] = pygame.Rect(x0, y0, button_w, button_h)
    button_map["step"] = pygame.Rect(x1, y0, button_w, button_h)
    button_map["reset"] = pygame.Rect(x2, y0, button_w, button_h)
    button_map["view_trait"] = pygame.Rect(x0, y0 + 46, 76, button_h)
    button_map["view_stage"] = pygame.Rect(x0 + 86, y0 + 46, 80, button_h)
    button_map["view_group"] = pygame.Rect(x0 + 176, y0 + 46, 82, button_h)
    button_map["view_energy"] = pygame.Rect(x0 + 268, y0 + 46, 80, button_h)
    button_map["fps_down"] = pygame.Rect(x0, y0 + 92, 70, button_h)
    button_map["fps_up"] = pygame.Rect(x0 + 80, y0 + 92, 70, button_h)

    _draw_button(screen, button_map["toggle_run"], "Pause" if model_ui.running else "Play", chip_font, active=True)
    _draw_button(screen, button_map["step"], "Step", chip_font)
    _draw_button(screen, button_map["reset"], "Reset", chip_font)
    for mode in VIEW_MODES:
        _draw_button(
            screen,
            button_map[f"view_{mode}"],
            mode.title(),
            chip_font,
            active=model_ui.view_mode == mode,
        )
    _draw_button(screen, button_map["fps_down"], "FPS -", chip_font)
    _draw_button(screen, button_map["fps_up"], "FPS +", chip_font)

    stats = (
        ("Step", f"{model_ui.model.step_index}/{int(model_ui.config['simulation_steps'])}"),
        ("Population", f"{len(model_ui.model.individuals)}/{int(model_ui.config['max_population'])}"),
        ("Mean h", _format_float(model_ui.latest_value("mean_helping_trait"))),
        ("Adult h", _format_float(model_ui.latest_value("adult_mean_helping_trait"))),
        ("Juvenile survival", _format_float(model_ui.latest_value("juvenile_survival_rate"))),
        ("Care relatedness", _format_float(model_ui.latest_value("mean_care_relatedness"))),
        ("Kin care fraction", _format_float(model_ui.latest_value("kin_care_fraction"))),
        ("Mate relatedness", _format_float(model_ui.latest_value("mean_mate_relatedness"))),
        ("Outside mating", _format_float(model_ui.latest_value("outside_group_mating_fraction"))),
        ("Births / deaths", f"{int(model_ui.latest_value('births'))} / {int(model_ui.latest_value('deaths'))}"),
        ("FPS", str(model_ui.current_fps)),
    )
    stats_top = button_map["fps_down"].bottom + 20
    for index, (label, value) in enumerate(stats):
        y = stats_top + index * 27
        label_surface = label_font.render(label, True, STYLE.muted_text)
        value_surface = body_font.render(value, True, STYLE.text_color)
        screen.blit(label_surface, (rect.x + 20, y))
        screen.blit(value_surface, (rect.x + 172, y - 2))

    footer = (
        "Keys: Space play/pause, S or Right step, R reset, "
        "V toggle view, 1-4 views, +/- speed"
    )
    footer_top = rect.bottom - 50
    for index, line in enumerate((footer[:62], footer[62:])):
        surface = label_font.render(line.strip(), True, STYLE.muted_text)
        screen.blit(surface, (rect.x + 18, footer_top + index * 18))

    return button_map


def draw_frame(
    screen: pygame.Surface,
    model_ui: ModelUI,
    layout: ViewerLayout,
    fonts: dict[str, pygame.font.Font],
) -> dict[str, pygame.Rect]:
    screen.fill(STYLE.background_color)
    _draw_header(
        screen,
        layout.header_rect,
        small_font=fonts["small"],
        title_font=fonts["title"],
        body_font=fonts["body"],
    )
    _draw_world(
        screen,
        model_ui,
        layout,
        label_font=fonts["label"],
        title_font=fonts["panel_title"],
    )
    _draw_chart(
        screen,
        layout.chart_card,
        model_ui,
        label_font=fonts["label"],
        title_font=fonts["panel_title"],
    )
    return _draw_controls(
        screen,
        layout.controls_card,
        model_ui,
        title_font=fonts["panel_title"],
        label_font=fonts["label"],
        body_font=fonts["body"],
        chip_font=fonts["chip"],
    )


def _make_fonts() -> dict[str, pygame.font.Font]:
    return {
        "small": pygame.font.SysFont(None, 20),
        "title": pygame.font.SysFont(None, 38),
        "panel_title": pygame.font.SysFont(None, 28),
        "label": pygame.font.SysFont(None, 20),
        "body": pygame.font.SysFont(None, 23),
        "chip": pygame.font.SysFont(None, 22),
    }


def _handle_key(model_ui: ModelUI, key: int) -> None:
    if key == pygame.K_SPACE:
        model_ui.running = not model_ui.running
    elif key in (pygame.K_s, pygame.K_RIGHT):
        model_ui.running = False
        model_ui.step()
    elif key == pygame.K_r:
        model_ui.reset()
    elif key == pygame.K_v:
        model_ui.toggle_view()
    elif key == pygame.K_1:
        model_ui.view_mode = "trait"
    elif key == pygame.K_2:
        model_ui.view_mode = "stage"
    elif key == pygame.K_3:
        model_ui.view_mode = "group"
    elif key == pygame.K_4:
        model_ui.view_mode = "energy"
    elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
        model_ui.current_fps = min(60, model_ui.current_fps + 1)
    elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
        model_ui.current_fps = max(1, model_ui.current_fps - 1)


def _handle_click(model_ui: ModelUI, button_map: dict[str, pygame.Rect], pos: tuple[int, int]) -> None:
    if button_map["toggle_run"].collidepoint(pos):
        model_ui.running = not model_ui.running
    elif button_map["step"].collidepoint(pos):
        model_ui.running = False
        model_ui.step()
    elif button_map["reset"].collidepoint(pos):
        model_ui.reset()
    elif button_map["fps_down"].collidepoint(pos):
        model_ui.current_fps = max(1, model_ui.current_fps - 1)
    elif button_map["fps_up"].collidepoint(pos):
        model_ui.current_fps = min(60, model_ui.current_fps + 1)
    else:
        for mode in VIEW_MODES:
            if button_map[f"view_{mode}"].collidepoint(pos):
                model_ui.view_mode = mode
                return


def main() -> None:
    pygame.init()
    model_ui = ModelUI()
    layout = build_layout(model_ui)
    screen = pygame.display.set_mode((layout.window_w, layout.window_h))
    pygame.display.set_caption("Ecological Kin Selection Live Grid")
    clock = pygame.time.Clock()
    fonts = _make_fonts()
    button_map: dict[str, pygame.Rect] = {}

    while True:
        if model_ui.running:
            model_ui.step()

        button_map = draw_frame(screen, model_ui, layout, fonts)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                _handle_key(model_ui, event.key)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                _handle_click(model_ui, button_map, event.pos)

        clock.tick(model_ui.current_fps)


if __name__ == "__main__":
    main()
