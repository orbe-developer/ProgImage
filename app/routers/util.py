"""Image-processing helpers shared by the processing/filtering/masking routers.

Validation helpers that used to live in ``wrappers.py`` and ``util.py``
have moved to ``app.dependencies`` (FastAPI Dependencies) and
``app.schemas`` (Pydantic ``Field`` constraints).
"""

from io import BytesIO, UnsupportedOperation

from fastapi import UploadFile


def get_image_extension(file: UploadFile) -> str:
    """Infer a Pillow-friendly extension from the UploadFile's content type."""
    content_type = file.content_type or ""
    slash_index = content_type.find("/")
    return content_type[slash_index + 1 :] if slash_index != -1 else "JPEG"


def save_image(pil_image, img_ext: str) -> BytesIO:
    """Serialise a PIL image to a BytesIO buffer at the start-of-stream."""
    buffer = BytesIO()
    pil_image.save(buffer, img_ext)

    try:
        buffer.seek(0)
    except (AttributeError, UnsupportedOperation):
        buffer = BytesIO(buffer.read())

    return buffer
