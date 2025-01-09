from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import call_routes, ws_routes

# from .config import Settings


def create_app() -> FastAPI:
    app = FastAPI()

    # Include routers
    app.include_router(ws_routes.router)

    return app


app = create_app()
