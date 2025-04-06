import logging
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import time
from app.services.auth_service import AuthService

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit_window = 60  # 1 minute
        self.max_requests = 100  # requests per minute
        self._requests = {}
        self.logger = logging.getLogger("SecurityMiddleware")

    async def dispatch(self, request: Request, call_next):
        try:
            # Rate limiting
            self.logger.info("Checking rate limit for request.")
            await self._check_rate_limit(request)
            
            # Process the request and get response
            self.logger.info("Processing request through call_next.")
            response = await call_next(request)
            
            # Add security headers
            self.logger.info("Adding security headers to response.")
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            return response
        except Exception as e:
            self.logger.error(f"Error in SecurityMiddleware: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred."
            )

    async def _check_rate_limit(self, request: Request):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self._requests = {
            ip: reqs for ip, reqs in self._requests.items()
            if current_time - reqs["window_start"] < self.rate_limit_window
        }
        
        # Check/update client's requests
        if client_ip not in self._requests:
            self._requests[client_ip] = {
                "window_start": current_time,
                "count": 1
            }
        else:
            if current_time - self._requests[client_ip]["window_start"] < self.rate_limit_window:
                self._requests[client_ip]["count"] += 1
                if self._requests[client_ip]["count"] > self.max_requests:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests"
                    )
            else:
                self._requests[client_ip] = {
                    "window_start": current_time,
                    "count": 1
                }
                

async def verify_token_middleware(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer),
    auth_service: AuthService = Depends(AuthService)
) -> Optional[str]:
    """Verify access token from cookie or Authorization header"""
    try:
        # First try to get token from cookie
        token = request.cookies.get("access_token")
        print(f"Token from cookie: {token}")
        
        
        # If no cookie, check Authorization header
        if not token and credentials:
            token = credentials.credentials
        
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
            
        # Verify the token
        user_id = auth_service.verify_token(token, request)
        request.state.user_id = user_id
        
        return token
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

# async def verify_token_middleware2(
#     request: Request,
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):
#     """Dummy middleware for token verification"""
#     # This is just a placeholder. Actual implementation should be done in the routes.
#     token = request.cookies.get("access_token")
#     print(f"Token from cookie: {token}")