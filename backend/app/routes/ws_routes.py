from fastapi import APIRouter, Depends, WebSocket
import base64
import asyncio
from typing import List
from sqlalchemy import select
import websockets
import os
from dotenv import load_dotenv

from app.database import get_db
from app.models.user import User
from app.services.open_ai_service import OpenAiService
from app.services.twilio_service import TwilioService
from app.utils.calendar_events import get_calendar_events
from sqlalchemy.ext.asyncio import AsyncSession
from app.sessions.user_sessions import sessions
from app.services import get_twilio_service, get_open_ai_service
from backend.app.models import user

router = APIRouter()


@router.websocket("/audio-stream")
async def websocket_endpoint(
    ws: WebSocket,
    twilio_service: TwilioService = Depends(get_twilio_service),
    openai_service: OpenAiService = Depends(get_open_ai_service),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Handle WebSocket connection"""
    await ws.accept()
    print("WebSocket connection established with Twilio")

    try:
        user_id = await twilio_service.fetch_user_id(ws)
        session = sessions.get(user_id, None)
        if session is None:
            await ws.close()
            raise Exception("Session not found")
        
        async with session:            
            session.twilio_ws = ws
            session.openai_ws = await openai_service.connect()
                        
            session.calendar_events = await get_calendar_events(session.user)
            await openai_service.start_session(ws=session.openai_ws, events=session.calendar_events)
            
            
            await asyncio.gather(
                twilio_service.receive_audio(twilio_ws=session.twilio_ws, openai_ws=session.openai_ws),
                openai_service.receive_audio(openai_ws=session.openai_ws, 
                                             twilio_ws=session.twilio_ws, 
                                             stream_sid=session.stream_sid),
            )

    except Exception as e:
        print(f"Error in websocket endpoint: {e}")

    finally:
        await ws.close()
        print("WebSocket connection closed")


router.add_api_websocket_route("/audio-stream", websocket_endpoint)
