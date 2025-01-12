from pydantic import BaseModel
from typing import Optional

class GoogleCredential(BaseModel):
    code: str
    redirect_uri: str
