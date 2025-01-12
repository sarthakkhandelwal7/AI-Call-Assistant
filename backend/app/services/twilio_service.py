import json
from fastapi import WebSocket
from twilio.rest import Client
from typing import Optional
import os
from dotenv import load_dotenv
from twilio.rest import Client as TwilioClient


class TwilioService:

    @classmethod
    def get_instance(cls) -> "TwilioService":
        return cls()

    def __init__(
        self, phone_number: str = None, account_sid: str = None, auth_token: str = None
    ):

        if account_sid and auth_token:
            load_dotenv()
            phone_number = os.getenv("TWILIO_PHONE_NUMBER")
            self.client = TwilioClient()
        else:
            self.client = TwilioClient(account_sid, auth_token)

        self.phone_number = phone_number
        self.stream_sid = None
        self.ws = None

    async def fetch_stream_sid(self, ws: WebSocket) -> None:
        """Wait for initial message to get stream_sid"""
        self.ws = ws
        while True:
            message = await self.ws.receive_text()
            data = json.loads(message)
            if data["event"] == "start":
                self.stream_sid = data["start"]["streamSid"]
                print(f"Call started with Stream SID: {self.stream_sid}")
                break

    async def receive_audio(self, openai_ws: WebSocket) -> None:
        """Receive audio stream from Twilio and send it to OpenAI"""
        try:
            async for message in self.ws.iter_text():
                data = json.loads(message)

                if data["event"] == "media" and openai_ws.state.value == 1:
                    payload = {
                        "type": "input_audio_buffer.append",
                        "audio": data["media"]["payload"],
                    }
                    await openai_ws.send(json.dumps(payload))

                if data["event"] == "stop":
                    print("Closed Message received", message)
                    break

        except Exception as e:
            print(f"Error receiving audio: {e}")
        
        finally:
            if openai_ws and openai_ws.state.value == 1:
                await openai_ws.close()

    def transfer_call(self, call_sid: str, to_number: str) -> None:
        """Transfer active call to another number"""

    def end_call(self, call_sid: str=None) -> None:
        """End active call"""
        self.ws.close()

    def send_sms(self, to_number: str, message: str) -> None:
        """Send SMS message"""
