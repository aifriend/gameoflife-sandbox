"""Engine correctness — well-known patterns must reproduce themselves."""
import numpy as np
import pytest

from gameoflife.engine import LifeBoard, parse_rule, simulate, step


def test_parse_rule_conway():
    b, s = parse_rule("B3/S23")
    assert b == frozenset({3})
    assert s == frozenset({2, 3})


def test_parse_rule_alt_forms():
    assert parse_rule("b3/s23") == parse_rule("B3/S23")
    assert parse_rule("3/23") == parse_rule("B3/S23")
    assert parse_rule(" B3/S23 ") == parse_rule("B3/S23")


def test_parse_rule_highlife():
    b, s = parse_rule("B36/S23")
    assert b == frozenset({3, 6})
    assert s == frozenset({2, 3})


def test_parse_rule_rejects_out_of_range_digit():
    """B9 etc. have no meaning in an 8-neighborhood — must error early."""
    with pytest.raises(ValueError, match="0-8"):
        parse_rule("B9/S23")
    with pytest.raises(ValueError, match="0-8"):
        parse_rule("B3/S239")


def test_parse_rule_rejects_letters():
    with pytest.raises(ValueError, match="0-8"):
        parse_rule("B3z/S23")


def test_parse_rule_rejects_missing_slash():
    with pytest.raises(ValueError, match="/"):
        parse_rule("B3S23")


def test_simulate_rejects_zero_record_every():
    """Regression: record_every=0 used to crash with ZeroDivisionError."""
    b = LifeBoard.empty(5, 5)
    with pytest.raises(ValueError, match="record_every"):
        list(simulate(b, steps=3, record_every=0))


def test_place_clips_negative_coords():
    """place() should silently clip a pattern that overhangs the top-left."""
    b = LifeBoard.empty(5, 5, boundary="fill")
    glider = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ], dtype=np.uint8)
    # Place with top-left at (-1, -1) — only the bottom-right 2x2 survives
    b.place(glider, -1, -1)
    expected = np.zeros((5, 5), dtype=np.uint8)
    # Survivors: glider[1:3, 1:3] = [[0,1],[1,1]] at board[0:2, 0:2]
    expected[0, 1] = 1
    expected[1, 0] = 1
    expected[1, 1] = 1
    np.testing.assert_array_equal(b.grid, expected)


def test_place_clips_overhanging_bottom_right():
    b = LifeBoard.empty(5, 5, boundary="fill")
    block = np.ones((3, 3), dtype=np.uint8)
    b.place(block, 4, 4)
    # Only board[4, 4] gets stamped (the rest overhangs)
    assert b.grid[4, 4] == 1
    assert b.grid.sum() == 1


def test_place_completely_outside_is_noop():
    b = LifeBoard.empty(5, 5)
    b.place(np.ones((2, 2), dtype=np.uint8), -10, -10)
    assert b.population == 0


def test_empty_grid_stays_empty():
    g = np.zeros((10, 10), dtype=np.uint8)
    out = step(g)
    assert out.sum() == 0


def test_single_cell_dies():
    g = np.zeros((10, 10), dtype=np.uint8)
    g[5, 5] = 1
    out = step(g)
    assert out.sum() == 0


def test_block_is_still_life():
    g = np.zeros((6, 6), dtype=np.uint8)
    g[2:4, 2:4] = 1   # 2x2 block
    out = step(g)
    np.testing.assert_array_equal(out, g)


def test_blinker_period_2():
    """Horizontal 3-bar -> vertical 3-bar -> horizontal 3-bar."""
    g = np.zeros((5, 5), dtype=np.uint8)
    g[2, 1:4] = 1
    g1 = step(g)
    g2 = step(g1)
    np.testing.assert_array_equal(g2, g)
    # First step must be vertical
    expected = np.zeros((5, 5), dtype=np.uint8)
    expected[1:4, 2] = 1
    np.testing.assert_array_equal(g1, expected)


def test_glider_translates_diagonally_after_period_4():
    """Glider returns to same shape but offset by (1,1) after 4 generations."""
    glider = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ], dtype=np.uint8)
    g = np.zeros((20, 20), dtype=np.uint8)
    g[2:5, 2:5] = glider

    cur = g.copy()
    for _ in range(4):
        cur = step(cur, boundary="fill")

    # Shape should appear at offset (3, 3) instead of (2, 2)
    expected = np.zeros((20, 20), dtype=np.uint8)
    expected[3:6, 3:6] = glider
    np.testing.assert_array_equal(cur, expected)


def test_population_counts():
    b = LifeBoard.empty(10, 10)
    b.set_cells([(5, 4), (5, 5), (5, 6)])
    assert b.population == 3
    b.tick()
    assert b.population == 3   # blinker preserves count


