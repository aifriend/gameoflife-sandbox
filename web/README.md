# Life Studio — web frontend

A retro-CRT, phosphor-green interactive Game of Life viewer. Companion UI
to the Python sandbox in the parent directory.

![Studio variant — pattern library / live canvas / rule builder](../docs/studio-screenshot.png)

## Run it

No build step. Any static HTTP server works because the page uses
React UMD + Babel-in-browser.

**One-liner** (recommended): from the project root,

```bash
./scripts/launch_web.sh
```

That checks port 5173, kills any stale launcher of its own, starts
`python -m http.server`, opens your default browser, and tails the
access log so you can watch requests as you click around. Ctrl+C
stops the server cleanly. Pass a port to override the default:
`./scripts/launch_web.sh 8080`.

**Manual:**

```bash
python -m http.server 8000
# then open: http://localhost:8000/web/
```

Or with `npx`:

```bash
npx serve .
# then open the printed URL + /web/
```

> Babel-in-browser is fine for a research sandbox but not production. If
> you want a real build, swap in Vite or esbuild and pre-compile
> `life-app.jsx`. The component code itself is framework-vanilla and
> portable.

## Controls

| | |
|---|---|
| `▶ Run / ❙❙ Pause` | start/stop the simulation |
| `Step ›` | advance one generation |
| `Reload` | recenter the active pattern |
| `Soup 30%` | random fill at 30% density |
| `Clear` | empty the grid |
| Speed slider | 1–120 generations per second |
| `Torus / Fixed` | toggle wrap-around vs. dead borders |
| `Glow` | per-cell phosphor glow shadow |
| `Scan` | retro CRT scanline overlay |
| **Click / drag** the canvas | toggle / paint cells |

## Layout

The Studio variant is a three-pane IDE:

- **Left** — pattern library, grouped by category (spaceship, oscillator,
  still life, methuselah, gun, exotic). Click to load.
- **Center** — live grid with `GEN` / `POP` overlay corners.
- **Right** — B/S rule builder (toggle each digit 0–8), preset rule
  buttons (Conway, HighLife, Seeds, Gnarl, …), telemetry (`GEN`, `POP`,
  `PEAK`, `PERIOD`), and a 240-gen population trace.

Period detection runs automatically by hashing the cell state every
tick — once a hash repeats, the gap is reported as `PERIOD`.

## Files

- `index.html` — entry point. Loads React + Babel from CDN, then
  `life-engine.js` + `life-app.jsx`, and renders `<LifeApp>`.
- `life-engine.js` — pure-JS Life engine (`LifeBoard` class) plus
  bundled pattern data and rule presets. Mirrors the Python project's
  `gameoflife/engine.py` semantics: B/S rules, wrap/fill boundary,
  click-to-paint.
- `life-app.jsx` — React UI. Pattern library, canvas (with glow +
  scanlines + vignette), rule builder, telemetry, population trace.

## Pattern parity with the Python lib

Every pattern bundled here is the same canonical phase as the
corresponding `.rle` in `../patterns/`. If you add a new RLE on the
Python side, you can mirror it here by hand or write a small RLE → JS
converter. The current set covers all 22 bundled Python patterns
except the Simkin gun (too big to inline) and a couple of demo
patterns.
