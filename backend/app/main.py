import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import call_routes, ws_routes, auth_routes
from app.middleware.security import SecurityMiddleware
from dotenv import load_dotenv

load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Secretary API",
        description="API for AI-powered call screening system",
        version="1.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            os.getenv("FRONTEND_URL", "http://localhost:3001"), 
            "http://localhost:3000", 
            "http://localhost:3001", 
            "http://localhost:8000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )
        
    
    # Security middleware
    app.add_middleware(SecurityMiddleware)
    
    
    # Include routers
    app.include_router(auth_routes.router)
    app.include_router(call_routes.router)
    app.include_router(ws_routes.router)
    
    return app

app = create_app()

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"{request.method} {request.url.path} took {process_time:.2f}s")
    return response