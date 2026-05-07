#!/usr/bin/env bash
# Setup script for the GameOfLife sandbox.
# Creates .venv via uv, installs dependencies, runs a smoke test.

set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv is not installed. Install it from https://docs.astral.sh/uv/"
    exit 1
fi

PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

echo "[1/4] Creating venv at .venv (Python ${PYTHON_VERSION})..."
uv venv --python "${PYTHON_VERSION}" .venv

echo "[2/4] Installing dependencies..."
VIRTUAL_ENV=.venv uv pip install -e ".[dev]"

echo "[3/4] Running smoke test..."
PYTHONPATH=. .venv/bin/python -c "
from gameoflife import LifeBoard, PatternLibrary
from gameoflife.analysis import detect_period

lib = PatternLibrary()
print(f'Library: {lib}')
glider = lib.get('glider')
print(f'Loaded: {glider!r}')
board = LifeBoard.from_pattern(glider.grid, rows=20, cols=20, boundary='fill')
res = detect_period(board, max_steps=10)
print(f'Glider period detection: {res}')
assert res.period == 4, 'Glider should have period 4'
print('SMOKE TEST PASSED')
"

echo "[4/4] Running test suite..."
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q

echo ""
echo "================================================================"
echo "  Setup complete. Activate with: source .venv/bin/activate"
echo ""
echo "  Try:"
echo "    python scripts/list_patterns.py --verify"
echo "    python scripts/analyze_pattern.py r_pentomino --max-steps 1500"
echo "    python scripts/run_simulation.py --pattern gosper_glider_gun"
echo "================================================================"
