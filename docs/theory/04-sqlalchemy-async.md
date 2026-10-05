# 04 — SQLAlchemy 2.0 Async

## ¿Qué es?

SQLAlchemy is Python's dominant SQL toolkit and ORM. Version 2.0 reshaped the API into a single unified style — the "2.0 style" — that is explicit, typed, and awaitable. The ORM now sits on top of a `select()`-based query construction API (no more implicit `Query` objects), model classes inherit from `DeclarativeBase` instead of the old `declarative_base()` factory, columns are declared with `Mapped[...]` + `mapped_column(...)` so static type-checkers understand them, and the async extension (`sqlalchemy.ext.asyncio`) exposes `AsyncEngine`, `AsyncSession`, and `async_sessionmaker`. Under the hood it still delegates to a DBAPI driver — in ProgImage that is `asyncpg` for Postgres and `aiosqlite` for the test database.

## ¿Por qué lo usamos?

FastAPI routes are `async def`, which means they live inside an event loop. A synchronous DB call from inside an async handler blocks the whole loop and defeats the point of using async. SQLAlchemy's async extension gives us `await session.execute(select(...))` which plays correctly with the loop, so the server can juggle hundreds of in-flight requests waiting on database I/O. On top of that we get the two value propositions people choose SQLAlchemy for in the first place: the ORM for mapping Python objects to rows and relationships, and the typed query DSL for everything the ORM is too heavy for.

## ¿Cómo funciona?

### Declarative base

Every model inherits from a shared `Base`. See `app/database.py:21`:

```python
class Base(DeclarativeBase):
    """Common declarative base for all ORM models."""
```

Subclassing `DeclarativeBase` registers each model class on `Base.metadata`, which is the catalogue of tables Alembic uses for autogenerate and the dev lifespan hook uses for `create_all`.

### `Mapped` + `mapped_column`

Columns are declared with a type annotation (`Mapped[T]`) plus a `mapped_column(...)` call describing the SQL side. See `app/models/user.py:22`:

```python
id: Mapped[int] = mapped_column(primary_key=True)
email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
hashed_password: Mapped[str] = mapped_column(String(255))
is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
)
```

Nullable columns use `Mapped[str | None]` — see `app/models/image.py:25`. The annotation drives both SQLAlchemy's runtime behaviour (nullable inferred from `Optional`) and the type-checker's view of each row object.

### Relationships and `back_populates`

A one-to-many is declared on both sides with matching `back_populates` keys. Owner side at `app/models/user.py:32`:

```python
images: Mapped[list["Image"]] = relationship(
    back_populates="owner",
    cascade="all, delete-orphan",
)
```

And the owned side at `app/models/image.py:37`:

```python
owner: Mapped["User"] = relationship(back_populates="images")
```

The `cascade="all, delete-orphan"` tells the ORM to delete `Image` rows when their `User` is deleted at the Python level. That is distinct from the FK's `ondelete="CASCADE"` (`app/models/image.py:33`), which is enforced by the database itself if a user is deleted via raw SQL. ProgImage declares both so the behaviour is identical regardless of entry point.

### The async engine and session factory

See `app/database.py:25`:

```python
engine = create_async_engine(settings.database_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
```

`create_async_engine` wraps an `asyncpg` connection pool. `async_sessionmaker` is a thin factory that produces `AsyncSession` instances; `expire_on_commit=False` is almost always what you want with async code because it stops the ORM from marking attributes stale after `commit()` (which would trigger an implicit refresh — i.e., another `await` — the next time you read them).

### The request-scoped session

The pattern for giving each request its own session uses an async generator dependency at `app/database.py:35`:

```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

FastAPI calls this once per request, holds the yielded session for the body of the route, and the `async with` block closes it on the way out — rolling back any uncommitted transaction.

### Running queries

In the 2.0 style you always construct a `select()` and `await session.execute(...)`:

```python
result = await session.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
```

That is the exact pattern used in `app/auth/dependencies.py:35`. For a single scalar result there is also `session.scalar(select(...))`. Writes go through `session.add(obj)` + `await session.commit()` + `await session.refresh(obj)` — the refresh after commit is what populates `created_at` and the auto-generated `id` (see `app/routers/images.py:40`).

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **Django ORM** | Great for Django-shaped apps. Async support is new and partial. Not usable outside Django without pulling in half the framework. |
| **Tortoise ORM** | Async-native from the start, Django-like API. Smaller ecosystem, fewer dialects, less migration tooling (uses Aerich). |
| **SQLModel** | A thin wrapper by the FastAPI author combining SQLAlchemy and Pydantic in one class. Elegant for simple cases, awkward when the DB model and the API model diverge. |
| **Raw `asyncpg`** | Fastest. Zero ORM overhead. You write every query, manage every connection, and give up migrations and relationship traversal. |
| **Databases + SQLAlchemy Core** | A pre-2.0 pattern for async when the ORM did not support it. Obsolete now that 2.0 is async-native. |

Specific friction: lazy-loading relationships does not work in async code the way it does in sync code — accessing `user.images` outside a transaction raises `MissingGreenlet` or triggers an implicit `await`. The idiomatic fix is `selectinload(User.images)` on the query. Also, `Mapped[list["Image"]]` using a forward reference string requires a `TYPE_CHECKING` import to keep static tools happy — see `app/models/user.py:13`.

## Para profundizar

- Official docs (ORM 2.0): <https://docs.sqlalchemy.org/en/20/orm/>
- Async usage guide: <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html>
- 1.x → 2.0 migration guide: <https://docs.sqlalchemy.org/en/20/changelog/migration_20.html>
- `select()` and modern query construction: <https://docs.sqlalchemy.org/en/20/tutorial/data_select.html>
