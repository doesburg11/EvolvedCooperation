#!/usr/bin/env python3
"""Live scatter-plot viewer for the top-down cooperation model.

Run from the repository root with:
  ./.conda/bin/python -m top_down_model.utils.live_viewer

Controls:
  space       play / pause
  n           single-step (while paused)
  r           reset simulation
  v           toggle view: trait colour vs band colour
  b           toggle reciprocity-bond lines
  s           toggle spouse-bond lines
  c           toggle cared-juvenile overlay
  f           toggle fed-juvenile overlay
  h           toggle household centers
  t           toggle band territories
  g           toggle grass background
  1 / 3 / 8   steps per frame (speed)
  up / down   increase / decrease fps
  esc         quit
"""

from __future__ import annotations

import math

import pygame

if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m top_down_model.utils.live_viewer'."
    )

from ..config.top_down_config import DEFAULT_CONFIG, resolve_config
from ..top_down_model import STAGE_ELDER, STAGE_JUVENILE, STAGE_SUBADULT, TopDownCooperationModel

# ── Layout constants ───────────────────────────────────────────────────────
_CANVAS = 600          # px, simulation area (square)
_MARGIN = 16
_HEADER_H = 90
_PANEL_W = 640
_FOOTER_H = 20
_WINDOW_W = _MARGIN * 3 + _CANVAS + _PANEL_W
_WINDOW_H = _MARGIN * 2 + _HEADER_H + _CANVAS + _FOOTER_H

_SPACE_W = float(DEFAULT_CONFIG["space_width"])
_SCALE = _CANVAS / _SPACE_W    # px per space unit

_INV_THRESH = float(DEFAULT_CONFIG["helping_trait_invasion_threshold"])

# ── Palette ────────────────────────────────────────────────────────────────
_C_PRIMARY    = (15,  51, 104)
_C_SECONDARY  = (28,  75, 143)
_C_PALE       = (234, 242, 251)
_C_BORDER     = (214, 228, 245)
_C_BODY       = (31,  45,  61)
_C_WHITE      = (255, 255, 255)
_C_BG         = (248, 250, 255)
_C_CANVAS_BG  = (240, 244, 249)
_C_HINT       = (200, 220, 245)
_C_BOND       = (140, 155, 190)
_C_SPOUSE     = (80,  96, 120)
_C_CARE       = (246, 188,  45)
_C_FOOD       = (37,  178, 205)
_C_HOUSE      = (58,  68,  84)
_C_GRASS_LOW  = (236, 242, 232)
_C_GRASS_HIGH = (122, 181,  99)

_GROUP_COLORS = [
    (220,  60,  50),
    ( 45, 155,  80),
    (220, 115,  30),
    (140,  65, 175),
]


# ── Drawing helpers ────────────────────────────────────────────────────────
def _trait_rgb(v: float) -> tuple[int, int, int]:
    v = max(0.0, min(1.0, float(v)))
    return (
        int(35  + v * (229 -  35)),
        int(88  + v * (118 -  88)),
        int(196 + v * ( 42 - 196)),
    )


