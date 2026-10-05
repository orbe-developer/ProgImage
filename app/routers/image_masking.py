"""Image masking endpoints: composite two images with various masks."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from PIL import ImageDraw, ImageFilter, Image as Image_PIL

from app.auth.dependencies import get_current_user
from app.dependencies import ValidatedImagePair, ValidatedImageTriplet
from app.models.user import User
from app.routers.util import get_image_extension, save_image
from app.schemas import ErrorResponse

router = APIRouter(prefix="/masking")

_MASK_RESPONSES = {
    200: {"content": {"image/png": {}, "image/jpeg": {}}},
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    406: {"model": ErrorResponse},
}


def _open_pair(files):
    """Open the first file and resize the second to match the first's size."""
    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)
    return image1, image2


@router.post(
    "/mask_image",
    response_class=StreamingResponse,
    responses=_MASK_RESPONSES,
)
async def mask_image(
    files: ValidatedImagePair,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    """Blend two images using a flat 50 %-opacity mask."""
    img_ext = get_image_extension(files[0])
    image1, image2 = _open_pair(files)
    mask = Image_PIL.new("L", image1.size, 128)
    composite = Image_PIL.composite(image1, image2, mask)
    buffer = save_image(composite, img_ext)
    return StreamingResponse(buffer, media_type=files[0].content_type)


@router.post(
    "/mask_image_drawing_circle",
    response_class=StreamingResponse,
    responses=_MASK_RESPONSES,
)
async def mask_image_by_drawing_circle(
    files: ValidatedImagePair,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    """Composite two images through an ellipse cutout."""
    img_ext = get_image_extension(files[0])
    image1, image2 = _open_pair(files)
    mask = Image_PIL.new("L", image1.size, 0)
    ImageDraw.Draw(mask).ellipse((140, 50, 260, 170), fill=255)
    composite = Image_PIL.composite(image1, image2, mask)
    buffer = save_image(composite, img_ext)
    return StreamingResponse(buffer, media_type=files[0].content_type)


@router.post(
    "/mask_image_drawing_blur_circle",
    response_class=StreamingResponse,
    responses=_MASK_RESPONSES,
)
async def mask_image_by_drawing_blur_circle(
    files: ValidatedImagePair,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    """Composite two images through a Gaussian-blurred ellipse."""
    img_ext = get_image_extension(files[0])
    image1, image2 = _open_pair(files)
    mask = Image_PIL.new("L", image1.size, 0)
    ImageDraw.Draw(mask).ellipse((140, 50, 260, 170), fill=255)
    blurred_mask = mask.filter(ImageFilter.GaussianBlur(10))
    composite = Image_PIL.composite(image1, image2, blurred_mask)
    buffer = save_image(composite, img_ext)
    return StreamingResponse(buffer, media_type=files[0].content_type)


@router.post(
    "/mask_image_existing_image",
    response_class=StreamingResponse,
    responses=_MASK_RESPONSES,
)
async def mask_image_with_existing_image(
    files: ValidatedImageTriplet,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    """Composite two images through a mask image supplied by the client."""
    img_ext = get_image_extension(files[0])
    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)
    mask = Image_PIL.open(files[2].file).convert("L").resize(image1.size)
    composite = Image_PIL.composite(image1, image2, mask)
    buffer = save_image(composite, img_ext)
    return StreamingResponse(buffer, media_type=files[0].content_type)
