"""Glider gun / eater primitives in gameoflife.gates."""
import numpy as np
import pytest

from gameoflife import LifeBoard, PatternLibrary
from gameoflife.gates import (
    EATER1,
    GLIDER_SE,
    GOSPER_GUN_SE,
    build_collision_demo,
    build_gun_eater_demo,
    place_eater,
    place_glider,
    place_gun,
)


def test_gun_array_matches_bundled_rle_file():
    """The in-code gun must equal the RLE file (the right block sits at
    columns 34-35, not 33-34)."""
    rle = PatternLibrary().get("gosper_glider_gun").grid
    np.testing.assert_array_equal(GOSPER_GUN_SE, rle)
    assert GOSPER_GUN_SE[2:4, 34:36].sum() == 4
    assert GOSPER_GUN_SE[:, 36:].size == 0  # 36 columns wide


def test_gun_population_grows_over_120_generations():
    """A working gun emits a glider every 30 generations, so the live-cell
    count must keep rising: 36 cells at generation 0, 36 + 5 * k later."""
    board = LifeBoard.empty(80, 160, boundary="fill")
    place_gun(board, 5, 5, "SE")
    assert board.population == 36
    board.tick(120)
    # Four gliders have been released, none has left the board yet.
    assert board.population >= 36 + 4 * 5
    assert board.population > 36


def test_gun_emits_one_glider_every_30_generations():
    board = LifeBoard.empty(80, 160, boundary="fill")
    place_gun(board, 5, 5, "SE")
    board.tick(60)
    pop_60 = board.population
    board.tick(30)
    # Same phase of the gun, exactly one more glider in flight.
    assert board.population == pop_60 + 5


def test_gun_eater_demo_is_periodic_with_period_30():
    board = build_gun_eater_demo()
    board.tick(240)  # let the first gliders reach the eater
    reference = board.grid.copy()
    pops = []
    for _ in range(30):
        board.tick()
        pops.append(board.population)
    # Exactly one gun cycle later the whole board is identical.
    np.testing.assert_array_equal(board.grid, reference)
    # Population is bounded: the stream is being eaten, not growing.
    assert max(pops) < 100


def test_gun_eater_demo_consumes_the_stream():
    board = build_gun_eater_demo()
    board.tick(300)
    # Nothing survives past the eater's position.
    assert board.grid[35:, :].sum() == 0
    assert board.grid[:, 49:].sum() == 0
    # The eater itself is intact at generation 300 (a multiple of 30).
    np.testing.assert_array_equal(board.grid[30:34, 44:48], EATER1)


def test_collision_demo_runs_and_leaves_debris():
    # Smoke check only. The builder's docstring says the debris settles into
    # still lifes, which is not asserted here (see the pull request notes).
    board = build_collision_demo()
    assert board.population == 10  # two gliders
    board.tick(200)
    assert board.population > 0


@pytest.mark.parametrize("direction", ["SE", "SW", "NE", "NW"])
def test_place_helpers_stamp_cells(direction):
    board = LifeBoard.empty(60, 60, boundary="fill")
    place_glider(board, 10, 10, direction)
    assert board.population == 5
    place_eater(board, 30, 30, direction)
    assert board.population == 5 + 7


@pytest.mark.parametrize("helper", [place_gun, place_eater, place_glider])
def test_place_helpers_reject_unknown_direction(helper):
    board = LifeBoard.empty(60, 60, boundary="fill")
    with pytest.raises(ValueError):
        helper(board, 5, 5, "XX")


def test_glider_se_is_the_phase_zero_glider():
    assert GLIDER_SE.sum() == 5
