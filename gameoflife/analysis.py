"""Pattern analysis: period detection, population, bounding box, displacement.

Useful for classifying patterns:
    - period 1, displacement 0  -> still life
    - period > 1, displacement 0 -> oscillator
    - period > 1, displacement != 0 -> spaceship
    - never returns -> infinite-growth / methuselah
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from gameoflife.engine import LifeBoard


@dataclass
class PeriodResult:
    period: Optional[int]            # None if not found within max_steps
    displacement: Tuple[int, int]    # (drow, dcol) over one period
    final_population: int
    is_still_life: bool
    is_oscillator: bool
    is_spaceship: bool

    def __repr__(self):
        kind = ("still life" if self.is_still_life else
                "oscillator" if self.is_oscillator else
                "spaceship" if self.is_spaceship else
                "unknown")
        return (f"PeriodResult(period={self.period}, displacement="
                f"{self.displacement}, kind={kind}, "
                f"final_population={self.final_population})")


def bounding_box(grid: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """(rmin, cmin, rmax, cmax) of live cells, inclusive. None if empty."""
    if grid.sum() == 0:
        return None
    rows = np.any(grid, axis=1)
    cols = np.any(grid, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return int(rmin), int(cmin), int(rmax), int(cmax)


def center_of_mass(grid: np.ndarray) -> Optional[Tuple[float, float]]:
    """Population-weighted centroid. None if grid is empty."""
    pop = grid.sum()
    if pop == 0:
        return None
    rs, cs = np.where(grid > 0)
    return float(rs.mean()), float(cs.mean())


def population(board: LifeBoard, steps: int) -> np.ndarray:
    """Population-over-time vector of length `steps + 1` (includes step 0).

    Mutates the board (advances it `steps` ticks).
    """
    out = np.zeros(steps + 1, dtype=np.int64)
    out[0] = board.population
    for i in range(steps):
        board.tick()
        out[i + 1] = board.population
    return out


def _crop(grid: np.ndarray):
    bb = bounding_box(grid)
    if bb is None:
        return np.zeros((0, 0), dtype=grid.dtype), (0, 0)
    rmin, cmin, rmax, cmax = bb
    return grid[rmin:rmax + 1, cmin:cmax + 1].copy(), (rmin, cmin)


def detect_period(board: LifeBoard, max_steps: int = 1000,
                  ignore_translation: bool = True) -> PeriodResult:
    """Find the period of a pattern.

    Compares the *cropped* live-cell pattern to the initial cropped pattern.
    With `ignore_translation=True` (default), spaceships are detected: any
    translation that yields the same cropped pattern counts as a match,
    and the displacement of the bounding-box top-left is reported.

    Mutates the board.
    """
    initial_crop, initial_origin = _crop(board.grid)
    initial_pop = int(initial_crop.sum())
    if initial_pop == 0:
        # An empty grid is trivially stable — call it a (degenerate) still life.
        return PeriodResult(period=1, displacement=(0, 0),
                            final_population=0,
                            is_still_life=True,
                            is_oscillator=False,
                            is_spaceship=False)

    for step_idx in range(1, max_steps + 1):
        board.tick()
        cur_crop, cur_origin = _crop(board.grid)
        if cur_crop.shape == initial_crop.shape and \
                np.array_equal(cur_crop, initial_crop):
            if ignore_translation:
                drow = cur_origin[0] - initial_origin[0]
                dcol = cur_origin[1] - initial_origin[1]
            else:
                drow = dcol = 0
                # Fall through only if origin matches
                if cur_origin != initial_origin:
                    continue
            is_still = step_idx == 1 and (drow, dcol) == (0, 0)
            is_osc = (drow, dcol) == (0, 0) and step_idx > 1
            is_ship = (drow, dcol) != (0, 0)
            return PeriodResult(
                period=step_idx,
                displacement=(drow, dcol),
                final_population=int(board.grid.sum()),
                is_still_life=is_still,
                is_oscillator=is_osc,
                is_spaceship=is_ship,
            )

    return PeriodResult(period=None, displacement=(0, 0),
                        final_population=int(board.grid.sum()),
                        is_still_life=False,
                        is_oscillator=False,
                        is_spaceship=False)


def density(grid: np.ndarray) -> float:
    """Live-cell fraction."""
    return float(grid.mean())


def hash_grid(grid: np.ndarray) -> int:
    """Stable hash of grid contents — useful for cycle detection over big runs."""
    cropped, _ = _crop(grid)
    return hash(cropped.tobytes() + bytes(cropped.shape))
