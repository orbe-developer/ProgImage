"""Pydantic schemas for request validation and response serialisation.

These models document the API contract in OpenAPI and provide the
Pydantic-based validation that FastAPI uses to coerce and reject
inbound data. Response models configured with ``from_attributes=True``
can be built directly from SQLAlchemy ORM objects.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageUploadResponse(BaseModel):
    """Returned after a successful image upload."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Database identifier of the stored image")
    content_type: str = Field(description="MIME type of the stored image")
    description: str | None = Field(
        default=None,
        description="Original filename or user-supplied description",
    )
    created_at: datetime = Field(description="When the image was stored")


class ImageResizeParams(BaseModel):
    """Query parameters for image compression and thumbnail generation."""

    width: int = Field(
        ge=0,
        le=10000,
        description="Target width in pixels (0 preserves original width)",
    )
    height: int = Field(
        ge=0,
        le=10000,
        description="Target height in pixels (0 preserves original height)",
    )


class ImageRotationParams(BaseModel):
    """Query parameters for image rotation."""

    angle: int = Field(description="Rotation angle in degrees")
    expand: bool | None = Field(
        default=None,
        description="Expand canvas to fit the rotated image",
    )


class ErrorResponse(BaseModel):
    """Standardised error payload used in `responses` metadata."""

    detail: str = Field(description="Human-readable error description")
