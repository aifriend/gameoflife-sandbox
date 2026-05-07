# GameOfLife — Computational Sandbox

[![CI](https://github.com/aifriend/gameoflife-sandbox/actions/workflows/ci.yml/badge.svg)](https://github.com/aifriend/gameoflife-sandbox/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A research environment for Conway's Game of Life: rules, patterns, period
analysis, and the path from glider collisions to Turing-completeness.

## Quick start

```bash
git clone https://github.com/aifriend/gameoflife-sandbox.git
cd gameoflife-sandbox
./setup.sh                    # creates .venv, installs deps, runs tests
source .venv/bin/activate

python scripts/list_patterns.py --verify
python scripts/analyze_pattern.py r_pentomino --max-steps 1500 --plot
python scripts/run_simulation.py --pattern gosper_glider_gun
```

See [README_SANDBOX.md](README_SANDBOX.md) for the full guided tour:
loading patterns, building gates from glider streams, running animations,
and exploring custom rules (HighLife, Seeds, etc.).

## What's inside

```
gameoflife/
    engine.py     — fast convolution-based Life engine, custom B/S rules
    patterns.py   — RLE parser/writer + bundled PatternLibrary
    analysis.py   — period detection, population trace, displacement
    visualize.py  — pygame interactive viewer + matplotlib animation
    gates.py      — gun/eater/glider primitives for logic constructions

patterns/
    spaceships/   — glider, LWSS, MWSS, HWSS
    oscillators/  — blinker, toad, beacon, pulsar, pentadecathlon
    still_lifes/  — block, beehive, loaf, boat, tub
    methuselahs/  — R-pentomino, acorn, diehard, bunnies
    guns/         — Gosper glider gun, Simkin glider gun
    exotic/       — eater 1, glider collisions
    logic/        — README on building gates from glider streams
    turing/       — README on UTM constructions, OTCA metapixel, etc.

scripts/
    run_simulation.py   — interactive pygame viewer
    analyze_pattern.py  — period detection + population plot
    animate.py          — render to GIF/MP4
    glider_demo.py      — collision and gun+eater demos
    list_patterns.py    — index of all bundled patterns

web/
    Studio — retro-CRT, phosphor-green interactive frontend (React +
    Canvas, no build step). See web/README.md.
```

## Web frontend

```bash
./scripts/launch_web.sh
```

Checks port 5173, kills any stale launcher of its own, starts
`http.server`, opens your browser, and tails the access log.
Ctrl+C stops the server cleanly. Override the port with
`./scripts/launch_web.sh 8080`.

Three-pane IDE layout: pattern library (left), live canvas with
glow + scanlines (center), B/S rule builder + telemetry + population
trace (right). Click to paint, drag to draw, run/step/clear, swap
patterns, toggle each rule digit. Full controls in [web/README.md](web/README.md).

## License

MIT.
