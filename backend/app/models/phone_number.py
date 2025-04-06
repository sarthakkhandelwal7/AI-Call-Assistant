from pydantic import BaseModel

class BuyNumberRequest(BaseModel):
    number: str
    
class BuyNumberResponse(BaseModel):
    success: bool
    message: str