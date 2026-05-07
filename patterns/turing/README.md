# Turing-completeness constructions

Conway's Game of Life is **Turing-complete**: any computation a Turing machine
can perform, Life can perform too — given enough cells and enough time.

## The argument, in one paragraph

A glider is a "moving signal". A glider gun produces an unbounded supply
of them. Glider streams can be reflected, gated, and combined to build
NOT, AND, OR — and from those, full digital logic. With enough wiring you
get registers, ALUs, and a finite-state controller. With unbounded grid
size you can encode an infinite Turing tape. Done.

## Concrete constructions in the wild

These are all on the public LifeWiki — the patterns themselves are huge
(some megabytes), so we don't ship them inline. Open them in
[Golly](https://golly.sourceforge.io/) for full speed.

| Construction | Year | Author | Notes |
|---|---|---|---|
| **Gosper glider gun** | 1970 | Bill Gosper | First proof Life can grow without bound |
| **Caterpillar** | 2004 | Goucher, Eppstein, et al. | Spaceship made of 11M+ cells |
| **OTCA metapixel** | 2006 | Brice Due | Self-similar — each pixel of a Life pattern is itself a Life pattern |
| **Rendell's UTM** | 2010 | Paul Rendell | First explicit universal Turing machine in Life |
| **Quest for Tetris (QFT)** | 2014 | rect, et al. | Plays Tetris — uses ~3 billion cells |
| **APGsearch / Catagolue** | ongoing | Adam Goucher | Distributed soup search; biggest pattern-discovery effort |

## Why this directory is mostly empty

Rendell's UTM RLE is ~200 KB — interesting to load and zoom around in,
but you're better off with **Golly** for that, since these constructions
run at billions of generations per second using HashLife.

If you want to integrate Golly's HashLife with this sandbox, install
[`lifelib`](https://gitlab.com/apgoucher/lifelib) (which is the engine
behind Catagolue) — it's pip-installable and gives you native HashLife
from Python.

```bash
uv pip install lifelib
```

Then in code:

```python
import lifelib
sess = lifelib.load_rules("b3s23")
lt = sess.lifetree()
pattern = lt.load("Rendell_UTM.rle")  # download separately
pattern[10**12]  # advance one trillion generations in milliseconds
```
