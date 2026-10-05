"""Password hashing (bcrypt) and JWT encode/decode helpers.

Uses ``bcrypt`` directly rather than passlib to avoid the known
compatibility issues between passlib and bcrypt 4.x+. JWT handling
goes through ``pyjwt`` which is the FastAPI-recommended library since
2024.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True when the plaintext password matches the bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    subject: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Produce a signed JWT with ``sub`` set to the user id."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload: dict[str, object] = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """Decode a JWT and return the ``sub`` claim as an int user id.

    Raises ``jwt.InvalidTokenError`` on any failure (expired, bad
    signature, missing subject, non-integer subject).
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    sub = payload.get("sub")
    if sub is None:
        raise jwt.InvalidTokenError("Token payload missing subject")
    try:
        return int(sub)
    except (TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError("Token subject is not an integer") from exc
