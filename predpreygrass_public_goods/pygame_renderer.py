import pygame
from dataclasses import dataclass


@dataclass
class GuiStyle:
    margin: int = 10
    panel_width: int = 550
    panel_padding: int = 12
    background_color: tuple = (245, 245, 245)
    panel_background: tuple = (235, 235, 235)
    world_panel_background: tuple = (232, 240, 232)
    world_panel_shadow: tuple = (210, 216, 210)
    world_panel_border: tuple = (42, 58, 44)
    world_header_background: tuple = (34, 84, 52)
    world_header_text: tuple = (248, 250, 248)
    world_badge_background: tuple = (246, 248, 246)
    world_badge_border: tuple = (52, 68, 56)
    grid_color: tuple = (224, 230, 224)
    grid_color_major: tuple = (176, 192, 176)
    predator_color: tuple = (220, 60, 60)
    prey_color: tuple = (60, 90, 220)
    grass_color: tuple = (50, 160, 70)
    no_grass_color: tuple = (244, 244, 244)
    text_color: tuple = (20, 20, 20)
    line_predator: tuple = (220, 60, 60)
    line_prey: tuple = (60, 90, 220)


class PyGameRenderer:
    def __init__(
        self,
        width: int,
        height: int,
        cell_size: int = 16,
        fps: int = 20,
        title: str = "Minimal Ecology Viewer",
    ):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.fps = fps
        self.style = GuiStyle()

        window_width = self.style.margin * 2 + width * cell_size + self.style.panel_width
        window_height = self.style.margin * 2 + height * cell_size + 24
        pygame.init()
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, max(12, int(cell_size * 0.9)))
        self.small_font = pygame.font.SysFont(None, max(12, int(cell_size * 0.75)))
        self.panel_font = pygame.font.SysFont(None, 36)
        self.panel_small_font = pygame.font.SysFont(None, 36)
        self.panel_large_font = pygame.font.SysFont(None, 36)
        self.panel_legend_font = pygame.font.SysFont(None, 36)
        self.panel_caption_font = pygame.font.SysFont(None, 24)

        self.history_steps = []
        self.history_prey = []
        self.history_pred = []
        self.history_max = 200
        self.paused = False
        self.step_once_requested = False
        self.min_fps = 5
        self.max_fps = 120

    def close(self) -> None:
        pygame.quit()

    def _handle_control_event(self, event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            return True

        if event.key in (pygame.K_SPACE, pygame.K_p):
            self.paused = not self.paused
            if not self.paused:
                self.step_once_requested = False
        elif event.key in (pygame.K_n, pygame.K_RIGHT):
            if self.paused:
                self.step_once_requested = True
        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.fps = min(self.max_fps, self.fps + 5)
        elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.fps = max(self.min_fps, self.fps - 5)
        elif event.key == pygame.K_0:
            self.fps = 30
        return True

    def _wait_while_paused(self) -> bool:
        while self.paused:
            for event in pygame.event.get():
                if not self._handle_control_event(event):
                    return False
            if self.step_once_requested:
                self.step_once_requested = False
                return True
            pygame.display.flip()
            self.clock.tick(12)
        return True

    def update(self, state, config, step: int, stats: dict | None = None) -> bool:
        for event in pygame.event.get():
            if not self._handle_control_event(event):
                return False

        self.screen.fill(self.style.background_color)
        self._draw_grass(state, config)
        self._draw_grid()
        self._draw_agents(state, config)
        self._draw_text(state, step)
        self._draw_panel(state, step, stats)

        pygame.display.flip()
        self.clock.tick(self.fps)
        return self._wait_while_paused()

    def _draw_grid(self) -> None:
        for x in range(self.width + 1):
            x_pix = self.style.margin + x * self.cell_size
            color = self.style.grid_color_major if x % 5 == 0 else self.style.grid_color
            line_width = 2 if x % 5 == 0 else 1
            pygame.draw.line(
                self.screen,
                color,
                (x_pix, self.style.margin),
                (x_pix, self.style.margin + self.height * self.cell_size),
                line_width,
            )
        for y in range(self.height + 1):
            y_pix = self.style.margin + y * self.cell_size
            color = self.style.grid_color_major if y % 5 == 0 else self.style.grid_color
            line_width = 2 if y % 5 == 0 else 1
            pygame.draw.line(
                self.screen,
                color,
                (self.style.margin, y_pix),
                (self.style.margin + self.width * self.cell_size, y_pix),
                line_width,
            )

    def _blend_color(self, start: tuple, end: tuple, mix: float) -> tuple:
        mix = max(0.0, min(1.0, mix))
        return tuple(int(start[i] + (end[i] - start[i]) * mix) for i in range(3))

    def _grass_tile_color(self, amount: float, gmax: float) -> tuple:
        if amount <= 0.0:
            return self.style.no_grass_color
        intensity = min(amount / max(gmax, 1e-6), 1.0)
        return self._blend_color(self.style.no_grass_color, self.style.grass_color, intensity)

    def _draw_grass(self, state, config) -> None:
        gmax = max(config.gmax, 1e-6)
        for y in range(self.height):
            for x in range(self.width):
                amount = state.grass[y][x]
                color = self._grass_tile_color(float(amount), gmax)
                rect = pygame.Rect(
                    self.style.margin + x * self.cell_size,
                    self.style.margin + y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pygame.draw.rect(self.screen, color, rect)

    def _draw_agents(self, state, config) -> None:
        for agent in state.agents:
            x_pix = self.style.margin + agent.x * self.cell_size + self.cell_size // 2
            y_pix = self.style.margin + agent.y * self.cell_size + self.cell_size // 2
            if agent.kind == "predator":
                color = self.style.predator_color
                ref_energy = config.predator_energy_init
            else:
                color = self.style.prey_color
                ref_energy = config.prey_energy_init
            size_factor = min(agent.energy / max(ref_energy, 1.0), 1.0)
            radius = max(2, int((self.cell_size // 2 - 1) * size_factor))
            pygame.draw.circle(self.screen, color, (x_pix, y_pix), radius)

    def _draw_text(self, state, step: int) -> None:
        prey = sum(1 for agent in state.agents if agent.kind == "prey")
        pred = sum(1 for agent in state.agents if agent.kind == "predator")
        text = f"t={step} prey={prey} pred={pred}"
        surface = self.font.render(text, True, self.style.text_color)
        self.screen.blit(surface, (self.style.margin, self.style.margin + self.height * self.cell_size + 2))

    def _draw_panel(self, state, step: int, stats: dict | None) -> None:
        panel_x = self.style.margin + self.width * self.cell_size + self.style.margin
        panel_y = self.style.margin
        panel_w = self.style.panel_width - self.style.margin
        panel_h = self.height * self.cell_size
        rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, self.style.panel_background, rect)

        prey = sum(1 for agent in state.agents if agent.kind == "prey")
        pred = sum(1 for agent in state.agents if agent.kind == "predator")
        self._push_history(step, prey, pred)

        y = panel_y + self.style.panel_padding
        y = self._draw_panel_line(panel_x, y, f"Step: {step}")
        y = self._draw_panel_line(panel_x, y, f"Prey: {prey}")
        y = self._draw_panel_line(panel_x, y, f"Pred: {pred}")

        if stats:
            grass = stats.get("grass", {}).get("mean", None)
            if grass is not None:
                y = self._draw_panel_line(panel_x, y, f"Grass: {grass:.2f}")

            prey_stats = stats.get("prey", {})
            pred_stats = stats.get("predator", {})
            y += 6
            y = self._draw_panel_line(panel_x, y, "Prey traits (mean):", bold=True)
            y = self._draw_panel_trait(panel_x, y, prey_stats, "speed")
            y = self._draw_panel_trait(panel_x, y, prey_stats, "vision")
            y = self._draw_panel_trait(panel_x, y, prey_stats, "metabolism")
            y += 6
            y = self._draw_panel_line(panel_x, y, "Pred traits (mean):", bold=True)
            y = self._draw_panel_trait(panel_x, y, pred_stats, "speed")
            y = self._draw_panel_trait(panel_x, y, pred_stats, "vision")
            y = self._draw_panel_trait(panel_x, y, pred_stats, "attack_power")
            y = self._draw_panel_trait(panel_x, y, pred_stats, "metabolism")

        # Sparkline at bottom
        spark_h = 90
        spark_y = panel_y + panel_h - spark_h - self.style.panel_padding
        spark_rect = pygame.Rect(
            panel_x + self.style.panel_padding,
            spark_y,
            panel_w - 2 * self.style.panel_padding,
            spark_h,
        )
        pygame.draw.rect(self.screen, (225, 225, 225), spark_rect)
        self._draw_sparkline(spark_rect)

    def _push_history(self, step: int, prey: int, pred: int) -> None:
        self.history_steps.append(step)
        self.history_prey.append(prey)
        self.history_pred.append(pred)
        if len(self.history_steps) > self.history_max:
            self.history_steps.pop(0)
            self.history_prey.pop(0)
            self.history_pred.pop(0)

    def _draw_panel_line(self, x: int, y: int, text: str, bold: bool = False) -> int:
        font = self.panel_font if bold else self.panel_small_font
        surface = font.render(text, True, self.style.text_color)
        self.screen.blit(surface, (x + self.style.panel_padding, y))
        return y + surface.get_height() + 6

    def _draw_panel_trait(self, x: int, y: int, stats: dict, name: str) -> int:
        key = f"{name}_mean"
        value = stats.get(key)
        if value is None:
            return y
        return self._draw_panel_line(x, y, f"  {name}: {value:.2f}")

    def _draw_sparkline(self, rect: pygame.Rect) -> None:
        if len(self.history_steps) < 2:
            return
        max_count = max(max(self.history_prey), max(self.history_pred), 1)
        n = len(self.history_steps)
        for i in range(1, n):
            x0 = rect.x + int((i - 1) / (n - 1) * rect.width)
            x1 = rect.x + int(i / (n - 1) * rect.width)

            y0 = rect.y + rect.height - int(self.history_prey[i - 1] / max_count * rect.height)
            y1 = rect.y + rect.height - int(self.history_prey[i] / max_count * rect.height)
            pygame.draw.line(self.screen, self.style.line_prey, (x0, y0), (x1, y1), 2)

            y0 = rect.y + rect.height - int(self.history_pred[i - 1] / max_count * rect.height)
            y1 = rect.y + rect.height - int(self.history_pred[i] / max_count * rect.height)
            pygame.draw.line(self.screen, self.style.line_predator, (x0, y0), (x1, y1), 2)

    def update_emerging(self, preds, preys, grass, step: int, stats: dict | None = None) -> bool:
        for event in pygame.event.get():
            if not self._handle_control_event(event):
                return False

        self.screen.fill(self.style.background_color)
        self._draw_world_panel_background()
        self._draw_emerging_grass(grass, stats)
        self._draw_grid()
        self._draw_emerging_agents(preds, preys)
        self._draw_emerging_text(step, len(preys), len(preds))
        self._draw_emerging_panel(preds, preys, grass, step, stats)

        pygame.display.flip()
        self.clock.tick(self.fps)
        return self._wait_while_paused()

    def _predator_coop_color(self, coop: float) -> tuple:
        coop = max(0.0, min(1.0, float(coop)))
        selfish = (70, 90, 150)
        mixed = (220, 180, 70)
        cooperative = (220, 70, 60)
        if coop <= 0.5:
            blend = coop / 0.5
            start = selfish
            end = mixed
        else:
            blend = (coop - 0.5) / 0.5
            start = mixed
            end = cooperative
        return tuple(
            int(start[i] + (end[i] - start[i]) * blend)
            for i in range(3)
        )

    def _draw_world_panel_background(self) -> None:
        board_x = self.style.margin
        board_y = self.style.margin
        board_w = self.width * self.cell_size
        board_h = self.height * self.cell_size

        shadow_rect = pygame.Rect(board_x + 6, board_y + 6, board_w, board_h)
        pygame.draw.rect(self.screen, self.style.world_panel_shadow, shadow_rect, border_radius=10)

        board_rect = pygame.Rect(board_x, board_y, board_w, board_h)
        pygame.draw.rect(self.screen, self.style.world_panel_background, board_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.style.world_panel_border, board_rect, 3, border_radius=10)

        header_rect = pygame.Rect(board_x + 10, board_y + 10, min(280, board_w - 20), 40)
        pygame.draw.rect(self.screen, self.style.world_header_background, header_rect, border_radius=8)
        header = self.font.render("Habitat Map", True, self.style.world_header_text)
        self.screen.blit(header, (header_rect.x + 12, header_rect.y + 10))

    def _draw_emerging_grass(self, grass, stats: dict | None) -> None:
        grass_cap = None
        if stats is not None:
            grass_cap = stats.get("grass_cap")
        gmax = max(float(grass_cap or float(grass.max() or 0.0)), 1e-6)
        for y in range(self.height):
            for x in range(self.width):
                amount = float(grass[y, x])
                color = self._grass_tile_color(amount, gmax)
                rect = pygame.Rect(
                    self.style.margin + x * self.cell_size,
                    self.style.margin + y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pygame.draw.rect(self.screen, color, rect)

    def _draw_emerging_agents(self, preds, preys) -> None:
        prey_size = max(3, self.cell_size // 2)
        prey_offset = prey_size // 2
        prey_positions = {(prey.x, prey.y) for prey in preys}
        for prey in preys:
            rect = pygame.Rect(
                self.style.margin + prey.x * self.cell_size + self.cell_size // 2 - prey_offset,
                self.style.margin + prey.y * self.cell_size + self.cell_size // 2 - prey_offset,
                prey_size,
                prey_size,
            )
            pygame.draw.rect(self.screen, self.style.prey_color, rect)
            pygame.draw.rect(self.screen, (245, 245, 245), rect, 1)

        for pred in preds:
            color = self._predator_coop_color(pred.coop)
            x_pix = self.style.margin + pred.x * self.cell_size + self.cell_size // 2
            y_pix = self.style.margin + pred.y * self.cell_size + self.cell_size // 2
            radius = max(3, self.cell_size // 2 - 1)
            if (pred.x, pred.y) in prey_positions:
                offset = max(2, self.cell_size // 6)
                x_pix += offset
                y_pix -= offset
                radius = max(3, radius - 1)
            pygame.draw.circle(self.screen, color, (x_pix, y_pix), radius)
            pygame.draw.circle(self.screen, (15, 15, 15), (x_pix, y_pix), radius, 2)

    def _draw_emerging_text(self, step: int, prey_count: int, pred_count: int) -> None:
        return None

    def _draw_grid_elements_legend(self, x: int, y: int, width: int) -> int:
        title_surface = self.panel_large_font.render("Grid Elements", True, self.style.text_color)
        self.screen.blit(title_surface, (x, y))
        y += title_surface.get_height() + 16

        legend_h = 205
        legend_rect = pygame.Rect(x, y, width, legend_h)
        pygame.draw.rect(self.screen, (248, 248, 248), legend_rect)
        pygame.draw.rect(self.screen, (25, 25, 25), legend_rect, 2)

        row_gap = 12
        row_y = y + 14
        icon_x = x + 18
        text_x = x + 86

        label_surface = self.panel_legend_font.render("Grass amount", True, self.style.text_color)
        self.screen.blit(label_surface, (icon_x, row_y))
        row_y += label_surface.get_height() + 10

        swatch_y = row_y
        swatch_size = 26
        swatch_gap = 34
        swatch_specs = (
            (self.style.no_grass_color, "none"),
            (self._grass_tile_color(0.25, 1.0), "low"),
            (self._grass_tile_color(1.0, 1.0), "high"),
        )
        swatch_x = icon_x + 6
        icon_right = swatch_x + swatch_size
        text_x = icon_right + 10
        for color, label in swatch_specs:
            swatch_rect = pygame.Rect(swatch_x, swatch_y, swatch_size, swatch_size)
            pygame.draw.rect(self.screen, color, swatch_rect)
            pygame.draw.rect(self.screen, (25, 25, 25), swatch_rect, 2)
            label_surface = self.panel_legend_font.render(label, True, self.style.text_color)
            label_y = swatch_y + (swatch_size - label_surface.get_height()) // 2
            self.screen.blit(label_surface, (swatch_x + swatch_size + 10, label_y))
            swatch_x += swatch_size + 10 + label_surface.get_width() + swatch_gap

        row_y = swatch_y + swatch_size + row_gap

        prey_size = 30
        prey_rect = pygame.Rect(icon_right - prey_size, row_y + 3, prey_size, prey_size)
        pygame.draw.rect(self.screen, self.style.prey_color, prey_rect)
        pygame.draw.rect(self.screen, (245, 245, 245), prey_rect, 2)
        label_surface = self.panel_legend_font.render("prey", True, self.style.text_color)
        label_y = row_y + (prey_size - label_surface.get_height()) // 2
        self.screen.blit(label_surface, (text_x, label_y))
        row_y += max(prey_size, label_surface.get_height()) + row_gap

        pred_radius = 15
        pred_center = (icon_right - pred_radius, row_y + 3 + pred_radius)
        pygame.draw.circle(self.screen, self._predator_coop_color(0.8), pred_center, pred_radius)
        pygame.draw.circle(self.screen, (15, 15, 15), pred_center, pred_radius, 2)
        label_surface = self.panel_legend_font.render("predator", True, self.style.text_color)
        label_y = row_y + (pred_radius * 2 - label_surface.get_height()) // 2
        self.screen.blit(label_surface, (text_x, label_y))

        return y + legend_h + 10

    def _draw_emerging_panel_legend(self, x: int, y: int, width: int) -> int:
        title_surface = self.panel_large_font.render("Predator Cooperation", True, self.style.text_color)
        self.screen.blit(title_surface, (x, y))
        y += title_surface.get_height() + 10

        legend_h = 180
        legend_rect = pygame.Rect(x, y, width, legend_h)
        pygame.draw.rect(self.screen, (248, 248, 248), legend_rect)
        pygame.draw.rect(self.screen, (25, 25, 25), legend_rect, 2)

        subtitle = self.panel_legend_font.render("Predator color = cooperation level", True, self.style.text_color)
        self.screen.blit(subtitle, (x + 12, y + 8))

        bar_x = x + 12
        bar_y = y + 58
        bar_w = width - 24
        bar_h = 32
        steps = max(1, bar_w - 1)
        for offset in range(bar_w):
            coop = offset / steps
            color = self._predator_coop_color(coop)
            pygame.draw.line(
                self.screen,
                color,
                (bar_x + offset, bar_y),
                (bar_x + offset, bar_y + bar_h),
            )
        pygame.draw.rect(self.screen, (15, 15, 15), pygame.Rect(bar_x, bar_y, bar_w, bar_h), 2)

        tick_specs = (
            (0.0, "0.0 selfish"),
            (0.5, "0.5 mixed"),
            (1.0, "1.0 cooperative"),
        )
        for tick_value, label in tick_specs:
            tick_x = bar_x + int(tick_value * (bar_w - 1))
            pygame.draw.line(self.screen, (25, 25, 25), (tick_x, bar_y + bar_h), (tick_x, bar_y + bar_h + 8), 2)
            label_surface = self.panel_legend_font.render(label, True, self.style.text_color)
            label_pos_x = tick_x - label_surface.get_width() // 2
            label_pos_x = max(x + 8, min(label_pos_x, x + width - label_surface.get_width() - 8))
            self.screen.blit(label_surface, (label_pos_x, bar_y + bar_h + 12))

        return y + legend_h + 10

    def _draw_emerging_panel(self, preds, preys, grass, step: int, stats: dict | None) -> None:
        panel_x = self.style.margin + self.width * self.cell_size + self.style.margin
        panel_y = self.style.margin
        panel_w = self.style.panel_width - self.style.margin
        panel_h = self.height * self.cell_size
        rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, self.style.panel_background, rect)

        prey = len(preys)
        pred = len(preds)
        self._push_history(step, prey, pred)

        y = panel_y + self.style.panel_padding
        y = self._draw_panel_line(panel_x, y, f"Step: {step}")
        y = self._draw_panel_line(panel_x, y, f"Speed: {self.fps} fps")
        y = self._draw_panel_line(panel_x, y, f"Paused: {'yes' if self.paused else 'no'}")
        y += 8
        y = self._draw_grid_elements_legend(
            panel_x + self.style.panel_padding,
            y,
            panel_w - 2 * self.style.panel_padding,
        )
        y = self._draw_emerging_panel_legend(
            panel_x + self.style.panel_padding,
            y,
            panel_w - 2 * self.style.panel_padding,
        )

        if stats:
            y = self._draw_panel_line(panel_x, y, f"Grass mean: {stats.get('grass_mean', 0.0):.2f}")
            y = self._draw_panel_line(panel_x, y, f"Grass max: {stats.get('grass_max', 0.0):.2f}")
            y += 6
            y = self._draw_panel_line(panel_x, y, f"Mean coop: {stats.get('mean_coop', 0.0):.3f}", bold=True)
            y = self._draw_panel_line(panel_x, y, f"Var coop: {stats.get('var_coop', 0.0):.4f}")

            energy = stats.get("energy", {})
            y += 6
            y = self._draw_panel_line(panel_x, y, "Energy stocks:", bold=True)
            y = self._draw_panel_line(panel_x, y, f"  pred: {energy.get('pred', 0.0):.1f}")
            y = self._draw_panel_line(panel_x, y, f"  prey: {energy.get('prey', 0.0):.1f}")
            y = self._draw_panel_line(panel_x, y, f"  grass: {energy.get('grass', 0.0):.1f}")
            y = self._draw_panel_line(panel_x, y, f"  total: {energy.get('total', 0.0):.1f}")

        controls_y = y + 18
        controls_end_y = self._draw_controls(panel_x, controls_y)

        spark_top_gap = 18
        spark_min_h = 60
        spark_max_h = 90
        spark_y = controls_end_y + spark_top_gap
        spark_bottom = panel_y + panel_h - self.style.panel_padding
        spark_h = min(spark_max_h, spark_bottom - spark_y)
        if spark_h >= spark_min_h:
            spark_rect = pygame.Rect(
                panel_x + self.style.panel_padding,
                spark_y,
                panel_w - 2 * self.style.panel_padding,
                spark_h,
            )
            pygame.draw.rect(self.screen, (225, 225, 225), spark_rect)
            self._draw_sparkline(spark_rect)

    def _draw_controls(self, x: int, y: int) -> int:
        y = self._draw_panel_line(x, y, "Controls:", bold=True)
        y = self._draw_panel_line(x, y, "  Space / P: pause")
        y = self._draw_panel_line(x, y, "  N / Right: step once")
        y = self._draw_panel_line(x, y, "  +/-: change speed")
        return self._draw_panel_line(x, y, "  0: reset to 30 fps")


def main() -> None:
    raise RuntimeError(
        "pygame_renderer.py is the minimal_engine renderer entrypoint, not the "
        "emerging_cooperation model. Run "
        "'predprey_public_goods/emerging_cooperation.py' or use the VS Code "
        "launch configuration 'Python: emerging_cooperation'."
    )


if __name__ == "__main__":
    main()
