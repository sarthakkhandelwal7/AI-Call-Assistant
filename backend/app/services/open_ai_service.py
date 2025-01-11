import base64
import json
import os
import websockets
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv


class OpenAiService:
    LOG_EVENT_TYPES = [
        "error",
        "response.content.done",
        # "rate_limits.updated",
        "response.done",
        "input_audio_buffer.committed",
        "input_audio_buffer.speech_stopped",
        "input_audio_buffer.speech_started",
        "session.created",
    ]

    SYSTEM_MESSAGE = (
        "You are a helpful and bubbly AI assistant who loves to chat about "
        "anything the user is interested in and is prepared to offer them facts. "
        "You have a penchant for dad jokes, owl jokes, and rickrolling – subtly. "
        "Always stay positive, but work in a joke when appropriate."
    )

    def __init__(self):
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self.stream_sid = None

    @classmethod
    async def create(cls) -> "OpenAiService":
        """Factory method for creating and initializing the service"""
        instance = cls()
        await instance.connect()
        return instance

    async def connect(self) -> None:
        """Establish WebSocket connection with OpenAI"""
        load_dotenv()
        self._ws = await websockets.connect(
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
            additional_headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "OpenAI-Beta": "realtime=v1",
            },
        )

    async def start_session(
        self,
        server_type="server_vad",
        voice="alloy",
        input_audio_format="g711_ulaw",
        output_audio_format="g711_ulaw",
        temperature=0.8,
        modalities=["text", "audio"],
    ) -> None:
        """Initialize session with OpenAI"""
        if not self._ws:
            raise RuntimeError("WebSocket connection not established")

        session_update = {
            "type": "session.update",
            "session": {
                "turn_detection": {"type": server_type},
                "voice": voice,
                "input_audio_format": input_audio_format,
                "output_audio_format": output_audio_format,
                "temperature": temperature,
                "modalities": modalities,
                "instructions": self.SYSTEM_MESSAGE,
            },
        }
        await self._ws.send(json.dumps(session_update))
        await self.send_initial_conversation_item()

    async def send_initial_conversation_item(self) -> None:
        """Send initial conversation item if AI talks first."""
        if not self._ws:
            raise RuntimeError("WebSocket connection not established")

        initial_conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Greet the user with 'Hello there! I am an AI voice assistant powered by Twilio and the OpenAI Realtime API. You can ask me for facts, jokes, or anything you can imagine. How can I help you?'",
                    }
                ],
            },
        }
        await self._ws.send(json.dumps(initial_conversation_item))
        await self._ws.send(json.dumps({"type": "response.create"}))

    async def receive_audio(self, twilio_ws) -> None:
        """Receive audio stream from OpenAI and send it to Twilio"""
        if not self._ws:
            raise RuntimeError("WebSocket connection not established")

        try:
            async for message in self._ws:
                data = json.loads(message)
                # if data["type"] in self.LOG_EVENT_TYPES:
                #     print(f"Received event: {data['type']}", data)

                if data.get("type") == "response.audio.delta" and "delta" in data:

                    response_audio = {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {"payload": data["delta"]},
                    }
                    await twilio_ws.send_json(response_audio)

        except Exception as e:
            print(f"Error receiving audio: {e}")

    async def close(self) -> None:
        """Close the WebSocket connection"""
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def __aenter__(self) -> "OpenAiService":
        await self.connect()
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
