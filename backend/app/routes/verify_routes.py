from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
import logging

from app.services import get_twilio_service
from app.services.twilio_service import TwilioService
from app.middleware.security import verify_token_middleware
from app.models.phone_number import CheckOtpRequest, SendOtpRequest 

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/verify", 
    tags=["verification"],
    dependencies=[Depends(verify_token_middleware)] # Secure these endpoints
)

@router.post("/send-otp")
async def send_otp(
    request_data: SendOtpRequest,
    twilio_service: TwilioService = Depends(get_twilio_service)
):
    """Sends a verification OTP to the provided phone number."""
    try:
        # Basic validation could be added here (e.g., regex for E.164)
        result = await twilio_service.send_verification_otp(request_data.phone_number)
        return {"message": "OTP sent successfully.", "status": result.get("status", "unknown")}
    except HTTPException as http_exc:
        raise http_exc # Re-raise exceptions from the service layer
    except Exception as e:
        logger.error(f"Error in send_otp endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send OTP.")

@router.post("/check-otp")
async def check_otp(
    request_data: CheckOtpRequest,
    twilio_service: TwilioService = Depends(get_twilio_service)
):
    """Checks the verification OTP entered by the user."""
    try:
        result = await twilio_service.check_verification_otp(
            phone_number=request_data.phone_number, 
            code=request_data.code
        )
        
        is_approved = result.get("status") == "approved" and result.get("valid") is True
        
        if is_approved:
            return {"message": "Verification successful.", "verified": True}
        else:
            # Provide a generic failure message unless Twilio gave a specific one
            error_message = result.get("message", "Verification failed. Invalid or expired code.")
            raise HTTPException(status_code=400, detail=error_message)
            
    except HTTPException as http_exc:
        raise http_exc # Re-raise exceptions from the service layer
    except Exception as e:
        logger.error(f"Error in check_otp endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to check OTP.") 