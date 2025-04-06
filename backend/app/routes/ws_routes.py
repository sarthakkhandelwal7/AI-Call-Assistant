from fastapi import APIRouter, Depends, WebSocket
import base64
import asyncio
from typing import List
from sqlalchemy import select
import websockets
import os
import uuid
import logging

from app.database import get_db, get_db_context
from app.models.user import User
from app.services.open_ai_service import OpenAiService
from app.services.twilio_service import TwilioService
from app.utils.calendar_events import get_calendar_events
from sqlalchemy.ext.asyncio import AsyncSession
from app.sessions.user_sessions import sessions, UserSession
from app.services import get_twilio_service, get_open_ai_service
from app.models import user

router = APIRouter()
logger = logging.getLogger("ws_routes")


@router.websocket("/audio-stream")
async def websocket_endpoint(
    ws: WebSocket,
    twilio_service: TwilioService = Depends(get_twilio_service),
    openai_service: OpenAiService = Depends(get_open_ai_service),
) -> None:
    """Handle WebSocket connection"""
    await ws.accept()
    logger.info("WebSocket connection established with Twilio")
    
    # Use our context manager for database access to ensure connection is closed
    async with get_db_context() as db:
        try:
            # Get the user ID from the WebSocket
            user_id = await twilio_service.fetch_user_id(ws)
            session = sessions.get(user_id, None)
            if session is None:
                await ws.close()
                raise Exception("Session not found")
            
            # Explicitly commit any database changes before proceeding with long operations
            await db.commit()
            
            async with session:            
                session.twilio_ws = ws
                session.openai_ws = await openai_service.connect()
                            
                session.calendar_events = await get_calendar_events(session.user)
                await openai_service.start_session(ws=session.openai_ws, events=session.calendar_events)
                
                await asyncio.gather(
                    twilio_service.receive_audio(twilio_ws=session.twilio_ws, openai_ws=session.openai_ws),
                    openai_service.receive_audio(session)
                )

        except Exception as e:
            logger.error(f"Error in websocket endpoint: {e}")
            # Make sure to rollback in case of error
            await db.rollback()

        finally:
            # ws.state.value == 1 wont work as application gets disconnected so have to check application_state.value
            if ws.application_state.value == 1:
                await ws.close()
            logger.info("All WebSockets connections are closed")


router.add_api_websocket_route("/audio-stream", websocket_endpoint)
