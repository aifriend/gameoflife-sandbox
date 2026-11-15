# Contributing

Thanks for your interest in this project. This is a small research sandbox,
so contributions stay light: bug fixes, new patterns, new analysis tools,
and documentation improvements are all welcome.

## Development setup

```bash
git clone https://github.com/aifriend/gameoflife-sandbox.git
cd gameoflife-sandbox
./setup.sh
source .venv/bin/activate
pytest -q
```

`setup.sh` requires [`uv`](https://docs.astral.sh/uv/). If you'd rather use
a vanilla `python -m venv` setup, that works too — see `pyproject.toml` for
the dependency list. The pygame viewer and matplotlib animations are an
optional extra: `pip install -e ".[viz]"`.

## Adding a new pattern

1. Drop your `.rle` file into the appropriate `patterns/<category>/` folder.
   If no category fits, add a new subdirectory.
2. Add a header comment describing the pattern (period, displacement,
   discoverer, year if you know).
3. Verify it loads and behaves as expected:

   ```bash
   python scripts/list_patterns.py --verify
   ```

4. If the pattern has known invariants (period, displacement), add a small
   test to `tests/test_patterns.py`.

## Code style

- No formatter is enforced. Try to match the surrounding style.
- Keep modules small and focused; prefer adding to an existing module over
  creating a new one for a one-off utility.
- New public functions should have a one-line docstring; complex behavior
  gets a longer one. Don't write trailing-summary docstrings for trivial
  helpers.
- Tests are in `tests/`. New code should come with at least one test that
  would have caught the bug or proven the feature works.

## Running tests

```bash
pytest -q              # all tests
pytest tests/test_engine.py -v    # single file, verbose
```

## Pull requests

- Keep PRs small and focused — one change per PR is much easier to review.
- Reference any relevant LifeWiki pages or papers when adding analysis or
  patterns.
- CI must pass on Python 3.9, 3.10, 3.11, and 3.12.

## Reporting bugs

Open an issue with:
- What you ran
- What you expected
- What actually happened (full traceback if there's an exception)
- Your Python version and OS

For pattern-correctness bugs (e.g. "pulsar dies after 5 generations"),
include the exact RLE you loaded.
