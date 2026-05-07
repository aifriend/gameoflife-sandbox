"""RLE (Run-Length Encoded) pattern I/O and a bundled pattern library.

RLE is the de-facto standard format on LifeWiki and Golly. Format:

    #N Glider
    #C The smallest spaceship.
    x = 3, y = 3, rule = B3/S23
    bob$2bo$3o!

Tokens:
    'b' = dead, 'o' = alive, '$' = end-of-row, '!' = end-of-pattern
    Numeric prefix = run-length (e.g. '3o' = 'ooo', '2$' = two newlines)

This module:
    - parses RLE text into numpy arrays
    - writes arrays back to RLE
    - exposes PatternLibrary for the bundled patterns/ collection
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np


@dataclass
class Pattern:
    """A loaded pattern.

    `comments` holds the lines from `#X ...` headers with the leading `#` and
    one-letter tag stripped (e.g. `#C The smallest spaceship.` → `"The smallest
    spaceship."`). The name itself comes from `#N` and is stored separately,
    not in comments.
    """
    name: str
    grid: np.ndarray                # 2D uint8
    rule: str = "B3/S23"
    comments: List[str] = field(default_factory=list)
    source_path: Optional[Path] = None

    @property
    def shape(self):
        return self.grid.shape

    @property
    def population(self) -> int:
        return int(self.grid.sum())

    def __repr__(self):
        return (f"Pattern(name={self.name!r}, shape={self.shape}, "
                f"pop={self.population}, rule={self.rule!r})")


# --------------------------------------------------------------------- parsing


_HEADER_RE = re.compile(
    r"x\s*=\s*(\d+)\s*,\s*y\s*=\s*(\d+)(?:\s*,\s*rule\s*=\s*([^\s,]+))?",
    re.IGNORECASE,
)


def load_rle_string(text: str, name: str = "unnamed") -> Pattern:
    """Parse an RLE string into a Pattern."""
    comments = []
    header_match = None
    body_lines = []

    for raw in text.splitlines():
        line = raw.rstrip("\r\n")
        if not line.strip():
            continue
        if line.startswith("#"):
            # Capture name separately from the comment list — otherwise a
            # round-trip via save_rle emits `#N` twice.
            if line.startswith("#N "):
                name = line[3:].strip() or name
                continue
            # Strip leading `#` and the optional tag letter + space, leaving
            # just the prose. Tags we recognize: C/c (comment), O (origin),
            # P/R/r (offset/rule). Unknown tags fall back to the raw text
            # after `#`.
            stripped = line[1:].lstrip()
            if len(stripped) >= 2 and stripped[0] in "COPRrc" and stripped[1] == " ":
                comments.append(stripped[2:])
            else:
                comments.append(stripped)
            continue
        if header_match is None:
            m = _HEADER_RE.search(line)
            if m:
                header_match = m
                continue
        body_lines.append(line)

    if header_match is None:
        raise ValueError("RLE: missing header line 'x = ..., y = ..., rule = ...'")

    width = int(header_match.group(1))
    height = int(header_match.group(2))
    rule = header_match.group(3) or "B3/S23"

    body = "".join(body_lines).split("!", 1)[0]

    grid = np.zeros((height, width), dtype=np.uint8)
    row = 0
    col = 0
    num_str = ""

    for ch in body:
        if ch.isdigit():
            num_str += ch
            continue
        run = int(num_str) if num_str else 1
        num_str = ""
        if ch == "b":
            col += run
        elif ch == "o":
            for _ in range(run):
                if row < height and col < width:
                    grid[row, col] = 1
                col += 1
        elif ch == "$":
            row += run
            col = 0
        elif ch in (" ", "\t", "\n", "\r"):
            continue
        else:
            # Tolerant: ignore unknown chars (some files have weird state IDs)
            continue

    return Pattern(name=name, grid=grid, rule=rule, comments=comments)


def load_rle(path: str | Path) -> Pattern:
    """Load an RLE file."""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    pat = load_rle_string(text, name=p.stem)
    pat.source_path = p
    return pat


def save_rle(pattern: Pattern | np.ndarray, path: str | Path,
             name: Optional[str] = None,
             rule: str = "B3/S23",
             comments: Optional[list] = None) -> None:
    """Write a Pattern or ndarray to an RLE file."""
    if isinstance(pattern, Pattern):
        grid = pattern.grid
        name = name or pattern.name
        rule = pattern.rule
        comments = comments or pattern.comments
    else:
        grid = np.asarray(pattern, dtype=np.uint8)
        name = name or "pattern"
        comments = comments or []

    h, w = grid.shape
    lines = []
    if name:
        lines.append(f"#N {name}")
    for c in comments:
        lines.append(f"#C {c}")
    lines.append(f"x = {w}, y = {h}, rule = {rule}")

    body = []
    for r in range(h):
        row_chars = ["o" if grid[r, c] else "b" for c in range(w)]
        # RLE: trailing dead cells in a row can be dropped
        # Compress runs
        compressed = _compress_run(row_chars)
        body.append(compressed)
    rle_body = "$".join(body) + "!"

    # Wrap at 70 chars
    wrapped = []
    while rle_body:
        wrapped.append(rle_body[:70])
        rle_body = rle_body[70:]
    lines.extend(wrapped)

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _compress_run(chars: list) -> str:
    """Compress ['o', 'o', 'b'] -> '2ob'. Drops trailing 'b' runs."""
    # Drop trailing dead
    while chars and chars[-1] == "b":
        chars.pop()
    if not chars:
        return ""
    out = []
    prev = chars[0]
    count = 1
    for c in chars[1:]:
        if c == prev:
            count += 1
        else:
            out.append(f"{count if count > 1 else ''}{prev}")
            prev = c
            count = 1
    out.append(f"{count if count > 1 else ''}{prev}")
    return "".join(out)


# --------------------------------------------------------------------- library


class PatternLibrary:
    """Loads bundled patterns from the patterns/ directory.

    Lookup by name (case-insensitive) or by category/name.

    >>> lib = PatternLibrary()
    >>> lib.list_categories()
    ['exotic', 'guns', 'logic', 'methuselahs', 'oscillators', 'spaceships', 'still_lifes', 'turing']
    >>> g = lib.get('glider')
    >>> g.shape
    (3, 3)
    """

    def __init__(self, root: Optional[Path] = None):
        if root is None:
            # Default: patterns/ directory next to the package root
            root = Path(__file__).resolve().parent.parent / "patterns"
        self.root = Path(root)

    def list_categories(self) -> list:
        if not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir()
                      if p.is_dir() and not p.name.startswith("."))

    def list_patterns(self, category: Optional[str] = None) -> list:
        out = []
        if category:
            d = self.root / category
            if d.exists():
                out.extend(sorted(d.glob("*.rle")))
        else:
            for cat in self.list_categories():
                out.extend(sorted((self.root / cat).glob("*.rle")))
        return [p.relative_to(self.root) for p in out]

    def find(self, name: str) -> Optional[Path]:
        """Case-insensitive search across all categories."""
        target = name.lower().replace(" ", "_").replace("-", "_")
        if target.endswith(".rle"):
            target = target[:-4]
        for cat in self.list_categories():
            for f in (self.root / cat).glob("*.rle"):
                stem = f.stem.lower().replace(" ", "_").replace("-", "_")
                if stem == target:
                    return f
        return None

    def get(self, name: str) -> Pattern:
        """Load a pattern by name. Raises KeyError if not found."""
        path = self.find(name)
        if path is None:
            available = [str(p) for p in self.list_patterns()]
            raise KeyError(f"Pattern {name!r} not found. Available: "
                           f"{available[:20]}{'...' if len(available) > 20 else ''}")
        return load_rle(path)

    def __contains__(self, name: str) -> bool:
        return self.find(name) is not None

    def __repr__(self) -> str:
        cats = self.list_categories()
        n = sum(len(self.list_patterns(c)) for c in cats)
        return f"PatternLibrary(root={self.root}, categories={len(cats)}, patterns={n})"
