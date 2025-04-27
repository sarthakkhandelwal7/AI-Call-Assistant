from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response, status
from app.services import get_auth_service
from app.database import get_db
from app.models.user import User
from app.models.login import GoogleLoginRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/google-login")
async def google_auth(
    request: Request,
    response: Response,
    login_data: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service = Depends(get_auth_service)
):
    logger.info(f"Received /google-login request. login_data: {login_data}")
    try:
        # Verify Google token and get user info
        logger.debug("Attempting to verify Google token with code...")
        user_data = await auth_service.verify_google_token(login_data.code)
        logger.debug(f"Google token verified. User data: {user_data}")
        
        # Get or create user
        logger.debug("Attempting to get or create user...")
        user = await auth_service.get_or_create_user(db, user_data)
        logger.debug(f"User retrieved/created: {user.id}")
        
        # Create access token with fingerprint
        access_token, expires, csrf_token = auth_service.create_access_token(user.id, request)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            expires=expires.timestamp(),
            httponly=True,
            secure=True,
            samesite="None"
        )
        
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            expires=expires.timestamp(),
            httponly=False,
            secure=True,
            samesite="None"
        )
        
        return {
            "message": "Successfully authenticated", 
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "profile_picture": user.profile_picture,
                "calendar_connected": user.calendar_connected
            },
            "csrf_token": csrf_token
        }
    except HTTPException as http_exc:
        logger.error(f"HTTPException during Google auth: {http_exc.status_code} - {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Authentication Error: {type(e).__name__} - {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed due to an internal error."
        )

@router.get("/get-user-info")
async def get_current_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    auth_service = Depends(get_auth_service)
):
    try:
        # Get token from cookies
        token = request.cookies.get("access_token")
        print(f"Received token: {token}")
        
        if not token:
            raise HTTPException(
                status_code=401, 
                detail="No authentication token found"
            )
        
        # Verify token and get user ID
        user_id = auth_service.verify_token(token, request)
        print(f"Extracted User ID: {user_id}")
        
        # Use async query
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            # Clear the invalid cookie
            response.delete_cookie(
                key="access_token",
                httponly=True,
                secure=True,
                samesite="None"
            )
            response.delete_cookie(
                key="csrf_token",
                httponly=False,
                secure=True,
                samesite="None"
            )
            
            raise HTTPException(
                status_code=401, 
                detail="User no longer exists. Please log in again."
            )
        
        # Return user data
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "profile_picture": user.profile_picture,
            "calendar_connected": user.calendar_connected,
            "timezone": user.timezone,
            "twilio_number": user.twilio_number,
            "user_number": user.user_number,
        }
    except Exception as e:
        print(f"Get User Info Error: {type(e).__name__}: {str(e)}")
        raise


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    auth_service = Depends(get_auth_service)
):
    """Get new access token using stored refresh token"""
    try:
        expired_token = request.cookies.get("access_token")
        if not expired_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token found"
            )
        
        user_id = auth_service.verify_token(expired_token, request)
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        access_token, expires, csrf_token = auth_service.create_access_token(user.id, request)
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            expires=expires.timestamp(),
            httponly=True,
            secure=True,
            samesite="None"
        )
        
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            expires=expires.timestamp(),
            httponly=False,
            secure=True,
            samesite="None"
        )
        
        return {"message": "Token refreshed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout")
async def logout(response: Response):
    """Clear authentication cookies"""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="None"
    )
    response.delete_cookie(
        key="csrf_token",
        httponly=False,
        secure=True,
        samesite="None"
    )
    return {"message": "Successfully logged out"}