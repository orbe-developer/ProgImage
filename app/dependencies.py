"""Shared FastAPI dependencies.

Replaces the old decorator-based ``wrappers.py`` with reusable
dependency callables. Content-type and arity checks live here;
numeric range validation lives in Pydantic ``Field`` constraints
on the schemas in ``app.schemas``.
"""

from typing import Annotated

from fastapi import Depends, File, HTTPException, UploadFile, status

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpg", "image/jpeg", "image/png"}
)


def _require_allowed_type(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Only '.jpg', '.jpeg' or '.png' files allowed.",
        )


async def validate_image(file: UploadFile = File(...)) -> UploadFile:
    """Reject any single UploadFile whose content_type is not JPEG/PNG."""
    _require_allowed_type(file)
    return file


async def validate_image_pair(
    files: list[UploadFile] = File(...),
) -> list[UploadFile]:
    """Accept exactly two JPEG/PNG files (for masking operations)."""
    if len(files) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must send 2 images to mask.",
        )
    for file in files:
        _require_allowed_type(file)
    return files


async def validate_image_triplet(
    files: list[UploadFile] = File(...),
) -> list[UploadFile]:
    """Accept exactly three JPEG/PNG files (mask-with-existing-image)."""
    if len(files) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must send 3 images to mask.",
        )
    for file in files:
        _require_allowed_type(file)
    return files


# Type aliases for ergonomic reuse in route signatures.
ValidatedImage = Annotated[UploadFile, Depends(validate_image)]
ValidatedImagePair = Annotated[list[UploadFile], Depends(validate_image_pair)]
ValidatedImageTriplet = Annotated[list[UploadFile], Depends(validate_image_triplet)]
