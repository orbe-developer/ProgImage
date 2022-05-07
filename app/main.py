from fastapi import FastAPI
from fastapi import APIRouter

from .database import Image, pg_db as connection
from .routers.images import router as image_router
from .routers.image_processing import router as image_processing
from .routers.image_filtering import router as image_filtering
from .routers.image_masking import router as image_masking



app = FastAPI(title='ProgImage', description=f'''ProgImage is a specialized service that offers image storage and retrieval. 
                                                \nIt also provides a number of image processing and transformation capabilities 
                                                such as compression, rotation, a variety of filters, thumbnail creation, and masking.''',
              version='1')

api_v1 = APIRouter(prefix='/api/v1')

api_v1.include_router(image_router, prefix="", tags=["images"],)
api_v1.include_router(image_processing, prefix="/images", tags=["image_processing"])
api_v1.include_router(image_filtering, prefix="/images", tags=["image_filtering"])
api_v1.include_router(image_masking, prefix="/images", tags=["image_masking"])

app.include_router(api_v1)


@app.on_event('startup')
def startup():
    '''
    Run before the server starts
    '''
    # print('The server is starting.')
    if connection.is_closed():
        connection.connect()

    connection.create_tables([Image])


@app.on_event('shutdown')
def shutdown():
    '''
    Run before the server stops
    '''
    # print('The server is shutting down.')
    if not connection.is_closed():
        connection.close()
