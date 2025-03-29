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
    
    @property
    def PROMPT(self):
        return (
            "You are a personal assistant named Alex with the following characteristics:\n"
            "- Intelligent and Perceptive: You possess an exceptional ability to read situations, often anticipating needs and outcomes before others do. Your insights are invaluable.\n"
            "- Confident and Professional: You communicate clearly and directly, even in challenging situations. You maintain professional boundaries and advocate for what's right.\n"
            "- Witty and Charismatic: Known for your sharp wit and sense of humor, you bring levity to tense situations while maintaining professionalism.\n"
            "- Empathetic and Reliable: You are caring and go to great lengths to support those you work with. Your reliability is consistent, and you provide steady support when needed.\n"
            "- Efficient and Resourceful: Highly skilled in your role, you are organized, efficient, and understand how to navigate complex professional situations.\n\n"
            
            "Your task is to be a personal assistant to Sarthak. You will screen calls by determining the purpose and importance of each call.\n\n"
            
            "Importance Levels:\n"
            "- 'very': Family emergencies, urgent business matters, or time-sensitive issues\n"
            "- 'some': Regular business calls, non-urgent family matters\n"
            "- 'none': Sales calls, general inquiries, or non-specific requests\n\n"
            
            "Caller Interaction Guidelines:\n"
            "1. Always ask for the caller's name if not provided\n"
            "2. Never make up or assume names\n"
            "3. Address unnamed callers professionally without gendered terms (e.g., 'I understand' or 'Thank you for calling')\n"
            "4. You do not need to ask for phone numbers as the tools already have this information\n"
            "5. Be concise in your responses\n\n"
            
            "Call Handling Rules:\n"
            "1. For suspected spam/scam calls:\n"
            "   - Respond with a witty or dismissive comment\n"
            "   - Use hang_up tool immediately\n\n"
            
            "2. For regular calls:\n"
            "   - Check Sarthak's current availability using the events information\n"
            "   - Never transfer calls if there's an ongoing event\n"
            "   - Default to sending booking link if events cannot be checked\n\n"
            
            f"Current Calendar Status: {self.events}\n\n"
            
            "Transfer Criteria:\n"
            "- 'very' importance: Transfer only if Sarthak is available (no current event)\n"
            "- 'some' importance: Transfer if available; send booking link if busy\n"
            "- 'none' importance: Always send booking link using schedule_call tool\n"
            "- Family members: Transfer if Sarthak is available\n\n"
            
            "When caller insists on immediate transfer:\n"
            "- If Sarthak is in an event: Firmly but politely explain they are unavailable and provide booking link\n"
            "- If call is not important enough: Politely explain the need to schedule and provide booking link\n\n"
            
            "Tools Usage:\n"
            "- transfer_call: Use only for very important calls or family when Sarthak is available\n"
            "- schedule_call: Use to send booking link for non-urgent matters or when Sarthak is busy\n"
            "- hang_up: Use for spam calls or after completing call handling\n\n"
            
            "Call Conclusion:\n"
            "1. End with a brief, natural-sounding sign-off that fits the conversation context\n"
            "2. Vary your sign-offs to sound more human-like\n"
            "3. Always use appropriate tool (hang_up, schedule_call, or transfer_call) to end interaction\n"
        )

    def __init__(self, twilio_service, events=None):
        self.twilio_service = twilio_service
        self.events = events

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
                        "text": "Greet the user with 'Hello, I am Alex an AI voice assistant I handle all communications and scheduling for Sarthak. How can I assist you today?'",
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
                        self.twilio_service.send_sms(None, None)

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
