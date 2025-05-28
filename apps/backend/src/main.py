from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="My FastAPI Application")

    @app.get("/")
    async def read_root():
        return {"message": "Welcome to My FastAPI Application"}

    return app
