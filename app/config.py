"""Application configuration via Pydantic Settings.

All values can be overridden by environment variables or a .env file
in the project root. See .env.example for the full list.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # --- App ---
    app_title: str = "ProgImage"
    app_version: str = "0.2.0"

    @property
    def database_url(self) -> str:
        """Async DSN for SQLAlchemy with asyncpg driver.

        Alembic migrations use the same async engine via the
        ``run_sync`` pattern configured in ``alembic/env.py``.
        """
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
