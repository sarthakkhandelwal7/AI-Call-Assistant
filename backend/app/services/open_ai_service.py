import base64
import json
import os
from fastapi import Depends
import websockets
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from backend.app.services.calendar_service import CalendarService


class OpenAiService:
    LOG_EVENT_TYPES = [
        "error",
        "response.content.done",
        "rate_limits.updated",
        "response.done",
        "input_audio_buffer.committed",
        "input_audio_buffer.speech_stopped",
        "input_audio_buffer.speech_started",
        "session.created",
    ]

    events = None

    PROMPT = (
        "You are a personal assistant named Alex with the following characteristics:"
        "Intelligent and Perceptive: You possess an exceptional ability to read situations, often anticipating needs and outcomes before others do. Your insights are invaluable."
        "Confident and Professional: You communicate clearly and aren't afraid to speak directly, even in challenging situations. You maintain professional boundaries and advocate for what's right."
        "Witty and Charismatic: Known for your sharp wit and sense of humor, you bring levity to tense situations while maintaining professionalism."
        "Empathetic and Reliable: You are caring and go to great lengths to support those you work with. Your reliability is consistent, and you provide steady support when needed."
        "Efficient and Resourceful: Highly skilled in your role, you are indispensable. You are organized, efficient, and understand how to navigate complex professional situations."
        "Your task is to be a personal assistant to Sarthak. You will screen calls by determining the purpose and importance of each call."
        "Categorize the importance as 'none', 'some', or 'very'. Be efficient and direct in your communication."
        "You do not need to ask the caller for their phone number, as the tools already have the phone number. Be as concise as possible in your responses."
        "If you suspect the caller is a spammer or scammer, respond with a witty or dismissive comment, then use the hang_up tool to end the call immediately."
        "If the call is not important, politely ask the caller to schedule a call with Sarthak by using the schedule_call tool, which will send them a scheduling link."
        "If the call is 'some' importance, then use the following events information to check Sarthak's schedule for today and if they're free, transfer the call using the transfer_call tool. Otherwise, just ask the caller to schedule a call at the link you're sending them and then use the schedule_call tool, insisting that they're busy right now."
        f"If the caller asks when Sarthak is free next, tell them the specific time the current event ends. {events}"
        "If the call is important, transfer the call to Sarthak using the transfer_call tool. Only transfer the call if it's very important or from a family member, otherwise just ask the caller to schedule a call at the link you're sending them and then use the schedule_call tool."
        "Always end the call with a brief, natural-sounding sign-off that fits the context of the conversation. Vary your sign-offs to sound more human-like. After the sign-off, use the appropriate tool (hang_up, schedule_call, or transfer_call) to end the interaction."
    )

    def __init__(self, twilio_service, calendar_service):
        self.twilio_service = twilio_service
        self.calendar_service = calendar_service

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
        voice="alloy",
        input_audio_format="g711_ulaw",
        output_audio_format="g711_ulaw",
        temperature=0.8,
        modalities=["text", "audio"],
    ) -> None:
        """Initialize session with OpenAI"""
        if not self._ws:
            raise RuntimeError("WebSocket connection not established")

        self.event = self.calendar_service.get_todays_events()

        session_update = {
            "type": "session.update",
            "session": {
                "turn_detection": {"type": "server_vad"},
                "voice": voice,
                "input_audio_format": input_audio_format,
                "output_audio_format": output_audio_format,
                "temperature": temperature,
                "modalities": modalities,
                "instructions": self.PROMPT,
                "tools": [
                    {
                        "type": "function",
                        "name": "hang_up",
                        "description": "End the call immediately",
                    },
                    {
                        "type": "function",
                        "name": "schedule_call",
                        "description": "Send a scheduling link to the caller",
                    },
                    {
                        "type": "function",
                        "name": "transfer_call",
                        "description": "Transfer the call to Sarthak",
                    },
                ],
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
                        "text": "Greet the user with 'Hello, I am Alex an AI voice assistant I handle all communications and scheduling for Sarthak - think of me as the gatekeeper with impeccable taste and timing. How can I assist you today?'",
                    }
                ],
            },
        }
        await self._ws.send(json.dumps(initial_conversation_item))
        await self._ws.send(json.dumps({"type": "response.create"}))

    async def receive_audio(self) -> None:
        """Receive audio stream from OpenAI and send it to Twilio"""
        if not self._ws:
            raise RuntimeError("WebSocket connection not established")

        function_name = None
        try:
            async for message in self._ws:
                data = json.loads(message)
                # if data["type"] in self.LOG_EVENT_TYPES:
                #     print(f"Received event: {data['type']}", data)

                # Save JSON data to responses folder
                file_name = data.get("type", "unknown").replace(".", "_") + ".json"

                # file_path = os.path.join("responses", file_name)

                with open(f"responses/{file_name}", "w") as file:
                    json.dump(data, file, indent=4)
                
                if "error" in data:
                    print(f"Error: {data['error']}")
                    raise Exception(data["error"])

                if data.get("type") == "response.audio.delta" and "delta" in data:

                    response_audio = {
                        "event": "media",
                        "streamSid": self.twilio_service.stream_sid,
                        "media": {"payload": data["delta"]},
                    }
                    await self.twilio_service.ws.send_json(response_audio)

                if data.get("type") == "response.function_call_arguments.done":
                    # Not menthiioned in the api docs but it containes a name key
                    function_name = data["name"]

                if data.get("type") == "response.done":
                    if function_name == "hang_up":
                        self.twilio_service.end_call()

                    elif function_name == "schedule_call":
                        self.twilio_service.send_sms()

                    elif function_name == "transfer_call":
                        self.twilio_service.transfer_call()

        except Exception as e:
            print(f"Error receiving audio: {e}")

    async def close(self) -> None:
        """Close the WebSocket connection"""
        if self._ws:
            await self._ws.close()
            self._ws = None
            print("OpenAI WebSocket connection closed")

    async def __aenter__(self) -> "OpenAiService":
        await self.connect()
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
