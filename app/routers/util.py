from fastapi import HTTPException, UploadFile
from io import BytesIO, UnsupportedOperation


def verify_image_content_type(file: UploadFile):
    if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png', ]:
        raise HTTPException(
            status_code=406,
            detail="Only '.jpg', '.jpeg' or '.png' files allowed."
        )


def verify_images_content_type(files: list[UploadFile]):
    for file in files:
        if file.content_type not in ['image/jpg', 'image/jpeg', 'image/png', ]:
            raise HTTPException(
                status_code=406,
                detail="Only '.jpg', '.jpeg' or '.png' files allowed."
            )


def verify_number_of_images(files: list[UploadFile]):
    if len(files) != 2:
        raise HTTPException(
            status_code=400,
            detail='You must send 2 images to mask.'
        )


def verify_image_dimesions(width: int, height: int):
    if width < 0 or height < 0:
        raise HTTPException(
            status_code=400, detail='width and height must be > 0')


def get_image_extension(file: UploadFile):
    content_type = file.content_type
    slash_index = content_type.find('/')
    img_ext = content_type[slash_index + 1:] if slash_index != -1 else "JPEG"
    return img_ext


def save_image(original_image, img_ext):
    processed_image = BytesIO()
    original_image.save(processed_image, img_ext)

    try:
        processed_image.seek(0)
    except (AttributeError, UnsupportedOperation):
        processed_image = BytesIO(processed_image.read())

    return processed_image
