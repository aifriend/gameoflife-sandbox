"""RLE round-trip + bundled pattern correctness."""
import numpy as np
import pytest

from gameoflife import LifeBoard, Pattern, PatternLibrary, load_rle_string, save_rle
from gameoflife.analysis import detect_period
from gameoflife.patterns import load_rle


def test_rle_glider_parses():
    rle = """#N Glider
x = 3, y = 3, rule = B3/S23
bob$2bo$3o!
"""
    p = load_rle_string(rle)
    assert p.shape == (3, 3)
    assert p.population == 5
    expected = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ], dtype=np.uint8)
    np.testing.assert_array_equal(p.grid, expected)


def test_rle_runlength_compression():
    rle = """x = 4, y = 1, rule = B3/S23
4o!
"""
    p = load_rle_string(rle)
    np.testing.assert_array_equal(p.grid, np.ones((1, 4), dtype=np.uint8))


def test_rle_blank_rows():
    rle = """x = 3, y = 4, rule = B3/S23
3o$$$3o!
"""
    p = load_rle_string(rle)
    assert p.shape == (4, 3)
    expected = np.array([[1, 1, 1], [0, 0, 0], [0, 0, 0], [1, 1, 1]],
                        dtype=np.uint8)
    np.testing.assert_array_equal(p.grid, expected)


def test_rle_save_load_roundtrip(tmp_path):
    grid = np.array([
        [1, 0, 1, 0],
        [0, 1, 1, 1],
        [1, 0, 0, 0],
    ], dtype=np.uint8)
    out = tmp_path / "test.rle"
    save_rle(grid, out, name="rt")
    loaded = load_rle_string(out.read_text())
    np.testing.assert_array_equal(loaded.grid, grid)


def test_rle_roundtrip_preserves_name_without_duplicating(tmp_path):
    """Regression: load → save → load used to emit `#N` twice (once from the
    name kwarg, once from the comment list which retained the parsed #N line)."""
    pat = PatternLibrary().get("glider")
    out = tmp_path / "glider_rt.rle"
    save_rle(pat, out)
    text = out.read_text()
    # Exactly one #N line
    assert text.count("\n#N ") + (1 if text.startswith("#N ") else 0) == 1
    # Round-trip preserves grid + name
    reloaded = load_rle_string(text)
    np.testing.assert_array_equal(reloaded.grid, pat.grid)
    assert reloaded.name == pat.name


def test_rle_comment_strips_tag_letter(tmp_path):
    """Loading an RLE with `#C foo` should give comments=['foo'], not ['C foo']."""
    rle = "#N Test\n#C First comment\n#C Second comment\nx = 2, y = 1, rule = B3/S23\n2o!\n"
    pat = load_rle_string(rle)
    assert pat.comments == ["First comment", "Second comment"]
    # And re-saving preserves them without prefix duplication
    out = tmp_path / "rt.rle"
    save_rle(pat, out)
    reloaded = load_rle_string(out.read_text())
    assert reloaded.comments == ["First comment", "Second comment"]


def test_save_rle_with_plain_ndarray(tmp_path):
    """save_rle accepts an ndarray directly (not just a Pattern)."""
    grid = np.array([
        [1, 1, 0],
        [0, 1, 0],
    ], dtype=np.uint8)
    out = tmp_path / "raw.rle"
    save_rle(grid, out, name="raw", comments=["from ndarray"])
    text = out.read_text()
    assert "#N raw" in text
    assert "#C from ndarray" in text
    reloaded = load_rle_string(text)
    np.testing.assert_array_equal(reloaded.grid, grid)
    assert reloaded.name == "raw"


def test_load_rle_missing_header_raises():
    """A body without an `x = ..., y = ...` header is malformed."""
    with pytest.raises(ValueError, match="header"):
        load_rle_string("bo$3o!\n")


def test_pattern_library_loads():
    lib = PatternLibrary()
    cats = lib.list_categories()
    assert "spaceships" in cats
    assert "oscillators" in cats
    assert "guns" in cats


