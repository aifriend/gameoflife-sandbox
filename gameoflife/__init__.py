"""Conway's Game of Life — computational sandbox.

Public API:
    LifeBoard        — fast numpy-backed grid
    step             — one generation
    simulate         — multi-step iterator
    Pattern          — dataclass returned by load_rle
    load_rle         — RLE pattern loader
    save_rle         — RLE pattern writer
    PatternLibrary   — bundled patterns (gliders, guns, methuselahs, ...)
    detect_period    — finds oscillator period
    population       — live-cell count over time
    bounding_box     — (rmin, cmin, rmax, cmax) of live cells
    center_of_mass   — centroid of live cells
    density          — live-cell fraction
    hash_grid        — translation-invariant grid hash
"""
from gameoflife.engine import LifeBoard, step, simulate
from gameoflife.patterns import (
    Pattern,
    load_rle,
    load_rle_string,
    save_rle,
    PatternLibrary,
)
from gameoflife.analysis import (
    bounding_box,
    center_of_mass,
    density,
    detect_period,
    hash_grid,
    population,
)

__version__ = "0.1.0"
__all__ = [
    "LifeBoard",
    "step",
    "simulate",
    "Pattern",
    "load_rle",
    "load_rle_string",
    "save_rle",
    "PatternLibrary",
    "detect_period",
    "population",
    "bounding_box",
    "center_of_mass",
    "density",
    "hash_grid",
]
