"""Every bundled .rle file must load, match its header and round-trip."""
import re
from pathlib import Path

import numpy as np
import pytest

from gameoflife import LifeBoard, load_rle, save_rle

PATTERN_DIR = Path(__file__).resolve().parent.parent / "patterns"
RLE_FILES = sorted(PATTERN_DIR.rglob("*.rle"))


def test_there_are_22_bundled_rle_files():
    assert len(RLE_FILES) == 22


@pytest.mark.parametrize("path", RLE_FILES,
                         ids=[p.relative_to(PATTERN_DIR).as_posix() for p in RLE_FILES])
class TestBundledRle:
    def test_loads_and_matches_header(self, path):
        pat = load_rle(path)
        header = re.search(r"x\s*=\s*(\d+)\s*,\s*y\s*=\s*(\d+)",
                           path.read_text(encoding="utf-8"))
        assert header, f"{path.name} has no x/y header"
        width, height = int(header.group(1)), int(header.group(2))
        assert pat.shape == (height, width)
        assert pat.population > 0
        assert set(np.unique(pat.grid)) <= {0, 1}

    def test_round_trips_through_save_rle(self, path, tmp_path):
        pat = load_rle(path)
        out = tmp_path / "copy.rle"
        save_rle(pat, out)
        again = load_rle(out)
        np.testing.assert_array_equal(again.grid, pat.grid)
        assert again.rule == pat.rule

    def test_can_be_simulated(self, path):
        pat = load_rle(path)
        h, w = pat.shape
        board = LifeBoard.from_pattern(pat.grid, rows=h + 40, cols=w + 40,
                                       rule=pat.rule, boundary="fill")
        board.tick(10)
        assert board.generation == 10
