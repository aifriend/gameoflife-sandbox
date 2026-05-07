# GameOfLife Research Sandbox — guided tour

A complete, ready-to-run environment for experimenting with Conway's
Game of Life. Engine, pattern library, analysis tools, and a path from
glider physics to **proven Turing-completeness**.

> **Why "computational" sandbox?** Life isn't just a pretty cellular
> automaton. It's been *proven* universal: Paul Rendell built an
> explicit universal Turing machine in Life cells (2010); the
> "Quest for Tetris" project plays Tetris in Life (2014); Brice Due's
> OTCA metapixel makes Life *self-similar* — every "pixel" of a Life
> pattern is itself a Life pattern. This sandbox gives you the tools to
> explore that universe.

---

## 1. Setup (one command)

```bash
./setup.sh
```

What it does:
- Creates `.venv/` via `uv` (Python 3.11 by default — override with `PYTHON_VERSION=3.10 ./setup.sh`)
- Installs `numpy`, `scipy`, `matplotlib`, `pygame`, `pytest`
- Installs the `gameoflife` package in editable mode
- Runs a glider smoke test
- Runs the full `pytest` suite (~30 tests)

After it finishes:
```bash
source .venv/bin/activate
```

### Manual setup (if you skip setup.sh)

```bash
uv venv --python 3.11 .venv
VIRTUAL_ENV=.venv uv pip install -e ".[dev]"
PYTHONPATH=. .venv/bin/python -m pytest tests/ -v
```

---

## 2. Try a pattern

### Browse the library
```bash
python scripts/list_patterns.py
```

### Run period analysis
```bash
python scripts/analyze_pattern.py glider
# Loaded: Pattern(name='glider', shape=(3,3), pop=5, rule='B3/S23')
# PeriodResult(period=4, displacement=(1,1), kind=spaceship, final_population=5)

python scripts/analyze_pattern.py pulsar
# period=3, kind=oscillator

python scripts/analyze_pattern.py r_pentomino --max-steps 1500
# period=>1500 (R-pentomino is methuselah; doesn't return inside 1500 gens)
```

### Plot population over time
```bash
python scripts/analyze_pattern.py r_pentomino --max-steps 1500 --plot
# Saves /tmp/pop.png — classic methuselah curve, peaks then settles
```

### Interactive viewer
```bash
python scripts/run_simulation.py --pattern gosper_glider_gun --rows 60 --cols 100
```

Controls:
- `SPACE` pause / resume
- `LEFT-CLICK` toggle a cell (when paused) — edit live
- `n` single step
- `r` randomize
- `c` clear
- `+`/`-` faster / slower
- `q` / `ESC` quit

### Render a GIF or MP4
```bash
python scripts/animate.py glider --steps 40 --out glider.gif
python scripts/animate.py r_pentomino --steps 200 --out r_pent.mp4
python scripts/animate.py gosper_glider_gun --steps 120 --out gun.gif --fps 30
```

(MP4 requires `ffmpeg` on your PATH; GIF works out of the box via Pillow.)

---

## 3. Custom rules

The engine is rule-agnostic. Pass any B/S notation:

```bash
python scripts/run_simulation.py --random 0.4 --rule B36/S23   # HighLife (replicator)
python scripts/run_simulation.py --random 0.5 --rule B2/S      # Seeds (no survival)
python scripts/run_simulation.py --random 0.5 --rule B1/S1     # Gnarl
python scripts/run_simulation.py --random 0.4 --rule B3/S012345678  # "Life without Death"
```

In code:
```python
from gameoflife import LifeBoard
b = LifeBoard.random(100, 100, density=0.4, rule="B36/S23", seed=42)
b.tick(500)
```

---

## 4. Building computation from gliders

The path from cellular automaton → Turing machine, in three steps:

### Step 1 — gliders are signals

A glider is the smallest spaceship: 5 cells, period 4, moves diagonally
at speed c/4. Inspect it:

```bash
python scripts/analyze_pattern.py glider --ascii
```

### Step 2 — guns are signal sources

A Gosper glider gun fires one glider every 30 generations. Open it:

```bash
python scripts/run_simulation.py --pattern gosper_glider_gun --rows 50 --cols 80
```

