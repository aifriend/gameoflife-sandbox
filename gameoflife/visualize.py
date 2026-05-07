"""Visualization: pygame interactive viewer and matplotlib animations.

pygame mode is event-driven:
    - SPACE      pause/resume
    - LEFT-CLICK toggle a cell (when paused)
    - RIGHT-CLICK clear the cell
    - r          randomize
    - c          clear board
    - +/-        speed up / slow down
    - n          single step (when paused)
    - q / ESC    quit

matplotlib mode produces an animation object you can show interactively or
save to MP4 / GIF.
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np

from gameoflife.engine import LifeBoard


# ===================================================================== pygame


def run_pygame(board: LifeBoard,
               cell_size: int = 8,
               fps: int = 30,
               title: str = "Game of Life") -> None:
    """Open an interactive pygame window."""
    # Suppress pygame's "Hello from..." banner unless user explicitly wants it
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame  # noqa: WPS433 — local import keeps headless installs working

    pygame.init()
    rows, cols = board.shape
    width = cols * cell_size
    height = rows * cell_size + 30   # extra room for status bar

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Menlo, Monaco, Courier", 14)

    paused = False
    speed = fps   # ticks per second of evolution (independent of draw fps)
    step_accum = 0.0
    running = True

    bg = np.array((10, 10, 18), dtype=np.uint8)
    fg = np.array((220, 220, 220), dtype=np.uint8)
    cell_surface = pygame.Surface((cols * cell_size, rows * cell_size))

    def draw():
        # Vectorized rendering — one numpy op for the whole grid, then a
        # single blit. Beats N Python draw_rect calls on busy boards.
        rgb = np.where(board.grid[..., None] > 0, fg, bg).astype(np.uint8)
        if cell_size > 1:
            rgb = rgb.repeat(cell_size, axis=0).repeat(cell_size, axis=1)
        # surfarray expects (width, height, 3) — transpose row/col axes.
        pygame.surfarray.blit_array(cell_surface, np.transpose(rgb, (1, 0, 2)))

        screen.fill((10, 10, 18))
        screen.blit(cell_surface, (0, 0))
        # Status bar
        status = (f"gen={board.generation}  pop={board.population}  "
                  f"speed={speed} tps  {'PAUSED' if paused else 'RUN'}")
        surf = font.render(status, True, (180, 180, 220))
        screen.blit(surf, (8, height - 22))
        pygame.display.flip()

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_n:
                    if paused:
                        board.tick()
                elif event.key == pygame.K_r:
                    rng = np.random.default_rng()
                    board.grid = (rng.random(board.shape) < 0.3).astype(np.uint8)
                    board.generation = 0
                elif event.key == pygame.K_c:
                    board.clear()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    speed = min(240, speed + 5)
                elif event.key == pygame.K_MINUS:
                    speed = max(1, speed - 5)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if my < rows * cell_size:
                    r, c = my // cell_size, mx // cell_size
                    if 0 <= r < rows and 0 <= c < cols:
                        if event.button == 1:
                            board.grid[r, c] ^= 1
                        elif event.button == 3:
                            board.grid[r, c] = 0

        if not paused:
            step_accum += dt * speed
            while step_accum >= 1.0:
                board.tick()
                step_accum -= 1.0

        draw()

    pygame.quit()


# ================================================================ matplotlib


def animate_matplotlib(board: LifeBoard,
                       steps: int = 200,
                       interval_ms: int = 80,
                       cmap: str = "binary",
                       title: Optional[str] = None,
                       save_path: Optional[str] = None,
                       fps: int = 15,
                       dpi: int = 100):
    """Build a matplotlib animation. Mutates the board.

    Returns the FuncAnimation object. If `save_path` is given, also writes
    .mp4 / .gif (extension determines writer).
    """
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter

    fig, ax = plt.subplots(figsize=(8, 8 * board.shape[0] / board.shape[1]))
    img = ax.imshow(board.grid, cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    if title:
        ax.set_title(title)
    info = ax.text(0.01, 0.99,
                   f"gen 0 | pop {board.population}",
                   transform=ax.transAxes,
                   va="top", ha="left",
                   color="red", fontsize=10,
                   bbox=dict(facecolor="white", alpha=0.7, pad=2))

    def update(frame):
        if frame > 0:
            board.tick()
        img.set_data(board.grid)
        info.set_text(f"gen {board.generation} | pop {board.population}")
        return img, info

    anim = FuncAnimation(fig, update, frames=steps + 1,
                         interval=interval_ms, blit=False, repeat=False)

    if save_path:
        ext = os.path.splitext(save_path)[1].lower()
        if ext in (".gif",):
            anim.save(save_path, writer=PillowWriter(fps=fps), dpi=dpi)
        elif ext in (".mp4", ".m4v", ".mov"):
            anim.save(save_path, writer=FFMpegWriter(fps=fps), dpi=dpi)
        else:
            raise ValueError(f"Unknown video extension: {ext}")

    return anim


def render_ascii(grid: np.ndarray, alive: str = "#", dead: str = ".") -> str:
    """ASCII rendering of a grid — handy for quick CLI output."""
    return "\n".join("".join(alive if grid[r, c] else dead
                             for c in range(grid.shape[1]))
                     for r in range(grid.shape[0]))
