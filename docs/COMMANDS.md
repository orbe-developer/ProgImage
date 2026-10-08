# Commands reference

Quick cheatsheet for every command you need to work with ProgImage day-to-day. Grouped by area; scannable, not tutorial. For the end-to-end runbook see [`MANUAL_TESTING.md`](MANUAL_TESTING.md); for operational background on each piece see the theory notes on the `study-notes` branch.

---

## Docker Compose

### Lifecycle

| Command | What it does |
|---|---|
| `docker compose up -d --build` | Build images (if changed) + start all services in background |
| `docker compose up -d db` | Start **only** Postgres (useful when running the app via `uv` locally) |
| `docker compose up -d app` | Start the app container (requires `db` healthy) |
| `docker compose stop app` | Stop the app container but keep DB running |
| `docker compose restart app` | Restart just the app (picks up code changes without rebuild) |
| `docker compose down` | Stop + remove containers, **keep** the data volume |
| `docker compose down -v` | Stop + remove containers **AND** the `progimage_pgdata` volume (wipes DB) |

### Inspection

| Command | What it does |
|---|---|
| `docker compose ps` | Containers status (healthy/unhealthy, ports) |
| `docker compose logs app` | All app logs since start |
| `docker compose logs -f app` | Follow logs live (Ctrl+C to exit) |
| `docker compose logs app --since 5m` | Only recent logs |
| `docker compose exec app /bin/bash` | Open a shell inside the app container |
| `docker ps -a --filter name=progimage` | List any lingering containers from previous runs |
| `docker volume ls --filter name=progimage` | List data volumes |

### One-shot runs

| Command | What it does |
|---|---|
| `docker compose run --rm migrate` | Run `alembic upgrade head` in a one-off container (needs `migrate` profile; defined in `docker-compose.yml`) |
| `docker compose run --rm app python -c "from app.config import settings; print(settings.database_url)"` | Run an arbitrary Python command inside a fresh container |

---

## Alembic (database migrations)

### Day-to-day

| Command | What it does |
|---|---|
| `uv run alembic current` | Which migration is currently applied in the DB |
| `uv run alembic history` | Full list of migrations oldest → newest |
| `uv run alembic heads` | Latest migration ID (what `upgrade head` would apply to) |
| `uv run alembic upgrade head` | Apply all pending migrations |
| `uv run alembic upgrade +1` | Apply the next migration only |
| `uv run alembic downgrade -1` | Roll back one migration |
| `uv run alembic downgrade base` | Roll back everything (empty schema) |

### Creating new migrations

| Command | What it does |
|---|---|
| `uv run alembic revision -m "add email index"` | Create an **empty** migration skeleton — fill in `upgrade()`/`downgrade()` by hand |
| `uv run alembic revision --autogenerate -m "add email index"` | Diff the current DB schema against `Base.metadata` and generate `op.*` calls for the delta. **Review the generated file** before applying — autogenerate can miss server defaults, type changes, and constraint renames |
| `uv run alembic stamp head` | Mark the DB as "already at head" without actually running the migration (useful after creating tables manually, e.g. via `lifespan.create_all`) |

### Via Docker

Same commands but prefix with `docker compose run --rm migrate` to run them against the container's Postgres:

```bash
docker compose run --rm migrate alembic current
docker compose run --rm migrate alembic history
docker compose run --rm migrate alembic downgrade -1
```

### Autogenerate workflow (after changing a model)

1. Edit `app/models/*.py` (add a column, change a type, etc.)
2. `uv run alembic revision --autogenerate -m "add bio to users"`
3. Open the generated file in `alembic/versions/<hash>_add_bio_to_users.py`
4. Review and tweak the `op.*` calls (autogenerate is conservative — may add drops you did not intend if you removed a column)
5. `uv run alembic upgrade head`

---

## PostgreSQL inspection

Run via `docker compose exec db psql -U postgres -d progimage`:

| Inside psql | What it does |
|---|---|
| `\l` | List all databases |
| `\c progimage` | Connect to a specific database |
| `\dt` | List tables in current schema |
| `\d users` | Describe the `users` table (columns, types, indexes, FKs) |
| `\di` | List indexes |
| `\du` | List roles/users |
| `\dn` | List schemas |
| `SELECT * FROM users LIMIT 5;` | Query data |
| `\q` | Quit |

### One-liners from outside

```bash
# List tables
docker compose exec db psql -U postgres -d progimage -c "\dt"

# Row counts
docker compose exec db psql -U postgres -d progimage -c "SELECT COUNT(*) FROM users;"

# What migrations has Alembic applied?
docker compose exec db psql -U postgres -d progimage -c "SELECT * FROM alembic_version;"

# Reset everything
docker compose exec db psql -U postgres -d progimage -c "DROP TABLE IF EXISTS alembic_version, images, users CASCADE;"
```

