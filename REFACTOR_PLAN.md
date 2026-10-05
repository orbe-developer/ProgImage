# ProgImage — Modernisation Plan for 9fin Senior Backend Engineer Application

## Context

ProgImage is a personal FastAPI project at `/Users/osb/Documents/GitHub/ProgImage` being used as portfolio evidence for a 9fin Senior Backend Engineer application. The 9fin JD requires:
- **"FastAPI with strong typing & Pydantic"**
- Experience designing data flow from storage to API endpoints
- **"complex access control business logic"** (part of the domain)
- Testable, maintainable code with code review discipline

Current state falls short on several fronts: zero Pydantic imports, no auth, no tests, no dependency manifest, no Docker, hardcoded DB credentials, deprecated FastAPI patterns, no virtual env tooling.

Goal: make the project **honestly defensible** at CV and interview level while also being a genuinely modern FastAPI codebase that demonstrates:
- Pydantic schemas + Pydantic Settings
- Async SQLAlchemy 2.0 with asyncpg
- JWT authentication with bcrypt password hashing
- pytest + httpx + pytest-asyncio
- uv + pyproject.toml
- Docker + docker-compose for one-command bring-up
- Modern FastAPI lifespan context manager (not deprecated on_event)

Side benefit: strengthens the pytest claim already made in the Oscar Associates CV skills table.

---

## Current state (findings)

### File inventory (verified)
```
ProgImage/
├── .gitignore              (references /env/, .pytest_cache/, __pycache__/)
├── .idea/                  (JetBrains, ignored)
├── README.md
└── app/
    ├── __init__.py         (empty)
    ├── database.py         (Peewee, HARDCODED postgres/postgres, DB "heycar_db")
    ├── main.py             (@app.on_event — deprecated)
    └── routers/
        ├── __init__.py     (empty)
        ├── images.py       (37 lines — POST, GET)
        ├── image_processing.py (83 lines — compress, rotate, thumbnail)
        ├── image_filtering.py  (227 lines — 12 near-identical filter endpoints)
        ├── image_masking.py    (109 lines — 4 masking operations)
        ├── util.py             (52 lines — helpers)
        └── wrappers.py         (48 lines — manual validation decorators)
```

