import json
from fastapi import APIRouter, Depends, WebSocket
import base64
import asyncio
from typing import List
import websockets
import os
from dotenv import load_dotenv

from backend.app.services.calendar_service import CalendarService
from backend.app.services.open_ai_service import OpenAiService
from backend.app.services.twilio_service import TwilioService

router = APIRouter()


@router.websocket("/audio-stream")
async def websocket_endpoint(
    ws: WebSocket,
    twilio_service: TwilioService = Depends(TwilioService.get_instance),
    calendar_service: CalendarService = Depends(CalendarService.get_instance),
) -> None:
    """Handle WebSocket connection"""
    await ws.accept()
    print("WebSocket connection established with Twilio")

    try:
        # Fetch stream SID from Twilio and saves both twilio ws and SID to TwilioService instance
        await twilio_service.fetch_stream_sid(ws)
        async with OpenAiService(
            twilio_service,
            calendar_service,
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
