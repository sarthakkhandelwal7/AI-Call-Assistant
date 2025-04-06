import os
import time
# from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import call_routes, ws_routes, auth_routes, phone_number_routes
from app.middleware.security import SecurityMiddleware
from app.core import get_settings


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("✅ AI Secretary API is starting")
#     yield
#     print("🛑 AI Secretary API is shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AI Secretary API",
        description="API for AI-powered call screening system",
        version="1.0.0",
        # lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.FRONTEND_URL,
            "http://localhost:3500",
            "http://localhost:8000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )

    app.add_middleware(SecurityMiddleware)

    app.include_router(auth_routes.router)
    app.include_router(call_routes.router)
    app.include_router(ws_routes.router)
    app.include_router(phone_number_routes.router)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"{request.method} {request.url.path} took {process_time:.2f}s")
        return response

    return app


app = create_app()
