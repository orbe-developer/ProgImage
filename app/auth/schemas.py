"""Pydantic schemas for the authentication endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    """Public representation of a user. Built from a SQLAlchemy row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """OAuth2-style bearer token payload."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
