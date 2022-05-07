from fastapi import APIRouter
from fastapi import HTTPException, UploadFile
from fastapi.responses import Response

from ..database import Image


router = APIRouter(prefix='/images')


@router.post("")
async def upload_image(file: UploadFile):

    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=406, detail="Only '.jpg', '.jpeg' or '.png' files allowed.")

    image_bytes = file.file.read()

    image_created = Image.create(
        image=image_bytes, content_type=file.content_type, description=file.filename)

    return image_created.id


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