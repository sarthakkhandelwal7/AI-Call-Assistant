from typing import Optional
from fastapi import APIRouter, Request, Response, Depends, HTTPException, middleware
from fastapi.responses import JSONResponse
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.middleware.security import verify_token_middleware
from app.models.user import User
from app.models.phone_number import BuyNumberRequest, BuyNumberResponse
from app.services.twilio_service import TwilioService
from backend.app.services.auth_service import AuthService
from app.services import get_twilio_service
import logging

logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/phone-number", tags=["phone-number"], dependencies=[Depends(verify_token_middleware)])
router = APIRouter(prefix="/phone-number", tags=["phone-number"])

@router.get("/get-registered-twilio-number", response_model=dict)
async def get_twilio_number(request: Request,
                      db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Check if the user has a Twilio number"""
    token = request.cookies.get("access_token")
    auth_service = AuthService()
    user_id = auth_service.verify_token(token, request)
    # user_id = request.state.user_id
    print(f"User ID: {user_id}")
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return JSONResponse(content={"has_twilio_number": user.twilio_number})


@router.get("/available-numbers")
async def get_available_numbers(
    request: Request,
    area_code: Optional[str] = "US",
    db: AsyncSession = Depends(get_db),
    twilio_service: TwilioService = Depends(get_twilio_service)
) -> JSONResponse:
    """Get available Twilio phone numbers that can be purchased"""
    try:
        numbers = await twilio_service.get_available_numbers(area_code=area_code)
        if not numbers:
            return JSONResponse(
                status_code=404,
                content={"detail": "No available phone numbers found"}
            )
        return JSONResponse(content={"numbers": numbers})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error fetching phone numbers: {str(e)}"}
        )

@router.post("/buy-number", )
async def buy_number(
    number_requested: BuyNumberRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    twilio_service: TwilioService = Depends(get_twilio_service)
) -> BuyNumberResponse:
    """
        Buys a new phone number using the Twilio service.
    """
    try:
        number = number_requested.number
        resp = await twilio_service.buy_new_number(number)
        if resp["status"] != 200:
            return BuyNumberResponse(success=False, message=resp["message"])
        token = request.cookies.get("access_token")
        auth_service = AuthService()
        user_id = auth_service.verify_token(token, request)
        await db.execute(
            User.update().where(User.id == user_id).values(twilio_number=number)
        )
        await db.commit()
        return BuyNumberResponse(success=True, message=resp["message"])
    except Exception as e:
        logger.error(f"Exception occurred: {e.detail}")
        raise
    
    
