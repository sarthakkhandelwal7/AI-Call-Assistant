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
        # load_dotenv()
        # account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        # auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        # phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        # return cls(account_sid, auth_token, phone_number)
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

    async def receive_audio_start(self, ws: WebSocket) -> None:
        """Wait for initial message to get stream_sid"""
        while True:
            message = await ws.receive_text()
            data = json.loads(message)
            if data["event"] == "start":
                self.stream_sid = data["start"]["streamSid"]
                print(f"Call started with Stream SID: {self.stream_sid}")
                break

    async def receive_audio(self, twilio_ws: WebSocket, openai_ws: WebSocket) -> None:
        """Receive audio stream from Twilio and send it to OpenAI"""
        try:
            async for message in twilio_ws.iter_text():
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
            if openai_ws.state.value == 1:
                await openai_ws.close()

    # async def send_audio(self, twilio_ws: WebSocket, openai_ws: WebSocket) -> None:
    #     """Send audio stream to Twilio"""
    #     try:
    #         async for message in openai_ws:
    #             data = json.loads(message)
    #             if data['type']

    #     except Exception as e:
    #         print(f"Error sending audio: {e}")
    #         if twilio_ws.open:
    #             await twilio_ws.close()

    def transfer_call(self, call_sid: str, to_number: str) -> None:
        """Transfer active call to another number"""

    def end_call(self, call_sid: str) -> None:
        """End active call"""

    def send_sms(self, to_number: str, message: str) -> None:
        """Send SMS message"""
