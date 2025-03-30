import base64
import json
import os
from fastapi import Depends
import websockets
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from backend.app.core import Settings

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

    
        
    def get_test_prompt(self) -> str:
        return (
            "You are Alex, an AI assistant. When a caller mentions transfer call, "
            "immediately use the transfer_call tool if Sarthak is available. or caller asks to transfer call"
            f"Current calendar: No events found for today."
            "When a caller mentions nothing important or general call or send sms"
            "or non-urgent matter, immediately use the schedule_call tool to send them a booking link."
            "When you detect any mention of extended warranties, bitcoin investments, or user mentions prank call "
            "or suspicious offers, immediately respond with a witty dismissal and use the hang_up tool."
        )
    def get_prompt(self, events: str) -> str:
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
            
            f"Current Calendar Status: {events}\n\n"
            
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

    def __init__(self, settings: Settings, twilio_service) -> None:
        self.twilio_service = twilio_service 
        self.settings = settings

    async def connect(self) -> websockets.WebSocketClientProtocol:
        """Establish WebSocket connection with OpenAI"""
        ws = await websockets.connect(
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
            additional_headers={
                "Authorization": f"Bearer {self.settings.OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            },
        )
        return ws

    async def start_session(
        self,
        ws: Optional[websockets.WebSocketClientProtocol],
        voice="alloy",
        input_audio_format="g711_ulaw",
        output_audio_format="g711_ulaw",
        temperature=0.8,
        modalities=["text", "audio"],
        events: str = "No events found for today.",
    ) -> None:
        """Initialize session with OpenAI"""
        if not ws:
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
                # "instructions": self.get_prompt(events),
                "instructions": self.get_test_prompt(),
                
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
        await ws.send(json.dumps(session_update))
        await self.send_initial_conversation_item(ws)

    async def send_initial_conversation_item(self, ws) -> None:
        """Send initial conversation item if AI talks first."""
        if not ws:
            raise RuntimeError("WebSocket connection not established")

        initial_conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        # "text": "Greet the user with 'Hello, I am Alex an AI voice assistant I handle all communications and scheduling for Sarthak. How can I assist you today?'",
                        "text": "Greet the user with 'Hello, I am Alex an AI voice assistant. How can I assist you today?'",
                    }
                ],
            },
        }
        await ws.send(json.dumps(initial_conversation_item))
        await ws.send(json.dumps({"type": "response.create"}))

    async def receive_audio(self, session) -> None:
        """Receive audio stream from OpenAI and send it to Twilio"""
        
        if not session.openai_ws:
            raise RuntimeError("WebSocket connection not established")

        function_name = None
        try:
            async for message in session.openai_ws:
                data = json.loads(message)
                # if data["type"] in self.LOG_EVENT_TYPES:
                #     print(f"Received event: {data['type']}", data)

                # Save JSON data to responses folder
                # file_name = data.get("type", "unknown").replace(".", "_") + ".json"

                # file_path = os.path.join("responses", file_name)

                # with open(f"responses/{file_name}", "w") as file:
                #     json.dump(data, file, indent=4)
                
                if "error" in data:
                    print(f"Error: {data['error']}")
                    raise Exception(data["error"])

                if data.get("type") == "response.audio.delta" and "delta" in data:

                    response_audio = {
                        "event": "media",
                        "streamSid": session.stream_sid,
                        "media": {"payload": data["delta"]},
                    }
                    await session.twilio_ws.send_json(response_audio)

                if data.get("type") == "response.function_call_arguments.done":
                    # Not menthiioned in the api docs but it containes a name key
                    function_name = data["name"]

                if data.get("type") == "response.done":
                    if function_name == "hang_up":
                        self.twilio_service.end_call(session.call_sid)

                    elif function_name == "schedule_call":
                        self.twilio_service.send_sms(session.user.user_number, session.from_number, session.user.full_name, session.user.calendar_url)

                    elif function_name == "transfer_call":
                        self.twilio_service.transfer_call(session.call_sid, session.user.user_number)

        except Exception as e:
            print(f"Error receiving audio in openai: {e}")