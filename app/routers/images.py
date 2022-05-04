from typing import Optional
from fastapi import APIRouter
from ..database import Image
from fastapi import HTTPException, UploadFile, Form

from fastapi.responses import StreamingResponse, Response

from io import BytesIO
from PIL import ImageFilter, ImageDraw, Image as Image_PIL

router = APIRouter(prefix='/images')


@router.post("")
async def upload_file(file: UploadFile):
    # try:

    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    image_bytes = file.file.read()

    image_created = Image.create(
        image=image_bytes, content_type=file.content_type, description=file.filename)

    return image_created.id
    # except ValueError as e:
    # print(f'Error saving the image to the database: {e}')


@router.get("/{image_id}", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
def get_image(image_id: int):
    image = Image.select().where(Image.id == image_id).first()

    if image is None:
        raise HTTPException(
            status_code=404,
            detail=f'Image with id {image_id} does not exist.')

    # memoryview to bytes
    image_bytes = image.image.tobytes()

    return Response(content=image_bytes, media_type=image.content_type)


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


# ------------------------------ Masking images ------------------------------
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
    # im = Image_PIL.blend(image1, image2, 0.5)    

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


# ------------------------------Filters------------------------------

""" def filter_image(function):
    def wrapper(file):
        if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
            raise HTTPException(
                status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

        function(file)

        filtered_image = BytesIO()
        original_image.save(filtered_image, "JPEG")
        filtered_image.seek(0) """


@router.post("/filter_blur", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def blur_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.BLUR)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_contour", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def contour_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.CONTOUR)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_detail", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def detail_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.DETAIL)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_edge_enhance", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def enhance_image_edges(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.EDGE_ENHANCE)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_edge_enhance_more", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def deeply_enhance_image_edges(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.EDGE_ENHANCE_MORE)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_emboss", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def emboss_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.EMBOSS)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_find_edges", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def find_image_edges(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.FIND_EDGES)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_smooth", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def smoth_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.SMOOTH)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_smooth_more", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def deeply_smoth_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.SMOOTH_MORE)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_sharpen", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def sharpen_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.SHARPEN)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_gaussian_blur", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def gaussian_blur_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    # original_image = original_image.filter(ImageFilter.GaussianBlur(radius=10))
    original_image = original_image.filter(ImageFilter.GaussianBlur)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_unsharp_mask", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
async def unsharp_mask_image(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    original_image = Image_PIL.open(file.file)
    original_image = original_image.filter(ImageFilter.UnsharpMask)

    filtered_image = BytesIO()
    original_image.save(filtered_image, "JPEG")
    filtered_image.seek(0)

    return StreamingResponse(filtered_image, media_type=file.content_type)
