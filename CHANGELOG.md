# Changelog

All notable changes are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-05-07

Adds an interactive web frontend on top of the Python sandbox. No
breaking changes to the Python API.

### Added
- **`web/`** — interactive Studio UI: phosphor-green CRT aesthetic,
  three-pane IDE layout (pattern library left, live canvas center,
  rule builder + telemetry + population trace right). Pure
  client-side: React UMD + Babel-in-browser, no build step.
  - Pure-JS `LifeBoard` engine mirroring the Python semantics
    (B/S rules, wrap/fill boundary, click-to-paint).
  - 20 canonical patterns hardcoded in JS (parity with the
    `patterns/` RLE collection minus the very large Simkin gun).
  - 8 rule presets (Conway, HighLife, Seeds, Gnarl, Life w/o Death,
    34 Life, Day & Night, Diamoeba).
  - FNV-1a hash period detection.
  - Adaptive cell size: layout fits any viewport from ~620px wide
    up, with cells scaling from 2px (narrow) to 14px (wide).
- **`scripts/launch_web.sh`** — one-command port-check / serve /
  open / tail. Auto-kills its own previous instance, refuses to
  reuse a port held by anything else, opens the URL via
  `open` / `xdg-open` / `wslview`, then tails the access log
  (Ctrl+C cleanly stops the server).
- **`docs/studio.png`** — screenshot of the Studio UI.

### Fixed
- The prototype's `eater1` wasn't actually a still life — corrected
  to the canonical fishhook shape that matches `patterns/exotic/eater1.rle`.

## [0.1.0] — 2026-05-07

Initial release.

### Added
- **Engine** (`gameoflife.engine`): `LifeBoard`, `step`, `simulate`. Fast
  scipy convolution backend with a pure-numpy fallback. Custom B/S rules
  (Conway, HighLife, Seeds, Gnarl, …) and `wrap`/`fill` boundaries.
- **Pattern I/O** (`gameoflife.patterns`): RLE parser and writer with
  comment-preserving round-trip; `Pattern` dataclass; `PatternLibrary`
  for case-insensitive lookup across the bundled `patterns/` tree.
- **Analysis** (`gameoflife.analysis`): translation-aware period
  detection (still / oscillator / spaceship classification with
  displacement), population traces, bounding box, center of mass,
  density, and translation-invariant grid hashing.
- **Visualization** (`gameoflife.visualize`): pygame interactive viewer
  with vectorized rendering; matplotlib animation export to GIF/MP4;
  ASCII rendering for the CLI.
- **Gates** (`gameoflife.gates`): glider, Gosper gun, eater 1, and
  helpers for placing them in any of 4 cardinal-diagonal directions —
  primitives for building Life-based logic.
- **Pattern library**: 22 bundled patterns across spaceships,
  oscillators, still lifes, methuselahs, guns, and exotic categories.
  Every pattern is verified by the test suite.
- **Scripts**: `run_simulation.py` (interactive), `analyze_pattern.py`
  (period + population plots), `animate.py` (GIF/MP4 export),
  `glider_demo.py`, `list_patterns.py`.
- **Tests**: 53 tests covering engine correctness, RLE round-trip,
  bundled-pattern verification, and analysis edge cases.
- CI on Python 3.9–3.12 via GitHub Actions.
