# Logic gates from glider collisions

This folder is intentionally minimal — most published gate constructions
on LifeWiki are large (hundreds to thousands of cells), and they only
make sense once you fully understand the glider-stream encoding.

## Bit encoding

A bit travels as a glider stream from a period-30 Gosper gun:
- `1` = glider present in this period-30 window
- `0` = glider absent (suppressed by an upstream gate or never produced)

So a "wire" in Life is an axis along which gliders travel; a "buffer"
delay is just distance along that wire.

## Primitives

| Construction | Where it lives | Function |
|---|---|---|
| Glider gun | `../guns/gosper_glider_gun.rle` | Source — emits a glider every 30 gens |
| Eater 1 | `../exotic/eater1.rle` | Sink — absorbs gliders without leaving debris |
| Glider collision | `../exotic/glider_collision_demo.rle` | Two gliders annihilating — basis of NOT |

## Building gates

- **NOT(A)**: A clock stream of gliders is fed in alongside the input
  stream A. Where A has a glider, it collides with the clock and both
  die. Where A is absent, the clock glider survives. The clock-survivors
  are the inverted output.

- **AND(A, B)**: Use a NOT gate followed by a "merge": A and B steer a
  shared clock stream — both must agree to let the clock through.

- **OR(A, B)**: Two streams merged via a perpendicular destructor that
  only triggers if both inputs are absent.

These are constructive — you can lay them out in `gameoflife/gates.py`
using `place_gun`, `place_eater`, `place_glider`. The full reference
is Paul Rendell's gate library:
https://www.rendell-attic.org/gol/tm.htm

## Want a working gate today?

Build it interactively. Open `scripts/run_simulation.py`, place a
glider gun and an eater with the helper functions in `gameoflife.gates`,
hit space to pause, drop a glider in by clicking, and watch the
collision unfold step-by-step (`n` for single step in the pygame viewer).
