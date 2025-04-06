from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
import uuid

# Create a Pydantic model for validation
class GoogleLoginRequest(BaseModel):
    code: str

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    timezone: Optional[str] = None
    user_number: Optional[str] = None # User's personal number
    calendar_url: Optional[HttpUrl | str] = None

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    user_number: Optional[str] = None
    calendar_url: Optional[HttpUrl | str] = None