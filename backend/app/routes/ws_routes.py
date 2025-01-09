import json
from fastapi import APIRouter, WebSocket
import base64
from typing import List

from backend.app.services.twilio_service import TwilioService

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Handle WebSocket connection"""
    await ws.accept()
    print("WebSocket connection established")
    try:
        media = await TwilioService.receive_audio(ws)

    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        await ws.close()
        print("WebSocket connection closed")


router.add_api_websocket_route("/ws", websocket_endpoint)
