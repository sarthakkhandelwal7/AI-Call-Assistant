import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import call_routes, ws_routes, auth_routes
from dotenv import load_dotenv

load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("FRONTEND_URL")],  # Your React frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Include routers
    app.include_router(call_routes.router)
    app.include_router(ws_routes.router)
    app.include_router(auth_routes.router)

    return app


app = create_app()
