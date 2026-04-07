#!/usr/bin/env python3
"""
Interactive Pygame UI for the spatial altruism model.

Edit `spatial_altruism/config/altruism_config.py`, then run from the repo root:
  ./.conda/bin/python -m spatial_altruism.altruism_pygame_ui
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m spatial_altruism.altruism_pygame_ui'."
    )

from .altruism_model import AltruismModel, make_params
from .config.altruism_config import config as model_config, resolve_config
from .utils.pygame_helpers import draw_grid, plot_history

CFG = resolve_config(model_config)

WIDTH = int(CFG["ui_window_width"])
HEIGHT = int(CFG["ui_window_height"])
PLOT_HEIGHT = int(CFG["ui_plot_height"])
SIDE_PANEL_WIDTH = int(CFG["ui_side_panel_width"])
GRID_WIDTH = int(CFG["width"])
GRID_HEIGHT = int(CFG["height"])
CELL_SIZE = min(WIDTH // GRID_WIDTH, HEIGHT // GRID_HEIGHT)
FPS = int(CFG["ui_frames_per_second"])


@dataclass(frozen=True)
class GuiStyle:
    margin: int = 16
    gap: int = 16
    card_padding: int = 18
    header_height: int = 96
    viewer_top_offset: int = 146
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
    empty_color: tuple[int, int, int] = (244, 239, 229)
    selfish_color: tuple[int, int, int] = (45, 95, 186)
    altruist_color: tuple[int, int, int] = (171, 53, 87)


UI_STYLE = GuiStyle()


class Slider:
    def __init__(self, x, y, w, label, minval, maxval, value, font, param_name):
        self.x = x
        self.y = y
        self.w = w
        self.rect = pygame.Rect(x, y, w, 36)
        self.label = label
        self.minval = minval
        self.maxval = maxval
        self.value = value
        self.font = font
        self.param_name = param_name
        self.dragging = False
        self.editing = False
        self.text = f"{self.value:.2f}"
        self.value_rect = None

    def draw(self, screen):
        label_surf = self.font.render(self.label, True, UI_STYLE.text_color)
        label_y = self.rect.y
        screen.blit(label_surf, (self.rect.x, label_y))

        bar_y = label_y + label_surf.get_height() + 10
        bar_rect = pygame.Rect(self.rect.x, bar_y, self.rect.w, 14)
        pygame.draw.rect(screen, UI_STYLE.accent_panel, bar_rect, border_radius=7)
        pygame.draw.rect(screen, UI_STYLE.card_border, bar_rect, 1, border_radius=7)

        pos = int((self.value - self.minval) / (self.maxval - self.minval) * self.rect.w)
        handle_rect = pygame.Rect(self.rect.x + pos - 10, bar_y - 8, 20, 30)
        handle_color = UI_STYLE.header_background if self.dragging else UI_STYLE.button_primary
        pygame.draw.rect(screen, handle_color, handle_rect, border_radius=6)

        value_x = self.rect.x + self.rect.w + 18
        value_y = bar_y - 7
        self.value_rect = pygame.Rect(value_x, value_y, 66, 28)
        pygame.draw.rect(screen, (255, 255, 255), self.value_rect, border_radius=4)
        pygame.draw.rect(screen, UI_STYLE.card_border, self.value_rect, 2, border_radius=4)
        value_color = UI_STYLE.button_primary if self.editing else UI_STYLE.text_color
        value_text = self.text if self.editing else f"{self.value:.2f}"
        val_surf = self.font.render(value_text, True, value_color)
        screen.blit(
            val_surf,
            (
                self.value_rect.x + 6,
                self.value_rect.y + (self.value_rect.height - val_surf.get_height()) // 2,
            ),
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                return True
            if self.value_rect and self.value_rect.collidepoint(event.pos):
                self.editing = True
                self.text = f"{self.value:.2f}"
                return True
            self.editing = False
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            relx = min(max(event.pos[0] - self.rect.x, 0), self.rect.w)
            self.value = self.minval + (self.maxval - self.minval) * relx / self.rect.w
            self.value = min(max(self.value, self.minval), self.maxval)
            self.text = f"{self.value:.2f}"
            return True

        if self.editing and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                try:
                    value = float(self.text)
                    self.value = min(max(value, self.minval), self.maxval)
                except ValueError:
                    pass
                self.editing = False
                return True
            if event.key == pygame.K_ESCAPE:
                self.editing = False
                return True
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 8 and (event.unicode.isdigit() or event.unicode in ".-"):
                self.text += event.unicode
            return True

        return False


class ModelUI:
    def __init__(self):
        self.params = make_params({"width": GRID_WIDTH, "height": GRID_HEIGHT})
        self.model = AltruismModel(self.params)
        self.history = []
        self.running = False
        self.ticks = 0

    def reset(self):
        self.model = AltruismModel(self.params)
        self.history = []
        self.ticks = 0
        self.running = False

    def step(self):
        alive = self.model.go()
        self.history.append(self.model.counts())
        self.ticks = self.model.ticks
        if not alive:
            self.running = False
        return alive

    def run(self, steps=1):
        for _ in range(steps):
            if not self.step():
                break


def main():
    style = UI_STYLE
    world_w = GRID_WIDTH * CELL_SIZE
    world_h = GRID_HEIGHT * CELL_SIZE
    plot_card_height = max(PLOT_HEIGHT + 40, 300)
    viewer_card_w = world_w + style.card_padding * 2
    viewer_card_h = world_h + style.viewer_top_offset + style.viewer_footer_height
    controls_card_h = max(viewer_card_h - plot_card_height - style.gap, 360)
    main_h = max(viewer_card_h, plot_card_height + style.gap + controls_card_h)
    window_w = style.margin * 2 + viewer_card_w + style.gap + SIDE_PANEL_WIDTH
    window_h = style.margin * 2 + style.header_height + style.gap + main_h

    pygame.init()
    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption("Spatial Altruism Replay")
    clock = pygame.time.Clock()

    small_font = pygame.font.SysFont(None, 20)
    panel_font = pygame.font.SysFont(None, 28)
    panel_large_font = pygame.font.SysFont(None, 32)
    panel_caption_font = pygame.font.SysFont(None, 20)

    header_rect = pygame.Rect(style.margin, style.margin, window_w - style.margin * 2, style.header_height)
    viewer_card = pygame.Rect(style.margin, header_rect.bottom + style.gap, viewer_card_w, viewer_card_h)
    world_rect = pygame.Rect(
        viewer_card.x + style.card_padding,
        viewer_card.y + style.viewer_top_offset,
        world_w,
        world_h,
    )
    chart_card = pygame.Rect(viewer_card.right + style.gap, viewer_card.y, SIDE_PANEL_WIDTH, plot_card_height)
    controls_card = pygame.Rect(
        chart_card.x,
        chart_card.bottom + style.gap,
        SIDE_PANEL_WIDTH,
        main_h - plot_card_height - style.gap,
    )
    plot_rect = pygame.Rect(chart_card.x + 18, chart_card.y + 78, chart_card.width - 36, chart_card.height - 96)

    button_y = viewer_card.y + 68
    button_rect = pygame.Rect(viewer_card.x + 18, button_y, 92, 34)
    reset_rect = pygame.Rect(button_rect.right + 10, button_y, 92, 34)
    plot_toggle_rect = pygame.Rect(reset_rect.right + 10, button_y, 112, 34)
    step_button_rect = pygame.Rect(plot_toggle_rect.right + 10, button_y, 88, 34)
    fps_rect = pygame.Rect(viewer_card.right - 102, button_y, 84, 34)

    model_ui = ModelUI()
    plot_visible = bool(CFG["ui_history_visible_default"])
    plot_img_holder = None
    current_fps = FPS

    slider_specs = [
        ("altruistic-probability", 0.0, 1.0, model_ui.params.altruistic_probability, "altruistic_probability"),
        ("selfish-probability", 0.0, 1.0, model_ui.params.selfish_probability, "selfish_probability"),
        ("cost-of-altruism", 0.0, 1.0, model_ui.params.cost_of_altruism, "cost_of_altruism"),
        (
            "benefit-from-altruism",
            0.0,
            1.0,
            model_ui.params.benefit_from_altruism,
            "benefit_from_altruism",
        ),
    ]
    if model_ui.params.model_variant == "steady_state":
        slider_specs.append(("disease", 0.0, 1.0, model_ui.params.disease, "disease"))
    slider_specs.append(("harshness", 0.0, 1.0, model_ui.params.harshness, "harshness"))

    slider_x = controls_card.x + 18
    slider_w = controls_card.width - 102
    slider_y0 = controls_card.y + 116
    slider_gap = 48
    sliders = [
        Slider(
            slider_x,
            slider_y0 + index * slider_gap,
            slider_w,
            label,
            min_value,
            max_value,
            value,
            small_font,
            param_name,
        )
        for index, (label, min_value, max_value, value, param_name) in enumerate(slider_specs)
    ]

    def update_plot():
        nonlocal plot_img_holder
        if plot_visible:
            plot_img_holder = plot_history(
                model_ui.history,
                max_width=plot_rect.width,
                max_height=plot_rect.height,
            )
        else:
            plot_img_holder = None

    def reset_model():
        model_ui.reset()
        update_plot()

    def commit_slider(slider: Slider):
        setattr(model_ui.params, slider.param_name, slider.value)
        reset_model()

    def draw_card(rect: pygame.Rect, fill=None, border=None):
        pygame.draw.rect(screen, fill or style.card_background, rect)
        pygame.draw.rect(screen, border or style.card_border, rect, 1)

    def draw_chip(rect: pygame.Rect, text: str, fill: tuple[int, int, int], text_color: tuple[int, int, int]):
        pygame.draw.rect(screen, fill, rect)
        label = small_font.render(text, True, text_color)
        screen.blit(
            label,
            (rect.x + (rect.width - label.get_width()) // 2, rect.y + (rect.height - label.get_height()) // 2),
        )

    def draw_header_banner():
        draw_card(header_rect, fill=style.header_background, border=style.header_background)
        eyebrow = small_font.render("EVOLVED COOPERATION", True, style.header_text)
        title = panel_large_font.render("Spatial Altruism Live Grid", True, style.header_text)
        subtitle = panel_caption_font.render(
            "Patch-lottery viewer styled to match the cooperative-hunting replay shell.",
            True,
            style.header_text,
        )
        screen.blit(eyebrow, (header_rect.x + 20, header_rect.y + 14))
        screen.blit(title, (header_rect.x + 20, header_rect.y + 30))
        screen.blit(subtitle, (header_rect.x + 20, header_rect.y + 70))

    def draw_viewer_shell(pink: int, green: int, black: int):
        draw_card(viewer_card)
        eyebrow = small_font.render("REPLAY", True, style.button_primary)
        title = panel_font.render("World State", True, style.text_color)
        if model_ui.params.model_variant == "uniform_culling":
            subtitle_text = "Periodic uniform culling clears a fixed share of sites on schedule."
        elif model_ui.params.model_variant == "compact_swath":
            subtitle_text = "Periodic compact-swath culling clears a square region on schedule."
        else:
            subtitle_text = "Altruists and selfish patches compete for each lattice site."
        subtitle = panel_caption_font.render(subtitle_text, True, style.muted_text)
        screen.blit(eyebrow, (viewer_card.x + 18, viewer_card.y + 14))
        screen.blit(title, (viewer_card.x + 18, viewer_card.y + 31))
        screen.blit(subtitle, (viewer_card.x + 18, viewer_card.y + 54))

        draw_chip(
            button_rect,
            "Pause" if model_ui.running else "Play",
            style.button_primary,
            style.button_text,
        )
        draw_chip(reset_rect, "Reset", style.button_secondary, style.button_text)
        draw_chip(
            plot_toggle_rect,
            "History ON" if plot_visible else "History OFF",
            style.button_secondary if plot_visible else style.button_disabled,
            style.button_text,
        )
        draw_chip(
            step_button_rect,
            "Step",
            style.button_secondary if not model_ui.running else style.button_disabled,
            style.button_text,
        )
        draw_chip(fps_rect, f"{current_fps} fps", style.button_secondary, style.button_text)

        occupancy = (pink + green) / max(pink + green + black, 1)
        playback_label = small_font.render("Occupancy", True, style.muted_text)
        screen.blit(playback_label, (viewer_card.x + 18, viewer_card.y + 112))
        occupancy_rect = pygame.Rect(viewer_card.x + 94, viewer_card.y + 120, viewer_card.width - 94 - 96, 6)
        pygame.draw.rect(screen, style.accent_panel, occupancy_rect)
        pygame.draw.rect(screen, style.card_border, occupancy_rect, 1)
        fill_rect = pygame.Rect(
            occupancy_rect.x,
            occupancy_rect.y,
            int(occupancy_rect.width * occupancy),
            occupancy_rect.height,
        )
        pygame.draw.rect(screen, style.button_primary, fill_rect)
        occupancy_text = small_font.render(f"{occupancy * 100:.0f}%", True, style.muted_text)
        screen.blit(occupancy_text, (viewer_card.right - 18 - occupancy_text.get_width(), viewer_card.y + 108))

        world_frame = pygame.Rect(world_rect.x - 2, world_rect.y - 2, world_rect.width + 4, world_rect.height + 4)
        pygame.draw.rect(screen, style.accent_panel, world_frame)
        pygame.draw.rect(screen, style.card_border, world_frame, 1)

        footer_left = small_font.render(f"Step {model_ui.ticks}", True, style.text_color)
        footer_right = panel_caption_font.render(
            f"Altruists {pink}, selfish {green}, empty {black}.",
            True,
            style.muted_text,
        )
        screen.blit(footer_left, (viewer_card.x + 18, viewer_card.bottom - 42))
        screen.blit(footer_right, (viewer_card.x + 18, viewer_card.bottom - 22))

    def draw_history_card():
        draw_card(chart_card)
        eyebrow = small_font.render("HISTORY", True, style.button_primary)
        title = panel_font.render("Population History", True, style.text_color)
        subtitle = panel_caption_font.render("Altruist and selfish occupancy over time.", True, style.muted_text)
        screen.blit(eyebrow, (chart_card.x + 18, chart_card.y + 14))
        screen.blit(title, (chart_card.x + 18, chart_card.y + 31))
        screen.blit(subtitle, (chart_card.x + 18, chart_card.y + 54))

        pygame.draw.rect(screen, style.accent_panel, plot_rect)
        pygame.draw.rect(screen, style.card_border, plot_rect, 1)
        if plot_visible and plot_img_holder is not None:
            plot_x = plot_rect.x + (plot_rect.width - plot_img_holder.get_width()) // 2
            plot_y = plot_rect.y + (plot_rect.height - plot_img_holder.get_height()) // 2
            screen.blit(plot_img_holder, (plot_x, plot_y))
        else:
            hint_lines = [
                "History rendering is hidden.",
                "Press the History chip or P to show it.",
                f"Samples collected: {len(model_ui.history)}",
            ]
            for index, line in enumerate(hint_lines):
                surface = small_font.render(line, True, style.muted_text)
                surface_x = plot_rect.x + (plot_rect.width - surface.get_width()) // 2
                surface_y = plot_rect.y + 32 + index * 24
                screen.blit(surface, (surface_x, surface_y))

    def draw_controls_card():
        draw_card(controls_card)
        eyebrow = small_font.render("PARAMETERS", True, style.button_primary)
        title = panel_font.render("Interactive Controls", True, style.text_color)
        screen.blit(eyebrow, (controls_card.x + 18, controls_card.y + 14))
        screen.blit(title, (controls_card.x + 18, controls_card.y + 31))

        if model_ui.params.model_variant == "uniform_culling":
            mode_line = (
                "Mode: uniform culling "
                f"(every {model_ui.params.uniform_culling_interval} steps, "
                f"fraction {model_ui.params.uniform_culling_fraction:.2f})"
            )
        elif model_ui.params.model_variant == "compact_swath":
            mode_line = (
                "Mode: compact swath "
                f"(every {model_ui.params.compact_swath_interval} steps, "
                f"fraction {model_ui.params.compact_swath_fraction:.2f})"
            )
        else:
            mode_line = "Mode: steady-state void competition"
        mode_surface = small_font.render(mode_line, True, style.muted_text)
        screen.blit(mode_surface, (controls_card.x + 18, controls_card.y + 52))

        legend_entries = (
            (style.altruist_color, "Altruist"),
            (style.selfish_color, "Selfish"),
            (style.empty_color, "Empty"),
        )
        legend_y = controls_card.y + 82
        legend_x = controls_card.x + 18
        for color, label in legend_entries:
            swatch = pygame.Rect(legend_x, legend_y, 14, 14)
            pygame.draw.rect(screen, color, swatch)
            pygame.draw.rect(screen, style.header_background, swatch, 1)
            label_surface = small_font.render(label, True, style.text_color)
            screen.blit(label_surface, (legend_x + 22, legend_y - 1))
            legend_x += 22 + label_surface.get_width() + 18

        for slider in sliders:
            slider.draw(screen)

    update_plot()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            editing_slider = next((slider for slider in sliders if slider.editing), None)
            if editing_slider and event.type == pygame.KEYDOWN:
                if editing_slider.handle_event(event) and not editing_slider.editing:
                    commit_slider(editing_slider)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    model_ui.running = not model_ui.running
                elif event.key == pygame.K_r:
                    reset_model()
                elif event.key == pygame.K_s and not model_ui.running:
                    model_ui.step()
                    update_plot()
                elif event.key == pygame.K_p:
                    plot_visible = not plot_visible
                    update_plot()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    current_fps = min(120, current_fps + 5)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    current_fps = max(5, current_fps - 5)

            slider_event_handled = False
            for slider in sliders:
                was_dragging = slider.dragging
                if slider.handle_event(event):
                    slider_event_handled = True
                    if not slider.dragging and not slider.editing and event.type == pygame.KEYDOWN:
                        commit_slider(slider)
                    break
                if event.type == pygame.MOUSEBUTTONUP and was_dragging:
                    commit_slider(slider)
                    slider_event_handled = True
                    break
            if slider_event_handled:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    model_ui.running = not model_ui.running
                elif reset_rect.collidepoint(event.pos):
                    reset_model()
                elif plot_toggle_rect.collidepoint(event.pos):
                    plot_visible = not plot_visible
                    update_plot()
                elif step_button_rect.collidepoint(event.pos) and not model_ui.running:
                    model_ui.step()
                    update_plot()

        if model_ui.running:
            model_ui.step()
            if plot_visible:
                update_plot()

        pink, green, black = model_ui.model.counts()
        screen.fill(style.background_color)
        draw_header_banner()
        draw_viewer_shell(pink, green, black)
        draw_grid(
            screen,
            model_ui.model,
            cell_size=CELL_SIZE,
            origin=(world_rect.x, world_rect.y),
            empty_color=style.empty_color,
            selfish_color=style.selfish_color,
            altruist_color=style.altruist_color,
            grid_color=style.grid_color,
            major_grid_color=style.grid_color_major,
        )
        draw_history_card()
        draw_controls_card()
        pygame.display.flip()
        clock.tick(current_fps)

    pygame.quit()


if __name__ == "__main__":
    main()
