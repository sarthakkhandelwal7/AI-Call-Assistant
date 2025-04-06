from pydantic import BaseModel, Field

class BuyNumberRequest(BaseModel):
    number: str
    
class BuyNumberResponse(BaseModel):
    success: bool
    message: str

class SendOtpRequest(BaseModel):
    phone_number: str = Field(..., description="E.164 formatted phone number to send OTP to.")

class CheckOtpRequest(BaseModel):
    phone_number: str = Field(..., description="E.164 formatted phone number.")
    code: str = Field(..., min_length=4, max_length=10, description="OTP code entered by user.")

