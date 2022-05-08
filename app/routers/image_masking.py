from fastapi import APIRouter
from fastapi import HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse


from io import BytesIO

from PIL import ImageDraw, ImageFilter, Image as Image_PIL

from app.routers.util import get_image_extension, save_image
from app.routers.wrappers import verify_content_types, verify_number_images

router = APIRouter(prefix='/masking')


@router.post("/mask_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_types
@verify_number_images
async def mask_image(files: list[UploadFile]):

    # get image extension
    img_ext = get_image_extension(files[0])

    # open image
    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)

    # mask image
    mask = Image_PIL.new("L", image1.size, 128)
    im = Image_PIL.composite(image1, image2, mask)

    # save image
    masked_image = save_image(im, img_ext)

    return StreamingResponse(masked_image, media_type=files[0].content_type)


@router.post("/mask_image_drawing_circle", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_types
@verify_number_images
async def mask_image_by_drawing_circle(files: list[UploadFile]):

    # get image extension
    img_ext = get_image_extension(files[0])

    # open image
    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)

    # mask image
    mask = Image_PIL.new("L", image1.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((140, 50, 260, 170), fill=255)
    im = Image_PIL.composite(image1, image2, mask)

    # save image
    masked_image = save_image(im, img_ext)

    return StreamingResponse(masked_image, media_type=files[0].content_type)


@router.post("/mask_image_drawing_blur_circle", responses={200: {"content": {"image/png": {}}}},
             response_class=Response)
@verify_content_types
@verify_number_images
async def mask_image_by_drawing_blur_circle(files: list[UploadFile]):
    # get image extension
    img_ext = get_image_extension(files[0])

    # open image
    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)

    # mask image
    mask = Image_PIL.new("L", image1.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((140, 50, 260, 170), fill=255)
    im = Image_PIL.composite(image1, image2, mask)

    mask_blur = mask.filter(ImageFilter.GaussianBlur(10))
    im = Image_PIL.composite(image1, image2, mask_blur)

    # save image
    masked_image = save_image(im, img_ext)

    return StreamingResponse(masked_image, media_type=files[0].content_type)


@router.post("/mask_image_existing_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_types
async def mask_image_with_existing_image(files: list[UploadFile]):
    if len(files) != 3:
        raise HTTPException(
            status_code=400, detail='You must send 3 images to mask.')

    # get image extension
    img_ext = get_image_extension(files[0])

    # open image
    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)

    mask = Image_PIL.open(files[2].file).convert('L').resize(image1.size)
    im = Image_PIL.composite(image1, image2, mask)

   # save image
    masked_image = save_image(im, img_ext)

    return StreamingResponse(masked_image, media_type=files[0].content_type)
