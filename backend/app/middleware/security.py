import logging
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import time
from app.services.auth_service import AuthService
from app.services import get_auth_service # Import the dependency getter
import jwt

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
    auth_service: AuthService = Depends(get_auth_service), # Use the getter
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)) # Make Bearer optional
) -> Optional[str]:
    """Verify access token from cookie AND check CSRF header."""
    try:
        # --- Get Access Token (Cookie preferred) ---
        token = request.cookies.get("access_token")
        if not token and credentials:
            token = credentials.credentials
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token missing"
            )
        
        # --- Get CSRF Token from Header --- 
        csrf_token_header = request.headers.get("X-CSRF-Token")
        if not csrf_token_header:
             # Allow GET/HEAD requests without CSRF token for non-state changing actions
             # You might want to make this check more specific based on routes/methods
             if request.method not in ("GET", "HEAD", "OPTIONS"):
                 raise HTTPException(
                     status_code=status.HTTP_403_FORBIDDEN, # 403 Forbidden is more appropriate for CSRF failure
                     detail="Missing CSRF token header"
                 )
             # For GET/HEAD/OPTIONS, proceed without CSRF check (or pass None)
             csrf_token_header = None 

        # --- Verify the token AND CSRF --- 
        # Pass the CSRF token from header to the verification service
        user_id = auth_service.verify_token(token, request, csrf_token=csrf_token_header)
        request.state.user_id = user_id
        
        return token # Return the verified access token

    except jwt.ExpiredSignatureError: # Catch specific JWT errors if needed
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Token has expired"
         )
    except HTTPException as http_exc: # Re-raise existing HTTP exceptions
        raise http_exc
    except Exception as e:
        print(f"Token/CSRF Verification Error in Middleware: {type(e).__name__} - {str(e)}")
        # Generic error for security
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or CSRF validation failed"
        )
