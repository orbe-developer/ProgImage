# 03 — Pydantic Settings

## ¿Qué es?

Pydantic Settings is a companion library to Pydantic for building configuration objects out of environment variables, `.env` files, and (optionally) secrets directories. You declare a `BaseSettings` subclass the same way you would declare a `BaseModel` — with typed attributes and defaults — and the library takes care of loading values at construction time, coercing them to the declared types, and failing loudly if a required value is missing. In Pydantic v2 it lives in its own package (`pydantic-settings`) rather than inside `pydantic` itself, which keeps the core validation library free of filesystem/env dependencies.

## ¿Por qué lo usamos?

ProgImage runs the same code in three different places: a developer laptop, a Docker Compose stack, and a test suite. Each environment needs different database credentials, a different JWT secret, and sometimes a different Postgres port. Pydantic Settings gives us one typed object that reads those values from the environment, validates them (an `int` port stays an `int`, not a string), and exposes derived values like the full async DSN as a Python property. It also plays nicely with the rest of the Pydantic stack we are already using for request/response schemas, so there is only one validation library in the dependency tree.

## ¿Cómo funciona?

### The `BaseSettings` class

See `app/config.py:10`:

```python
class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables / .env."""

    # --- Database ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "progimage"

    # --- JWT ---
    jwt_secret: str = "change-me-in-production-with-a-strong-32-byte-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
```

Every attribute is either required (no default) or has a safe default. At instantiation time, Pydantic Settings walks each field, looks for a matching environment variable (by default the uppercase field name — `DB_HOST`, `JWT_SECRET`, etc.), falls back to `.env`, and finally to the declared default. Type coercion runs on each value, so `DB_PORT=5432` from the shell arrives as `int`, not `str`.

### `SettingsConfigDict`

Behaviour is tuned via `model_config`, which in v2 is a `SettingsConfigDict` (the settings-specific version of `ConfigDict`). See `app/config.py:41`:

```python
model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
)
```

- `env_file=".env"` — look for a `.env` file in the working directory and treat it as a source of defaults (lower precedence than the real environment).
- `case_sensitive=False` — `db_host`, `DB_HOST`, and `Db_Host` all map to the same field. Convenient when environments inherit variables from different providers.
- `extra="ignore"` — tolerate unrelated environment variables. Without this the whole app would refuse to start on any machine that happened to have an unknown variable set.

### Computed properties

Settings classes are plain Pydantic models at heart, so you can add `@property` methods that derive values on demand. ProgImage uses this for the DSN at `app/config.py:29`:

```python
@property
def database_url(self) -> str:
    return (
        f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
        f"@{self.db_host}:{self.db_port}/{self.db_name}"
    )
```

Both the SQLAlchemy engine (`app/database.py:25`) and Alembic's `env.py:22` call `settings.database_url`, so there is a single source of truth for the DSN. Change `DB_PORT` once in the environment and both the running app and the migration runner see it.

### The singleton pattern

`settings = Settings()` at module level (`app/config.py:49`) is the common pattern: construct one instance when the module is imported, then import `settings` wherever needed. Values are frozen for the life of the process. For cases where you want to construct different `Settings` objects per-test, you can instantiate the class directly with keyword arguments that take precedence over everything else.

## Trade-offs y alternativas

| Alternative | Trade-off |
|---|---|
| **`os.environ.get(...)` scattered through modules** | Zero dependencies, but no validation, no coercion, no central place to see every variable. Easy to typo. |
| **`python-dotenv` alone** | Loads `.env` into `os.environ`. Still leaves you parsing strings by hand. Composes with Pydantic Settings rather than competing with it. |
| **`dynaconf`** | Richer feature set (multiple file formats, layered configs, Vault integration). Heavier dependency and a different mental model from Pydantic. |
| **`environ-config` / `attrs`-based libraries** | Clean, typed, no Pydantic. Fine if you are not already using Pydantic — but if you are, you double the validation surface. |

Specific friction with Pydantic Settings: the auto-mapping from field name to env variable can surprise you when fields contain underscores (`db_port` ↔ `DB_PORT`, which happens to work, but nested delimiters need explicit configuration). Also, computed values like `database_url` live outside the validation graph, so if you refactor one of the inputs you do not get a validation error — just a wrong string.

## Para profundizar

- Official docs: <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>
- Settings sources (env, dotenv, secrets, CLI): <https://docs.pydantic.dev/latest/concepts/pydantic_settings/#settings-sources>
- `SettingsConfigDict` reference: <https://docs.pydantic.dev/latest/api/pydantic_settings/>
- Twelve-Factor App "Config" principle (the design this library serves): <https://12factor.net/config>
