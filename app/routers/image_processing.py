"""Image processing endpoints: compress, rotate, thumbnail."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from PIL import Image as Image_PIL

from app.auth.dependencies import get_current_user
from app.dependencies import ValidatedImage
from app.models.user import User
from app.routers.util import get_image_extension, save_image
from app.schemas import ErrorResponse, ImageResizeParams, ImageRotationParams

router = APIRouter(prefix="/processing")

_PROCESSING_RESPONSES = {
    200: {"content": {"image/png": {}, "image/jpeg": {}}},
    401: {"model": ErrorResponse},
    406: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


@router.post(
    "/compress_image",
    response_class=StreamingResponse,
    responses=_PROCESSING_RESPONSES,
)
async def compress_image(
    file: ValidatedImage,
    params: ImageResizeParams = Depends(),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    """Resize an image to the requested dimensions."""
    img_ext = get_image_extension(file)
    original = Image_PIL.open(file.file)

    width, height = params.width, params.height
    if width == 0 and height == 0:
        width, height = original.size

    resized = original.resize(size=(width, height))
    buffer = save_image(resized, img_ext)
    return StreamingResponse(buffer, media_type=file.content_type)


@router.post(
    "/rotate_image",
    response_class=StreamingResponse,
    responses=_PROCESSING_RESPONSES,
)
async def rotate_image(
    file: ValidatedImage,
    params: ImageRotationParams = Depends(),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    """Rotate an image by a given angle in degrees."""
    img_ext = get_image_extension(file)
    original = Image_PIL.open(file.file)
    rotated = original.rotate(params.angle, expand=params.expand)
    buffer = save_image(rotated, img_ext)
    return StreamingResponse(buffer, media_type=file.content_type)


@router.post(
    "/thumbnail_image",
    response_class=StreamingResponse,
    responses=_PROCESSING_RESPONSES,
)
async def make_thumbnail(
    file: ValidatedImage,
    params: ImageResizeParams = Depends(),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    """Produce a thumbnail bounded by the requested dimensions."""
    img_ext = get_image_extension(file)
    original = Image_PIL.open(file.file)

    width, height = params.width, params.height
    if width == 0 and height == 0:
        width, height = original.size

    # Pillow's thumbnail() mutates in place while preserving aspect ratio.
    original.thumbnail((width, height))
    buffer = save_image(original, img_ext)
    return StreamingResponse(buffer, media_type=file.content_type)