def test_pattern_glider_period_4():
    lib = PatternLibrary()
    pat = lib.get("glider")
    assert pat.population == 5
    board = LifeBoard.from_pattern(pat.grid, rows=30, cols=30,
                                   boundary="fill")
    res = detect_period(board, max_steps=20)
    assert res.period == 4
    assert res.is_spaceship
    # Glider moves (1,1) per period (SE)
    assert res.displacement == (1, 1)


def test_from_pattern_inherits_rule_from_pattern_object():
    """Passing a Pattern (not just an ndarray) should auto-set rule."""
    rle = "x = 3, y = 1, rule = B36/S23\n3o!\n"
    pat = load_rle_string(rle)
    board = LifeBoard.from_pattern(pat, rows=10, cols=10, boundary="fill")
    assert board.rule == "B36/S23"


def test_from_pattern_kwarg_overrides_pattern_rule():
    rle = "x = 3, y = 1, rule = B36/S23\n3o!\n"
    pat = load_rle_string(rle)
    board = LifeBoard.from_pattern(pat, rows=10, cols=10,
                                   rule="B3/S23", boundary="fill")
    assert board.rule == "B3/S23"


def test_pattern_blinker_period_2():
    lib = PatternLibrary()
    pat = lib.get("blinker")
    board = LifeBoard.from_pattern(pat.grid, rows=10, cols=10,
                                   boundary="fill")
    res = detect_period(board, max_steps=10)
    assert res.period == 2
    assert res.is_oscillator


def test_pattern_block_still_life():
    lib = PatternLibrary()
    pat = lib.get("block")
    board = LifeBoard.from_pattern(pat.grid, rows=10, cols=10,
                                   boundary="fill")
    res = detect_period(board, max_steps=10)
    assert res.period == 1
    assert res.is_still_life


def test_pattern_pulsar_period_3():
    lib = PatternLibrary()
    pat = lib.get("pulsar")
    board = LifeBoard.from_pattern(pat.grid, rows=30, cols=30,
                                   boundary="fill")
    res = detect_period(board, max_steps=10)
    assert res.period == 3
    assert res.is_oscillator


def test_pattern_pentadecathlon_period_15():
    lib = PatternLibrary()
    pat = lib.get("pentadecathlon")
    board = LifeBoard.from_pattern(pat.grid, rows=30, cols=30,
                                   boundary="fill")
    res = detect_period(board, max_steps=30)
    assert res.period == 15


def test_pattern_lwss_speed_c_over_2():
    lib = PatternLibrary()
    pat = lib.get("lwss")
    board = LifeBoard.from_pattern(pat.grid, rows=20, cols=40,
                                   boundary="fill")
    res = detect_period(board, max_steps=20)
    assert res.period == 4
    assert res.is_spaceship
    # Orthogonal motion of (0, 2) — 2 cells in 4 generations = c/2
    assert abs(res.displacement[0]) + abs(res.displacement[1]) == 2


def test_pattern_diehard_vanishes():
    """Diehard methuselah is supposed to leave NO live cells after 130 gens."""
    lib = PatternLibrary()
    pat = lib.get("diehard")
    board = LifeBoard.from_pattern(pat.grid, rows=80, cols=80,
                                   boundary="fill")
    board.tick(130)
    assert board.population == 0


def test_pattern_r_pentomino_long_running():
    """R-pentomino should still be active at generation 100 and quiet by 1200."""
    lib = PatternLibrary()
    pat = lib.get("r_pentomino")
    board = LifeBoard.from_pattern(pat.grid, rows=200, cols=200,
                                   boundary="fill")
    board.tick(100)
    assert board.population > 0
    # Final R-pentomino population is 116 — but on finite "fill" board, gliders
    # eventually leave. Just check it's not still chaotic at 1200.
    board.tick(1100)   # total 1200
    pop_at_1200 = board.population
    board.tick(50)
    assert abs(board.population - pop_at_1200) < pop_at_1200 * 0.5
