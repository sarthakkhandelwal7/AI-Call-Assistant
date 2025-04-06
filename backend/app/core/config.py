from attr import frozen
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Settings for the application."""
    # Required API Keys and URLs
    OPENAI_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_VERIFY_SERVICE_SID: str
    STREAM_URL: str
    FRONTEND_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    
    # Optional/Dev specific - Make these optional with defaults
    TWILIO_PHONE_NUMBER: str | None = None
    HARVEY_PHONE_NUMBER: str | None = None
    CALENDLY_URL: str | None = None
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    
    # Database connection pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    class Config:
        # Get environment from APP_ENV variable, default to development
        env = os.getenv("APP_ENV", "dev")
        
        # Use different .env files based on environment
        env_file = f".env.{env}"
        
        # Fall back to .env if the specific file doesn't exist
        if not os.path.isfile(env_file):
            env_file = ".env"
            
        frozen = True  # Make the settings immutable after initialization

