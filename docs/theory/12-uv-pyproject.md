# 12 — uv and pyproject.toml

## ¿Qué es?

`pyproject.toml` is the standardised configuration file for Python projects, introduced by PEP 518 (declaring build-system requirements) and extended by PEP 621 (project metadata) and PEP 735 (dependency groups). It replaces the old mix of `setup.py`, `setup.cfg`, and `requirements*.txt` files with one declarative source of truth. `uv` is a fast Python package and project manager written in Rust by Astral (the authors of `ruff`). It reads `pyproject.toml`, resolves a dependency graph, writes a lockfile (`uv.lock`), creates and manages a project-local virtual environment, and runs commands inside it. It is drop-in competitive with `pip` + `pip-tools` + `virtualenv` + `poetry` while being roughly 10–100× faster for the common operations.

## ¿Por qué lo usamos?

ProgImage needs reproducible installs across local development, CI, and Docker builds. The combination of PEP 621 metadata and a `uv.lock` committed to git gives us exactly that: the file is a complete, resolved pin of every direct and transitive dependency with hashes. Dev-only packages (pytest, httpx) are separated from runtime packages via PEP 735 dependency groups, so the Docker image can install `--no-dev` and ship a smaller runtime. uv also replaces several tools at once (resolver, installer, venv manager, Python-version selector), which keeps the toolchain small.

## ¿Cómo funciona?

### `[project]` — PEP 621 metadata

The core project table declares name, version, Python requirement, and runtime dependencies. See `pyproject.toml:1`:

```toml
[project]
name = "progimage"
version = "0.2.0"
description = "FastAPI image storage, transformation, and processing API with JWT authentication and SQLAlchemy async"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    { name = "Orbehin Sarmiento Barzaga" },
]
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic[email]>=2.6",
    "pydantic-settings>=2.2",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    ...
]
```

Each entry is a PEP 508 requirement string. Extras are expressed with brackets (`pydantic[email]` pulls `pydantic` plus the optional `email-validator` dependency). The whole table is tool-agnostic — pip, uv, poetry, hatch all understand it the same way.

### `[dependency-groups]` — PEP 735

Dependency groups are a newer standard for packages that are needed for development but should not be shipped. See `pyproject.toml:25`:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "aiosqlite>=0.19",
]
```

The group name (`dev` here, but you could add `docs`, `lint`, etc.) is arbitrary. `uv sync` installs all groups by default; `uv sync --no-dev` or `uv sync --only-group=dev` give you more surgical control. The Dockerfile uses `--no-dev` at both `uv sync` calls so the production image never ships pytest.

### `[build-system]` — PEP 518

The build backend table tells `pip install .` which tool to use for building a wheel. See `pyproject.toml:37`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

`hatchling` is the lightweight build backend from the Hatch project. It is pure Python, actively maintained, and the current community default for simple pure-Python packages. The alternatives — `setuptools`, `flit-core`, `pdm-backend`, `poetry-core` — are all interchangeable at this layer; a package maintainer picks one and nothing else changes.

### `[tool.hatch.build.targets.wheel]`

See `pyproject.toml:41`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["app"]
```

Hatchling needs to be told which top-level directory is the Python package. ProgImage ships `app` as its single importable package; alternative layouts would use a `src/` directory with `packages = ["src/app"]`.

### `[tool.pytest.ini_options]`

Tool-specific sections live under `[tool.<name>]`. pytest reads its config here instead of a separate `pytest.ini`. See `pyproject.toml:33`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Collapsing tool configs into one file is a big part of what makes `pyproject.toml` nice to live with — one file to open, one place to look.

### `uv.lock`

Running `uv sync` resolves the full transitive dependency graph against the declared constraints and writes `uv.lock` — a committed artefact pinning every package to an exact version with hashes. Subsequent `uv sync` invocations install straight from the lock without re-resolving (unless `--upgrade` or a changed `pyproject.toml` forces it). This is what makes the Docker build reproducible: the `--frozen` flag refuses to run if the lockfile and `pyproject.toml` have drifted apart, so a stale lock cannot sneak through CI.

### `uv sync` vs `uv add`

- `uv sync` — install the environment as described by `pyproject.toml` + `uv.lock`. The idempotent, reproducible operation; this is what Docker and CI call.
- `uv add fastapi` — add a dependency to `pyproject.toml`, re-resolve, update `uv.lock`, install. Local developer convenience; corresponds roughly to `poetry add` or `pip install && pip freeze`.
- `uv remove`, `uv lock`, `uv run` round out the common flow.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **pip + pip-tools + virtualenv** | The classic combo. Works, well-understood. Noticeably slower, and you juggle three tools where uv is one. |
| **Poetry** | Mature project manager with similar scope. Slower, has its own lockfile format (not PEP 751), occasionally opinionated in surprising ways. |
| **PDM** | Similar scope to Poetry/uv. Smaller user base. First-class PEP 582 (`__pypackages__`) support if you dislike venvs. |
| **Hatch (full)** | A fuller project manager built around hatchling. Environments and scripts included. Great tool; uv has eclipsed it in raw speed. |
| **Conda / Mamba** | Needed only when you have non-Python binary dependencies that pip wheels do not cover (big ML stacks, geospatial). Overkill for a web app. |

Specific friction: uv is young — the first release was late 2024. The API has stabilised but some workflows that are documented in Poetry Stack Overflow answers have no exact uv equivalent. The lockfile format itself is uv-specific (PEP 751, the standardised lockfile PEP, is still in draft), so switching to a different manager later means regenerating the lock from `pyproject.toml` constraints.

## Para profundizar

- uv docs: <https://docs.astral.sh/uv/>
- PEP 621 (project metadata): <https://peps.python.org/pep-0621/>
- PEP 735 (dependency groups): <https://peps.python.org/pep-0735/>
- Hatchling build backend: <https://hatch.pypa.io/latest/config/build/>
- PEP 518 (build-system): <https://peps.python.org/pep-0518/>
