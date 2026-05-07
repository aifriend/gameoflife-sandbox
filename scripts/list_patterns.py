#!/usr/bin/env python3
"""List all bundled patterns with their headline stats.

    python scripts/list_patterns.py
    python scripts/list_patterns.py --verify  # also detect period for each
"""
from __future__ import annotations

import argparse
import sys

from gameoflife import LifeBoard, PatternLibrary, load_rle
from gameoflife.analysis import detect_period


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true",
                   help="Run period detection on each pattern (slower)")
    p.add_argument("--max-steps", type=int, default=200)
    args = p.parse_args(argv)

    lib = PatternLibrary()
    print(f"Library root: {lib.root}\n")

    for cat in lib.list_categories():
        files = lib.list_patterns(cat)
        print(f"[{cat}]  ({len(files)} patterns)")
        for rel in files:
            full = lib.root / rel
            pat = load_rle(full)
            row = f"  {rel.stem:30s}  {pat.shape[0]:>3} x {pat.shape[1]:>3}   pop={pat.population:>4}"
            if args.verify:
                margin = max(args.max_steps // 5, 30)
                board = LifeBoard.from_pattern(
                    pat.grid,
                    rows=pat.shape[0] + 2 * margin,
                    cols=pat.shape[1] + 2 * margin,
                    rule=pat.rule, boundary="fill",
                )
                res = detect_period(board, max_steps=args.max_steps)
                if res.period is None:
                    row += f"   period=>{args.max_steps}"
                else:
                    kind = ("still" if res.is_still_life else
                            "osc" if res.is_oscillator else
                            "ship" if res.is_spaceship else "?")
                    row += f"   period={res.period} disp={res.displacement} ({kind})"
            print(row)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
