# 05 — Alembic

## ¿Qué es?

Alembic is the migration tool written by the author of SQLAlchemy. A migration is a versioned, executable script that moves the database schema from one state to another, up or down. Alembic stores a chain of these scripts under `alembic/versions/`, each one knowing its parent revision, and keeps a single row in an `alembic_version` table on the target database that records which revision is currently applied. The CLI (`alembic upgrade head`, `alembic downgrade -1`, `alembic revision --autogenerate`) walks that chain and either runs the Python code in each script or asks SQLAlchemy to diff your models against the live schema and generate a new script.

## ¿Por qué lo usamos?

Letting the ORM create tables on startup (`Base.metadata.create_all`) is fine for a demo but useless in production — it only ever creates missing tables, never alters existing ones, and leaves no history of how the schema got to its current shape. Alembic solves exactly that: the schema becomes a sequence of reviewable, reversible changes checked into git, applied in the same deterministic order on every environment. In ProgImage this matters because the Docker Compose stack runs a one-shot `migrate` service that applies the latest head before the app starts, and the same scripts can be replayed on an empty database to reproduce the schema anywhere.

## ¿Cómo funciona?

### Configuration: `alembic.ini`

The `.ini` file is Alembic's declarative config. The lines that actually matter for ProgImage are the script location and the fact that the DB URL is set in code, not here. See `alembic.ini:8`:

```ini
script_location = %(here)s/alembic
```

And at `alembic.ini:89`:

```ini
# sqlalchemy.url is set at runtime in alembic/env.py from app.config.settings
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

The commented-out `sqlalchemy.url` is intentional. We want the DSN to come from Pydantic Settings so there is a single source of truth; `env.py` injects it before any migration runs.

### The async `env.py`

`env.py` is the Python entry point Alembic executes for every CLI command. Standard scaffolding assumes a synchronous engine; ProgImage's version is adapted for async drivers. See `alembic/env.py:12`:

```python
from app.config import settings
from app.database import Base
from app import models  # noqa: F401 — side-effect: registers models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata
```

The `app import models` line is deliberately a side-effect import — importing each model module is what registers its tables against `Base.metadata`, which is in turn what autogenerate compares against the live schema.

The async pattern itself lives at `alembic/env.py:69`:

```python
async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())
```

Two pieces are doing the work:

- `async_engine_from_config(...)` builds an `AsyncEngine` from the same section Alembic would normally hand to the sync factory.
- `await connection.run_sync(do_run_migrations)` is the bridge. Alembic's internal migration runner is synchronous, so we hand it a sync-looking `Connection` object that is actually driving an async driver underneath. `run_sync` runs the callable in a worker thread managed by the async engine.

`asyncio.run(...)` at the bottom is the entry — standard async bootstrap, not Alembic-specific.

### A generated revision

Each file under `alembic/versions/` is a Python module exporting `upgrade()` and `downgrade()` plus revision metadata. See `alembic/versions/0b74c4621aa6_initial_schema_with_users_and_images.py:21`:

```python
def upgrade() -> None:
    """Create users and images tables."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        ...
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    ...
```

The `op` module is a thin wrapper over SQLAlchemy DDL that emits SQL (or runs it) depending on online vs offline mode. The matching `downgrade()` at `0b74c4621aa6_initial_schema_with_users_and_images.py:65` drops everything in reverse order.

### Autogenerate vs manual

`alembic revision --autogenerate -m "add column X"` compares `Base.metadata` to the live DB and writes a revision that closes the gap. It is excellent for straightforward column adds, renames (with care), and new tables, but it does not understand server-side defaults perfectly, cannot infer data migrations, and sometimes misorders operations. The habit worth building is: autogenerate the skeleton, then read every line of the generated file before committing it.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **Django migrations** | Tightly integrated with the Django ORM, great UX, but only inside Django. |
| **Yoyo-migrations** | Lightweight, SQL-first, no ORM coupling. No autogenerate — you write every migration by hand. |
| **sqitch** | Database-agnostic, Perl-based, SQL files only. Powerful dependency model. Steeper learning curve and a non-Python toolchain. |
| **Hand-rolled SQL + a `schema_version` table** | Minimal dependencies. You reimplement everything Alembic gives you — chaining, rollback, autogenerate — badly. |
| **`Base.metadata.create_all()` only** | Zero migrations. Fine for prototypes; fatal the first time a column needs to change in production. |

Specific friction: the async `env.py` is longer than the sync template and newcomers tend to copy a sync `env.py` by mistake, then wonder why `alembic upgrade head` prints `greenlet_spawn has not been called`. Also, autogenerate against SQLite can hide problems that only show up against Postgres (e.g., SQLite does not enforce most ALTER constraints) — ProgImage runs migrations against the real Postgres service in Docker to avoid that trap, see [`11-docker-compose.md`](11-docker-compose.md).

## Para profundizar

- Official tutorial: <https://alembic.sqlalchemy.org/en/latest/tutorial.html>
- Async `env.py` cookbook: <https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic>
- Autogenerate caveats: <https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect>
- `op` reference: <https://alembic.sqlalchemy.org/en/latest/ops.html>
