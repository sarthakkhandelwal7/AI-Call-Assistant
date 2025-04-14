import os
import time
# from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import call_routes, ws_routes, auth_routes, phone_number_routes, health_status, user_routes, verify_routes
from app.middleware.security import SecurityMiddleware
from app.core import get_settings
import logging
from app.logging_config import configure_logging

# Configure logging first
configure_logging()
logger = logging.getLogger(__name__)


def create_app():
    app = FastAPI(
        # lifespan=lifespan
    )
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.FRONTEND_URL
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )

    # Add security middleware
    app.add_middleware(SecurityMiddleware)

    # Include routers
    app.include_router(auth_routes.router)
    app.include_router(call_routes.router)
    app.include_router(health_status.router)
    app.include_router(ws_routes.router)
    app.include_router(phone_number_routes.router)
    app.include_router(user_routes.router)
    app.include_router(verify_routes.router)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"{request.method} {request.url.path} took {process_time:.2f}s")
        response.headers["X-Process-Time"] = str(process_time)
        return response

    @app.on_event("startup")
    async def startup_event():
        """Application startup events"""
        logger.info("✅ AI Secretary API is starting")
        logger.info("All routers and middleware configured")
        logger.info(f"CORS origins: {settings.FRONTEND_URL}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown events"""
        logger.info("🛑 AI Secretary API is shutting down")

    return app


app = create_app()

# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
