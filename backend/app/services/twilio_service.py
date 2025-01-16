import json
from fastapi import WebSocket
from typing import Optional
import os
from dotenv import load_dotenv
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse


class TwilioService:

    @classmethod
    def get_instance(cls) -> "TwilioService":
        return cls()

    def __init__(
        self, user_number: str = None, account_sid: str = None, auth_token: str = None
    ):
        load_dotenv()
        if not account_sid or not auth_token:
            self.client = TwilioClient()
            
        else:
            self.client = TwilioClient(account_sid, auth_token)
            
        self.user_number = os.getenv("USER_PHONE_NUMBER")
        self.calendar_url = os.getenv("CALENDLY_URL")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.stream_sid = None
        self.call_sid = None
        self.ws = None

    async def fetch_stream_sid(self, ws: WebSocket) -> None:
        """Wait for initial message to get stream_sid"""
        self.ws = ws
        while True:
            message = await self.ws.receive_text()
            data = json.loads(message)
            if data["event"] == "start":
                self.stream_sid = data["start"]["streamSid"]
                self.call_sid = data.get("start", {}).get("callSid")
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

    def transfer_call(self) -> None:
        """Transfer active call to user's number"""
        twilml = f"""
        <Response>
            <Dial>
                <Number>{self.user_number}</Number>
            </Dial>
        </Response>
        """
        self.client.calls(self.call_sid).update(twiml=twilml)

    def end_call(self) -> None:
        """End active call"""
        self.client.calls(self.call_sid).update(status="completed")

    def send_sms(self) -> None:
        """Send SMS message"""
        message = f"Hello, You can schedule a call with Sarthak using this calander link. {self.calendar_url}"
        self.client.messages.create(to=self.user_number, from_=self.twilio_number, body=message)
