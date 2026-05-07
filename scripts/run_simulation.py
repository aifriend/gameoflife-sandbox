#!/usr/bin/env python3
"""Run a Game of Life simulation interactively in pygame.

Examples:
    # Random soup, 100x100 toroidal
    python scripts/run_simulation.py --rows 100 --cols 100 --random 0.3

    # Load a famous pattern
    python scripts/run_simulation.py --pattern glider
    python scripts/run_simulation.py --pattern gosper_glider_gun --rows 60 --cols 100

    # Custom rule (HighLife)
    python scripts/run_simulation.py --random 0.4 --rule B36/S23

Controls:
    SPACE       pause/resume
    LEFT-CLICK  toggle a cell (when paused)
    RIGHT-CLICK clear a cell
    n           single step
    r           randomize
    c           clear
    +/-         faster/slower
    q / ESC     quit
"""
from __future__ import annotations

import argparse
import sys

from gameoflife import LifeBoard, PatternLibrary
from gameoflife.visualize import run_pygame


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rows", type=int, default=80)
    p.add_argument("--cols", type=int, default=120)
    p.add_argument("--rule", default="B3/S23",
                   help="B/S notation (default: B3/S23 — Conway's Life)")
    p.add_argument("--boundary", choices=["wrap", "fill"], default="wrap")
    p.add_argument("--cell-size", type=int, default=8)
    p.add_argument("--fps", type=int, default=20,
                   help="Initial ticks per second (use +/- to adjust live)")
    p.add_argument("--random", type=float, default=None,
                   metavar="DENSITY",
                   help="Start with a random soup of given density (0.0-1.0)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--pattern", type=str, default=None,
                   help="Load a named pattern from the library "
                        "(e.g. glider, gosper_glider_gun, r_pentomino)")
    p.add_argument("--list-patterns", action="store_true")
    args = p.parse_args(argv)

    lib = PatternLibrary()

    if args.list_patterns:
        for cat in lib.list_categories():
            print(f"\n[{cat}]")
            for f in lib.list_patterns(cat):
                print(f"  {f.stem}")
        return 0

    if args.pattern:
        pat = lib.get(args.pattern)
        print(f"Loaded {pat!r}")
        board = LifeBoard.from_pattern(
            pat.grid,
            rows=args.rows, cols=args.cols,
            rule=pat.rule, boundary=args.boundary,
        )
    elif args.random is not None:
        board = LifeBoard.random(
            args.rows, args.cols,
            density=args.random, seed=args.seed,
            rule=args.rule, boundary=args.boundary,
        )
    else:
        # Default: a glider in the middle
        pat = lib.get("glider")
        board = LifeBoard.from_pattern(
            pat.grid, rows=args.rows, cols=args.cols,
            rule=args.rule, boundary=args.boundary,
        )

    print(f"Starting: {board!r}")
    print("SPACE pause | n step | r random | c clear | +/- speed | q quit")
    run_pygame(board, cell_size=args.cell_size, fps=args.fps,
               title=f"Life — {args.pattern or 'soup'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