---

## pytest

### Running tests

| Command | What it does |
|---|---|
| `uv run pytest` | Run all tests (quiet) |
| `uv run pytest -v` | Verbose: one line per test |
| `uv run pytest -q` | Minimal: dots |
| `uv run pytest tests/test_auth.py` | Run only one file |
| `uv run pytest tests/test_auth.py::test_register_success` | Run only one test |
| `uv run pytest -k "login"` | Run tests whose name matches the substring |
| `uv run pytest -x` | Stop at the first failure |
| `uv run pytest --lf` | Last-failed: re-run only tests that failed last time |
| `uv run pytest -s` | Don't capture stdout (see `print()` output live) |

### Coverage

Requires `pytest-cov` (already in `[dependency-groups.dev]`).

| Command | What it does |
|---|---|
| `uv run pytest --cov=app` | Run tests + show coverage summary |
| `uv run pytest --cov=app --cov-report=term-missing` | Show per-file coverage **plus** which specific line numbers are not covered |
| `uv run pytest --cov=app --cov-report=html` | Generate `htmlcov/index.html` — browsable per-file report with highlighted uncovered lines |
| `open htmlcov/index.html` | Open the HTML report (macOS) |
| `uv run pytest --cov=app --cov-fail-under=80` | Fail the test run if coverage drops below 80% (useful in CI) |

### Debugging a failing test

| Command | What it does |
|---|---|
| `uv run pytest --pdb` | Drop into pdb on the first failure |
| `uv run pytest -x --pdb -s` | Stop on first failure, drop into pdb, show stdout |

---

## uv (dependency management)

### Dependencies

| Command | What it does |
|---|---|
| `uv sync` | Install all deps + dev-deps declared in `pyproject.toml` into `.venv/` |
| `uv sync --no-dev` | Only runtime deps |
| `uv add fastapi-cache` | Add a runtime dep (updates `pyproject.toml` + `uv.lock`) |
| `uv add --dev pytest-benchmark` | Add a dev-only dep |
| `uv remove fastapi-cache` | Remove a dep |
| `uv lock` | Regenerate `uv.lock` without installing |
| `uv lock --upgrade` | Upgrade all deps to latest compatible versions |
| `uv lock --upgrade-package fastapi` | Upgrade a single package |

### Running

| Command | What it does |
|---|---|
| `uv run uvicorn app.main:app --reload` | Run uvicorn from the project venv |
| `uv run python -c "from app.config import settings; print(settings.database_url)"` | Run arbitrary Python under the venv |
| `uv run alembic upgrade head` | Run any script in the venv |

### Environment info

| Command | What it does |
|---|---|
| `uv venv` | Create (or report path of) the project venv |
| `uv tree` | Show the dependency tree |
| `uv tree --package pydantic` | Explain where a specific package comes from (useful for diamond deps) |
| `uv pip list` | List installed packages |

---

## Everyday workflows

### Fresh start (wipe everything, rebuild)

```bash
docker compose down -v           # drop containers + data volume
rm -rf .venv .pytest_cache .coverage htmlcov
uv sync                          # recreate venv
docker compose up -d --build     # rebuild + start stack (lifespan recreates tables)
```

### Switch from Docker to local uv

```bash
docker compose stop app          # free port 8000; keep db running
# ensure .env has DB_HOST=localhost
grep DB_HOST .env
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Switch from local uv to Docker

```bash
# Ctrl+C the uvicorn in the terminal where it runs, then:
docker compose up -d app
```

### After changing a SQLAlchemy model

Pick one depending on strategy:

```bash
# Dev-only (quick, drops/recreates in a wipe):
docker compose down -v && docker compose up -d --build

# Prod-style (versioned migration):
uv run alembic revision --autogenerate -m "describe the change"
# review alembic/versions/<hash>_describe_the_change.py
uv run alembic upgrade head
```

### Add a new runtime dependency

```bash
uv add pydantic-extra-types      # updates pyproject.toml + uv.lock
git diff pyproject.toml uv.lock  # review
```

### Check coverage before committing

```bash
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=90
# If it passes, commit. If not, add tests for the "Missing" lines reported.
```

---

## Troubleshooting shortcuts

| Symptom | First thing to try |
|---|---|
| Port `8000` already in use | `docker compose ps` → stop whichever is using it, or `lsof -i :8000` |
| `connection refused` from the app | `docker compose logs db` — Postgres may not be healthy yet |
| Alembic "relation already exists" | Tables were created by `lifespan`. `alembic stamp head` to mark migrations as applied without re-running |
| `.env` not being picked up | Check cwd when running `uv run uvicorn` — `.env` is read relative to it. Confirm with `cat .env` from the same shell |
| Pydantic `ValidationError` on config load | A required `Settings` field is missing from `.env` or env vars — compare `app/config.py` against your `.env` |