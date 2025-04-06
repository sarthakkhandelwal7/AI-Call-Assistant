from functools import lru_cache
from .config import Settings

__all__ = ["get_settings", "Settings"]

@lru_cache()
def get_settings() -> Settings:
    """Get the application settings."""
    return Settings()