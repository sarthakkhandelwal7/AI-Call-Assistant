import os
import logging
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
from app.database import get_db, get_db_context

router = APIRouter(prefix="/calls", tags=["calls"])
logger = logging.getLogger("call_routes")
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
    settings: Settings = Depends(get_settings),
) -> Response:
    """Handle incoming calls from Twilio"""
    # global call_status
    # call_status = CallStatus.IN_PROGRESS
    async with get_db_context() as db:
        try:
            request_form = await request.form()  # returns a coroutine so await it
            from_number = request_form.get("From")
            twilio_number = request_form.get("To")
            STREAM_URL = settings.STREAM_URL
            
            logger.info(f"Inbound call from {from_number} to {twilio_number}")
            
            result = await db.execute(
                select(User).filter(User.twilio_number == twilio_number)
            )
            user = result.scalar_one_or_none()    
            if not user:
                logger.warning(f"User not found for Twilio number: {twilio_number}")
                return Response(content="User not found", media_type="text/plain")
            
            # Create and store session
            session = UserSession(user.id, user, from_number)
            
            # Commit any changes and ensure connection is returned to pool
            await db.commit()
            
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
        except Exception as e:
            logger.error(f"Error in inbound call handler: {str(e)}")
            await db.rollback()  # Make sure to rollback in case of error
            return Response(content=f"Error: {str(e)}", status_code=500)


# @router.get("/status")
# async def get_call_status() -> JSONResponse:
#     """Get current call status"""
#     print(f"call_status: {call_status.value}")
#     return JSONResponse(
#         status_code=200,
#         content={"status": call_status.value},
#         headers={"content-type": "application/json"},
#     )
