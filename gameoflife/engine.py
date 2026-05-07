"""Fast Game of Life engine.

Neighbor-count backends (auto-selected — scipy preferred, numpy fallback):
    - scipy.signal.convolve2d with a 3x3 ones kernel.
    - pure-numpy roll-based when scipy is unavailable.

Boundary modes: 'wrap' (toroidal), 'fill' (dead cells outside the grid).

Custom rules: B/S notation. Default is Conway's B3/S23.
    - B-set: birth counts (a dead cell with N live neighbors becomes alive iff N in B).
    - S-set: survival counts (a live cell stays alive iff its neighbor count is in S).
    Examples:
        B3/S23   - Conway's Life
        B36/S23  - HighLife (with replicator)
        B2/S     - Seeds (no survival)
        B1/S1    - Gnarl
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Tuple

import numpy as np

try:
    from scipy.signal import convolve2d
    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False


_KERNEL = np.array([[1, 1, 1],
                    [1, 0, 1],
                    [1, 1, 1]], dtype=np.uint8)


def parse_rule(rule: str) -> Tuple[frozenset, frozenset]:
    """Parse a B/S rule string. Returns (birth_set, survive_set).

    Accepts 'B3/S23', 'b3/s23', '3/23', etc.
    """
    s = rule.strip().lower().replace(" ", "")
    if "/" not in s:
        raise ValueError(f"Rule must contain '/': got {rule!r}")
    left, right = s.split("/", 1)
    left = left.lstrip("b")
    right = right.lstrip("s")
    try:
        b = frozenset(int(c) for c in left)
        srv = frozenset(int(c) for c in right)
    except ValueError as exc:
        raise ValueError(f"Rule digits must be 0-8: got {rule!r}") from exc
    # 8-cell Moore neighborhood — any digit outside 0-8 can never match.
    bad = {n for n in (b | srv) if n < 0 or n > 8}
    if bad:
        raise ValueError(
            f"Rule digits must be 0-8 (8-neighborhood): got {rule!r} "
            f"with invalid digit(s) {sorted(bad)}"
        )
    return b, srv


def step(grid: np.ndarray,
         birth: Iterable[int] = (3,),
         survive: Iterable[int] = (2, 3),
         boundary: str = "wrap") -> np.ndarray:
    """Advance one generation. Returns a NEW array (does not mutate input).

    Args:
        grid: 2D uint8 array (0 = dead, 1 = alive).
        birth: neighbor counts that revive a dead cell.
        survive: neighbor counts that keep a live cell alive.
        boundary: 'wrap' (toroidal) or 'fill' (dead outside).
    """
    if grid.dtype != np.uint8:
        grid = grid.astype(np.uint8)

    if _HAS_SCIPY:
        if boundary == "wrap":
            n = convolve2d(grid, _KERNEL, mode="same", boundary="wrap")
        elif boundary == "fill":
            n = convolve2d(grid, _KERNEL, mode="same",
                           boundary="fill", fillvalue=0)
        else:
            raise ValueError(f"Unknown boundary: {boundary!r}")
    else:
        n = _neighbor_count_numpy(grid, boundary)

    birth_mask = np.zeros_like(grid, dtype=bool)
    survive_mask = np.zeros_like(grid, dtype=bool)
    for b in birth:
        birth_mask |= (n == b)
    for s in survive:
        survive_mask |= (n == s)

    alive = grid.astype(bool)
    new_alive = (~alive & birth_mask) | (alive & survive_mask)
    return new_alive.astype(np.uint8)


def _neighbor_count_numpy(grid: np.ndarray, boundary: str) -> np.ndarray:
    """Pure-numpy 8-neighborhood count. Fallback when scipy is missing."""
    if boundary == "wrap":
        out = np.zeros_like(grid, dtype=np.uint8)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                out += np.roll(grid, (di, dj), axis=(0, 1))
        return out
    elif boundary == "fill":
        padded = np.zeros((grid.shape[0] + 2, grid.shape[1] + 2),
                          dtype=np.uint8)
        padded[1:-1, 1:-1] = grid
        out = np.zeros_like(grid, dtype=np.uint8)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                out += padded[1 + di:1 + di + grid.shape[0],
                              1 + dj:1 + dj + grid.shape[1]]
        return out
    else:
        raise ValueError(f"Unknown boundary: {boundary!r}")


@dataclass
class LifeBoard:
    """A Game of Life board with state and configuration.

    >>> b = LifeBoard.empty(20, 20)
    >>> b.set_cells([(10, 10), (10, 11), (10, 12)])  # blinker
    >>> b.tick(2)
    >>> b.population
    3
    """
    grid: np.ndarray
    rule: str = "B3/S23"
    boundary: str = "wrap"
    generation: int = 0

    def __post_init__(self):
        if self.grid.dtype != np.uint8:
            self.grid = self.grid.astype(np.uint8)
        # Validate inputs at construction time so errors surface early.
        parse_rule(self.rule)
        if self.boundary not in ("wrap", "fill"):
            raise ValueError(f"boundary must be 'wrap' or 'fill', got "
                             f"{self.boundary!r}")

    # ---------------------- constructors -----------------------------

    @classmethod
    def empty(cls, rows: int, cols: int, **kwargs) -> "LifeBoard":
        return cls(grid=np.zeros((rows, cols), dtype=np.uint8), **kwargs)

    @classmethod
    def random(cls, rows: int, cols: int, density: float = 0.3,
               seed: int | None = None, **kwargs) -> "LifeBoard":
        rng = np.random.default_rng(seed)
        grid = (rng.random((rows, cols)) < density).astype(np.uint8)
        return cls(grid=grid, **kwargs)

    @classmethod
    def from_pattern(cls, pattern: Any, rows: int = 0, cols: int = 0,
                     center: bool = True, **kwargs) -> "LifeBoard":
        """Place `pattern` on a board of size (rows, cols). If rows/cols are
        zero, the board is sized with a 5x margin around the pattern.

        `pattern` can be a numpy array OR a Pattern object — when a Pattern
        is passed, its `rule` is auto-inherited unless the caller overrides
        it via `rule=...` in kwargs.
        """
        # Duck-typed Pattern handling — avoids a circular import on patterns.py.
        if hasattr(pattern, "grid") and hasattr(pattern, "rule"):
            kwargs.setdefault("rule", pattern.rule)
            grid = pattern.grid
        else:
            grid = pattern
        ph, pw = grid.shape
        if rows == 0:
            rows = max(ph * 5, ph + 20)
        if cols == 0:
            cols = max(pw * 5, pw + 20)
        if rows < ph or cols < pw:
            raise ValueError(f"Board {rows}x{cols} too small for pattern "
                             f"{ph}x{pw}")
        board = cls.empty(rows, cols, **kwargs)
        if center:
            r0 = (rows - ph) // 2
            c0 = (cols - pw) // 2
        else:
            r0, c0 = 0, 0
        board.grid[r0:r0 + ph, c0:c0 + pw] = np.asarray(grid, dtype=np.uint8)
        return board

    # ---------------------- mutation -----------------------------

    def set_cells(self, cells: Iterable[Tuple[int, int]], value: int = 1):
        for r, c in cells:
            self.grid[r, c] = value

    def place(self, pattern: np.ndarray, row: int, col: int):
        """Stamp `pattern` onto the board with top-left at (row, col).
        Out-of-bounds cells are clipped silently."""
        ph, pw = pattern.shape
        r0, c0 = row, col
        r1, c1 = row + ph, col + pw
        # Clip to board
        ar0 = max(0, r0)
        ac0 = max(0, c0)
        ar1 = min(self.grid.shape[0], r1)
        ac1 = min(self.grid.shape[1], c1)
        if ar1 <= ar0 or ac1 <= ac0:
            return
        pr0 = ar0 - r0
        pc0 = ac0 - c0
        pr1 = pr0 + (ar1 - ar0)
        pc1 = pc0 + (ac1 - ac0)
        self.grid[ar0:ar1, ac0:ac1] |= pattern[pr0:pr1, pc0:pc1].astype(np.uint8)

    def clear(self):
        self.grid[:] = 0
        self.generation = 0

    # ---------------------- evolution -----------------------------

    def tick(self, n: int = 1) -> "LifeBoard":
        """Advance n generations IN PLACE. Returns self for chaining.

        Re-parses `self.rule` once per call, so mutating `.rule` between
        calls takes effect immediately.
        """
        birth, survive = parse_rule(self.rule)
        for _ in range(n):
            self.grid = step(self.grid, birth, survive, self.boundary)
            self.generation += 1
        return self

    def copy(self) -> "LifeBoard":
        return LifeBoard(grid=self.grid.copy(), rule=self.rule,
                         boundary=self.boundary, generation=self.generation)

    # ---------------------- inspection -----------------------------

    @property
    def population(self) -> int:
        return int(self.grid.sum())

    @property
    def shape(self) -> Tuple[int, int]:
        return self.grid.shape

    def __repr__(self) -> str:
        return (f"LifeBoard(shape={self.shape}, gen={self.generation}, "
                f"pop={self.population}, rule={self.rule!r}, "
                f"boundary={self.boundary!r})")

    def __str__(self) -> str:
        """ASCII rendering — '#' alive, '.' dead. Truncated at 80x40."""
        h, w = self.shape
        h = min(h, 40)
        w = min(w, 80)
        lines = []
        for r in range(h):
            lines.append("".join("#" if self.grid[r, c] else "."
                                 for c in range(w)))
        return "\n".join(lines)


def simulate(board: LifeBoard, steps: int,
             record_every: int = 1) -> Iterator[np.ndarray]:
    """Yield snapshots of the grid as the board ticks forward.

    The first yield is the INITIAL state (generation 0 of this call).
    Then yields after every `record_every` ticks. Mutates the board.
    """
    if record_every <= 0:
        raise ValueError(f"record_every must be > 0, got {record_every}")
    yield board.grid.copy()
    for i in range(steps):
        board.tick()
        if (i + 1) % record_every == 0:
            yield board.grid.copy()
