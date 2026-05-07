#!/usr/bin/env python3
"""Render a pattern's evolution as an animated GIF or MP4.

Examples:
    python scripts/animate.py glider --steps 40 --out glider.gif
    python scripts/animate.py r_pentomino --steps 200 --out r_pent.gif
    python scripts/animate.py gosper_glider_gun --steps 120 --out gun.mp4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gameoflife import LifeBoard, PatternLibrary, load_rle
from gameoflife.visualize import animate_matplotlib


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pattern", help="Library name or path to .rle file")
    p.add_argument("--steps", type=int, default=100)
    p.add_argument("--rows", type=int, default=0,
                   help="Override board height (default: auto-fit)")
    p.add_argument("--cols", type=int, default=0,
                   help="Override board width (default: auto-fit)")
    p.add_argument("--boundary", choices=["wrap", "fill"], default="fill")
    p.add_argument("--interval-ms", type=int, default=80)
    p.add_argument("--fps", type=int, default=15)
    p.add_argument("--out", type=str, required=True,
                   help="Output file (.gif or .mp4)")
    args = p.parse_args(argv)

    path = Path(args.pattern)
    if path.exists():
        pat = load_rle(path)
    else:
        pat = PatternLibrary().get(args.pattern)

    print(f"Loaded {pat!r}")
    board = LifeBoard.from_pattern(
        pat.grid, rows=args.rows, cols=args.cols,
        rule=pat.rule, boundary=args.boundary,
    )
    print(f"Board: {board!r}")
    print(f"Rendering {args.steps} steps to {args.out}...")
    animate_matplotlib(
        board, steps=args.steps,
        interval_ms=args.interval_ms,
        title=pat.name,
        save_path=args.out,
        fps=args.fps,
    )
    print(f"Saved {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
