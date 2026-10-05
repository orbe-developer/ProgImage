# 02 — Pydantic (v2)

## ¿Qué es?

Pydantic is a data validation library based on Python type hints. You declare the shape of a payload or response as a class whose attributes carry type annotations and optional `Field(...)` constraints; Pydantic generates the parser and validator for you.

Version 2 was a near-total rewrite with the core moved to Rust (`pydantic-core`). It is dramatically faster than v1 (~5–50× for typical workloads) and introduces some API changes (`ConfigDict` instead of inner `class Config:`, `model_config = ConfigDict(from_attributes=True)` instead of `orm_mode = True`, `model_validate` instead of `.from_orm()`). ProgImage uses v2 exclusively.

## ¿Por qué lo usamos?

- **Compile-time-ish schema**: a `BaseModel` subclass is the single declaration of a payload shape — parsing, validation, serialisation, and OpenAPI schema all derive from it.
- **FastAPI integration**: FastAPI uses Pydantic for request bodies, query models (via `Depends()`), response models, and error responses. Pydantic is not optional in a FastAPI app.
- **Field constraints**: `Field(ge=0, le=10000, min_length=8, max_length=128)` replaces hand-rolled validation loops. The 9fin JD explicitly asks for "strong typing & Pydantic" — this is what they mean.
- **ORM interop**: `ConfigDict(from_attributes=True)` lets a model be built directly from a SQLAlchemy row, which keeps router code tiny (`return image` on `app/routers/images.py:46` becomes an `ImageUploadResponse` automatically).

## ¿Cómo funciona?

### `BaseModel`

Every schema inherits from `BaseModel`. See `app/schemas.py:14–21`:

```python
class ImageUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Database identifier of the stored image")
    content_type: str = Field(description="MIME type of the stored image")
    description: str | None = Field(default=None, description="...")
    created_at: datetime = Field(description="When the image was stored")
```

Pydantic reads the type annotations and `Field(...)` defaults at class-creation time and compiles an optimised validator in Rust. At runtime, `ImageUploadResponse(id=..., ...)` or `ImageUploadResponse.model_validate(sqlalchemy_row)` runs that validator and returns an instance (or raises `ValidationError`).

### `Field(...)` constraints

`Field` carries metadata that both FastAPI and Pydantic honour. ProgImage leans on the numeric constraints heavily — see `app/schemas.py:24–33`:

```python
class ImageResizeParams(BaseModel):
    width: int = Field(ge=0, le=10000, description="Target width in pixels")
    height: int = Field(ge=0, le=10000, description="Target height in pixels")
```

- `ge`, `le` → greater-equal, less-equal (integer and float constraints)
- `min_length`, `max_length` → strings and collections
- `pattern` → regex-based string validation
- `description` → shows up in OpenAPI

A request with `width=-5` is rejected before the endpoint body runs; FastAPI returns a 422 with a structured error body naming the offending field. This is the behaviour `tests/test_processing.py:test_compress_rejects_negative_width_via_pydantic` verifies.

### `ConfigDict(from_attributes=True)`

In v2, model config is a `ConfigDict` assigned to `model_config` (not an inner `class Config:` as in v1). The two settings ProgImage uses:

```python
model_config = ConfigDict(from_attributes=True)
```

This flag lets Pydantic read fields off any object that exposes them as attributes, not only off dicts. In practice it means `ImageUploadResponse.model_validate(image_row)` works where `image_row` is a SQLAlchemy ORM instance. Without this flag you would have to build a dict yourself.

### `EmailStr`

For email fields Pydantic ships `pydantic.EmailStr` (requires the `email-validator` package, which we pull via `pydantic[email]` in `pyproject.toml`). See `app/auth/schemas.py:10`:

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
```

Any email that fails RFC 5322-ish validation is rejected with a 422 before the route body runs; `tests/test_auth.py:test_register_malformed_email_rejected` exercises this path.

### Nested models and discriminated unions

ProgImage does not need nested models for its payloads, but Pydantic supports them cleanly: a field annotated as another `BaseModel` subclass is validated recursively. For polymorphic payloads, v2 adds `Field(discriminator="kind")` for discriminated unions — useful if different event shapes share an endpoint.

### Serialisation

`model.model_dump()` returns a dict; `model.model_dump_json()` returns a JSON string. In FastAPI you almost never call these yourself — the framework serialises the response based on `response_model`. But in tests we do call them (`tests/test_images.py` reads the JSON body back via `r.json()`, which maps to `model_dump` on the server side).

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **dataclasses + manual validation** | Zero dependencies, but you reimplement every constraint. No OpenAPI, no coercion. |
| **marshmallow** | Mature ecosystem (Flask-smorest, etc.). Verbose compared to Pydantic — fields declared as class attributes using `fields.Int()` style. Not integrated with FastAPI. |
| **attrs + cattrs** | Clean, highly configurable. `cattrs` handles (de)serialisation. More assembly required than Pydantic. |
| **msgspec** | Even faster than Pydantic v2 for pure serialisation workloads; smaller API, less ecosystem reach. Worth watching but not the standard choice. |

Pydantic v2 isn't free of friction. Error messages, while structured, can be dense when nested validators fail. v1→v2 migration broke patterns like `.from_orm()`, `.dict()`, and the `Config` nested class — any Pydantic v1 Stack Overflow answer you find needs translation.

## Para profundizar

- Official docs: <https://docs.pydantic.dev/latest/>
- Field constraints reference: <https://docs.pydantic.dev/latest/concepts/fields/>
- v1 → v2 migration guide: <https://docs.pydantic.dev/latest/migration/>
- Deep-dive on v2 performance / Rust core: <https://docs.pydantic.dev/latest/blog/pydantic-v2-final/>
