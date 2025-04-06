from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
import uuid 
from app.database import get_db
from app.models.user import User
from app.models.login import UpdateProfileRequest

from app.middleware.security import verify_token_middleware

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/user", 
    tags=["user"],
    dependencies=[Depends(verify_token_middleware)]
)


@router.put("/update-profile")
async def update_profile(
    request: Request, 
    update_data: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update user profile information"""
    try:
        user_id: uuid.UUID = getattr(request.state, "user_id", None)
        if not user_id:
            logger.error("User ID not found in request state after verify_token_middleware")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication context missing."
            )
        
        # Fetch user from DB using the user_id from middleware
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            # This case might occur if user was deleted between token generation and request
            logger.warning(f"User with ID {user_id} not found in database during profile update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )
        
        # Update user fields if provided in the request
        update_fields = update_data.model_dump(exclude_unset=True)
        if not update_fields:
            logger.info(f"No fields to update for user ID: {user_id}")
            # Return current user data if no updates provided
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
        
        for key, value in update_fields.items():
            setattr(user, key, value)
            
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User profile updated for user ID: {user.id}")
        
        # Return updated user data
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
        
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions directly
        raise http_exc
    except Exception as e:
        logger.error(f"Error updating profile for user ID {user_id if 'user_id' in locals() else 'unknown'}: {str(e)}")
        await db.rollback() # Rollback in case of other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        ) 