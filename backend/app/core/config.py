from attr import frozen
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the application."""
    OPENAI_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_VERIFY_SERVICE_SID: str
    FRONTEND_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    
    # Optional/Dev specific - Make these optional with defaults

    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    
    # Database connection pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    class Config:
        env_file = ".env"
        frozen = True  # Make the settings immutable after initialization

