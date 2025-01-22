from pydantic import BaseModel

# Create a Pydantic model for validation
class GoogleLoginRequest(BaseModel):
    code: str