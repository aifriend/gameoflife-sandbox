"""Analysis tools — period detection, bounding box, population trace."""
import numpy as np
import pytest

from gameoflife import LifeBoard
from gameoflife.analysis import (
    bounding_box,
    center_of_mass,
    detect_period,
    hash_grid,
    population,
)


def test_bounding_box_empty():
    assert bounding_box(np.zeros((5, 5), dtype=np.uint8)) is None


def test_bounding_box_single_cell():
    g = np.zeros((10, 10), dtype=np.uint8)
    g[3, 7] = 1
    assert bounding_box(g) == (3, 7, 3, 7)


def test_bounding_box_block():
    g = np.zeros((10, 10), dtype=np.uint8)
    g[2:4, 5:7] = 1
    assert bounding_box(g) == (2, 5, 3, 6)


def test_center_of_mass():
    g = np.zeros((10, 10), dtype=np.uint8)
    g[2:4, 5:7] = 1   # 2x2 block, COM = (2.5, 5.5)
    com = center_of_mass(g)
    assert com == pytest.approx((2.5, 5.5))


def test_population_trace_blinker():
    b = LifeBoard.empty(5, 5, boundary="fill")
    b.set_cells([(2, 1), (2, 2), (2, 3)])
    pop = population(b, steps=4)
    # Blinker stays at 3 forever
    assert pop.tolist() == [3, 3, 3, 3, 3]


def test_detect_period_block():
    b = LifeBoard.empty(8, 8, boundary="fill")
    b.set_cells([(3, 3), (3, 4), (4, 3), (4, 4)])
    res = detect_period(b, max_steps=5)
    assert res.period == 1
    assert res.is_still_life


def test_detect_period_glider_displacement():
    glider = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ], dtype=np.uint8)
    b = LifeBoard.from_pattern(glider, rows=20, cols=20, boundary="fill")
    res = detect_period(b, max_steps=10)
    assert res.period == 4
    assert res.displacement == (1, 1)
    assert res.is_spaceship


def test_detect_period_no_match_returns_none():
    """R-pentomino doesn't return to its initial state inside 100 steps."""
    r_pent = np.array([
        [0, 1, 1],
        [1, 1, 0],
        [0, 1, 0],
    ], dtype=np.uint8)
    b = LifeBoard.from_pattern(r_pent, rows=80, cols=80, boundary="fill")
    res = detect_period(b, max_steps=100)
    assert res.period is None


def test_detect_period_empty_grid_is_still_life():
    """Regression: empty grid used to return is_still_life=False."""
    b = LifeBoard.empty(10, 10, boundary="fill")
    res = detect_period(b, max_steps=5)
    assert res.period == 1
    assert res.is_still_life is True
    assert res.final_population == 0


def test_hash_grid_translation_invariant():
    """A pattern in two different positions should hash the same."""
    g1 = np.zeros((10, 10), dtype=np.uint8)
    g2 = np.zeros((10, 10), dtype=np.uint8)
    glider = np.array([[0, 1, 0], [0, 0, 1], [1, 1, 1]], dtype=np.uint8)
    g1[1:4, 1:4] = glider
    g2[5:8, 6:9] = glider
    assert hash_grid(g1) == hash_grid(g2)


def test_hash_grid_is_stable_across_processes():
    """blake2b is not salted per process, unlike the built-in hash()."""
    import subprocess
    import sys
    code = (
        "import numpy as np; from gameoflife import hash_grid; "
        "g = np.zeros((6, 6), dtype=np.uint8); g[1, 2] = g[2, 3] = g[3, 1] = 1; "
        "print(hash_grid(g))"
    )
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, check=True).stdout.strip() for _ in range(2)}
    assert len(outs) == 1


def test_hash_grid_distinguishes_shapes_with_same_cells():
    row = np.ones((1, 4), dtype=np.uint8)
    square = np.ones((2, 2), dtype=np.uint8)
    assert hash_grid(row) != hash_grid(square)
