from fastapi import FastAPI

from src.api.v1 import api_router_v1
from src.core.logger import setup_logger


def create_app() -> FastAPI:
    app = FastAPI(
        title='Workout Recorder API',
        version='0.1.0',
        # (オプション) OpenAPIドキュメントのURLなどを設定
        # docs_url="/api/docs",
        # redoc_url="/api/redoc",
        # openapi_url="/api/v1/openapi.json"
    )
    setup_logger()

    app.include_router(api_router_v1, prefix='/api')

    @app.get('/')
    def read_root():
        return {'message': 'Welcome to Workout Recorder API!'}

    return app
