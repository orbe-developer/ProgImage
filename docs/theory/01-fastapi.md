# 01 — FastAPI

## ¿Qué es?

FastAPI is a modern Python web framework for building HTTP APIs. It is built on top of **Starlette** (an ASGI toolkit for routing and middleware) and **Pydantic** (data validation). The two value propositions that distinguish it from Flask/Django are:

1. **Type hints drive behaviour.** You annotate route parameters with Python types and `Depends(...)`, and FastAPI uses those annotations for request parsing, response serialisation, OpenAPI schema generation, and interactive docs — all automatically.
2. **Async-first.** Routes can be `async def` and the framework runs them in an event loop, which is essential for I/O-heavy workloads (HTTP calls, database queries, file reads). Synchronous routes still work, but FastAPI shines when it does not have to block.

ProgImage runs FastAPI 0.142 on top of Uvicorn (ASGI server). Interactive docs live at `/docs` (Swagger UI) and `/redoc`.

## ¿Por qué lo usamos?

The 9fin Senior Backend JD says it explicitly: "we currently use FastAPI with strong typing & Pydantic". For a portfolio piece defending that claim, FastAPI is non-negotiable.

Beyond the JD, FastAPI gives us several things cheaply:

- **Dependency injection** — `Depends(get_current_user)` runs the auth check and injects the `User` row; `Depends(get_session)` yields a per-request `AsyncSession`. No request-local globals, no middleware magic.
- **Response models** — annotate the endpoint with `response_model=ImageUploadResponse` and FastAPI validates and serialises the return value, strips any extra fields (e.g., `hashed_password`), and documents the shape in OpenAPI.
- **OpenAPI for free** — every endpoint shows up at `/docs`. Reviewers can poke at the API without the Postman collection.
- **Lifespan** — `asynccontextmanager`-based startup/shutdown that replaces the deprecated `@app.on_event()` and composes cleanly with async DB engines.

## ¿Cómo funciona?

### App construction and lifespan

See `app/main.py`:

```python
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="...",
    lifespan=lifespan,
)
```

The `lifespan` context manager is passed to the `FastAPI` constructor. The code before `yield` runs once at startup; the code after runs at shutdown. ProgImage uses it to create tables (dev convenience) and dispose the SQLAlchemy engine.

### Routers

`APIRouter` lets you group endpoints into modules and compose them. ProgImage mounts them under `/api/v1`:

```python
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1.include_router(images_router, tags=["images"])
api_v1.include_router(image_processing_router, prefix="/images", tags=["image-processing"])
# ...
app.include_router(api_v1)
```

`tags=[...]` groups endpoints in the OpenAPI UI. Each router can also set its own `prefix`, so `auth_router` has routes like `/register`, `/login`, `/me` that end up at `/api/v1/auth/register` etc.

### Route parameters and Depends

Every piece of a request can be injected by type annotation. See `app/routers/images.py:21`:

```python
async def upload_image(
    file: ValidatedImage,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Image:
    ...
```

- `file: ValidatedImage` — a type alias for `Annotated[UploadFile, Depends(validate_image)]` (see `app/dependencies.py:48`). FastAPI reads the `UploadFile` from the multipart form, calls `validate_image(file)` to enforce content-type, and injects the result.
- `session: AsyncSession = Depends(get_session)` — FastAPI calls the async generator `get_session`, holds the yielded session for the duration of the request, and closes it after the response.
- `current_user: User = Depends(get_current_user)` — chains dependencies: `get_current_user` itself depends on `get_session` and `oauth2_scheme`.

The dependency graph is resolved once per request. Overlapping dependencies (`get_current_user` and the route both use `session`) share the same object automatically.

### Pydantic parameter models

For query parameters you can either declare each one separately or group them in a Pydantic model and inject it with `Depends()`. ProgImage uses the second pattern in `app/routers/image_processing.py:31`:

```python
async def compress_image(
    file: ValidatedImage,
    params: ImageResizeParams = Depends(),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    width, height = params.width, params.height
    ...
```

FastAPI inspects `ImageResizeParams`, treats each field as a separate query parameter, and runs Pydantic validation on them. The result is that `width=-5` fails with 422 before `compress_image` is called.

### Response models and `responses={...}`

Each endpoint can declare its success response model and document additional status codes:

```python
@router.post(
    "",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_406_NOT_ACCEPTABLE: {"model": ErrorResponse},
    },
)
```

`response_model` triggers serialisation and strips any fields not declared on the model. The `responses` dict only affects OpenAPI documentation — your 401 still has to be raised explicitly (via `HTTPException` or an auth dependency), but the response shape is now part of the published schema.

### `StreamingResponse` and `Response`

For raw bytes (image data), FastAPI exposes `Response` and `StreamingResponse` so you can skip JSON serialisation. ProgImage uses `Response(content=image.data, media_type=image.content_type)` to return image bytes directly and `StreamingResponse(buffer, media_type=...)` for Pillow outputs.

### Exceptions

`raise HTTPException(status_code=404, detail="...")` short-circuits the response. FastAPI serialises it as `{"detail": "..."}` with the right status code. In ProgImage this is used throughout the auth router (401 for bad credentials, 400 for duplicate email) and the images router (404 for not-owned images).

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **Flask + flask-restx** | Older, mature, synchronous by default. Verbose for the same functionality (manual request parsing, no DI, less OpenAPI integration). |
| **Django REST Framework** | Full-featured, batteries included, but opinionated and heavier. ORM-coupled. Async support is bolted on, not native. |
| **Litestar** | Newer FastAPI-like framework with slightly different ergonomics and better async DB story out of the box. Smaller ecosystem. |
| **Starlette directly** | FastAPI is a thin layer over Starlette. If all you need is routing and middleware (no Pydantic, no DI, no OpenAPI), Starlette is the lighter choice. |

Specific friction with FastAPI:

- Dependency overrides for tests (`app.dependency_overrides[dep] = fake`) are powerful but easy to leak between tests if you forget to clear them — hence the `app.dependency_overrides.clear()` call in `tests/conftest.py:63`.
- Writing routes that mix query, body, and `Form` fields requires careful signatures — the `Form(...)` / `File(...)` markers exist exactly for the cases where FastAPI cannot infer the source.

## Para profundizar

- Official docs: <https://fastapi.tiangolo.com>
- Dependency injection deep-dive: <https://fastapi.tiangolo.com/tutorial/dependencies/>
- OpenAPI customisation: <https://fastapi.tiangolo.com/how-to/configure-swagger-ui/>
- Lifespan events: <https://fastapi.tiangolo.com/advanced/events/>
