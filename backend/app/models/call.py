from enum import Enum
from pydantic import BaseModel, Field

# from .base import BaseModel


class CallStatus(Enum):
    NO_CURRENT_CALL = "no current call"
    IN_PROGRESS = "in progress"
    TRANSFERRED = "transferred"
    SCHEDULED = "scheduled"


class CallRequest(BaseModel):
    phone_number: str = Field(..., title="Phone number to call")
