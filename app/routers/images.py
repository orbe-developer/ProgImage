"""Image upload and retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.dependencies import ValidatedImage
from app.models.image import Image
from app.models.user import User
from app.schemas import ErrorResponse, ImageUploadResponse

router = APIRouter(prefix="/images")


@router.post(
    "",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_406_NOT_ACCEPTABLE: {"model": ErrorResponse},
    },
)
async def upload_image(
    file: ValidatedImage,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Image:
    """Upload a new image. The authenticated user becomes its owner."""
    data = await file.read()
    image = Image(
        content_type=file.content_type,
        data=data,
        description=file.filename,
        owner_id=current_user.id,
    )
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image


@router.get(
    "/{image_id}",
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}, "image/jpeg": {}}},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
async def get_image(
    image_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Return the raw bytes of an image owned by the current user.

    Access control: images owned by other users are reported as 404
    (not 403) so the API does not leak which image ids exist.
    """
    result = await session.execute(
        select(Image).where(
            Image.id == image_id,
            Image.owner_id == current_user.id,
        )
    )
    image = result.scalar_one_or_none()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found",
        )
    return Response(content=image.data, media_type=image.content_type)
