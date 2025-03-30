import asyncio
import json
from turtle import st
import uuid
from venv import logger
from fastapi import WebSocket
from openai import BadRequestError
from twilio.rest import Client as TwilioClient
from app.sessions.user_sessions import sessions
from app.core import Settings

class TwilioService:
    def __init__(self, settings: Settings):
        self.client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)       
        

    async def fetch_user_id(self, ws: WebSocket) -> int:
        """Wait for initial message to get stream_sid"""
        while True:
            message = await ws.receive_text()
            data = json.loads(message)
            if data["event"] == "start":
                user_id = uuid.UUID(data["start"]["customParameters"]["user_id"])
                session = sessions[user_id]
                session.stream_sid = data["start"]["streamSid"]
                session.call_sid = data.get("start", {}).get("callSid")
                print(f"Call started with Stream SID: {session.stream_sid}")
                return user_id

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
            print(f"Error receiving audio in twilio: {e}")
        
        finally:
            if openai_ws and openai_ws.state.value == 1:
                await openai_ws.close()

    # In TwilioService class
    async def get_available_numbers(self, country_code="US", area_code=None, limit=20):
        """Fetch available phone numbers with error handling"""
        try:
            params = {"limit": limit}
            
            # Run the Twilio API call in a separate thread to avoid blocking
            numbers = await asyncio.to_thread(
                lambda: self.client.available_phone_numbers(country_code).local.list(**params)
            )
            
            # Format the response to include useful information
            formatted_numbers = []
            for number in numbers:
                formatted_numbers.append({
                    "phone_number": number.phone_number,
                    "friendly_name": number.friendly_name,
                    "capabilities": {
                        "voice": number.capabilities.get("voice", False),
                        "sms": number.capabilities.get("sms", False)
                    }
                })
            
            return formatted_numbers
        except Exception as e:
            print(f"Error fetching available numbers: {str(e)}")
            return None
    
    async def buy_new_number(self, number):
        try:
            response = await asyncio.to_thread(
                lambda: self.client.incoming_phone_numbers.create(phone_number=number)
            )
            formatted_response = {
                "status": 200,
                "message": "Number purchased successfully",
                "phone_number": response.phone_number,
                "friendly_name": response.friendly_name,
                **response.capabilities
            }
            return formatted_response
        
        except BadRequestError as e:
            logger.error(f"Error buying number: {str(e)}")
            return {"status": getattr(e, 'status', 400),
                    "message": e.msg}
            
        except Exception as e:
            logger.error(f"Error buying number: {str(e)}")
            return {"status": 500, "message": str(e)}
        
    def transfer_call(self, call_sid, user_number) -> None:
        """Transfer active call to user's number"""
        twilml = f"""
        <Response>
            <Dial>
                <Number>{user_number}</Number>
            </Dial>
        </Response>
        """
        self.client.calls(call_sid).update(twiml=twilml)

    def end_call(self, call_sid) -> None:
        """End active call"""
        self.client.calls(call_sid).update(status="completed")

    def send_sms(self, user_number, from_number, full_name, calendar_url) -> None:
        """Send SMS message"""
        message = f"Hello, You can schedule a call with {full_name} using this calendar link. {calendar_url}"
        self.client.messages.create(to=user_number, from_=from_number, body=message)
