"""Logic-gate construction primitives in Life.

Background — why Life is Turing-complete
----------------------------------------
A Gosper glider gun fires a glider every 30 generations. Glider streams
encode bits (presence = 1, absence = 0). When two streams collide at the
right angle and offset:

    - certain collisions ANNIHILATE both gliders (a "destructor")
    - certain collisions REFLECT one stream
    - certain collisions emit a NEW glider perpendicular to both inputs

By carefully placing guns, eaters (like the "fishhook" / eater 1), and
reflectors, you can build NOT, AND, OR gates, then memory cells, then a
universal Turing machine. Paul Rendell built the first explicit UTM in
Life in 2010; it's huge (tens of thousands of cells) but mechanically
straightforward once you have the gate library.

This module gives you the primitives:

    - GLIDER_NE, GLIDER_NW, GLIDER_SE, GLIDER_SW : 4 phase-locked gliders
    - GOSPER_GUN_SE   : the canonical glider gun (period 30)
    - EATER1          : "fishhook" still life that absorbs a glider every
                        4 generations during the absorption sequence
    - place_gun, place_eater, place_glider — helpers to stamp them at
      specific board coordinates

We DON'T ship a full NAND or memory cell here — those are research
artifacts you can build on top. For the full UTM see the references in
patterns/turing/README.md.

Reference: https://conwaylife.com/wiki/OTCA_metapixel
           https://conwaylife.com/wiki/Turing_machine
"""
from __future__ import annotations

import numpy as np

from gameoflife.engine import LifeBoard


# 4 directional gliders (phase 0). The shape is the same; the orientation
# is the difference. Direction names refer to where the glider TRAVELS.
GLIDER_SE = np.array([
    [0, 1, 0],
    [0, 0, 1],
    [1, 1, 1],
], dtype=np.uint8)

GLIDER_SW = np.fliplr(GLIDER_SE).copy()
GLIDER_NE = np.flipud(GLIDER_SE).copy()
GLIDER_NW = np.flipud(np.fliplr(GLIDER_SE)).copy()

# Gosper glider gun (Bill Gosper, 1970) — period 30, fires SE-bound gliders.
# 36x9 bounding box.
GOSPER_GUN_SE = np.array([
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
    [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
    [1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
], dtype=np.uint8)


# Eater 1 ("fishhook") — a 7-cell still life that absorbs SE-bound gliders.
# When a glider hits the mouth, both eater and glider deform for 4 generations,
# then the eater reforms in its original shape (the glider is gone). 4x4 box.
EATER1 = np.array([
    [1, 1, 0, 0],
    [1, 0, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
], dtype=np.uint8)


def place_gun(board: LifeBoard, row: int, col: int,
              direction: str = "SE") -> None:
    """Stamp a Gosper glider gun. `direction` is the firing direction."""
    if direction == "SE":
        board.place(GOSPER_GUN_SE, row, col)
    elif direction == "SW":
        board.place(np.fliplr(GOSPER_GUN_SE).copy(), row, col)
    elif direction == "NE":
        board.place(np.flipud(GOSPER_GUN_SE).copy(), row, col)
    elif direction == "NW":
        board.place(np.flipud(np.fliplr(GOSPER_GUN_SE)).copy(), row, col)
    else:
        raise ValueError(f"direction must be SE/SW/NE/NW, got {direction!r}")


def place_eater(board: LifeBoard, row: int, col: int,
                direction: str = "SE") -> None:
    """Stamp an eater 1 ('fishhook'). Direction is the mouth orientation."""
    pattern = EATER1
    if direction == "SE":
        pass
    elif direction == "SW":
        pattern = np.fliplr(EATER1).copy()
    elif direction == "NE":
        pattern = np.flipud(EATER1).copy()
    elif direction == "NW":
        pattern = np.flipud(np.fliplr(EATER1)).copy()
    else:
        raise ValueError(f"direction must be SE/SW/NE/NW, got {direction!r}")
    board.place(pattern, row, col)


def place_glider(board: LifeBoard, row: int, col: int,
                 direction: str = "SE") -> None:
    """Stamp a single glider."""
    table = {"SE": GLIDER_SE, "SW": GLIDER_SW,
             "NE": GLIDER_NE, "NW": GLIDER_NW}
    if direction not in table:
        raise ValueError(f"direction must be SE/SW/NE/NW, got {direction!r}")
    board.place(table[direction], row, col)


def build_collision_demo(rows: int = 80, cols: int = 80) -> LifeBoard:
    """Two head-on gliders meeting near the center.

    The exact outcome (annihilation, blocks, beehive, ships, or other debris)
    depends sensitively on relative phase and offset. With the offsets used
    here the gliders settle into 4 stable still lifes. Adjust the placements
    to explore other outcomes — this is the kind of taxonomy that underpins
    every Life-based logic gate.
    """
    b = LifeBoard.empty(rows, cols, boundary="fill")
    place_glider(b, 10, 10, "SE")
    place_glider(b, 10, cols - 13, "SW")
    return b


def build_gun_eater_demo(rows: int = 60, cols: int = 80) -> LifeBoard:
    """A glider gun firing into an eater 1 — a stable producer/consumer
    pair. Demonstrates how to clean up a stream."""
    b = LifeBoard.empty(rows, cols, boundary="fill")
    place_gun(b, 5, 5, "SE")
    # The gun's SE-bound gliders travel along the diagonal row - col = -14.
    # An SE-oriented eater whose top-left cell is at (30, 44) sits on that
    # diagonal and swallows every glider; from about generation 200 on the
    # whole board repeats exactly every 30 generations.
    place_eater(b, 30, 44, "SE")
    return b
