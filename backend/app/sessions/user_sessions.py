from typing import Dict
import uuid
from app.models.user import User

class UserSession:
    def __init__(self, user_id: uuid.UUID, 
                 user: User,
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
        if self.twilio_ws:
            await self.twilio_ws.close()
            print(f"Closed Twilio connection for user {self.user_id}")
        
        if self.openai_ws:
            await self.openai_ws.close()
            print(f"Closed OpenAI connection for user {self.user_id}")
        
        if self.user_id in sessions:
            del sessions[self.user_id]


sessions: Dict[uuid.UUID, UserSession] = {}