from fastapi import APIRouter
from fastapi import HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse


from io import BytesIO

from PIL import ImageFilter, Image as Image_PIL

router = APIRouter(prefix='/filtering')

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