def _draw_sparkline(
    screen: pygame.Surface,
    values: list[float],
    rect: pygame.Rect,
    font: pygame.font.Font,
) -> None:
    pygame.draw.rect(screen, _C_WHITE, rect)
    pygame.draw.rect(screen, _C_BORDER, rect, 1)

    lp, rp, tp, bp = 44, 8, 8, 26
    pr = pygame.Rect(rect.x + lp, rect.y + tp, rect.width - lp - rp, rect.height - tp - bp)

    axis_c = (120, 170, 230)
    pygame.draw.line(screen, axis_c, (pr.x, pr.y), (pr.x, pr.bottom), 2)
    pygame.draw.line(screen, axis_c, (pr.x, pr.bottom), (pr.right, pr.bottom), 2)

    for tick in [0.0, 0.25, 0.5, 0.75, 1.0]:
        gy = pr.bottom - int(tick * pr.height)
        pygame.draw.line(screen, axis_c, (pr.x - 4, gy), (pr.x, gy), 1)
        if tick > 0.0:
            pygame.draw.line(screen, _C_BORDER, (pr.x, gy), (pr.right, gy), 1)
        lbl = font.render(f"{tick:.2f}", True, _C_BODY)
        screen.blit(lbl, (rect.x + 4, gy - 8))

    n = len(values)
    if n >= 2:
        pts = []
        for i, val in enumerate(values):
            px = pr.x + int(i * (pr.width - 1) / max(1, n - 1))
            py = pr.bottom - int(max(0.0, min(1.0, val)) * (pr.height - 1))
            pts.append((px, py))
        pygame.draw.lines(screen, _C_SECONDARY, False, pts, 2)

    for k in range(min(3, n)):
        t = round(k * (n - 1) / max(1, min(3, n) - 1))
        gx = pr.x + int(t * (pr.width - 1) / max(1, n - 1))
        pygame.draw.line(screen, axis_c, (gx, pr.bottom), (gx, pr.bottom + 4), 1)
        lbl = font.render(str(t), True, _C_BODY)
        screen.blit(lbl, (gx - lbl.get_width() // 2, pr.bottom + 7))


def _draw_band_size_chart(
    screen: pygame.Surface,
    series_by_band: list[tuple[int, list[float]]],
    rect: pygame.Rect,
    font: pygame.font.Font,
) -> None:
    pygame.draw.rect(screen, _C_WHITE, rect)
    pygame.draw.rect(screen, _C_BORDER, rect, 1)

    lp, rp, tp, bp = 44, 8, 8, 22
    pr = pygame.Rect(rect.x + lp, rect.y + tp, rect.width - lp - rp, rect.height - tp - bp)
    axis_c = (120, 170, 230)
    pygame.draw.line(screen, axis_c, (pr.x, pr.y), (pr.x, pr.bottom), 2)
    pygame.draw.line(screen, axis_c, (pr.x, pr.bottom), (pr.right, pr.bottom), 2)

    max_count = max(
        [1.0]
        + [
            max(values) if values else 0.0
            for _, values in series_by_band
        ]
    )
    for tick in [0.0, 0.5, 1.0]:
        value = max_count * tick
        gy = pr.bottom - int(tick * pr.height)
        pygame.draw.line(screen, axis_c, (pr.x - 4, gy), (pr.x, gy), 1)
        if tick > 0.0:
            pygame.draw.line(screen, _C_BORDER, (pr.x, gy), (pr.right, gy), 1)
        lbl = font.render(str(int(round(value))), True, _C_BODY)
        screen.blit(lbl, (rect.x + 4, gy - 8))

    for band_id, values in series_by_band:
        n = len(values)
        if n < 2:
            continue
        pts = []
        for i, val in enumerate(values):
            px = pr.x + int(i * (pr.width - 1) / max(1, n - 1))
            py = pr.bottom - int(max(0.0, min(max_count, val)) / max_count * (pr.height - 1))
            pts.append((px, py))
        pygame.draw.lines(screen, _GROUP_COLORS[band_id % len(_GROUP_COLORS)], False, pts, 2)

    n = max((len(values) for _, values in series_by_band), default=0)
    for k in range(min(3, n)):
        t = round(k * (n - 1) / max(1, min(3, n) - 1))
        gx = pr.x + int(t * (pr.width - 1) / max(1, n - 1))
        pygame.draw.line(screen, axis_c, (gx, pr.bottom), (gx, pr.bottom + 4), 1)
        lbl = font.render(str(t), True, _C_BODY)
        screen.blit(lbl, (gx - lbl.get_width() // 2, pr.bottom + 5))


def _draw_toroidal_line(
    screen: pygame.Surface,
    sim_rect: pygame.Rect,
    ax: float,
    ay: float,
    bx: float,
    by: float,
    color: tuple[int, int, int],
    width_px: int = 1,
) -> None:
    width = _SPACE_W
    dx = bx - ax
    dy = by - ay
    if abs(dx) > width / 2.0:
        bx -= math.copysign(width, dx)
    if abs(dy) > width / 2.0:
        by -= math.copysign(width, dy)

    old_clip = screen.get_clip()
    screen.set_clip(sim_rect)
    for sx in (-width, 0.0, width):
        for sy in (-width, 0.0, width):
            x1 = sim_rect.x + int((ax + sx) * _SCALE)
            y1 = sim_rect.y + int((ay + sy) * _SCALE)
            x2 = sim_rect.x + int((bx + sx) * _SCALE)
            y2 = sim_rect.y + int((by + sy) * _SCALE)
            line_rect = pygame.Rect(
                min(x1, x2),
                min(y1, y2),
                abs(x2 - x1) + 1,
                abs(y2 - y1) + 1,
            )
            if line_rect.colliderect(sim_rect):
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), width_px)
    screen.set_clip(old_clip)


def _draw_toroidal_circle(
    screen: pygame.Surface,
    sim_rect: pygame.Rect,
    cx: float,
    cy: float,
    radius: float,
    color: tuple[int, int, int],
    width_px: int = 1,
) -> None:
    world_w = _SPACE_W
    radius_px = max(1, int(radius * _SCALE))
    old_clip = screen.get_clip()
    screen.set_clip(sim_rect)
    for sx in (-world_w, 0.0, world_w):
        for sy in (-world_w, 0.0, world_w):
            px = sim_rect.x + int((cx + sx) * _SCALE)
            py = sim_rect.y + int((cy + sy) * _SCALE)
            circle_rect = pygame.Rect(
                px - radius_px,
                py - radius_px,
                radius_px * 2,
                radius_px * 2,
            )
            if circle_rect.colliderect(sim_rect):
                pygame.draw.circle(screen, color, (px, py), radius_px, width_px)
    screen.set_clip(old_clip)


def _draw_grass(
    screen: pygame.Surface,
    model: TopDownCooperationModel,
    sim_rect: pygame.Rect,
) -> None:
    max_grass = float(model.config["grass_max_per_cell"])
    if max_grass <= 0.0:
        return
    grid = model.grass
    rows, cols = grid.shape
    cell_w = sim_rect.width / cols
    cell_h = sim_rect.height / rows
    for row in range(rows):
        for col in range(cols):
            frac = max(0.0, min(1.0, float(grid[row, col]) / max_grass))
            color = tuple(
                int(_C_GRASS_LOW[i] + frac * (_C_GRASS_HIGH[i] - _C_GRASS_LOW[i]))
                for i in range(3)
            )
            rect = pygame.Rect(
                sim_rect.x + int(col * cell_w),
                sim_rect.y + int(row * cell_h),
                max(1, int(math.ceil(cell_w))),
                max(1, int(math.ceil(cell_h))),
            )
            pygame.draw.rect(screen, color, rect)


def _draw_scatter(
    screen: pygame.Surface,
    model: TopDownCooperationModel,
    sim_rect: pygame.Rect,
    view_trait: bool,
    show_bonds: bool,
    show_spouses: bool,
    show_care: bool,
    show_food: bool,
    show_households: bool,
    show_bands: bool,
    show_grass: bool,
) -> None:
    pygame.draw.rect(screen, _C_CANVAS_BG, sim_rect)
    if show_grass:
        _draw_grass(screen, model, sim_rect)
    pygame.draw.rect(screen, _C_BORDER, sim_rect, 1)

    inds = model.individuals
    by_id = {ind.id: ind for ind in inds}
    ox, oy = sim_rect.x, sim_rect.y

    if show_bands:
        for band in model.bands.values():
            color = _GROUP_COLORS[band.id % len(_GROUP_COLORS)]
            _draw_toroidal_circle(screen, sim_rect, band.x, band.y, band.radius, color, 2)
            px = ox + int(band.x * _SCALE)
            py = oy + int(band.y * _SCALE)
            pygame.draw.circle(screen, _C_WHITE, (px, py), 4)
            pygame.draw.circle(screen, color, (px, py), 4, 2)

    if show_households:
        live_households = {ind.household_id for ind in inds}
        for household_id, household in model.households.items():
            if household_id not in live_households:
                continue
            px = ox + int(household.x * _SCALE)
            py = oy + int(household.y * _SCALE)
            rect = pygame.Rect(px - 4, py - 4, 8, 8)
            pygame.draw.rect(screen, _C_WHITE, rect)
            pygame.draw.rect(screen, _C_HOUSE, rect, 2)

    if show_spouses:
        drawn_spouses: set[frozenset[int]] = set()
        for ind in inds:
            if ind.spouse_id is None:
                continue
            spouse = by_id.get(ind.spouse_id)
            if spouse is None or spouse.spouse_id != ind.id:
                continue
            key = frozenset((ind.id, spouse.id))
            if key in drawn_spouses:
                continue
            drawn_spouses.add(key)
            _draw_toroidal_line(
                screen,
                sim_rect,
                ind.x,
                ind.y,
                spouse.x,
                spouse.y,
                _C_SPOUSE,
                width_px=2,
            )

    if show_bonds:
        drawn: set[frozenset[int]] = set()
        for ind in inds:
            if ind.reciprocity_bond_id is None:
                continue
            key = frozenset((ind.id, ind.reciprocity_bond_id))
            if key in drawn:
                continue
            drawn.add(key)
            bondmate = by_id.get(ind.reciprocity_bond_id)
            if bondmate is None:
                continue
            _draw_toroidal_line(
                screen,
                sim_rect,
                ind.x,
                ind.y,
                bondmate.x,
                bondmate.y,
                _C_BOND,
            )

    for ind in inds:
        if view_trait:
            color = _trait_rgb(ind.helping_trait)
        else:
            color = _GROUP_COLORS[ind.group_id % len(_GROUP_COLORS)]
        if ind.stage == STAGE_JUVENILE:
            r = 3
        elif ind.stage == STAGE_SUBADULT:
            r = 4
        elif ind.stage == STAGE_ELDER:
            r = 7
        else:
            r = 5
        px = ox + int(ind.x * _SCALE)
        py = oy + int(ind.y * _SCALE)
        pygame.draw.circle(screen, color, (px, py), r)

    if show_care:
        old_clip = screen.get_clip()
        screen.set_clip(sim_rect)
        for ind in inds:
            if ind.stage != STAGE_JUVENILE:
                continue
            care = model.last_child_care_by_juvenile.get(ind.id, 0.0)
            if care <= 0.0:
                continue
            px = ox + int(ind.x * _SCALE)
            py = oy + int(ind.y * _SCALE)
            ring_r = max(6, min(15, int(6 + care * 5)))
            pygame.draw.circle(screen, _C_CARE, (px, py), ring_r, 2)
        screen.set_clip(old_clip)

    if show_food:
        old_clip = screen.get_clip()
        screen.set_clip(sim_rect)
        for ind in inds:
            if ind.stage != STAGE_JUVENILE:
                continue
            food = model.last_parent_food_by_juvenile.get(ind.id, 0.0)
            if food <= 0.0:
                continue
            px = ox + int(ind.x * _SCALE)
            py = oy + int(ind.y * _SCALE)
            ring_r = max(9, min(18, int(9 + food * 6)))
            pygame.draw.circle(screen, _C_FOOD, (px, py), ring_r, 2)
        screen.set_clip(old_clip)


# ── Main ───────────────────────────────────────────────────────────────────
def main() -> None:
    cfg = resolve_config({"write_latest_run": False})

    pygame.init()
    screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H))
    pygame.display.set_caption("Top-Down Cooperation Model – Live Viewer")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 34)
    body_font  = pygame.font.SysFont(None, 24)
    stat_font  = pygame.font.SysFont(None, 20)
    hint_font  = pygame.font.SysFont(None, 22)
    tiny_font  = pygame.font.SysFont(None, 20)

    sim_rect   = pygame.Rect(_MARGIN, _MARGIN + _HEADER_H, _CANVAS, _CANVAS)
    panel_rect = pygame.Rect(sim_rect.right + _MARGIN, sim_rect.y, _PANEL_W, _CANVAS)
    inner_x    = panel_rect.x + 14
    inner_w    = panel_rect.width - 28

    model        = TopDownCooperationModel(cfg)
    paused       = True
    view_trait   = True
    show_bonds = False
    show_spouses = False
    show_care = True
    show_food = True
    show_households = False
    show_bands = True
    show_grass = True
    fps          = 20
    spf          = 1          # steps per frame

    running = True
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
                    model = TopDownCooperationModel(cfg)
                    paused = True
                elif event.key == pygame.K_n:
                    model.step()
                elif event.key == pygame.K_UP:
                    fps = min(60, fps + 1)
                elif event.key == pygame.K_DOWN:
                    fps = max(1, fps - 1)
                elif event.key == pygame.K_v:
                    view_trait = not view_trait
                elif event.key == pygame.K_b:
                    show_bonds = not show_bonds
                elif event.key == pygame.K_s:
                    show_spouses = not show_spouses
                elif event.key == pygame.K_c:
                    show_care = not show_care
                elif event.key == pygame.K_f:
                    show_food = not show_food
                elif event.key == pygame.K_h:
                    show_households = not show_households
                elif event.key == pygame.K_t:
                    show_bands = not show_bands
                elif event.key == pygame.K_g:
                    show_grass = not show_grass
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    spf = 1
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    spf = 3
                elif event.key in (pygame.K_8, pygame.K_KP8):
                    spf = 8

        if not paused:
            for _ in range(spf):
                model.step()

        # ── Background + header ────────────────────────────────────────────
        screen.fill(_C_BG)
        pygame.draw.rect(screen, _C_PRIMARY, (0, 0, _WINDOW_W, _MARGIN + _HEADER_H))

        title_s = title_font.render("Top-Down Cooperation Model – Live Viewer", True, _C_WHITE)
        screen.blit(title_s, (_MARGIN, _MARGIN + 8))

        view_label = "trait" if view_trait else "band"
        hint1 = hint_font.render(
            "space play/pause  |  n single-step  |  r reset  |  up/down fps  |  esc quit",
            True, _C_WHITE,
        )
        hint2 = hint_font.render(
            f"v:{view_label}  b:{'on' if show_bonds else 'off'}"
            f"  s:{'on' if show_spouses else 'off'}"
            f"  c:{'on' if show_care else 'off'}"
            f"  f:{'on' if show_food else 'off'}"
            f"  h:{'on' if show_households else 'off'}"
            f"  t:{'on' if show_bands else 'off'}"
            f"  g:{'on' if show_grass else 'off'}"
            f"  |  1/3/8 speed:{spf}×  |  fps:{fps}",
            True, _C_HINT,
        )
        screen.blit(hint1, (_MARGIN, _MARGIN + 44))
        screen.blit(hint2, (_MARGIN, _MARGIN + 64))

        # ── Simulation scatter ─────────────────────────────────────────────
        _draw_scatter(
            screen,
            model,
            sim_rect,
            view_trait,
            show_bonds,
            show_spouses,
            show_care,
            show_food,
            show_households,
            show_bands,
            show_grass,
        )

        # ── Side panel ────────────────────────────────────────────────────
        pygame.draw.rect(screen, _C_PALE, panel_rect)
        pygame.draw.rect(screen, _C_BORDER, panel_rect, 1)

        h = model.history
        step      = model.step_index
        pop       = len(model.individuals)
        band_count = int(h["band_count"][-1]) if h["band_count"] else len(model.bands)
        mean_band_size = h["mean_band_size"][-1] if h["mean_band_size"] else 0.0
        band_migrations = (
            int(h["cumulative_band_migrations"][-1])
            if h["cumulative_band_migrations"]
            else 0
        )
        band_fissions = (
            int(h["cumulative_band_fissions"][-1])
            if h["cumulative_band_fissions"]
            else 0
        )
        band_fusions = (
            int(h["cumulative_band_fusions"][-1])
            if h["cumulative_band_fusions"]
            else 0
        )
        interband_marriages = (
            int(h["cumulative_interband_marriages"][-1])
            if h["cumulative_interband_marriages"]
            else 0
        )
        mt        = h["mean_helping_trait"][-1] if h["mean_helping_trait"] else 0.0
        inv_f     = h["helping_invasion_frequency"][-1] if h["helping_invasion_frequency"] else 0.0
        help_raw  = h["realized_helping_rate"][-1] if h["realized_helping_rate"] else math.nan
        help_rate = help_raw if math.isfinite(help_raw) else None
        help_txt  = f"{help_rate * 100:.1f}%" if help_rate is not None else "n/a"
        help_events = int(h["helping_events"][-1]) if h["helping_events"] else 0
        help_opps = int(h["helping_opportunities"][-1]) if h["helping_opportunities"] else 0
        mean_rep  = h["mean_reputation"][-1] if h["mean_reputation"] else 0.0
        norm_viol = h["norm_violation_rate"][-1] if h["norm_violation_rate"] else 0.0
        bmem_raw  = (
            h["mean_reciprocity_bond_memory"][-1]
            if h["mean_reciprocity_bond_memory"]
            else 0.0
        )
        bmem      = bmem_raw if math.isfinite(bmem_raw) else 0.0
        grass_raw = (
            h["mean_grass_fraction"][-1]
            if h["mean_grass_fraction"]
            else math.nan
        )
        grass_txt = f"{grass_raw * 100:.1f}%" if math.isfinite(grass_raw) else "n/a"
        grass_harvest = h["grass_harvest"][-1] if h["grass_harvest"] else 0.0
        food_transfer = (
            h["parent_food_transfer"][-1]
            if h["parent_food_transfer"]
            else 0.0
        )
        fed_count = int(h["fed_juvenile_count"][-1]) if h["fed_juvenile_count"] else 0
        food_surv_raw = (
            h["mean_juvenile_food_survival_effect"][-1]
            if h["mean_juvenile_food_survival_effect"]
            else math.nan
        )
        food_surv_txt = f"{food_surv_raw:+.3f}" if math.isfinite(food_surv_raw) else "n/a"
        stage_counts = (
            int(h["juvenile_count"][-1]) if h["juvenile_count"] else 0,
            int(h["subadult_count"][-1]) if h["subadult_count"] else 0,
            int(h["adult_count"][-1]) if h["adult_count"] else 0,
            int(h["elder_count"][-1]) if h["elder_count"] else 0,
        )
        care_total = (
            h["total_child_rearing_care"][-1]
            if h["total_child_rearing_care"]
            else 0.0
        )
        cared_count = int(h["cared_juvenile_count"][-1]) if h["cared_juvenile_count"] else 0
        spouse_pairs = int(h["spouse_bond_pairs"][-1]) if h["spouse_bond_pairs"] else 0
        spouse_recip = (
            int(h["spouse_reciprocity_bond_pairs"][-1])
            if h["spouse_reciprocity_bond_pairs"]
            else 0
        )
        households = int(h["household_count"][-1]) if h["household_count"] else 0
        hh_size = h["mean_household_size"][-1] if h["mean_household_size"] else 0.0
        hh_bonus = (
            h["mean_household_survival_bonus"][-1]
            if h["mean_household_survival_bonus"]
            else math.nan
        )
        hh_bonus_txt = f"{hh_bonus:.3f}" if math.isfinite(hh_bonus) else "n/a"
        juv_raw = (
            h["juvenile_survival_rate"][-1]
            if h["juvenile_survival_rate"]
            else math.nan
        )
        juv_txt = f"{juv_raw * 100:.1f}%" if math.isfinite(juv_raw) else "n/a"

        # Stats rows
        stats_y = panel_rect.y + 14
        label_w = 166
        line_h  = 14
        for label, value in [
            ("Step",           str(step)),
            ("Population",     str(pop)),
            ("Bands",          f"{band_count} avg {mean_band_size:.1f}"),
            ("Band totals",    f"mig {band_migrations} fis {band_fissions} fus {band_fusions}"),
            ("Interband marr", str(interband_marriages)),
            ("Stages J/S/A/E",  "/".join(str(v) for v in stage_counts)),
            ("Mean help trait",f"{mt:.4f}"),
            (f"Trait >= {_INV_THRESH:.2f}", f"{inv_f * 100:.1f}%"),
            ("Realized help",  help_txt),
            ("Help events",    f"{help_events}/{help_opps}"),
            ("Mean reputation",f"{mean_rep:.3f}"),
            ("Norm violators", f"{norm_viol * 100:.1f}%"),
            ("Bond memory",    f"{bmem:.3f}"),
            ("Grass",          grass_txt),
            ("Harvest",        f"{grass_harvest:.1f}"),
            ("Food->juv",      f"{food_transfer:.1f} ({fed_count})"),
            ("Food surv",      food_surv_txt),
            ("Spouses",        f"{spouse_pairs} ({spouse_recip} recip)"),
            ("Households",     f"{households} avg {hh_size:.1f}"),
            ("HH surv bonus",  hh_bonus_txt),
            ("Child care",     f"{care_total:.1f}"),
            ("Cared juv",      str(cared_count)),
            ("Juv survival",   juv_txt),
        ]:
            screen.blit(stat_font.render(label, True, _C_BODY),    (inner_x,           stats_y))
            screen.blit(stat_font.render(value, True, _C_PRIMARY),  (inner_x + label_w, stats_y))
            stats_y += line_h

        # Lower panel: readable legend on the left, charts on the right.
        lower_y = stats_y + 12
        legend_x = inner_x
        legend_y = lower_y
        legend_w = 300
        chart_x = legend_x + legend_w + 18
        chart_w = max(220, panel_rect.right - 14 - chart_x)
        chart_h = 84
        sw = 18
        band_ids = sorted(model.bands)

        for swatch_c, txt in [
            (_trait_rgb(0.0), "Trait 0 (blue)"),
            (_trait_rgb(1.0), "Trait 1 (orange)"),
        ]:
            pygame.draw.rect(screen, swatch_c, (legend_x, legend_y, sw, sw))
            pygame.draw.rect(screen, _C_BORDER, (legend_x, legend_y, sw, sw), 1)
            lbl = hint_font.render(txt, True, _C_BODY)
            screen.blit(lbl, (legend_x + sw + 8, legend_y + (sw - lbl.get_height()) // 2))
            legend_y += 22

        legend_y += 3
        group_start_y = legend_y
        for idx, band_id in enumerate(band_ids):
            gc = _GROUP_COLORS[band_id % len(_GROUP_COLORS)]
            col = idx % 2
            row = idx // 2
            gx = legend_x + col * 112
            gy = group_start_y + row * 22
            pygame.draw.circle(screen, gc, (gx + sw // 2, gy + sw // 2), sw // 2)
            lbl = hint_font.render(f"Band {band_id}", True, _C_BODY)
            screen.blit(lbl, (gx + sw + 8, gy + (sw - lbl.get_height()) // 2))
        legend_y = group_start_y + math.ceil(len(band_ids) / 2) * 22 + 4

        lbl = tiny_font.render("Circle size: juvenile < subadult < adult < elder", True, _C_BODY)
        screen.blit(lbl, (legend_x, legend_y))
        legend_y += 19
        pygame.draw.circle(screen, _C_CARE, (legend_x + sw // 2, legend_y + sw // 2), sw // 2, 2)
        lbl = hint_font.render("Gold ring = received care this step", True, _C_BODY)
        screen.blit(lbl, (legend_x + sw + 8, legend_y + (sw - lbl.get_height()) // 2))
        legend_y += 22
        pygame.draw.circle(screen, _C_FOOD, (legend_x + sw // 2, legend_y + sw // 2), sw // 2, 2)
        lbl = hint_font.render("Cyan ring = received parent food", True, _C_BODY)
        screen.blit(lbl, (legend_x + sw + 8, legend_y + (sw - lbl.get_height()) // 2))
        legend_y += 22
        house_rect = pygame.Rect(legend_x + 2, legend_y + 2, sw - 4, sw - 4)
        pygame.draw.rect(screen, _C_WHITE, house_rect)
        pygame.draw.rect(screen, _C_HOUSE, house_rect, 2)
        lbl = hint_font.render("Square = household residence", True, _C_BODY)
        screen.blit(lbl, (legend_x + sw + 8, legend_y + (sw - lbl.get_height()) // 2))
        legend_y += 22
        pygame.draw.circle(screen, _GROUP_COLORS[0], (legend_x + sw // 2, legend_y + sw // 2), sw // 2, 2)
        lbl = hint_font.render("Outline = band territory", True, _C_BODY)
        screen.blit(lbl, (legend_x + sw + 8, legend_y + (sw - lbl.get_height()) // 2))

        spark_rect = pygame.Rect(chart_x, lower_y + 20, chart_w, chart_h)
        chart_lbl = hint_font.render("Mean help trait", True, _C_PRIMARY)
        screen.blit(chart_lbl, (spark_rect.x, lower_y))
        _draw_sparkline(screen, list(h["mean_helping_trait"]), spark_rect, tiny_font)

        group_chart_y = spark_rect.bottom + 24
        group_chart_rect = pygame.Rect(chart_x, group_chart_y + 20, chart_w, chart_h)
        group_lbl = hint_font.render("Band sizes", True, _C_PRIMARY)
        screen.blit(group_lbl, (group_chart_rect.x, group_chart_y))
        history_band_ids = sorted(
            int(key.split("_")[1])
            for key in h
            if len(key.split("_")) == 3
            and key.split("_")[0] == "band"
            and key.split("_")[1].isdigit()
            and key.split("_")[2] == "count"
        )
        group_series = [
            (band_id, list(h[f"band_{band_id}_count"]))
            for band_id in history_band_ids
        ]
        _draw_band_size_chart(screen, group_series, group_chart_rect, tiny_font)

        # Footer status bar
        mode_str = "paused" if paused else "running"
        status = body_font.render(
            f"step={step}  pop={pop}  mean_trait={mt:.4f}"
            f"  trait>={_INV_THRESH:.2f}:{inv_f*100:.1f}%"
            f"  help:{help_txt}  grass:{grass_txt}  food:{food_transfer:.1f}"
            f"  care:{care_total:.1f}  bands:{band_count}  {mode_str}",
            True, _C_BODY,
        )
        screen.blit(status, (_MARGIN, sim_rect.bottom + 4))

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()


if __name__ == "__main__":
    main()
