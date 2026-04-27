"""Reusable Pygame drawing helpers for the spatial altruism UI."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pygame


def draw_grid(
    screen,
    model,
    cell_size: int,
    *,
    origin: tuple[int, int] = (0, 0),
    empty_color=(244, 239, 229),
    selfish_color=(45, 95, 186),
    altruist_color=(171, 53, 87),
    grid_color=(224, 230, 224),
    major_grid_color=(176, 192, 176),
    major_step: int = 5,
):
    origin_x, origin_y = origin
    for y in range(model.p.height):
        for x in range(model.p.width):
            val = model.pcolor[y, x]
            color = empty_color if val == 0 else selfish_color if val == 1 else altruist_color
            pygame.draw.rect(
                screen,
                color,
                (
                    origin_x + x * cell_size,
                    origin_y + y * cell_size,
                    cell_size,
                    cell_size,
                ),
            )

    for x in range(model.p.width + 1):
        color = major_grid_color if x % major_step == 0 else grid_color
        line_width = 2 if x % major_step == 0 else 1
        pygame.draw.line(
            screen,
            color,
            (origin_x + x * cell_size, origin_y),
            (origin_x + x * cell_size, origin_y + model.p.height * cell_size),
            line_width,
        )
    for y in range(model.p.height + 1):
        color = major_grid_color if y % major_step == 0 else grid_color
        line_width = 2 if y % major_step == 0 else 1
        pygame.draw.line(
            screen,
            color,
            (origin_x, origin_y + y * cell_size),
            (origin_x + model.p.width * cell_size, origin_y + y * cell_size),
            line_width,
        )


def draw_text(screen, text, pos, font, color=(0, 0, 0)):
    surf = font.render(text, True, color)
    screen.blit(surf, pos)


def plot_history(history, max_width: int, max_height: int, output_path: str | Path = "pop_plot.png"):
    target_ratio = max(max_width, 1) / max(max_height, 1)
    fig_height = 3.0
    fig_width = max(4.0, fig_height * target_ratio)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor("#F7FBFF")
    ax.set_facecolor("#FFFFFF")
    if history:
        arr = np.array(history)
        ax.plot(arr[:, 0], label="altruists", color="#AB3557", linewidth=2.2)
        ax.plot(arr[:, 1], label="selfish", color="#2D5FBA", linewidth=2.2)
    else:
        ax.plot([], [], label="altruists", color="#AB3557", linewidth=2.2)
        ax.plot([], [], label="selfish", color="#2D5FBA", linewidth=2.2)

    ax.legend(frameon=False)
    ax.set_xlabel("time")
    ax.set_ylabel("frequency")
    ax.set_title("Populations")
    ax.grid(True, color="#D6E4F5", linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#738FB2")
    ax.spines["bottom"].set_color("#738FB2")
    fig.tight_layout()

    output_path = Path(output_path)
    fig.savefig(output_path)
    plt.close(fig)

    img = pygame.image.load(str(output_path))
    if img.get_width() > max_width or img.get_height() > max_height:
        scale = min(max_width / img.get_width(), max_height / img.get_height())
        scaled_size = (
            max(1, int(img.get_width() * scale)),
            max(1, int(img.get_height() * scale)),
        )
        img = pygame.transform.smoothscale(img, scaled_size)
    return img