### Git history (verified)
Linear learning-project trajectory:
- `d5106ba` First commit — initial FastAPI + Peewee + single `images.py` monolith (462 lines)
- `eb897f2`, `8a71eda` "First commit" x2 — small corrections
- `b59f411` Create README.md
- `9eeaeb3` Split image file into image_processing, image_filtering, image_masking (PR #1)
- `10ac421` Delete comments in main.py
- `05a054d` Create the wrappers and util modules (PR #2) — DRYed up filter/masking files
- `a713139` Add comprehensive README

Remote: `git@github.com-orbe-developer:orbe-developer/ProgImage.git` on `main`. No `.pytest_cache/` exists (tests mentioned in `.gitignore` were planned but never written).

### Critical gaps for the 9fin claim
- ❌ No `pydantic` imports anywhere — no `BaseModel`, no `Field`
- ❌ No `requirements.txt` / `pyproject.toml` — reviewer can't install deps
- ❌ No `Dockerfile` / `docker-compose.yml` — reviewer can't run in one command
- ❌ No `tests/` directory — pytest claim lacks any demo
- ❌ No `.env` or config module — DB password hardcoded
- ❌ No authentication — JD values access control
- ❌ Deprecated `@app.on_event` instead of modern `lifespan`
- ❌ Response types untyped: POST `/images` returns bare `int`
- ❌ Peewee ORM is less common in modern FastAPI roles than SQLAlchemy

### Code smells (lower priority)
- 12 near-identical filter endpoints
- Typo `smoth_image` instead of `smooth_image`
- `description` field stores filename (misleading)
- DB name `heycar_db` is a leftover
- No logging

---

## Decisions confirmed (via AskUserQuestion)

| Decision | Choice |
|---|---|
| **ORM** | Migrate to Async SQLAlchemy 2.0 (asyncpg driver) |
| **Security** | JWT auth with User model, bcrypt hashing, FastAPI OAuth2PasswordBearer |
| **Deps + venv** | `uv` + `pyproject.toml` |

Scope: full modernisation — Pydantic + SQLAlchemy async + JWT + Docker + tests + uv + lifespan.

---

## Answers to your other questions

### "¿Es necesario Pydantic?"
Yes — for two reasons:
1. The 9fin claim must be honest. "FastAPI with strong typing & Pydantic" means `BaseModel` schemas, not just FastAPI's internal use of Pydantic for `int` coercion.
2. Pydantic genuinely improves the code: response contracts become self-documenting in OpenAPI, Field validation replaces hand-rolled checks, Settings handles config cleanly.

### "¿Los wrappers hacían lo mismo que Pydantic?"
Partially yes. Breakdown:

| Current wrapper | Pydantic replacement? |
|---|---|
| `verify_image_dimesions(width, height > 0)` | **Yes, 100%** — replaced by `Field(ge=0, le=10000)` |
| `verify_number_of_images(len == 2)` | Partial — can use `conlist(min_length=2, max_length=2)` |
| `verify_image_content_type(file)` | **No** — runtime check on `UploadFile.content_type` is hard for Pydantic (file is already decoded). Better refactored into a FastAPI **Dependency** than a decorator. |
| `verify_images_content_type(files)` | Same as above — refactor to Dependency |

Plan: remove `verify_image_dimesions` (Pydantic Field), convert content-type checks to FastAPI Dependencies (cleaner than decorators), keep `verify_number_of_images` as a Dependency too.

### "¿Debe cambiarse la estructura de carpetas?"
Yes, with additions (not restructuring). See folder tree below.

### "¿Hay que crear otros archivos?"
Yes — many: schemas, config, auth module, models, tests, Docker files, pyproject.toml, .env.example, Alembic (optional).

### "¿Vale la pena cambiar Peewee → SQLAlchemy?"
**Yes** (your decision: async SQLAlchemy 2.0). Modern FastAPI standard. More transferable skill. Pairs naturally with Pydantic. Shows session management and declarative mapping — both common interview topics.

### "¿Vale la pena un entorno virtual?"
**Yes, essential.** With `uv` it's automatic — `uv venv` + `uv sync` and you're done. The current project doesn't have one tracked (`.gitignore` ignores `/env/` but nothing is set up). After this plan: documented, reproducible, one-command setup.

### "¿Debemos revisar git history?"
Done above. Confirms the project is a learning project with incremental refactors. Last significant work ~1 year of commits ago (dates vary — commit history is small). No tests ever added. No deployment infrastructure. All the modernisation work in this plan is net-new, not undoing past work.

### "Guardar plan en documento para próxima sesión"
Yes — after plan approval, this plan will be committed to `ProgImage/REFACTOR_PLAN.md` so future sessions have full context. Current plan location (`/Users/osb/.claude/plans/`) is session-scratch; the committed copy survives.

---

## Final plan — full modernisation

### Phase 0 — Save plan in project

**Create `ProgImage/REFACTOR_PLAN.md`** (this document). Lets any future session or reviewer understand the modernisation. Committed to git from the start.

### Phase 1 — Tooling foundation

**Create `pyproject.toml`** (uv-compatible):
```
[project]
name = "progimage"
version = "0.2.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic>=2.6",
    "pydantic-settings>=2.2",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "pillow>=10.2",
    "python-multipart>=0.0.9",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "python-dotenv>=1.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "aiosqlite>=0.19",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Bring-up: `uv venv && uv sync` → `uv run uvicorn app.main:app --reload`.

Peewee removed entirely. `python-jose` + `passlib[bcrypt]` for JWT + password hashing.

### Phase 2 — Config via Pydantic Settings

**Create `app/config.py`**:
```
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "progimage"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="")

settings = Settings()
```

**Create `.env.example`** mirroring the above fields. Add `.env` to `.gitignore`.

### Phase 3 — SQLAlchemy async models

**Create `app/database.py`** (replaces current Peewee version):
```
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

**Create `app/models/` package**:
- `app/models/__init__.py` — imports Image, User
- `app/models/image.py` — `Image` SQLAlchemy declarative model:
  - `id: Mapped[int] = mapped_column(primary_key=True)`
  - `content_type: Mapped[str]`
  - `image: Mapped[bytes]` (LargeBinary)
  - `description: Mapped[str | None]`
  - `created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)`
  - `owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))`
  - `owner: Mapped["User"] = relationship(back_populates="images")`
- `app/models/user.py` — `User` SQLAlchemy declarative model:
  - `id`, `email` (unique), `hashed_password`, `is_active`, `created_at`
  - `images: Mapped[list["Image"]] = relationship(back_populates="owner")`

**Alembic setup**:
- `uv run alembic init alembic`
- `alembic.ini` — read URL from env
- `alembic/env.py` — use `Base.metadata` and async engine
- Initial migration creating `users` and `images` tables

### Phase 4 — Pydantic schemas

**Create `app/schemas.py`**:
- `ImageUploadResponse(BaseModel)` — `id`, `content_type`, `description`, `created_at`
- `ImageResizeParams(BaseModel)` — `width: int = Field(ge=0, le=10000)`, `height: int = Field(ge=0, le=10000)`
- `ImageRotationParams(BaseModel)` — `angle: int`, `expand: bool | None = None`
- `ErrorResponse(BaseModel)` — `detail: str`

### Phase 5 — JWT authentication module

**Create `app/auth/` package**:

- `app/auth/schemas.py`:
  - `UserCreate(BaseModel)` — `email: EmailStr`, `password: str = Field(min_length=8)`
  - `UserRead(BaseModel)` — `id`, `email`, `is_active`, `created_at`
  - `Token(BaseModel)` — `access_token: str`, `token_type: Literal["bearer"] = "bearer"`
  - `TokenPayload(BaseModel)` — `sub: int`, `exp: int`

- `app/auth/security.py`:
  - `pwd_context = CryptContext(schemes=["bcrypt"])`
  - `hash_password(password)` / `verify_password(plain, hashed)`
  - `create_access_token(subject: int)` returns JWT string
  - `decode_token(token)` returns `TokenPayload` or raises

- `app/auth/dependencies.py`:
  - `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")`
  - `async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> User:`
    - Decodes token, looks up user by id, raises 401 if invalid/missing

- `app/auth/router.py`:
  - `POST /auth/register` — accepts `UserCreate`, hashes password, inserts User, returns `UserRead`
  - `POST /auth/login` — accepts `OAuth2PasswordRequestForm`, verifies credentials, returns `Token`
  - `GET /auth/me` — protected by `Depends(get_current_user)`, returns `UserRead`

### Phase 6 — FastAPI lifespan + wire everything

**Rewrite `app/main.py`**:
```
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.auth.router import router as auth_router
from app.routers.images import router as images_router
# ...

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: ensure tables exist (dev convenience; prod uses alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="ProgImage", version="0.2.0", lifespan=lifespan)
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1.include_router(images_router, tags=["images"])
# ...
app.include_router(api_v1)
```

Remove deprecated `on_event` entirely.

### Phase 7 — Refactor routers

**`app/routers/images.py`**:
- Add `response_model=ImageUploadResponse` to POST
- Use `AsyncSession = Depends(get_session)` and `current_user: User = Depends(get_current_user)`
- Scope uploads to `current_user`; GET returns 404 if image doesn't belong to user
- Replace raw int return with `ImageUploadResponse(...)` populated from the ORM object
- Add `responses={404: {"model": ErrorResponse}}` and `401: {"model": ErrorResponse}`

**`app/routers/image_processing.py`**:
- Replace `width: int, height: int` with `params: ImageResizeParams = Depends()`
- Replace `angle: int` + `expand: Optional[bool]` with `params: ImageRotationParams = Depends()`
- Remove `@verify_dimensions` decorator — Pydantic covers it now
- Protect all endpoints with `Depends(get_current_user)`

**`app/routers/image_filtering.py`** and **`image_masking.py`**:
- Add `Depends(get_current_user)` to protect endpoints
- Leave filter duplication alone (out of scope, Tier 3 skip)

**`app/routers/wrappers.py`**:
- Remove `verify_dimensions` (Pydantic replaces it)
- Keep `verify_content_type` / `verify_content_types` / `verify_number_images` **but convert to FastAPI Dependencies** rather than decorators (cleaner, chainable with auth)
- Optionally move to `app/dependencies.py` for discoverability

**`app/routers/util.py`**:
- Remove `verify_image_dimesions`
- Keep `get_image_extension`, `save_image`

### Phase 8 — Tests

**Create `tests/` with pytest + httpx + pytest-asyncio**:

- `tests/__init__.py`
- `tests/conftest.py`:
  - Override `get_session` to use SQLite in-memory via `aiosqlite` for test isolation
  - Override `settings.jwt_secret` to a test value
  - Provide `anonymous_client`, `authenticated_client` fixtures
  - Provide `test_user` fixture
- `tests/test_auth.py`:
  - Register succeeds, returns `UserRead`
  - Register with duplicate email → 400
  - Register with weak password (< 8 chars) → 422 (Pydantic)
  - Login with valid credentials → 200 with token
  - Login with wrong password → 401
  - `/auth/me` requires token
- `tests/test_images.py`:
  - POST `/images` requires auth → 401 anonymous, 200 authenticated
  - POST happy path returns `ImageUploadResponse` shape with id/content_type/description
  - POST with wrong content type → 406
  - GET `/images/{id}` returns bytes for owner
  - GET `/images/{id}` returns 404 for non-owner (access control proof)
- `tests/test_processing.py`:
  - POST compress with valid dimensions → 200 bytes
  - POST compress with `width=-5` → 422 (Pydantic Field validation proves itself)
  - POST rotate happy path

Target: 10–15 tests. Enough to defend the pytest claim and demonstrate access control.

Run: `uv run pytest -q`.

### Phase 9 — Docker

**Create `Dockerfile`**:
```
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev build-essential \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Create `docker-compose.yml`**:
```
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_DB: ${DB_NAME:-progimage}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      retries: 5
  app:
    build: .
    environment:
      DB_HOST: db
      DB_USER: ${DB_USER:-postgres}
      DB_PASSWORD: ${DB_PASSWORD:-postgres}
      DB_NAME: ${DB_NAME:-progimage}
      JWT_SECRET: ${JWT_SECRET:-dev-secret-do-not-use-in-prod}
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
volumes:
  pgdata:
```

One command: `docker compose up --build`.

### Phase 10 — README overhaul

Update `README.md`:
- Stack: Python 3.12 · FastAPI · Pydantic · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL · JWT (python-jose + bcrypt) · Pillow · pytest · Docker · uv
- Features: image CRUD + processing + authentication + access control
- Local dev: `uv venv && uv sync && uv run uvicorn app.main:app --reload`
- Container: `docker compose up --build`
- Tests: `uv run pytest -q`
- API docs: `http://localhost:8000/docs`
- Auth flow example (curl register → login → use token)

---

## Final folder structure

```
ProgImage/
├── alembic/
│   ├── versions/
│   │   └── xxxx_initial.py
│   ├── env.py
│   ├── script.py.mako
│   └── README
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                 ← lifespan, wires routers
│   ├── config.py               ← NEW: Pydantic Settings
│   ├── database.py             ← SQLAlchemy async engine + session
│   ├── schemas.py              ← NEW: image + param + error schemas
│   ├── auth/                   ← NEW: authentication package
│   │   ├── __init__.py
│   │   ├── router.py           ← /register, /login, /me
│   │   ├── schemas.py          ← UserCreate, UserRead, Token
│   │   ├── security.py         ← bcrypt + JWT helpers
│   │   └── dependencies.py     ← get_current_user
│   ├── models/                 ← NEW: SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── image.py            ← Image model with owner FK
│   │   └── user.py             ← User model
│   └── routers/
│       ├── __init__.py
│       ├── images.py              ← Pydantic response + auth + async session
│       ├── image_processing.py    ← Pydantic params + auth
│       ├── image_filtering.py     ← auth guard (duplication left as-is)
│       ├── image_masking.py       ← auth guard
│       ├── wrappers.py            ← trimmed; content-type checks become Dependencies
│       └── util.py                ← trimmed
├── tests/
│   ├── __init__.py
│   ├── conftest.py             ← fixtures: in-memory DB, auth client
│   ├── test_auth.py
│   ├── test_images.py
│   └── test_processing.py
├── .env.example                ← NEW
├── .gitignore                  ← add .env, .venv/
├── Dockerfile                  ← NEW
├── docker-compose.yml          ← NEW
├── pyproject.toml              ← NEW: uv-managed
├── uv.lock                     ← NEW: generated by uv sync
├── README.md                   ← updated
└── REFACTOR_PLAN.md            ← NEW: this plan (committed from Phase 0)
```

### Files created
- `app/config.py`, `app/schemas.py`
- `app/auth/__init__.py`, `app/auth/router.py`, `app/auth/schemas.py`, `app/auth/security.py`, `app/auth/dependencies.py`
- `app/models/__init__.py`, `app/models/image.py`, `app/models/user.py`
- `alembic/` directory + `alembic.ini`
- `tests/__init__.py`, `tests/conftest.py`, `tests/test_auth.py`, `tests/test_images.py`, `tests/test_processing.py`
- `.env.example`, `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `REFACTOR_PLAN.md`

### Files modified
- `app/main.py` (lifespan, wire routers)
- `app/database.py` (SQLAlchemy async)
- `app/routers/images.py` (schemas, auth, session)
- `app/routers/image_processing.py` (Pydantic params, auth)
- `app/routers/image_filtering.py` (auth guard)
- `app/routers/image_masking.py` (auth guard)
- `app/routers/wrappers.py` (trim, convert to Dependencies)
- `app/routers/util.py` (trim)
- `README.md` (overhaul)
- `.gitignore` (add .env, .venv/)

### Files not touched (out of scope)
- Filter endpoint duplication in `image_filtering.py` (Tier 3 — nice-to-have, not required)
- `smoth_image` typo rename (same reason)
- Logging setup (same reason)

---

## Verification

End-to-end checks after implementation:

1. **One-command bring-up:** `docker compose up --build` starts Postgres + app; FastAPI serves at `http://localhost:8000/docs`
2. **Local dev:** `uv venv && uv sync && uv run uvicorn app.main:app --reload` works
3. **Schemas visible:** `/docs` and `/openapi.json` show `ImageUploadResponse`, `ImageResizeParams`, `ImageRotationParams`, `ErrorResponse`, `UserCreate`, `UserRead`, `Token` under Schemas
4. **Auth flow:**
   - `POST /api/v1/auth/register` → 201 with `UserRead`
   - `POST /api/v1/auth/login` → 200 with `Token`
   - `GET /api/v1/auth/me` with Bearer token → 200
   - `GET /api/v1/auth/me` without token → 401 with `ErrorResponse`
5. **Access control:** User A uploads image, User B GETs that image id → 404 (not leaked)
6. **Pydantic validation:** `POST /api/v1/images/processing/compress_image?width=-5&height=10` → 422 (Pydantic shape, not custom 400)
7. **Upload roundtrip:** `curl -F file=@sample.png -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/images` returns JSON with `{"id", "content_type", "description", "created_at"}`
8. **Tests pass:** `uv run pytest -q` reports all green (target 10–15 tests)
9. **No deprecation warnings:** uvicorn startup clean (no `on_event` warning)
10. **Alembic:** `uv run alembic upgrade head` works against a fresh DB

Once these pass, the Pydantic + pytest + FastAPI claims in the Oscar Associates CV are honestly defensible, and the project is interview-ready for 9fin Senior Backend Engineer. Can also demonstrate access control (JD mentions "complex access control business logic").

---

## Approximate effort

| Phase | Effort |
|---|---|
| 0 — Save plan | 5 min |
| 1 — pyproject.toml + uv | 20 min |
| 2 — Pydantic Settings | 20 min |
| 3 — SQLAlchemy models + Alembic | 2 h |
| 4 — Pydantic schemas | 20 min |
| 5 — JWT auth module | 2 h |
| 6 — Main.py lifespan + wiring | 30 min |
| 7 — Refactor routers | 1.5 h |
| 8 — Tests | 2 h |
| 9 — Docker | 1 h |
| 10 — README | 30 min |
| **Total** | **~10–11 h** |

---

## Session continuity

After plan approval:
1. First action is to commit this plan as `ProgImage/REFACTOR_PLAN.md` so any future session (yours or a new Claude session) can read it as context.
2. We can also use `TaskCreate` to break the 10 phases into tracked tasks that persist within this session.
3. If we have to split across sessions, the next session should start by reading `ProgImage/REFACTOR_PLAN.md` and checking which phases are already complete (via git log on the ProgImage repo).

## Commit discipline

**One commit per phase.** Each of the 10 phases finishes with a single commit on `main`:

- Makes the progression auditable and reversible — any phase can be `git revert`ed in isolation if a later phase exposes a problem.
- The commit message starts with `Phase N:` so git log doubles as a progress tracker.
- If a session ends mid-phase, the next session can run `git log --oneline main` on this repo and immediately see which phase to resume.

Commit message template:
```
Phase <N>: <short summary>

<optional bullet list of what the phase delivered>
```

Example from Phase 0:
```
Phase 0: Add modernisation plan (REFACTOR_PLAN.md)

Captures scope decisions (async SQLAlchemy, JWT auth, uv + pyproject),
answers to design questions, final folder structure, verification steps,
and per-phase commit discipline. Serves as context for future sessions.
```