def test_random_board_repeatable():
    a = LifeBoard.random(20, 20, density=0.3, seed=42)
    b = LifeBoard.random(20, 20, density=0.3, seed=42)
    np.testing.assert_array_equal(a.grid, b.grid)


def test_boundary_wrap_vs_fill():
    """A glider near the edge behaves differently under wrap vs fill."""
    glider = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ], dtype=np.uint8)
    g = np.zeros((10, 10), dtype=np.uint8)
    g[7:10, 7:10] = glider

    out_wrap = step(g, boundary="wrap")
    out_fill = step(g, boundary="fill")
    # Different — wrap allows neighbors to come back from the opposite side
    assert not np.array_equal(out_wrap, out_fill)


def test_highlife_replicator_birth_rule():
    """In B36/S23 a dead cell with 6 neighbors revives. Conway B3/S23 wouldn't."""
    g = np.zeros((5, 5), dtype=np.uint8)
    # 6 neighbors around (2,2)
    g[1, 1] = g[1, 2] = g[1, 3] = 1
    g[3, 1] = g[3, 2] = g[3, 3] = 1
    out_conway = step(g, boundary="fill")
    out_high = step(g, birth=(3, 6), survive=(2, 3), boundary="fill")
    assert out_conway[2, 2] == 0
    assert out_high[2, 2] == 1


def test_simulate_yields_initial_state_first():
    from gameoflife.engine import simulate
    b = LifeBoard.empty(5, 5)
    b.set_cells([(2, 1), (2, 2), (2, 3)])
    snaps = list(simulate(b, steps=2))
    assert len(snaps) == 3
    assert int(snaps[0].sum()) == 3   # initial
    assert int(snaps[1].sum()) == 3   # after 1 tick


def test_simulate_record_every_subsamples():
    from gameoflife.engine import simulate
    b = LifeBoard.empty(5, 5)
    b.set_cells([(2, 1), (2, 2), (2, 3)])
    snaps = list(simulate(b, steps=10, record_every=5))
    # Initial + after step 5 + after step 10
    assert len(snaps) == 3


def test_copy_preserves_state():
    b = LifeBoard.empty(10, 10, rule="B36/S23", boundary="fill")
    b.set_cells([(1, 1), (1, 2), (1, 3)])
    b.tick(2)
    c = b.copy()
    assert c.shape == b.shape
    assert c.population == b.population
    assert c.rule == b.rule
    assert c.boundary == b.boundary
    assert c.generation == b.generation
    np.testing.assert_array_equal(c.grid, b.grid)
    # Independence — mutating copy must not touch original
    c.tick()
    assert c.generation == b.generation + 1


def test_numpy_fallback_matches_scipy(monkeypatch):
    """When scipy is unavailable, the pure-numpy neighbor count must produce
    identical results to the scipy path. Exercises both boundary modes."""
    from gameoflife import engine

    glider = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ], dtype=np.uint8)
    g = np.zeros((20, 20), dtype=np.uint8)
    g[5:8, 5:8] = glider

    for boundary in ("wrap", "fill"):
        # scipy path
        monkeypatch.setattr(engine, "_HAS_SCIPY", True)
        scipy_out = engine.step(g, boundary=boundary)
        # numpy fallback
        monkeypatch.setattr(engine, "_HAS_SCIPY", False)
        numpy_out = engine.step(g, boundary=boundary)
        np.testing.assert_array_equal(scipy_out, numpy_out)

    # Also stress with a random-ish soup to catch any edge-case mismatch.
    rng = np.random.default_rng(7)
    soup = (rng.random((30, 25)) < 0.35).astype(np.uint8)
    for boundary in ("wrap", "fill"):
        monkeypatch.setattr(engine, "_HAS_SCIPY", True)
        a = engine.step(soup, boundary=boundary)
        monkeypatch.setattr(engine, "_HAS_SCIPY", False)
        b = engine.step(soup, boundary=boundary)
        np.testing.assert_array_equal(a, b)


def test_mutating_rule_takes_effect_on_next_tick():
    """Regression: cached birth/survive used to ignore later .rule mutations."""
    b = LifeBoard.empty(7, 7, rule="B3/S23", boundary="fill")
    # 6 neighbors around (3,3) — Conway: stays dead, HighLife: birth.
    b.set_cells([(2, 2), (2, 3), (2, 4), (4, 2), (4, 3), (4, 4)])
    snapshot = b.grid.copy()
    b.tick()
    assert b.grid[3, 3] == 0   # Conway B3/S23

    # Reset, switch rule, tick again
    b.grid = snapshot.copy()
    b.generation = 0
    b.rule = "B36/S23"
    b.tick()
    assert b.grid[3, 3] == 1   # HighLife — 6-neighbor birth fires