This was Bill Gosper's $50 prize-winning discovery in 1970 — the first
proof Life supports unbounded population growth.

### Step 3 — collisions are gates

```python
from gameoflife import LifeBoard
from gameoflife.gates import place_gun, place_eater, place_glider
from gameoflife.visualize import run_pygame

# A gun firing into an eater = clean producer/consumer
b = LifeBoard.empty(60, 80, boundary="fill")
place_gun(b, row=5, col=5, direction="SE")
place_eater(b, row=35, col=50, direction="NW")
run_pygame(b)
```

Or use the pre-built demos:
```bash
python scripts/glider_demo.py collision --pygame   # head-on collision (debris)
python scripts/glider_demo.py gun --pygame         # gun + eater (steady stream)
```

From there:
- **NOT gate** = clock stream destroyed by data stream where data is `1`
- **AND gate** = data stream survives only if both inputs absent its destructor
- **Memory cell** = closed loop of glider streams between gates
- **Turing-complete machine** = enough of all of the above

The classic reference is [Paul Rendell's UTM](https://www.rendell-attic.org/gol/tm.htm).
For the modern monumental construction, see
[Quest for Tetris](https://github.com/QuestForTetris/QFT).

See [`patterns/logic/README.md`](patterns/logic/README.md) for the gate-design
walkthrough and [`patterns/turing/README.md`](patterns/turing/README.md) for
the universal-construction landscape.

---

## 5. Programmatic API

```python
from gameoflife import LifeBoard, PatternLibrary
from gameoflife.analysis import detect_period, population

# Build a board
b = LifeBoard.random(50, 50, density=0.3, seed=42, boundary="wrap")

# Step it forward
b.tick(100)
print(b.population, b.generation)

# Load a known pattern
lib = PatternLibrary()
gun = lib.get("gosper_glider_gun")
b = LifeBoard.from_pattern(gun.grid, rows=80, cols=120, boundary="fill")

# Analyze
res = detect_period(b.copy(), max_steps=500)
print(res)   # period=30 (Gosper gun) — but only on infinite grid; on
             # finite grids the gliders escape and the gun resets

# Population trace
pop = population(b.copy(), steps=500)   # numpy array of 501 counts
```

### Saving custom patterns

```python
import numpy as np
from gameoflife.patterns import save_rle

my_pattern = np.array([
    [0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [1, 1, 1, 0, 0],
], dtype=np.uint8)
save_rle(my_pattern, "my_glider.rle", name="my_glider", comments=["Test"])
```

---

## 6. Performance & scaling

The default engine uses `scipy.signal.convolve2d` — fast enough for
**~1000x1000 grids at 50–100 generations/sec** on an M1 Mac.

For *much* bigger experiments (Rendell's UTM has tens of thousands of
cells and runs for billions of generations), install `lifelib`:

```bash
uv pip install -e ".[fast]"
```

`lifelib` is the HashLife engine behind [Catagolue](https://catagolue.hatsya.com/),
Adam Goucher's distributed soup-search project. It cancels out
**exponential** chunks of repeated work — patterns can be advanced
1,000,000,000+ generations in milliseconds.

This sandbox doesn't wrap `lifelib` directly (its API is well-documented
upstream), but the patterns/ collection here is interoperable: every RLE
file loads natively in lifelib and Golly.

---

## 7. Where to go next

Research questions you can attack from this sandbox:

1. **Density experiments**: how does the survival rate of a random soup
   depend on initial density? Densities far from ~30–40% die quickly
   (too sparse → starvation, too dense → over-population), and the
   "interesting" range is fairly narrow. Sweep `density` and plot
   long-term population.
2. **Methuselah classification**: brute-force-search small patterns
   (≤ 20 cells) for ones with the longest stabilization time.
3. **Spaceship taxonomy**: pull every spaceship from
   [Catagolue](https://catagolue.hatsya.com/) and classify by
   period × displacement. Plot speed (cells/gen).
4. **Custom rules**: scan B/S rule space and detect which rules support
   gliders. Wolfram's class-3 / class-4 boundary lives in here.
5. **Build a NAND gate** end-to-end from gun + eater + reflectors.
   This is the real "from cells to computer" exercise.

Have fun.
