"""Image filtering endpoints.

Twelve filters share the same shape: validate content type, open the
file with Pillow, apply the filter, stream the bytes back. A helper
collapses the duplication while keeping each public endpoint explicit
in OpenAPI.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from PIL import ImageFilter, Image as Image_PIL
from PIL.ImageFile import ImageFile

from app.auth.dependencies import get_current_user
from app.dependencies import ValidatedImage
from app.models.user import User
from app.routers.util import get_image_extension, save_image
from app.schemas import ErrorResponse

router = APIRouter(prefix="/filtering")

_FILTER_RESPONSES = {
    200: {"content": {"image/png": {}, "image/jpeg": {}}},
    401: {"model": ErrorResponse},
    406: {"model": ErrorResponse},
}


def _apply(file, pil_filter: ImageFilter.Filter | type[ImageFilter.Filter]) -> StreamingResponse:
    """Open the UploadFile, apply the given Pillow filter, stream result."""
    img_ext = get_image_extension(file)
    original: ImageFile = Image_PIL.open(file.file)
    filtered = original.filter(pil_filter)
    buffer = save_image(filtered, img_ext)
    return StreamingResponse(buffer, media_type=file.content_type)


@router.post("/filter_blur", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def blur_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.BLUR)


@router.post("/filter_contour", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def contour_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.CONTOUR)


@router.post("/filter_detail", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def detail_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.DETAIL)


@router.post("/filter_edge_enhance", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def enhance_image_edges(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.EDGE_ENHANCE)


@router.post("/filter_edge_enhance_more", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def deeply_enhance_image_edges(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.EDGE_ENHANCE_MORE)


@router.post("/filter_emboss", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def emboss_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.EMBOSS)


@router.post("/filter_find_edges", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def find_image_edges(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.FIND_EDGES)


@router.post("/filter_smooth", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def smooth_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.SMOOTH)


@router.post("/filter_smooth_more", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def deeply_smooth_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.SMOOTH_MORE)


@router.post("/filter_sharpen", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def sharpen_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.SHARPEN)


@router.post("/filter_gaussian_blur", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def gaussian_blur_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.GaussianBlur())


@router.post("/filter_unsharp_mask", response_class=StreamingResponse, responses=_FILTER_RESPONSES)
async def unsharp_mask_image(
    file: ValidatedImage,
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    return _apply(file, ImageFilter.UnsharpMask())
