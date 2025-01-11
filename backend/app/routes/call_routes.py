import os
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from app.services.twilio_service import TwilioService
from app.models.call import CallRequest, CallStatus
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/calls", tags=["calls"])
call_status = CallStatus.NO_CURRENT_CALL


@router.post("/calls/outbound")
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
) -> Response:
    """Handle incoming calls from Twilio"""
    global call_status
    call_status = CallStatus.IN_PROGRESS
    request = await request.form()  # returns a corutine so await it
    twilio_service.phone_number = request["From"]
    STREAM_URL = os.getenv("STREAM_URL")
    print(f"Received a call from_number: {twilio_service.phone_number}")

    twilML_response = f"""
        <Response>
                <Connect>
                    <Stream url="{STREAM_URL}">
                    </Stream>
                </Connect>
            </Response>
    """

    return Response(content=twilML_response, media_type="application/xml")


@router.get("/status")
async def get_call_status() -> JSONResponse:
    """Get current call status"""
    print(f"call_status: {call_status.value}")
    return JSONResponse(
        status_code=200,
        content={"status": call_status.value},
        headers={"content-type": "application/json"},
    )
