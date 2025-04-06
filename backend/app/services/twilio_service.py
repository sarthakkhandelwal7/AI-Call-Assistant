import asyncio
import json
import uuid
import logging
import os
from fastapi import WebSocket, HTTPException
from openai import BadRequestError
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException
from app.sessions.user_sessions import sessions
from app.core import Settings

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID

    async def fetch_user_id(self, ws: WebSocket) -> int:
        """Wait for initial message to get stream_sid"""
        # Wait for the start event
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
                
                if data["event"] == "stop":
                    print("Closed Message received", message)
                    break

                if data["event"] == "media" and openai_ws.state.value == 1:
                    payload = {
                        "type": "input_audio_buffer.append",
                        "audio": data["media"]["payload"],
                    }
                    await openai_ws.send(json.dumps(payload))
                

        except Exception as e:
            print(f"Error receiving audio in twilio: {e}")
        

    # In TwilioService class
    async def get_available_numbers(self, country_code="US", area_code=None, limit=20):
        """Fetch available phone numbers with error handling"""
        try:
            params = {"limit": limit}
            
            # Add area code filter if provided
            if area_code and area_code.isdigit() and len(area_code) == 3:
                params["area_code"] = area_code
            
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
                lambda: self.client.incoming_phone_numbers.create(phone_number=number, VoiceUrl=self.settings.STREAM_URL)
            )
            formatted_response = {
                "status": 201,
                "message": "Number purchased successfully",
                "sid": response.sid,
                "phone_number": response.phone_number,
                "friendly_name": response.friendly_name,
                **response.capabilities
            }
            return formatted_response
        
        except BadRequestError as e:
            logger.error(f"Error buying number: {str(e)}")
            status_code = getattr(e, 'status', 400)
            return {"status": status_code,
                    "message": e.msg}
            
        except TwilioRestException as e:
            logger.error(f"TwilioRestException buying number: {str(e)}")
            return {"status": e.status, "message": e.msg}

        except Exception as e:
            logger.error(f"Unexpected error buying number: {str(e)}")
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

    async def send_verification_otp(self, phone_number: str):
        """Send OTP using Twilio Verify"""
        if not self.verify_service_sid:
            logger.error("Twilio Verify Service SID not configured.")
            raise HTTPException(status_code=500, detail="Verification service not configured")
        
        try:
            logger.info(f"Sending OTP to {phone_number} using service {self.verify_service_sid}")
            verification = await asyncio.to_thread(
                lambda: self.client.verify.v2.services(self.verify_service_sid)
                                      .verifications.create(to=phone_number, channel='sms')
            )
            logger.info(f"OTP send attempt SID: {verification.sid}, Status: {verification.status}")
            return {"status": verification.status} # e.g., "pending"
        except TwilioRestException as e:
            logger.error(f"Twilio error sending OTP to {phone_number}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to send OTP: {e.msg}")
        except Exception as e:
            logger.error(f"Unexpected error sending OTP: {e}")
            raise HTTPException(status_code=500, detail="An internal error occurred while sending OTP.")

    async def check_verification_otp(self, phone_number: str, code: str):
        """Check OTP using Twilio Verify"""
        if not self.verify_service_sid:
            logger.error("Twilio Verify Service SID not configured.")
            raise HTTPException(status_code=500, detail="Verification service not configured")
        
        try:
            logger.info(f"Checking OTP for {phone_number} with code {code[:1]}*** using service {self.verify_service_sid}")
            verification_check = await asyncio.to_thread(
                lambda: self.client.verify.v2.services(self.verify_service_sid)
                                       .verification_checks.create(to=phone_number, code=code)
            )
            logger.info(f"OTP check status for {phone_number}: {verification_check.status}, Valid: {verification_check.valid}")
            return {
                "status": verification_check.status, # e.g., "approved" or "pending"
                "valid": verification_check.valid
            }
        except TwilioRestException as e:
            # Handle specific case where code might be wrong (often returns 404 Not Found)
            if e.status == 404:
                 logger.warning(f"OTP check failed for {phone_number}: Code incorrect or expired.")
                 return {"status": "failed", "valid": False, "message": "Incorrect or expired code."}
            
            logger.error(f"Twilio error checking OTP for {phone_number}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to check OTP: {e.msg}")
        except Exception as e:
            logger.error(f"Unexpected error checking OTP: {e}")
            raise HTTPException(status_code=500, detail="An internal error occurred while checking OTP.")
