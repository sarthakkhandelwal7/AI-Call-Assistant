import json
from fastapi import APIRouter, Depends, WebSocket
import base64
import asyncio
from typing import List
import websockets
import os
from dotenv import load_dotenv

from backend.app.services.open_ai_service import OpenAiService
from backend.app.services.twilio_service import TwilioService

router = APIRouter()


@router.websocket("/audio-stream")
async def websocket_endpoint(
    ws: WebSocket,
    twilio_service: TwilioService = Depends(TwilioService.get_instance),
) -> None:
    """Handle WebSocket connection"""
    await ws.accept()
    print("WebSocket connection established with Twilio")

    try:
        async with OpenAiService() as openai_service:
            await twilio_service.receive_audio_start(ws)
            openai_service.stream_sid = twilio_service.stream_sid

            await asyncio.gather(
                twilio_service.receive_audio(ws, openai_ws=openai_service._ws),
                openai_service.receive_audio(ws),
            )

    except Exception as e:
        print(f"Error in websocket endpoint: {e}")

    finally:
        await ws.close()
        print("WebSocket connection closed")
        if openai_service and openai_service._ws.state == 1:
            await openai_service.close()
            print("OpenAI WebSocket connection closed")


router.add_api_websocket_route("/audio-stream", websocket_endpoint)
