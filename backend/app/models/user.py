from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True)
    full_name = Column(String)
    profile_picture = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    refresh_token = Column(String, nullable=True)
    calendar_connected = Column(Boolean, default=False)

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    email: EmailStr
    google_id: str
    full_name: str
    profile_picture: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    profile_picture: Optional[str] = None
    calendar_connected: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None