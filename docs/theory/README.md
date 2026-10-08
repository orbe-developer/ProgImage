# ProgImage — Theory Notes

A set of focused references for every technology introduced during the ProgImage modernisation. Written primarily as a **personal study guide** for the applicant: each file explains *what* a piece is, *why* it was chosen for ProgImage specifically, *how* it is used in the code, and *what the trade-offs* are versus alternatives.

Open each file next to the corresponding part of the codebase (file + line references are given throughout) and you should walk away able to defend every decision in `REFACTOR_PLAN.md`.

## Reading order

Start top-to-bottom if this is your first pass. The files are mostly independent, but a few build on each other (`06-jwt-authentication.md` references `07-bcrypt-passwords.md`; `09-httpx-asgi-testing.md` references `08-pytest-asyncio.md`).

### Framework layer

1. [`01-fastapi.md`](01-fastapi.md) — the web framework: routers, Depends, response models, lifespan, OpenAPI
2. [`02-pydantic.md`](02-pydantic.md) — data validation and serialisation: `BaseModel`, `Field`, `ConfigDict`, `from_attributes`
3. [`03-pydantic-settings.md`](03-pydantic-settings.md) — configuration via `BaseSettings` and `.env`

### Database layer

4. [`04-sqlalchemy-async.md`](04-sqlalchemy-async.md) — SQLAlchemy 2.0 async: `DeclarativeBase`, `Mapped`, `async_sessionmaker`, `select()`, relationships
5. [`05-alembic.md`](05-alembic.md) — schema migrations: async `env.py`, autogenerate vs manual, upgrade/downgrade

### Authentication layer

6. [`06-jwt-authentication.md`](06-jwt-authentication.md) — JSON Web Tokens: structure, claims, algorithms, OAuth2PasswordBearer flow
7. [`07-bcrypt-passwords.md`](07-bcrypt-passwords.md) — password hashing: why not plain, salt + work factor, direct `bcrypt` vs `passlib`

### Testing layer

8. [`08-pytest-asyncio.md`](08-pytest-asyncio.md) — pytest fundamentals + async testing: fixtures, scopes, `asyncio_mode="auto"`
9. [`09-httpx-asgi-testing.md`](09-httpx-asgi-testing.md) — testing FastAPI without a server: `AsyncClient` + `ASGITransport`, dependency overrides, in-memory SQLite

### Delivery layer

10. [`10-docker.md`](10-docker.md) — Dockerfile anatomy: multi-stage builds, non-root user, healthcheck, image size
11. [`11-docker-compose.md`](11-docker-compose.md) — multi-service bring-up: healthchecks, `depends_on`, profiles, named volumes
12. [`12-uv-pyproject.md`](12-uv-pyproject.md) — modern Python tooling: PEP 621, PEP 735 dependency groups, `uv.lock`, hatchling

### Cross-cutting concerns

13. [`13-access-control-patterns.md`](13-access-control-patterns.md) — AuthN vs AuthZ, owner-scoped reads, why 404 over 403, SQL-level enforcement
14. [`14-pytest-coverage.md`](14-pytest-coverage.md) — code coverage with `pytest-cov`: statement vs branch coverage, reading reports, trade-offs vs mutation testing

## Conventions

Every file follows the same shape:

- **¿Qué es?** — one-paragraph summary
- **¿Por qué lo usamos?** — the role this piece plays in ProgImage
- **¿Cómo funciona?** — concrete examples lifted from the ProgImage source
- **Trade-offs y alternativas** — what else you could have picked and why we did not
- **Para profundizar** — links to official documentation and recommended reading

Code snippets reference files using the `path/to/file.py:line` format so you can `cmd+click` straight to the source in an editor.
