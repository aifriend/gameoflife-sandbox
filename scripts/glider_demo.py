#!/usr/bin/env python3
"""Glider physics demos — head-on collisions, gun + eater pairs.

Headless by default; pass --pygame to open the interactive viewer.
"""
from __future__ import annotations

import argparse
import sys

from gameoflife.analysis import bounding_box
from gameoflife.gates import build_collision_demo, build_gun_eater_demo
from gameoflife.visualize import render_ascii, run_pygame


def render_active(grid, margin=2):
    """ASCII-render only the bounding box of live cells (with a small margin)."""
    bb = bounding_box(grid)
    if bb is None:
        return "(empty)"
    rmin, cmin, rmax, cmax = bb
    rmin = max(0, rmin - margin)
    cmin = max(0, cmin - margin)
    rmax = min(grid.shape[0] - 1, rmax + margin)
    cmax = min(grid.shape[1] - 1, cmax + margin)
    sub = grid[rmin:rmax + 1, cmin:cmax + 1]
    return f"(rows {rmin}..{rmax}, cols {cmin}..{cmax})\n" + render_ascii(sub)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("demo", choices=["collision", "gun", "all"],
                   nargs="?", default="all")
    p.add_argument("--pygame", action="store_true",
                   help="Open the interactive viewer instead of stepping ASCII")
    p.add_argument("--steps", type=int, default=60)
    args = p.parse_args(argv)

    demos = []
    if args.demo in ("collision", "all"):
        demos.append(("Head-on glider collision (settles into still lifes)",
                      build_collision_demo()))
    if args.demo in ("gun", "all"):
        demos.append(("Gosper gun + eater (steady-state stream)",
                      build_gun_eater_demo()))

    for title, board in demos:
        print(f"\n=== {title} ===")
        print(f"  {board!r}")
        if args.pygame:
            run_pygame(board, title=title)
        else:
            print(f"\nGeneration 0  (active area shown)")
            print(render_active(board.grid))
            board.tick(args.steps)
            print(f"\nGeneration {board.generation}  pop={board.population}")
            print(render_active(board.grid))
            print(f"\n(use --pygame for the interactive viewer)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
