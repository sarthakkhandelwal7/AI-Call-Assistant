from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.sql import func


Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True)
    full_name = Column(String)
    profile_picture = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    refresh_token = Column(String, nullable=True)
    calendar_connected = Column(Boolean, default=False)
    timezone = Column(String, default='UTC')
    twilio_number = Column(String, unique=True, nullable=True, index=True)
    user_number = Column(String, unique=True, nullable=True, index=True)


# Pydantic models for request/response validation
class UserCreate(BaseModel):
    email: EmailStr
    google_id: str
    full_name: str
    profile_picture: Optional[str] = None
    timezone: Optional[str] = 'UTC'
    twilio_number: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    profile_picture: Optional[str] = None
    calendar_connected: bool
    timezone: str
    twilio_number: Optional[str] = None

    class Config:
        from_attributes = True