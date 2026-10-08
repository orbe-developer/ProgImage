# 14 — pytest coverage (pytest-cov)

## ¿Qué es?

**Code coverage** is a measurement of what fraction of your source code is actually executed when the test suite runs. The usual unit of measure is a **line** or **statement**: if `app/auth/router.py` has 100 executable statements and the tests exercise 85 of them, the file has 85 % statement coverage. A refined form, **branch coverage**, also looks at every `if`/`else`, `try`/`except`, and `and`/`or` short-circuit, so a line that is reached but whose "false" branch is never taken counts as only partially covered.

In Python the reference tool is **`coverage.py`** (<https://coverage.readthedocs.io>), and **`pytest-cov`** is a thin plugin that wires it into pytest so you can collect coverage simply by passing `--cov=app` to `pytest`. ProgImage uses the pytest-cov integration; the raw data file (`.coverage`) is dropped in the project root, and reports can be rendered as text, HTML, or XML (for CI).

## ¿Por qué lo usamos?

Three concrete reasons for ProgImage:

1. **Spot untested paths before an interviewer does.** `app/routers/image_filtering.py` has 12 near-identical endpoints but only `test_filter_blur_happy_path` in the test suite. A coverage report with `--cov-report=term-missing` lists the exact line numbers of the other 11 filter functions, so if a reviewer asks "which endpoints have test coverage?" there is a precise answer, not a guess.
2. **Guard against regressions in CI.** `--cov-fail-under=90` makes pytest exit non-zero if coverage drops below a threshold. In a CI pipeline this prevents a PR from merging if someone deletes a test by accident or adds a new feature without tests.
3. **Guide refactor confidence.** When you want to collapse 12 filter functions into one factory (the Tier 3 refactor we deferred in Phase 7), you look at the coverage of the touched code first — if the lines about to change are 100 % covered, you refactor with a safety net; if they are at 20 %, you write tests before refactoring.

## ¿Cómo funciona?

### The three-step mechanism

1. `pytest-cov` tells `coverage.py` to install a Python trace function (via `sys.settrace`) before any test runs.
2. During the run, every executed line in the target package (`--cov=app`) is recorded in an in-memory map, then flushed to `.coverage` at the end.
3. The reporter reads `.coverage` and compares the executed set against the full set of executable lines (ignoring blank lines, imports in some configs, and docstrings) to compute the percentages.

### Enabling it in ProgImage

Added to `pyproject.toml` as a dev dep:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "aiosqlite>=0.19",
    "pytest-cov>=7.1.0",
]
```

Run with:

```bash
uv run pytest --cov=app --cov-report=term-missing
```

Example output (abridged — numbers vary slightly as the project evolves):

```
Name                                 Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
app/auth/router.py                      35      5    85%   58, 90
app/routers/image_filtering.py          54     12    78%   48, 60, …
app/schemas.py                          16      0   100%
-----------------------------------------------------------------
TOTAL                                  359     25    93%
```

- **Stmts** — number of executable statements in the file.
- **Miss** — statements never executed by any test.
- **Cover** — `(Stmts − Miss) / Stmts`.
- **Missing** — the exact line numbers of the uncovered statements. In the example, `app/auth/router.py:58` is probably one of the error branches in `/register` or `/login` that no test exercises.

### HTML output for exploration

```bash
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

`htmlcov/` is a browsable site: click any file to see the source with green lines (covered) and red lines (uncovered), hover over branches to see which arms are taken. This is the fastest way to find "oh, no test ever hits the duplicate-email branch".

### Branch coverage

Statement coverage misses cases where both arms of an `if` need testing. Enable branch coverage with:

```bash
uv run pytest --cov=app --cov-report=term-missing --cov-branch
```

The missing-lines column now also lists uncovered branches, e.g. `58->61` meaning the edge from line 58 to line 61 was never taken.

### Related config knobs

Live in `pyproject.toml` under `[tool.coverage.run]` and `[tool.coverage.report]` (not currently set in ProgImage; defaults apply). Common overrides:

```toml
[tool.coverage.run]
branch = true                          # always use branch coverage
omit = ["app/alembic/*", "tests/*"]    # exclude from measurement

[tool.coverage.report]
show_missing = true
skip_covered = true                    # hide 100% files to focus on gaps
fail_under = 90                        # fail the run if coverage drops
```

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **No coverage at all** | Zero overhead, but you cannot answer "what is tested?" quantitatively. Suitable for a tiny script, not for anything you plan to maintain. |
| **Statement coverage only** | Fast, easy to understand. Misses conditional-branch gaps (an `if` where only the `True` side is tested shows 100 % statement coverage). |
| **Branch coverage** (`--cov-branch`) | Catches the above. Slower (not much) and reports can get noisy, but a much more honest signal. Recommended for critical paths. |
| **Mutation testing** (`mutmut`, `cosmic-ray`) | Instead of counting executed lines, mutates the source (e.g. flips `>` to `<`) and checks whether tests catch each mutation. Finds "tests that run the code but do not actually verify anything". Expensive (minutes to hours) but a far stronger signal than line coverage. |
| **Property-based testing** (`hypothesis`) | Not a replacement for coverage, but complementary — generates many inputs so edge cases that line-coverage would never show up are discovered. Useful for Pydantic schemas (see [`02-pydantic.md`](02-pydantic.md)) and anything with numeric constraints. |

Specific friction with coverage.py / pytest-cov:

- **Coverage is not test quality.** A test that calls an endpoint but asserts nothing counts the same as a test that asserts the full response shape. 100 % coverage with weak asserts is worse than 70 % with strong asserts. (See [`08-pytest-asyncio.md`](08-pytest-asyncio.md) for the pytest-side of what good assertions look like.)
- **Goodhart's law.** When a target becomes a measure (`--cov-fail-under=95`), developers optimise for the measure. People write tests that only touch code to pump the number up without verifying behaviour. Prefer a modest threshold (e.g. 80 %) that lets the team invest the remaining energy in test quality.
- **Async + process-based parallelism** (`pytest-xdist`) requires combining per-worker `.coverage.*` files — set `parallel = true` under `[tool.coverage.run]` and append `--cov-report=term-missing` with `coverage combine` in CI.
- **Importing a file counts as covering its top-level statements.** A file that is imported but whose functions are never called will still show high coverage because the import time ran all the `def`, `class`, decorator calls. The "cover" of a bare `def foo(): pass` is the `def` line, not the body.

## Para profundizar

- `coverage.py` official docs: <https://coverage.readthedocs.io>
- `pytest-cov` docs: <https://pytest-cov.readthedocs.io>
- "Coverage is not a measure of test quality" — Ned Batchelder (coverage.py author): <https://nedbatchelder.com/blog/200710/flaws_in_coverage_measurement.html>
- Mutation testing in Python with `mutmut`: <https://mutmut.readthedocs.io>
- "Goodhart's law" primer applied to engineering metrics: <https://en.wikipedia.org/wiki/Goodhart's_law>
