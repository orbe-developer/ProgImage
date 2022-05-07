from fastapi import APIRouter
from fastapi import HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse


from io import BytesIO

from PIL import ImageDraw, ImageFilter, Image as Image_PIL

router = APIRouter(prefix='/masking')


@router.post("/mask_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def mask_image(files: list[UploadFile]):
    """ if len(files) != 3:
        raise ValueError('You must send 3 images to mask.') """
    for file in files:
        if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
            raise HTTPException(
                status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    # get image extension
    content_type = files[0].content_type
    slash_index = content_type.find('/')
    img_ext = content_type[slash_index + 1:] if slash_index != -1 else "JPEG"
    print('EXTENSION', img_ext)

    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)

    mask = Image_PIL.new("L", image1.size, 128)
    im = Image_PIL.composite(image1, image2, mask)

    masked_image = BytesIO()
    im.save(masked_image, img_ext)
    masked_image.seek(0)

    return StreamingResponse(masked_image, media_type=content_type)


@router.post("/mask_image_drawing_circle", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def mask_image_by_drawing_circle(files: list[UploadFile]):
    """ if len(files) != 3:
        raise ValueError('You must send 3 images to mask.') """
    for file in files:
        if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
            raise HTTPException(
                status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    # get image extension
    content_type = files[0].content_type
    slash_index = content_type.find('/')
    img_ext = content_type[slash_index + 1:] if slash_index != -1 else "JPEG"
    print('EXTENSION', img_ext)

    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)

    mask = Image_PIL.new("L", image1.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((140, 50, 260, 170), fill=255)
    im = Image_PIL.composite(image1, image2, mask)

    masked_image = BytesIO()
    im.save(masked_image, img_ext)
    masked_image.seek(0)

    return StreamingResponse(masked_image, media_type=content_type)


@router.post("/mask_image_drawing_blur_circle", responses={200: {"content": {"image/png": {}}}},
             response_class=Response)
async def mask_image_by_drawing_blur_circle(files: list[UploadFile]):
    """ if len(files) != 3:
        raise ValueError('You must send 3 images to mask.') """
    for file in files:
        if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
            raise HTTPException(
                status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    # get image extension
    content_type = files[0].content_type
    slash_index = content_type.find('/')
    img_ext = content_type[slash_index + 1:] if slash_index != -1 else "JPEG"
    print('EXTENSION', img_ext)

    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)

    mask = Image_PIL.new("L", image1.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((140, 50, 260, 170), fill=255)
    im = Image_PIL.composite(image1, image2, mask)

    mask_blur = mask.filter(ImageFilter.GaussianBlur(10))
    im = Image_PIL.composite(image1, image2, mask_blur)

    mask_blur = BytesIO()
    im.save(mask_blur, img_ext)
    mask_blur.seek(0)

    return StreamingResponse(mask_blur, media_type=content_type)


@router.post("/mask_image_existing_image", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def mask_image_with_existing_image(files: list[UploadFile]):
    if len(files) != 3:
        raise HTTPException(status_code=400, detail='You must send 3 images to mask.')
    for file in files:
        if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
            raise HTTPException(
                status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    # get image extension
    content_type = files[0].content_type
    slash_index = content_type.find('/')
    img_ext = content_type[slash_index + 1:] if slash_index != -1 else "JPEG"
    print('EXTENSION', img_ext)

    image1 = Image_PIL.open(files[0].file)
    image2 = Image_PIL.open(files[1].file).resize(image1.size)

    mask = Image_PIL.open(files[2].file).convert('L').resize(image1.size)
    im = Image_PIL.composite(image1, image2, mask)

    masked_image = BytesIO()
    im.save(masked_image, img_ext)
    masked_image.seek(0)

    return StreamingResponse(masked_image, media_type=content_type)