from functools import lru_cache

from fastapi import Depends

from app.services.twilio_service import TwilioService
from app.services.open_ai_service import OpenAiService
from app.core import Settings, get_settings

__all__ = ["TwilioService", "OpenAiService", "get_twilio_service", "get_open_ai_service"]  # Export the services for easier access

@lru_cache()
def get_twilio_service(settings: Settings = Depends(get_settings)) -> TwilioService:
    """Get the Twilio service instance."""
    return TwilioService(settings)

@lru_cache()
def get_open_ai_service(settings: Settings = Depends(get_settings), 
                        twilio_service: TwilioService = Depends(get_twilio_service)) -> OpenAiService:
    """Get the OpenAI service instance."""
    return OpenAiService(settings, twilio_service)
    