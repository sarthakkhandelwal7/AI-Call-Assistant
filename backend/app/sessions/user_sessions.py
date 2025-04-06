from typing import Dict
import uuid
from requests import session
import starlette
from app.models.user import UserResponse

class UserSession:
    def __init__(self, user_id: uuid.UUID, 
                 user: UserResponse,
                 from_number: str, 
                 twilio_ws=None, 
                 openai_ws=None):
        self.user_id = user_id
        self.user = user
        self.twilio_ws = twilio_ws
        self.openai_ws = openai_ws
        self.from_number: str = from_number
        self.calendar_events: str = ""
        self.stream_sid = None
        self.call_sid = None
        sessions[self.user_id] = self
        
    async def fetch_user_events(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.twilio_ws.close()
        print(f"Closed Twilio connection for user {self.user_id}")
        await self.openai_ws.close()
        print(f"Closed OpenAI connection for user {self.user_id}")
        del sessions[self.user_id]


sessions: Dict[uuid.UUID, UserSession] = {}