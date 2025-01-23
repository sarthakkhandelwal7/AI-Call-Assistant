from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response, status
from sqlalchemy.orm import Session
from app.services.auth_service import AuthService
from app.database import get_db
from app.models.user import User
from app.models.login import GoogleLoginRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = AuthService()

from fastapi import Body  # Add this import

@router.post("/google-login")
async def google_auth(
    request: Request,
    response: Response,
    login_data: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Verify Google token and get user info
        user_data = await auth_service.verify_google_token(login_data.code)
        
        # Get or create user
        user = await auth_service.get_or_create_user(db, user_data)
        
        # Create access token with fingerprint
        access_token, expires, csrf_token = auth_service.create_access_token(user.id, request)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            expires=expires.timestamp(),
            httponly=True,
            secure=True,
            samesite="strict"
        )
        
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            expires=expires.timestamp(),
            secure=True,
            samesite="strict"
        )
        
        return {
            "message": "Successfully authenticated", 
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "profile_picture": user.profile_picture,
                "calendar_connected": user.calendar_connected
            }
        }
    except Exception as e:
        print(f"Authentication Error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/get-user-info")
async def get_current_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
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
                samesite="strict"
            )
            response.delete_cookie(
                key="csrf_token",
                secure=True,
                samesite="strict"
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
    db: AsyncSession = Depends(get_db)
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
            samesite="strict"
        )
        
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            expires=expires.timestamp(),
            secure=True,
            samesite="strict"
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
        samesite="strict"
    )
    response.delete_cookie(
        key="csrf_token",
        secure=True,
        samesite="strict"
    )
    return {"message": "Successfully logged out"}