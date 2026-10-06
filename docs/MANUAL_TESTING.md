# Manual testing walkthrough

End-to-end runbook for verifying every piece of ProgImage works on a fresh checkout. Covers both deployment methods in order:

1. **Method B — Docker Compose** (recommended first run; self-contained, no local Python state required besides `uv` for optional steps).
2. **Method A — Local with `uv`** reusing the Compose Postgres (demonstrates that the app code is not coupled to Docker).

Each step gives the exact command to run plus the expected result so you can compare line-by-line. Status codes come from a real walk-through — if you see anything different, jump to the [Troubleshooting](#troubleshooting) section.

---

## Prerequisites

| Tool | Version used | Install |
|------|--------------|---------|
| Docker Desktop | 29.0.1 (Server) | <https://docs.docker.com/desktop/mac-install> |
| Docker Compose | v2.40.3+ | ships with Docker Desktop |
| `uv` | 0.9.17+ | `brew install uv` or <https://docs.astral.sh/uv/> |
| Postman | 10+ | <https://www.postman.com/downloads/> |
| `curl`, `python3` | any recent | preinstalled on macOS |

> Only `docker` + `docker compose` are required to run Method B. `uv` is required for Method A and the test suite.

---

## What you will verify

- The full stack boots in one command and the healthchecks pass.
- JWT authentication: register, login, protected endpoint, and 401 on missing/bad token.
- Per-user access control: User A's image returns 404 (not 403) for User B.
- Pydantic `Field` validation runs **before** the endpoint body: `width=-5` returns a structured 422.
- Image processing endpoints (compress, rotate, filter, mask) return transformed bytes.
- Masking's exact-arity dependency returns 400 when you send 1 instead of 2 files.
- The same Postman collection works whether the API is served by the Compose container or by local `uv run uvicorn`.
- The pytest suite (24 tests) is green against an in-memory SQLite database.

---

## Method B — Docker Compose

### B1. Clean state check

```bash
cd /path/to/ProgImage

docker ps -a --filter name=progimage
docker volume ls --filter name=progimage
```

Both should return headers only. If anything shows up, run `docker compose down -v` first.

### B2. Make sure the environment file exists

```bash
ls -la .env || cp .env.example .env
cat .env
```

Default values are good enough for local use (`DB_HOST=localhost`, `DB_PORT=5432`, `JWT_SECRET` is a dev placeholder — do not deploy with it).

### B3. Build and start

```bash
docker compose up -d --build
```

First build takes ~60s. On a cached rebuild it is <10s. You should see:

```
Container progimage-db-1    Healthy
Container progimage-app-1   Started
```

### B4. Verify the stack

```bash
docker compose ps
docker compose logs app | tail -10
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/docs
```

Expected:

- `docker compose ps` shows both services `Up … (healthy)`.
- Logs end with `Application startup complete.` and `Uvicorn running on http://0.0.0.0:8000`.
- `/docs` returns `HTTP 200`.

### B5. Inspect the OpenAPI schema

```bash
curl -s http://localhost:8000/openapi.json \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Title: {d['info']['title']} v{d['info']['version']}\"); print(f\"Paths: {len(d['paths'])} endpoints\"); print(f\"Schemas: {sorted(d['components']['schemas'].keys())}\")"
```

Expected: `Title: ProgImage v0.2.0`, `Paths: 24 endpoints`, and a schemas list that includes `ImageUploadResponse`, `UserCreate`, `UserRead`, `Token`, `ErrorResponse`. `ImageResizeParams` / `ImageRotationParams` deliberately do not appear — FastAPI inlines them as separate query parameters when the models are injected via `Depends()`.

### B6. Import the Postman collection

Open Postman and import both files:

- `postman/ProgImage.postman_collection.json`
- `postman/ProgImage.postman_environment.json`

In the environments dropdown (top right), select **"ProgImage — local"**.

The collection has 5 folders (Auth, Images, Processing, Filtering, Masking) with 24 requests. The collection-level Authorization is Bearer `{{token}}`; Register and Login override to no-auth. The Login request's `Tests` script writes the returned `access_token` into both the collection and the active environment variable, so subsequent requests work without manual copy-paste.

### B7. Auth flow (3 requests)

In Postman:

| Request | Expected status | Expected body |
|---------|-----------------|---------------|
| **Auth → Register** | `201` | `UserRead` with `id`, `email`, `is_active=true`, `created_at` |
| **Auth → Login** | `200` | `{ "access_token": "eyJ...", "token_type": "bearer" }` — the Postman Console (`View → Show Postman Console`) also logs `Token saved …` |
| **Auth → Me** | `200` | Same `UserRead` returned by Register |

Sanity check: temporarily switch the **Auth → Me** request's authorisation to "No Auth" and send → you should get `401 { "detail": "Not authenticated" }`. Switch back to "Inherit auth from parent".

### B8. Images — upload and retrieve

In Postman:

| Request | What to configure | Expected status |
|---------|-------------------|-----------------|
| **Images → Upload Image** | Body (form-data) → `file` → select any JPEG or PNG from your disk | `201`, `ImageUploadResponse` with `id`, `content_type`, `description` (= filename), `created_at`. Console prints `imageId saved: 1`. |
| **Images → Get Image By Id** | URL uses `{{imageId}}` auto-populated by the Upload Tests script | `200` with the raw image bytes. Postman renders a preview inline. |

### B9. Access control — a second user cannot read

In Postman:

1. **Auth → Register** with a different body:
   ```json
   { "email": "attacker@test.com", "password": "longenoughpassword" }
   ```
   Expected `201`.
2. **Auth → Login** with the new credentials (`username=attacker@test.com`, `password=longenoughpassword`). Expected `200` — token now belongs to the attacker.
3. **Images → Get Image By Id** (URL still points at `/images/1`, which belongs to the first user). Expected **`404 Not Found`** with `{"detail": "Image 1 not found"}`. **Not 403** — see [`docs/theory/13-access-control-patterns.md`](theory/13-access-control-patterns.md) if present on this branch for why.
4. **Auth → Login** again as the original user, then **Images → Get Image By Id** → `200`.

### B10. Pydantic validation — invalid query parameters

In Postman, open **Processing → Compress Image** and attach any image to `file`. Then change the `width` query parameter to:

| `width` | Expected status | Expected `type` in error body |
|---------|-----------------|-------------------------------|
| `-5` | `422` | `greater_than_equal` on `query.width` |
| `100000` | `422` | `less_than_equal` on `query.width` |
| `50` (and `height=50`) | `200` | Response is the compressed image bytes |

The validation runs **before** the endpoint body — the `_apply` helper on `app/routers/image_processing.py:46` is never invoked for the first two cases.

### B11. Filtering (visual)

In Postman, each of these takes one `file` upload and returns the transformed image inline:

- **Filtering → Blur** → `200`
- **Filtering → Find Edges** → `200` (clearest visual effect)
- **Filtering → Emboss** → `200`

All 12 filters share the `_apply(file, pil_filter)` helper in `app/routers/image_filtering.py` — the Phase 7 refactor collapsed duplication while keeping each endpoint explicit in OpenAPI.

### B12. Masking (arity enforcement)

In Postman, open **Masking → Mask (flat 50%)**:

| Scenario | What to send | Expected status |
|----------|--------------|-----------------|
| Happy path | 2 rows with key `files`, each a different image | `200` with blended image |
| Arity check | Remove one row (only 1 `files` entry) | **`400`** with `{"detail": "You must send 2 images to mask."}` |

Then **Masking → Mask (existing image)** with 3 image rows → `200`. The third image is converted to grayscale and used as the mask.

These dependencies live in `app/dependencies.py:34-62` (`validate_image_pair`, `validate_image_triplet`) and replaced the Phase 7-era decorator wrappers.

---

## Method A — Local with `uv` (reusing Compose's Postgres)

The point of this method is to demonstrate the app is not Docker-coupled: the same code runs locally against the same database.

### A1. Stop only the app container, keep the DB

```bash
docker compose stop app
docker compose ps
```

Expected: `progimage-db-1` still `Up … (healthy)`; `progimage-app-1` is gone (or `exited`).

### A2. Verify `.env` points at `localhost`

```bash
grep DB_HOST .env
```

Expected: `DB_HOST=localhost`. The Compose DB publishes port `5432` on the host, so this resolves to the same Postgres the containerised app was using.

### A3. Start uvicorn via uv (foreground)

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expected output ends with:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Keep this terminal open. If you see a `VIRTUAL_ENV mismatch` warning, see [Troubleshooting](#troubleshooting-virtual_env-warning).

### A4. Verify the API responds (Postman)

In the **existing Postman tab** (same collection, same environment) — no changes needed:

- **Auth → Login** → `200`
- **Auth → Me** → `200`

Users and images uploaded in Method B are still there (same DB).

### A5. Run the full test suite in a second terminal

```bash
cd /path/to/ProgImage
uv run pytest -v
```

Expected: `24 passed in ~9s`. The tests use an in-memory SQLite via `tests/conftest.py:30` and dependency overrides — they do not touch the Compose Postgres.

---

## Cleanup

In the uvicorn terminal: `Ctrl+C` to stop it.

Then:

```bash
docker compose down -v
```

The `-v` flag removes the `progimage_pgdata` named volume. Omit it if you want to keep the users/images for the next run.

---

## Troubleshooting

### `OSError: Readme file does not exist: README.md` during `docker compose up --build`

Fixed on main — the Dockerfile now copies `README.md` into the builder stage because `pyproject.toml`'s `readme = "README.md"` field is read by hatchling during the project install step. If you're seeing this on an older checkout, pull `main` or add `README.md` to the `COPY alembic.ini README.md ./` line in the Dockerfile.

### Postman `/auth/me` returns `401` right after a successful `/auth/login`

Postman resolves `{{var}}` in the order **environment → collection → globals**. If the imported environment file declares `token` with an empty default, it shadows the collection variable the Login script populates.

Fix (choose one):

1. Deselect the environment: top-right dropdown → "No environment".
2. Open the environment (Environments sidebar → "ProgImage — local") and delete the `token` row.
3. Pull `main` and re-import the collection — the Login script now also writes to the environment scope when one is active.

### `migrate` profile fails with "relation 'users' already exists"

The default lifespan runs `Base.metadata.create_all` at app startup for dev convenience. If the app has started once against a fresh DB, Alembic will then try to create the same tables and fail.

In production you choose one path or the other:

- Comment out `Base.metadata.create_all` in `app/main.py` and rely on `docker compose run --rm migrate` for schema changes.
- Or keep `create_all` and skip Alembic entirely (fine for a demo, not for a long-lived service).

For a one-off recovery against this specific error, stamp Alembic to head without applying anything:

```bash
docker compose run --rm migrate alembic stamp head
```

### `VIRTUAL_ENV mismatch` warning from `uv run`

```
warning: `VIRTUAL_ENV=/path/to/other-project/.venv` does not match the project environment path `.venv` …
```

Your shell has an unrelated venv activated. Quick fix for the current session:

```bash
deactivate 2>/dev/null || unset VIRTUAL_ENV
```

For a permanent fix, check:

- `~/.zshrc`, `~/.zshenv`, `~/.zprofile` for a `source /path/to/.venv/bin/activate` line.
- VSCode / Cursor settings: `python.terminal.activateEnvironment` — set to `false` if you want to opt out of auto-activation.
- `~/.oh-my-zsh/custom/` plugins (`virtualenvwrapper` or similar).

### `/docs` returns connection refused

The app container is not up. Run `docker compose ps`. If `progimage-app-1` is missing or in `exited` state, check its logs with `docker compose logs app` — the most common cause is Postgres not being healthy yet (restart with `docker compose restart app`).

### Postman shows the Upload returning the string `"1"` instead of a JSON object

You're hitting an older build where POST `/images` returned a bare integer (pre-Phase 7). Pull `main`, rebuild (`docker compose up -d --build`), re-import the Postman collection.

---

## What to try next

- Open `/docs` in a browser and poke the Swagger UI — same API, different client.
- Change `JWT_EXPIRE_MINUTES=1` in `.env`, restart the app, log in, wait 90 seconds, then call `/auth/me` → you should get `401` because the token expired.
- Add a new filter: duplicate one of the entries in `app/routers/image_filtering.py` and point it at a different `ImageFilter` constant. Reload uvicorn, hit `/docs` — the new endpoint shows up without touching anything else.
- Run the test suite with `uv run pytest -q --cov=app` after `uv add --dev pytest-cov` to see the coverage report.
