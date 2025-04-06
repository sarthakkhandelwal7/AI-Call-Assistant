from attr import frozen
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the application."""
    OPENAI_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    STREAM_URL: str
    FRONTEND_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    
    class Config:
        env_file = ".env"
        frozen = True  # Make the settings immutable after initialization

