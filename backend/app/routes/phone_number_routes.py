from typing import Optional
import uuid
from fastapi import APIRouter, Request, Response, Depends, HTTPException, middleware, status
from fastapi.responses import JSONResponse
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.middleware.security import verify_token_middleware
from app.models.user import User
from app.models.phone_number import BuyNumberRequest, BuyNumberResponse
from app.services.twilio_service import TwilioService
from app.services import get_twilio_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/phone-number", 
    tags=["phone-number"],
    dependencies=[Depends(verify_token_middleware)]
)

@router.get("/get-registered-twilio-number", response_model=dict)
async def get_twilio_number(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Check if the user has a Twilio number"""
    try:
        user_id: uuid.UUID = getattr(request.state, "user_id", None)
        if not user_id:
            logger.error("User ID not found in request state after verify_token_middleware")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication context missing."
            )

        logger.debug(f"Fetching registered Twilio number for User ID: {user_id}")
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            logger.warning(f"User {user_id} not found for get_registered_twilio_number")
            raise HTTPException(status_code=404, detail="User not found")
        
        return JSONResponse(content={"number": user.twilio_number})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error in get_registered_twilio_number for user {user_id if 'user_id' in locals() else 'unknown'}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/available-numbers")
async def get_available_numbers(
    request: Request,
    area_code: Optional[str] = None,
    twilio_service: TwilioService = Depends(get_twilio_service)
) -> JSONResponse:
    """Get available Twilio phone numbers that can be purchased"""
    try:
        if area_code:
            if not area_code.isdigit() or len(area_code) != 3:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Area code must be a 3-digit number"}
                )
        
        numbers = await twilio_service.get_available_numbers(area_code=area_code)
        if not numbers:
            return JSONResponse(
                status_code=404,
                content={"detail": "No available phone numbers found for this area code"}
            )
        return JSONResponse(content={"numbers": numbers})
    except HTTPException as http_exc:
         raise http_exc
    except Exception as e:
        logger.error(f"Error fetching available numbers (area code: {area_code}): {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error fetching phone numbers: {str(e)}"}
        )

@router.post("/buy-number")
async def buy_number(
    number_requested: BuyNumberRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    twilio_service: TwilioService = Depends(get_twilio_service)
) -> BuyNumberResponse:
    """
    Buys a new phone number using the Twilio service.
    """
    user_id: uuid.UUID = None
    try:
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            logger.error("User ID not found in request state after verify_token_middleware")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication context missing."
            )
            
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        number_to_buy = number_requested.number
        
        if not user:
             logger.error(f"User {user_id} not found in DB after successful Twilio purchase for {number_to_buy}. Refunding/Releasing number might be needed manually.")
             return BuyNumberResponse(success=False, message="User not found, number purchase failed internally.")
        
        if user.twilio_number:
            logger.warning(f"User {user_id} already has number {user.twilio_number}. Cannot assign new number {number_to_buy}. Refunding/Releasing might be needed manually.")
            return BuyNumberResponse(success=False, message="User already has an assigned number.")
        
        logger.info(f"User {user_id} attempting to buy number {number_requested.number}")
        
        
        resp = await twilio_service.buy_new_number(number_to_buy)

        if resp["status"] != 201:
             logger.warning(f"Twilio buy_new_number failed for user {user_id}, number {number_to_buy}: {resp.get('message')}")
             error_status = resp.get("status", 400)
             return BuyNumberResponse(success=False, message=resp.get("message", "Failed to purchase number from provider."))
        
        logger.info(f"Twilio purchase successful for number {number_to_buy} (SID: {resp.get('sid')})")
        

        user.twilio_number = number_to_buy
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Successfully assigned number {number_to_buy} to user {user_id}")
        return BuyNumberResponse(success=True, message=resp.get("message", "Number purchased and assigned successfully."))
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error buying number process for user {user_id if user_id else 'unknown'}: {e}", exc_info=True)
        await db.rollback()
        detail = getattr(e, 'detail', "Failed to purchase number due to an internal server error.")
        raise HTTPException(status_code=500, detail=str(detail))