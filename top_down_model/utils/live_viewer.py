#!/usr/bin/env python3
"""Live scatter-plot viewer for the top-down cooperation model.

Run from the repository root with:
  ./.conda/bin/python -m top_down_model.utils.live_viewer

Controls:
  space       play / pause
  n           single-step (while paused)
  r           reset simulation
  v           toggle view: trait colour vs group colour
  p           toggle partner-bond lines
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
from ..top_down_model import STAGE_ELDER, STAGE_JUVENILE, TopDownCooperationModel

# ── Layout constants ───────────────────────────────────────────────────────
_CANVAS = 600          # px, simulation area (square)
_MARGIN = 16
_HEADER_H = 90
_PANEL_W = 360
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
_C_PARTNER    = (140, 155, 190)

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


def _draw_scatter(
    screen: pygame.Surface,
    model: TopDownCooperationModel,
    sim_rect: pygame.Rect,
    view_trait: bool,
    show_partners: bool,
) -> None:
    pygame.draw.rect(screen, _C_CANVAS_BG, sim_rect)
    pygame.draw.rect(screen, _C_BORDER, sim_rect, 1)

    inds = model.individuals
    by_id = {ind.id: ind for ind in inds}
    ox, oy = sim_rect.x, sim_rect.y

    if show_partners:
        drawn: set[frozenset[int]] = set()
        for ind in inds:
            if ind.partner_id is None:
                continue
            key = frozenset((ind.id, ind.partner_id))
            if key in drawn:
                continue
            drawn.add(key)
            partner = by_id.get(ind.partner_id)
            if partner is None:
                continue
            ax = ox + int(ind.x * _SCALE)
            ay = oy + int(ind.y * _SCALE)
            bx = ox + int(partner.x * _SCALE)
            by_coord = oy + int(partner.y * _SCALE)
            pygame.draw.line(screen, _C_PARTNER, (ax, ay), (bx, by_coord), 1)

    for ind in inds:
        if view_trait:
            color = _trait_rgb(ind.helping_trait)
        else:
            color = _GROUP_COLORS[ind.group_id % len(_GROUP_COLORS)]
        if ind.stage == STAGE_JUVENILE:
            r = 3
        elif ind.stage == STAGE_ELDER:
            r = 7
        else:
            r = 5
        px = ox + int(ind.x * _SCALE)
        py = oy + int(ind.y * _SCALE)
        pygame.draw.circle(screen, color, (px, py), r)


# ── Main ───────────────────────────────────────────────────────────────────
def main() -> None:
    cfg = resolve_config({"write_latest_run": False})

    pygame.init()
    screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H))
    pygame.display.set_caption("Top-Down Cooperation Model – Live Viewer")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 34)
    body_font  = pygame.font.SysFont(None, 24)
    hint_font  = pygame.font.SysFont(None, 22)
    tiny_font  = pygame.font.SysFont(None, 20)

    sim_rect   = pygame.Rect(_MARGIN, _MARGIN + _HEADER_H, _CANVAS, _CANVAS)
    panel_rect = pygame.Rect(sim_rect.right + _MARGIN, sim_rect.y, _PANEL_W, _CANVAS)
    inner_x    = panel_rect.x + 14
    inner_w    = panel_rect.width - 28

    model        = TopDownCooperationModel(cfg)
    paused       = True
    view_trait   = True
    show_partners = False
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
                elif event.key == pygame.K_p:
                    show_partners = not show_partners
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

        view_label = "trait" if view_trait else "group"
        hint1 = hint_font.render(
            "space play/pause  |  n single-step  |  r reset  |  up/down fps",
            True, _C_WHITE,
        )
        hint2 = hint_font.render(
            f"v view:{view_label}  |  p partners:{'on' if show_partners else 'off'}"
            f"  |  1/3/8 speed:{spf}×  |  fps:{fps}  |  esc quit",
            True, _C_HINT,
        )
        screen.blit(hint1, (_MARGIN, _MARGIN + 44))
        screen.blit(hint2, (_MARGIN, _MARGIN + 64))

        # ── Simulation scatter ─────────────────────────────────────────────
        _draw_scatter(screen, model, sim_rect, view_trait, show_partners)

        # ── Side panel ────────────────────────────────────────────────────
        pygame.draw.rect(screen, _C_PALE, panel_rect)
        pygame.draw.rect(screen, _C_BORDER, panel_rect, 1)

        h = model.history
        step      = model.step_index
        pop       = len(model.individuals)
        mt        = h["mean_helping_trait"][-1] if h["mean_helping_trait"] else 0.0
        inv_f     = h["helping_invasion_frequency"][-1] if h["helping_invasion_frequency"] else 0.0
        mean_rep  = h["mean_reputation"][-1] if h["mean_reputation"] else 0.0
        norm_viol = h["norm_violation_rate"][-1] if h["norm_violation_rate"] else 0.0
        pmem_raw  = h["mean_partner_memory"][-1] if h["mean_partner_memory"] else 0.0
        pmem      = pmem_raw if math.isfinite(pmem_raw) else 0.0

        # Stats rows
        stats_y = panel_rect.y + 14
        label_w = 136
        line_h  = 24
        for label, value in [
            ("Step",           str(step)),
            ("Population",     str(pop)),
            ("Mean trait",     f"{mt:.4f}"),
            ("Helpers >10%",   f"{inv_f * 100:.1f}%"),
            ("Mean reputation",f"{mean_rep:.3f}"),
            ("Norm violators", f"{norm_viol * 100:.1f}%"),
            ("Partner memory", f"{pmem:.3f}"),
        ]:
            screen.blit(body_font.render(label, True, _C_BODY),    (inner_x,           stats_y))
            screen.blit(body_font.render(value, True, _C_PRIMARY),  (inner_x + label_w, stats_y))
            stats_y += line_h

        # Trait legend
        stats_y += 10
        sw = 20
        for swatch_c, txt in [
            (_trait_rgb(0.0), "Defector (trait 0)"),
            (_trait_rgb(1.0), "Helper (trait 1)"),
        ]:
            pygame.draw.rect(screen, swatch_c, (inner_x, stats_y, sw, sw))
            pygame.draw.rect(screen, _C_BORDER, (inner_x, stats_y, sw, sw), 1)
            lbl = hint_font.render(txt, True, _C_BODY)
            screen.blit(lbl, (inner_x + sw + 8, stats_y + (sw - lbl.get_height()) // 2))
            stats_y += sw + 4

        # Group legend
        stats_y += 4
        for gid, (gc, gname) in enumerate(zip(_GROUP_COLORS, ["Group 0", "Group 1", "Group 2", "Group 3"])):
            pygame.draw.circle(screen, gc, (inner_x + sw // 2, stats_y + sw // 2), sw // 2)
            lbl = hint_font.render(gname, True, _C_BODY)
            screen.blit(lbl, (inner_x + sw + 8, stats_y + (sw - lbl.get_height()) // 2))
            stats_y += sw + 4

        # Size legend
        stats_y += 4
        lbl = tiny_font.render("Circle size: small=juvenile  med=adult  large=elder", True, _C_BODY)
        screen.blit(lbl, (inner_x, stats_y))

        # Sparkline
        spark_h  = 130
        spark_y  = panel_rect.bottom - spark_h - 28
        spark_rect = pygame.Rect(panel_rect.x + 8, spark_y, panel_rect.width - 16, spark_h)
        chart_lbl = hint_font.render("Mean cooperation over time", True, _C_PRIMARY)
        screen.blit(chart_lbl, (inner_x, spark_y - 20))
        _draw_sparkline(screen, list(h["mean_helping_trait"]), spark_rect, tiny_font)

        # Footer status bar
        mode_str = "paused" if paused else "running"
        status = body_font.render(
            f"step={step}  pop={pop}  mean_trait={mt:.4f}  helpers={inv_f*100:.1f}%  {mode_str}",
            True, _C_BODY,
        )
        screen.blit(status, (_MARGIN, sim_rect.bottom + 4))

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()


if __name__ == "__main__":
    main()
