#!/usr/bin/env python3
"""Analyze a pattern: detect period, classify, plot population.

Examples:
    python scripts/analyze_pattern.py glider
    python scripts/analyze_pattern.py r_pentomino --max-steps 1500 --plot
    python scripts/analyze_pattern.py pulsar
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from gameoflife import LifeBoard, PatternLibrary, load_rle
from gameoflife.analysis import detect_period, population
from gameoflife.visualize import render_ascii


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pattern", help="Library name or path to .rle file")
    p.add_argument("--max-steps", type=int, default=1000,
                   help="Cap for period detection (default: 1000)")
    p.add_argument("--boundary", choices=["wrap", "fill"], default="fill",
                   help="'fill' is correct for spaceships and methuselahs "
                        "since toroidal wrap distorts their behavior")
    p.add_argument("--plot", action="store_true",
                   help="Plot population over time")
    p.add_argument("--plot-out", type=str, default="pop.png",
                   help="Output path for --plot (default: pop.png in CWD)")
    p.add_argument("--ascii", action="store_true",
                   help="Show the initial pattern as ASCII")
    args = p.parse_args(argv)

    # Load pattern from library or direct path
    path = Path(args.pattern)
    if path.exists():
        pat = load_rle(path)
    else:
        lib = PatternLibrary()
        pat = lib.get(args.pattern)

    print(f"Loaded {pat!r}")
    if args.ascii:
        print(render_ascii(pat.grid))
        print()

    # Place on a generously-sized board
    margin = max(args.max_steps // 10, 50)
    rows = pat.grid.shape[0] + 2 * margin
    cols = pat.grid.shape[1] + 2 * margin
    board = LifeBoard.from_pattern(pat.grid, rows=rows, cols=cols,
                                   rule=pat.rule, boundary=args.boundary)

    # Detect period
    print(f"Running period detection (max_steps={args.max_steps}, "
          f"boundary={args.boundary})...")
    board_for_period = board.copy()
    result = detect_period(board_for_period, max_steps=args.max_steps)
    print(f"  {result}")

    # Population trace
    board_for_pop = board.copy()
    pop = population(board_for_pop, args.max_steps)
    print(f"\nPopulation trace ({args.max_steps + 1} samples):")
    print(f"  initial:  {pop[0]}")
    print(f"  min:      {pop.min()}  at step {pop.argmin()}")
    print(f"  max:      {pop.max()}  at step {pop.argmax()}")
    print(f"  final:    {pop[-1]}")
    print(f"  mean:     {pop.mean():.1f}")

    if args.plot:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not installed; skipping plot")
            return 0
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(pop, lw=1)
        ax.set_xlabel("Generation")
        ax.set_ylabel("Live cells")
        ax.set_title(f"{pat.name} — population over time")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(args.plot_out, dpi=120)
        print(f"\nSaved plot to {args.plot_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
