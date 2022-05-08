
from functools import wraps

from app.routers.util import verify_image_content_type, verify_images_content_type, verify_image_dimesions, verify_number_of_images


def verify_content_type(function):

    @wraps(function)
    async def wrapper(file, *args, **kwargs):
        verify_image_content_type(file)

        return await function(file, *args, **kwargs)

    return wrapper


def verify_content_types(function):

    @wraps(function)
    async def wrapper(files, *args, **kwargs):
        verify_images_content_type(files)

        return await function(files, *args, **kwargs)

    return wrapper


def verify_dimensions(function):

    @wraps(function)
    async def wrapper(file, width, height):
        verify_image_dimesions(width, height)

        return await function(file, width, height)

    return wrapper


def verify_number_images(function):

    @wraps(function)
    async def wrapper(files):
        verify_number_of_images(files)

        return await function(files)

    return wrapper
