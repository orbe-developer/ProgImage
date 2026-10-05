# ProgImage

A modern FastAPI service for image storage, retrieval, and transformation. Users register, log in, and own the images they upload. All image endpoints are protected by JWT bearer tokens, and reads are scoped so one user cannot see another user's images.

**Stack:** Python 3.12 · FastAPI · Pydantic (v2) · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL (asyncpg) · PyJWT · bcrypt · Pillow · pytest + httpx + pytest-asyncio · Docker · uv

---

## Features

- Email + password registration and OAuth2-style JWT login
- Per-owner image upload and retrieval with access control (foreign non-owners get 404, not 403, so image ids are not leaked)
- Image processing: compress, rotate, thumbnail
- Twelve image filters (blur, contour, edge enhance, emboss, find edges, smooth, sharpen, Gaussian blur, unsharp mask, and more)
- Four masking operations (flat 50 %, circle, blurred circle, mask-with-image)
- Pydantic Field validation on every size/angle query parameter; `BaseSettings` for configuration
- Interactive API docs at `/docs` (Swagger UI) and `/redoc`
- Comprehensive test suite with pytest, httpx `AsyncClient`, and ASGITransport (24 tests, all green)
- One-command bring-up with `docker compose up --build`

---

## Quick start

### Option A — Docker (recommended)

```bash
cp .env.example .env           # edit if you want non-default secrets
docker compose up --build       # Postgres + app
# Apply migrations once per fresh DB:
docker compose run --rm migrate
```

The API is served on `http://localhost:8000` and the interactive docs on `http://localhost:8000/docs`.

### Option B — Local with uv

Requires Python 3.11+ and PostgreSQL running on `localhost:5432`.

```bash
cp .env.example .env
uv sync                                      # creates .venv and installs deps
uv run alembic upgrade head                  # once per fresh DB
uv run uvicorn app.main:app --reload         # dev server on :8000
```

The default lifespan hook runs `Base.metadata.create_all` at startup, so you can skip `alembic upgrade head` for local experimentation. Alembic is still the source of truth for production migrations.

---

## Running the tests

```bash
uv run pytest
```

The suite uses an in-memory SQLite database per test, overrides the `get_session` dependency, and exercises the full ASGI pipeline through `httpx.AsyncClient`. See `tests/conftest.py` for the fixtures and `tests/test_*.py` for coverage.

---

## Authentication flow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"supersecret"}'

# 2. Login — grab the access_token from the response
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d 'username=alice@example.com&password=supersecret' | jq -r .access_token)

# 3. Call a protected endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me

# 4. Upload an image
curl -H "Authorization: Bearer $TOKEN" \
  -F file=@sample.png http://localhost:8000/api/v1/images

# 5. Retrieve it
curl -H "Authorization: Bearer $TOKEN" \
  -o out.png http://localhost:8000/api/v1/images/1
```

---

## API surface

Base path: `/api/v1`

### Auth

| Method | Path             | Description                            |
|--------|------------------|----------------------------------------|
| POST   | `/auth/register` | Register a new user                    |
| POST   | `/auth/login`    | Exchange email + password for a token  |
| GET    | `/auth/me`       | Return the authenticated user          |

### Images

| Method | Path                 | Description                                     |
|--------|----------------------|-------------------------------------------------|
| POST   | `/images`            | Upload an image (JPEG or PNG), owned by caller  |
| GET    | `/images/{id}`       | Retrieve an owned image's bytes                 |

### Processing

| Method | Path                                   | Query params        |
|--------|----------------------------------------|---------------------|
| POST   | `/images/processing/compress_image`    | `width`, `height`   |
| POST   | `/images/processing/rotate_image`      | `angle`, `expand?`  |
| POST   | `/images/processing/thumbnail_image`   | `width`, `height`   |

### Filtering

Twelve `POST /images/filtering/filter_*` endpoints (blur, contour, detail, edge_enhance, edge_enhance_more, emboss, find_edges, smooth, smooth_more, sharpen, gaussian_blur, unsharp_mask).

### Masking

| Method | Path                                             | Files                     |
|--------|--------------------------------------------------|---------------------------|
| POST   | `/images/masking/mask_image`                     | 2 files, flat mask         |
| POST   | `/images/masking/mask_image_drawing_circle`      | 2 files, ellipse mask      |
| POST   | `/images/masking/mask_image_drawing_blur_circle` | 2 files, blurred ellipse   |
| POST   | `/images/masking/mask_image_existing_image`      | 3 files; third is the mask |

---

## Project layout

```
ProgImage/
├── alembic/                     # DB migrations
│   ├── versions/
│   │   └── 0b74c4621aa6_initial_schema_with_users_and_images.py
│   └── env.py
├── alembic.ini
├── app/
│   ├── main.py                  # FastAPI lifespan, router wiring
│   ├── config.py                # Pydantic Settings
│   ├── database.py              # Async engine, session factory, Base
│   ├── schemas.py               # Image, resize, rotation, error schemas
│   ├── dependencies.py          # validate_image + arity dependencies
│   ├── auth/                    # Register, login, me + JWT + bcrypt
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   └── dependencies.py
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py
│   │   └── image.py
│   └── routers/
│       ├── images.py            # Upload + retrieval (owner-scoped)
│       ├── image_processing.py
│       ├── image_filtering.py
│       └── image_masking.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_images.py
│   └── test_processing.py
├── Dockerfile                   # Multi-stage, non-root runtime user
├── docker-compose.yml           # app + postgres + migrate profile
├── .env.example
├── pyproject.toml               # uv-managed
├── uv.lock
├── REFACTOR_PLAN.md             # Modernisation plan + commit discipline
└── README.md
```

---

## Configuration

Every setting is read by `app.config.Settings` from the environment (or `.env` in the project root). See `.env.example` for the complete list; the headline knobs are:

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `JWT_SECRET` (please change in production; generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- `JWT_ALGORITHM` (default `HS256`), `JWT_EXPIRE_MINUTES` (default `60`)

---

## Modernisation history

This codebase was built progressively from a Peewee + decorator-based prototype into the current async stack. The full plan, including why each decision was made, lives in [`REFACTOR_PLAN.md`](REFACTOR_PLAN.md). Each phase is one commit, so `git log --oneline` doubles as a progress tracker.
