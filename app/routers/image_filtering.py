from fastapi import APIRouter
from fastapi import UploadFile
from fastapi.responses import Response, StreamingResponse

from PIL import ImageFilter, Image as Image_PIL

from app.routers.util import get_image_extension, save_image
from app.routers.wrappers import verify_content_type


router = APIRouter(prefix='/filtering')


@router.post("/filter_blur", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def blur_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.BLUR)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_contour", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def contour_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.CONTOUR)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_detail", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def detail_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.DETAIL)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_edge_enhance", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def enhance_image_edges(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.EDGE_ENHANCE)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_edge_enhance_more", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def deeply_enhance_image_edges(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.EDGE_ENHANCE_MORE)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_emboss", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def emboss_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.EMBOSS)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_find_edges", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def find_image_edges(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.FIND_EDGES)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_smooth", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def smoth_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.SMOOTH)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_smooth_more", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def deeply_smoth_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.SMOOTH_MORE)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_sharpen", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def sharpen_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.SHARPEN)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_gaussian_blur", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def gaussian_blur_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.GaussianBlur)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)


@router.post("/filter_unsharp_mask", responses={200: {"content": {"image/png": {}}}}, response_class=Response)
@verify_content_type
async def unsharp_mask_image(file: UploadFile):
    # get image extension
    img_ext = get_image_extension(file)

    # open image
    original_image = Image_PIL.open(file.file)

    # apply filter
    original_image = original_image.filter(ImageFilter.UnsharpMask)

    # save image
    filtered_image = save_image(original_image, img_ext)

    return StreamingResponse(filtered_image, media_type=file.content_type)
