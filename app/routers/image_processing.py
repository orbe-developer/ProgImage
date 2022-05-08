from fastapi import APIRouter
from fastapi import UploadFile, Form

from fastapi.responses import Response, StreamingResponse

from PIL import Image as Image_PIL

from typing import Optional

from app.routers.util import get_image_extension, save_image
from app.routers.wrappers import verify_content_type, verify_dimensions


router = APIRouter(prefix='/processing')


@router.post("/compress_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
@verify_dimensions
async def compress_image(file: UploadFile, width: int, height: int):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # get dimensions
    if width == 0 and height == 0:
        width, height = original_image.size

    # compress image
    original_image = original_image.resize(size=(width, height))

    # save image
    compressed_image = save_image(original_image, img_ext)

    # original_image.save(compressed_image, img_ext, quality=95)

    return StreamingResponse(compressed_image, media_type=file.content_type)


@router.post("/rotate_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def rotate_image(file: UploadFile, angle: int, expand: Optional[bool] = Form(None)):

    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # rotate image
    original_image = original_image.rotate(angle, expand=expand)

    # save image
    rotated_image = save_image(original_image, img_ext)

    return StreamingResponse(rotated_image, media_type=file.content_type)


@router.post("/thumbnail_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
@verify_dimensions
async def make_thumbnail_of_image(file: UploadFile, width: int, height: int):

    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # get dimensions
    if width == 0 and height == 0:
        width, height = original_image.size

    # thumbnail image
    original_image.thumbnail((width, height))
    original_image.save(file.filename)

    # save image
    thumbnail_image = save_image(original_image, img_ext)

    return StreamingResponse(thumbnail_image, media_type=file.content_type)
