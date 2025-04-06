import os
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from app.services.twilio_service import TwilioService
from app.models.call import CallRequest, CallStatus
from app.sessions.user_sessions import sessions, UserSession
from sqlalchemy.future import select
from app.models.user import User
from app.services import get_twilio_service
from app.core import get_settings, Settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/calls", tags=["calls"])
# call_status = CallStatus.NO_CURRENT_CALL


@router.post("/calls/outbound")
async def handle_outbound_call(
    request: CallRequest,
    twilio_service: TwilioService = Depends(get_twilio_service),
) -> Response:
    """Handle outgoing calls"""
    return Response(content="Call initiated", media_type="text/plain")


@router.post("/inbound", response_model=None)
async def handle_inbound_call(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Handle incoming calls from Twilio"""
    # global call_status
    # call_status = CallStatus.IN_PROGRESS
    request = await request.form()  # returns a corutine so await it
    from_number = request.get("From")
    twilio_number = request.get("To")
    STREAM_URL = settings.STREAM_URL
    result = await db.execute(
        select(User).filter(User.twilio_number == twilio_number)
    )
    user = result.scalar_one_or_none()    
    if not user:
        return Response(content="User not found", media_type="text/plain")
    
    UserSession(user.id, user, from_number)
    twilML_response = f"""
        <Response>
                <Connect>
                    <Stream url="{STREAM_URL}">
                    <Parameter name="user_id" value="{user.id}"/>
                    </Stream>
                </Connect>
            </Response>
    """

    return Response(content=twilML_response, media_type="application/xml")


# @router.get("/status")
# async def get_call_status() -> JSONResponse:
#     """Get current call status"""
#     print(f"call_status: {call_status.value}")
#     return JSONResponse(
#         status_code=200,
#         content={"status": call_status.value},
#         headers={"content-type": "application/json"},
#     )
