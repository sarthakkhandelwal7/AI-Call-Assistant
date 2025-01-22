import os
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from app.services.twilio_service import TwilioService
from app.models.call import CallRequest, CallStatus
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/sms", tags=["sms"])


@router.post("/outbound")
async def handle_outbound_call(
    request: CallRequest,
    twilio_service: TwilioService = Depends(TwilioService.get_instance),
) -> Response:
    """Handle outgoing calls"""
    return Response(content="Call initiated", media_type="text/plain")


@router.post("/inbound")
async def handle_inbound_call(
    request: Request,
    twilio_service: TwilioService = Depends(TwilioService.get_instance),
) -> None:
    """Handle incoming calls from Twilio"""
    data = await request.form()
    print(data)
    


@router.get("/status")
async def get_call_status() -> JSONResponse:
    """Get current call status"""
    # print(f"call_status: {call_status.value}")
    return JSONResponse(
        status_code=200,
        content={"status": "Testing"},
        headers={"content-type": "application/json"},
    )
