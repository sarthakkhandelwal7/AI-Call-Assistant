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
    
    @staticmethod
    async def receive_audio(ws: WebSocket) -> None:
        """Receive audio stream from Twilio"""
        while True:
            message = await ws.receive_text()
            if not message:
                print("No message received...")
                continue

            data = json.loads(message)
            if data["event"] == "start":
                stream_sid = data.get("streamSid")
                call_sid = data.get("start", {}).get("callSid")
                print(f"Call started with SID: {call_sid}")

            if data["event"] == "media":
                media = data.get("media")

            if data["event"] == "stop":
                print("Closed Message received", message)
                break
        
        return media

    def transfer_call(self, call_sid: str, to_number: str) -> None:
        """Transfer active call to another number"""

    def end_call(self, call_sid: str) -> None:
        """End active call"""

    def send_sms(self, to_number: str, message: str) -> None:
        """Send SMS message"""
