from fastapi import APIRouter
from fastapi import HTTPException, UploadFile, Form

from fastapi.responses import Response, StreamingResponse

from io import BytesIO

from PIL import Image as Image_PIL

from typing import Optional

router = APIRouter(prefix='/processing')

@router.post("/compress_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def compress_image(file: UploadFile, width: int, height: int):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png', ]:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    if width < 0 or height < 0:
        raise HTTPException(
            status_code=400, detail='width and height must be > 0')

    original_image = Image_PIL.open(file.file)

    # get image extension
    content_type = file.content_type
    slash_index = content_type.find('/')
    img_ext = content_type[slash_index + 1:] if slash_index != -1 else "JPEG"

    # get dimensions
    if width == 0 and height == 0:
        width, height = original_image.size

    # compress image
    original_image = original_image.resize(size=(width, height))

    compressed_image = BytesIO()
    original_image.save(compressed_image, img_ext)
    # original_image.save(compressed_image, img_ext, quality=95)
    compressed_image.seek(0)

    return StreamingResponse(compressed_image, media_type=file.content_type)


@router.post("/rotate_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def rotate_image(file: UploadFile, angle: int, expand: Optional[bool] = Form(None)):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    # get image extension
    content_type = file.content_type
    slash_index = content_type.find('/')
    img_ext = content_type[slash_index + 1:] if slash_index != -1 else "JPEG"

    # open the image
    original_image = Image_PIL.open(file.file)

    # rotate image
    original_image = original_image.rotate(angle, expand=expand)

    rotated_image = BytesIO()
    original_image.save(rotated_image, img_ext)
    rotated_image.seek(0)

    return StreamingResponse(rotated_image, media_type=file.content_type)


@router.post("/thumbnail_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def make_thumbnail_of_image(file: UploadFile, width: int, height: int):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    if width < 0 or height < 0:
        raise HTTPException(
            status_code=400, detail='width and height must be > 0')

    # get image extension
    content_type = file.content_type
    slash_index = content_type.find('/')
    img_ext = content_type[slash_index + 1:] if slash_index != -1 else "JPEG"

    # open the image
    original_image = Image_PIL.open(file.file)

    # get dimensions
    if width == 0 and height == 0:
        width, height = original_image.size

    # thumbnail image
    original_image.thumbnail((width, height))
    original_image.save(file.filename)

    thumbnail_image = BytesIO()
    original_image.save(thumbnail_image, img_ext)
    thumbnail_image.seek(0)

    return StreamingResponse(thumbnail_image, media_type=file.content_type)