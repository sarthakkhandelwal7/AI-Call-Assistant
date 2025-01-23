from fastapi import APIRouter, Depends, WebSocket
import base64
import asyncio
from typing import List
from sqlalchemy import select
import websockets
import os
from dotenv import load_dotenv

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.services.open_ai_service import OpenAiService
from backend.app.services.twilio_service import TwilioService
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.utils.calendar_events import get_calendar_events

router = APIRouter()


@router.websocket("/audio-stream")
async def websocket_endpoint(
    ws: WebSocket,
    twilio_service: TwilioService = Depends(TwilioService.get_instance),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Handle WebSocket connection"""
    await ws.accept()
    print("WebSocket connection established with Twilio")

    try:
        # Fetch stream SID from Twilio and saves both twilio ws and SID to TwilioService instance
        await twilio_service.fetch_stream_sid(ws)
        if not twilio_service.call_sid:
            await ws.close()
            return
        
        
        call_details = twilio_service.client.calls(twilio_service.call_sid).fetch()
        
        # The Twilio number that was dialed
        dialed_number = call_details.to
        result = await db.execute(
            select(User).filter(User.twilio_number == dialed_number)
        )
        
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"No user found for Twilio number: {dialed_number}")
            await ws.close()
            return
        
        events = await get_calendar_events(user)
        
        async with OpenAiService(
            twilio_service,
            events,
        ) as openai_service:

            await asyncio.gather(
                twilio_service.receive_audio(openai_ws=openai_service._ws),
                openai_service.receive_audio(),
            )

    except Exception as e:
        print(f"Error in websocket endpoint: {e}")

    finally:
        await ws.close()
        print("WebSocket connection closed")


router.add_api_websocket_route("/audio-stream", websocket_endpoint)
